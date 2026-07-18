from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import validate_module_v2 as canonical_loader  # noqa: E402


class CanonicalModuleLoaderTests(unittest.TestCase):
    def test_all_examples_load_through_canonical_identity_contract(self) -> None:
        for path in sorted((ROOT / "examples").glob("*.json")):
            if path.name.endswith(".layout.json"):
                continue
            with self.subTest(path=path.name):
                module = canonical_loader.load_and_validate(path)
                self.assertEqual(1, module["revision"])
                self.assertEqual(
                    len(module["steps"]),
                    len({step["id"] for step in module["steps"]}),
                )

    def test_loader_rejects_identity_failure_after_layered_validation(self) -> None:
        source = ROOT / "examples" / "self-attention.json"
        module = json.loads(source.read_text(encoding="utf-8"))
        del module["revision"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "module.json"
            path.write_text(json.dumps(module), encoding="utf-8")
            with self.assertRaises(canonical_loader.ModuleValidationError) as context:
                canonical_loader.load_and_validate(path)
        self.assertIn(
            "$.revision: required field is missing",
            [str(issue) for issue in context.exception.issues],
        )


if __name__ == "__main__":
    unittest.main()
