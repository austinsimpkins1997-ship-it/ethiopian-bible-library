"""Record the British Library Add MS 16189 title and folio lead; do not bundle manuscript text."""
from __future__ import annotations

import json
from pathlib import Path

from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-380"
CANON_ID = "eotc-ot-26"
CATALOGUE_ID = "eotc-031"
EDITION_ID = "bl-add-ms-16189-metsihafe-tibeb"
SOURCE_URL = "https://searcharchives.bl.uk/catalog/032-003450047"
VIEWER_URL = "https://iiif.bl.uk/uv/#?manifest=https://bl.digirati.io/iiif/ark:/81055/vdc_100132593940.0x000001"
PROPHET_LOCI = {
    "eotc-ot-33": ("eotc-041", "Hosea", "42v"),
    "eotc-ot-34": ("eotc-042", "Amos", "46v"),
    "eotc-ot-35": ("eotc-043", "Micah", "50r"),
    "eotc-ot-36": ("eotc-044", "Joel", "52r"),
    "eotc-ot-37": ("eotc-045", "Obadiah", "53v"),
    "eotc-ot-38": ("eotc-046", "Jonah", "54r"),
    "eotc-ot-39": ("eotc-047", "Nahum", "55r"),
    "eotc-ot-40": ("eotc-048", "Habakkuk", "56r"),
    "eotc-ot-41": ("eotc-049", "Zephaniah", "57r"),
    "eotc-ot-42": ("eotc-050", "Haggai", "58r"),
    "eotc-ot-43": ("eotc-051", "Zechariah", "59r"),
    "eotc-ot-44": ("eotc-052", "Malachi", "63r"),
}


def _sort_ids(values: set[str]) -> list[str]:
    return sorted(values, key=lambda value: int(value.rsplit("-", 1)[1]))


def _append_once(value: str, addition: str) -> str:
    value = value.strip()
    return value if addition in value else f"{value} {addition}".strip()


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive.get("sources", [])}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "British Library Archives and Manuscripts — Add MS 16189 digitized manuscript catalogue record",
        "url": SOURCE_URL,
        "full_view_url": VIEWER_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The British Library record identifies Add MS 16189 as a Ge'ez/Ethiopic parchment codex of 64 folios, "
            "dated broadly 1500–1847, with two columns and 31 or 33 lines. Its contents field names ‘Metsihafe Tibeb (the books of wisdom)’ "
            "at folios 20v–29v and links to a digitized-content viewer. The page says access restrictions apply and instructs users to consult "
            "Library staff. The same contents field lists the Twelve Prophets in folios 42v–64v and their starting folios: Hosea 42v, Amos 46v, "
            "Micah 50r, Joel 52r, Obadiah 53v, Jonah 54r, Nahum 55r, Habakkuk 56r, Zephaniah 57r, Haggai 58r, Zechariah 59r, and Malachi 63r. "
            "Its usage statement says the Library believes the Ethiopian manuscripts are not in copyright under Ethiopian law, "
            "while asking users to respect their cultural significance and not reuse images derogatorily or offensively. This is a manuscript "
            "discovery lead, not a transcription or proof of exact identity, completeness, or Church-list crosswalk. The page does not establish "
            "a reuse grant for the manuscript images or extracted text. No text or images are copied."
        ),
        "archive_status": "Digitized Ge'ez manuscript metadata and folio lead; access restrictions and image/text reuse terms unresolved; no text bundled",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].rsplit("-", 1)[1]))

    canon_path = ROOT / "canon-registry.json"
    canon = json.loads(canon_path.read_text(encoding="utf-8"))
    book = next(item for item in canon["books"] if item["canon_id"] == CANON_ID)
    book["source_ids"] = _sort_ids(set(book.get("source_ids", [])) | {SOURCE_ID})
    mapping_note = (
        "The British Library catalog for Ge'ez/Ethiopic codex Add MS 16189 names ‘Metsihafe Tibeb (the books of wisdom)’ at folios 20v–29v. "
        "This matching title and folio range identify a manuscript discovery lead, not a verified match to the complete Church-list work or its recension, and not proof that the work is identical to Wisdom of Solomon or another biblical wisdom work."
    )
    book["mapping_note"] = _append_once(book.get("mapping_note", ""), mapping_note)

    prophet_evidence = (
        "British Library Add MS 16189's catalog lists the Twelve Prophets in this Ge'ez codex at folios 42v–64v and names a starting folio for each. "
        "This is manuscript-catalog evidence only; it does not verify a transcription, complete book boundaries, or identity with a particular current Church edition."
    )
    for prophet_canon_id, (catalogue_id, name, folio) in PROPHET_LOCI.items():
        prophet = next(item for item in canon["books"] if item["canon_id"] == prophet_canon_id)
        prophet["source_ids"] = _sort_ids(set(prophet.get("source_ids", [])) | {SOURCE_ID})
        prophet["mapping_note"] = _append_once(prophet.get("mapping_note", ""), prophet_evidence)
        prophet_row = next(item for item in archive["catalogue"] if item["catalogue_id"] == catalogue_id)
        prophet_row["evidence_source_ids"] = _sort_ids(set(prophet_row.get("evidence_source_ids", [])) | {SOURCE_ID})
        prophet_row["reviewer_notes"] = _append_once(
            prophet_row.get("reviewer_notes", ""),
            f"British Library Add MS 16189 catalogs {name} beginning at folio {folio} within its Twelve Prophets section (ff.42v–64v). This is a manuscript discovery lead only; it does not verify the text, full boundaries, completeness, or current Church-edition identity.",
        )

    row = next(item for item in archive["catalogue"] if item["catalogue_id"] == CATALOGUE_ID)
    row["evidence_source_ids"] = _sort_ids(set(row.get("evidence_source_ids", [])) | {SOURCE_ID})
    row["identity_status"] = "Matching manuscript title identified; exact work identity and canon correspondence remain uncertain"
    row["text_availability_status"] = (
        "The British Library catalog describes a Ge'ez/Ethiopic manuscript witness of this title at folios 20v–29v in Add MS 16189 and links "
        "to a digitized viewer. Access restrictions apply; no transcription or images are bundled, and contents, completeness, and reuse rights remain unverified."
    )
    row["rights_status"] = (
        "The British Library says it believes the Ethiopian manuscripts are not in copyright under Ethiopian law and gives cultural-use guidance; "
        "its record also says access restrictions apply. No specific reuse grant for these manuscript images or extracted text has been established here. "
        "Rights remain unknown; no text or images are bundled."
    )
    row["verification_date"] = "2026-10-26"
    row["reviewer_notes"] = _append_once(
        row.get("reviewer_notes", ""),
        "Add MS 16189 is a matching-title manuscript lead, catalogued at folios 20v–29v. Its broad date, manuscript contents, access and reuse statements are recorded in SRC-380. Folio boundaries and catalog title do not establish the complete book's recension, text, chapter structure, identity with Wisdom of Solomon, or canon equivalence.",
    )

    archive["canon_registry"] = canon
    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    lead = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": CANON_ID,
        "mapping_state": "uncertain",
        "title": "Metsihafe Tibeb — British Library Add MS 16189 manuscript lead",
        "witness_type": "manuscript",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": "British Library Add MS 16189, a Ge'ez/Ethiopic parchment codex catalogued broadly 1500–1847; its contents list names Metsihafe Tibeb at folios 20v–29v.",
        "scope_description": (
            "Metadata-only witness lead. The British Library catalog gives the title and folio span but no transcription; the folios and their text "
            "have not been inspected here. The record describes a 64-folio codex and links to a digitized viewer, while noting access restrictions. "
            "A matching title supports an uncertain candidate link to the Church-list entry, not proof that this manuscript contains the complete "
            "canonical work, establishes its recension, or is representative of current Church use. It does not establish that the work is identical "
            "to Wisdom of Solomon or another biblical wisdom work. No text or images are bundled."
        ),
        "source_ids": ["SRC-029", SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "The British Library says it believes these manuscripts are not in copyright under Ethiopian law and asks users to respect their cultural "
            "significance; its record says access restrictions apply. No specific reuse grant for the images or extracted text has been established. "
            "No text or images are copied or bundled."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "The Church's English list and British Library catalog metadata were inspected. Title, language/script, broad date range, physical format, "
            "folio span, viewer link, and stated access/use terms are recorded. The manuscript leaves, text, recension, completeness, chapter boundaries, "
            "identity with Wisdom of Solomon or another specific work, and exact canon identity remain unreviewed."
        ),
    }
    leads = registry.setdefault("edition_leads", [])
    leads[:] = [item for item in leads if item.get("edition_id") != EDITION_ID]
    leads.append(lead)
    archive["translation_registry"] = registry

    review = f"""# Metsihafe Tibeb: Add MS 16189 manuscript lead

## What the sources establish

- The Ethiopian Orthodox Tewahedo Church's English list names “Metsihafe Tibeb (the books of wisdom)” as Old Testament entry 26. The list supports preserving that title and position; it does not specify a manuscript, textual boundary, or recension. [Church list](https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en)
- The British Library catalog record for Add MS 16189 identifies a Ge'ez/Ethiopic parchment codex, 64 folios, broadly dated 1500–1847. Its contents field names “Metsihafe Tibeb (the books of wisdom)” at folios 20v–29v. It links to a digitized-content viewer. The catalog also says access restrictions apply. [British Library record](https://searcharchives.bl.uk/catalog/032-003450047) · [digitized-content viewer]({VIEWER_URL})
- The same catalog lists the Twelve Prophets on folios 42v–64v and records starting folios: Hosea 42v, Amos 46v, Micah 50r, Joel 52r, Obadiah 53v, Jonah 54r, Nahum 55r, Habakkuk 56r, Zephaniah 57r, Haggai 58r, Zechariah 59r, Malachi 63r. These are catalogued start locations, not verified complete book boundaries or chapter counts. [British Library record](https://searcharchives.bl.uk/catalog/032-003450047)
- The Library's usage statement says it believes the Ethiopian manuscripts are not in copyright under Ethiopian law, but emphasizes their cultural significance and asks users not to reuse images in derogatory or offensive ways. This does not establish the rights status of all underlying texts, a specific reuse grant for these images, or rights in every jurisdiction.

## Archive treatment

Add MS 16189 is a matching-title, folio-level discovery lead. The manuscript leaves have not been reviewed or transcribed. The archive does not claim the folios contain a complete, representative, or textually verified edition of the Church-list book. The record does not establish that Metsihafe Tibeb is identical to Wisdom of Solomon or any other specific work. The lead is marked uncertain, rights remain unknown, and no text or images are bundled. The lead does not increase reader coverage.

The same codex is an additional manuscript-location lead for the Twelve Prophets. Starting folios are recorded on the corresponding catalogue entries; no book endpoints, chapter counts, or textual completeness are inferred.
"""
    write_text_atomically(ROOT / "research" / "metsihafe-tibeb-source-review.md", review)
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(registry_path, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(canon_path, json.dumps(canon, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    build()
