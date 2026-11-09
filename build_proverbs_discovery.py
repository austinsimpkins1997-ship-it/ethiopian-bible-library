"""Record the Proverbs source and crosswalk lead without bundling unresolved-rights text."""

from __future__ import annotations

import json
from archive_manifest import write_text_atomically
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-280"
SCHOLARLY_SOURCE_ID = "SRC-281"
LICENSE_CONTEXT_SOURCE_ID = "SRC-295"
EDITION_ID = "betamasaheft-proverbs-of-solomon-tei-2026"
COMMIT = "2574a6c84ed477af76122a6b112df3bbf45a96f5"
FILE_SHA256 = "474193ee1bbc75fdc8f83bfe25e409134035ab4672395494b823728ae8c9f225"
FILE_BYTES = 212_903
SOURCE_URL = (
    "https://github.com/BetaMasaheft/Works/blob/"
    f"{COMMIT}/3001-4000/LIT3927Messale.xml"
)
WORK_URL = "https://betamasaheft.awhamburg.de/works/LIT3927Messale/text"
SCHOLARLY_URL = "https://en.sewasew.com/p/wisdom-books-biblical"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    archive["readers"] = [
        item for item in archive.get("readers", [])
        if item.get("reader_id") != "proverbs-of-solomon-betamasaheft-tei-research"
    ]
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Beta maṣāḥǝft Works — Proverbs of Solomon (LIT3927Messale) source review",
        "url": WORK_URL,
        "inspection_and_limitations": (
            f"Inspected the pinned file at BetaMasaheft/Works commit {COMMIT} "
            f"({FILE_BYTES:,} bytes; SHA-256 {FILE_SHA256}); the XML is not included in this archive. "
            "The TEI root defaults to English. Its single edition division declares Geʽez and is labeled "
            "‘Text of the EOTC printed Bible.’ The Beta maṣāḥǝft work page says the text was digitized "
            "from modern Vulgata printed editions and converted to XML by its team. The TEI file states "
            "CC BY-SA 4.0, while the site separately displays a CC BY-NC-SA 4.0 footer; their "
            "relationship is unresolved, and rights in the unidentified modern printed exemplar are "
            "not established. The pinned TEI has 26 ordered chapter divisions and 766 labeled line "
            "elements, each linked to a reference target. These are structural counts, not a verse count, "
            "completeness finding, or proof of canon correspondence. No scripture wording is copied."
        ),
        "archive_status": (
            "Metadata-only edition lead; text withheld under the project rule for conflicting or "
            "unresolved rights and chapter crosswalk"
        ),
    }
    sources[SCHOLARLY_SOURCE_ID] = {
        "source_id": SCHOLARLY_SOURCE_ID,
        "source_name": "Encyclopaedia Aethiopica — ‘Wisdom Books, biblical’ (web-hosted article)",
        "url": SCHOLARLY_URL,
        "inspection_and_limitations": (
            "The page identifies its source as Encyclopaedia Aethiopica. It describes the traditional "
            "Ethiopian subdivision as Proverbs 1–24 (Méssale or Méssaléyatä Sälomon) and Proverbs "
            "25–29 (Tägíasä Sälomon), cites Dillmann’s Lexicon and Cowley 1988, and notes other "
            "Senodos canon enumerations. It also cites a printed Ethiopian edition with page ranges "
            "for the separately titled works. This secondary reference establishes that the tradition "
            "uses its own book boundaries; it does not identify the boundaries of the 26 divisions in "
            "the pinned Beta maṣāḥǝft TEI or establish a universal canon arrangement. The archive "
            "does not copy the article text."
        ),
        "archive_status": "Secondary scholarly crosswalk evidence; does not certify this TEI’s extent or Church-list identity",
    }
    sources[LICENSE_CONTEXT_SOURCE_ID] = {
        "source_id": LICENSE_CONTEXT_SOURCE_ID,
        "source_name": "University of Hamburg UHH Data Notes — Beta maṣāḥǝft TEI-XML dataset license metadata",
        "url": "https://www.fdm.uni-hamburg.de/en/uhh-data-notes/data-notes/issue-2020/dano-01-001.html",
        "inspection_and_limitations": (
            "The University of Hamburg data note describes the Beta maṣāḥǝft TEI-XML dataset as open and "
            "lists CC BY-SA 4.0. It states that each file contains a specific license statement and that the "
            "dataset default applies where a file has none. This supports recording the pinned Proverbs file's "
            "own CC BY-SA notice as file-specific evidence. It does not explain the current Beta maṣāḥǝft "
            "Guidelines' separate CC BY-NC-SA 4.0 statement, adjudicate the relationship between those notices, "
            "or establish rights in the unidentified printed exemplar from which the Geʽez text was digitized. "
            "Inspected 2026-10-25."
        ),
        "archive_status": "Primary institutional dataset-license metadata; informs file-level license scope but leaves current project-guidelines discrepancy and underlying print rights unresolved",
    }
    archive["sources"] = sorted(
        sources.values(), key=lambda item: int(item["source_id"].split("-")[1])
    )
    catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-029")
    catalogue["edition_or_translation"] = (
        "Online lead: Beta maṣāḥǝft LIT3927Messale, pinned source review; no reader bundled"
    )
    catalogue["chapter_count"] = "26 source divisions observed in a candidate TEI; Church-list mapping unresolved"
    catalogue["chapter_order_status"] = "TEI divisions labeled 1–26; not crosswalked to traditional Ethiopian Proverbs/Tegsats boundaries"
    catalogue["text_availability_status"] = "Text source identified online; not bundled because file/site license notices conflict and print rights are unresolved"
    catalogue["completeness_status"] = "Not assessed against a specified printed exemplar or Ethiopian book division"
    catalogue["rights_status"] = "Mixed/conflicting notices: file-level CC BY-SA and site-level CC BY-NC-SA; underlying print rights unknown"
    catalogue["verification_date"] = "2026-10-25"
    catalogue["source_id"] = SOURCE_ID
    catalogue["evidence_source_ids"] = ["SRC-002", SOURCE_ID, SCHOLARLY_SOURCE_ID, LICENSE_CONTEXT_SOURCE_ID]
    catalogue["reviewer_notes"] = (
        "The TEI calls its Geʽez edition ‘Text of the EOTC printed Bible’ but has 26 source chapters. "
        "Encyclopaedia Aethiopica describes Méssale as Prov 1–24 and Tägíasä as Prov 25–29; the "
        "specific crosswalk and remaining extent are unresolved. Text is withheld pending rights "
        "clarification under CONTENT-LICENSES.md. No source wording is bundled."
    )
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["research_corpora"] = [
        item for item in registry.get("research_corpora", [])
        if item.get("corpus_id") != "betamasaheft-proverbs-of-solomon-tei-research"
    ]
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[EDITION_ID] = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": "eotc-ot-24",
        "mapping_state": "uncertain",
        "title": "Proverbs of Solomon (LIT3927Messale), Beta maṣāḥǝft TEI source lead",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            f"Pinned Beta maṣāḥǝft {WORK_URL}; the source file is {FILE_BYTES:,} bytes, "
            f"SHA-256 {FILE_SHA256}, at Works commit {COMMIT}. Its only edition declares Geʽez and "
            "is labeled ‘Text of the EOTC printed Bible.’ The source says it derives from modern "
            "Vulgata printed editions."
        ),
        "scope_description": (
            "An online source lead, not a bundled reader. The TEI contains 26 ordered divisions and "
            "766 labeled lines with reference targets. Encyclopaedia Aethiopica describes the "
            "traditional division as Méssale (Proverbs 1–24) and Tägíasä (Proverbs 25–29); it does "
            "not establish how the 26 divisions in this TEI correspond to those books or whether "
            "the source covers the remaining scope. The title-level candidate crosswalk is uncertain."
        ),
        "source_ids": ["SRC-002", SOURCE_ID, SCHOLARLY_SOURCE_ID, LICENSE_CONTEXT_SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "Not cleared for redistribution under project policy: the TEI file says CC BY-SA 4.0 and "
            "the University of Hamburg data note explains that Beta maṣāḥǝft files carry specific license "
            "statements, but the current site guidelines separately say CC BY-NC-SA 4.0. Their relationship "
            "and rights in the unidentified modern printed exemplar remain unresolved."
        ),
        "rights_classification": "mixed",
        "review_status": (
            "Pinned source identity, license notices, edition language, source label, chapter and "
            "line counts, and scholarly division evidence inspected. Text not copied. Exact "
            "crosswalk, print rights, completeness, and transcription accuracy remain unverified."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (ROOT / "research" / "proverbs-source-review.md").write_text(
        "# Proverbs source review\n\n"
        f"Inspected [Beta maṣāḥǝft LIT3927Messale]({WORK_URL}) and the source file pinned at "
        f"[Works commit {COMMIT}]({SOURCE_URL}). The source file is {FILE_BYTES:,} bytes "
        f"(SHA-256 `{FILE_SHA256}`); the full file is not retained in the public site. Its sole Geʽez edition is "
        "labeled ‘Text of the EOTC printed Bible.’ The Beta maṣāḥǝft page says the text was digitized "
        "from modern Vulgata printed editions and converted to XML by its team.\n\n"
        "The file-level notice says CC BY-SA 4.0. The University of Hamburg [data note on the dataset]"
        "(https://www.fdm.uni-hamburg.de/en/uhh-data-notes/data-notes/issue-2020/dano-01-001.html) "
        "says each file has its own license statement, defaulting to CC BY-SA 4.0 where no file-level "
        "statement is present. Beta maṣāḥǝft’s current site Guidelines separately state CC BY-NC-SA 4.0. "
        "The data note does not resolve that discrepancy or establish rights in the unidentified printed exemplar. The "
        "project’s [content policy](../CONTENT-LICENSES.md) says not to bundle text while reuse terms "
        "conflict or remain unclear, so no scripture wording or source XML is included.\n\n"
        "The pinned file has 26 ordered chapter divisions and 766 labeled line elements, each linked "
        "to a reference target. These are source-structure counts only. The [Encyclopaedia Aethiopica "
        f"article on biblical wisdom books]({SCHOLARLY_URL}) describes the traditional split as "
        "Méssale (Proverbs 1–24) and Tägíasä Sälomon (Proverbs 25–29), and cites other canon "
        "enumerations. The TEI’s 26 divisions are not shown to correspond to either scope. This "
        "remains an uncertain edition lead, excluded from canon-linked reader coverage. No wording is bundled.\n",
        encoding="utf-8",
    )
    print("Recorded Proverbs source and scholarly crosswalk evidence; no text bundled or counted as coverage.")


if __name__ == "__main__":
    build()
