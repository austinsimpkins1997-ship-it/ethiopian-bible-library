"""Record TAU's historical Ethiopic Ezra–Nehemiah edition and menu scope."""

from __future__ import annotations

import json
from pathlib import Path

from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
CANON_ID = "eotc-ot-15"
CATALOGUE_IDS = ("eotc-017", "eotc-018")
SOURCE_ID = "SRC-361"
EDITION_SOURCE_ID = "SRC-362"
EDITION_ID = "tau-pereira-ezra-nehemia-1919"
INDEX_URL = "https://www.tau.ac.il/~hacohen/Biblia.html"
INFO_URL = "https://www.tau.ac.il/~hacohen/Ezra/Information.html"
RIGHTS_URL = "https://www.tau.ac.il/~hacohen/Information.html"
PEREIRA_PDF_URL = "https://www.patristique.org/sites/patristique.org/IMG/pdf/po_66_xiii_5.pdf"
MENU_PAGES = [11, 13, 17, 20, 24, 27, 30, 34, 39, 41, 46, 48, 51, 56, 59, 63, 66, 71, 74, 80, 84, 87, 92]
MENU_AUDIT = {
    "url": INDEX_URL,
    "http_status": 200,
    "size_bytes": 111977,
    "sha256": "0686b54eeb4f6d69e247b19eb1d03f69154f5c006a60be456402538a91e31c70",
    "observed_at": "2026-10-26",
    "form_title": "Ezra and Nehemia",
    "entry_count": 23,
    "printed_edition_structure": {
        "bibliographic_edition": "F. M. Esteves Pereira, Patrologia Orientalis XIII.5 no. 66; Paris, 1919; 1988 facsimile scan",
        "chapter_count": 23,
        "chapter_numbering": "I–XXIII",
        "book_sections": {"Ezra": "I–X", "Nehemiah": "XI–XXIII"},
        "manuscript_variation": [
            {
                "witness": "Collection d'Abbadie, MS 35",
                "reported_chapter_count": 21,
                "boundary_note": "Pereira's prose says Ezra I–IX and Nehemiah X–XXI; the following concordance table places Nehemiah I:1 at chapter IX. Preserve as an unresolved inconsistency in the edition's description.",
            },
            {
                "witness": "British Museum Add. 16.188",
                "reported_chapter_count": None,
                "boundary_note": "Pereira says this manuscript is not divided into chapters.",
            },
        ],
        "menu_alignment": "TAU has 23 ordered targets, consistent with the 23 printed chapters; individual target-to-page alignment was not checked.",
        "completeness_verified": False,
        "source_id": EDITION_SOURCE_ID,
    },
    "entries": [
        {"label": label, "source_path": f"Ezra/Ezrap {page}.html"}
        for label, page in enumerate(MENU_PAGES, 1)
    ],
}


def append_once(value: str, addition: str) -> str:
    value = value.strip()
    return value if addition in value else f"{value} {addition}".strip()


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Tel Aviv University — Ethiopic Bible index, Ezra and Nehemia menu audit",
        "url": INDEX_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The live index form titled ‘Ezra and Nehemia’ exposes 23 menu options numbered 1–23, "
            "targeting TAU page wrappers Ezrap 11 through Ezrap 92 in source order. The retained menu audit records the "
            "HTTP response size and SHA-256 plus each option label and path; the source HTML and page images are not copied. "
            "TAU's separate Ezra information page says each chapter is accessible from the menu and identifies its Ethiopic "
            "Ezrâ III as canonical Ezra and Nehemiah. Pereira's printed 1919 edition is numbered I–XXIII, with Ezra X "
            "ending before Nehemiah XI begins (SRC-362); the 23 menu targets are consistent with this numbering but were "
            "not individually collated against print pages. Pereira reports manuscript chapter divisions vary. Completeness, "
            "wording, and current EOTC-edition identity remain unverified."
        ),
        "archive_status": "Primary index menu audit; external page images identified, no text or images bundled",
    }
    sources[EDITION_SOURCE_ID] = {
        "source_id": EDITION_SOURCE_ID,
        "source_name": "Pereira, Le troisième livre de ‘Ezrâ — Ethiopic text and French translation (1919 edition; 1988 facsimile scan)",
        "url": PEREIRA_PDF_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The 98-page PDF identifies Francisco Maria Esteves Pereira's Ethiopic/French edition as "
            "Patrologia Orientalis XIII.5 no. 66, original Paris 1919, in a 1988 facsimile reprint. The printed text is "
            "numbered through chapter XXIII; its headings and adjacent text show Ezra X ending before Nehemiah XI begins. "
            "Pereira says manuscript chapter divisions vary. He describes d'Abbadie MS 35 as having 21 chapters, but the "
            "introductory prose and following chapter-to-Greek-verse concordance differ about its Ezra/Nehemiah boundary; "
            "he says British Museum Add. 16.188 has no chapter divisions. This supports the printed edition's structure, "
            "not completeness or identity with a current EOTC edition. No pages or wording are bundled; reuse rights for "
            "this hosted facsimile and its French translation have not been established."
        ),
        "archive_status": "Bibliographic and chapter-structure evidence; external facsimile linked, no text or images bundled",
    }
    sources["SRC-097"]["local_review_url"] = "research/ezra-nehemia-source-review.md"
    sources["SRC-034"]["inspection_and_limitations"] = append_once(
        sources["SRC-034"]["inspection_and_limitations"],
        "Ezra follow-up (2026-10-26): the live ‘Ezra and Nehemia’ form exposes 23 menu options numbered 1–23; see SRC-361 and research/ezra-nehemia-menu-audit.json. This records menu structure only, not a page-by-page text audit or proof of completeness.",
    )
    sources["SRC-034"]["inspection_and_limitations"] = append_once(
        sources["SRC-034"]["inspection_and_limitations"],
        "Pereira structural follow-up (2026-10-26): the 1919 printed edition numbers the grouped work I–XXIII, with Ezra X ending before Nehemiah XI begins (SRC-362); TAU's 23 menu targets are consistent with this, but were not individually collated. Pereira reports manuscript chapter divisions vary, including an unchaptered witness.",
    )
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].rsplit("-", 1)[1]))

    canon_path = ROOT / "canon-registry.json"
    canon = json.loads(canon_path.read_text(encoding="utf-8"))
    book = next(item for item in canon["books"] if item["canon_id"] == CANON_ID)
    source_ids = set(book.get("source_ids", [])) | {"SRC-029", "SRC-034", "SRC-097", "SRC-100", SOURCE_ID, EDITION_SOURCE_ID}
    book["source_ids"] = sorted(source_ids, key=lambda value: int(value.rsplit("-", 1)[1]))
    book["mapping_state"] = "reviewed_match"
    book["reader_status"] = (
        "Historical Geʽez Ezra–Nehemiah edition and its I–XXIII print numbering documented; no local reader text bundled, "
        "and print completeness is unverified."
    )
    book["mapping_note"] = (
        "Reviewed work/title match: the Church list groups ‘Ezra and Nehemia’; TAU identifies Pereira's Ethiopic Ezrâ III "
        "as the canonical book containing Ezra and Nehemiah. The 1919 print edition numbers Ezra I–X and Nehemiah XI–XXIII; "
        "TAU exposes 23 menu links consistent with this numbering, but they were not individually collated. Manuscript "
        "chapter divisions vary. This is not proof of completeness or a match to a current EOTC edition. "
        "No text or images are bundled."
    )
    archive["canon_registry"] = canon

    for catalogue_id in CATALOGUE_IDS:
        row = next(item for item in archive["catalogue"] if item["catalogue_id"] == catalogue_id)
        row["identity_status"] = "Historical grouped Ezra–Nehemiah work identified; Pereira 1919 boundary documented, current-edition identity unverified"
        row["edition_or_translation"] = "F. M. Esteves Pereira, Le troisième livre de ‘Ezrâ (Esdras et Néhémie canoniques), Patrologia Orientalis XIII.5 (Paris, 1919); digitized page images linked by TAU"
        row["chapter_count"] = "Pereira 1919 printed edition: 23 numbered chapters (Ezra I–X; Nehemiah XI–XXIII); TAU menu lists 23 targets. Manuscript divisions vary."
        row["chapter_order_status"] = "Printed edition sequence I–XXIII and book transition X/XI observed; TAU menu has 23 ordered targets consistent with it, but links were not individually collated."
        row["text_availability_status"] = "External page images are linked at TAU; no local transcription or scan images are bundled"
        row["completeness_status"] = "Printed chapter structure documented, but completeness not assessed against all pages, a manuscript, or a current EOTC witness"
        row["rights_status"] = (
            "TAU grants conditional noncommercial copying of digitized Ethiopic texts with the Ran HaCohen copyright and permission notices. "
            "This is not an open license. The displayed page images also include a French translation; the scope of permission for those "
            "images and French text is not established here. This archive links to TAU and bundles no pages."
        )
        row["verification_date"] = "2026-10-26"
        row["evidence_source_ids"] = ["SRC-029", "SRC-034", "SRC-097", "SRC-100", SOURCE_ID, EDITION_SOURCE_ID]
        row["reviewer_notes"] = (
            "TAU's book-specific note distinguishes Ethiopic Ezrâ III as the canonical Ezra–Nehemiah work. Pereira's 1919 "
            "printed edition is numbered I–XXIII, with the transition between Ezra X and Nehemiah XI; its manuscript witnesses "
            "vary in chapter divisions. TAU's 23 links are consistent with the printed scheme but have not been individually "
            "matched. Completeness, a current EOTC printed edition, and the Church-list display split remain unverified. "
            "No local text or images are bundled. See research/ezra-nehemia-source-review.md."
        )

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[EDITION_ID] = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": CANON_ID,
        "mapping_state": "reviewed_match",
        "title": "Canonical Ethiopic Ezra and Nehemiah (Ezrâ III), Pereira 1919 — TAU digitized edition lead",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "F. M. Esteves Pereira (ed.), Le troisième livre de ‘Ezrâ (Esdras et Néhémie canoniques): version éthiopienne, "
            "Patrologia Orientalis XIII.5 (Paris, 1919); online page images and notes by Tel Aviv University / Ran HaCohen."
        ),
        "scope_description": (
            "TAU identifies Ezrâ III as the canonical book containing Ezra and Nehemiah. Pereira's 1919 printed edition has "
            "numbered chapters I–XXIII, with Ezra ending at X and Nehemiah beginning at XI; TAU's 23 ordered targets are "
            "consistent with that scheme. Pereira reports manuscript chapter divisions vary, including a 21-chapter witness "
            "and an unchaptered witness. Menu-to-print alignment, full completeness, and identity with a current EOTC edition "
            "remain unverified."
        ),
        "source_ids": ["SRC-029", "SRC-034", "SRC-097", "SRC-100", SOURCE_ID, EDITION_SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "TAU permits noncommercial copying of digitized Ethiopic texts with its required attribution and permission notices; "
            "this is not an open license. The scope of that notice for the displayed page images, which include French text, "
            "has not been established for this package. No pages are copied or bundled."
        ),
        "rights_classification": "permission_limited",
        "review_status": (
            "TAU's title-specific notes and live index menu were inspected; the menu response and 23 entries are recorded in "
            "research/ezra-nehemia-menu-audit.json. Pereira's printed chapter headings and book transition were inspected in "
            "SRC-362. The 23 menu links were not individually matched to print pages; no full textual accuracy, completeness, "
            "or current-edition comparison was made."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    archive["translation_registry"] = registry

    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(canon_path, json.dumps(canon, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(registry_path, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(
        ROOT / "research" / "ezra-nehemia-menu-audit.json",
        json.dumps({"schema_version": 1, **MENU_AUDIT}, ensure_ascii=False, indent=2) + "\n",
    )
    review = f"""# Ezra and Nehemia source review

## Work identification

The Ethiopian Orthodox Tewahedo Church's English list groups **Ezra and Nehemia** as one of its 81 entries (Old Testament entry 15). Tel Aviv University's [book-specific notes]({INFO_URL}) identify the displayed Geʽez work as F. M. Esteves Pereira's 1919 *Le troisième livre de ‘Ezrâ (Esdras et Néhémie canoniques)*. They distinguish this canonical Ezrâ III from the separately numbered Ethiopic Ezra I and II works. This supports a scoped historical work/title match to the Church-list wording; it does not establish identity with a current EOTC printed edition.

## What the digital evidence establishes

The live [TAU Ethiopic Bible index]({INDEX_URL}) was inspected on 2026-10-26. Its form titled “Ezra and Nehemia” displayed 23 menu options labeled 1–23, targeting page wrappers in the source order recorded in [the menu audit](ezra-nehemia-menu-audit.json). The response was 111,977 bytes with SHA-256 `{MENU_AUDIT['sha256']}`. TAU says each chapter is accessible from this menu.

The digitized [Pereira edition PDF]({PEREIRA_PDF_URL}) is a 98-page scan of the 1919 edition in a 1988 facsimile reprint. Its printed text is numbered I–XXIII: Ezra ends at chapter X and Nehemiah begins at XI. The 23 ordered TAU targets are consistent with this print structure, but were not individually matched to print pages. Pereira explicitly says manuscript chapter divisions vary. For d'Abbadie MS 35 he reports 21 chapters, while his introductory prose and following chapter-to-Greek-verse table differ about the precise Ezra/Nehemiah boundary; for British Museum Add. 16.188 he says the text has no chapter divisions. These are edition- and witness-specific structures. This review does not prove every page is present or textually accurate, or that the edition matches a current EOTC printed Bible. No local scan, OCR, or scripture wording was created.

## Rights and archive treatment

TAU's [site-wide notice]({RIGHTS_URL}) grants permission to use, copy, and distribute digitized Ethiopic texts for noncommercial purposes when its copyright and permission notices accompany each copy. This is conditional permission, not an open license. The displayed pages include a French translation; the rights scope for reproducing the images and French text was not resolved. The archive therefore links to TAU but bundles no page images, OCR, or scripture wording. The catalogue records the external lead and its limits; reader coverage does not increase.

## Evidence

- Church-list wording and 81-entry count: [SRC-029](https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en)
- TAU's book-specific edition identification: [SRC-097]({INFO_URL})
- TAU index menu and ordered 23-link audit: [SRC-034]({INDEX_URL}) and [SRC-361]({INDEX_URL})
- Pereira edition title, print structure, and manuscript variation: [SRC-362]({PEREIRA_PDF_URL})
- TAU conditional reuse notice: [SRC-100]({RIGHTS_URL})
"""
    write_text_atomically(ROOT / "research" / "ezra-nehemia-source-review.md", review)
    print("Recorded TAU's historical Ezra–Nehemiah edition and 23 menu targets; no text or images bundled and no reader coverage added.")


if __name__ == "__main__":
    build()
