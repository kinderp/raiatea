from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[3]
LEGACY_NAME = "validate_module" + "_v2"
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".txt",
    ".toml",
}
IGNORED_PARTS = {".git", "node_modules", "build", "dist", "__pycache__"}


class ValidatorConsolidationTests(unittest.TestCase):
    def test_repository_has_no_legacy_validator_reference(self) -> None:
        references: list[str] = []
        for path in sorted(REPOSITORY_ROOT.rglob("*")):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            if any(part in IGNORED_PARTS for part in path.parts):
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if LEGACY_NAME in content:
                references.append(str(path.relative_to(REPOSITORY_ROOT)))
        self.assertEqual(
            [],
            references,
            "legacy validator references remain:\n" + "\n".join(references),
        )


if __name__ == "__main__":
    unittest.main()
