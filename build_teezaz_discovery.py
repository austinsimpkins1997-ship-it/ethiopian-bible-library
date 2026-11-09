"""Record source-backed Te'ezaz identification without bundling unverified text."""

from __future__ import annotations

import json
from pathlib import Path

from archive_manifest import write_text_atomically
from metadata_helpers import ensure_appended_note_once

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-441"
EDITION_ID = "tau-horner-teezaz-image-edition-1904"
CANON_ID = "eotc-nt-29"
CATALOGUE_ID = "eotc-083"

COWLEY_TEEZAZ_NOTE = (
    "Rechecked 2026-10-27 for the Te'ezaz lead: Cowley describes Sinodos as four apostolically "
    "attributed sections and says Te'ezaz is attested with 71 or 72 canons and was printed in "
    "Horner's 1904 Statutes (footnote 12). He also reports variable Sinodos manuscript contents "
    "and order. This is a secondary report, not a collation of Horner's edition or a ruling on "
    "the modern Church-list title."
)
ARCHIVE_STATUS_NOTE = (
    "also directly links the Te'ezaz section to Horner 1904 while reporting 71/72-canons variation"
)
HORNER_EDITION_NOTE = (
    "Cowley reports Te'ezaz as 71 or 72 canons and printed in Horner 1904; Mikre-Sellassie reports 71 and cites Horner. "
    "Horner's contents call printed pp. 127–232 'Translation of the Ethiopic' and begin 'Translation of the Arabic' at p. 233. "
    "These are translation-section locators in Horner's broader Statutes volume, not verified boundaries for the Church-list Tizaz entry. "
    "The Internet Archive scan is a separate English-language digitization and explicitly omits the Ethiopic and Arabic text witnesses."
)


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}

    # Preserve Cowley's existing source record while recording the relevant
    # passage actually inspected for this discovery lead.
    cowley = sources["SRC-210"]
    cowley["inspection_and_limitations"] = ensure_appended_note_once(
        cowley["inspection_and_limitations"], COWLEY_TEEZAZ_NOTE
    )
    cowley["archive_status"] = ensure_appended_note_once(
        cowley["archive_status"], ARCHIVE_STATUS_NOTE, separator="; "
    )

    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "G.A. Mikre-Sellassie, “The Bible and Its Canon in the Ethiopian Orthodox Church,” The Bible Translator 44, no. 1 (January 1993), pp. 111–123",
        "url": "https://translation.bible/wp-content/uploads/2024/06/mikre-sellassie-1993-the-bible-and-its-canon-in-the-ethiopian-orthodox-church.pdf",
        "inspection_and_limitations": (
            "Inspected 2026-10-27. At printed p. 120, Mikre-Sellassie describes Sinodos as four sections and "
            "reports Te'ezaz as containing 71 canons, citing G. Horner, The Statutes of the Apostles (1904), "
            "in footnote 47. This independently supports the section's title/count connection to Horner, but "
            "is secondary scholarship, not a direct Church ruling or manuscript collation. The article itself "
            "discusses broader/narrower canon lists and unresolved counting differences elsewhere; it must not "
            "be used to assert one universally settled canon form. No text copied."
        ),
        "archive_status": "Secondary scholarly source inspected for the Te'ezaz/Sinodos section count and Horner 1904 citation; not a text witness or Church ruling",
        "rights_classification": "unknown",
        "rights_status": "No article text is copied. Reuse terms for this hosted article and the cited Horner edition have not been assessed here; citation is not a reuse license.",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].rsplit("-", 1)[1]))

    catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == CATALOGUE_ID)
    catalogue["edition_or_translation"] = (
        "TAU-hosted Ge'ez page images labeled Te'ezaz (following Horner 1904); the linked Internet Archive Horner scan is a separate English-language digitization, not the Ge'ez witness"
    )
    catalogue["text_availability_status"] = (
        "No reader text is bundled. TAU's page-image edition is externally linked; its information page reports missing printed pages. "
        "The Horner Internet Archive scan omits the Ge'ez and Arabic texts but includes OCR for the English translation of the Ethiopic section; that broader translation section is not verified as the Church-list Tizaz text."
    )
    catalogue["completeness_status"] = (
        "Not verified. TAU reports that pages 5, 9, 17, 21, 25, 35, 41, 49, 53, 60, 70, and 71 seem missing in the print edition; "
        "no complete image/OCR collation or chapter-boundary audit has been done."
    )
    catalogue["rights_status"] = (
        "No text or images are bundled. Reuse terms for TAU images and the hosted article are unverified. Internet Archive labels the Horner item's "
        "possible copyright status NOT_IN_COPYRIGHT for the US region; that provider claim does not establish worldwide reuse rights."
    )
    catalogue["verification_date"] = "2026-10-27"
    catalogue["evidence_source_ids"] = sorted(
        set(catalogue.get("evidence_source_ids", [])) | {"SRC-029", "SRC-210", "SRC-211", "SRC-213", "SRC-368", SOURCE_ID},
        key=lambda value: int(value.rsplit("-", 1)[1]) if value.startswith("SRC-") else value,
    )
    catalogue["reviewer_notes"] = (
        "Cowley reports Te'ezaz as one of four apostolically attributed Sinodos sections, gives a count of 71 or 72 canons, "
        "and says it was printed in Horner 1904 (SRC-210). Mikre-Sellassie independently reports 71 canons and cites Horner "
        "(SRC-441). Horner's contents identify its English translation of the Ethiopic at printed pp. 127–232 and the Arabic translation beginning at p. 233; these are section locators in Horner's broader Statutes volume, not verified boundaries for Church-list Tizaz. The scan OCR includes headings for Statutes 71 and 72, but the full sequence has not been audited. The linked Internet Archive copy explicitly lacks the Ethiopic and Arabic text witnesses (SRC-368). "
        "TAU identifies its external page images as the Te'ezaz section following Horner and reports that printed pages 5, 9, 17, 21, 25, 35, 41, 49, 53, 60, 70, and 71 seem missing in that edition (SRC-213). This is TAU's warning about its hosted edition, not proof that those pages are absent from every witness. "
        "Horner's contents identify the English translation of the Ethiopic on pp. 127-232 and the Arabic translation from p. 233; this is a section boundary within Horner's volume, not a verified boundary for the Church-list Tizaz entry. "
        "These sources support a strong research association, but this is not an authoritative crosswalk: the modern Church-list spelling/gloss ‘Tizaz (the book of Herald)’ "
        "has not been reconciled against a Church text witness; manuscript contents vary, and the 71/72 count differs across reports. "
        "Keep the mapping provisional; no text, images, exact boundaries, or reuse permissions are asserted."
    )
    catalogue["source_id"] = "SRC-029"

    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    lead = next(item for item in registry["edition_leads"] if item.get("edition_id") == EDITION_ID)
    lead["source_ids"] = sorted(
        set(lead["source_ids"]) | {SOURCE_ID}, key=lambda value: int(value.rsplit("-", 1)[1])
    )
    lead["scope_description"] = catalogue["reviewer_notes"]
    lead["review_status"] = (
        "Rechecked 2026-10-27: TAU's information page identifies its hosted Ge'ez images as Te'ezaz and reports missing printed pages; "
        "Cowley reports Te'ezaz with 71 or 72 canons and links it to Horner 1904; Mikre-Sellassie reports 71 and cites Horner. "
        "Horner's contents identify an English translation of the Ethiopic at printed pp. 127-232 and Arabic from p. 233; this is a section boundary within the broader Statutes volume, not a verified Church-list Tizaz boundary. IA metadata says this separate English-language scan lacks the Ethiopic and Arabic text witnesses. The OCR contains headings for Statutes 71 and 72, but the full sequence has not been audited. These sources strengthen the work "
        "association but do not reconcile the Church-list gloss/spelling, manuscript variation, exact boundaries, missing pages, "
        "translation accuracy, completeness, or reuse rights. No text or images were copied or bundled."
    )
    lead["edition_statement"] = ensure_appended_note_once(
        lead["edition_statement"], HORNER_EDITION_NOTE
    )
    write_text_atomically(registry_path, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    print("Updated Te'ezaz provenance: corroborating scholarship recorded; text remains unbundled and mapping provisional.")


if __name__ == "__main__":
    build()
