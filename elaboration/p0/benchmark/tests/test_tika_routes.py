from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
CONFIG_PATH = BENCH_DIR / "config" / "tika-pdf-native-no-ocr.xml"
SPEC = importlib.util.spec_from_file_location("p0_tika_routes", ROUTES_DIR / "tika_routes.py")
TIKA = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TIKA)


SYNTHETIC_XHTML = b'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><meta name="Content-Type" content="application/pdf"/></head>
<body>
<div class="page">
<h1 id="title">Raiatea B01 PDF 001</h1>
<p>Alpha paragraph preserves exact benchmark text.</p>
<p>Beta paragraph follows alpha in reading order.</p>
</div>
</body></html>'''

NO_PAGE_XHTML = b'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<p>Alpha paragraph preserves exact benchmark text.</p>
</body></html>'''


class TikaConfigTests(unittest.TestCase):
    def test_config_disables_ocr_and_excludes_tesseract(self):
        root = ET.parse(CONFIG_PATH).getroot()
        params = {
            param.attrib.get("name"): (param.text or "").strip()
            for param in root.findall(".//param")
        }
        self.assertEqual(params.get("ocrStrategy"), "no_ocr")
        self.assertEqual(params.get("extractInlineImages"), "false")
        excludes = {
            parser.attrib.get("class")
            for parser in root.findall(".//parser-exclude")
        }
        self.assertIn("org.apache.tika.parser.ocr.TesseractOCRParser", excludes)

    def test_config_contains_no_access_control_or_remote_settings(self):
        text = CONFIG_PATH.read_text(encoding="utf-8").lower()
        for forbidden in ["password", "-p", "http://", "https://", "extractall", "nodrm"]:
            self.assertNotIn(forbidden, text)


class TikaMapperTests(unittest.TestCase):
    def test_mapper_promotes_only_explicit_semantics_and_page_marker(self):
        mapped = TIKA.map_tika_xhtml(SYNTHETIC_XHTML)
        self.assertTrue(mapped["page_structure_observed"])
        self.assertFalse(mapped["bbox_structure_observed"])
        self.assertEqual(len(mapped["pages_observed"]), 1)
        blocks = mapped["blocks"]
        self.assertEqual([block["semantic_type"] for block in blocks], ["heading", "paragraph", "paragraph"])
        self.assertEqual(blocks[0]["semantic_level"], 1)
        self.assertEqual(blocks[0]["page_index"], 0)
        self.assertIsNone(blocks[0]["bbox_points_bottom_left"])
        self.assertEqual(mapped["metadata"]["Content-Type"], ["application/pdf"])

    def test_mapper_does_not_invent_page_identity(self):
        mapped = TIKA.map_tika_xhtml(NO_PAGE_XHTML)
        self.assertFalse(mapped["page_structure_observed"])
        self.assertEqual(mapped["pages_observed"], [])
        self.assertIsNone(mapped["blocks"][0]["page_index"])
        self.assertIsNone(mapped["blocks"][0]["bbox_points_bottom_left"])


class TikaRouteTests(unittest.TestCase):
    def test_hash_mismatch_blocks_before_java_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "fixture.pdf"
            source.write_bytes(b"%PDF-1.4\n%%EOF\n")
            jar = root / "tika.jar"
            jar.write_bytes(b"wrong")
            with mock.patch.object(TIKA, "java_version") as java_version:
                observation = TIKA.run_tika_pdf_xhtml(source, jar, CONFIG_PATH)
        self.assertEqual(observation["status"], "blocked")
        self.assertFalse(observation["tika_artifact"]["verified"])
        java_version.assert_not_called()

    def test_route_invokes_local_verified_jar_config_and_xhtml_only(self):
        captured = {}

        class Completed:
            returncode = 0
            stdout = SYNTHETIC_XHTML
            stderr = b""

        def fake_run(command, **kwargs):
            captured["command"] = command
            captured["cwd"] = Path(kwargs["cwd"])
            return Completed()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "fixture.pdf"
            source.write_bytes(b"%PDF-1.4\n%%EOF\n")
            jar = root / "tika-app-3.3.2.jar"
            jar.write_bytes(b"verified-test-placeholder")
            with mock.patch.object(
                TIKA,
                "verify_tika_jar",
                return_value={
                    "verified": True,
                    "reason": None,
                    "expected_sha512": TIKA.TIKA_APP_SHA512,
                    "actual_sha512": TIKA.TIKA_APP_SHA512,
                    "sha256": "a" * 64,
                    "bytes": jar.stat().st_size,
                },
            ), mock.patch.object(
                TIKA,
                "java_version",
                return_value={
                    "executable": "java",
                    "resolved_executable": "/usr/bin/java",
                    "version_line": 'openjdk version "21"',
                    "returncode": 0,
                    "error": None,
                },
            ), mock.patch.object(TIKA.subprocess, "run", side_effect=fake_run):
                observation = TIKA.run_tika_pdf_xhtml(source, jar, CONFIG_PATH)

        self.assertEqual(observation["status"], "success")
        self.assertEqual(observation["ocr_policy"], "explicit-no-ocr")
        command = captured["command"]
        self.assertEqual(command[0], "java")
        self.assertTrue(command[1].startswith("-Djava.io.tmpdir="))
        self.assertIn("-jar", command)
        self.assertIn("-x", command)
        self.assertTrue(any(item.startswith("--config=") for item in command))
        self.assertFalse(any(item.startswith("http://") or item.startswith("https://") for item in command))
        self.assertFalse(any(item in {"-p", "--password", "-z", "--extract"} for item in command))
        self.assertEqual(captured["cwd"].name, "work")
        self.assertFalse(observation["bbox_structure_observed"])

    def test_route_reports_missing_config_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "fixture.pdf"
            source.write_bytes(b"fixture")
            jar = root / "tika.jar"
            jar.write_bytes(b"placeholder")
            missing = root / "missing.xml"
            with mock.patch.object(
                TIKA,
                "verify_tika_jar",
                return_value={
                    "verified": True,
                    "reason": None,
                    "expected_sha512": TIKA.TIKA_APP_SHA512,
                    "actual_sha512": TIKA.TIKA_APP_SHA512,
                    "sha256": "a" * 64,
                    "bytes": jar.stat().st_size,
                },
            ), mock.patch.object(TIKA, "java_version") as java_version:
                observation = TIKA.run_tika_pdf_xhtml(source, jar, missing)
        self.assertEqual(observation["status"], "blocked")
        codes = {item["code"] for item in observation["warnings"]}
        self.assertIn("tika-config-missing", codes)
        java_version.assert_not_called()


if __name__ == "__main__":
    unittest.main()
