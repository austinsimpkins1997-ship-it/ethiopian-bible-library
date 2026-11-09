import json
import unittest
import zipfile

from build_brenton_octateuch import PACKAGE, USFM_MEMBER, parse_usfm, sha256


class BrentonPsalmsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package_bytes = PACKAGE.read_bytes()
        with zipfile.ZipFile(PACKAGE) as source:
            cls.raw = source.read(USFM_MEMBER["PSA"])
        cls.parsed = parse_usfm(cls.raw, "PSA", USFM_MEMBER["PSA"], sha256(cls.package_bytes))

    def test_selected_usfm_member_and_measured_structure(self):
        manifest = json.loads((PACKAGE.parent / "capture-manifest.json").read_text(encoding="utf-8"))
        selected = manifest["selected_members"][USFM_MEMBER["PSA"]]
        self.assertEqual(selected["sha256"], sha256(self.raw))
        self.assertEqual(selected["byte_length"], len(self.raw))
        self.assertEqual(self.parsed["chapter_count"], 151)
        self.assertEqual(self.parsed["unit_count"], 2535)
        self.assertEqual(self.parsed["structural_marker_counts"], {"p": 520, "d": 150, "p_inline_text_segments": 88})
        self.assertEqual(self.parsed["continuation_segment_count"], 88)

    def test_descriptive_title_and_unlabelled_paragraph_text_remain_distinct(self):
        chapter = self.parsed["chapters"][9]
        first = chapter["verses"][0]
        self.assertEqual(first["number"], "1")
        self.assertEqual(first["source_markers_before"], ["d"])
        self.assertEqual(first["continuations"], [{
            "source_marker": "p",
            "text": "In the Lord I have put my trust: how will ye say to my soul, Flee to the mountains as a sparrow?",
        }])
        self.assertTrue(all(note.get("text") for note in chapter["notes"]))

    def test_bundled_psalms_layer_is_not_claimed_as_verified_translation(self):
        reader = json.loads((PACKAGE.parent.parent.parent / "psalms-geez-ludolf.json").read_text(encoding="utf-8"))
        companion = reader["parallel_translation"]
        self.assertEqual(companion["source_member"], USFM_MEMBER["PSA"])
        self.assertIn("unverified", companion["verification_status"])
        self.assertEqual(companion["language_tag"], "en")
        self.assertEqual(reader["reader_id"], "psalms-geez-ludolf-hacohen")


if __name__ == "__main__":
    unittest.main()
