"""Keep Pages validation on PRs and restrict deployment to validated main runs."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"


class PagesWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        validate = re.search(r"(?ms)^  validate:\n(.*?)(?=^  deploy:\n)", cls.source)
        deploy = re.search(r"(?ms)^  deploy:\n(.*)\Z", cls.source)
        if not validate or not deploy:
            raise AssertionError("Pages workflow must define separate validate and deploy jobs.")
        cls.validate_job = validate.group(1)
        cls.deploy_job = deploy.group(1)

    def test_pull_requests_run_validation_with_read_only_workflow_permissions(self):
        self.assertRegex(self.source, r"(?ms)^  pull_request:\n    branches: \[main\]")
        self.assertRegex(self.source, r"(?ms)^permissions:\n  contents: read\n\nconcurrency:")
        self.assertIn("python build_standalone.py", self.validate_job)
        self.assertIn("python -B verify_archive_manifest.py", self.validate_job)
        self.assertIn("python -B -m unittest discover -s tests -v", self.validate_job)
        self.assertIn("node tests/test_service_worker.js", self.validate_job)
        self.assertIn("node tests/test_offline_reader_cache.js", self.validate_job)
        self.assertNotIn("pages: write", self.validate_job)
        self.assertNotIn("id-token: write", self.validate_job)

    def test_deployment_waits_for_validation_and_is_limited_to_main(self):
        self.assertIn("needs: validate", self.deploy_job)
        self.assertIn(
            "if: github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main')",
            self.deploy_job,
        )
        self.assertIn("pages: write", self.deploy_job)
        self.assertIn("id-token: write", self.deploy_job)
        self.assertIn("uses: actions/deploy-pages@v4", self.deploy_job)


if __name__ == "__main__":
    unittest.main()
