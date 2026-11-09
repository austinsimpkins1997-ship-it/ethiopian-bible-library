"""Build an evidence-scoped, per-entry reader availability register."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "book-coverage.json"
SCHEMA_URI = "schemas/book-coverage.schema.json"


def _mapping_state(value: object) -> str:
    """Represent an absent crosswalk explicitly in the derived coverage view."""
    return value if isinstance(value, str) and value.strip() else "unrecorded"


def _reader_summary(reader: dict, reader_data_url: str) -> dict:
    fields = (
        "reader_id", "title", "display_name", "language", "language_tag", "script_code",
        "text_origin", "edition", "edition_scope", "chapter_count", "unit_count", "unit_label",
        "rights_classification", "rights_status", "license_id", "license_url",
        "copyright_notice", "commercial_use", "verification_status", "source_ids",
    )
    return {**{field: reader[field] for field in fields if field in reader}, "reader_data_url": reader_data_url}


def _lead_summary(kind: str, lead: dict) -> dict:
    identifier_field = {
        "translation": "translation_id",
        "edition": "edition_id",
        "corpus": "corpus_id",
    }[kind]
    return {
        "lead_type": kind,
        "lead_id": lead.get(identifier_field),
        "title": lead.get("title") or lead.get("edition_statement") or lead.get("translation_name"),
        "mapping_state": _mapping_state(lead.get("mapping_state")),
        "scope_description": lead.get("scope_description") or lead.get("unit_summary"),
        "text_bundled": lead.get("text_bundled", lead.get("reader_status") == "bundled_research_reader"),
        "rights_classification": lead.get("rights_classification"),
        "rights_status": lead.get("rights_status"),
        "license_id": lead.get("license_id"),
        "license_url": lead.get("license_url"),
        "source_ids": sorted(set(lead.get("source_ids", []))),
    }


def build_book_coverage(archive: dict, reader_data_urls: dict[str, str]) -> dict:
    """Derive per-entry bundled-reader and lead status from the built archive."""
    canon_books = archive.get("canon_registry", {}).get("books", [])
    if not canon_books:
        raise ValueError("The coverage register requires the registered canon entries.")

    books_by_id = {book.get("canon_id"): book for book in canon_books}
    if None in books_by_id or len(books_by_id) != len(canon_books):
        raise ValueError("Canon entries must have unique canon IDs.")
    readers_by_canon: dict[str, list[dict]] = {canon_id: [] for canon_id in books_by_id}
    for reader in archive.get("readers", []):
        canon_id = reader.get("canon_id")
        if canon_id is not None:
            if canon_id not in readers_by_canon:
                raise ValueError(f"Reader {reader.get('reader_id')} points to unknown canon ID {canon_id}.")
            reader_id = reader.get("reader_id")
            if reader_id not in reader_data_urls:
                raise ValueError(f"Reader {reader_id} has no local package path in the coverage register.")
            readers_by_canon[canon_id].append(_reader_summary(reader, reader_data_urls[reader_id]))

    research_by_canon: dict[str, list[dict]] = {canon_id: [] for canon_id in books_by_id}
    registry = archive.get("translation_registry", {})
    for corpus in registry.get("research_corpora", []):
        canon_id = corpus.get("candidate_canon_id")
        if corpus.get("reader_status") == "bundled_research_reader" and canon_id is not None:
            if canon_id not in research_by_canon:
                raise ValueError(f"Research corpus {corpus.get('corpus_id')} points to unknown candidate canon ID {canon_id}.")
            reader_id = corpus.get("reader_id")
            if reader_id not in reader_data_urls:
                raise ValueError(f"Research reader {reader_id} has no local package path in the coverage register.")
            research_by_canon[canon_id].append({
                "corpus_id": corpus.get("corpus_id"),
                "reader_id": reader_id,
                "reader_data_url": reader_data_urls[reader_id],
                "title": corpus.get("title"),
                "mapping_state": _mapping_state(corpus.get("canon_mapping_state")),
                "mapping_note": corpus.get("canon_mapping_note"),
                "language_tag": corpus.get("language_tag"),
                "script_code": corpus.get("script_code"),
                "unit_count": corpus.get("unit_count"),
                "rights_classification": corpus.get("rights_classification"),
                "rights_status": corpus.get("rights_status"),
                "license_id": corpus.get("license_id"),
                "license_url": corpus.get("license_url"),
                "review_status": corpus.get("review_status"),
                "source_ids": sorted(set(corpus.get("source_ids", []))),
            })

    leads_by_canon: dict[str, list[dict]] = {canon_id: [] for canon_id in books_by_id}
    for kind, key in (("translation", "translation_leads"), ("edition", "edition_leads"), ("corpus", "corpus_leads")):
        for lead in registry.get(key, []):
            canon_id = lead.get("candidate_canon_id") or lead.get("canon_id")
            if canon_id in leads_by_canon:
                leads_by_canon[canon_id].append(_lead_summary(kind, lead))

    catalogue_by_id = {
        item.get("catalogue_id"): item
        for item in archive.get("catalogue", [])
        if item.get("catalogue_id")
    }
    sources_by_id = {
        item.get("source_id"): item
        for item in archive.get("sources", [])
        if item.get("source_id")
    }

    entries = []
    availability_counts: Counter[str] = Counter()
    for book in canon_books:
        canon_id = book["canon_id"]
        canon_readers = sorted(readers_by_canon[canon_id], key=lambda item: item.get("reader_id", ""))
        research_readers = sorted(research_by_canon[canon_id], key=lambda item: item.get("corpus_id", ""))
        leads = sorted(leads_by_canon[canon_id], key=lambda item: (item["lead_type"], item.get("lead_id") or ""))
        catalogue_source_ids = sorted({
            source_id
            for catalogue_id in book.get("catalogue_ids", [])
            for source_id in (
                [catalogue_by_id[catalogue_id].get("source_id")]
                + catalogue_by_id[catalogue_id].get("evidence_source_ids", [])
                if catalogue_id in catalogue_by_id else []
            )
            if source_id
        })
        canon_entry_source_ids = sorted(set(book.get("source_ids", [])))
        reader_source_ids = sorted({
            source_id
            for record in [*canon_readers, *research_readers]
            for source_id in record.get("source_ids", [])
        })
        lead_source_ids = sorted({
            source_id for lead in leads for source_id in lead.get("source_ids", [])
        })
        if canon_readers:
            state = "canon_linked_reader"
        elif research_readers:
            research_states = {reader.get("mapping_state") for reader in research_readers}
            if "reviewed_match" in research_states:
                state = "reviewed_title_match_research_reader_only"
            elif "asserted_by_source" in research_states:
                state = "source_asserted_research_reader_only"
            else:
                state = "research_candidate_reader_only"
        else:
            state = "no_bundled_reader"
        availability_counts[state] += 1
        source_ids = sorted(set(catalogue_source_ids + canon_entry_source_ids + reader_source_ids + lead_source_ids))
        supplemental_research_views = []
        for source_id in source_ids:
            source = sources_by_id.get(source_id)
            view_url = source.get("local_research_view_url") if source else None
            if not view_url:
                continue
            path = Path(view_url)
            if path.is_absolute() or ".." in path.parts or not (ROOT / path).is_file():
                raise ValueError(f"Source {source_id} has a missing or unsafe local research view: {view_url}.")
            supplemental_research_views.append({
                "source_id": source_id,
                "source_name": source.get("source_name"),
                "research_view_url": path.as_posix(),
                "archive_status": source.get("archive_status"),
                "rights_classification": source.get("rights_classification"),
                "rights_status": source.get("rights_status"),
                "inspection_and_limitations": source.get("inspection_and_limitations"),
            })
        entries.append({
            "canon_id": canon_id,
            "section": book.get("section"),
            "section_number": book.get("section_number"),
            "display_name": book.get("display_name"),
            "source_label": book.get("source_label"),
            "catalogue_ids": book.get("catalogue_ids", []),
            "catalogue_source_ids": catalogue_source_ids,
            "canon_entry_source_ids": canon_entry_source_ids,
            "mapping_state": _mapping_state(book.get("mapping_state")),
            "mapping_note": book.get("mapping_note"),
            "reader_availability": state,
            "canon_linked_readers": canon_readers,
            "research_reader_candidates": research_readers,
            "unbundled_leads": leads,
            "supplemental_research_views": supplemental_research_views,
            "reader_source_ids": reader_source_ids,
            "lead_source_ids": lead_source_ids,
            "related_source_ids": source_ids,
        })

    if sum(availability_counts.values()) != len(canon_books):
        raise ValueError("Coverage states do not account for every canon entry exactly once.")
    return {
        "schema_version": 1,
        "scope": "Snapshot of bundled local reader records and registered leads for the 81 entries in the included Ethiopian Orthodox Church list. It does not establish that unbundled editions do not exist elsewhere, that a mapped reader is a current Church edition, or that any text is complete or accurate.",
        "source_registry": "canon-registry.json",
        "entry_count": len(entries),
        "availability_counts": {
            state: availability_counts[state]
            for state in (
                "canon_linked_reader",
                "reviewed_title_match_research_reader_only",
                "source_asserted_research_reader_only",
                "research_candidate_reader_only",
                "no_bundled_reader",
            )
        },
        "source_id_reference": "archive.json#/sources",
        "schema_uri": SCHEMA_URI,
        "entries": entries,
    }


def write_book_coverage(archive: dict, reader_data_urls: dict[str, str]) -> dict:
    coverage = build_book_coverage(archive, reader_data_urls)
    canon_registry = archive.get("canon_registry", {})
    expected_books = canon_registry.get("book_count")
    if expected_books is not None and expected_books != coverage["entry_count"]:
        raise ValueError(
            "Canon registry book_count disagrees with the generated coverage entry_count: "
            f"{expected_books} != {coverage['entry_count']}."
        )
    linked_ids = {
        entry["canon_id"]
        for entry in coverage["entries"]
        if entry["canon_linked_readers"]
    }
    expected_linked = canon_registry.get("reader_count")
    if expected_linked is not None and expected_linked != len(linked_ids):
        raise ValueError(
            "Canon registry reader_count disagrees with distinct canon-linked entries in "
            f"book-coverage.json: {expected_linked} != {len(linked_ids)}."
        )
    OUTPUT.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return coverage
