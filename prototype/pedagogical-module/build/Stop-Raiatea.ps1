[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
function Fail([string]$Code) { [Console]::Error.WriteLine($Code); exit 1 }

$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateDir = Join-Path $ReleaseDir '.raiatea-runtime'
$StateFile = Join-Path $StateDir 'server-state.json'
if (-not (Test-Path -LiteralPath $StateFile -PathType Leaf)) { Fail 'STATE_STALE' }

try {
    $state = Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json
    $names = @($state.PSObject.Properties.Name | Sort-Object)
    if (($names -join ',') -ne 'entrypoint,host,marker,pid,port') { Fail 'STATE_STALE' }
    if ($state.marker -ne 'raiatea-launch-state-v1' -or $state.host -ne '127.0.0.1' -or $state.entrypoint -ne 'pilot/index.html') { Fail 'STATE_STALE' }
    $processId = [int]$state.pid
    $port = [int]$state.port
    if ($processId -le 1 -or $port -lt 1024 -or $port -gt 65535) { Fail 'STATE_STALE' }
} catch { Fail 'STATE_STALE' }

try { $process = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" } catch { $process = $null }
if (-not $process) {
    Remove-Item -LiteralPath $StateFile -Force -ErrorAction SilentlyContinue
    Fail 'STATE_STALE'
}
$pilot = Join-Path $ReleaseDir 'pilot'
$command = [string]$process.CommandLine
if ($command -notmatch [regex]::Escape('http.server') -or $command -notmatch [regex]::Escape("$port") -or $command -notmatch [regex]::Escape('127.0.0.1') -or $command -notmatch [regex]::Escape($pilot)) {
    Fail 'STATE_FOREIGN_PROCESS'
}

try { Stop-Process -Id $processId -ErrorAction Stop } catch { Fail 'STOP_FAILED' }
for ($i = 0; $i -lt 40; $i++) {
    if (-not (Get-Process -Id $processId -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Milliseconds 100
}
if (Get-Process -Id $processId -ErrorAction SilentlyContinue) {
    try { Stop-Process -Id $processId -Force -ErrorAction Stop } catch { Fail 'STOP_FAILED' }
}
Remove-Item -LiteralPath $StateFile -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $StateDir 'server.log') -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $StateDir -Force -ErrorAction SilentlyContinue
Write-Output "Raiatea stopped on port $port."
