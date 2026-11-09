"""Preserve a source-attributed Maale translation-strategy example."""

from __future__ import annotations

from rights_metadata import same_source_identity


SOURCE = {
    "source_id": "SRC-398",
    "source_name": "The Word for the World — Maale Revelation 3:20 translation example",
    "url": "https://www.twftw.org/post/i-stand-at-the-gate-and-call-out",
    "inspection_and_limitations": (
        "The agency article, published 2022-12-12, reports a Maale rendering of Revelation 3:20 "
        "that replaces the unfamiliar door-and-knocking scene with a garden gate and calling out. "
        "It explains this choice by describing how visitors greet people from a garden gate in Maale "
        "culture. This is an agency-reported translation example, not an independently checked "
        "linguistic analysis. The article does not identify the source-language wording, relay path, "
        "named translators, or a specific edition. It therefore cannot establish that the example "
        "appears in the bundled 2008 MDYTWF / mdyeth files."
    ),
    "archive_status": (
        "Official agency article inspected 2026-10-26; stored as attributed, language-level "
        "translation-process evidence. No scripture text or edition crosswalk is added."
    ),
}


PROCESS_EVIDENCE = {
    "record_id": "twftw-maale-rev-3-20-strategy-2022",
    "language_tag": "mdy",
    "record_type": "project_history",
    "claim_summary": (
        "The Word for the World reports that a Maale translation of Revelation 3:20 uses a "
        "garden-gate greeting in place of the door-and-knocking scene, which the article says "
        "fits local visiting practice. This is a reported contextual strategy example, not a "
        "verified text of the bundled 2008 edition."
    ),
    "participants": [
        {
            "agent_type": "organization",
            "name": "The Word for the World",
            "claimed_role": "publisher and reporter of the translation example",
        },
        {
            "agent_type": "community_team",
            "name": "Maale translators (individuals not named in the article)",
            "claimed_role": "translators credited collectively by the article for the example",
        },
    ],
    "edition_link_status": "not_established",
    "edition_ids": [],
    "translation_path_status": "not_stated",
    "milestones": [
        {
            "event": "Agency article published with the Maale Revelation 3:20 example",
            "date": "2022-12-12",
            "date_precision": "day",
            "source_claim": "The article is dated December 12, 2022 and reports the example; it does not date the translation or link it to a specific edition.",
        }
    ],
    "source_ids": ["SRC-398"],
    "limitations": (
        "The report does not name the translators, establish a source or relay language, "
        "identify an edition or text file, or provide independent community review. It cannot "
        "be used to claim the same wording occurs in MDYTWF / mdyeth (2008), nor does this "
        "archive certify semantic equivalence."
    ),
}


def apply(archive: dict) -> None:
    """Idempotently add the source and attributed process record to the archive."""
    sources = archive.setdefault("sources", [])
    existing_source = next(
        (item for item in sources if item.get("source_id") == SOURCE["source_id"]), None
    )
    if existing_source is not None and not same_source_identity(existing_source, SOURCE):
        raise ValueError(f"Conflicting source record {SOURCE['source_id']}.")
    if existing_source is None:
        sources.append(dict(SOURCE))
        sources.sort(key=lambda item: item["source_id"])

    registry = archive.setdefault("translation_registry", {})
    evidence = registry.setdefault("translation_process_evidence", [])
    existing_record = next(
        (item for item in evidence if item.get("record_id") == PROCESS_EVIDENCE["record_id"]),
        None,
    )
    if existing_record is not None and existing_record != PROCESS_EVIDENCE:
        raise ValueError(f"Conflicting process-evidence record {PROCESS_EVIDENCE['record_id']}.")
    if existing_record is None:
        evidence.append(dict(PROCESS_EVIDENCE))
        evidence.sort(key=lambda item: item["record_id"])
