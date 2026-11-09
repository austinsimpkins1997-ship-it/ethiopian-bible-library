import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is required to exercise the browser alignment helper")
class ReaderAlignmentTests(unittest.TestCase):
    def run_helper(self, source, english):
        script = "const a=require('./reader-alignment.js'); const rows=a.buildParallelRows(" + json.dumps(source) + "," + json.dumps(english) + "); process.stdout.write(JSON.stringify(rows));"
        result = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def test_pairs_only_unique_printed_labels(self):
        rows = self.run_helper(
            [{"unit_order": 1, "source_marker": "1", "text": "a"}, {"unit_order": 2, "source_marker": "3", "text": "b"}],
            [{"number": "1", "text": "A"}, {"number": "2", "text": "B"}, {"number": "3", "text": "C"}],
        )
        self.assertEqual([(r["source"]["text"] if r["source"] else None, r["english"]["text"] if r["english"] else None) for r in rows], [("a", "A"), ("b", "C"), (None, "B")])

    def test_duplicate_source_labels_are_not_collapsed_or_paired(self):
        rows = self.run_helper(
            [{"unit_order": 10, "source_marker": "[-]", "text": "first"}, {"unit_order": 11, "source_marker": "[-]", "text": "second"}],
            [{"number": "[-]", "text": "English"}],
        )
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["source"]["text"] for r in rows[:2]], ["first", "second"])
        self.assertTrue(all(r["english"] is None for r in rows[:2]))
        self.assertEqual(rows[2]["english"]["text"], "English")

    def test_internal_order_is_never_treated_as_a_printed_label(self):
        rows = self.run_helper(
            [{"unit_order": 1, "text": "unlabeled source"}],
            [{"number": "1", "text": "English verse one"}],
        )
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[0]["english"])
        self.assertIsNone(rows[1]["source"])


if __name__ == "__main__":
    unittest.main()
