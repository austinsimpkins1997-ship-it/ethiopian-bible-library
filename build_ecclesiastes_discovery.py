"""Record a source-backed Ecclesiastes lead without redistributing uncertain-rights text."""

from __future__ import annotations

import json
from archive_manifest import write_text_atomically
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-279"
EDITION_ID = "betamasaheft-ecclesiastes-tei-2026"
COMMIT = "2574a6c84ed477af76122a6b112df3bbf45a96f5"
SOURCE_URL = (
    "https://github.com/BetaMasaheft/Works/blob/"
    f"{COMMIT}/1001-2000/LIT1320Eccles.xml"
)
WORK_URL = "https://betamasaheft.awhamburg.de/works/LIT1320Eccles/text"
FILE_SHA256 = "3af9fd2b36b52278058cd3278717690eeff3d30e4054b743eca70c96c1311b35"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Beta maṣāḥǝft Works — Ecclesiastes (LIT1320Eccles), pinned TEI source review",
        "url": WORK_URL,
        "inspection_and_limitations": (
            f"Inspected the source file at the pinned BetaMasaheft/Works commit {COMMIT} "
            f"({FILE_SHA256}; 152,281 bytes). The TEI root defaults to English; two separate "
            "edition divisions declare Geʽez (gez): Mercer and EOTCed. Each has 12 explicit, "
            "ordered chapter divisions. Mercer has 222 TEI line elements and its edition "
            "statement grants only noncommercial use of that transcription. EOTCed is explicitly "
            "labeled ‘Text of the EOTC printed Bible’; its file-level TEI licence states CC BY-SA "
            "4.0, while the source says this text was digitized from modern Vulgata printed editions "
            "and converted to XML by the Beta maṣāḥǝft team. The exact printed exemplar and its "
            "rights are not identified. The TEI file contains both editions; the compound file is not redistributed. A separate EOTCed-only extract is bundled under SRC-294, while the exact print exemplar and underlying rights remain unresolved. The EOTCed division has 226 line elements and 222 "
            "reference links. Its `l/@n` markers and reference targets are not interchangeable: in "
            "chapter 12, source markers 14–17 point to targets 11–14. These counts are TEI structure, "
            "not a count of biblical verses or proof of completeness or accuracy. The compound file is not bundled; an EOTCed-only extract is separately catalogued under SRC-294."
        ),
        "archive_status": (
            "Pinned source reviewed; the compound TEI is not distributed, while an EOTCed-only extract is separately recorded as SRC-294; "
            "edition mapping, underlying print rights, completeness, and transcription accuracy unresolved"
        ),
    }
    archive["sources"] = sorted(
        sources.values(), key=lambda item: int(item["source_id"].split("-")[1])
    )

    catalogue = next(
        item for item in archive["catalogue"] if item.get("display_name") == "Ecclesiastes"
    )
    catalogue.update(
        {
            "identity_status": "Beta maṣāḥǝft TEI includes a division labeled ‘Text of the EOTC printed Bible’; exact print exemplar not identified",
            "edition_or_translation": "Beta maṣāḥǝft LIT1320Eccles, EOTCed division; source file pinned at Works commit " + COMMIT,
            "chapter_count": "12 ordered source divisions observed in the TEI; offline text not bundled",
            "chapter_order_status": "Explicit divisions 1–12 observed; no cross-check against a print exemplar",
            "text_availability_status": "Source lead identified online; text not bundled while per-edition and underlying-print reuse rights remain unresolved",
            "completeness_status": "Not assessed against the exact printed exemplar",
            "rights_status": "File-level CC BY-SA 4.0 notice coexists with a noncommercial notice for the separate Mercer division; rights in the EOTC-labeled division’s modern printed exemplar are unresolved",
            "verification_date": "2026-10-25",
            "reviewer_notes": (
                "The source has separate Mercer and EOTCed Geʽez editions. Mercer is expressly "
                "noncommercial; the EOTCed text is labeled as from the printed EOTC Bible but its "
                "exact exemplar and underlying rights are unknown. The 226 EOTCed line elements "
                "are not treated as verse counts; chapter 12 source markers 14–17 map to linked "
                "reference targets 11–14. No text is copied or counted as reader coverage."
            ),
            "source_id": SOURCE_ID,
            "evidence_source_ids": ["SRC-002", SOURCE_ID],
        }
    )
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[EDITION_ID] = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": "eotc-ot-27",
        "mapping_state": "uncertain",
        "title": "Ecclesiastes (LIT1320Eccles), Beta maṣāḥǝft TEI editions",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "Pinned Beta maṣāḥǝft LIT1320Eccles TEI file. It contains distinct Mercer and EOTCed "
            "Geʽez edition divisions. EOTCed is labeled ‘Text of the EOTC printed Bible’; the source "
            "says it was digitized from modern Vulgata printed editions. Exact print exemplar and "
            "underlying rights are not established."
        ),
        "scope_description": (
            "Provisional candidate for the Church-list Ecclesiastes entry. Both TEI divisions have "
            "12 explicit chapter divisions. The EOTCed division has 226 line elements and 222 "
            "reference links; the source's chapter 12 line markers 14–17 link to targets 11–14. "
            "The line count is not a verse count. The full file also contains a separate Mercer "
            "transcription expressly restricted to noncommercial use and excluded from the EOTCed-only extract. The exact EOTC print rights and relationship between license notices remain unresolved. Accuracy and completeness are unverified."
        ),
        "source_ids": [SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "Unresolved for redistribution: file-level CC BY-SA 4.0 notice; separate Mercer "
            "edition has noncommercial terms; rights in the EOTC-labeled modern printed exemplar "
            "are not established."
        ),
        "rights_classification": "mixed",
        "review_status": (
            "Pinned TEI identity, edition divisions, Geʽez declarations, chapter structure, line "
            "counts, references, and conflicting scope-specific rights notices inspected. The separate Mercer division is excluded; the scoped EOTCed extract is recorded in SRC-294. Exact EOTC exemplar, underlying print rights, completeness, and accuracy "
            "remain unverified."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit_path = ROOT / "research" / "ecclesiastes-source-audit.md"
    audit_path.write_text(
        "# Ecclesiastes source review\n\n"
        f"Inspected the pinned [Beta maṣāḥǝft TEI file]({SOURCE_URL}) and its [work text page]({WORK_URL}). "
        f"The inspected file was 152,281 bytes, SHA-256 `{FILE_SHA256}`. It contains two distinct "
        "Geʽez editions, `Mercer` and `EOTCed`; the TEI root defaults to English. Each edition "
        "contains 12 explicitly ordered chapter divisions.\n\n"
        "The `EOTCed` division is labeled ‘Text of the EOTC printed Bible.’ The source says this "
        "version was digitized from modern Vulgata printed editions and converted to XML by the "
        "Beta maṣāḥǝft team. The TEI file has a CC BY-SA 4.0 notice. The same TEI header states "
        "that the separate Mercer transcription is copyright Ran HaCohen and carries a "
        "noncommercial permission notice. The exact modern print exemplar and its rights are not "
        "identified. Because the compound file combines those distinct notices, the full compound XML is not bundled. An EOTCed-only extract is separately bundled under SRC-294, but the file-level CC BY-SA notice is not treated as a resolution of rights in the EOTC division’s unidentified printed source.\n\n"
        "Structural observation only: `EOTCed` has 226 TEI line elements and 222 reference links. "
        "The line `n` attributes are preserved separately from reference targets. In chapter 12, "
        "source markers 14–17 point to linked targets 11–14. These are not assumed to be biblical "
        "verse counts. No independent collation, accuracy review, or completeness check against a "
        "specific print exemplar has been performed. The EOTCed-only reader is separately counted as a source-asserted title link; physical completeness and accuracy remain unverified.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build()
    print("Recorded Ecclesiastes source lead; text remains unbundled pending rights clarification.")
