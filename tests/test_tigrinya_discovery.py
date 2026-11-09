import copy
import unittest

from build_tigrinya_discovery import EDITION_LEADS, SOURCES, apply


class TigrinyaDiscoveryTests(unittest.TestCase):
    def make_archive(self):
        return {
            "sources": [],
            "translation_registry": {
                "edition_leads": [],
                "languages": [{
                    "language_tag": "ti",
                    "language_name": "Tigrinya (ትግርኛ)",
                    "source_ids": [],
                    "availability_survey": {"notes": "Bible.com count remains two."},
                }],
            },
        }

    def test_metadata_is_scoped_and_rights_do_not_claim_reuse(self):
        archive = self.make_archive()
        apply(archive)
        leads = archive["translation_registry"]["edition_leads"]
        lead_ids = {lead["edition_id"] for lead in leads}
        self.assertEqual(lead_ids, {lead["edition_id"] for lead in EDITION_LEADS})
        self.assertEqual(len(leads), 10)
        added_catalogue_leads = {
            lead["edition_id"]: lead for lead in leads
            if lead["edition_id"] in {
                "tigrinya-eritrea-revised-deuterocanon-2000",
                "tigrinya-eritrea-cldc032-retail-2010",
            }
        }
        self.assertEqual(set(added_catalogue_leads), {
            "tigrinya-eritrea-revised-deuterocanon-2000",
            "tigrinya-eritrea-cldc032-retail-2010",
        })
        self.assertEqual(added_catalogue_leads["tigrinya-eritrea-revised-deuterocanon-2000"]["source_ids"], ["SRC-438", "SRC-439"])
        self.assertEqual(added_catalogue_leads["tigrinya-eritrea-cldc032-retail-2010"]["source_ids"], ["SRC-440"])
        for lead in added_catalogue_leads.values():
            self.assertFalse(lead["text_bundled"])
            self.assertIsNone(lead["candidate_canon_id"])
            self.assertEqual(lead["rights_classification"], "unknown")
        genesis = next(lead for lead in leads if "Genesis Portion" in lead["title"])
        pdf = next(lead for lead in leads if lead["edition_id"] == "tigrinya-common-language-bible-dbs-pdf-tirtbi")
        eritrea_bible = next(lead for lead in leads if "whole-Bible product records" in lead["title"])
        self.assertFalse(any(lead["text_bundled"] for lead in leads))
        self.assertEqual(genesis["rights_classification"], "unknown")
        self.assertEqual(pdf["rights_classification"], "permission_limited")
        self.assertIn("27 New Testament", pdf["scope_description"])
        self.assertIsNone(pdf["candidate_canon_id"])
        self.assertEqual(eritrea_bible["rights_classification"], "unknown")
        self.assertIsNone(eritrea_bible["candidate_canon_id"])
        self.assertEqual(eritrea_bible["mapping_state"], "not_mapped")
        self.assertIn("81-book mapping", eritrea_bible["scope_description"])
        contemporary = next(lead for lead in leads if lead["edition_id"] == "tigrinya-contemporary-bible-city-bible-2024")
        app_claim = next(lead for lead in leads if lead["edition_id"] == "tigrinya-app-66-book-site-claim")
        self.assertFalse(contemporary["text_bundled"])
        self.assertIsNone(contemporary["candidate_canon_id"])
        self.assertEqual(contemporary["rights_classification"], "all_rights_reserved")
        source_by_id = {source["source_id"]: source for source in SOURCES}
        self.assertIn("all rights reserved worldwide", source_by_id["SRC-370"]["rights_status"].lower())
        self.assertIn("does not grant", source_by_id["SRC-370"]["rights_status"])
        self.assertIn("no Ethiopian or Eritrean Orthodox canon crosswalk", contemporary["scope_description"])
        self.assertTrue({"SRC-369", "SRC-370"}.issubset(contemporary["source_ids"]))
        self.assertFalse(app_claim["text_bundled"])
        self.assertIsNone(app_claim["candidate_canon_id"])
        self.assertIn("HTML shell", app_claim["scope_description"])
        self.assertEqual(app_claim["rights_classification"], "unknown")
        self.assertIn("remain unknown", source_by_id["SRC-371"]["rights_status"])
        self.assertIn("underlying scripture text", source_by_id["SRC-407"]["inspection_and_limitations"])
        self.assertIn("application", source_by_id["SRC-407"]["rights_status"])
        github_xml = source_by_id["SRC-355"]
        self.assertEqual(github_xml["rights_classification"], "permission_limited")
        self.assertIn("limited HTTP range read", github_xml["inspection_and_limitations"])
        self.assertIn("embeds a Bible.com link to version TIG24", github_xml["inspection_and_limitations"])
        self.assertIn("contradicts", github_xml["inspection_and_limitations"])
        self.assertIn("MIT", github_xml["rights_status"])
        self.assertIn("all rights reserved", github_xml["rights_status"].lower())
        self.assertNotIn("Public Domain", github_xml["rights_status"])
        self.assertEqual(app_claim["source_ids"], ["SRC-371", "SRC-407"])
        self.assertIn("all 66 Old and New Testament books", app_claim["edition_statement"])
        self.assertIn("not equated with the Ethiopian/Eritrean Orthodox 81-entry list", app_claim["scope_description"])
        self.assertIn("underlying Bible text", app_claim["rights_status"])
        notes = archive["translation_registry"]["languages"][0]["availability_survey"]["notes"]
        self.assertIn("XML header for AmharicTigrinya2024Bible.xml was inspected", notes)
        self.assertIn("No text is copied", notes)
        self.assertTrue({"SRC-331", "SRC-332", "SRC-333", "SRC-334"}.issubset(
            archive["translation_registry"]["languages"][0]["source_ids"]
        ))
        self.assertTrue({"SRC-369", "SRC-370", "SRC-371", "SRC-407"}.issubset(
            archive["translation_registry"]["languages"][0]["source_ids"]
        ))
        self.assertEqual(len(archive["sources"]), len(SOURCES))

    def test_apply_is_idempotent(self):
        archive = self.make_archive()
        apply(archive)
        first = copy.deepcopy(archive)
        apply(archive)
        self.assertEqual(archive, first)

    def test_revised_eritrea_bible_remains_metadata_only_and_unmapped(self):
        lead = next(item for item in EDITION_LEADS if item["edition_id"] == "tigrinya-revised-bible-eritrea-1998")
        self.assertFalse(lead["text_bundled"])
        self.assertIsNone(lead["candidate_canon_id"])
        self.assertEqual(lead["mapping_state"], "not_mapped")
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertEqual(lead["source_ids"], ["SRC-333", "SRC-334"])


if __name__ == "__main__":
    unittest.main()

