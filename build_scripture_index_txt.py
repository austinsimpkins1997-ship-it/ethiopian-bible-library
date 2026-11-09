"""Build a complete plain-text reference index from the local archive data."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "scripture-index.txt"


def _unit_label(unit: dict) -> str:
    for field in ("number", "source_marker", "unit_order"):
        value = unit.get(field)
        if value is not None and str(value).strip():
            return str(value).strip()
    return "[unlabeled source unit]"


def _chapter_line(chapter: dict, index: int) -> str:
    chapter_label = chapter.get("chapter")
    if chapter_label is None:
        chapter_label = index
    units = chapter.get("verses")
    if units is None:
        units = chapter.get("units", [])
    labels = ", ".join(_unit_label(unit) for unit in units)
    if not labels:
        labels = "[no numbered units in this chapter record]"
    return f"  Chapter {chapter_label}: {labels}"


def build_text(archive: dict) -> str:
    catalogue = archive.get("catalogue", [])
    readers = {reader.get("reader_id"): reader for reader in archive.get("readers", [])}
    canon_books = archive.get("canon_registry", {}).get("books", [])
    corpora = archive.get("translation_registry", {}).get("research_corpora", [])
    canon_by_catalogue: dict[str, list[dict]] = {}
    for canon_book in canon_books:
        for catalogue_id in canon_book.get("catalogue_ids", []):
            canon_by_catalogue.setdefault(catalogue_id, []).append(canon_book)

    lines = [
        "ETHIOPIAN BIBLE LIBRARY — COMPLETE SCRIPTURE REFERENCE INDEX",
        "Generated from the locally bundled archive data.",
        "",
        f"Catalogue rows: {len(catalogue)}.",
        "These are catalogue display rows, not a claim that there are 90 distinct canon books.",
        "The archive's Church-list register separately records 81 entries (46 Old Testament and 35 New Testament).",
        "This file is an index of source chapter and verse/unit labels; it does not reproduce scripture wording.",
        "Labels and ordering are preserved as stored by each reader. No verse numbering is silently normalized.",
        "Canon-linked reader records and research-only readers are identified separately. Research-only links",
        "do not establish denominational affiliation, exact edition identity, completeness, or translation accuracy.",
        "Works outside the 90 catalogue rows (including 2 Enoch and 3 Enoch) are not counted here.",
        "",
    ]

    total_canon_readers = 0
    total_research_readers = 0
    for row in catalogue:
        row_id = row.get("catalogue_id", "[no catalogue id]")
        row_name = row.get("display_name", "[untitled]")
        canon_records = canon_by_catalogue.get(row_id, [])
        canon_ids = {record.get("canon_id") for record in canon_records if record.get("canon_id")}
        linked_reader_ids = {
            reader_id for reader_id, reader in readers.items()
            if reader.get("canon_id") in canon_ids
        }
        research_corpus_by_reader = {
            corpus.get("reader_id"): corpus
            for corpus in corpora
            if corpus.get("candidate_canon_id") in canon_ids and corpus.get("reader_id") in readers
        }
        research_reader_ids = set(research_corpus_by_reader) - linked_reader_ids
        total_canon_readers += len(linked_reader_ids)
        total_research_readers += len(research_reader_ids)

        lines.extend([
            "=" * 88,
            f"{row_id}  {row_name}",
            f"Section: {row.get('tradition_group', 'Unspecified')}",
            f"Catalogue note: {row.get('canon_view') or row.get('identity_status') or 'No mapping note recorded.'}",
            f"Edition / translation: {row.get('edition_or_translation') or 'Not identified.'}",
            f"Catalogue chapter note: {row.get('chapter_count') or 'Not established.'}",
            f"Text availability: {row.get('text_availability_status') or 'Not recorded.'}",
            f"Completeness: {row.get('completeness_status') or 'Not assessed.'}",
        ])
        if row.get("rights_status"):
            lines.append(f"Rights note: {row['rights_status']}")
        if canon_records:
            links = "; ".join(
                f"{c.get('canon_id')} — {c.get('display_name')} [{c.get('mapping_state', 'mapping state unrecorded')}]"
                for c in canon_records
            )
            lines.append(f"Church-list crosswalk record(s): {links}")
        else:
            lines.append("Church-list crosswalk: none recorded.")

        if not linked_reader_ids and not research_reader_ids:
            lines.append("Scripture references: No reader package is currently linked to this catalogue row.")
        for reader_id in sorted(linked_reader_ids):
            reader = readers[reader_id]
            lines.append("")
            lines.append(f"CANON-LINKED READER — {reader.get('title', reader_id)} [{reader_id}]")
            lines.append(
                f"Observed: {reader.get('chapter_count', len(reader.get('chapters', [])))} chapters; "
                f"{reader.get('unit_count', 'unit count not recorded')} {reader.get('unit_label', 'source units')}."
            )
            for i, chapter in enumerate(reader.get("chapters", []), start=1):
                lines.append(_chapter_line(chapter, i))
            if reader.get("verification_status"):
                lines.append(f"Reader verification scope: {reader['verification_status']}")

        for reader_id in sorted(research_reader_ids):
            reader = readers[reader_id]
            corpus = research_corpus_by_reader[reader_id]
            lines.append("")
            lines.append(
                f"RESEARCH-ONLY READER — {reader.get('title', reader_id)} [{reader_id}]"
            )
            lines.append(
                f"Mapping state: {corpus.get('canon_mapping_state', 'not recorded')}; "
                "not counted as a canon-linked reader."
            )
            lines.append(
                f"Observed: {reader.get('chapter_count', len(reader.get('chapters', [])))} chapters; "
                f"{reader.get('unit_count', 'unit count not recorded')} {reader.get('unit_label', 'source units')}."
            )
            for i, chapter in enumerate(reader.get("chapters", []), start=1):
                lines.append(_chapter_line(chapter, i))
            if reader.get("verification_status"):
                lines.append(f"Reader verification scope: {reader['verification_status']}")

        lines.append("")

    lines.extend([
        "=" * 88,
        "INDEX BUILD TOTALS",
        f"Catalogue rows indexed: {len(catalogue)}",
        f"Canon-linked reader appearances across catalogue rows: {total_canon_readers}",
        f"Research-only reader appearances across catalogue rows: {total_research_readers}",
        f"Reader packages in archive: {len(readers)}",
        "Repeated reader appearances can occur when a Church-list grouped entry maps to multiple display rows.",
        "Chapter/unit references are navigation labels from the stored reader packages, not a claim that every",
        "text is complete, critically established, aligned across languages, or cleared for every reuse purpose.",
        "",
    ])
    return "\n".join(lines)


def write(archive: dict) -> Path:
    OUTPUT.write_text(build_text(archive), encoding="utf-8", newline="\n")
    return OUTPUT


def main() -> None:
    archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
    path = write(archive)
    print(f"Wrote complete reference index: {path.name} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
