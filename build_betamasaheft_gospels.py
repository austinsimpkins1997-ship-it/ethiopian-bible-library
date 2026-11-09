"""Extract pinned Beta maṣāḥǝft Geʽez scripture TEI files without normalizing anomalies."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMMIT = "9029473659ab6efc4035ee52b9922192c99ba75e"
TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS}
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
CONFIG = [
    {
        "name": "Matthew", "canon_id": "eotc-nt-01", "work_id": "LIT2709Matthew",
        "reader_id": "matthew-betamasaheft-tei", "file": "LIT2709Matthew.xml-original.xml",
        "source_repo_path": "2001-3000/LIT2709Matthew.xml",
        "page_source": "SRC-219", "file_source": "SRC-220", "catalogue_id": "eotc-055",
        "chapters": 28, "lines": 1187, "numbered": 1072, "empty": 0,
        "anomalies": ["Chapter 7 has source line labels 1–28 followed by a second label 24; the trailing label is preserved unchanged."],
    },
    {
        "name": "Luke", "canon_id": "eotc-nt-03", "work_id": "LIT2713Luke",
        "reader_id": "luke-betamasaheft-tei", "file": "LIT2713Luke.xml-original.xml",
        "source_repo_path": "2001-3000/LIT2713Luke.xml",
        "page_source": "SRC-221", "file_source": "SRC-222", "catalogue_id": "eotc-057",
        "chapters": 24, "lines": 1277, "numbered": 1151, "empty": 1,
        "anomalies": ["Chapter 21 starts with an empty TEI line carrying source label 21, followed by an unnumbered heading and numbered labels 1–36. The empty line, labels, and headings are preserved in source order."],
    },
    {
        "name": "John", "canon_id": "eotc-nt-04", "work_id": "LIT2715John",
        "reader_id": "john-betamasaheft-tei", "file": "LIT2715John.xml-original.xml",
        "source_repo_path": "2001-3000/LIT2715John.xml",
        "page_source": "SRC-223", "file_source": "SRC-224", "catalogue_id": "eotc-058",
        "chapters": 21, "lines": 937, "numbered": 879, "empty": 0,
        "anomalies": [],
    },
    {
        "name": "Acts of the Apostles", "canon_id": "eotc-nt-05", "work_id": "LIT1019Actsof",
        "reader_id": "acts-betamasaheft-tei", "file": "LIT1019Actsof.xml",
        "source_dir": "acts", "source_repo_path": "1001-2000/LIT1019Actsof.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "display_title": "Acts", "work_label": "Acts of the Apostles",
        "edition_id": "betamasaheft-acts-apostles-tei-2026",
        "section_xml_id": "Acts", "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-225", "file_source": "SRC-226", "catalogue_id": "eotc-059",
        "chapters": 28, "lines": 1208, "numbered": 1007, "empty": 0,
        "anomalies": [
            "Chapter 12 source labels repeat 3 and then resume at 8; labels are retained verbatim.",
            "Chapter 14 source labels repeat 25 before 26 and 27; labels are retained verbatim.",
            "Chapter 26 source labels omit 12 and repeat 16; labels are retained verbatim.",
        ],
        "scope_note": "The source TEI contains a separate IntroductionActs section with manuscript-derived incipits outside the numbered Acts text. It remains in the retained TEI but is not folded into the 28-chapter Acts reader.",
    },
    {
        "name": "Esther", "work_label": "Book of Esther", "display_title": "Esther",
        "canon_id": "eotc-ot-19", "work_id": "LIT1362Esther",
        "reader_id": "esther-betamasaheft-tei", "file": "LIT1362Esther.xml",
        "source_dir": "esther", "source_repo_path": "1001-2000/LIT1362Esther.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "edition_id": "betamasaheft-esther-tei-2026", "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-227", "file_source": "SRC-228", "catalogue_id": "eotc-022",
        "chapters": 13, "lines": 252, "numbered": 252, "empty": 0, "anomalies": [],
    },
    {
        "name": "Judith", "work_label": "Book of Judith", "display_title": "Judith",
        "canon_id": "eotc-ot-18", "work_id": "LIT1701Judith",
        "reader_id": "judith-betamasaheft-tei", "file": "LIT1701Judith.xml",
        "source_dir": "judith", "source_repo_path": "1001-2000/LIT1701Judith.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "edition_id": "betamasaheft-judith-tei-2026", "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-229", "file_source": "SRC-230", "catalogue_id": "eotc-021",
        "chapters": 16, "lines": 343, "numbered": 343, "empty": 0, "anomalies": [],
    },
    {
        "name": "Revelation", "work_label": "Revelation of John", "display_title": "Revelation",
        "canon_id": "eotc-nt-27", "work_id": "LIT3179Revela",
        "reader_id": "revelation-betamasaheft-tei", "file": "LIT3179Revela.xml",
        "source_dir": "revelation", "source_repo_path": "3001-4000/LIT3179Revela.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "edition_id": "betamasaheft-revelation-tei-2026", "section_xml_id": "Revelation",
        "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-231", "file_source": "SRC-232", "catalogue_id": "eotc-081",
        "chapters": 22, "lines": 434, "numbered": 402, "empty": 0,
        "anomalies": ["Chapter 2 has a repeated source label 26 and then resumes at 28; the source labels are preserved unchanged."],
    },
    {
        "name": "Hosea", "work_label": "Book of Hosea", "display_title": "Hosea",
        "canon_id": "eotc-ot-33", "work_id": "LIT3144Hosea",
        "reader_id": "hosea-betamasaheft-tei", "file": "LIT3144Hosea.xml",
        "source_dir": "hosea", "source_repo_path": "3001-4000/LIT3144Hosea.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "edition_id": "betamasaheft-hosea-tei-2026", "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-233", "file_source": "SRC-234", "catalogue_id": "eotc-041",
        "chapters": 14, "lines": 197, "numbered": 197, "empty": 0, "anomalies": [],
    },
    {
        "name": "Micah", "work_label": "Book of Micah", "display_title": "Micah",
        "canon_id": "eotc-ot-35", "work_id": "LIT3146Micah",
        "reader_id": "micah-betamasaheft-tei", "file": "LIT3146Micah.xml",
        "source_dir": "micah", "source_repo_path": "3001-4000/LIT3146Micah.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "edition_id": "betamasaheft-micah-tei-2026", "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-235", "file_source": "SRC-236", "catalogue_id": "eotc-043",
        "chapters": 7, "lines": 106, "numbered": 106, "empty": 0, "anomalies": [],
    },
    {
        "name": "Zechariah", "work_label": "Book of Zechariah", "display_title": "Zechariah",
        "canon_id": "eotc-ot-43", "work_id": "LIT3150Zechar",
        "reader_id": "zechariah-betamasaheft-tei", "file": "LIT3150Zechar.xml",
        "source_dir": "zechariah", "source_repo_path": "3001-4000/LIT3150Zechar.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "edition_id": "betamasaheft-zechariah-tei-2026", "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-237", "file_source": "SRC-238", "catalogue_id": "eotc-051",
        "chapters": 14, "lines": 202, "numbered": 202, "empty": 0, "anomalies": [],
    },
    {
        "name": "James", "work_label": "Epistle of James", "display_title": "James",
        "canon_id": "eotc-nt-25", "work_id": "LIT3512Epistle",
        "reader_id": "james-betamasaheft-tei", "file": "LIT3512Epistle.xml",
        "source_dir": "james", "source_repo_path": "3001-4000/LIT3512Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "edition_id": "betamasaheft-james-tei-2026", "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-239", "file_source": "SRC-240", "catalogue_id": "eotc-074",
        "chapters": 5, "lines": 126, "numbered": 108, "empty": 0,
        "anomalies": ["The selected text scope contains 18 unnumbered TEI line elements; all are preserved in their source order without assigning verse labels."],
    },
    {
        "name": "Hebrews", "work_label": "Epistle to the Hebrews", "display_title": "Hebrews",
        "canon_id": "eotc-nt-19", "work_id": "LIT3524Epistle",
        "reader_id": "hebrews-betamasaheft-tei", "file": "LIT3524Epistle.xml",
        "source_dir": "hebrews", "source_repo_path": "3001-4000/LIT3524Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999",
        "edition_id": "betamasaheft-hebrews-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible",
        "page_source": "SRC-241", "file_source": "SRC-242", "catalogue_id": "eotc-073",
        "chapters": 13, "lines": 328, "numbered": 302, "empty": 0,
        "anomalies": ["The selected text scope contains 26 unnumbered TEI line elements; all are preserved in their source order without assigning verse labels."],
    },
    {
        "name": "I Peter", "work_label": "First Epistle of Peter", "display_title": "I Peter",
        "canon_id": "eotc-nt-20", "work_id": "LIT3507Epistle", "reader_id": "first-peter-betamasaheft-tei",
        "file": "LIT3507Epistle.xml", "source_dir": "first-peter", "source_repo_path": "3001-4000/LIT3507Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-first-peter-tei-2026",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-243", "file_source": "SRC-244", "catalogue_id": "eotc-075",
        "chapters": 5, "lines": 121, "numbered": 105, "empty": 0, "anomalies": ["The selected scope contains 16 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "II Peter", "work_label": "Second Epistle of Peter", "display_title": "II Peter",
        "canon_id": "eotc-nt-21", "work_id": "LIT3508Epistle", "reader_id": "second-peter-betamasaheft-tei",
        "file": "LIT3508Epistle.xml", "source_dir": "second-peter", "source_repo_path": "3001-4000/LIT3508Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-second-peter-tei-2026",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-245", "file_source": "SRC-246", "catalogue_id": "eotc-076",
        "chapters": 3, "lines": 70, "numbered": 61, "empty": 0, "anomalies": ["The selected scope contains 9 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "I John", "work_label": "First Epistle of John", "display_title": "I John",
        "canon_id": "eotc-nt-22", "work_id": "LIT3509Epistle", "reader_id": "first-john-betamasaheft-tei",
        "file": "LIT3509Epistle.xml", "source_dir": "first-john", "source_repo_path": "3001-4000/LIT3509Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-first-john-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-247", "file_source": "SRC-248", "catalogue_id": "eotc-077",
        "chapters": 5, "lines": 121, "numbered": 105, "empty": 0, "anomalies": ["The selected scope contains 16 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "I Corinthians", "work_label": "First Epistle to the Corinthians", "display_title": "I Corinthians",
        "canon_id": "eotc-nt-07", "work_id": "LIT3516Epistle", "reader_id": "first-corinthians-betamasaheft-tei",
        "file": "LIT3516Epistle.xml", "source_dir": "first-corinthians", "source_repo_path": "3001-4000/LIT3516Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-first-corinthians-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-249", "file_source": "SRC-250", "catalogue_id": "eotc-061",
        "chapters": 16, "lines": 477, "numbered": 438, "empty": 0, "anomalies": ["The selected scope contains 39 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "II Corinthians", "work_label": "Second Epistle to the Corinthians", "display_title": "II Corinthians",
        "canon_id": "eotc-nt-08", "work_id": "LIT3517Epistle", "reader_id": "second-corinthians-betamasaheft-tei",
        "file": "LIT3517Epistle.xml", "source_dir": "second-corinthians", "source_repo_path": "3001-4000/LIT3517Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-second-corinthians-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-251", "file_source": "SRC-252", "catalogue_id": "eotc-062",
        "chapters": 13, "lines": 283, "numbered": 260, "empty": 0, "anomalies": ["The selected scope contains 23 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "Galatians", "work_label": "Epistle to the Galatians", "display_title": "Galatians",
        "canon_id": "eotc-nt-09", "work_id": "LIT3518Epistle", "reader_id": "galatians-betamasaheft-tei",
        "file": "LIT3518Epistle.xml", "source_dir": "galatians", "source_repo_path": "3001-4000/LIT3518Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-galatians-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-253", "file_source": "SRC-254", "catalogue_id": "eotc-063",
        "chapters": 6, "lines": 165, "numbered": 149, "empty": 0, "anomalies": ["The selected scope contains 16 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "Ephesians", "work_label": "Epistle to the Ephesians", "display_title": "Ephesians",
        "canon_id": "eotc-nt-10", "work_id": "LIT3519Epistle", "reader_id": "ephesians-betamasaheft-tei",
        "file": "LIT3519Epistle.xml", "source_dir": "ephesians", "source_repo_path": "3001-4000/LIT3519Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-ephesians-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-255", "file_source": "SRC-256", "catalogue_id": "eotc-064",
        "chapters": 6, "lines": 174, "numbered": 154, "empty": 0, "anomalies": ["The selected scope contains 20 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "Philippians", "work_label": "Epistle to the Philippians", "display_title": "Philippians",
        "canon_id": "eotc-nt-11", "work_id": "LIT3520Epistle", "reader_id": "philippians-betamasaheft-tei",
        "file": "LIT3520Epistle.xml", "source_dir": "philippians", "source_repo_path": "3001-4000/LIT3520Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-philippians-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-257", "file_source": "SRC-258", "catalogue_id": "eotc-065",
        "chapters": 4, "lines": 117, "numbered": 104, "empty": 0, "anomalies": ["The selected scope contains 13 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "Colossians", "work_label": "Epistle to the Colossians", "display_title": "Colossians",
        "canon_id": "eotc-nt-12", "work_id": "LIT3521Epistle", "reader_id": "colossians-betamasaheft-tei",
        "file": "LIT3521Epistle.xml", "source_dir": "colossians", "source_repo_path": "3001-4000/LIT3521Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-colossians-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-259", "file_source": "SRC-260", "catalogue_id": "eotc-066",
        "chapters": 4, "lines": 110, "numbered": 94, "empty": 0, "anomalies": ["The selected scope contains 16 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "I Thessalonians", "work_label": "First Epistle to the Thessalonians", "display_title": "I Thessalonians",
        "canon_id": "eotc-nt-13", "work_id": "LIT3522Epistle", "reader_id": "first-thessalonians-betamasaheft-tei",
        "file": "LIT3522Epistle.xml", "source_dir": "first-thessalonians", "source_repo_path": "3001-4000/LIT3522Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-first-thessalonians-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-261", "file_source": "SRC-262", "catalogue_id": "eotc-067",
        "chapters": 5, "lines": 101, "numbered": 89, "empty": 0, "anomalies": ["The selected scope contains 12 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "II Thessalonians", "work_label": "Second Epistle to the Thessalonians", "display_title": "II Thessalonians",
        "canon_id": "eotc-nt-14", "work_id": "LIT3523Epistle", "reader_id": "second-thessalonians-betamasaheft-tei",
        "file": "LIT3523Epistle.xml", "source_dir": "second-thessalonians", "source_repo_path": "3001-4000/LIT3523Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-second-thessalonians-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-263", "file_source": "SRC-264", "catalogue_id": "eotc-068",
        "chapters": 3, "lines": 58, "numbered": 47, "empty": 0, "anomalies": ["The selected scope contains 11 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "I Timothy", "work_label": "First Epistle to Timothy", "display_title": "I Timothy",
        "canon_id": "eotc-nt-15", "work_id": "LIT3525Epistle", "reader_id": "first-timothy-betamasaheft-tei",
        "file": "LIT3525Epistle.xml", "source_dir": "first-timothy", "source_repo_path": "3001-4000/LIT3525Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-first-timothy-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-265", "file_source": "SRC-266", "catalogue_id": "eotc-069",
        "chapters": 6, "lines": 133, "numbered": 113, "empty": 0, "anomalies": ["The selected scope contains 20 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "II Timothy", "work_label": "Second Epistle to Timothy", "display_title": "II Timothy",
        "canon_id": "eotc-nt-16", "work_id": "LIT3526Epistle", "reader_id": "second-timothy-betamasaheft-tei",
        "file": "LIT3526Epistle.xml", "source_dir": "second-timothy", "source_repo_path": "3001-4000/LIT3526Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-second-timothy-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-267", "file_source": "SRC-268", "catalogue_id": "eotc-070",
        "chapters": 4, "lines": 99, "numbered": 84, "empty": 0, "anomalies": ["The selected scope contains 15 unnumbered TEI line elements; none is assigned a verse label."],
    },
    {
        "name": "Titus", "work_label": "Epistle to Titus", "display_title": "Titus",
        "canon_id": "eotc-nt-17", "work_id": "LIT3527Epistle", "reader_id": "titus-betamasaheft-tei",
        "file": "LIT3527Epistle.xml", "source_dir": "titus", "source_repo_path": "3001-4000/LIT3527Epistle.xml",
        "commit": "ec53d3f4c5de47e463fa56a8465cf1090316a999", "edition_id": "betamasaheft-titus-tei-2026", "section_xml_id": "Epistle",
        "expected_note": "Text of the EOTC printed Bible", "page_source": "SRC-269", "file_source": "SRC-270", "catalogue_id": "eotc-071",
        "chapters": 3, "lines": 52, "numbered": 46, "empty": 0, "anomalies": ["The selected scope contains 6 unnumbered TEI line elements; none is assigned a verse label."],
    },
]


def normalized_text(node: ET.Element | None) -> str:
    return re.sub(r"\s+", " ", "".join(node.itertext()) if node is not None else "").strip()


def source_record(config: dict, kind: str, digest: str | None = None, byte_count: int | None = None) -> dict:
    book = config["name"]
    work_id = config["work_id"]
    commit = config.get("commit", COMMIT)
    display_title = config.get("work_label", f"Gospel of {book}")
    if kind == "page":
        text_kind = "Geʽez scripture text"
        return {
            "source_id": config["page_source"],
            "source_name": f"Beta maṣāḥǝft — {display_title} ({work_id}) work record",
            "url": f"https://betamasaheft.awhamburg.de/works/{work_id}/main",
            "inspection_and_limitations": (
                f"Official Beta maṣāḥǝft work record for {work_id} identifies a {text_kind} titled {display_title}. "
                "The corresponding pinned TEI file explicitly declares its enclosing edition xml:lang=\"gez\" "
                "and labels the relevant text ‘Text of the EOTC printed Bible.’ This supports a provisional "
                "title-level link only. It does not identify the exact print exemplar or current EOTC edition, "
                "nor establish accuracy or completeness. The TEI root xml:lang=\"en\" default is preserved "
                "as a metadata conflict."
            ),
            "archive_status": "Work metadata inspected; a pinned file-specific TEI transcription is retained separately; exact current-edition identity, completeness, and textual accuracy remain unverified",
        }
    source_dir = config.get("source_dir", "gospels")
    file_path = f"readers/source/{source_dir}/{config['file']}"
    source_repo_path = config["source_repo_path"]
    return {
        "source_id": config["file_source"],
        "source_name": f"Beta maṣāḥǝft Works — pinned {work_id} TEI source snapshot",
        "url": f"https://github.com/BetaMasaheft/Works/blob/{commit}/{source_repo_path}",
        "inspection_and_limitations": (
            f"Retrieved on 2026-10-25 from BetaMasaheft/Works commit {commit} and retained unchanged at "
            f"{file_path} ({byte_count:,} bytes; SHA-256 {digest}). The TEI root xml:id is {work_id} and "
            "xml:lang=en; its enclosing edition explicitly declares xml:lang=gez. "
            + (f"The selected text division ({config['section_xml_id']}) bears the EOTC printed-Bible note. " if config.get("section_xml_id") else "The enclosing edition division contains the note ‘Text of the EOTC printed Bible.’ ")
            + "The file-level availability statement declares CC BY-SA 4.0. "
            f"Structural extraction preserves all {config['chapters']} ordered chapter divisions and "
            f"{config['lines']} TEI line elements ({config['numbered']} with source labels, "
            f"{config['lines'] - config['numbered']} without labels; {config['empty']} empty). "
            + ("Source numbering/empty-element anomalies are recorded in the reader and retained unchanged. " if config["anomalies"] else "")
            + "No collation against the printed exemplar or manuscripts was performed. Exact exemplar, "
            "transcription accuracy, physical-edition completeness, and identity with a current EOTC edition "
            "remain unverified. The file-level license does not establish rights in the unidentified print exemplar."
        ),
        "archive_status": "Pinned source TEI retained locally; source declarations, file-level license, and extraction structure inspected; accuracy and physical-edition completeness unverified",
    }


def build_one(config: dict) -> dict:
    source_path = ROOT / "readers" / "source" / config.get("source_dir", "gospels") / config["file"]
    raw = source_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    root = ET.fromstring(raw)
    work_id = config["work_id"]
    if root.get(f"{{{XML_NS}}}id") != work_id or root.get(f"{{{XML_NS}}}lang") != "en":
        raise ValueError(f"Unexpected {config['name']} TEI root identity or default language")
    edition = next((node for node in root.iter(f"{{{TEI_NS}}}div") if node.get("type") == "edition"), None)
    if edition is None or edition.get(f"{{{XML_NS}}}lang") != "gez":
        raise ValueError(f"{config['name']} edition must explicitly declare Geʽez")
    notes = [normalized_text(node) for node in edition.findall(f"{{{TEI_NS}}}note")]
    expected_note = config.get("expected_note", "Text of the EOTC printed Bible")
    scope = next((node for node in edition.iter(f"{{{TEI_NS}}}div") if node.get(f"{{{XML_NS}}}id") == config.get("section_xml_id")), edition) if config.get("section_xml_id") else edition
    scope_notes = [normalized_text(node) for node in scope.iter(f"{{{TEI_NS}}}note")]
    if expected_note not in scope_notes:
        raise ValueError(f"{config['name']} TEI does not contain the expected text-scope note")
    license_element = next((node for node in root.iter(f"{{{TEI_NS}}}licence") if "creativecommons.org/licenses/by-sa/4.0" in node.get("target", "")), None)
    if license_element is None:
        raise ValueError(f"{config['name']} TEI file does not declare CC BY-SA 4.0")

    chapter_scope = scope if config.get("section_xml_id") else edition
    divisions = [node for node in chapter_scope if node.tag == f"{{{TEI_NS}}}div" and node.get("subtype") == "chapter"]
    if [node.get("n") for node in divisions] != [str(i) for i in range(1, config["chapters"] + 1)]:
        raise ValueError(f"{config['name']} chapter divisions differ from the pinned expected sequence")
    chapters = []
    all_lines = []
    for chapter_number, division in enumerate(divisions, start=1):
        label = division.get("n")
        heading_node = division.find(f"{{{TEI_NS}}}label")
        units = []
        for unit_order, line in enumerate(division.iter(f"{{{TEI_NS}}}l"), start=1):
            text = normalized_text(line)
            source_marker = line.get("n")
            unit = {
                "number": unit_order,
                "unit_order": unit_order,
                "source_marker": source_marker,
                "source_element_id": line.get(f"{{{XML_NS}}}id"),
                "source_refs": [ref.get("target") for ref in line.iter(f"{{{TEI_NS}}}ref") if ref.get("target")],
                "text": text,
            }
            if not text:
                unit["source_text_state"] = "empty_source_element"
            units.append(unit)
            all_lines.append(line)
        if not units:
            raise ValueError(f"{config['name']} chapter {label} contains no TEI line elements")
        chapter_notes = []
        for unit in units:
            if unit.get("source_text_state") == "empty_source_element":
                chapter_notes.append({
                    "verse": unit["number"],
                    "marker": f"source label {unit['source_marker']}",
                    "text": "Archive note: the retained TEI line element is empty; no wording has been supplied.",
                    "source_reference": f"{config['file']}, chapter {label}, TEI line element {unit['unit_order']}",
                    "note_origin": "archive",
                })
        chapters.append({
            "chapter": chapter_number,
            "source_chapter_label": label,
            "heading": [normalized_text(heading_node)] if normalized_text(heading_node) else [],
            "units": units,
            "notes": chapter_notes,
        })

    numbered = sum(line.get("n") is not None for line in all_lines)
    empty = sum(not normalized_text(line) for line in all_lines)
    if (len(all_lines), numbered, empty) != (config["lines"], config["numbered"], config["empty"]):
        raise ValueError(f"{config['name']} TEI line inventory changed: {(len(all_lines), numbered, empty)}")
    source_ids = ["SRC-029", config["page_source"], config["file_source"], "SRC-176"]
    anomaly_note = " ".join(config["anomalies"]) if config["anomalies"] else "No duplicate or out-of-sequence numbered labels were detected in this TEI chapter inventory."
    total_unnumbered = len(all_lines) - numbered
    copyright_notice = (
        f"The retained Beta maṣāḥǝft {work_id} TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, "
        "link the source and license, identify this extraction and whitespace normalization, and share "
        "adaptations alike. This file-level license does not establish rights in the unidentified printed "
        "exemplar or relicense other materials in the archive."
    )
    reader = {
        "reader_id": config["reader_id"],
        "canon_id": config["canon_id"],
        "text_origin": "source_transcription",
        "title": f"{config.get('display_title', config['name'])} — Geʽez source transcription (Beta maṣāḥǝft TEI)",
        "display_name": f"{config.get('display_title', config['name'])} · Geʽez · provisional title link; exact edition unverified",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "source_declared_inherited_edition_xml_lang",
        "script_code": "Ethi",
        "edition": f"Beta maṣāḥǝft {work_id} TEI source snapshot, pinned at Works commit {config.get('commit', COMMIT)}",
        "edition_scope": (
            f"The retained TEI file for {work_id} contains an edition division explicitly tagged xml:lang=\"gez\" "
            f"and the selected text scope is labeled ‘{expected_note}.’ Its root xml:lang=\"en\" is retained as a "
            "document-default conflict; TEI inheritance assigns the explicit edition-level language to its nested text. "
            f"The archive links this source provisionally by title to Church-list {config.get('display_title', config['name'])}. "
            "This does not identify the exact printed exemplar or prove identity with a current EOTC edition."
        ),
        "section_label": "Chapter",
        "unit_label": "TEI line element (all numbered and unnumbered elements)",
        "source_ids": source_ids,
        "rights_classification": "open_license",
        "copyright_notice": copyright_notice,
        "commercial_use": "The file-level CC BY-SA 4.0 permits sharing and adaptation, including commercially, subject to attribution, indication of changes, and ShareAlike terms. This does not establish rights in the unidentified printed exemplar or alter the website's separate license notice.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "chapter_count": len(chapters),
        "unit_count": len(all_lines),
        "source_numbered_unit_count": numbered,
        "source_unnumbered_unit_count": total_unnumbered,
        "source_empty_unit_count": empty,
        "chapter_structure_note": (
            f"The pinned TEI selected text scope contains {len(chapters)} ordered chapter divisions and {len(all_lines)} line elements: "
            f"{numbered} have source n labels, {total_unnumbered} do not, and {empty} are empty. "
            "These are source-structure counts, not verse counts or evidence of completeness against the print exemplar. "
            + anomaly_note
        ),
        "transcription_note": (
            "The reader extraction includes every TEI line element in the selected text scope in source order, preserves each source n label "
            "as a string, and normalizes whitespace for display. An empty TEI line remains an empty unit with an explicit state; "
            "no wording or verse label is supplied. Inline TEI markup is flattened in the display text; the unchanged source XML "
            "is retained beside the reader."
        ),
        "editorial_signs_note": "Unnumbered line elements and chapter headings are retained in order and are not relabeled as verses. Source references are retained as metadata. No missing wording, numbering, or translation has been reconstructed.",
        "verification_status": (
            f"Pinned file hash, TEI identity, edition-level Geʽez declaration, file-level license statement, {len(chapters)} chapter divisions, "
            f"and all {len(all_lines)} source line elements were checked locally. This validates extraction structure only. "
            "The exact print exemplar, textual accuracy, physical-edition completeness, and identity with a current EOTC edition remain unverified. "
            + anomaly_note
        ),
        "source_pages": f"readers/source/{config.get('source_dir', 'gospels')}/{config['file']} (unchanged pinned TEI source)",
        "source_snapshot_sha256": digest,
        "additional_notes": (
            "No English translation or parallel text is bundled. The TEI file-level CC BY-SA 4.0 applies to this source file and its adaptation; "
            "it does not establish rights in the unidentified printed exemplar. The Church-list title link is provisional. "
            + config.get("scope_note", "")
        ),
        "chapters": chapters,
    }
    reader_path = ROOT / "readers" / f"{config['reader_id']}.json"
    reader_path.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return reader


def update_archive_and_registries(readers: list[dict]) -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    reg_path = ROOT / "translation-registry.json"
    registry = json.loads(reg_path.read_text(encoding="utf-8"))
    source_map = {source["source_id"]: source for source in archive.get("sources", [])}
    leads = {lead["edition_id"]: lead for lead in registry.get("edition_leads", [])}
    gez = next(language for language in registry["languages"] if language.get("language_tag") == "gez")
    language_records = {row.get("reader_id"): row for row in gez.get("records", [])}
    tei_guidance = source_map.get("SRC-176")
    if tei_guidance:
        tei_guidance["inspection_and_limitations"] = (
            "The TEI P5 Guidelines state that xml:lang indicates an element's content language and is inherited by nested elements. "
            "This standard supports reading an explicit xml:lang=\"gez\" on the edition divisions in the retained Beta maṣāḥǝft TEI "
            "files for Matthew (LIT2709Matthew), Mark (LIT2711Mark), Luke (LIT2713Luke), John (LIT2715John), Acts "
            "(LIT1019Actsof; its Acts text division), Esther (LIT1362Esther), Judith (LIT1701Judith), and Revelation "
            "(LIT3179Revela; its Revelation text division) as applying to their "
            "chapter and line descendants despite each document root's xml:lang=\"en\" default. The standard explains markup semantics; "
            "it does not establish whether a source's language assignment is textually correct, nor does it verify transcription accuracy."
        )
        tei_guidance["archive_status"] = "Official TEI language-inheritance guidance used to interpret the pinned Gospel TEI edition-level language declarations"

    for config, reader in zip(CONFIG, readers):
        digest = reader["source_snapshot_sha256"]
        path = ROOT / "readers" / "source" / config.get("source_dir", "gospels") / config["file"]
        byte_count = path.stat().st_size
        for kind, source_id in (("page", config["page_source"]), ("file", config["file_source"])):
            source_map[source_id] = source_record(config, kind, digest, byte_count)
        edition_id = config.get("edition_id", f"betamasaheft-{config['name'].lower()}-tei-edition-2026")
        leads[edition_id] = {
            "edition_id": edition_id,
            "candidate_canon_id": config["canon_id"],
            "mapping_state": "uncertain",
            "title": f"{config.get('work_label', 'Gospel of ' + config['name'])} ({config['work_id']}), Beta maṣāḥǝft TEI text",
            "witness_type": "digital_edition",
            "language_tag": "gez",
            "language_name": "Geʽez (Classical Ethiopic)",
            "script_code": "Ethi",
            "edition_statement": (
                f"Pinned Beta maṣāḥǝft {config['work_id']} TEI file at Works commit {config.get('commit', COMMIT)}. "
                "Its enclosing edition declares xml:lang=\"gez\" and the selected text scope is labeled ‘Text of the EOTC printed Bible’; "
                "the TEI root default is xml:lang=\"en\". The exact printed exemplar is not identified."
            ),
            "scope_description": (
            f"Provisional title-level link to Church-list {config.get('display_title', config['name'])} based on work identity and the edition note. "
                f"The bundled reader extracts all {config['chapters']} ordered chapter divisions and {config['lines']} TEI line elements "
                f"({config['numbered']} numbered, {config['lines']-config['numbered']} unnumbered, {config['empty']} empty). "
                "This does not establish transcription accuracy, completeness against the physical edition, or exact current EOTC edition identity. "
                + ("Source numbering/empty-element anomalies are preserved as observed. " if config["anomalies"] else "")
                + "The TEI root xml:lang=\"en\" is retained as a metadata conflict; its enclosing xml:lang=\"gez\" governs the extracted text."
            ),
            "source_ids": reader["source_ids"],
            "text_bundled": False,
            "bundled_reader_id": config["reader_id"],
            "rights_status": (
                "The retained TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link the source and license, indicate this extraction, "
                "and share adaptations alike. This file-level license does not establish rights in the unidentified printed exemplar."
            ),
            "rights_classification": "open_license",
            "license_id": "CC-BY-SA-4.0",
            "license_url": LICENSE,
            "review_status": reader["verification_status"],
        }
        language_records[config["reader_id"]] = {
            "canon_id": config["canon_id"],
            "reader_id": config["reader_id"],
            "layer_role": "source_text_transcription",
            "status": "bundled",
            "basis_language_tag": "gez",
            "basis_description": "Beta maṣāḥǝft TEI edition explicitly declares Geʽez and notes ‘Text of the EOTC printed Bible’; title-level Church-list link is provisional. Accuracy and exact current-edition identity are unverified.",
            "rights_status": "CC BY-SA 4.0 (file-level TEI license; rights in unidentified print exemplar not established)",
            "rights_classification": "open_license",
            "source_ids": reader["source_ids"],
        }
        catalogue_row = next((row for row in archive.get("catalogue", []) if row.get("catalogue_id") == config["catalogue_id"]), None)
        if catalogue_row:
            catalogue_row["text_availability_status"] = f"A Geʽez TEI source transcription is bundled with a provisional title-level link to Church-list {config.get('display_title', config['name'])}; exact edition identity is unverified."
            catalogue_row["chapter_count"] = f"{config['chapters']} observed TEI chapter divisions; physical-edition completeness unverified"
            catalogue_row["chapter_order_status"] = f"All {config['chapters']} TEI chapter divisions are ordered 1–{config['chapters']}."
            catalogue_row["completeness_status"] = f"The pinned TEI contains {config['lines']} line elements ({config['numbered']} labeled, {config['lines']-config['numbered']} unlabeled, {config['empty']} empty); accuracy and physical-edition completeness remain unknown."
            catalogue_row["rights_status"] = "The TEI file states CC BY-SA 4.0 for that file and adaptations; rights in the unidentified printed exemplar are not established."
            catalogue_row["reviewer_notes"] = reader["verification_status"]
            catalogue_row["evidence_source_ids"] = list(dict.fromkeys(catalogue_row.get("evidence_source_ids", []) + reader["source_ids"]))

    archive["sources"] = sorted(source_map.values(), key=lambda source: source["source_id"])
    registry["edition_leads"] = sorted(leads.values(), key=lambda lead: lead["edition_id"])
    gez["records"] = sorted(language_records.values(), key=lambda row: row.get("reader_id", ""))
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    reg_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_portable_layer(config: dict, reader: dict) -> None:
    template_path = ROOT / "examples" / "amos-geez-pereira-layer.json"
    record = json.loads(template_path.read_text(encoding="utf-8"))
    base = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
    reader_hash = hashlib.sha256((ROOT / "readers" / f"{config['reader_id']}.json").read_bytes()).hexdigest()
    source_file = next(source_id for source_id in reader["source_ids"] if source_id == config["file_source"])
    commit = config.get("commit", COMMIT)
    record.update({
        "record_id": f"{base}/layer/{config['reader_id']}",
        "work_id": f"{base}/work/betamasaheft-{config['work_id']}",
        "labels": [{"value": f"{config['name']} — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"}],
        "tradition_assertions": [{"tradition_id": f"{base}/tradition/eotc", "canon_id": f"{base}/canon/{config['canon_id']}", "mapping_state": "uncertain", "evidence_source_ids": reader["source_ids"], "notes": "The TEI edition note says ‘Text of the EOTC printed Bible’ and explicitly declares Geʽez; this supports a provisional title-level link only. Exact current-edition identity, physical-edition completeness, and transcription accuracy remain unverified."}],
        "witness": {"witness_id": f"{base}/witness/betamasaheft-{config['work_id']}", "witness_type": "digital_edition", "title": f"Beta maṣāḥǝft {config['work_id']} TEI text", "date_statement": f"Source file pinned at Works commit {commit}; exact print-exemplar date unknown", "repository_or_publisher": "Beta maṣāḥǝft, University of Hamburg", "shelfmark_or_edition_id": config["work_id"], "editorial_policy": "Provider says the text was digitized from modern Vulgata printed editions and converted to TEI; the exact printed exemplar is not identified. The retained XML remains available alongside the whitespace-normalized display extraction.", "source_ids": [source_file]},
        "language_tag": "gez", "language_name_as_recorded": "Geʽez (Classical Ethiopic)", "script_code": "Ethi", "basis_path": ["gez"], "agents": [],
        "content_package": {"uri": f"../readers/{config['reader_id']}.json", "media_type": "application/json", "sha256": reader_hash, "format_version": "1", "json_pointer": ""},
        "coverage": {"extent_state": "complete_for_declared_edition", "extent_basis": "source_inventory", "unit_count": reader["unit_count"], "structure_description": f"All {reader['unit_count']} TEI line elements from {reader['chapter_count']} explicit chapter divisions are extracted. This is complete for the declared TEI edition scope only; completeness against the physical printed exemplar is unverified.", "missing_or_lacunose_ranges": [], "supplements_and_editorial_signs": "Whitespace normalized for display; inline markup flattened but unchanged source XML retained. Empty TEI line elements remain explicit empty units; none is supplied with wording.", "numbering_policy": "Preserve every TEI source n label exactly as present and retain unnumbered lines in source order. Do not normalize duplicate or anomalous source labels."},
        "rights": {"status": "open_license", "statement": "The TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link the source and license, identify this extraction and whitespace normalization, and share adaptations alike. This file-level license does not establish rights in the unidentified printed exemplar.", "license_id": "CC-BY-SA-4.0", "rights_holder": "Beta maṣāḥǝft TEI file; underlying print rights not established", "attribution_required": True, "territory_or_term_limits": "The file-level license applies to the TEI file and its adaptation; do not infer rights in the unidentified printed source.", "evidence_source_ids": [source_file]},
        "review_dimensions": [
            {"dimension": "identity", "state": "checked_with_limits", "scope": f"TEI work id {config['work_id']} and Church-list title checked; physical exemplar and exact current-edition identity unresolved.", "reviewer": None, "review_method": "source_inspection", "review_process": "Pinned TEI header, edition division and Church-list title inspected", "reviewed_at": "2026-10-25", "evidence_source_ids": reader["source_ids"], "notes": "Provisional title link only."},
            {"dimension": "language_identification", "state": "checked_with_limits", "scope": "TEI root xml:lang=en and enclosing edition xml:lang=gez inspected; every extracted line is inside that edition scope.", "reviewer": None, "review_method": "automated_validation", "review_process": "Pinned source XML language declarations and TEI inheritance rules checked", "reviewed_at": "2026-10-25", "evidence_source_ids": [source_file, "SRC-176"], "notes": "Edition-level gez applies to nested text; root-level en remains recorded as a conflict."},
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": f"All {reader['chapter_count']} chapter divisions and {reader['unit_count']} line elements checked against the pinned XML.", "reviewer": None, "review_method": "automated_validation", "review_process": "Offline TEI parser validates source hash, divisions and exact line-element inventory", "reviewed_at": "2026-10-25", "evidence_source_ids": [source_file], "notes": "Source order and labels preserved; this is not print collation."},
            {"dimension": "completeness", "state": "unknown", "scope": "No comparison against the exact printed exemplar or manuscript witnesses was performed.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": [source_file], "notes": "Extraction includes all TEI line elements in the declared edition scope; physical-edition completeness unknown."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No independent collation against the printed source or manuscripts was performed.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": [source_file], "notes": "Structural checks do not establish wording accuracy."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "File-level CC BY-SA 4.0 statement inspected in the pinned TEI file.", "reviewer": None, "review_method": "source_inspection", "review_process": "File-specific license retained separately from website terms", "reviewed_at": "2026-10-25", "evidence_source_ids": [source_file], "notes": "Underlying print rights remain unestablished."},
        ],
        "publication_state": "bundled", "community_access_note": None,
        "additional_notes": "This is a source transcription, not an English translation. Source numbering anomalies, if any, are described in the reader and preserved verbatim in the bundled source TEI.",
    })
    out = ROOT / "examples" / f"{config['reader_id']}-layer.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> list[dict]:
    readers = [build_one(config) for config in CONFIG]
    update_archive_and_registries(readers)
    for config, reader in zip(CONFIG, readers):
        write_portable_layer(config, reader)
    for reader in readers:
        print(f"Built {reader['reader_id']}: {reader['chapter_count']} chapters, {reader['unit_count']} TEI lines, SHA-256 {reader['source_snapshot_sha256']}")
    return readers


if __name__ == "__main__":
    main()
