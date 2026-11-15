"""Index existing English witnesses for comparison, without changing any text/canon record."""
from __future__ import annotations

import json
import re
from pathlib import Path

from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
# Explicit work-family navigation for retained non-USFM witnesses. This is not a
# claim that a modern English edition translates these particular Ge'ez words.
GEEZ_CODES = {
    "genesis-geez-dillmann-hacohen": "GEN", "exodus-geez-dillmann-hacohen": "EXO",
    "leviticus-geez-dillmann-hacohen": "LEV", "numbers-geez-dillmann-hacohen": "NUM",
    "deuteronomy-geez-dillmann-hacohen": "DEU", "joshua-geez-dillmann-hacohen": "JOS",
    "judges-geez-dillmann-hacohen": "JDG", "ruth-geez-dillmann-hacohen": "RUT",
    "psalms-geez-ludolf-hacohen": "PSA", "amos-geez-pereira-ghebre-tau": "AMO",
    "joel-geez-dillmann-hacohen-tau": "JOL", "obadiah-geez-bachmann-theot": "OBA",
    "jonah-geez-lofgren-ghebre-tau": "JON", "nahum-geez-lofgren-ghebre-tau": "NAM",
    "habakkuk-geez-lofgren-ghebre-tau": "HAB", "zephaniah-geez-lofgren-hacohen-tau": "ZEP",
    "haggai-geez-lofgren-ghebre-tau": "HAG", "malachi-geez-lofgren-ghebre-tau": "MAL",
    "sirach-geez-dillmann-hacohen-tau": "SIR", "samuel-i-geez-research": "1SA",
    "samuel-ii-geez-research": "2SA", "kings-i-geez-research": "1KI", "kings-ii-geez-research": "2KI",
}


def work_code(reader: dict) -> tuple[str | None, str]:
    reader_id = reader["reader_id"]
    if reader_id in GEEZ_CODES:
        return GEEZ_CODES[reader_id], "explicit_historical_work_family_reference"
    location = str(reader.get("source_pages", ""))
    matches = set(re.findall(r"\b\d{2,3}-([A-Z0-9]{3})[^/; ]*\.usfm\b", location))
    # Amharic retained HTML pages use the publisher's standard book identifier.
    if reader_id.startswith(("amh2003-", "gamo-")):
        matches.update(re.findall(r"\b([1-4]?[A-Z]{2,3})\.htm\b", location))
    if len(matches) == 1:
        return matches.pop(), "retained_publisher_book_code"
    return None, "unresolved_book_code"


def build(archive: dict) -> dict:
    readers = archive["readers"]
    english = {}
    for reader in readers:
        if reader["reader_id"].startswith("webbe-2020-") and reader.get("language_tag") == "en":
            code, _ = work_code(reader)
            if code is None or code in english:
                raise ValueError(f"Missing/duplicate English book code: {reader['reader_id']}")
            english[code] = reader
    records = {}
    for reader in readers:
        code, basis = work_code(reader)
        reference = english.get(code)
        already_english = reader.get("language_tag") in {"en", "eng"}
        records[reader["reader_id"]] = {
            "state": "already_english" if already_english else "english_reference" if reference else "unavailable",
            "work_code": code,
            "mapping_basis": basis,
            "english_reader_id": reference["reader_id"] if reference else None,
            "source_ids": sorted(set(reader.get("source_ids", []) + (reference.get("source_ids", []) if reference else []))),
            "relationship": "Separate published English edition for comparison; not a translation of this exact witness or a verified verse/chapter alignment.",
        }
    return {
        "schema_version": 1,
        "scope": "Work-family navigation among existing public reader packages. Does not alter canon, rights, text, or review status.",
        "counts": {
            "readers": len(readers), "already_english": sum(r["state"] == "already_english" for r in records.values()),
            "non_english_with_reference": sum(r["state"] == "english_reference" for r in records.values()),
            "unavailable": sum(r["state"] == "unavailable" for r in records.values()),
            "english_reference_books": len(english),
        },
        "readers": records,
    }


def write(archive: dict, root: Path = ROOT) -> dict:
    result = build(archive)
    write_text_atomically(root / "english-reference-index.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    report = write(json.loads((ROOT / "archive.json").read_text(encoding="utf-8")))
    print(json.dumps(report["counts"]))
