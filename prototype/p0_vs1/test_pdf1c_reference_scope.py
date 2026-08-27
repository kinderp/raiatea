from __future__ import annotations

import unittest
from unittest.mock import patch

from prototype.p0_vs1 import docling_reference


class Pdf1cReferenceScopeTests(unittest.TestCase):
    def test_installed_freeze_reads_only_constrained_package_names(self) -> None:
        calls: list[str] = []

        def version(name: str) -> str:
            calls.append(name)
            return {"docling": "2.118.0", "numpy": "2.0.0"}[name]

        expected = ["docling==2.118.0", "numpy==2.0.0"]
        with patch.object(docling_reference.importlib.metadata, "version", side_effect=version):
            observed = docling_reference.installed_freeze(expected)
        self.assertEqual(observed, expected)
        self.assertEqual(calls, ["docling", "numpy"])
        self.assertNotIn("pip", calls)
        self.assertNotIn("setuptools", calls)


if __name__ == "__main__":
    unittest.main()
