from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
sys.path.insert(0, str(BUILD))

import build_evaluator_archive  # noqa: E402
import build_posix_evaluator_archive  # noqa: E402


def free_port() -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


class PosixLaunchHelperTests(unittest.TestCase):
    def build_and_extract(self, root: Path, version: str = "posix-1") -> Path:
        archive = build_posix_evaluator_archive.build_posix_evaluator_archive(root / "build", version)
        return build_evaluator_archive.verify_evaluator_archive(archive, root / "verified")

    def test_archive_contains_helpers_guide_and_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            release = self.build_and_extract(Path(temporary))
            entries = dict(
                (path, digest)
                for digest, path in build_evaluator_archive._parse_checksums(
                    (release / "SHA256SUMS").read_text(encoding="ascii")
                )
            )
            for name in ("launch-posix.sh", "stop-posix.sh", "POSIX-LAUNCH.md"):
                self.assertTrue((release / name).is_file())
                self.assertIn(name, entries)
            self.assertIn("127.0.0.1", (release / "launch-posix.sh").read_text(encoding="utf-8"))
            self.assertNotIn("curl http", (release / "launch-posix.sh").read_text(encoding="utf-8"))

    def test_launch_serves_and_stop_cleans_state_with_space_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="raiatea posix ") as temporary:
            root = Path(temporary)
            release = self.build_and_extract(root)
            port = free_port()
            launch = subprocess.run(
                ["sh", str(release / "launch-posix.sh"), "--no-open", "--port", str(port)],
                text=True,
                capture_output=True,
                timeout=20,
            )
            self.assertEqual(0, launch.returncode, launch.stderr)
            self.assertIn(f"http://127.0.0.1:{port}/index.html", launch.stdout)
            state_path = release / ".raiatea-runtime" / "server-state.json"
            self.assertTrue(state_path.is_file())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual("raiatea-launch-state-v1", state["marker"])
            try:
                deadline = time.monotonic() + 5
                while True:
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                            break
                    except OSError:
                        if time.monotonic() >= deadline:
                            self.fail("server did not become reachable")
                        time.sleep(0.05)
            finally:
                stop = subprocess.run(
                    ["sh", str(release / "stop-posix.sh")],
                    text=True,
                    capture_output=True,
                    timeout=20,
                )
            self.assertEqual(0, stop.returncode, stop.stderr)
            self.assertFalse(state_path.exists())

    def test_invalid_and_occupied_ports_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            release = self.build_and_extract(Path(temporary))
            invalid = subprocess.run(
                ["sh", str(release / "launch-posix.sh"), "--no-open", "--port", "abc"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, invalid.returncode)
            self.assertIn("PORT_INVALID", invalid.stderr)
            with socket.socket() as server:
                server.bind(("127.0.0.1", 0))
                server.listen()
                port = server.getsockname()[1]
                occupied = subprocess.run(
                    ["sh", str(release / "launch-posix.sh"), "--no-open", "--port", str(port)],
                    text=True,
                    capture_output=True,
                )
            self.assertNotEqual(0, occupied.returncode)
            self.assertIn("PORT_IN_USE", occupied.stderr)
            self.assertFalse((release / ".raiatea-runtime" / "server-state.json").exists())

    def test_foreign_state_never_kills_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            release = self.build_and_extract(Path(temporary))
            state_dir = release / ".raiatea-runtime"
            state_dir.mkdir()
            process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            try:
                (state_dir / "server-state.json").write_text(
                    json.dumps(
                        {
                            "entrypoint": "pilot/index.html",
                            "host": "127.0.0.1",
                            "marker": "raiatea-launch-state-v1",
                            "pid": process.pid,
                            "port": free_port(),
                        },
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                stopped = subprocess.run(
                    ["sh", str(release / "stop-posix.sh")],
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(0, stopped.returncode)
                self.assertIn("STATE_FOREIGN_PROCESS", stopped.stderr)
                self.assertIsNone(process.poll())
            finally:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
