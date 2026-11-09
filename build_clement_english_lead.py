"""Record a bibliographic lead for the English Book of Clement; bundle no text."""
from __future__ import annotations

import json
from pathlib import Path

from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-381"
PROJECT_SOURCE_ID = "SRC-382"
PUBLISHER_SCOPE_SOURCE_ID = "SRC-383"
BETA_WORK_SOURCE_ID = "SRC-424"
CANON_ID = "eotc-nt-34"
CATALOGUE_ID = "eotc-088"
EDITION_ID = "lumpkin-ethiopic-clement-english-2024"
PRODUCT_URL = "https://www.amazon.com/Book-Clement-Ethiopian-Bible-Translation/dp/1958450154"
PROJECT_URL = "https://ethiopianorthodoxbible.wordpress.com/2024/08/25/beware-of-complete-and-81-book-ethiopian-bibles-in-english/"
PUBLISHER_SCOPE_URL = "https://www.fifthestatepub.com/post/ethiopian-bible-81-books-explained"
BETA_WORK_URL = "https://raw.githubusercontent.com/BetaMasaheft/Works/330a89d34e4088d2eaabb5b87101dbf054457166/1001-2000/LIT1957Mashaf.xml"
CHURCH_URL = "https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en"


def _sort_source_ids(values: set[str]) -> list[str]:
    return sorted(values, key=lambda value: int(value.rsplit("-", 1)[1]))


def _append_once(value: str, addition: str) -> str:
    value = value.strip()
    return value if addition in value else f"{value} {addition}".strip()


def replace_generated_review_section(review: str, addition: str) -> str:
    """Replace all generated Clement review sections without duplicating them."""
    generated_start = "## Beta maṣāḥǝft work record (metadata and short incipits, not a reader)"
    legacy_start = "## English print-edition lead (not yet text-reviewed)"
    marker = generated_start if generated_start in review else legacy_start
    prefix = review.split(marker, 1)[0] if marker in review else review
    return f"{prefix.rstrip()}\n\n{addition.strip()}\n"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive.get("sources", [])}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Amazon bibliographic listing — Breandan Lumpkin, The Book of Clement from the Ethiopian Bible",
        "url": PRODUCT_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The retailer listing identifies Breandan Lumpkin as author, Fifth Estate, Incorporated as publisher, "
            "publication date 2024-12-05, English language, 236 pages, and ISBN 978-1958450154. The listing title/subtitle calls this "
            "‘The Book of Clement from the Ethiopian Bible’ and ‘The First English Translation of Peter’s Visions Given to Clement.’ "
            "This bibliographic record does not establish the Geʽez base witness, translation path, textual boundaries, completeness, accuracy, "
            "or equivalence with the scholarly Maṣḥafa Qalemǝnṭos (CAe 1957). Its contents and rights terms were not inspected; no text is copied."
        ),
        "archive_status": "English print-edition bibliographic lead; text, basis, completeness, quality, and reuse rights unreviewed; no text bundled",
        "rights_classification": "unknown",
        "rights_status": "Retail availability does not grant redistribution rights. No open license or reuse permission was identified in the inspected listing; no text is bundled.",
    }
    sources[PROJECT_SOURCE_ID] = {
        "source_id": PROJECT_SOURCE_ID,
        "source_name": "Ethiopian Orthodox Bible Project — English-availability statement for Ethiopic Clement",
        "url": PROJECT_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-26. This independent project page calls the item ‘The Book of Clement (Ethiopic Version in English),’ says an English "
            "translation is available for purchase, and cautions that Ethiopic Clement is not 1 Clement. It links to the retailer record captured as "
            "SRC-381. The page does not identify the translator or state the source witness, textual scope, translation path, completeness, accuracy, or "
            "reuse rights for that edition. Its identification with Maṣḥafa Qalemǝnṭos (CAe 1957) and the Church-list label remains a secondary claim "
            "requiring examination of the book itself. No text is copied."
        ),
        "archive_status": "Secondary English-availability statement; bibliographic lead only; edition text and rights unreviewed; no text bundled",
        "rights_classification": "unknown",
        "rights_status": "The page states that the project’s website content is copyrighted; it does not grant rights in the linked book or scripture text. No text is copied.",
    }
    sources[PUBLISHER_SCOPE_SOURCE_ID] = {
        "source_id": PUBLISHER_SCOPE_SOURCE_ID,
        "source_name": "Fifth Estate Publishing — scope note for announced revised Book of Clement reader edition",
        "url": PUBLISHER_SCOPE_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The publisher's article describes Breandan Lumpkin's revised reader edition as ‘coming soon’ and reports a "
            "12-chapter editorial arrangement: chapters 1–5 correspond to manuscript Book I, 6–7 to Book II, 8–10 to Book III, and 11 to Book IV. "
            "It says chapter 12 follows a short summary of Books V and VII, while the complete translation of Books V–VII lies outside that edition. "
            "The article's wording is internally uneven about the summarized book range; this record preserves rather than repairs it. These are the "
            "publisher's descriptions of an announced revised edition, not a collation of its text, proof that it was published, or evidence for the "
            "contents of the distinct 2024 print edition. Chapter mapping is editorial and does not establish Geʽez manuscript boundaries. No text copied."
        ),
        "archive_status": "Publisher-described forthcoming edition and partial scope; release and text not inspected; no text bundled",
        "rights_classification": "unknown",
        "rights_status": "The publisher article grants no reuse right in the announced edition or underlying scripture. No text is copied or bundled.",
    }
    sources[BETA_WORK_SOURCE_ID] = {
        "source_id": BETA_WORK_SOURCE_ID,
        "source_name": "Beta maṣāḥǝft Works — LIT1957Mashaf TEI record for Maṣḥafa Qalemǝnṭos (CAe 1957)",
        "url": BETA_WORK_URL,
        "local_metadata_url": "readers/source/clement-betamasaheft/capture-manifest.json",
        "local_review_url": "research/clement-source-review.md",
        "inspection_and_limitations": (
            "Inspected 2026-10-27 from a commit-pinned GitHub raw TEI file (commit 330a89d34e4088d2eaabb5b87101dbf054457166; "
            "16,865 bytes; SHA-256 db5f90e9b78079a7befae9a7a081ec72c10c1bedfaef79ef847d3f466796dd6e). Its title statement gives Geʽez, "
            "normalized, and English title forms for Maṣḥafa Qalemǝnṭos / Book of Clement. The TEI text section has an introduction, seven "
            "numbered Book divisions, and short Geʽez incipit divisions; no chapter/verse hierarchy or continuous full book text was found. "
            "The file itself states CC BY-SA 4.0. Beta maṣāḥǝft's current Guidelines state CC BY-NC-SA 4.0 for project data/remixes, while "
            "the University of Hamburg dataset record carries dataset-level CC BY 4.0 metadata and defers to file-level notices. Because the "
            "terms differ and no text is bundled, reuse of the transcription remains unresolved. The work record identifies CAe 1957; it does "
            "not prove identity with the exact Church-list entry. See local metadata-only capture and review."
        ),
        "archive_status": "Pinned work record and short incipit metadata; not a full reader; Church-list crosswalk uncertain; conflicting reuse notices; no text bundled",
        "rights_classification": "mixed",
        "rights_status": (
            "The pinned TEI file states CC BY-SA 4.0; current project Guidelines state CC BY-NC-SA 4.0 for project data/remixes, and the dataset-level "
            "repository record states CC BY 4.0 while pointing to file-specific terms. The applicable terms for reuse of this TEI and its Ethiopic excerpts "
            "are unresolved. No scripture text is bundled."
        ),
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].rsplit("-", 1)[1]))

    canon_path = ROOT / "canon-registry.json"
    canon = json.loads(canon_path.read_text(encoding="utf-8"))
    book = next(item for item in canon["books"] if item["canon_id"] == CANON_ID)
    book["source_ids"] = _sort_source_ids(
        set(book.get("source_ids", [])) | {SOURCE_ID, PROJECT_SOURCE_ID, PUBLISHER_SCOPE_SOURCE_ID, BETA_WORK_SOURCE_ID}
    )
    book["reader_status"] = (
        "No canon-linked reader bundled. Bausi reports complementary French/Italian translations of the Ethiopic Maṣḥafa Qalemǝnṭos, with partial coverage "
        "(French books I–II and part of III plus excerpts elsewhere; Italian books III–VII); those texts are bibliographic reports, not files audited here (SRC-207). "
        "A 2024 English print-edition lead titled The Book of Clement from the Ethiopian Bible is identified, and the publisher describes a separate forthcoming "
        "revised reader edition as partial. The French, Italian, 2024 English, and announced revised editions are not merged. Their exact identity with the "
        "Church-list entry, edition text, source witness, boundaries, completeness, translation method, and accuracy have not been reviewed."
    )
    book["mapping_note"] = _append_once(
        book.get("mapping_note", ""),
        "A 2024 English print listing titled The Book of Clement from the Ethiopian Bible is a discovery lead (SRC-381). Its bibliographic title and a secondary project’s description as an Ethiopic English version do not independently establish that it translates Bausi’s Maṣḥafa Qalemǝnṭos (CAe 1957) or the exact work intended by this Church-list label. No text is bundled.",
    )
    book["mapping_note"] = _append_once(
        book["mapping_note"],
        "Fifth Estate separately describes a forthcoming revised reader edition with partial scope (SRC-383); this publisher statement concerns that announced revision and must not be transferred to the distinct 2024 print edition. Publication of the revised edition is unconfirmed.",
    )
    book["mapping_note"] = _append_once(
        book["mapping_note"],
        "Beta maṣāḥǝft's pinned CAe 1957 TEI record labels Maṣḥafa Qalemǝnṭos / Book of Clement and contains short Geʽez incipits, but no complete reader text. This supports a related-work discovery lead only; it does not establish the exact Church-list crosswalk. Reuse terms conflict across the file and project-level notices (SRC-424, SRC-296, SRC-297).",
    )
    book["reader_status"] = _append_once(
        book["reader_status"],
        "A pinned Beta maṣāḥǝft CAe 1957 TEI work record contains title metadata and short Geʽez incipits, not a complete reader text; its Church-list crosswalk is related-work evidence only and reuse terms remain mixed (SRC-424).",
    )
    write_text_atomically(canon_path, json.dumps(canon, ensure_ascii=False, indent=2) + "\n")

    row = next(item for item in archive["catalogue"] if item["catalogue_id"] == CATALOGUE_ID)
    row["evidence_source_ids"] = _sort_source_ids(
        set(row.get("evidence_source_ids", [])) | {SOURCE_ID, PROJECT_SOURCE_ID, PUBLISHER_SCOPE_SOURCE_ID, BETA_WORK_SOURCE_ID}
    )
    row["edition_or_translation"] = _append_once(
        row.get("edition_or_translation", ""),
        "A 2024 English print edition is bibliographically listed as The Book of Clement from the Ethiopian Bible, by Breandan Lumpkin (Fifth Estate, ISBN 978-1958450154). The Ethiopian Orthodox Bible Project calls it an English translation of Ethiopic Clement. Separately, the publisher describes a forthcoming revised reader edition with twelve modern chapters; its article says full Books V–VII lie outside that announced edition. Do not transfer this scope description to the distinct 2024 print edition. Neither edition has been inspected here for its exact Geʽez base, complete contents, translation method, accuracy, or equivalence with Maṣḥafa Qalemǝnṭos (CAe 1957). These are unbundled leads, not coverage.",
    )
    row["text_availability_status"] = _append_once(
        row.get("text_availability_status", ""),
        "A 2024 English print edition and a separately announced forthcoming revised reader edition are identified in retailer, secondary-project, and publisher metadata (SRC-381–SRC-383). The 2026 publisher article describes the announced edition as partial, with complete Books V–VII outside its scope; do not assume that this applies to the distinct 2024 edition. Neither book text was inspected or bundled; identity, boundaries, completeness, translation method, accuracy, publication status, and reuse rights remain unverified.",
    )
    row["rights_status"] = _append_once(
        row.get("rights_status", ""),
        "The English print listing grants no redistribution permission; rights for the edition and underlying text were not established. No text is bundled.",
    )
    row["verification_date"] = "2026-10-26"
    row["reviewer_notes"] = _append_once(
        row.get("reviewer_notes", ""),
        "SRC-381 records retailer bibliographic metadata; SRC-382 records the secondary Ethiopian Orthodox Bible Project’s English-availability claim; SRC-383 records Fifth Estate's announced revised-edition scope note. The publisher says complete Books V–VII fall outside that forthcoming edition, but this does not establish the 2024 edition's contents. These records identify acquisition/review leads, not independently verified translation quality, source witness, text boundaries, completeness, rights, publication, or exact crosswalk to CAe 1957 or the Church-list entry.",
    )
    archive["canon_registry"] = canon

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    lead = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": CANON_ID,
        "mapping_state": "uncertain",
        "title": "The Book of Clement from the Ethiopian Bible: The First English Translation of Peter’s Visions Given to Clement",
        "witness_type": "printed_edition",
        "language_tag": "en",
        "language_name": "English",
        "script_code": "Latn",
        "edition_statement": "Retail listing identifies Breandan Lumpkin as author, Fifth Estate, Incorporated as publisher, 2024-12-05 publication date, 236 pages, and ISBN 978-1958450154. The Ethiopian Orthodox Bible Project describes it as an English translation of Ethiopic Clement.",
        "scope_description": (
            "Metadata-only discovery lead for the 2024 print edition. The retailer title/subtitle and secondary-project description associate the "
            "volume with Ethiopic Clement, but the volume itself was not inspected. The Geʽez base witness, translation path, textual boundaries, "
            "completeness, and accuracy are not established. The publisher's separate 2026 article describes a forthcoming revised reader edition "
            "with a 12-chapter arrangement and says complete Books V–VII fall outside that announced edition; do not assume this description applies "
            "to the 2024 book. Its identification with the scholarly Maṣḥafa Qalemǝnṭos (CAe 1957), the Ethiopic Apocalypse of Peter, or the exact "
            "work intended by the Church-list ‘Book of Clement’ remains unverified. Do not conflate it with 1 Clement or the three Epistles of Clement. "
            "No text is bundled."
        ),
        "source_ids": [SOURCE_ID, PROJECT_SOURCE_ID, PUBLISHER_SCOPE_SOURCE_ID, "SRC-207", "SRC-029"],
        "text_bundled": False,
        "rights_status": "Retail availability is not a reuse grant. No open license or redistribution permission for the English translation or underlying text was identified; no text is bundled.",
        "rights_classification": "unknown",
        "review_status": "Retail and secondary-project metadata inspected. The English edition's text, Geʽez basis, translation path, contents, scope, completeness, accuracy, rights, and exact work/canon crosswalk remain unreviewed. This lead does not count as bundled reader coverage.",
    }
    leads = registry.setdefault("edition_leads", [])
    leads[:] = [item for item in leads if item.get("edition_id") != EDITION_ID]
    leads.append(lead)
    revised_lead = {
        "edition_id": "lumpkin-qalementos-revised-reader-announced-2026",
        "candidate_canon_id": CANON_ID,
        "mapping_state": "uncertain",
        "title": "The Book of Clement from the Ethiopian Bible, Revised Reader’s Edition (announced; publication unconfirmed)",
        "witness_type": "printed_edition",
        "language_tag": "en",
        "language_name": "English",
        "script_code": "Latn",
        "edition_statement": "Fifth Estate's 2026-10-26 article describes a revised reader edition as forthcoming and gives a 12-chapter editorial structure. Publication and bibliographic identifiers were not confirmed.",
        "scope_description": (
            "Metadata-only announced edition. The publisher maps modern chapters 1–5 to manuscript Book I, 6–7 to Book II, 8–10 to Book III, and "
            "11 to Book IV. It says chapter 12 follows a short summary of Books V and VII, and that the complete translation of Books V–VII lies "
            "outside the edition; the article's summarized-book wording is uneven and is preserved as reported. This is the publisher's description, "
            "not a checked text or a source-manuscript collation. The modern chapters are not established as Geʽez manuscript boundaries. The article "
            "does not establish the exact crosswalk to the Church-list entry or Bausi's CAe 1957 work. Publication is unconfirmed and no text is bundled."
        ),
        "source_ids": [PUBLISHER_SCOPE_SOURCE_ID, "SRC-207", "SRC-029"],
        "text_bundled": False,
        "rights_status": "The publisher article does not grant reuse permission for the announced edition or underlying scripture. Publication and rights are unverified; no text is bundled.",
        "rights_classification": "unknown",
        "review_status": "Publisher article inspected 2026-10-26. Its announcement and described partial editorial scope are recorded as publisher claims. No copy, published edition, source witness, translation method, full text, chapter boundaries, completeness, accuracy, or reuse terms were inspected.",
    }
    leads[:] = [item for item in leads if item.get("edition_id") != revised_lead["edition_id"]]
    leads.append(revised_lead)
    beta_lead_id = "betamasaheft-qalementos-cae1957-metadata"
    beta_lead = {
        "edition_id": beta_lead_id,
        "candidate_canon_id": CANON_ID,
        "mapping_state": "related_work",
        "title": "Maṣḥafa Qalemǝnṭos / Book of Clement — Beta maṣāḥǝft LIT1957Mashaf TEI work record",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "Commit-pinned Beta maṣāḥǝft Works TEI work record, file LIT1957Mashaf.xml, commit "
            "330a89d34e4088d2eaabb5b87101dbf054457166. Its title statement identifies the work as CAe 1957 and gives Geʽez, normalized, and English titles."
        ),
        "scope_description": (
            "Metadata and short text excerpts only: the TEI body contains an introduction, seven numbered Book divisions, and short Geʽez incipit divisions; "
            "no continuous, chaptered full-text reader is present in this file. This is a related-work lead for the Church-list ‘Book of Clement’; the exact "
            "crosswalk is uncertain. It is not conflated with 1 Clement, 2 Clement, other Clementine works, or the distinct Ethiopic Apocalypse of Peter (CAe 317)."
        ),
        "source_ids": [BETA_WORK_SOURCE_ID, "SRC-207", "SRC-029", "SRC-296", "SRC-297"],
        "text_bundled": False,
        "rights_status": (
            "No transcription is bundled. The pinned TEI file states CC BY-SA 4.0, while current project Guidelines state CC BY-NC-SA 4.0 for project data/remixes "
            "and the University of Hamburg dataset record gives dataset-level CC BY 4.0 metadata with file-specific terms. Applicable reuse terms remain unresolved."
        ),
        "rights_classification": "mixed",
        "review_status": (
            "The raw file at the pinned commit was fetched, its SHA-256 and byte length recorded, and its TEI title statement, text divisions, and file-level license "
            "checked. The live Beta maṣāḥǝft page was unavailable during review; metadata derives from the pinned TEI file. The content is not a full text reader, "
            "and identity with the exact Church-list entry, completeness, and reuse permission remain unverified."
        ),
    }
    leads[:] = [item for item in leads if item.get("edition_id") != beta_lead_id]
    leads.append(beta_lead)
    write_text_atomically(registry_path, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    archive["translation_registry"] = registry
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    review_path = ROOT / "research" / "clement-source-review.md"
    review = review_path.read_text(encoding="utf-8")
    addition = f"""

## Beta maṣāḥǝft work record (metadata and short incipits, not a reader)

The commit-pinned [LIT1957Mashaf TEI record](https://github.com/BetaMasaheft/Works/blob/330a89d34e4088d2eaabb5b87101dbf054457166/1001-2000/LIT1957Mashaf.xml) identifies CAe 1957 with Geʽez, normalized, and English title forms for *Maṣḥafa Qalemǝnṭos / Book of Clement*. The file includes an introduction, seven numbered Book divisions, and short Geʽez incipit divisions; it has no chapter/verse hierarchy and is not a continuous full-text reader. A metadata-only capture record is retained [here](../readers/source/clement-betamasaheft/capture-manifest.json); the TEI text itself is not copied.

The file states CC BY-SA 4.0. Current Beta maṣāḥǝft Guidelines state CC BY-NC-SA 4.0 for project data/remixes, and the University of Hamburg's dataset-level record uses CC BY 4.0 with file-specific terms. Their relationship for this TEI's reuse is unresolved. The lead therefore remains metadata-only, rights-mixed, and separate from verified Church-list coverage. See sources SRC-424, SRC-296, and SRC-297.

## English print-edition lead (not yet text-reviewed)

The Ethiopian Orthodox Bible Project states that an English translation of “Ethiopic Clement” is available for purchase and explicitly warns readers not to confuse it with 1 Clement. Its statement identifies neither the translator nor the source witness in that page. [Project bibliography/claim]({PROJECT_URL})

The linked retailer listing identifies *The Book of Clement from the Ethiopian Bible: The First English Translation of Peter’s Visions Given to Clement*, author Breandan Lumpkin, publisher Fifth Estate, Incorporated, publication date 5 December 2024, 236 pages, ISBN 978-1958450154. These are retailer-supplied metadata; the book’s contents, source witness, translation path, boundaries, completeness, accuracy, and reuse terms were not inspected. [Retail bibliographic listing]({PRODUCT_URL})

This is an acquisition and review lead only. The title and secondary description do not prove that the 2024 volume translates the same Ethiopic work Bausi identifies as *Maṣḥafa Qalemǝnṭos* (CAe 1957), nor that it matches the Church list’s exact “Book of Clement” entry. A separate Fifth Estate article describes a forthcoming revised reader edition and says complete Books V–VII lie outside its scope; that is a publisher statement about the announced revised edition, not verified evidence about the 2024 print volume. The article says chapter 12 follows a short summary of Books V and VII, then refers to the full translation of V–VII being outside the edition; this wording is retained as an unresolved source inconsistency. [Publisher scope note]({PUBLISHER_SCOPE_URL}) No text is copied or bundled; rights remain unknown. The catalogue mapping stays uncertain and this lead does not increase bundled-reader coverage.

## Separately announced revised reader edition

Fifth Estate’s article says a revised reader edition is “coming soon” and outlines twelve modern chapters. It maps chapters 1–5 to manuscript Book I, chapters 6–7 to Book II, chapters 8–10 to Book III, and chapter 11 to Book IV. The publisher says chapter 12 follows a short summary of Books V and VII, while its next sentence says the complete translation of Books V–VII lies outside the edition. The scope note records that inconsistency as published and does not resolve it by inference. The article does not confirm publication, ISBN, source manuscript, accuracy, or reuse rights. These are editorial chapter divisions, not verified manuscript boundaries. [Fifth Estate article]({PUBLISHER_SCOPE_URL})
"""
    write_text_atomically(review_path, replace_generated_review_section(review, addition))


if __name__ == "__main__":
    build()
