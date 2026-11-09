"""Record source-bounded evidence for the Church-listed Tegsats entry."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "translation-registry.json"
CANON_ID = "eotc-ot-25"
CATALOGUE_ID = "eotc-030"
SOURCE_IDS = ["SRC-029", "SRC-101", "SRC-108", "SRC-205", "SRC-281", "SRC-385"]
CHURCH_URL = "https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en"
MIKRE_URL = "https://translation.bible/wp-content/uploads/2024/06/mikre-sellassie-1993-the-bible-and-its-canon-in-the-ethiopian-orthodox-church.pdf"
EA_URL = "https://en.sewasew.com/p/wisdom-books-biblical"
THESIS_URL = "https://ora.ox.ac.uk/objects/uuid%3Ae7c60bb3-3fc4-4b10-941f-8065617acbfa"
INDEX_URL = "https://israelite-biblical-canons.neocities.org/pages_for_biblical_texts/proverbs"
BL_URL = "https://searcharchives.bl.uk/catalog/032-003433717"
BL_VIEWER_URL = "https://iiif.bl.uk/uv/#?manifest=https://bl.digirati.io/iiif/ark:/81055/vdc_100132593851.0x000001"
BL_MANIFEST_URL = "https://bl.digirati.io/iiif/ark:/81055/vdc_100132593851.0x000001"
BL_MANIFEST_PATH = ROOT / "readers" / "source" / "tegsats-bl-add-ms-16186" / "iiif-manifest.json"
BL_CAPTURE_PATH = ROOT / "readers" / "source" / "tegsats-bl-add-ms-16186" / "capture-manifest.json"
BL_CAPTURE_RELATIVE = "readers/source/tegsats-bl-add-ms-16186/capture-manifest.json"
BL_MANIFEST_RELATIVE = "readers/source/tegsats-bl-add-ms-16186/iiif-manifest.json"
BL_MANIFEST_SHA256 = "dc8fee1a1fe2958e8f9f8384a5fd455f9a9e9e41b9d86d3c70695cb778a161ed"


def _sort_source_ids(values: set[str]) -> list[str]:
    return sorted(values, key=lambda value: int(value.rsplit("-", 1)[1]))


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    canon_path = ROOT / "canon-registry.json"
    canon = json.loads(canon_path.read_text(encoding="utf-8"))

    source_map = {item["source_id"]: item for item in archive["sources"]}
    missing = (set(SOURCE_IDS) - {"SRC-385"}) - set(source_map)
    if missing:
        raise ValueError(f"Tegsats review depends on missing source records: {sorted(missing)}")

    if not BL_MANIFEST_PATH.is_file() or not BL_CAPTURE_PATH.is_file():
        raise ValueError("The retained British Library IIIF manifest and capture record are required.")
    manifest_bytes = BL_MANIFEST_PATH.read_bytes()
    capture = json.loads(BL_CAPTURE_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_bytes)
    if (hashlib.sha256(manifest_bytes).hexdigest() != BL_MANIFEST_SHA256
            or capture.get("sha256") != BL_MANIFEST_SHA256
            or capture.get("bytes") != len(manifest_bytes)
            or capture.get("source_url") != BL_MANIFEST_URL
            or manifest.get("type") != "Manifest"
            or manifest.get("rights") not in (None, "")
            or manifest.get("label", {}).get("en") != ["Add MS 16186"]):
        raise ValueError("The British Library IIIF manifest identity or checksum does not match the retained capture record.")
    canvas_labels = ["".join(item.get("label", {}).get("en", [])) for item in manifest.get("items", [])]
    expected_folios = ["f.22r", "f.22v", "f.23r", "f.24r", "f.25r", "f.26r", "f.26v"]
    if len(canvas_labels) != 159 or any(label not in canvas_labels for label in expected_folios):
        raise ValueError("The British Library IIIF manifest no longer contains the recorded 159 canvas/folio inventory.")

    source_map["SRC-385"] = {
        "source_id": "SRC-385",
        "source_name": "British Library Archives and Manuscripts — Add MS 16186 catalogue record",
        "url": BL_URL,
        "full_view_url": BL_VIEWER_URL,
        "local_metadata_url": BL_CAPTURE_RELATIVE,
        "local_review_url": "research/tegsats-source-review.md",
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The British Library catalog identifies Add MS 16186 as a Geez/Ethiopic parchment codex dated 1600–1699. "
            "Its scope field lists Proverbs 1–24 at folios 3r–22r and ‘Tagśāṣa Salomon’ at folios 22r–26rb, catalogued as corresponding to Proverbs 25–29. "
            "The catalog links a digitized-content viewer and states that access restrictions apply. Its usage statement says the Library believes "
            "the manuscripts are not in copyright under Ethiopian law, while asking users to respect their cultural significance; this is not treated "
            "as a specific reuse grant for manuscript images or extracted text. Separately, the catalog page footer says its text is © British Library Board "
            "and available under CC BY except where otherwise stated; that license is recorded for catalog-page text, not presumed to cover manuscript images "
            "or an extracted transcription. The IIIF Presentation 3 manifest was captured locally (335,223 bytes; SHA-256 "
            f"{BL_MANIFEST_SHA256}) and contains 159 canvas records, including f.22r–f.26v. Its top-level rights field is present but blank; usage terms are embedded as "
            "metadata. Only the JSON manifest was captured: no canvas image bytes or manuscript text were fetched or bundled. This metadata does not prove image "
            "availability, complete book boundaries, or a verified crosswalk to the Church-listed Tegsats."
        ),
        "archive_status": "Metadata-only manuscript lead; CC BY catalogue text and 159-canvas IIIF metadata retained; manuscript image/text access and reuse remain unresolved; no text bundled",
    }

    # The 1993 article itself distinguishes the exact lists it reports and
    # gives the 25–31 Tegsas note in its printed p. 120, footnote 51.
    source_map["SRC-101"]["inspection_and_limitations"] = (
        "SAGE metadata identifies the peer-reviewed article by G.A. Mikre-Sellassie, The Bible Translator 44/1 (January 1993), pp. 111–123. "
        "The full article PDF was inspected. On printed p. 120, note 51 reports a five-part Solomon grouping in the Amharic commentary on Fetha Negest: "
        "Messale (Proverbs 1–24), Tegsas (Proverbs 25–31), Wisdom, Ecclesiastes, and Song of Songs. Printed pp. 120–122 distinguish broader and narrower historical canon lists and describe differing enumerations; this is an attributed historical scholarly account, not an official current ruling or an edition-level crosswalk to the Church's undated English list. "
        "The article is not bundled. The separately hosted PDF is at https://translation.bible/wp-content/uploads/2024/06/mikre-sellassie-1993-the-bible-and-its-canon-in-the-ethiopian-orthodox-church.pdf."
    )

    source_map["SRC-108"]["inspection_and_limitations"] = (
        "Oxford Research Archive metadata identifies Hugh Pilkington's DPhil thesis, A critical edition of the Book of Proverbs in Ethiopic, "
        "awarded by Oxford in 1978, with two OCR PDF files and copyright metadata naming Pilkington (1978). The repository abstract states that "
        "Cambridge University Library Add. 1570 was the base text; 21 Ethiopic manuscripts and two printed sources were collated; and the base text "
        "was translated literally to retain Ethiopic idiosyncrasies. The abstract reports four textual traditions, mixed Greek and Hebraic features, "
        "and LXX-dependent chapter/verse structure. These are the thesis author's summary claims, not independently checked conclusions. A secondary "
        "index assigns a purported Book of Rebukes section to pp. 318–522, but the thesis PDFs and those pages have not been inspected here; exact "
        "Tegsats boundaries, text content, translation extent, and completeness are unverified. The repository lists copyright dated 1978 and no open "
        "license is recorded; no thesis text is copied. Inspected the repository abstract and item metadata 2026-10-26. DOI: 10.5287/ora-kzy5ayyad."
    )

    row = next(item for item in archive["catalogue"] if item["catalogue_id"] == CATALOGUE_ID)
    row.update({
        "display_name": "Tegsats (Reproof)",
        "alternate_names_or_notes": (
            "The Church list uses ‘Tegsats (Reproof).’ Mikre-Sellassie (1993, printed p. 120 n. 51) writes ‘Tegsas’; Encyclopaedia Aethiopica's ‘Wisdom Books, biblical’ entry uses ‘Tägíasä Sälomon.’ "
            "These are attributed source spellings, not a claim that every form denotes an identical witness."
        ),
        "canon_view": (
            "The Church's English list gives Proverbs and Tegsats (Reproof) separate numbered entries. Historical scholarship reports separate Solomon collections, but the exact present-day Church-list witness and boundaries are not established."
        ),
        "identity_status": (
            "Separately named by the Church list; related historical work boundaries differ between cited secondary sources and are not verified against a selected witness."
        ),
        "edition_or_translation": (
            "No reader edition selected. Oxford's abstract describes Hugh Pilkington's 1978 DPhil critical edition of Ethiopic Proverbs, based on Cambridge Add. 1570, collated against 21 Ethiopic manuscripts and two printed sources, with a literal English translation of the base text. A secondary index assigns a purported Reproof section to pp. 318–522; those pages and the thesis files have not been inspected, so its scope as this separate Church-list entry is unverified."
        ),
        "chapter_count": "Not established for this Church-list entry; cited historical sources disagree on the Proverbs range associated with Reproof.",
        "chapter_order_status": (
            "Mikre-Sellassie (1993, printed p. 120 n. 51) reports Proverbs 25–31; Encyclopaedia Aethiopica's ‘Wisdom Books, biblical’ entry reports Proverbs 25–29; British Library Add MS 16186 catalogs its Tagśāṣa Salomon section as corresponding to Proverbs 25–29. These are different kinds of evidence, and none is treated as verified boundaries for a specific current Church-list edition."
        ),
        "text_availability_status": (
            "No reader bundled. The British Library catalogs a Tagśāṣa Salomon section at folios 22r–26rb and a locally retained IIIF manifest lists 159 canvas records, including those folio labels. No manuscript images or scripture text were fetched, inspected, or transcribed. Pilkington's thesis abstract describes an English rendering of its Ethiopic Proverbs base text, but the thesis and purported Reproof section have not been inspected or reproduced; the section's relation to this entry remains unknown. Access and reuse terms for all thesis and manuscript text/images remain unresolved."
        ),
        "completeness_status": "Not assessed; no defined edition or witness has been selected and collated.",
        "rights_status": (
            "No text or images are bundled. Oxford metadata records Hugh Pilkington as copyright holder with a 1978 copyright date; no open license or thesis reuse permission is recorded. Rights for linked manuscript transcriptions have not been established. The British Library's Ethiopian-law statement and cultural-use guidance do not establish a specific reuse grant for Add MS 16186 images or extracted text."
        ),
        "verification_date": "2026-10-25",
        "reviewer_notes": (
            "The Church's undated English list names this separately from Proverbs. Mikre-Sellassie reports the Fetha Negest commentary's five Solomonic books and gives Messale as Prov. 1–24 and Tegsas as Prov. 25–31 (1993, printed p. 120 n. 51). Encyclopaedia Aethiopica reports Tägíasä Sälomon as Prov. 25–29. The British Library catalogs Tagśāṣa Salomon in Add MS 16186 at ff.22r–26rb, corresponding to Prov. 25–29. This manuscript catalog entry identifies a witness and an attributed range, not the complete Church-listed work. Oxford's thesis abstract reports a critical edition based on Cambridge Add. 1570, 21 Ethiopic manuscripts, and a literal English translation; it does not verify the secondary index's reported Reproof pages (318–522) as the Church-listed Tegsats text. The disagreement and evidence types remain explicit. No text is copied or counted as reader coverage."
        ),
        "source_id": "SRC-029",
        "catalogue_seed_url": CHURCH_URL,
        "evidence_source_ids": SOURCE_IDS,
    })

    book = next(item for item in canon["books"] if item["canon_id"] == CANON_ID)
    book["source_ids"] = _sort_source_ids(set(book.get("source_ids", [])) | set(SOURCE_IDS))
    book["mapping_note"] = (
        "The Church's numbered English list separately names Proverbs (24) and Tegsats (Reproof) (25). Mikre-Sellassie (1993, printed p. 120 n. 51) reports a historical Fetha Negest commentary grouping Messale as Proverbs 1–24 and Tegsas as 25–31; Encyclopaedia Aethiopica reports 25–29; British Library Add MS 16186 catalogs Tagśāṣa Salomon at ff.22r–26rb as corresponding to Proverbs 25–29. The manuscript record is a witness-level discovery lead, not proof of the full Church-list entry's boundaries or exact edition. No reader is bundled."
    )

    archive["sources"] = sorted(source_map.values(), key=lambda item: int(item["source_id"].rsplit("-", 1)[1]))
    archive["canon_registry"] = canon
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    edition_id = "bl-add-ms-16186-tagsasa-solomon"
    lead = {
        "edition_id": edition_id,
        "candidate_canon_id": CANON_ID,
        "mapping_state": "uncertain",
        "title": "Tagśāṣa Salomon — British Library Add MS 16186 manuscript lead",
        "witness_type": "manuscript",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": "British Library Add MS 16186, a Geʽez/Ethiopic parchment codex dated 1600–1699; the catalog lists Tagśāṣa Salomon at folios 22r–26rb and says it corresponds to Proverbs 25–29.",
        "scope_description": (
            "Metadata-only witness lead. The British Library catalog identifies a manuscript section under this title and folio range, but its leaves "
            "have not been inspected or transcribed here. The catalog's Proverbs 25–29 correspondence is a description of this witness, not proof of the "
            "complete Church-listed Tegsats work, its recension, or a contemporary edition crosswalk. Other cited sources report differing ranges. No text or images are bundled."
        ),
        "source_ids": ["SRC-029", "SRC-385"],
        "text_bundled": False,
        "rights_status": (
            "The British Library catalogue page states that its text is © British Library Board and available under CC BY except where otherwise stated. This applies "
            "to the catalogue text and is not presumed to license manuscript images or extracted scripture. The catalogue says access restrictions apply and that the "
            "Library believes Ethiopian manuscripts are not in copyright under Ethiopian law, while requesting culturally respectful image reuse. No specific reuse "
            "grant for this manuscript's images or extracted text is established here."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "The Church list, British Library catalog metadata, and checksum-pinned IIIF Presentation 3 manifest were inspected. The 335,223-byte manifest contains 159 "
            "canvas records, including f.22r–f.26v; this verifies metadata inventory only. Title, shelfmark, language/script, broad date, folio span, viewer link, "
            "catalogued Proverbs correspondence, and stated access/use limits are recorded. No image bytes or scripture text were fetched. Manuscript wording, full work "
            "boundaries, completeness, and exact Church-list identity remain unreviewed."
        ),
    }
    leads = registry.setdefault("edition_leads", [])
    leads[:] = [item for item in leads if item.get("edition_id") != edition_id]
    leads.append(lead)

    pilkington_id = "pilkington-tegsats-reproof-1978"
    pilkington = next((item for item in leads if item.get("edition_id") == pilkington_id), None)
    if pilkington is None:
        raise ValueError("The existing Pilkington Tegsats discovery lead is missing.")
    pilkington["scope_description"] = (
        "Oxford's thesis abstract describes a critical edition whose base text is Cambridge University Library Add. 1570, collated against "
        "21 Ethiopic manuscripts and two printed sources, with a literal English translation of the base text. A separate secondary index "
        "assigns an Ethiopic Book of Rebukes section to thesis pp. 318–522. The thesis PDFs and those pages remain uninspected; the index's "
        "page/section claim, chapter range, completeness, and relation to the Church-listed Tegsats are unverified; the thesis abstract alone does not verify that the thesis section is the Church-listed work. This is an edition lead, not bundled coverage."
    )
    pilkington["review_status"] = (
        "The Oxford repository record and abstract were inspected. They support the thesis identity, base manuscript, stated collation scope, and the author's report of a literal English rendering. "
        "The secondary-index pointer to pp. 318–522 is not independently confirmed in the thesis. Exact Tegsats boundaries, thesis text content, completeness, reuse terms, and Church-list identity remain unreviewed."
    )

    translation_id = "pilkington-proverbs-ethiopic-en-1978"
    translation = {
        "translation_id": translation_id,
        "canon_id": CANON_ID,
        "title": "Ethiopic Proverbs — Pilkington's literal English rendering in the 1978 critical edition",
        "mapping_state": "uncertain",
        "scope_description": (
            "Oxford's thesis abstract states that the Ethiopic base text was translated literally into English. The thesis is a critical edition of Proverbs; a secondary index assigns a purported Book of Rebukes section to pp. 318–522, but those pages have not been checked. It is unknown whether that section corresponds to the Church-list's separate Tegsats entry, and no completeness or wording claim is made."
        ),
        "language_tag": "en",
        "translator": "Hugh Pilkington",
        "edition": "A critical edition of the Book of Proverbs in Ethiopic (DPhil thesis, University of Oxford, 1978)",
        "translation_path": ["gez", "en"],
        "source_ids": ["SRC-029", "SRC-073", "SRC-101", "SRC-108", "SRC-205", "SRC-281"],
        "text_bundled": False,
        "rights_status": (
            "Oxford metadata names Hugh Pilkington as copyright holder and gives a 1978 copyright date. No open license or permission to reproduce the thesis translation is recorded; do not copy the text without establishing the applicable terms."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "The Oxford abstract reports a literal English translation of the Ethiopic base text; no translation passages were inspected. The claimed Reproof section and its page range come from a separate secondary index and have not been verified in the thesis. The English layer's extent, wording, translation accuracy, and match to the Church-list Tegsats entry remain unknown."
        ),
        "notes": (
            "This is a bibliographic lead for an English translation described within a copyrighted critical-edition thesis, not a bundled or reusable text. The translation path is stated as Geʽez-to-English from the thesis abstract's description of the Ethiopic base; intermediate editorial or translation steps were not examined."
        ),
    }
    translation_leads = registry.setdefault("translation_leads", [])
    translation_leads[:] = [item for item in translation_leads if item.get("translation_id") != translation_id]
    translation_leads.append(translation)
    archive["translation_registry"] = registry
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(canon_path, json.dumps(canon, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(REGISTRY_PATH, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")

    review = f"""# Tegsats (Reproof): source and boundary review

## What the sources support

- The Ethiopian Orthodox Tewahedo Church's undated English page lists Proverbs as Old Testament entry 24 and “Tegsats (Reproof)” as entry 25. That directly supports preserving them as separate list entries; it does not give either entry's chapter boundaries. [Church list]({CHURCH_URL})
- G.A. Mikre-Sellassie's 1993 article reports, in printed p. 120 note 51, five “books of Solomon” in an Amharic commentary on Fetha Negest: Messale (Proverbs 1–24), Tegsas (Proverbs 25–31), Wisdom, Ecclesiastes, and Song of Songs. The article discusses multiple historical canon lists; this passage is an attributed report, not an official contemporary ruling or a verified mapping to a particular edition. [Article PDF]({MIKRE_URL})
- The web-hosted *Encyclopaedia Aethiopica* entry “Wisdom Books, biblical” gives a different traditional division: Méssale 1–24 and Tägíasä Sälomon 25–29. This conflicts with the 1993 article's note and must remain visible as a source disagreement. [Encyclopaedia Aethiopica entry]({EA_URL})
- Oxford's thesis abstract says Hugh Pilkington's 1978 critical edition uses Cambridge Add. 1570 as its base, collates 21 Ethiopic manuscripts and two printed sources, and includes a literal English translation of the base text. It reports LXX-dependent chapter/verse structure and mixed Greek/Hebraic features; these are the thesis author's scholarly conclusions, not independently re-evaluated here. Oxford lists two OCR PDFs and copyright dated 1978. A separate reference index links “Ethiopic Book of Rebukes” to pp. 318–522, but the thesis files and those pages have not been inspected. The index is a discovery pointer, not proof that those pages represent the Church-list Tegsats entry. [Oxford thesis record]({THESIS_URL}) · [Secondary reference index]({INDEX_URL})
- The British Library catalogs Add MS 16186 as a Geʽez/Ethiopic parchment codex dated 1600–1699 and lists “Tagśāṣa Salomon” at folios 22r–26rb, corresponding in its catalog to Proverbs 25–29. The catalog page footer separately licenses its text under CC BY except where otherwise stated; this is not assumed to license manuscript images or extracted scripture. A 335,223-byte IIIF Presentation 3 manifest is stored locally with a checksum-pinned capture record. Its 159 canvas metadata includes f.22r–f.26v, but no image bytes or scripture text were fetched. Its top-level `rights` value is present but blank; the embedded usage statement does not resolve image access/reuse. [British Library record]({BL_URL}) · [digitized-content viewer]({BL_VIEWER_URL}) · [local IIIF manifest]({BL_MANIFEST_RELATIVE}) · [capture record]({BL_CAPTURE_RELATIVE})

## Archive treatment

The archive preserves the Church's exact entry title and list position. It does not assert that 25–29 or 25–31 is the definitive range for the complete Church-listed work. Add MS 16186's 25–29 range is attributed to its manuscript catalog record only. Oxford's abstract supports a literal English rendering within Pilkington's critical edition of Ethiopic Proverbs, but neither it nor the secondary index establishes that this English text is a translation of the separately listed Church-book Tegsats. The translation and thesis remain unbundled and copyright terms are unresolved. The catalogue-record text is CC BY as stated in the footer; rights and access for manuscript images and extracted scripture remain unresolved. The local IIIF file is metadata only. No witness text or images were copied, no chapter count or completeness is claimed, and the entry stays without a reader; the 81-entry list and canon-linked reader count do not change.
"""
    write_text_atomically(ROOT / "research" / "tegsats-source-review.md", review)


if __name__ == "__main__":
    build()
