from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "pedagogical-module.yml"


class EvaluatorReleaseCiArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_has_read_only_permissions_and_bounded_triggers(self) -> None:
        self.assertIn("permissions:\n  contents: read", self.workflow)
        self.assertIn('      - "prototype/pedagogical-module/**"', self.workflow)
        self.assertIn('      - ".github/workflows/pedagogical-module.yml"', self.workflow)
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn("github.event.pull_request.draft == false", self.workflow)

    def test_producer_builds_verifies_and_uploads_exact_archive(self) -> None:
        producer = self.workflow.split("  release-artifact-producer:", 1)[1].split(
            "  release-artifact-consumer:", 1
        )[0]
        self.assertIn("--release-version ci-v1", producer)
        self.assertIn("--verify /tmp/raiatea-ci-release/raiatea-evaluator-ci-v1.tar", producer)
        self.assertIn("name: raiatea-evaluator-ci-v1", producer)
        self.assertIn("path: /tmp/raiatea-ci-release/raiatea-evaluator-ci-v1.tar", producer)
        self.assertIn("retention-days: 3", producer)
        self.assertIn("compression-level: 0", producer)
        self.assertNotIn("secrets.", producer)

    def test_consumer_depends_on_artifact_and_uses_clean_verification(self) -> None:
        consumer = self.workflow.split("  release-artifact-consumer:", 1)[1]
        self.assertIn("needs: release-artifact-producer", consumer)
        self.assertIn("actions/download-artifact@", consumer)
        self.assertIn("/tmp/raiatea-ci-download", consumer)
        self.assertIn("Reject unexpected artifact payload", consumer)
        self.assertIn("--verify /tmp/raiatea-ci-download/raiatea-evaluator-ci-v1.tar", consumer)
        self.assertIn("/tmp/raiatea-ci-consumer-verify", consumer)
        self.assertNotIn("/tmp/raiatea-ci-release", consumer)
        self.assertNotIn("secrets.", consumer)

    def test_consumer_smoke_tests_all_required_static_endpoints(self) -> None:
        consumer = self.workflow.split("  release-artifact-consumer:", 1)[1]
        self.assertIn("--bind 127.0.0.1", consumer)
        self.assertIn("http://127.0.0.1:4174/index.html", consumer)
        self.assertIn("self-attention.html", consumer)
        self.assertIn("query-key-value.html", consumer)
        self.assertIn("pilot-manifest.json", consumer)
        self.assertIn("trap 'kill", consumer)

    def test_upload_and_download_actions_are_commit_pinned(self) -> None:
        for action in ("actions/upload-artifact@", "actions/download-artifact@"):
            lines = [line.strip() for line in self.workflow.splitlines() if action in line]
            self.assertTrue(lines)
            for line in lines:
                ref = line.split("@", 1)[1].split()[0]
                self.assertEqual(40, len(ref))
                self.assertTrue(all(character in "0123456789abcdef" for character in ref))


if __name__ == "__main__":
    unittest.main()
