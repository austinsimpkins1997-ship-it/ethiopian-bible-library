import json
from pathlib import Path
import unittest

from build_review_coverage import build_summary, render_html


ROOT = Path(__file__).resolve().parents[1]


class ReviewCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads((ROOT / "examples" / "archive-graph-registered-layers.json").read_text(encoding="utf-8"))
        cls.summary = build_summary(cls.graph)

    def test_summary_preserves_event_and_layer_denominators(self):
        self.assertEqual(self.summary["layer_count"], len(self.graph["layers"]))
        self.assertEqual(self.summary["review_event_count"], len(self.graph["review_events"]))
        for dimension in self.summary["dimensions"]:
            self.assertLessEqual(dimension["distinct_layer_count"], dimension["event_count"])

    def test_summary_counts_events_by_state_and_does_not_invent_reviewer_names(self):
        events = self.graph["review_events"]
        self.assertEqual(
            sum(sum(item["state_counts"].values()) for item in self.summary["dimensions"]),
            len(events),
        )
        named = sum(bool(event.get("reviewer")) for event in events)
        self.assertEqual(self.summary["events_with_named_reviewer"], named)

    def test_unresolved_review_states_remain_visible_with_scope_warning(self):
        states = {
            state
            for dimension in self.summary["dimensions"]
            for state in dimension["state_counts"]
        }
        self.assertTrue({"unknown", "not_checked"} & states)
        html = render_html(self.summary)
        self.assertIn("does not establish completeness, accuracy, canon identity", html)
        self.assertIn("download this summary as JSON", html)

    def test_translation_basis_paths_are_counted_without_inferring_unknowns(self):
        translations = [layer for layer in self.graph["layers"] if layer["layer_type"] == "translation"]
        documented = sum(
            isinstance(layer.get("basis_path"), list) and len(layer["basis_path"]) >= 2
            for layer in translations
        )
        traceability = self.summary["translation_traceability"]
        self.assertEqual(traceability["translation_layer_count"], len(translations))
        self.assertEqual(traceability["basis_path_counts"].get("documented", 0), documented)
        self.assertEqual(traceability["basis_path_counts"].get("unknown", 0), len(translations) - documented)
        self.assertEqual(
            sum(row["layer_count"] for row in traceability["language_script_counts"]),
            len(self.graph["layers"]),
        )
        self.assertEqual(
            sum(row["translation_layer_count"] for row in traceability["language_script_counts"]),
            len(translations),
        )
        self.assertIn("not inferred from the output language", traceability["interpretation_limit"])

    def test_built_review_coverage_files_match_the_graph(self):
        built = json.loads((ROOT / "examples" / "review-coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(built, self.summary)
        page = (ROOT / "research" / "review-coverage.html").read_text(encoding="utf-8")
        self.assertIn(f"{self.summary['review_event_count']}</strong> recorded review events", page)


if __name__ == "__main__":
    unittest.main()
