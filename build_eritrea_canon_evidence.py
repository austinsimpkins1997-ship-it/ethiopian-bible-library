"""Build a cautious transcription of the Eritrean Diocese page's numbered list.

This is a page-level evidence record, not an independently approved Eritrean
canon, an edition-level witness, or a crosswalk to the Ethiopian list.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "research" / "eritrea-canon-source-transcription.json"
COMPARISON_OUTPUT = ROOT / "research" / "eritrea-eotc-label-comparison.json"
COMPARISON_HTML = ROOT / "research" / "eritrea-eotc-label-comparison.html"
COMPARISON_SCHEMA = "../schemas/eritrea-canon-label-comparison.schema.json"

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
        "source_page_checked_at": "2026-10-27",
        "page_locator": "Page heading 'Canonized Books'; numbered Old Testament and New Testament list; references and author attribution at the end of the same page.",
        "transcription_scope": "The numbered English Old Testament and New Testament labels shown on that page, preserving its spelling, grouping, order, and the final slash-separated label.",
        "review_status": "The live page was reinspected on 2026-10-27 and its numbered English labels were compared with this transcription: 46 Old Testament and 35 New Testament entries. This is verification of the webpage transcription only; it was not checked against a synodical canon list, Eritrean-language source, printed Bible contents, or manuscript witnesses.",
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
    build_label_comparison(archive, record)
    print(f"Built {OUTPUT.relative_to(ROOT)}: 46 OT + 35 NT source-numbered labels.")


def build_label_comparison(archive: dict, eritrea_record: dict) -> dict:
    """Compare source labels by section ordinal without asserting title/work identity."""
    eotc_books = archive.get("canon_registry", {}).get("books", [])
    if not eotc_books:
        raise ValueError("The EOTC source-label comparison requires its registered list.")
    sections = eritrea_record["counts_as_numbered_by_page"]
    items = []
    section_counts = {}
    for section in ("Old Testament", "New Testament"):
        eotc_section = sorted(
            (book for book in eotc_books if book.get("section") == section),
            key=lambda book: book.get("section_number", 0),
        )
        page_labels = sections[section]["entries"]
        if len(eotc_section) != sections[section]["count"] or len(page_labels) != len(eotc_section):
            raise ValueError(f"The two {section} lists cannot be compared position-by-position.")
        exact_count = 0
        normalized_count = 0
        for position, (book, page_label) in enumerate(zip(eotc_section, page_labels), 1):
            eotc_label = book.get("source_label")
            if not isinstance(eotc_label, str) or not eotc_label.strip():
                raise ValueError(f"EOTC source label missing at {section} position {position}.")
            normalized_eotc = " ".join(unicodedata.normalize("NFKC", eotc_label).split()).casefold()
            normalized_page = " ".join(unicodedata.normalize("NFKC", page_label).split()).casefold()
            exact = eotc_label == page_label
            normalized = normalized_eotc == normalized_page
            exact_count += exact
            normalized_count += normalized
            items.append({
                "section": section,
                "section_position": position,
                "eotc_source_label": eotc_label,
                "eritrea_diocese_page_label": page_label,
                "exact_literal_label_match": exact,
                "match_after_nfkc_whitespace_and_case_normalization": normalized,
            })
        section_counts[section] = {
            "entry_count": len(eotc_section),
            "exact_literal_label_matches": exact_count,
            "matches_after_nfkc_whitespace_and_case_normalization": normalized_count,
        }
    exact_total = sum(value["exact_literal_label_matches"] for value in section_counts.values())
    normalized_total = sum(value["matches_after_nfkc_whitespace_and_case_normalization"] for value in section_counts.values())
    result = {
        "schema_version": 1,
        "title": "Ethiopian and Eritrean Diocese canon-page label comparison",
        "comparison_method": "Compare the EOTC canon registry's source_label with the Eritrean Diocese page transcription at the same section ordinal. Exact comparison preserves spelling, capitalization, punctuation, and grouping. The normalized comparison applies Unicode NFKC, whitespace compaction, and case-folding only.",
        "scope_note": "This compares English labels at corresponding section positions; it is not a canon crosswalk or a claim that similarly placed or spelled labels identify the same work, edition, textual scope, or church practice. The Eritrean source is an institutional Diocese webpage that cites other sources; this comparison does not establish synod-approved Eritrean canon status.",
        "source_ids": ["SRC-029", eritrea_record["source_id"]],
        "source_registry": "archive.json#/sources",
        "eritrea_transcription": "research/eritrea-canon-source-transcription.json",
        "entry_count": len(items),
        "exact_literal_label_matches": exact_total,
        "exact_literal_label_differences": len(items) - exact_total,
        "matches_after_nfkc_whitespace_and_case_normalization": normalized_total,
        "differences_after_nfkc_whitespace_and_case_normalization": len(items) - normalized_total,
        "section_counts": section_counts,
        "entries": items,
    }
    COMPARISON_OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mismatches = [entry for entry in items if not entry["exact_literal_label_match"]]
    rows = "\n".join(
        "<tr><td>{} · {}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            escape(entry["section"]), entry["section_position"],
            escape(entry["eotc_source_label"]), escape(entry["eritrea_diocese_page_label"]),
            "Case/spacing/Unicode form only" if entry["match_after_nfkc_whitespace_and_case_normalization"] else "Label text differs",
        )
        for entry in mismatches
    )
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ethiopian and Eritrean Diocese canon-page label comparison — Ethiopian Bible Library</title>
<style>:root{{color-scheme:light;--ink:#183d37;--muted:#5f716d;--line:#ded9cc;--paper:#fbf8f0;--gold:#b58845}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:#25332f;font:16px/1.6 system-ui,sans-serif}}main{{max-width:1000px;margin:0 auto;padding:32px 20px 72px}}h1,h2{{font-family:Georgia,serif;color:var(--ink);line-height:1.2}}h1{{font-size:clamp(1.8rem,4vw,2.7rem)}}a{{color:#195d50}}.note{{border-left:3px solid var(--gold);padding:12px 16px;background:#fff;margin:1.2rem 0}}.stats{{display:flex;flex-wrap:wrap;gap:.6rem;margin:1.2rem 0}}.stats span{{border:1px solid var(--line);background:#fff;padding:.55rem .8rem}}.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{padding:.65rem .75rem;border:1px solid var(--line);text-align:left;vertical-align:top}}th{{color:var(--ink)}}footer{{margin-top:2rem;color:var(--muted)}}
</style></head><body><main>
<p><a href="eritrea.html">← Eritrea research note</a></p>
<p><a href="../index.html#sources">Archive sources &amp; method</a></p>
<h1>Ethiopian and Eritrean Diocese page-label comparison</h1>
<p>This report compares the English labels in the Ethiopian Orthodox Tewahedo Church list with the numbered list on the Eritrean Orthodox Tewahdo Church Diocese of the U.S.A. and Canada webpage. It aligns rows by Old/New Testament section and printed position only.</p>
<div class="note"><strong>Reading limit:</strong> This is a literal label comparison, not a canon crosswalk. Matching labels do not prove identical works, editions, textual scope, or church practice. The Eritrean input is a Diocese webpage transcription, not an independently verified synod-approved list.</div>
<div class="stats"><span><strong>{len(items)} / 81</strong> numbered positions compared</span><span><strong>{exact_total} / 81</strong> exact source-label matches</span><span><strong>{len(items)-exact_total}</strong> exact-label differences</span><span><strong>{normalized_total} / 81</strong> match after case, whitespace, and Unicode normalization</span></div>
<p>After normalization, {len(items)-normalized_total} label strings still differ. A normalized match only removes case, whitespace, and Unicode-form differences; it does not equate synonyms, grouped titles, or textual works.</p>
<h2>Positions with different literal labels</h2>
<div class="table-wrap"><table><thead><tr><th>Section position</th><th>EOTC list source label</th><th>Diocese page label</th><th>String comparison</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Inputs: <a href="../index.html#source-src-029">EOTC official English canon list (SRC-029)</a> and <a href="../index.html#source-src-045">Eritrean Orthodox Diocese of the U.S.A. and Canada webpage (SRC-045)</a>. <a href="eritrea-canon-source-transcription.json" download>Download Eritrean page transcription</a> · <a href="eritrea-eotc-label-comparison.json" download>Download all 81 comparison rows</a> · <a href="../schemas/eritrea-canon-label-comparison.schema.json">View JSON Schema</a>.</p>
<footer>Generated from the local canon registry and the retained page-label transcription. Source labels, not display labels, are compared.</footer>
</main></body></html>
'''
    COMPARISON_HTML.write_text(html, encoding="utf-8")
    return result


if __name__ == "__main__":
    main()
