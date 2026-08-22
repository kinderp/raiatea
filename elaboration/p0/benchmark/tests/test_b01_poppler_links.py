from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location("p0_pdf_link_routes", ROUTES_DIR / "pdf_routes.py")
ROUTES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ROUTES)

PDF2XML_WITH_LINK = b'''<?xml version="1.0" encoding="UTF-8"?>
<pdf2xml producer="poppler" version="24.02.0">
<page number="1" position="absolute" top="0" left="0" height="1188" width="918">
<text top="668" left="108" width="282" height="18"><a href="https://example.invalid/raiatea-benchmark">Raiatea benchmark link</a></text>
</page></pdf2xml>'''


class PopplerExplicitLinkTests(unittest.TestCase):
    def test_pdftohtml_preserves_explicit_uri_target_and_anchor_text(self):
        temp = tempfile.TemporaryDirectory()
        work = Path(temp.name) / "work"
        work.mkdir()
        (work / "out.xml").write_bytes(PDF2XML_WITH_LINK)
        metadata = {
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "duration_seconds": 0.001,
            "command_options": [
                "-xml", "-hidden", "-q",
                str(Path(temp.name) / "input" / "fixture.pdf"),
                str(work / "out"),
            ],
            "generated_files": ["out.xml"],
            "side_effect_files": [],
            "controlled_parent": True,
            "os_level_sandbox": False,
            "network_instrumentation": "not-measured",
            "_temporary_directory": temp,
        }
        with mock.patch.object(ROUTES, "_controlled_run", return_value=(work, metadata)), mock.patch.object(
            ROUTES, "_pdfinfo_page_sizes", return_value={0: (612.0, 792.0)}
        ):
            observation = ROUTES.run_pdftohtml_xml(Path("fixture.pdf"))

        self.assertEqual(observation["status"], "success")
        self.assertEqual(
            observation["links"],
            [
                {
                    "kind": "uri",
                    "target": "https://example.invalid/raiatea-benchmark",
                    "from_text": "Raiatea benchmark link",
                    "page_index": 0,
                    "source": "pdftohtml-explicit-anchor",
                }
            ],
        )

    def test_pdftotext_route_does_not_claim_link_collection(self):
        self.assertNotIn(
            '"links": []',
            ROUTES.run_pdftotext_bbox_layout.__code__.co_consts,
        )


if __name__ == "__main__":
    unittest.main()
