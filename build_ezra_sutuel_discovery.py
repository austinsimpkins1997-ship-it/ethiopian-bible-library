"""Record EAP scope and access evidence for the grouped Ezra canon entry."""
from __future__ import annotations

import json
from pathlib import Path

from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-347"
BL_CATALOGUE_ID = "SRC-200"
TAU_MENU_SOURCE_ID = "SRC-421"
CANON_ID = "eotc-ot-16"
EDITION_ID = "bl-eap286-1-1-499-ezra-sutuel"
TAU_EDITION_ID = "tau-dillmann-1894-ezrae-apocalypsis-images"
EAP_URL = "https://eap.bl.uk/archive-file/EAP286-1-1-499"
CHURCH_SOURCE_ID = "SRC-029"
LAURENCE_HATHI_ID = "SRC-378"
LAURENCE_GOOGLE_ID = "SRC-379"
LAURENCE_EDITION_ID = "laurence-ethiopic-4ezra-english-1820"


def _sort_source_ids(values: set[str]) -> list[str]:
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
        "source_name": "British Library Endangered Archives Programme — digitized EAP286/1/1/499",
        "url": EAP_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-25. The EAP digitized-item page describes one parchment codex, dated late 16th to early 17th century, "
            "in Geez and Ethiopic (Ge'ez) script, and lists 126 TIFF images held originally by the Institute of Ethiopian Studies, "
            "Addis Ababa University. Its title names ‘Book of Ezra Sutu'el, Book of Second Ezra, excerpt from Prayer of the Covenant’ "
            "and its legal field says ‘Access is for research purposes only.’ That access statement is not a copyright license or an "
            "express reuse grant. The record does not establish item boundaries, text completeness, or a Church-list sublabel crosswalk. "
            "No manuscript text or images are copied."
        ),
        "archive_status": "Digitized manuscript metadata; research-only access label observed; reuse rights and textual boundaries unresolved",
    }
    sources[LAURENCE_HATHI_ID] = {
        "source_id": LAURENCE_HATHI_ID,
        "source_name": "HathiTrust Digital Library — Laurence, Primi Ezrae libri (1820), catalog record and full-view item",
        "url": "https://catalog.hathitrust.org/Record/009706619",
        "full_view_url": "https://babel.hathitrust.org/cgi/pt?id=hvd.ah5jfu",
        "inspection_and_limitations": (
            "Inspected 2026-10-26. HathiTrust's catalog record identifies Richard Laurence (1760–1838) as translator, gives publication at "
            "Oxford by J. Parker and others in 1820, lists Ethiopic, English, and Latin, describes vii + 322 pages, and links to a Harvard "
            "full-view copy. This is edition-level bibliographic evidence, not a checked transcription, chapter-boundary audit, or proof that "
            "the volume's work maps to either sublabel in the Ethiopian Orthodox Church's grouped Ezra entry. No text or page images are bundled."
        ),
        "archive_status": "Full-view historical edition lead; no text bundled; canon crosswalk and exact English chapter coverage not verified",
    }
    sources[LAURENCE_GOOGLE_ID] = {
        "source_id": LAURENCE_GOOGLE_ID,
        "source_name": "Google Books — Laurence, Primi Ezrae libri (1820), digitized copy metadata",
        "url": "https://books.google.com/books/about/Primi_Ezr%C3%A6_libri.html?id=hcVCAAAAYAAJ",
        "inspection_and_limitations": (
            "Inspected 2026-10-26. Google Books identifies the title as an Ethiopic version of the work called Fourth Ezra in the Vulgate, "
            "translated into Latin and English by Richard Laurence; it gives Typis Academicis, 1820, New York Public Library as the original "
            "source, and 322 pages. It corroborates bibliographic identity but does not establish exact chapter coverage, textual accuracy, "
            "or a crosswalk to the Church's grouped Ezra title. No text or page images are bundled."
        ),
        "archive_status": "Bibliographic corroboration for Laurence's 1820 Ethiopic / English / Latin edition; no reader text or canon crosswalk established",
    }
    sources[TAU_MENU_SOURCE_ID] = {
        "source_id": TAU_MENU_SOURCE_ID,
        "source_name": "Tel Aviv University — Ethiopic Bible index: Ezrae Apocalypsis menu",
        "url": "https://www.tau.ac.il/~hacohen/Biblia.html",
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The main index form titled ‘The Apocalypse of Esdras (2 Esdras)’ and labeled ‘Ezrae Apocalypsis’ "
            "lists menu labels 1–14 with image-page targets Apocryphi/Apop 153.html, 155, 158, 161, 164, 166, 170, 172, 175, 177, 181, 183, 186, and 189; a plus-sign target at 192 follows. "
            "The linked HTML pages display scanned page images, not a parsed transcription. This menu inventory confirms access points only; it does not independently establish that each is a chapter boundary, all pages of each chapter, complete book scope, exact current-edition identity, or textual accuracy. No pages or text are bundled."
        ),
        "archive_status": "External image-edition menu inventoried; 14 numbered access points; no text or image pages bundled",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].rsplit("-", 1)[1]))

    addition = (
        "The British Library EAP title lists Ezra Sutu'el, Book of Second Ezra, and an excerpt from the Prayer of the Covenant for one codex; "
        "this catalogue title does not establish separate internal boundaries or a complete witness to either Church-list component. "
        "The exact work mappings for the Church-list sublabels to the manuscript remain unresolved."
    )
    canon_path = ROOT / "canon-registry.json"
    canon = json.loads(canon_path.read_text(encoding="utf-8"))
    book = next(item for item in canon["books"] if item["canon_id"] == CANON_ID)
    book["source_ids"] = _sort_source_ids(set(book.get("source_ids", [])) | {CHURCH_SOURCE_ID, BL_CATALOGUE_ID, SOURCE_ID, TAU_MENU_SOURCE_ID, "SRC-097", "SRC-098", "SRC-100"})
    book["mapping_note"] = _append_once(book.get("mapping_note", ""), addition)

    catalogue_addition = (
        "The EAP item page for EAP286/1/1/499 names Ezra Sutu'el, Book of Second Ezra, and a Prayer of the Covenant excerpt in one codex. "
        "The Church and TAU evidence supports a provisional title-family crosswalk between the two Ezra sublabels and the third-/fourth-Esdras traditions, "
        "but the manuscript's internal boundaries, completeness, exact edition identity, and text remain unverified. TAU separately lists a 14-target image menu for the Apocalypse of Esdras; those targets have not been audited as complete chapter boundaries and are not bundled. The EAP page lists 126 TIFF images and research-only access; no reuse license is established."
    )
    for catalogue_id in ("eotc-019", "eotc-090"):
        row = next(item for item in archive["catalogue"] if item["catalogue_id"] == catalogue_id)
        row["evidence_source_ids"] = _sort_source_ids(set(row.get("evidence_source_ids", [])) | {BL_CATALOGUE_ID, SOURCE_ID, TAU_MENU_SOURCE_ID})
        row["identity_status"] = "Church-list sublabel preserved; manuscript title candidate observed; exact work identity unresolved"
        row["text_availability_status"] = (
            "A digitized manuscript image lead is recorded (126 TIFF images); no text transcription or images are bundled, "
            "and item boundaries and completeness remain unassessed."
        )
        row["rights_status"] = (
            "The EAP image page states ‘Access is for research purposes only’; it does not state a manuscript reuse license. "
            "Rights classification remains unknown; no text or images are copied."
        )
        row["verification_date"] = "2026-10-25"
        row["reviewer_notes"] = _append_once(row.get("reviewer_notes", ""), catalogue_addition)

    archive["canon_registry"] = canon
    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    lead = next(item for item in registry["edition_leads"] if item["edition_id"] == EDITION_ID)
    lead["source_ids"] = _sort_source_ids(set(lead.get("source_ids", [])) | {BL_CATALOGUE_ID, SOURCE_ID})
    lead["rights_status"] = (
        "The British Library EAP digital-item page labels access ‘for research purposes only’; it gives no explicit license for "
        "redistribution or adaptation of manuscript text or images. The rights classification remains unknown. Do not treat the "
        "access statement as permission to copy or republish. No text or images are bundled."
    )
    lead["review_status"] = (
        "The British Library catalogue and linked EAP item page were inspected. The page identifies a 126-image Ge'ez/Ethiopic "
        "parchment codex and research-only access. Church and TAU evidence supports only a provisional title-family crosswalk for the grouped entry. "
        "Image contents, manuscript sublabel boundaries, completeness, exact edition identity, and manuscript/text rights remain unreviewed."
    )

    if not any(item.get("edition_id") == LAURENCE_EDITION_ID for item in registry.get("edition_leads", [])):
        registry.setdefault("edition_leads", []).append({
            "edition_id": LAURENCE_EDITION_ID,
            "candidate_canon_id": None,
            "mapping_state": "not_mapped",
            "title": "English translation in Laurence's Ethiopic Apocalypse of Ezra edition (1820)",
            "witness_type": "printed_edition",
            "language_tag": "en",
            "language_name": "English",
            "script_code": "Latn",
            "edition_statement": (
                "Richard Laurence, Primi Ezrae libri qui apud Vulgatam appellatur quartus, versio Aethiopica; nunc primo in medium prolata, "
                "et Latine Angliceque reddita (Oxford, 1820). HathiTrust catalogs the printed volume in Ethiopic, English, and Latin; "
                "Google Books identifies it as the Ethiopic version of Fourth Ezra in the Vulgate."
            ),
            "scope_description": (
                "This lead points to the English component of a historical trilingual printed edition that also contains Ethiopic and Latin. "
                "Tel Aviv University's Dillmann-edition note says Laurence's English translation begins on p. 199. The exact English text "
                "coverage and chapter boundaries have not been checked against the 1820 volume. TAU's numbering notes distinguish Ethiopic "
                "Ezra works, while the Church list groups ‘Ezra (2nd) and Ezra Sutuel’; no crosswalk between this edition and that grouped "
                "Church entry is established. This is not bundled reader text and does not count as coverage."
            ),
            "source_ids": ["SRC-097", "SRC-098", LAURENCE_HATHI_ID, LAURENCE_GOOGLE_ID],
            "text_bundled": False,
            "rights_status": (
                "The 1820 printed text is historically old, but this archive has not completed jurisdiction-specific rights review or "
                "established reuse terms for HathiTrust/Google Books page images. No text or scans are copied or bundled."
            ),
            "rights_classification": "unknown",
            "review_status": (
                "HathiTrust catalog and linked full-view record and Google Books bibliographic metadata were inspected. The edition's "
                "language set, date, translator, and 322-page extent are catalog-confirmed; TAU says the English translation begins at p. 199. "
                "The text itself, chapter range, completeness, translation quality, rights for page images, and Church-list crosswalk remain "
                "unverified."
            ),
        })
    archive["translation_registry"] = registry
    tau_lead = next((item for item in registry.get("edition_leads", []) if item.get("edition_id") == TAU_EDITION_ID), None)
    if tau_lead is None:
        tau_lead = {
            "edition_id": TAU_EDITION_ID,
            "candidate_canon_id": CANON_ID,
            "mapping_state": "uncertain",
            "title": "Ezrae Apocalypsis (Apocalypse of Esdras) — Dillmann 1894, TAU image edition",
            "witness_type": "digital_edition",
            "language_tag": "gez",
            "language_name": "Geʽez (Classical Ethiopic)",
            "script_code": "Ethi",
            "edition_statement": "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Quintus, quo continentur Libri Apocryphi, Berlin, 1894. TAU describes an internet image version and labels the work ‘The Apocalypse of Esdras (2 Esdras)’ / ‘Ezrae Apocalypsis.’",
            "scope_description": "TAU's main index lists 14 numbered menu access points for this image edition. Its crosswalk to the Church's grouped ‘Ezra (2nd) and Ezra Sutuel’ entry is provisional by title-family only; TAU's separate Ezra notes equate Ethiopic Ezra I / Apocalypse of Esdras with Vulgate fourth Esdras. The menu does not establish full pagination, chapter boundaries, completeness, exact current-edition identity, or textual accuracy. The page targets show scanned images rather than a parsed text. No image pages or transcription are bundled, and this lead is not reader coverage.",
            "source_ids": [CHURCH_SOURCE_ID, "SRC-097", "SRC-098", "SRC-100", TAU_MENU_SOURCE_ID],
            "text_bundled": False,
            "rights_status": "TAU's site-wide notice permits noncommercial use, copying, and distribution of digitized Ethiopic texts only with the required Ran HaCohen copyright and permission notice; other uses require contacting the copyright owner. The archive does not bundle text or images. This is permission-limited, not an open-content or commercial license; underlying edition and image rights have not been independently determined.",
            "rights_classification": "permission_limited",
            "review_status": "The TAU information page, main-index menu, and site-wide notice were inspected. Fourteen numbered image-page targets were inventoried. The image pages were not audited as a complete sequence; chapter boundaries, physical-page continuity, transcription, completeness, accuracy, exact canon crosswalk, and worldwide rights are not established.",
        }
        registry.setdefault("edition_leads", []).append(tau_lead)
    else:
        tau_lead["source_ids"] = _sort_source_ids(set(tau_lead.get("source_ids", [])) | {CHURCH_SOURCE_ID, "SRC-097", "SRC-098", "SRC-100", TAU_MENU_SOURCE_ID})
        tau_lead["review_status"] = "The TAU information page, main-index menu, and site-wide notice were inspected. Fourteen numbered image-page targets were inventoried. The image pages were not audited as a complete sequence; chapter boundaries, physical-page continuity, transcription, completeness, accuracy, exact canon crosswalk, and worldwide rights are not established."

    review = """# Ezra Sutu'el and Second Ezra: source-scope review

## Evidence kept distinct

- The Ethiopian Orthodox Tewahedo Church's English list groups “Ezra (2nd) and Ezra Sutuel” as one entry (number 16); it separately lists “Ezra and Nehemia” as entry 15. The same page says the Ethiopic Bible includes the third and fourth Esdras, without assigning those names to specific manuscripts or editions.
- Tel Aviv University's notes for Pereira's 1919 Ethiopic Ezra edition distinguish three Ethiopic works: Ezra I (Apocalypse of Esdras / Vulgate 4 Esdras), Ezra II (Septuagint Esdras alpha / Vulgate 3 Esdras), and Ezra III (canonical Ezra and Nehemiah). Read together with the Church page, this supports a **provisional title-family crosswalk**: “Ezra (2nd)” likely corresponds to the third-Esdras work and “Ezra Sutuel” likely to the fourth-Esdras apocalypse. This is an evidence-based inference, not an explicit crosswalk in either source. TAU's 1894 Dillmann Apocryphi page uses its own labels (“2 Esdras” for Apocalypse of Esdras and “1 Esdras” for Apocryphal Esdras), demonstrating why numbering must remain attached to its source and cannot be transferred by numeral alone.
- The British Library EAP item EAP286/1/1/499 describes one parchment codex, dated 1560–1640, in Geez/Ethiopic script, with 126 TIFF images. Its title names Ezra Sutu'el, Book of Second Ezra, and an excerpt from the Prayer of the Covenant (folio 44r). The linked EAP page states that access is for research purposes only.
- TAU's main Ethiopic Bible menu labels the Dillmann 1894 image edition “The Apocalypse of Esdras (2 Esdras)” / “Ezrae Apocalypsis” and lists 14 numbered access points, followed by a notes link. The numbered targets open scanned page images. The archive inventories the menu but has not verified the pages as a continuous or complete chapter sequence; no image pages or text are bundled.

## Archive treatment

The EAP record is a manuscript discovery lead whose title names both Ezra Sutu'el and Book of Second Ezra, consistent with the provisional title-family crosswalk above. Its internal boundaries, relation to TAU's separately edited Ethiopic works, completeness, exact edition identity, and textual accuracy remain unknown. The EAP research-access notice is not treated as a reuse license; rights remain unknown. No manuscript image, OCR, transcription, or English translation is bundled, and the record does not increase reader coverage.

### TAU image-edition lead

TAU's 1894 Dillmann index exposes a separate Ethiopic Apocalypse of Esdras image edition through 14 numbered menu targets. The first target is an image page; the menu inventory is not a verification of chapter boundaries or completeness. TAU's site-wide notice allows noncommercial copying/distribution of digitized Ethiopic texts with the stated Ran HaCohen notice, but the archive does not bundle the images or transcribe them. This is a permission-limited external lead, not an offline reader or an increase in reader coverage.

## Separate historical English edition lead

HathiTrust catalogs Richard Laurence's 1820 edition as Ethiopic, English, and Latin, and links to a Harvard full-view copy. Google Books identifies the title as an Ethiopic version of Fourth Ezra in the Vulgate translated into Latin and English by Laurence. TAU says Laurence's English translation begins on page 199. This makes the edition a plausible English witness to the Ezra Sutuel / fourth-Esdras component by title-family, but its exact wording, chapter scope, textual relationship, and fit to the Church's intended text have not been checked. It is not bundled and adds no reader coverage; no global rights claim is made.

## Sources

- Church list, entry 15–16 and general note on Esdras: [SRC-029](https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en)
- TAU Ethiopic Ezra edition notes: [SRC-097](https://www.tau.ac.il/~hacohen/Ezra/Information.html)
- TAU Dillmann 1894 Apocryphi notes: [SRC-098](https://www.tau.ac.il/~hacohen/Apocryphi/Information.html)
- TAU Ethiopic Bible index and 14-target Apocalypse menu: [SRC-421](https://www.tau.ac.il/~hacohen/Biblia.html)
- British Library catalogue metadata: [SRC-200](https://searcharchives.bl.uk/catalog/040-002902239)
- British Library EAP digitized-item page and its access notice: [SRC-347](https://eap.bl.uk/archive-file/EAP286-1-1-499)
- HathiTrust edition catalog and full-view copy: [SRC-378](https://catalog.hathitrust.org/Record/009706619) · [full-view record](https://babel.hathitrust.org/cgi/pt?id=hvd.ah5jfu)
- Google Books edition metadata: [SRC-379](https://books.google.com/books/about/Primi_Ezr%C3%A6_libri.html?id=hcVCAAAAYAAJ)
- TAU's site-wide conditional reuse notice: [SRC-100](https://www.tau.ac.il/~hacohen/Information.html)
"""
    write_text_atomically(ROOT / "research" / "ezra-sutuel-source-review.md", review)
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(registry_path, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(canon_path, json.dumps(canon, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    build()
