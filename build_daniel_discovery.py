"""Record the pinned Daniel TEI lead without bundling text or asserting coverage."""

from __future__ import annotations

import json
from archive_manifest import write_text_atomically
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-282"
EDITION_ID = "betamasaheft-daniel-tei-2026"
COMMIT = "ddee2d46c14eff7d738099a8503af1f0e084763e"
FILE_SHA256 = "bb8688848c941c67a1b104f76a13542e3ac30c1bb81d9b899c8601d6f206953b"
FILE_BYTES = 169_133
SOURCE_URL = f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/3001-4000/LIT3529Daniel.xml"
WORK_URL = "https://betamasaheft.awhamburg.de/works/LIT3529Daniel/text"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Beta maṣāḥǝft Works — Daniel (LIT3529Daniel) source review",
        "url": WORK_URL,
        "inspection_and_limitations": (
            f"Inspected the pinned BetaMasaheft/Works file at commit {COMMIT} "
            f"({FILE_BYTES:,} bytes; SHA-256 {FILE_SHA256}); the XML is not included in this archive. "
            "Its TEI root defaults to English, while the sole edition division explicitly declares "
            "Geʽez and labels the text ‘Text of the EOTC printed Bible.’ The file-level notice grants "
            "CC BY-SA 4.0; it does not identify the modern printed exemplar or establish that the "
            "file-level grant covers that exemplar. The pinned TEI contains 14 ordered chapter "
            "divisions and 437 labeled line elements with reference elements. Chapter 14's line "
            "labels are 0–2 rather than starting at 1. Counts describe TEI structure only; they do "
            "not verify completeness, accuracy, or correspondence with the Church-list Daniel entry. "
            "The TEI abstract lists Susanna, Bel and the Dragon, the Prayer of Azariah and the Three "
            "Holy Children, the Prayer of the Three Children, and the Third Song of the Three Youths "
            "in the Furnace as associated components of the Daniel work; their boundaries in this "
            "edition are not independently assessed. "
            "The work page was not independently accessible during this review. The selected reader extraction and its review limits are recorded separately."
        ),
        "archive_status": "Metadata-only edition lead; no text bundled and no coverage claim",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))

    catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-040")
    catalogue.update({
        "edition_or_translation": "Online lead: Beta maṣāḥǝft LIT3529Daniel, pinned source review; no reader bundled",
        "chapter_count": "14 TEI divisions observed; completeness and Church-list crosswalk unverified",
        "chapter_order_status": "TEI divisions labeled 1–14; chapter 14 line labels start at 0 and run through 2",
        "text_availability_status": "Geʽez source identified online; text not bundled pending print-source rights and edition review",
        "completeness_status": "Not assessed against a specified printed exemplar or complete textual witness",
        "rights_status": "TEI file states CC BY-SA 4.0; underlying printed exemplar and scope of grant unresolved",
        "verification_date": "2026-10-25",
        "source_id": SOURCE_ID,
        "evidence_source_ids": ["SRC-029", "SRC-034", "SRC-150", SOURCE_ID],
        "reviewer_notes": (
            "Pinned Beta maṣāḥǝft TEI identifies a Geʽez edition as ‘Text of the EOTC printed Bible.’ "
            "Its file-level CC BY-SA notice does not identify the printed exemplar or settle rights in it. "
            "Fourteen TEI chapter divisions are present; chapter 14 uses line labels 0–2. No text is bundled, "
            "and correspondence, completeness, and accuracy remain unverified. The abstract also "
            "lists several Daniel-associated stories and prayers; their boundaries against this canon "
            "row are not established."
        ),
    })

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[EDITION_ID] = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": "eotc-ot-32",
        "mapping_state": "uncertain",
        "title": "Daniel (LIT3529Daniel), Beta maṣāḥǝft TEI source lead",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            f"Pinned Beta maṣāḥǝft Works file at commit {COMMIT}; {FILE_BYTES:,} bytes, "
            f"SHA-256 {FILE_SHA256}. The edition division declares Geʽez and is labeled "
            "‘Text of the EOTC printed Bible.’"
        ),
        "scope_description": (
            "Metadata-only lead. The TEI has 14 ordered chapter divisions and 437 labeled lines; "
            "chapter 14 line labels run 0–2. Its abstract lists Susanna, Bel and the Dragon, and "
            "three associated prayer/song components. Their boundaries against the grouped Church-list "
            "Daniel entry are not established; counts do not establish completeness or accuracy."
        ),
        "source_ids": ["SRC-029", "SRC-034", "SRC-150", SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "The file states CC BY-SA 4.0, but the printed exemplar is unidentified and the file-level "
            "notice does not establish that the exemplar's rights are cleared. Do not redistribute text pending review."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "Pinned source identity, file-level license notice, edition language and label, and TEI "
            "chapter/line structure inspected. No text copied. Printed-source rights, source-to-canon "
            "crosswalk, completeness, and transcription accuracy remain unverified."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (ROOT / "research" / "daniel-source-review.md").write_text(
        "# Daniel source review\n\n"
        f"Inspected the pinned [Beta maṣāḥǝft Works TEI file]({SOURCE_URL}) at commit `{COMMIT}`. "
        f"The file is {FILE_BYTES:,} bytes (SHA-256 `{FILE_SHA256}`); its XML is not retained here. "
        f"The [work page]({WORK_URL}) was not independently accessible during this review. The TEI root "
        "defaults to English, while its only edition declares Geʽez (`gez`) and labels itself ‘Text of the "
        "EOTC printed Bible.’ The file contains a CC BY-SA 4.0 notice. The underlying printed exemplar is "
        "not identified, so that notice is not treated as proof that the printed text is cleared for reuse.\n\n"
        "The pinned TEI has 14 ordered chapter divisions and 437 labeled line elements with reference "
        "elements. Its abstract lists Susanna, Bel and the Dragon, and three associated prayer/song "
        "components as part of the Daniel work; their boundaries are not independently assessed. "
        "Chapter 14 labels its three lines 0, 1, and 2, unlike a sequence starting at 1. These "
        "are observations about TEI structure, not a completeness or accuracy check. No source wording is "
        "included. The lead remains unbundled and excluded from canon-linked reader coverage pending "
        "rights review, source identification, and crosswalk verification.\n",
        encoding="utf-8",
    )
    print("Recorded Daniel source metadata; the reader builder handles the separately licensed text extraction.")


if __name__ == "__main__":
    build()
