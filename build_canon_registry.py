"""Build the Church-list coverage index without treating catalogue rows as canon units."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "canon-registry.json"

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
    ("Ezra (2nd) and Ezra Sutuel", ["eotc-019"]),
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
OFFICIAL_LABELS = {
    "Jubilees": "Jublee",
    "Book of Joshua the Son of Sirac": "Book of Joshua the son of Sirac",
    "Metsihafe Tibeb (books of wisdom)": "Metsihafe Tibeb (the books of wisdom)",
    "Acts": "The Acts",
    "Sirate Tsion (Book of Order)": "Sirate Tsion (the book of order)",
    "Tizaz (Book of Herald)": "Tizaz (the book of Herald)",
    "I Book of Dominos": "The I book of Dominos",
    "II Book of Dominos": "The II book of Dominos",
    "Book of Clement": "The book of Clement",
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
    13: "jubilees-geez-hacohen",
    14: "enoch-geez-eotc",
    23: "psalms-geez-ludolf-hacohen",
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
    13: "jubilees-geez-hacohen.json",
    14: "enoch-geez-eotc.json",
    23: "psalms-geez-ludolf.json",
}
SOURCE_METADATA = {
    23: {
        "source_ids": ["SRC-029", "SRC-036", "SRC-058", "SRC-059", "SRC-067", "SRC-068", "SRC-069"],
        "mapping_note": (
            "The Church list names Psalms; this reader contains the TAU-hosted Geʽez transcription of Ludolf's Psalter in 151 Rahlfs-numbered pages. "
            "The reader preserves source label anomalies and has not been independently collated. This supports navigation, not an exact canon crosswalk or completeness claim."
        ),
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


def main() -> None:
    books = []
    for number, (name, catalogue_ids) in enumerate(OT, 1):
        reader_id = READER_IDS.get(number)
        bundled_reader = bool(reader_id and (ROOT / "readers" / READER_FILES[number]).is_file())
        source_metadata = SOURCE_METADATA.get(number, {})
        reader_status = (
            "Bundled: Geʽez EOTC printed-edition transcription" if number == 14 and bundled_reader else
            "Bundled: Geʽez Ludolf Psalter transcription" if number == 23 and bundled_reader else
            "Bundled: Geʽez + English companion" if number == 1 and bundled_reader else
            "Bundled: Geʽez source transcription" if bundled_reader else
            source_metadata.get("reader_status", "No text bundled")
        )
        books.append({
            "canon_id": f"eotc-ot-{number:02d}", "section": "Old Testament",
            "section_number": number, "display_name": name,
            "source_label": OFFICIAL_LABELS.get(name, name),
            "catalogue_ids": catalogue_ids, "source_ids": source_metadata.get("source_ids", ["SRC-029"]),
            "reader_status": reader_status,
            "reader_id": reader_id if bundled_reader else None,
            "mapping_note": (
                "The Church list's ‘I Maccabees’/‘II and III Maccabees’ labels are preserved. "
                "Their mapping to the separately catalogued Meqabyan texts needs tradition-specific review."
                if number in (20, 21) else
                source_metadata.get("mapping_note", "") if source_metadata else
                "This is a grouped title in the Church list; separate catalogue rows are discovery aids, not proof of exact textual boundaries."
                if len(catalogue_ids) > 1 else ""
            ),
        })
    for number, name in enumerate(NT_NAMES, 1):
        books.append({
            "canon_id": f"eotc-nt-{number:02d}", "section": "New Testament",
            "section_number": number, "display_name": name,
            "source_label": OFFICIAL_LABELS.get(name, name),
            "catalogue_ids": [f"eotc-{54 + number:03d}"],
            "source_ids": ["SRC-029"],
            "reader_status": "No text bundled", "reader_id": None,
            "mapping_note": "",
        })
    if len(OT) != 46 or len(NT_NAMES) != 35 or len(books) != 81:
        raise ValueError("Church-list registry must contain 46 Old Testament and 35 New Testament entries.")
    registry = {
        "source_id": "SRC-029",
        "basis": "The Ethiopian Orthodox Tewahedo Church’s own English canon page lists 46 Old Testament and 35 New Testament entries and explicitly states a total of 81. Grouped names are kept as that source presents them; they are not silently split into separate canonical units.",
        "mapping_caution": "Links to this archive’s 89 research rows support navigation only. They do not independently establish a title’s canonical mapping, text identity, completeness, or translation.",
        "book_count": len(books),
        "reader_count": sum(entry["reader_id"] is not None for entry in books),
        "books": books,
    }
    OUTPUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {OUTPUT.name}: {len(OT)} Old Testament entries + {len(NT_NAMES)} New Testament entries.")


if __name__ == "__main__":
    main()
