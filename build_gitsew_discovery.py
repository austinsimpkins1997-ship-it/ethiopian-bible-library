"""Record a reported Gitsew text acquisition without copying scripture."""

from __future__ import annotations

import json
from archive_manifest import write_text_atomically
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-284"
EDITION_ID = "eob-project-gitsew-acquisition-report-2017"
SOURCE_URL = "https://ethiopianorthodoxbible.wordpress.com/2017/08/12/progress-we-have-acquired-the-book-of-gitsew/"
CANON_URL = "https://ethiopianorthodoxbible.wordpress.com/ethiopian-orthodox-canon-of-scripture/"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Ethiopian Orthodox Bible Project — Gitsew text acquisition report",
        "url": SOURCE_URL,
        "local_review_url": "research/gitsew-source-review.md",
        "inspection_and_limitations": (
            "The project's 2017 post reports that its team acquired a complete Gitsew text in Geʽez and "
            "Amharic and purchased a book in Ethiopia; it describes the work as one of four Sinodos books. "
            "The page says its displayed images are photographs of the book. The archive did not inspect "
            "those images, the physical book, its title page, edition/imprint, text boundaries, or any text. "
            "The report is a secondary project statement, not direct evidence of the underlying edition's "
            "identity, completeness, or accuracy. The website displays Copyright © 2017–2025 Ethiopian "
            "Orthodox Bible Project Committee, All Rights Reserved; it does not state the book-text reuse "
            "terms. No wording or images are copied. Inspected 2026-10-25."
        ),
        "archive_status": (
            "Metadata-only report of an acquired Geʽez/Amharic Gitsew book; physical witness, edition, "
            "contents, completeness, and text reuse terms not examined"
        ),
    }
    archive["sources"] = sorted(
        sources.values(), key=lambda item: int(item["source_id"].split("-")[1])
    )
    catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-084")
    catalogue["edition_or_translation"] = (
        "Ethiopian Orthodox Bible Project reports acquisition of a Geʽez/Amharic Gitsew book (2017); "
        "physical edition not identified and no reader bundled"
    )
    catalogue["text_availability_status"] = (
        "A project reports holding the complete text in a purchased book; no text is publicly bundled here, "
        "and the underlying edition/content were not inspected"
    )
    catalogue["completeness_status"] = (
        "The project describes its acquired text as complete; this archive has not inspected the book, "
        "boundaries, or text and does not independently verify completeness"
    )
    catalogue["rights_status"] = (
        "Underlying book-text reuse rights unknown; the discovery webpage itself states All Rights Reserved. "
        "No wording or images copied"
    )
    catalogue["verification_date"] = "2026-10-25"
    catalogue["source_id"] = SOURCE_ID
    catalogue["evidence_source_ids"] = ["SRC-029", "SRC-073", "SRC-211", SOURCE_ID]
    catalogue["reviewer_notes"] = (
        "The Ethiopian Orthodox Bible Project reports that it acquired a complete Geʽez/Amharic Gitsew text "
        "in a book purchased in Ethiopia and identifies Gitsew as one of four Sinodos books. This is a "
        "discovery lead, not an inspected witness: no text, book title page, edition data, boundaries, or "
        "reuse license was reviewed. The project webpage is marked All Rights Reserved. Do not infer that "
        "the original printed text is freely reusable or complete from the project report alone."
    )
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[EDITION_ID] = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": "eotc-nt-30",
        "mapping_state": "uncertain",
        "title": "Gitsew — reported Geʽez/Amharic book acquisition (Ethiopian Orthodox Bible Project, 2017)",
        "witness_type": "unknown",
        "language_tag": "mul",
        "language_name": "Multiple languages",
        "language_tags": ["gez", "am"],
        "script_code": "Ethi",
        "edition_statement": (
            "An Ethiopian Orthodox Bible Project post dated 2017-08-12 reports acquisition of a book containing "
            "Gitsew in Geʽez and Amharic. The underlying title page, edition, imprint, and publication date were not inspected."
        ),
        "scope_description": (
            "The project reports acquiring the complete text and describes Gitsew as one of four books of Sinodos; "
            "the EOTC English canon list separately names Gitsew at entry 30. This supports an uncertain title-level "
            "candidate only. The post is not the book itself and does not prove edition identity, textual boundaries, "
            "completeness, accuracy, or a specific Geʽez/Amharic alignment. No text or image is bundled."
        ),
        "source_ids": ["SRC-029", "SRC-073", "SRC-211", SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "Unknown for the underlying book text. The discovery webpage states Copyright © 2017–2025 Ethiopian "
            "Orthodox Bible Project Committee, All Rights Reserved. No permission to reproduce the book text or "
            "project photographs is established; none is copied."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "Project acquisition report and cited canon/context records inspected. The physical book, photographs, "
            "title page, text, edition, boundaries, completeness, and reuse permission were not examined. The "
            "underlying text is not bundled and is not counted as a reader."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = (
        "# Gitsew source review\n\n"
        f"The [Ethiopian Orthodox Bible Project's 2017 report]({SOURCE_URL}) says its team acquired a complete "
        "Gitsew text in Geʽez and Amharic, purchased as a book in Ethiopia, and describes it as one of the four "
        "Sinodos books. The project's [canon page]({CANON_URL}) lists Gitsew as broader New Testament entry 30. "
        "The page also carries the project's copyright notice: Copyright © 2017–2025, All Rights Reserved.\n\n"
        "This is a discovery lead, not a reader. The physical book, title page, edition/imprint, photographs, "
        "text, boundaries, completeness, accuracy, and book-text reuse terms were not inspected. The website's "
        "copyright notice applies to that page; it does not by itself determine rights in the underlying book. "
        "No wording or images were copied, and the lead does not increase reader coverage.\n\n"
        "Lexham Bible Dictionary lists Gessew among the four Sinodos works and summarizes reported manuscript "
        "variation; this supports contextual naming, not identification of the acquired physical book. See the "
        "existing source record SRC-211. The candidate link to the Church-list Gitsew entry remains uncertain.\n"
    )
    (ROOT / "research" / "gitsew-source-review.md").write_text(report, encoding="utf-8")
    print("Recorded Gitsew as an unbundled, unverified acquisition-report lead.")


if __name__ == "__main__":
    build()
