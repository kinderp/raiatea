[CmdletBinding()]
param(
    [object]$Port = 8000,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
function Fail([string]$Code) { [Console]::Error.WriteLine($Code); exit 1 }

$PortText = [string]$Port
if ($PortText -notmatch '^[0-9]+$') { Fail 'PORT_INVALID' }
try { $Port = [int]$PortText } catch { Fail 'PORT_INVALID' }
if ($Port -lt 1024 -or $Port -gt 65535) { Fail 'PORT_INVALID' }

$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateDir = Join-Path $ReleaseDir '.raiatea-runtime'
$StateFile = Join-Path $StateDir 'server-state.json'

foreach ($relative in @('RELEASE-NOTES.md','SHA256SUMS','release-manifest.json','pilot/index.html')) {
    $path = Join-Path $ReleaseDir $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Fail 'RELEASE_FILE_UNSAFE' }
}

try {
    $manifest = Get-Content -LiteralPath (Join-Path $ReleaseDir 'release-manifest.json') -Raw | ConvertFrom-Json
    $prefix = 'raiatea-evaluator-'
    $name = Split-Path -Leaf $ReleaseDir
    if (-not $name.StartsWith($prefix) -or $manifest.format -ne 'raiatea-evaluator-release' -or $manifest.releaseVersion -ne $name.Substring($prefix.Length)) { Fail 'RELEASE_IDENTITY_MISMATCH' }
} catch { Fail 'RELEASE_IDENTITY_MISMATCH' }

if (Test-Path -LiteralPath $StateFile) { Fail 'STATE_ALREADY_EXISTS' }

$PythonExe = $null
$candidates = @(
    [pscustomobject]@{ Exe = 'py'; Prefix = @('-3') },
    [pscustomobject]@{ Exe = 'python'; Prefix = @() }
)
foreach ($candidate in $candidates) {
    try {
        $command = Get-Command $candidate.Exe -ErrorAction Stop
        $prefixArgs = @($candidate.Prefix)
        $resolved = & $command.Source @prefixArgs -c "import sys; print(sys.executable) if sys.version_info >= (3,10) else sys.exit(1)"
        if ($LASTEXITCODE -eq 0 -and $resolved) {
            $candidatePath = ([string]$resolved).Trim()
            if (Test-Path -LiteralPath $candidatePath -PathType Leaf) { $PythonExe = $candidatePath; break }
        }
    } catch { }
}
if (-not $PythonExe) { Fail 'PYTHON_NOT_FOUND' }

try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    $listener.Start(); $listener.Stop()
} catch { Fail 'PORT_IN_USE' }

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$pilot = Join-Path $ReleaseDir 'pilot'
$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $PythonExe
$startInfo.Arguments = "-m http.server $Port --bind 127.0.0.1 --directory `"$pilot`""
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
try {
    $process = [System.Diagnostics.Process]::Start($startInfo)
    if (-not $process) { Fail 'SERVER_START_FAILED' }
} catch { Fail 'SERVER_START_FAILED' }

$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    if ($process.HasExited) { break }
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/index.html" -TimeoutSec 1
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch { Start-Sleep -Milliseconds 100 }
}
if (-not $ready) {
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $StateFile -Force -ErrorAction SilentlyContinue
    Fail 'SERVER_NOT_READY'
}

$state = [ordered]@{ marker='raiatea-launch-state-v1'; pid=$process.Id; port=$Port; host='127.0.0.1'; entrypoint='pilot/index.html' }
$tmp = Join-Path $StateDir ('.server-state.' + $PID + '.json')
$json = ($state | ConvertTo-Json -Compress) + [Environment]::NewLine
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tmp, $json, $utf8)
Move-Item -LiteralPath $tmp -Destination $StateFile
$url = "http://127.0.0.1:$Port/index.html"
if (-not $NoOpen) { try { Start-Process $url | Out-Null } catch { } }
Write-Output "Raiatea ready: $url"
Write-Output "Stop with: powershell -File `"$ReleaseDir\Stop-Raiatea.ps1`""
