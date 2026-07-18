from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class PilotAcceptanceDocumentationTests(unittest.TestCase):
    def test_manual_checklist_contains_complete_evaluator_flow(self) -> None:
        text = (ROOT / "PILOT-ACCEPTANCE.md").read_text(encoding="utf-8")
        for required in (
            "build_pilot.py",
            "python -m http.server",
            "Inizia il percorso",
            "Recupero mirato",
            "Riepilogo del percorso",
            "Esporta evidenze JSON",
            "query-key-value-evidence-v1.json",
            "Rifiuto sovrascrittura verificato",
            "Esito finale: PASS / FAIL",
            "Nessuna richiesta esterna osservata",
        ):
            self.assertIn(required, text)

    def test_acceptance_contract_preserves_product_boundaries(self) -> None:
        text = (ROOT / "docs" / "pilot-end-to-end-acceptance.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("does not add new learner behavior", text)
        self.assertIn("generated pilot files", text)
        self.assertIn("protected squash merge", text)
        self.assertIn("parent #58 closed", text)


if __name__ == "__main__":
    unittest.main()
