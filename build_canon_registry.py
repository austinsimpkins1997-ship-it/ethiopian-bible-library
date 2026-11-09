"""Build the Church-list coverage index without treating catalogue rows as canon units."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "canon-registry.json"
SOURCE_TRANSCRIPTION = ROOT / "research" / "eotc-english-canon-source-transcription.json"

OT = [
    ("Genesis", ["eotc-001"]), ("Exodus", ["eotc-002"]),
    ("Leviticus", ["eotc-003"]), ("Numbers", ["eotc-004"]),
    ("Deuteronomy", ["eotc-005"]), ("Joshua", ["eotc-006"]),
    ("Judges", ["eotc-007"]), ("Ruth", ["eotc-008"]),
    ("I and II Samuel", ["eotc-009", "eotc-010"]),
    ("I and II Kings", ["eotc-011", "eotc-012"]),
    ("I Chronicles", ["eotc-013"]), ("II Chronicles", ["eotc-014"]),
    ("Jubilees", ["eotc-015"]), ("Enoch", ["eotc-016"]),
    ("Ezra and Nehemia", ["eotc-017", "eotc-018"]),
    ("Ezra (2nd) and Ezra Sutuel", ["eotc-090", "eotc-019"]),
    ("Tobit", ["eotc-020"]), ("Judith", ["eotc-021"]),
    ("Esther", ["eotc-022"]),
    ("I Maccabees", ["eotc-023"]),
    ("II and III Maccabees", ["eotc-024", "eotc-025"]),
    ("Job", ["eotc-026"]), ("Psalms", ["eotc-027"]),
    ("Proverbs", ["eotc-029"]), ("Tegsats (Reproof)", ["eotc-030"]),
    ("Metsihafe Tibeb (books of wisdom)", ["eotc-031"]),
    ("Ecclesiastes", ["eotc-032"]), ("Song of Songs", ["eotc-028"]),
    ("Isaiah", ["eotc-033"]),
    ("Jeremiah", ["eotc-034", "eotc-035", "eotc-036", "eotc-037", "eotc-038"]),
    ("Ezekiel", ["eotc-039"]), ("Daniel", ["eotc-040"]),
    ("Hosea", ["eotc-041"]), ("Amos", ["eotc-042"]),
    ("Micah", ["eotc-043"]), ("Joel", ["eotc-044"]),
    ("Obadiah", ["eotc-045"]), ("Jonah", ["eotc-046"]),
    ("Nahum", ["eotc-047"]), ("Habakkuk", ["eotc-048"]),
    ("Zephaniah", ["eotc-049"]), ("Haggai", ["eotc-050"]),
    ("Zechariah", ["eotc-051"]), ("Malachi", ["eotc-052"]),
    ("Book of Joshua the Son of Sirac", ["eotc-053"]),
    ("Book of Josephas the Son of Bengorion", ["eotc-054"]),
]

NT_NAMES = [
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "I Corinthians",
    "II Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "I Thessalonians", "II Thessalonians", "I Timothy", "II Timothy", "Titus",
    "Philemon", "Hebrews", "I Peter", "II Peter", "I John", "II John",
    "III John", "James", "Jude", "Revelation", "Sirate Tsion (Book of Order)",
    "Tizaz (Book of Herald)", "Gitsew", "Abtilis", "I Book of Dominos",
    "II Book of Dominos", "Book of Clement", "Didascalia",
]
# Catalogue display order puts James before the Johannine and Petrine letters,
# while the Church's 81-entry list places James after III John. Keep this
# crosswalk explicit; arithmetic IDs silently attached six wrong titles.
NT_CATALOGUE_IDS = {
    20: "eotc-075",  # I Peter
    21: "eotc-076",  # II Peter
    22: "eotc-077",  # I John
    23: "eotc-078",  # II John
    24: "eotc-079",  # III John
    25: "eotc-074",  # James
}
NT_READER_IDS = {
    1: "matthew-betamasaheft-tei",
    2: "mark-betamasaheft-tei-research",
    3: "luke-betamasaheft-tei",
    4: "john-betamasaheft-tei",
    5: "acts-betamasaheft-tei",
    6: "romans-betamasaheft-tei",
    19: "hebrews-betamasaheft-tei",
    25: "james-betamasaheft-tei",
    27: "revelation-betamasaheft-tei",
    7: "first-corinthians-betamasaheft-tei",
    8: "second-corinthians-betamasaheft-tei",
    9: "galatians-betamasaheft-tei",
    10: "ephesians-betamasaheft-tei",
    11: "philippians-betamasaheft-tei",
    12: "colossians-betamasaheft-tei",
    13: "first-thessalonians-betamasaheft-tei",
    14: "second-thessalonians-betamasaheft-tei",
    15: "first-timothy-betamasaheft-tei",
    16: "second-timothy-betamasaheft-tei",
    17: "titus-betamasaheft-tei",
    20: "first-peter-betamasaheft-tei",
    21: "second-peter-betamasaheft-tei",
    22: "first-john-betamasaheft-tei",
}
NT_READER_FILES = {
    1: "matthew-betamasaheft-tei.json",
    2: "mark-research-tei.json",
    3: "luke-betamasaheft-tei.json",
    4: "john-betamasaheft-tei.json",
    5: "acts-betamasaheft-tei.json",
    6: "romans-betamasaheft-tei.json",
    19: "hebrews-betamasaheft-tei.json",
    25: "james-betamasaheft-tei.json",
    27: "revelation-betamasaheft-tei.json",
    7: "first-corinthians-betamasaheft-tei.json",
    8: "second-corinthians-betamasaheft-tei.json",
    9: "galatians-betamasaheft-tei.json",
    10: "ephesians-betamasaheft-tei.json",
    11: "philippians-betamasaheft-tei.json",
    12: "colossians-betamasaheft-tei.json",
    13: "first-thessalonians-betamasaheft-tei.json",
    14: "second-thessalonians-betamasaheft-tei.json",
    15: "first-timothy-betamasaheft-tei.json",
    16: "second-timothy-betamasaheft-tei.json",
    17: "titus-betamasaheft-tei.json",
    20: "first-peter-betamasaheft-tei.json",
    21: "second-peter-betamasaheft-tei.json",
    22: "first-john-betamasaheft-tei.json",
}
REVIEWED_TITLE_METADATA = {
    15: {
        'source_ids': ['SRC-029', 'SRC-034', 'SRC-097', 'SRC-100', 'SRC-361'],
        'mapping_state': 'reviewed_match',
        'reader_status': 'Historical Geʽez Ezra–Nehemiah edition and 23 TAU menu pages documented; no local reader text bundled, and print completeness is unverified.',
        'mapping_note': "Reviewed work/title match: the Church list groups ‘Ezra and Nehemia’; TAU identifies Pereira's Ethiopic Ezrâ III as the canonical book containing Ezra and Nehemiah. Its index exposes 23 numbered menu links, but this is not an audit of the pages against the print edition, proof of completeness, or a match to a current EOTC edition. No text or images are bundled.",
    },
    13: {'source_ids': ['SRC-029', 'SRC-041'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names ‘Jublee’ and its accompanying prose refers to the book of Jubilee; the pinned Beta maṣāḥǝft work record is titled Book of Jubilees. The selected Ran transcription is a work-level match only; it is not the separate EOTC-printed edition in the parent TEI record, which remains withheld pending rights review. Textual accuracy and completeness are not established."},
    14: {'source_ids': ['SRC-029', 'SRC-065', 'SRC-066'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Enoch; the pinned Beta maṣāḥǝft work record is 1 Enoch and its selected EOTCed division is labeled ‘Text of the EOTC printed Bible.’ This matches the named work only; the physical print exemplar and date, transcription accuracy, and completeness remain unverified."},
    37: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-153', 'SRC-186'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Obadiah; TAU's index uses the Latin form Abdias, and the linked book-specific page identifies the Ethiopic Book of Obadiah. This matches the named biblical work only; Bachmann's 1892 critical edition transcription is not identified as a current EOTC printed edition and its text has not been freshly collated."},
    23: {'source_ids': ['SRC-029', 'SRC-067', 'SRC-068'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Psalms; TAU's Ethiopic Bible index lists Psalmus under Psalterium Davidis and its accompanying notes identify the Ethiopic Psalter digitization. This supports the Psalms/Psalter work link only. Rahlfs numbering, extent, and alignment with any current EOTC printed edition are separate and unverified."},
    32: {'source_ids': ['SRC-029', 'SRC-282'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Daniel and the pinned Beta maṣāḥǝft TEI identifies the Geʽez work as Daniel, with an edition division labeled ‘Text of the EOTC printed Bible.’ This matches the named work only; exact print exemplar, internal component boundaries, completeness, and transcription accuracy remain unverified."},
    34: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-151', 'SRC-193'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list and TAU's Ethiopic index both use Amos, and the TAU book page identifies the Ethiopic Book of Amos. This matches the work title only; Pereira's historical witness is not identified as the current EOTC printed edition and transcription accuracy/completeness remain unverified."},
    36: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-149', 'SRC-192'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Joel; TAU's index gives the Latinized form Ioel, and its book page identifies the Ethiopic Book of Joel. This is a title/work match only; Dillmann's historical witness, label anomalies, accuracy, and completeness are not thereby certified as the current Church text."},
    38: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-156', 'SRC-187'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Jonah; TAU's index gives the Latinized form Ionas and its book-specific page identifies the Ethiopic Book of Jonah. This is a title/work match only; the historical critical-edition transcription is not identified as the current Church print text and its accuracy/completeness remain unverified."},
    39: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-155', 'SRC-188'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list and TAU's index both name Nahum, and TAU's book page identifies an Ethiopic Nahum transcription. This title/work match does not identify the historical critical-edition transcription with a current EOTC printed edition or verify its accuracy/completeness."},
    40: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-157', 'SRC-189'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Habakkuk; TAU's index uses the Latinized form Habacuc and its book page identifies the Ethiopic Book of Habakkuk. This matches the work title only; the historical witness, current edition identity, numbering equivalence, transcription accuracy, and completeness remain unverified."},
    41: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-157', 'SRC-158', 'SRC-190'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Zephaniah; TAU's index uses the Latinized form Sophonias and its book page identifies the Ethiopic Book of Zephaniah. This matches the work title only; the historical witness is not identified as the current EOTC printed edition and accuracy/completeness remain unverified."},
    42: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-157', 'SRC-160', 'SRC-191'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Haggai; TAU's index uses the Latinized form Aggaeus and its book page identifies the Ethiopic Book of Haggai. This matches the work title only; the historical witness is not identified as the current EOTC printed edition and accuracy/completeness remain unverified."},
    44: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-161', 'SRC-195'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Malachi; TAU's index uses the Latinized form Malachias and its book-specific page identifies the Ethiopic Book of Malachi. This is a title/work match only; the historical witness, current edition identity, transcription accuracy, and completeness remain unverified."},
    45: {'source_ids': ['SRC-029', 'SRC-034', 'SRC-098', 'SRC-101', 'SRC-318', 'SRC-348'], 'mapping_note': "Reviewed work/title crosswalk: the Church list calls entry 45 ‘Book of Joshua the Son of Sirac.’ Cambridge’s scholarly excerpt explicitly identifies ‘Jesus (Joshua), Son of Sirach’ as also known as Wisdom of Sirach and Ecclesiasticus; TAU identifies its Geʽez digital witness as Ecclesiasticus / Wisdom of the Son of Sirach. This establishes a bounded title/work-family match only. It does not establish recension, the exact current EOTC printed edition, Dillmann 1894’s canonical authority, completeness, or transcription accuracy."},
}
NT_SOURCE_METADATA = {
    29: {
        "source_ids": ["SRC-029", "SRC-073", "SRC-210", "SRC-211", "SRC-213", "SRC-368", "SRC-441"],
        "mapping_state": "uncertain",
        "reader_status": "No reader bundled. Cowley and Mikre-Sellassie link Te'ezaz to Horner 1904, and TAU labels its page images Te'ezaz; exact reconciliation with the Church-list gloss, manuscript boundaries, completeness, and rights remains unresolved.",
        "mapping_note": "The Church list names Tizaz (Book of Herald). Cowley reports Te'ezaz as a Sinodos section of 71 or 72 canons and says it was printed in Horner 1904; Mikre-Sellassie reports 71 and cites Horner. TAU identifies its hosted Ge'ez page images as the Te'ezaz section following Horner. Horner's contents separately locate an English translation of the Ethiopic at pp. 127–232, but this section of the broader Statutes volume is not verified as the boundary of the Church-list Tizaz entry. These sources support a provisional title/edition association, but the differing gloss/spelling, manuscript variation, and 71/72 count are not reconciled against a Church text witness. The Horner scan is not the Ge'ez witness. No text or images are bundled; completeness, accuracy, and reuse rights are unverified.",
    },
    34: {
        "source_ids": ["SRC-029", "SRC-073", "SRC-207"],
        "mapping_state": "uncertain",
        "reader_status": "No canon-linked reader bundled; a related Ethiopic seven-book Qälementos and complementary French/Italian translations are documented, but exact identity with this Church-list entry remains uncertain and no text is bundled.",
        "mapping_note": "Bausi (2024) identifies the Ethiopic Maṣḥafa Qalemǝnṭos (Book of Clement; CAe 1957) and distinguishes it from the Ethiopic Apocalypse of Peter and from a separate count of three Epistles of Clement. The name overlap makes it a plausible candidate for this English Church-list label, but the Church page gives no Geʽez title and Bausi does not establish this exact list crosswalk. No reader is bundled.",
    },
    30: {
        "source_ids": ["SRC-029", "SRC-073", "SRC-211", "SRC-284"],
        "mapping_note": "The Church list names Gitsew. The Ethiopian Orthodox Bible Project reports acquiring a Geʽez/Amharic Gitsew book in 2017 and calls it one of four Sinodos books; this is a secondary acquisition report, not an inspected witness. Lexham and Asale use the form Gessew in discussing Sinodos, but manuscript contents and title relations vary. Candidate title link only; edition, text, boundaries, completeness, accuracy, and reuse rights are unverified. No reader is bundled.",
    },
    31: {
        "source_ids": ["SRC-029", "SRC-073", "SRC-210", "SRC-211", "SRC-285"],
        "mapping_note": "The Church list names Abtilis. Beta maṣāḥǝft catalogs Apostolic canons Abṭelisāt (81), CAe 2677; one manuscript record labels an 81-canon first recension while another witness records an 80-canon second recension. The same catalogue distinguishes the separately recorded Apostolic canons (56), CAe 2670. This is a title/work-family discovery lead, not an exact Church-list crosswalk or a single stable text. No text is bundled; completeness and reuse rights are unverified.",
    },
    32: {
        "source_ids": ["SRC-029", "SRC-073", "SRC-211", "SRC-286", "SRC-287", "SRC-288"],
        "mapping_note": "The Church list names I Book of Dominos; the Ethiopian Orthodox Bible Project glosses it as Book of the Covenant I and describes its edition of First Dominos. Beta maṣāḥǝft catalogs the Geʽez Testamentum Domini (CAe 2461), a plausible work-family candidate. The exact Church-list-to-work and edition crosswalk remains uncertain; no text is bundled.",
    },
    33: {
        "source_ids": ["SRC-029", "SRC-073", "SRC-211", "SRC-286", "SRC-287", "SRC-288"],
        "mapping_note": "The Church list names II Book of Dominos; the Ethiopian Orthodox Bible Project glosses it as Book of the Covenant II and describes its edition of Second Dominos. Beta maṣāḥǝft catalogs the separate composite Geʽez Testamentum Domini in Galilea (CAe 2462), a plausible work-family candidate. The exact Church-list-to-work and edition crosswalk remains uncertain; no text is bundled.",
    },
    6: {
        "source_ids": ["SRC-029", "SRC-274", "SRC-176"],
        "mapping_note": "The Church list names Romans. The pinned Beta maṣāḥǝft TEI title is Epistle to the Romans, and its Epistle note says the text is taken from the printed EOTC Bible. This supports a provisional title-level link. The source calls its 16 manuscript-based text divisions preliminary and does not account for recensions; exact print exemplar, recension, current EOTC edition identity, completeness, and accuracy remain unverified.",
    },
    1: {
        "source_ids": ["SRC-029", "SRC-219", "SRC-220", "SRC-176"],
        "mapping_note": "The Church list names Matthew. The pinned Beta maṣāḥǝft TEI identifies a Geʽez Gospel of Matthew and its edition note says ‘Text of the EOTC printed Bible,’ supporting a provisional title-level link. The exact print exemplar, current EOTC edition identity, completeness, and transcription accuracy remain unverified; numbering anomalies are preserved as found.",
    },
    2: {
        "source_ids": ["SRC-029", "SRC-083", "SRC-084", "SRC-091", "SRC-092", "SRC-176"],
        "mapping_note": "The Church list names Mark, and the pinned Beta maṣāḥǝft TEI identifies a Geʽez Gospel of Mark whose edition note says ‘Text of the EOTC printed Bible.’ This supports a provisional title-level link. The exact printed exemplar, current EOTC edition identity, completeness, and transcription accuracy remain unverified.",
    },
    3: {
        "source_ids": ["SRC-029", "SRC-221", "SRC-222", "SRC-176"],
        "mapping_note": "The Church list names Luke. The pinned Beta maṣāḥǝft TEI identifies a Geʽez Gospel of Luke and its edition note says ‘Text of the EOTC printed Bible,’ supporting a provisional title-level link. The exact print exemplar, current EOTC edition identity, completeness, and transcription accuracy remain unverified; an empty line and source-order anomaly in chapter 21 are preserved as found.",
    },
    4: {
        "source_ids": ["SRC-029", "SRC-223", "SRC-224", "SRC-176"],
        "mapping_note": "The Church list names John. The pinned Beta maṣāḥǝft TEI identifies a Geʽez Gospel of John and its edition note says ‘Text of the EOTC printed Bible,’ supporting a provisional title-level link. The exact print exemplar, current EOTC edition identity, completeness, and transcription accuracy remain unverified.",
    },
    5: {
        "source_ids": ["SRC-029", "SRC-225", "SRC-226", "SRC-176"],
        "mapping_note": "The Church list names The Acts. The pinned Beta maṣāḥǝft TEI work LIT1019Actsof contains a Geʽez Acts division explicitly labeled ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The TEI file also contains a separate manuscript-derived introduction, retained in the source but excluded from the 28-chapter Acts reader. The exact print exemplar, current EOTC edition identity, completeness, and transcription accuracy remain unverified; repeated and omitted chapter labels are preserved.",
    },
    27: {
        "source_ids": ["SRC-029", "SRC-231", "SRC-232", "SRC-176"],
        "mapping_note": "The Church list names Revelation. The pinned Beta maṣāḥǝft TEI contains a 22-chapter Geʽez text division labeled ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. Its exact printed exemplar, identity with a current EOTC edition, accuracy, and physical-edition completeness remain unverified. Chapter 2 repeats source label 26; all source labels are preserved.",
    },
    19: {
        "source_ids": ["SRC-029", "SRC-241", "SRC-242", "SRC-176"],
        "mapping_note": "The Church list names Hebrews. The pinned Beta maṣāḥǝft TEI identifies an Epistle to the Hebrews and a Geʽez text division labeled ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current EOTC edition identity, transcription accuracy, and completeness remain unverified. The 26 unnumbered TEI lines are retained without supplying labels.",
    },
    25: {
        "source_ids": ["SRC-029", "SRC-239", "SRC-240", "SRC-176"],
        "mapping_note": "The Church list names James. The pinned Beta maṣāḥǝft TEI identifies the Epistle of James and a Geʽez edition labeled ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current EOTC edition identity, transcription accuracy, and completeness remain unverified. The 18 unnumbered TEI lines are retained without supplying labels.",
    },
    7: {"source_ids": ["SRC-029", "SRC-249", "SRC-250", "SRC-176"], "mapping_note": "The Church list names I Corinthians. The pinned Beta maṣāḥǝft TEI identifies First Epistle to the Corinthians and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 39 unnumbered lines are retained without labels."},
    8: {"source_ids": ["SRC-029", "SRC-251", "SRC-252", "SRC-176"], "mapping_note": "The Church list names II Corinthians. The pinned Beta maṣāḥǝft TEI identifies Second Epistle to the Corinthians and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 23 unnumbered lines are retained without labels."},
    9: {"source_ids": ["SRC-029", "SRC-253", "SRC-254", "SRC-176"], "mapping_note": "The Church list names Galatians. The pinned Beta maṣāḥǝft TEI identifies the Epistle to the Galatians and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 16 unnumbered lines are retained without labels."},
    10: {"source_ids": ["SRC-029", "SRC-255", "SRC-256", "SRC-176"], "mapping_note": "The Church list names Ephesians. The pinned Beta maṣāḥǝft TEI identifies the Epistle to the Ephesians and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 20 unnumbered lines are retained without labels."},
    11: {"source_ids": ["SRC-029", "SRC-257", "SRC-258", "SRC-176"], "mapping_note": "The Church list names Philippians. The pinned Beta maṣāḥǝft TEI identifies the Epistle to the Philippians and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 13 unnumbered lines are retained without labels."},
    12: {"source_ids": ["SRC-029", "SRC-259", "SRC-260", "SRC-176"], "mapping_note": "The Church list names Colossians. The pinned Beta maṣāḥǝft TEI identifies the Epistle to the Colossians and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 16 unnumbered lines are retained without labels."},
    13: {"source_ids": ["SRC-029", "SRC-261", "SRC-262", "SRC-176"], "mapping_note": "The Church list names I Thessalonians. The pinned Beta maṣāḥǝft TEI identifies the First Epistle to the Thessalonians and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 12 unnumbered lines are retained without labels."},
    14: {"source_ids": ["SRC-029", "SRC-263", "SRC-264", "SRC-176"], "mapping_note": "The Church list names II Thessalonians. The pinned Beta maṣāḥǝft TEI identifies the Second Epistle to the Thessalonians and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 11 unnumbered lines are retained without labels."},
    15: {"source_ids": ["SRC-029", "SRC-265", "SRC-266", "SRC-176"], "mapping_note": "The Church list names I Timothy. The pinned Beta maṣāḥǝft TEI identifies the First Epistle to Timothy and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 20 unnumbered lines are retained without labels."},
    16: {"source_ids": ["SRC-029", "SRC-267", "SRC-268", "SRC-176"], "mapping_note": "The Church list names II Timothy. The pinned Beta maṣāḥǝft TEI identifies the Second Epistle to Timothy and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 15 unnumbered lines are retained without labels."},
    17: {"source_ids": ["SRC-029", "SRC-269", "SRC-270", "SRC-176"], "mapping_note": "The Church list names Titus. The pinned Beta maṣāḥǝft TEI identifies the Epistle to Titus and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 6 unnumbered lines are retained without labels."},
    18: {
        "source_ids": ["SRC-029", "SRC-384"],
        "reader_status": "No canon-linked reader. Fourteen separately scoped Philemon research readers are bundled across 13 language tags, including Baiso in Ethiopic and Latin scripts and an English WEBBE module. Their work/title links are candidate or reviewed title matches only; none is asserted to be an EOTC or Eritrean edition, and none counts as canon-linked reader coverage.",
        "mapping_note": "The Church's cited English list names Philemon at New Testament entry 18. Thirteen bundled research readers carry a Philemon title or the standard USFM module code PHM and are indexed as work/title candidates; Gamo is marked as a reviewed title match, while other edition links remain provisional. This does not establish EOTC or Eritrean affiliation, exact edition identity, translation ancestry, completeness, or accuracy. The providers' conventional Bible module sets are not treated as Church-canon equivalences.",
    },
    20: {"source_ids": ["SRC-029", "SRC-243", "SRC-244", "SRC-176"], "mapping_note": "The Church list names I Peter. The pinned Beta maṣāḥǝft TEI identifies the First Epistle of Peter and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 16 unnumbered lines are retained without labels."},
    21: {"source_ids": ["SRC-029", "SRC-245", "SRC-246", "SRC-176"], "mapping_note": "The Church list names II Peter. The pinned Beta maṣāḥǝft TEI identifies the Second Epistle of Peter and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 9 unnumbered lines are retained without labels."},
    22: {"source_ids": ["SRC-029", "SRC-247", "SRC-248", "SRC-176"], "mapping_note": "The Church list names I John. The pinned Beta maṣāḥǝft TEI identifies the First Epistle of John and labels the Geʽez text ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact print exemplar, current edition identity, accuracy, and completeness remain unverified. Its 16 unnumbered lines are retained without labels."},
}

NT_REVIEWED_TITLE_METADATA = {
    2: {'source_ids': ['SRC-029', 'SRC-083', 'SRC-092'], 'mapping_note': "Reviewed work/title crosswalk: the Church's numbered list names Mark; the pinned Beta maṣāḥǝft work record is Gospel of Mark, with a Geʽez division labeled ‘Text of the EOTC printed Bible.’ This supports the named-work match only. Exact print exemplar, completeness, edition identity, and transcription accuracy remain unverified."}
}
NT_SOURCE_METADATA.update(NT_REVIEWED_TITLE_METADATA)

NT_MAPPING_METADATA = {
    28: ("The Church list names Sirate Tsion; Cowley/Lexham report Ser’atä Seyon as a 30-canon title and suggest it may relate to Canons after the Ascension. Beta maṣāḥǝft records a Geʽez 29-canon witness of Canons after the Ascension (CAe 2673) in BL Oriental 794. Lexham explicitly says the relation is unclear; the 29/30 count and title discrepancy are unresolved. Candidate lead only, not a verified crosswalk or complete text.", ["SRC-029", "SRC-073", "SRC-210", "SRC-211", "SRC-289"]),
    29: ("The Church list names Tizaz; Cowley and the Lexham Bible Dictionary list Te’ezaz among four apostolic Sinodos sections. Tel Aviv University hosts images following Horner’s 1904 edition and labels that section Te’ezaz, but its own notice lists 12 apparently missing pages. This is a provisional title/edition match, not a complete or verified Church-list text; no transcription is bundled.", ["SRC-029", "SRC-073", "SRC-210", "SRC-211", "SRC-213"]),
    30: ("The Church list names Gitsew; Cowley and the Lexham Bible Dictionary name Gessew among four apostolic Sinodos sections. This is a plausible title-family match only; manuscript contents vary, and no specific witness, edition, text boundaries, or completeness is verified here.", ["SRC-029", "SRC-073", "SRC-210", "SRC-211"]),
    31: ("The Church list names Abtilis; Cowley and the Lexham Bible Dictionary name Abtelis among four apostolic Sinodos sections. Beta maṣāḥǝft catalogs Abṭelisāt (81), including witnesses labeled 81 and 80 canons, and separately distinguishes Apostolic canons (56). These records support a discovery lead only; exact Church-list mapping, text boundaries, and completeness remain unverified.", ["SRC-029", "SRC-073", "SRC-210", "SRC-211", "SRC-285"]),
    32: ("The EOTC canon page lists I Book of Dominos. The Ethiopian Orthodox Bible Project glosses it as Book of the Covenant I, and Beta maṣāḥǝft records the Geʽez Testamentum Domini (CAe 2461), described as a 60-chapter, two-part work. This is a plausible but unverified work-family candidate; exact Church-list mapping and edition boundaries are not established.", ["SRC-029", "SRC-073", "SRC-211", "SRC-286", "SRC-287"]),
    33: ("The EOTC canon page lists II Book of Dominos. The Ethiopian Orthodox Bible Project glosses it as Book of the Covenant II, and Beta maṣāḥǝft records the separate Geʽez Testamentum Domini in Galilea (CAe 2462), a composite work that includes the Epistula Apostolorum. This is a plausible but unverified work-family candidate; exact Church-list mapping and edition boundaries are not established.", ["SRC-029", "SRC-073", "SRC-211", "SRC-286", "SRC-288"]),
    34: ("Asale's dissertation (2015, pp. 178–180) describes three Epistles of Clement counted together as one book in one canon account. This is comparative context, not proof that this title identifies a particular Clement text or edition.", ["SRC-029", "SRC-073"]),
    35: ("The Church list names Didascalia, and Asale discusses it among broader-list additions. TAU separately labels a Platt 1834 image edition Didascalia and exposes 22 numbered section targets; this is a title-level candidate, not proof of matching textual scope, recension, or canonical classification. No reader is bundled.", ["SRC-029", "SRC-073", "SRC-086", "SRC-100", "SRC-345", "SRC-346"]),
}

READER_IDS = {
    1: "genesis-geez-dillmann-hacohen",
    2: "exodus-geez-dillmann-hacohen",
    3: "leviticus-geez-dillmann-hacohen",
    4: "numbers-geez-dillmann-hacohen",
    5: "deuteronomy-geez-dillmann-hacohen",
    6: "joshua-geez-dillmann-hacohen",
    7: "judges-geez-dillmann-hacohen",
    8: "ruth-geez-dillmann-hacohen",
    27: "ecclesiastes-geez-betamasaheft-eotced",
    32: "daniel-betamasaheft-tei",
    18: "judith-betamasaheft-tei",
    19: "esther-betamasaheft-tei",
    33: "hosea-betamasaheft-tei",
    35: "micah-betamasaheft-tei",
    43: "zechariah-betamasaheft-tei",
    17: "tobit-geez-betamasaheft-eotced",
    13: "jubilees-geez-hacohen",
    14: "enoch-geez-eotc",
    34: "amos-geez-pereira-ghebre-tau",
    36: "joel-geez-dillmann-hacohen-tau",
    23: "psalms-geez-ludolf-hacohen",
    28: "song-of-songs-geez-betamasaheft-eotced",
    37: "obadiah-geez-bachmann-theot",
    38: "jonah-geez-lofgren-ghebre-tau",
    39: "nahum-geez-lofgren-ghebre-tau",
    40: "habakkuk-geez-lofgren-ghebre-tau",
    41: "zephaniah-geez-lofgren-hacohen-tau",
    42: "haggai-geez-lofgren-ghebre-tau",
    44: "malachi-geez-lofgren-ghebre-tau",
    45: "sirach-geez-dillmann-hacohen-tau",
}
READER_FILES = {
    1: "genesis-geez.json",
    2: "exodus-geez.json",
    3: "leviticus-geez.json",
    4: "numbers-geez.json",
    5: "deuteronomy-geez.json",
    6: "joshua-geez.json",
    7: "judges-geez.json",
    8: "ruth-geez.json",
    27: "ecclesiastes-geez-betamasaheft-eotced.json",
    32: "daniel-betamasaheft-tei.json",
    18: "judith-betamasaheft-tei.json",
    19: "esther-betamasaheft-tei.json",
    33: "hosea-betamasaheft-tei.json",
    35: "micah-betamasaheft-tei.json",
    43: "zechariah-betamasaheft-tei.json",
    17: "tobit-geez-betamasaheft-eotced.json",
    13: "jubilees-geez-hacohen.json",
    14: "enoch-geez-eotc.json",
    34: "amos-geez-pereira-ghebre-tau.json",
    36: "joel-geez-dillmann-hacohen-tau.json",
    23: "psalms-geez-ludolf.json",
    28: "song-of-songs-geez-betamasaheft-eotced.json",
    37: "obadiah-geez-bachmann-theot.json",
    38: "jonah-geez-lofgren-ghebre-tau.json",
    39: "nahum-geez-lofgren-ghebre-tau.json",
    40: "habakkuk-geez-lofgren-ghebre-tau.json",
    41: "zephaniah-geez-lofgren-hacohen-tau.json",
    42: "haggai-geez-lofgren-ghebre-tau.json",
    44: "malachi-geez-lofgren-ghebre-tau.json",
    45: "sirach-geez-dillmann-hacohen-tau.json",
}
SOURCE_METADATA = {
    9: {
        "source_ids": ["SRC-029", "SRC-164", "SRC-336"],
        "mapping_state": "asserted_by_source",
        "mapping_note": "The Church list groups ‘I and II Samuel’ at entry 9. TAU explicitly identifies Ethiopic Reigns I–II as Samuel I–II. Two separate locally bundled historical Geʽez research readers preserve the 31- and 24-chapter components. This source-supported title/work link does not establish identity with a current EOTC edition or verify print completeness or transcription accuracy.",
    },
    10: {
        "source_ids": ["SRC-029", "SRC-164", "SRC-337"],
        "mapping_state": "asserted_by_source",
        "mapping_note": "The Church list groups ‘I and II Kings’ at entry 10. TAU explicitly identifies Ethiopic Reigns III–IV as Kings I–II. Two separate locally bundled historical Geʽez research readers preserve 23 and 25 observed source chapters, respectively. This source-supported title/work link does not establish identity with a current EOTC edition or verify print completeness or transcription accuracy.",
    },
    2: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-035"],
        "mapping_note": "Reviewed title/work-level crosswalk: the Church's numbered canon list names Exodus, and TAU's Ethiopic Bible index independently lists the Geʽez Exodus item under its Octateuch. This matches the named biblical work only; it does not establish that Dillmann's 1853–1855 edition is the current Church text, or verify the transcription's wording, textual completeness, or manuscript/edition identity.",
    },
    3: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-035"],
        "mapping_note": "Reviewed title/work-level crosswalk: the Church's numbered canon list names Leviticus, and TAU's Ethiopic Bible index independently lists the Geʽez Leviticus item under its Octateuch. This matches the named biblical work only; it does not establish that Dillmann's 1853–1855 edition is the current Church text, or verify the transcription's wording, textual completeness, or manuscript/edition identity.",
    },
    4: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-035"],
        "mapping_note": "Reviewed title/work-level crosswalk: the Church's numbered canon list names Numbers, and TAU's Ethiopic Bible index independently lists the Geʽez Numeri item under its Octateuch. This matches the named biblical work only; it does not establish that Dillmann's 1853–1855 edition is the current Church text, or verify the transcription's wording, textual completeness, or manuscript/edition identity.",
    },
    5: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-035"],
        "mapping_note": "Reviewed title/work-level crosswalk: the Church's numbered canon list names Deuteronomy, and TAU's Ethiopic Bible index independently lists the Geʽez Deuteronomium item under its Octateuch. This matches the named biblical work only; it does not establish that Dillmann's 1853–1855 edition is the current Church text, or verify the transcription's wording, textual completeness, or manuscript/edition identity.",
    },
    6: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-035"],
        "mapping_note": "Reviewed title/work-level crosswalk: the Church's numbered canon list names Joshua, and TAU's Ethiopic Bible index independently lists the Geʽez Josua item under its Octateuch. This matches the named biblical work only; it does not establish that Dillmann's 1853–1855 edition is the current Church text, or verify the transcription's wording, textual completeness, or manuscript/edition identity.",
    },
    7: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-035"],
        "mapping_note": "Reviewed title/work-level crosswalk: the Church's numbered canon list names Judges, and TAU's Ethiopic Bible index independently lists the Geʽez Judices item under its Octateuch. This matches the named biblical work only; it does not establish that Dillmann's 1853–1855 edition is the current Church text, or verify the transcription's wording, textual completeness, or manuscript/edition identity.",
    },
    8: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-035"],
        "mapping_note": "Reviewed title/work-level crosswalk: the Church's numbered canon list names Ruth, and TAU's Ethiopic Bible index independently lists the Geʽez Ruth item under its Octateuch. This matches the named biblical work only; it does not establish that Dillmann's 1853–1855 edition is the current Church text, or verify the transcription's wording, textual completeness, or manuscript/edition identity.",
    },
    1: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-035"],
        "mapping_note": "Reviewed title/work-level crosswalk: the Church's numbered canon list names Genesis, and TAU's Ethiopic Bible index independently lists Genesis in Ethiopic and English under its Octateuch. This matches the named biblical work only; it does not establish that Dillmann's 1853–1855 edition is the current Church text, or verify the transcription's wording, textual completeness, or manuscript/edition identity.",
    },
    27: {
        "source_ids": ["SRC-029", "SRC-176", "SRC-279", "SRC-294"],
        "mapping_note": "The Church list names Ecclesiastes. The pinned Beta maṣāḥǝft TEI contains a Geʽez division labeled ‘Text of the EOTC printed Bible,’ supporting a source-asserted title link only. A scoped extract contains 12 ordered chapters, 226 source lines, and 222 linked references; chapter 12 markers 13–17 link to targets 10–14, preserved separately. The exact print exemplar, accuracy, completeness, and underlying print rights remain unverified; the separate noncommercial Mercer division is excluded.",
    },
    28: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-176", "SRC-292", "SRC-293"],
        "mapping_note": "The Church-list title is Song of Songs. Beta maṣāḥǝft LIT2362Songof contains a Geʽez EOTCed division labeled ‘Text of the EOTC printed Bible’; its 2025 revision history says EOTC Bible text was added. This supports a source-asserted title link. The work page also gives a generic modern-Vulgata digitization statement; exact print exemplar and the relationship between these statements remain unresolved. The 131 source lines are extracted, with duplicated chapter 8 marker 14 preserved. Accuracy and completeness are not independently verified.",
    },
    22: {
        "source_ids": ["SRC-029", "SRC-038", "SRC-109", "SRC-110", "SRC-111", "SRC-143", "SRC-146", "SRC-283"],
        "mapping_note": "The Church list names Job. Separate Geʽez leads exist for Pereira’s historical critical edition and Beta maṣāḥǝft LIT1688Job; neither establishes an exact EOTC print match or complete reader here. Beta maṣāḥǝft’s text-page CC BY-SA 4.0 file notice conflicts with its CC BY-NC-SA 4.0 site notice, so no wording is copied. English Brenton Septuagint Job is a separate historical companion translated from Greek; it is not Geʽez and its alignment with any Church edition is unverified.",
    },
    32: {
        "source_ids": ["SRC-029", "SRC-282"],
        "mapping_note": "The Church list names Daniel. The pinned Beta maṣāḥǝft TEI has a Geʽez edition labeled ‘Text of the EOTC printed Bible’ and its abstract identifies the work as Daniel, including named Daniel-associated stories and prayers. This supports a provisional title-level link only. The exact print exemplar, internal component boundaries, completeness, and transcription accuracy remain unverified; chapter 14 source labels 0–2 are retained.",
    },
    33: {
        "source_ids": ["SRC-029", "SRC-233", "SRC-234", "SRC-176"],
        "mapping_note": "The Church list names Hosea. The pinned Beta maṣāḥǝft TEI identifies a Geʽez Book of Hosea and labels its edition ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. Exact print exemplar, current EOTC edition identity, accuracy, and completeness remain unverified.",
    },
    35: {
        "source_ids": ["SRC-029", "SRC-235", "SRC-236", "SRC-176"],
        "mapping_note": "The Church list names Micah. The pinned Beta maṣāḥǝft TEI identifies a Geʽez Book of Micah and labels its edition ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. Exact print exemplar, current EOTC edition identity, accuracy, and completeness remain unverified.",
    },
    43: {
        "source_ids": ["SRC-029", "SRC-237", "SRC-238", "SRC-176"],
        "mapping_note": "The Church list names Zechariah. The pinned Beta maṣāḥǝft TEI identifies a Geʽez Book of Zechariah and labels its edition ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. This is distinct from the separately named Zephaniah. Exact print exemplar, current EOTC edition identity, accuracy, and completeness remain unverified.",
    },
    18: {
        "source_ids": ["SRC-029", "SRC-229", "SRC-230", "SRC-176"],
        "mapping_note": "The Church list names Judith. The pinned Beta maṣāḥǝft TEI identifies a Book of Judith and a Geʽez edition labeled ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact printed exemplar, current EOTC edition identity, transcription accuracy, and completeness remain unverified.",
    },
    19: {
        "source_ids": ["SRC-029", "SRC-227", "SRC-228", "SRC-176"],
        "mapping_note": "The Church list names Esther. The pinned Beta maṣāḥǝft TEI identifies a Book of Esther and a Geʽez edition labeled ‘Text of the EOTC printed Bible’; this supports a provisional title-level link only. The exact printed exemplar, current EOTC edition identity, transcription accuracy, and completeness remain unverified.",
    },
    17: {
        "source_ids": ["SRC-029", "SRC-134", "SRC-217", "SRC-218"],
        "mapping_note": "The Church list names Tobit. The Beta maṣāḥǝft TEI edition explicitly declares gez and says it is text of the EOTC printed Bible, supporting a title-level link. The Church-list crosswalk, exact printed exemplar, transcription accuracy, and completeness against print remain unverified.",
    },
    34: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-151", "SRC-193"],
        "mapping_note": "The Church list and this source transcription share the title Amos; the link is title-level navigation. It does not establish that Pereira's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. See the reader's captured-page and review notes.",
    },
    36: {
        "source_ids": ["SRC-029", "SRC-036", "SRC-149", "SRC-192"],
        "mapping_note": "The Church list and this source transcription share the title Joel; the link is title-level navigation. It does not establish that Dillmann's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. The reader records observed label gaps; see its review notes.",
    },
    20: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    21: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    24: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    25: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    45: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-098", "SRC-100", "SRC-101", "SRC-318"],
    },
    23: {
        "source_ids": ["SRC-029", "SRC-036", "SRC-058", "SRC-059", "SRC-067", "SRC-068", "SRC-069"],
        "reader_status": "Bundled: Geʽez source transcription + Brenton English Septuagint companion (Greek basis; independent witness, alignment unverified)",
        "mapping_note": (
            "The Church list names Psalms; this reader contains the TAU-hosted Geʽez transcription of Ludolf's Psalter in 151 Rahlfs-numbered pages. "
            "The reader preserves source label anomalies and has not been independently collated. This supports navigation, not an exact canon crosswalk or completeness claim."
        ),
    },
    37: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-153", "SRC-186"],
        "mapping_note": "The Church list and this source transcription share the title Obadiah; the link is title-level navigation. It does not establish that Bachmann's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. See the reader's review notes.",
    },
    38: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-156", "SRC-187"],
        "mapping_note": "The Church list and this source transcription share the title Jonah; the link is title-level navigation. It does not establish that Löfgren's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. See the reader's review notes.",
    },
    39: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-155", "SRC-188"],
        "mapping_note": "The Church list and this source transcription share the title Nahum; the link is title-level navigation. It does not establish that Löfgren's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. See the reader's review notes.",
    },
    40: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-157", "SRC-189"],
        "mapping_note": "The Church list and this source transcription share the title Habakkuk; the link is title-level navigation. It does not establish that Löfgren's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. The reader preserves a source-page link anomaly; see its review notes.",
    },
    41: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-157", "SRC-158", "SRC-190"],
        "mapping_note": "The Church list and this source transcription share the title Zephaniah; the link is title-level navigation. It does not establish that Löfgren's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. See the reader's review notes.",
    },
    42: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-157", "SRC-160", "SRC-191"],
        "mapping_note": "The Church list and this source transcription share the title Haggai; the link is title-level navigation. It does not establish that Löfgren's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. See the reader's review notes.",
    },
    44: {
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-161", "SRC-195"],
        "mapping_note": "The Church list and this source transcription share the title Malachi; the link is title-level navigation. It does not establish that Löfgren's historical edition reproduces the Church list's intended Ethiopic text or verify transcription completeness or accuracy. See the reader's review notes.",
    },
    14: {
        "source_ids": ["SRC-029", "SRC-040", "SRC-065", "SRC-066"],
        "mapping_note": (
            "The Church list names Enoch, and the pinned Beta maṣāḥǝft block EOTCed is labeled as text of the EOTC printed Bible. "
            "The exact printed exemplar and date are unspecified. The reader preserves the TEI block's 108 chapters and 1,058 labeled lines; "
            "chapter 21 starts at source marker 2. This verifies the stored block's structure, not manuscript or printed-page accuracy."
        ),
    }
}

SOURCE_METADATA.update(REVIEWED_TITLE_METADATA)
for _reviewed_number in range(1, 9):
    SOURCE_METADATA[_reviewed_number]["mapping_state"] = "reviewed_match"
for _reviewed_metadata in REVIEWED_TITLE_METADATA.values():
    _reviewed_metadata["mapping_state"] = "reviewed_match"
for _reviewed_metadata in NT_REVIEWED_TITLE_METADATA.values():
    _reviewed_metadata["mapping_state"] = "reviewed_match"


def main() -> None:
    source_list = json.loads(SOURCE_TRANSCRIPTION.read_text(encoding="utf-8"))
    old_labels = source_list.get("old_testament", [])
    new_labels = source_list.get("new_testament", [])
    if source_list.get("source_id") != "SRC-029":
        raise ValueError("Canon-label transcription must cite the Church source SRC-029.")
    if [row.get("number") for row in old_labels] != list(range(1, 47)) or [row.get("number") for row in new_labels] != list(range(1, 36)):
        raise ValueError("Canon-label transcription must preserve ordered 46/35 numbering.")
    books = []
    for number, (name, catalogue_ids) in enumerate(OT, 1):
        source_label = old_labels[number - 1]["label"]
        reader_id = READER_IDS.get(number)
        bundled_reader = bool(reader_id and (ROOT / "readers" / READER_FILES[number]).is_file())
        source_metadata = SOURCE_METADATA.get(number, {})
        english_companion = False
        if bundled_reader:
            reader_data = json.loads((ROOT / "readers" / READER_FILES[number]).read_text(encoding="utf-8"))
            companion = reader_data.get("parallel_translation", {})
            english_companion = companion.get("language_tag") == "en" and companion.get("text_origin") == "published_translation"
        if number in (9, 10):
            component_ids = (
                ["samuel-i-geez-research", "samuel-ii-geez-research"] if number == 9 else
                ["kings-i-geez-research", "kings-ii-geez-research"]
            )
            missing_components = [reader_id for reader_id in component_ids if not (ROOT / "readers" / f"{reader_id}.json").is_file()]
            if missing_components:
                raise ValueError(f"Grouped Church-list entry {number} lacks required local research readers: {missing_components}")
        reader_status = (
            "Two bundled historical Geʽez research component readers (31 and 24 source chapters); TAU asserts the Samuel mapping, while current EOTC edition identity, completeness, and accuracy remain unverified." if number == 9 else
            "Two bundled historical Geʽez research component readers (23 and 25 observed source chapters); TAU asserts the Kings mapping, while current EOTC edition identity, completeness, and accuracy remain unverified." if number == 10 else
            "Bundled: Geʽez EOTC printed-edition transcription" if number == 14 and bundled_reader else
            "Bundled: Geʽez source transcription + Brenton English Septuagint companion (Greek basis; independent witness, alignment unverified)" if number == 23 and english_companion else
            "Bundled: Geʽez Ludolf Psalter transcription" if number == 23 and bundled_reader else
            "Bundled: Geʽez + English Brenton companion" if number == 1 and bundled_reader else
            "Bundled: Geʽez source transcription + English Brenton research companion (wording unreviewed)" if number == 2 and english_companion else
            "Bundled: Geʽez source transcription" if bundled_reader else
            source_metadata.get("reader_status", "No reader bundled here; external availability not assessed")
        )
        mapping_note = (
            "The Church page presents ‘Ezra (2nd)’ and ‘Ezra Sutuel’ as one numbered entry. "
            "A provisional title-family crosswalk is supported by the Church page's separate statement that the Ethiopic Bible includes third and fourth Esdras, together with TAU's identification of Ethiopic Ezra II with Septuagint Esdras alpha / Vulgate tertius Esdrae and Ezra I (Apocalypse of Esdras) with Vulgate quartus Esdrae. This suggests, but does not prove, that ‘Ezra (2nd)’ corresponds to the third-Esdras work and ‘Ezra Sutuel’ to the fourth-Esdras apocalypse. The British Library codex title names both labels, but its internal boundaries, completeness, exact edition identity, and textual contents are unverified; no reader coverage is claimed."
            if number == 16 else
            "The Church page uses the plural phrase ‘books of wisdom.’ Wisdom of Solomon is "
            "a research candidate row only; its identity as the exact listed work is not established."
            if number == 26 else
            "The Church list's ‘I Maccabees’/‘II and III Maccabees’ labels are preserved. "
            "Mikre-Sellassie (1993) documents different Maccabean groupings in broader and narrower list traditions; those labels do not prove a one-to-one mapping to the catalogue's Meqabyan texts, whose identities remain unresolved."
            if number in (20, 21) else
            "Mikre-Sellassie (1993) describes Messale (Proverbs 1–24) and Tegsas (Proverbs 25–31) as separate titles in a historical canon account. The Church page lists Proverbs and Tegsats (Reproof); their exact boundaries and relationship to a specific edition remain unverified."
            if number in (24, 25) else
            source_metadata.get("mapping_note", "")
            if number == 45 else
            source_metadata.get("mapping_note", "") if source_metadata else
            "This is a grouped title in the Church list; separate catalogue rows are discovery aids, not proof of exact textual boundaries."
            if len(catalogue_ids) > 1 else ""
        )
        if not mapping_note:
            mapping_note = (
                f"The Church's cited English list names ‘{source_label}’ at Old Testament entry {number}; this record preserves that printed label. "
                "No reader is bundled here, external availability has not been assessed, and no exact edition/work crosswalk is asserted."
            )
        books.append({
            "canon_id": f"eotc-ot-{number:02d}", "section": "Old Testament",
            "section_number": number, "display_name": name,
            "source_label": source_label,
            "catalogue_ids": catalogue_ids, "source_ids": source_metadata.get("source_ids", ["SRC-029"]),
            **({"mapping_state": source_metadata["mapping_state"]} if source_metadata.get("mapping_state") else {}),
            "reader_status": reader_status,
            "reader_id": reader_id if bundled_reader else None,
            "mapping_note": mapping_note,
        })
    for number, name in enumerate(NT_NAMES, 1):
        source_label = new_labels[number - 1]["label"]
        reader_id = NT_READER_IDS.get(number)
        reader_file = NT_READER_FILES.get(number)
        bundled_reader = bool(reader_id and reader_file and (ROOT / "readers" / reader_file).is_file())
        metadata = NT_SOURCE_METADATA.get(number, {})
        reader_status = "Bundled: Geʽez source transcription (provisional title-level link; edition accuracy and completeness unverified)" if bundled_reader else metadata.get("reader_status", "No reader bundled here; external availability not assessed")
        books.append({
            "canon_id": f"eotc-nt-{number:02d}", "section": "New Testament",
            "section_number": number, "display_name": name,
            "source_label": source_label,
            "catalogue_ids": [NT_CATALOGUE_IDS.get(number, f"eotc-{54 + number:03d}")],
            "source_ids": metadata.get("source_ids", NT_MAPPING_METADATA.get(number, ("", ["SRC-029"]))[1]),
            **({"mapping_state": metadata["mapping_state"]} if metadata.get("mapping_state") else {}),
            "reader_status": reader_status, "reader_id": reader_id if bundled_reader else None,
            "mapping_note": (
                metadata.get("mapping_note")
                or NT_MAPPING_METADATA.get(number, ("", []))[0]
                or f"The Church's cited English list names ‘{source_label}’ at New Testament entry {number}; this record preserves that printed label. No reader is bundled here, external availability has not been assessed, and no exact edition/work crosswalk is asserted."
            ),
        })
    if len(OT) != 46 or len(NT_NAMES) != 35 or len(books) != 81:
        raise ValueError("Church-list registry must contain 46 Old Testament and 35 New Testament entries.")
    registry = {
        "source_id": "SRC-029",
        "basis": "The Ethiopian Orthodox Tewahedo Church’s own English canon page lists 46 Old Testament and 35 New Testament entries and explicitly states a total of 81. Grouped names are kept as that source presents them; they are not silently split into separate canonical units.",
        "mapping_caution": "Links to this archive’s 90 research rows support navigation only. They do not independently establish a title’s canonical mapping, text identity, completeness, or translation.",
        "context_source_ids": ["SRC-072", "SRC-073", "SRC-101"],
        "scholarly_context": "The 81-count and wording above describe the Church's cited English page, not a claim that all historical or scholarly lists have identical contents or counting rules. Bruk Ayele Asale's 2016 peer-reviewed article says the composition of the traditional 81 remains obscure; his 2015 University of KwaZulu-Natal thesis discusses multiple lists and competing broader/narrower classifications, including unresolved manuscript connections among Proverbs and Tegsas and names for the broader New Testament books. G.A. Mikre-Sellassie's 1993 article compares historical list traditions that group Proverbs, Maccabees, Sirach, and other works differently. These are attributed scholarly analyses, not Church rulings or proof of this page's edition-level crosswalks. The archive does not infer alternate mappings or generate missing canon entries from them.",
        "book_count": len(books),
        "reader_count": sum(entry["reader_id"] is not None for entry in books),
        "books": books,
    }
    OUTPUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {OUTPUT.name}: {len(OT)} Old Testament entries + {len(NT_NAMES)} New Testament entries.")


if __name__ == "__main__":
    main()
