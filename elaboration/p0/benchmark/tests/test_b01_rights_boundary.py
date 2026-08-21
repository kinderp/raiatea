from __future__ import annotations

from pathlib import Path
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"


class B01RightsBoundaryTests(unittest.TestCase):
    def test_poppler_control_routes_never_request_nodrm_override(self):
        for filename in ["pdf_routes.py", "measure_b01.py"]:
            source = (ROUTES_DIR / filename).read_text(encoding="utf-8")
            # Ignore explanatory documentation that names the forbidden option;
            # executable argument lists/metadata must never contain the quoted
            # command-line token itself.
            self.assertNotIn('"-nodrm"', source, filename)
            self.assertNotIn("'-nodrm'", source, filename)


if __name__ == "__main__":
    unittest.main()
