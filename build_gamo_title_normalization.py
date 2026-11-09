"""Add English navigation labels decoded from eBible's standard book IDs.

This maps the publisher's standard codes to English navigation names and records
provisional title-level catalogue candidates without asserting canon membership.
"""

from __future__ import annotations

import json
from pathlib import Path
from book_code_crosswalks import PUBLISHER_BOOK_CODE_CANDIDATES, candidate_note

ROOT = Path(__file__).resolve().parent
MENU = ROOT / "research" / "gamo-menu.json"
OUTPUT = ROOT / "research" / "gamo-title-normalization.json"
SOURCE_ID = "SRC-196"

BOOK_NAMES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers", "DEU": "Deuteronomy",
    "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth", "1SA": "1 Samuel", "2SA": "2 Samuel",
    "1KI": "1 Kings", "2KI": "2 Kings", "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra",
    "NEH": "Nehemiah", "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Songs", "ISA": "Isaiah", "JER": "Jeremiah",
    "LAM": "Lamentations", "EZK": "Ezekiel", "DAN": "Daniel", "HOS": "Hosea", "JOL": "Joel",
    "AMO": "Amos", "OBA": "Obadiah", "JON": "Jonah", "MIC": "Micah", "NAM": "Nahum",
    "HAB": "Habakkuk", "ZEP": "Zephaniah", "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
    "MAT": "Matthew", "MRK": "Mark", "LUK": "Luke", "JHN": "John", "ACT": "Acts", "ROM": "Romans",
    "1CO": "1 Corinthians", "2CO": "2 Corinthians", "GAL": "Galatians", "EPH": "Ephesians",
    "PHP": "Philippians", "COL": "Colossians", "1TH": "1 Thessalonians", "2TH": "2 Thessalonians",
    "1TI": "1 Timothy", "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon", "HEB": "Hebrews",
    "JAS": "James", "1PE": "1 Peter", "2PE": "2 Peter", "1JN": "1 John", "2JN": "2 John",
    "3JN": "3 John", "JUD": "Jude", "REV": "Revelation",
}


def build() -> dict:
    menu = json.loads(MENU.read_text(encoding="utf-8"))
    entries = []
    seen_codes: set[str] = set()
    for item in menu["entries"]:
        code = item["publisher_book_code"]
        if code not in BOOK_NAMES:
            raise ValueError(f"No English codebook name registered for Gamo publisher code {code!r}")
        if code in seen_codes:
            raise ValueError(f"Duplicate Gamo publisher code: {code}")
        seen_codes.add(code)
        reader_path = ROOT / "readers" / f"{item['reader_id']}.json"
        reader = json.loads(reader_path.read_text(encoding="utf-8"))
        source_label = item["source_title_label"]
        english_name = BOOK_NAMES[code]
        reader["display_name"] = f"{english_name} · Gamo ({code})"
        reader["title"] = f"{english_name} — Gamo text ({source_label})"
        reader["normalized_title_en"] = english_name
        reader["source_title_label"] = source_label
        reader["title_normalization"] = {
            "method": "publisher_standard_book_code_lookup",
            "publisher_book_code": code,
            "normalized_english_name": english_name,
            "source_title_label": source_label,
            "is_translation_of_source_label": False,
            "canon_mapping": "uncertain_title_candidate" if code in PUBLISHER_BOOK_CODE_CANDIDATES else "not_assigned",
            "source_ids": ["SRC-168", "SRC-171", SOURCE_ID],
            "note": (
                "English navigation label decoded from the publisher's standard book code. The Gamo source label is preserved verbatim; this is not a translation of that label. "
                + candidate_note(code, PUBLISHER_BOOK_CODE_CANDIDATES[code])
                if code in PUBLISHER_BOOK_CODE_CANDIDATES else
                "English navigation label decoded from the publisher's standard book code. The Gamo source label is preserved verbatim; this is not a translation of that label. No distinct 81-entry catalogue candidate is assigned."
            ),
        }
        reader_path.write_bytes((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        entries.append({
            "position": item["position"], "publisher_book_code": code,
            "source_title_label": source_label, "normalized_title_en": english_name,
            "reader_id": item["reader_id"], "normalization_method": "publisher_standard_book_code_lookup",
            "source_ids": ["SRC-168", "SRC-171", SOURCE_ID],
            "translation_of_gamo_label": False,
            "canon_mapping_state": "uncertain" if code in PUBLISHER_BOOK_CODE_CANDIDATES else "not_mapped",
            "canon_crosswalk": PUBLISHER_BOOK_CODE_CANDIDATES.get(code),
        })
    if len(entries) != 66:
        raise ValueError(f"Expected all 66 publisher menu entries; found {len(entries)}")
    return {
        "record_type": "title_code_normalization_index",
        "edition_id": menu["edition_id"], "language_tag": menu["language_tag"],
        "script_code": menu["script_code"], "observed_at": menu["observed_at"],
        "scope": "English navigation names for the 66 observed Gamo publisher-menu entries, decoded only from their standard book codes.",
        "limitations": "This is not a Gamo translation, transliteration, explanation of title semantics, or scripture translation. Each original Gamo label remains alongside the English code-derived label. Standard-code title candidates are provisional discovery pointers only; they do not establish textual identity, canon membership, tradition affiliation, scope equivalence, or completeness. Lamentations has no distinct candidate in the 81-entry list.",
        "code_system": "SIL25-UBS26 three-letter standard Bible book codes, as documented in eBible.org OXES documentation.",
        "source_ids": ["SRC-168", "SRC-171", SOURCE_ID], "entries": entries,
    }


if __name__ == "__main__":
    data = build()
    OUTPUT.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"Normalized English navigation labels for {len(data['entries'])} Gamo readers; source labels remain preserved.")
