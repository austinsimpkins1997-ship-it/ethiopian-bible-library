import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RebuildInstructionsTests(unittest.TestCase):
    def test_readme_rebuild_commands_match_pages_workflow_and_root_files(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        workflow_start = workflow.index("- name: Rebuild source-backed readers")
        workflow_end = workflow.index("- name: Require committed build outputs", workflow_start)
        workflow_block = workflow[workflow_start:workflow_end]
        workflow_commands = []
        for line in workflow_block.splitlines():
            command = line.strip()
            if command.startswith("run: "):
                command = command[5:].strip()
            if command.startswith(("python ", "node ")):
                workflow_commands.append(command)

        readme_match = re.search(
            r"(?ms)^## Rebuild and verify the embedded site\s+.*?```powershell\s*\n(.*?)\n```",
            readme,
        )
        self.assertIsNotNone(readme_match, "README must provide a PowerShell rebuild block.")
        readme_commands = [line.strip() for line in readme_match.group(1).splitlines() if line.strip()]
        self.assertEqual(readme_commands, workflow_commands)

        for command in workflow_commands:
            parts = command.split()
            if parts[0] == "python":
                script = next((part for part in parts[1:] if part.endswith(".py")), None)
                if script:
                    self.assertTrue((ROOT / script).is_file(), f"Missing root-level script: {command}")
                else:
                    self.assertIn("-m unittest discover -s tests", command)

        self.assertNotIn("python build_wisdom_solomon_research_reader.py", workflow_commands)


if __name__ == "__main__":
    unittest.main()
