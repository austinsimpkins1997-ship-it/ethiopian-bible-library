"""Build a cautious transcription of the Eritrean Diocese page's numbered list.

This is a page-level evidence record, not an independently approved Eritrean
canon, an edition-level witness, or a crosswalk to the Ethiopian list.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "research" / "eritrea-canon-source-transcription.json"

OLD_TESTAMENT = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
    "Judges", "Ruth", "I and II Samuel", "I and II Kings", "I Chronicles",
    "II Chronicles", "Jublee", "Enoch", "Ezra and Nehemia",
    "Ezra (2nd) and Ezra Sutuel", "Tobit", "Judith", "Esther", "I Maccabees",
    "II and III Maccabees", "Job", "Psalms", "Proverbs", "Tegsats (Reproof)",
    "Metsihafe Tibeb (the Book of Wisdom)", "Ecclesiastes", "The Song of Songs",
    "Isaiah", "Jeremiah", "Ezekiel", "Daniel", "Hosea", "Amos", "Micah",
    "Joel", "Obadiah", "Jonah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi", "Book of Joshua the son of Sirach",
    "The Book of Josephas the Son of Bengorion",
]

NEW_TESTAMENT = [
    "Matthew", "Mark", "Luke", "John", "The Acts", "Romans", "I Corinthians",
    "II Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "I Thessalonians", "II Thessalonians", "I Timothy", "II Timothy", "Titus",
    "Philemon", "Hebrews", "I Peter", "II Peter", "I John", "II John",
    "III John", "James", "Jude", "Revelation", "Sirate Tsion (the Book of order)",
    "Tizaz (the book of Herald)", "Gitsew", "Abtilis", "The I book of Dominos",
    "The II book of Dominos", "The book of Clement", "Didascalia | Didache",
]


def main() -> None:
    archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
    source = next((s for s in archive["sources"] if s["source_id"] == "SRC-045"), None)
    if source is None:
        raise ValueError("Missing SRC-045 institutional-page evidence record.")
    if len(OLD_TESTAMENT) != 46 or len(NEW_TESTAMENT) != 35:
        raise ValueError("Source transcription must preserve the page's 46 + 35 numbered labels.")
    if OLD_TESTAMENT[-1] != "The Book of Josephas the Son of Bengorion" or NEW_TESTAMENT[-1] != "Didascalia | Didache":
        raise ValueError("Source list boundaries changed; review before rebuilding.")
    record = {
        "record_id": "eritrea-diocese-canon-page-transcription-v1",
        "record_type": "institutional_webpage_list_transcription",
        "tradition_label": "Eritrean Orthodox Tewahdo Church (as named by the cited page)",
        "source_id": source["source_id"],
        "source_url": source["url"],
        "source_title": source["source_name"],
        "page_attribution": "The page is hosted by the Eritrean Orthodox Tewahdo Church Diocese of the U.S.A. and Canada, is signed Eden Adhanom, and cites the Ethiopian Church canon page and Wikipedia.",
        "transcription_scope": "The numbered English Old Testament and New Testament labels shown on that page, preserving its spelling, grouping, order, and the final slash-separated label.",
        "review_status": "Transcribed from the cited live page; not checked against a synodical canon list, Eritrean-language source, printed Bible contents, or manuscript witnesses.",
        "counts_as_numbered_by_page": {
            "Old Testament": {"count": len(OLD_TESTAMENT), "entries": OLD_TESTAMENT},
            "New Testament": {"count": len(NEW_TESTAMENT), "entries": NEW_TESTAMENT},
            "total_numbered_entries": len(OLD_TESTAMENT) + len(NEW_TESTAMENT),
        },
        "interpretive_cautions": [
            "The page calls these 81 canonized books, but the count here is the page's numbering, not a verified count of distinct textual works after grouped entries are resolved.",
            "The source itself says its narrower list is identical to the western Bible and then includes Enoch, Jubilees, and three Meqabyan books; preserve that inconsistency as source wording, not a resolved taxonomy.",
            "The final New Testament label is printed as 'Didascalia | Didache'. This record does not decide whether that denotes one combined entry, alternatives, or an editorial error.",
            "This evidence is separate from the Ethiopian Orthodox Tewahedo Church's list. Similar counts or labels do not establish identity of canon, edition, translation, or church practice.",
        ],
        "reuse_note": "Metadata transcription only. The source page is linked for context; this record grants no rights to scripture editions or translations.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {OUTPUT.relative_to(ROOT)}: 46 OT + 35 NT source-numbered labels.")


if __name__ == "__main__":
    main()
