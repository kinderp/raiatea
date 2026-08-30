use serde::Deserialize;
use serde_json::{json, Value};
use std::env;
use std::io::{self, BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use tauri::{Manager, State};

const DEMO_CONTRACT: &str = "raiatea.gui-live-demo.0.1.0";
const MAX_FRAME_BYTES: usize = 1024 * 1024;
const ALLOWED_METHODS: [&str; 5] = [
    "gateway.status",
    "library.page",
    "source.detail",
    "search.page",
    "representation.page",
];

#[derive(Debug, Deserialize)]
struct DemoManifest {
    contract: String,
    scope_id: String,
    catalog_store: String,
}

fn allowed_method(method: &str) -> bool {
    ALLOWED_METHODS.contains(&method)
}

fn repo_root() -> Result<PathBuf, String> {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .map_err(|_| "desktop-repo-root-unavailable".to_string())
}

fn demo_manifest_path(repo: &Path) -> PathBuf {
    env::var_os("RAIATEA_GUI_DEMO_MANIFEST")
        .map(PathBuf::from)
        .unwrap_or_else(|| repo.join(".raiatea-demo").join("manifest.json"))
}

fn load_demo_manifest(path: &Path) -> Result<DemoManifest, String> {
    let raw = std::fs::read_to_string(path)
        .map_err(|_| "desktop-demo-manifest-missing-run-bootstrap".to_string())?;
    let manifest: DemoManifest = serde_json::from_str(&raw)
        .map_err(|_| "desktop-demo-manifest-invalid".to_string())?;
    if manifest.contract != DEMO_CONTRACT {
        return Err("desktop-demo-manifest-version-mismatch".to_string());
    }
    if manifest.scope_id.is_empty() {
        return Err("desktop-demo-scope-id-invalid".to_string());
    }
    let catalog = PathBuf::from(&manifest.catalog_store);
    if !catalog.is_absolute() || !catalog.is_file() {
        return Err("desktop-demo-catalog-store-invalid".to_string());
    }
    Ok(manifest)
}

fn python_command() -> String {
    env::var("RAIATEA_PYTHON").unwrap_or_else(|_| {
        if cfg!(windows) {
            "python".to_string()
        } else {
            "python3".to_string()
        }
    })
}

fn drain_to_newline<R: BufRead>(reader: &mut R) -> io::Result<()> {
    loop {
        let available = reader.fill_buf()?;
        if available.is_empty() {
            return Ok(());
        }
        let available_len = available.len();
        if let Some(position) = available.iter().position(|byte| *byte == b'\n') {
            reader.consume(position + 1);
            return Ok(());
        }
        reader.consume(available_len);
    }
}

fn read_bounded_line<R: BufRead>(reader: &mut R, max_bytes: usize) -> io::Result<Vec<u8>> {
    let mut output = Vec::new();
    loop {
        let available = reader.fill_buf()?;
        if available.is_empty() {
            return Err(io::Error::new(
                io::ErrorKind::UnexpectedEof,
                "sidecar-response-eof",
            ));
        }
        let available_len = available.len();
        if let Some(position) = available.iter().position(|byte| *byte == b'\n') {
            let take = position + 1;
            if output.len() + take > max_bytes {
                reader.consume(take);
                return Err(io::Error::new(
                    io::ErrorKind::InvalidData,
                    "sidecar-response-too-large",
                ));
            }
            output.extend_from_slice(&available[..take]);
            reader.consume(take);
            return Ok(output);
        }

        if output.len() + available_len > max_bytes {
            reader.consume(available_len);
            drain_to_newline(reader)?;
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "sidecar-response-too-large",
            ));
        }
        output.extend_from_slice(available);
        reader.consume(available_len);
    }
}

struct BridgeProcess {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
}

impl BridgeProcess {
    fn spawn_from_demo() -> Result<Self, String> {
        let repo = repo_root()?;
        let manifest = load_demo_manifest(&demo_manifest_path(&repo))?;
        Self::spawn(&repo, &manifest)
    }

    fn spawn(repo: &Path, manifest: &DemoManifest) -> Result<Self, String> {
        let mut child = Command::new(python_command())
            .current_dir(repo)
            .arg("-m")
            .arg("prototype.p0_vs1.application_bridge_sidecar")
            .arg("--catalog-store")
            .arg(&manifest.catalog_store)
            .arg("--scope-id")
            .arg(&manifest.scope_id)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|_| "desktop-sidecar-spawn-failed".to_string())?;

        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| "desktop-sidecar-stdin-unavailable".to_string())?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| "desktop-sidecar-stdout-unavailable".to_string())?;
        Ok(Self {
            child,
            stdin,
            stdout: BufReader::new(stdout),
        })
    }

    fn request(&mut self, request_id: &str, method: &str, params: Value) -> Result<Value, String> {
        if !allowed_method(method) {
            return Err("desktop-bridge-method-forbidden".to_string());
        }
        if !params.is_object() {
            return Err("desktop-bridge-params-must-be-object".to_string());
        }
        if self
            .child
            .try_wait()
            .map_err(|_| "desktop-sidecar-state-check-failed".to_string())?
            .is_some()
        {
            return Err("desktop-sidecar-not-running".to_string());
        }

        let request = json!({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        });
        let mut frame = serde_json::to_vec(&request)
            .map_err(|_| "desktop-bridge-request-serialization-failed".to_string())?;
        frame.push(b'\n');
        if frame.len() > MAX_FRAME_BYTES {
            return Err("desktop-bridge-request-too-large".to_string());
        }
        self.stdin
            .write_all(&frame)
            .and_then(|_| self.stdin.flush())
            .map_err(|_| "desktop-sidecar-write-failed".to_string())?;

        let response_frame = read_bounded_line(&mut self.stdout, MAX_FRAME_BYTES)
            .map_err(|error| match error.kind() {
                io::ErrorKind::InvalidData => "desktop-sidecar-response-too-large".to_string(),
                _ => "desktop-sidecar-read-failed".to_string(),
            })?;
        let response: Value = serde_json::from_slice(&response_frame)
            .map_err(|_| "desktop-sidecar-response-invalid-json".to_string())?;
        let object = response
            .as_object()
            .ok_or_else(|| "desktop-sidecar-response-must-be-object".to_string())?;
        if object.get("jsonrpc") != Some(&Value::String("2.0".to_string())) {
            return Err("desktop-sidecar-response-version-invalid".to_string());
        }
        if object.get("id") != Some(&Value::String(request_id.to_string())) {
            return Err("desktop-sidecar-response-id-mismatch".to_string());
        }
        let has_result = object.contains_key("result");
        let has_error = object.contains_key("error");
        if has_result == has_error {
            return Err("desktop-sidecar-response-shape-invalid".to_string());
        }
        if has_error {
            let message = object
                .get("error")
                .and_then(Value::as_object)
                .and_then(|error| error.get("message"))
                .and_then(Value::as_str)
                .unwrap_or("bridge-error");
            return Err(format!("desktop-sidecar:{message}"));
        }
        object
            .get("result")
            .cloned()
            .ok_or_else(|| "desktop-sidecar-result-missing".to_string())
    }
}

impl Drop for BridgeProcess {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

struct DesktopState {
    bridge: Mutex<BridgeProcess>,
    next_id: AtomicU64,
}

#[tauri::command]
fn raiatea_application_request(
    state: State<'_, DesktopState>,
    method: String,
    params: Value,
) -> Result<Value, String> {
    let sequence = state.next_id.fetch_add(1, Ordering::Relaxed);
    let request_id = format!("tauri:{sequence}");
    let mut bridge = state
        .bridge
        .lock()
        .map_err(|_| "desktop-sidecar-lock-poisoned".to_string())?;
    bridge.request(&request_id, &method, params)
}

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let bridge = BridgeProcess::spawn_from_demo().map_err(|message| {
                Box::<dyn std::error::Error>::from(io::Error::other(message))
            })?;
            app.manage(DesktopState {
                bridge: Mutex::new(bridge),
                next_id: AtomicU64::new(1),
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![raiatea_application_request])
        .run(tauri::generate_context!())
        .expect("error while running Raiatea live desktop demo");
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn method_allowlist_is_closed() {
        for method in ALLOWED_METHODS {
            assert!(allowed_method(method));
        }
        assert!(!allowed_method("system.shell"));
        assert!(!allowed_method("fs.read"));
    }

    #[test]
    fn bounded_line_reader_accepts_one_frame_and_rejects_oversize() {
        let mut reader = BufReader::new(Cursor::new(b"{\"ok\":true}\nnext\n".to_vec()));
        let first = read_bounded_line(&mut reader, 64).expect("bounded frame");
        assert_eq!(first, b"{\"ok\":true}\n");
        let second = read_bounded_line(&mut reader, 64).expect("second frame");
        assert_eq!(second, b"next\n");

        let mut oversized = BufReader::new(Cursor::new(format!("{}\nok\n", "x".repeat(80)).into_bytes()));
        assert_eq!(
            read_bounded_line(&mut oversized, 32)
                .expect_err("oversize must fail")
                .kind(),
            io::ErrorKind::InvalidData
        );
        assert_eq!(read_bounded_line(&mut oversized, 32).expect("stream resync"), b"ok\n");
    }

    #[test]
    #[ignore = "requires python demo bootstrap"]
    fn live_sidecar_smoke() {
        let mut bridge = BridgeProcess::spawn_from_demo().expect("spawn live demo sidecar");
        let status = bridge
            .request("test:status", "gateway.status", json!({}))
            .expect("gateway status");
        assert_eq!(status["payload"]["mode"], "live");

        let library = bridge
            .request(
                "test:library",
                "library.page",
                json!({"page_size": 10, "cursor": null}),
            )
            .expect("library page");
        let first = &library["payload"]["items"][0];
        let item_ref = first["item_ref"].as_str().expect("item ref");

        let detail = bridge
            .request(
                "test:detail",
                "source.detail",
                json!({"item_ref": item_ref}),
            )
            .expect("source detail");
        let representation_id = detail["payload"]["representations"][0]["representation_id"]
            .as_str()
            .expect("representation id");

        let search = bridge
            .request(
                "test:search",
                "search.page",
                json!({
                    "plan": {
                        "criteria": [{
                            "field": "extracted_text",
                            "operator": "contains",
                            "value": "Introduction"
                        }],
                        "sort_field": "source_ref_id",
                        "descending": false
                    },
                    "page_size": 10,
                    "cursor": null
                }),
            )
            .expect("search page");
        assert_eq!(search["payload"]["freshness"], "fresh");
        assert!(search["payload"]["items"].as_array().is_some_and(|rows| !rows.is_empty()));

        let representation = bridge
            .request(
                "test:representation",
                "representation.page",
                json!({
                    "representation_id": representation_id,
                    "page_size": 5,
                    "cursor": null
                }),
            )
            .expect("representation page");
        assert!(representation["payload"]["units"]
            .as_array()
            .is_some_and(|units| !units.is_empty()));
    }
}
