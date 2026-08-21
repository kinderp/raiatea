from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


BENCH_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("p0_generate_fixtures", BENCH_DIR / "generate_fixtures.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


class BenchmarkHarnessTests(unittest.TestCase):
    def setUp(self):
        self.fixture_manifest = json.loads(
            (BENCH_DIR / "manifests" / "fixtures.json").read_text(encoding="utf-8")
        )
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )

    def test_internal_contracts_are_not_public_p0_schema(self):
        self.assertEqual(
            self.fixture_manifest["contract"]["scope"], "benchmark-evidence-only"
        )
        self.assertFalse(self.fixture_manifest["contract"]["public_p0_schema"])
        self.assertEqual(self.gold["contract"]["scope"], "benchmark-evidence-only")
        self.assertFalse(self.gold["contract"]["public_p0_schema"])

    def test_rights_fail_closed_without_redistribution_license(self):
        self.assertEqual(
            self.fixture_manifest["rights_gate"]["redistribution"], "not-established"
        )
        self.assertEqual(self.fixture_manifest["rights_gate"]["decision_issue"], 131)
        for fixture in self.fixture_manifest["fixtures"]:
            self.assertEqual(fixture["rights"]["redistribution"], "not-established")
            self.assertFalse(fixture["rights"]["public_rights_safe"])
            self.assertEqual(fixture["rights"]["remote_provider"], "denied")

    def test_epub_gold_has_no_canonical_page_geometry(self):
        forbidden = {"page", "page_number", "page_index", "bbox", "polygon"}
        for fixture_id, fixture_gold in self.gold["fixtures"].items():
            if not fixture_id.startswith("B02-"):
                continue
            self.assertTrue(
                fixture_gold["coordinate_semantics"]["kind"].startswith("epub-")
            )
            self.assertFalse(
                fixture_gold["coordinate_semantics"]["canonical_rendered_pages"]
            )
            self.assertTrue(forbidden.isdisjoint(set(_walk_keys(fixture_gold))))

    def test_generation_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_result = MODULE.generate_all(Path(first))
            second_result = MODULE.generate_all(Path(second))
            first_hashes = {item["id"]: item["sha256"] for item in first_result["generated"]}
            second_hashes = {item["id"]: item["sha256"] for item in second_result["generated"]}
            self.assertEqual(first_hashes, second_hashes)

    def test_generated_pdf_basics(self):
        with tempfile.TemporaryDirectory() as tmp:
            MODULE.generate_all(Path(tmp))
            for filename, markers in {
                "B01-PDF-001.pdf": [
                    b"%PDF-1.4",
                    b"Raiatea B01 PDF 001",
                    b"Alpha paragraph preserves exact benchmark text.",
                ],
                "B01-PDF-002.pdf": [
                    b"%PDF-1.4",
                    b"Raiatea B01 PDF 002",
                    b"Left one.",
                    b"Right one.",
                ],
            }.items():
                data = (Path(tmp) / filename).read_bytes()
                self.assertTrue(data.startswith(b"%PDF-1.4"))
                self.assertIn(b"/Type /Page", data)
                self.assertIn(b"%%EOF", data)
                for marker in markers:
                    self.assertIn(marker, data)

    def test_generated_epub_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            MODULE.generate_all(Path(tmp))
            for filename in [
                "B02-EPUB-001.epub",
                "B02-EPUB-002.epub",
                "B02-EPUB-NEG-001.epub",
                "B02-EPUB-NEG-002.epub",
            ]:
                path = Path(tmp) / filename
                with zipfile.ZipFile(path) as zf:
                    infos = zf.infolist()
                    self.assertEqual(infos[0].filename, "mimetype")
                    self.assertEqual(infos[0].compress_type, zipfile.ZIP_STORED)
                    self.assertEqual(zf.read("mimetype"), b"application/epub+zip")
                    names = set(zf.namelist())
                    self.assertIn("META-INF/container.xml", names)
                    self.assertIn("OEBPS/package.opf", names)
                    self.assertIn("OEBPS/nav.xhtml", names)
                    self.assertIn("OEBPS/ch1.xhtml", names)
                    self.assertIn("OEBPS/ch2.xhtml", names)

    def test_navigation_fixture_has_cross_resource_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            MODULE.generate_all(Path(tmp))
            with zipfile.ZipFile(Path(tmp) / "B02-EPUB-002.epub") as zf:
                ch1 = zf.read("OEBPS/ch1.xhtml").decode("utf-8")
                nav = zf.read("OEBPS/nav.xhtml").decode("utf-8")
                self.assertIn('href="ch2.xhtml#details"', ch1)
                self.assertIn('href="ch2.xhtml#details"', nav)

    def test_active_content_fixture_is_inert_benchmark_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            MODULE.generate_all(Path(tmp))
            with zipfile.ZipFile(Path(tmp) / "B02-EPUB-NEG-001.epub") as zf:
                ch1 = zf.read("OEBPS/ch1.xhtml").decode("utf-8")
                self.assertIn("<script", ch1)
                self.assertIn("__raiatea_inert_fixture", ch1)
                self.assertNotIn("<script src=", ch1)
                self.assertNotIn("fetch(", ch1)
                self.assertNotIn("XMLHttpRequest", ch1)
                script_body = ch1.split("<script", 1)[1].split("</script>", 1)[0]
                self.assertNotIn("http://", script_body)
                self.assertNotIn("https://", script_body)

    def test_unsafe_path_fixture_is_never_extracted_by_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            MODULE.generate_all(root)
            epub_path = root / "B02-EPUB-NEG-002.epub"
            with zipfile.ZipFile(epub_path) as zf:
                self.assertIn("../outside.txt", zf.namelist())
            self.assertFalse((root.parent / "outside.txt").exists())
            self.assertFalse((root / "outside.txt").exists())

    def test_generated_manifest_records_fingerprints_and_rights(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = MODULE.generate_all(Path(tmp))
            self.assertFalse(result["contract"]["public_p0_schema"])
            self.assertEqual(len(result["generated"]), len(self.fixture_manifest["fixtures"]))
            for item in result["generated"]:
                self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(item["bytes"], 0)
                self.assertEqual(item["rights"]["redistribution"], "not-established")


if __name__ == "__main__":
    unittest.main()
