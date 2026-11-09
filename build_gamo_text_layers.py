"""Build portable layer metadata for the locally archived Gamo research readers.

This records publisher-supplied Gamo text as published translations with an
explicitly unknown source/relay path. It makes no Ethiopian Orthodox canon
assertions and does not attempt to translate or normalize Gamo wording.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from archive_manifest import write_text_atomically


ROOT = Path(__file__).resolve().parent
READERS = ROOT / "readers"
EXAMPLES = ROOT / "examples"
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
SOURCE_IDS = ["SRC-168", "SRC-169", "SRC-178"]
REVIEWED_AT = "2026-10-26"


def build() -> int:
    reader_paths = sorted(READERS.glob("gamo-*-research.json"))
    if len(reader_paths) != 66:
        raise ValueError(f"Expected 66 Gamo research readers; found {len(reader_paths)}.")
    seen_codes: set[str] = set()

    for reader_path in reader_paths:
        reader = json.loads(reader_path.read_text(encoding="utf-8"))
        code = reader.get("publisher_book_code")
        if not isinstance(code, str) or not code.isascii() or not code.isalnum() or code in seen_codes:
            raise ValueError(f"{reader_path.name} has a missing, invalid, or duplicate publisher code.")
        seen_codes.add(code)
        if (reader.get("language_tag") != "gmv" or reader.get("script_code") != "Ethi"
                or reader.get("text_origin") != "published_translation"
                or reader.get("translation_basis_status") != "unknown"):
            raise ValueError(f"{reader_path.name} language, script, origin, or unknown basis changed.")
        if reader.get("rights_classification") != "open_license" or reader.get("license_id") != "CC-BY-SA-4.0":
            raise ValueError(f"{reader_path.name} does not carry the expected source-specific open license.")
        if set(reader.get("source_ids", [])) != set(SOURCE_IDS):
            raise ValueError(f"{reader_path.name} source citations changed; review the layer source mapping.")

        relative_uri = f"../readers/{reader_path.name}"
        package_hash = hashlib.sha256(reader_path.read_bytes()).hexdigest()
        label = reader["source_title_label"]
        title = f"eBible.org Gamo Bible (GMVETW / gmve), publisher entry {code}: {label}"
        source_note = (
            f"This layer is the publisher-linked Gamo/Gamotso (gmv) text under menu code {code}. "
            "The source or relay-language path is not identified in the cited edition record and is not inferred."
        )
        record = {
            "schema_version": 2,
            "record_id": f"{BASE}/layer/gamo-gmvetw-translation-{code.lower()}",
            "work_id": f"{BASE}/work/gamo-gmvetw-menu-entry-{code.lower()}",
            "labels": [{"value": label, "language_tag": "gmv", "label_type": "original_form"}],
            "tradition_assertions": [],
            "witness": {
                "witness_id": f"{BASE}/witness/gamo-gmvetw-{code.lower()}",
                "witness_type": "digital_edition",
                "title": title,
                "date_statement": "Source files dated 2025-05-03; mobile HTML package generated 2026-10-20, as recorded by the provider.",
                "repository_or_publisher": "The Word for the World International; digital edition distributed by eBible.org",
                "shelfmark_or_edition_id": f"GMVETW / gmve; publisher book code {code}",
                "editorial_policy": reader["transcription_note"],
                "source_ids": SOURCE_IDS,
            },
            "layer_type": "translation",
            "text_origin": "published_translation",
            "language_tag": "gmv",
            "language_name_as_recorded": "Gamo (Gamotso)",
            "script_code": "Ethi",
            "basis_path": None,
            "basis_path_status": "unknown",
            "agents": [{
                "role": "publisher",
                "name": "The Word for the World International",
                "authority_or_affiliation": None,
                "source_ids": ["SRC-168"],
            }],
            "content_package": {
                "uri": relative_uri,
                "media_type": "application/json",
                "sha256": package_hash,
                "format_version": "1",
            },
            "coverage": {
                "extent_state": "unknown",
                "extent_basis": "source_inventory",
                "unit_count": reader["unit_count"],
                "structure_description": (
                    f"The local extraction contains {reader['chapter_count']} consecutive chapter pages linked from the captured "
                    f"publisher package and {reader['unit_count']} nonempty source spans. These are counts of the captured digital "
                    "scope only; completeness against a print edition, manuscript, or other canonical list is not established."
                ),
                "missing_or_lacunose_ranges": [],
                "supplements_and_editorial_signs": reader["editorial_signs_note"],
                "numbering_policy": "Publisher chapter and verse labels are retained as strings, including combined labels; no renumbering or cross-witness equivalence is implied.",
            },
            "rights": {
                "status": "open_license",
                "statement": (
                    "Copyright © 2024 The Word for the World International; contributor: The Word for the World Northern Africa. "
                    "Source: eBible.org, Gamo Bible GMVETW / gmve, Ethiopic script. The provider identifies CC BY-SA 4.0 "
                    "(https://creativecommons.org/licenses/by-sa/4.0/), requiring attribution, an indication of changes, and "
                    "share-alike distribution of adaptations. This archive converted publisher HTML structure to JSON and normalized "
                    "HTML whitespace for display; source labels are retained, and these changes do not imply publisher endorsement. "
                    "The provider states that images have separate terms; this text-only layer excludes images, fonts, and CSS. "
                    "The license does not apply to other archive content."
                ),
                "license_id": "CC-BY-SA-4.0",
                "rights_holder": "The Word for the World International",
                "attribution_required": True,
                "territory_or_term_limits": "No separate territory restriction was recorded in the cited license notice; this archive makes no independent worldwide legal determination.",
                "evidence_source_ids": ["SRC-168", "SRC-178"],
            },
            "review_dimensions": [
                {
                    "dimension": "identity",
                    "state": "checked_with_limits",
                    "scope": f"Provider edition identifier GMVETW / gmve and publisher menu code {code}; exact identity to a print witness is not established.",
                    "reviewer": None,
                    "review_method": "source_inspection",
                    "review_process": "Review of the retained publisher metadata and locally captured HTML package.",
                    "reviewed_at": REVIEWED_AT,
                    "evidence_source_ids": ["SRC-168", "SRC-178"],
                    "notes": "Publisher-code crosswalk candidates are kept in the research corpus and do not assert canon affiliation.",
                },
                {
                    "dimension": "language_identification",
                    "state": "checked_with_limits",
                    "scope": "The edition record identifies Gamo/Gamotso (gmv) and Ethiopic script (Ethi).",
                    "reviewer": None,
                    "review_method": "source_inspection",
                    "review_process": "Review of the provider edition metadata and reader language fields.",
                    "reviewed_at": REVIEWED_AT,
                    "evidence_source_ids": ["SRC-168", "SRC-178"],
                    "notes": "This identifies the publisher-declared language and script; it is not an independent linguistic review.",
                },
                {
                    "dimension": "chapter_or_section_sequence",
                    "state": "checked_with_limits",
                    "scope": reader["verification_status"],
                    "reviewer": None,
                    "review_method": "automated_validation",
                    "review_process": "build_gamo_research_readers.py validates the captured publisher index and linked chapter pages.",
                    "reviewed_at": REVIEWED_AT,
                    "evidence_source_ids": ["SRC-178"],
                    "notes": "Confirms extraction from the retained HTML package, not completeness against print or manuscript witnesses.",
                },
                {
                    "dimension": "unit_boundaries",
                    "state": "checked_with_limits",
                    "scope": f"{reader['unit_count']} nonempty spans and their displayed source labels in the captured {reader['chapter_count']}-chapter sequence.",
                    "reviewer": None,
                    "review_method": "automated_validation",
                    "review_process": "Gamo HTML extraction and local package validation.",
                    "reviewed_at": REVIEWED_AT,
                    "evidence_source_ids": ["SRC-178"],
                    "notes": "Structural extraction only; no verse alignment or wording accuracy is claimed.",
                },
                {
                    "dimension": "translation_accuracy",
                    "state": "unknown",
                    "scope": "No independent translation review or collation was performed; the source and any relay-language path are not identified by the cited edition record.",
                    "reviewer": None,
                    "review_method": "unknown",
                    "review_process": None,
                    "reviewed_at": None,
                    "evidence_source_ids": ["SRC-168", "SRC-178"],
                    "notes": source_note,
                },
                {
                    "dimension": "completeness",
                    "state": "unknown",
                    "scope": "Completeness beyond the locally captured linked digital pages has not been established.",
                    "reviewer": None,
                    "review_method": "unknown",
                    "review_process": None,
                    "reviewed_at": None,
                    "evidence_source_ids": ["SRC-168", "SRC-178"],
                    "notes": "Observed chapter and span counts do not establish completeness against a print edition, manuscript, or church canon.",
                },
                {
                    "dimension": "rights",
                    "state": "checked_with_limits",
                    "scope": "Provider's CC BY-SA 4.0 notice for text; excluded image assets have separate terms.",
                    "reviewer": None,
                    "review_method": "source_inspection",
                    "review_process": "Review of the provider edition page, reuse notice, and retained text-only source package.",
                    "reviewed_at": REVIEWED_AT,
                    "evidence_source_ids": ["SRC-168", "SRC-178"],
                    "notes": "Source-derived text is shared under the stated license; no license is asserted for the site or excluded media.",
                },
            ],
            "publication_state": "bundled",
            "community_access_note": None,
            "additional_notes": (
                "This is a source-derived Gamo research translation layer. It has no canon or tradition assertion. The separate Gamo "
                "research corpus records provisional title-code candidates; those candidates do not establish Ethiopian Orthodox affiliation "
                "or canon coverage. The unknown translation basis remains explicit."
            ),
        }
        output = EXAMPLES / f"gamo-{code.lower()}-translation-layer.json"
        write_text_atomically(output, json.dumps(record, ensure_ascii=False, indent=2) + "\n", newline="\n")

    if len(seen_codes) != 66:
        raise ValueError("Gamo portable-layer generation did not cover all unique publisher codes.")
    print(f"Built {len(seen_codes)} portable Gamo translation-layer records with explicit unknown basis paths.")
    return len(seen_codes)


if __name__ == "__main__":
    build()
