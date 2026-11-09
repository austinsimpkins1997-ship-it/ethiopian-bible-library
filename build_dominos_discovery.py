"""Record provisional Dominos/Book-of-the-Covenant work leads, without copying text."""

from __future__ import annotations

import json
from archive_manifest import write_text_atomically
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EOB_SOURCE_ID = "SRC-286"
TD_SOURCE_ID = "SRC-287"
TDG_SOURCE_ID = "SRC-288"
TD_URL = "https://betamasaheft.awhamburg.de/works/LIT2461Testam/main"
TDG_URL = "https://betamasaheft.awhamburg.de/works/LIT2462Testam/main"
EOB_URL = "https://ethiopianorthodoxbible.wordpress.com/category/buy-eotc-books/"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[EOB_SOURCE_ID] = {
        "source_id": EOB_SOURCE_ID,
        "source_name": "Ethiopian Orthodox Bible Project — English editions of the two Dominos books",
        "url": EOB_URL,
        "inspection_and_limitations": (
            "The project page says its editions of the two books of Dominos (Covenant) use Cooper and Maclean for "
            "First Dominos, noting that their base manuscript is from the Syriac/Greek tradition, and M. R. James "
            "for Second Dominos, with notes it says match the Geʽez manuscript. This is the project's own secondary "
            "description of its published editions, not an independent examination of those books or proof that the "
            "Church-list labels map exactly to particular Beta maṣāḥǝft work records. No edition, text, or page image "
            "was copied. Inspected 2026-10-25."
        ),
        "archive_status": "Secondary bibliographic crosswalk lead; underlying editions and exact work alignment not examined",
    }
    sources[TD_SOURCE_ID] = {
        "source_id": TD_SOURCE_ID,
        "source_name": "Beta maṣāḥǝft — Testamentum Domini (CAe 2461)",
        "url": TD_URL,
        "inspection_and_limitations": (
            "The Beta maṣāḥǝft work record identifies the Geʽez title Kidān za-ʾǝgziʾǝna ʾIyasus Krǝstos, "
            "calls the work Testamentum Domini, describes it as a 60-chapter work divided into two parts, and lists "
            "a Beylot 1984 Ethiopic edition. This catalogued work is a plausible candidate for the first Book of "
            "Dominos based on the cited secondary crosswalk, but the exact Church-list mapping and edition equivalence "
            "are not verified here. The text and edition were not downloaded or copied. Inspected 2026-10-25."
        ),
        "archive_status": "Geʽez scholarly work-record candidate; no text bundled; exact Church-list mapping unverified",
    }
    sources[TDG_SOURCE_ID] = {
        "source_id": TDG_SOURCE_ID,
        "source_name": "Beta maṣāḥǝft — Testamentum Domini in Galilea (CAe 2462)",
        "url": TDG_URL,
        "inspection_and_limitations": (
            "The Beta maṣāḥǝft work record identifies the Geʽez title Kidān za-ʾǝgziʾǝna wa-madḫānina ʾIyasus "
            "Krǝstos and describes a composite work: an apocalypse of Jesus to the Apostles in Galilee (edition "
            "chapters 1–11) joined to the Epistula Apostolorum (chapters 12–62). It lists seven manuscript records. "
            "This work is a plausible candidate for the second Book of Dominos based on the cited secondary "
            "crosswalk, but the exact Church-list mapping and edition equivalence are not verified here. The text "
            "and edition were not downloaded or copied. Inspected 2026-10-25."
        ),
        "archive_status": "Composite Geʽez work-record candidate; no text bundled; exact Church-list mapping unverified",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))

    crosswalk_sources = ["SRC-029", "SRC-073", "SRC-211", EOB_SOURCE_ID, TD_SOURCE_ID, TDG_SOURCE_ID]
    for catalogue_id, canon_id, title, work_description, source_id in (
        (
            "eotc-086", "eotc-nt-32", "Testamentum Domini (CAe 2461)",
            "Beta maṣāḥǝft records the Geʽez Testamentum Domini (60 chapters, two parts; CAe 2461). A secondary "
            "Ethiopian Orthodox Bible Project page associates its First Dominos edition with the first Covenant book. "
            "Candidate crosswalk only; exact Church-list mapping and edition equivalence have not been checked.",
            TD_SOURCE_ID,
        ),
        (
            "eotc-087", "eotc-nt-33", "Testamentum Domini in Galilea (CAe 2462)",
            "Beta maṣāḥǝft records the Geʽez Testamentum Domini in Galilea (CAe 2462), a composite work containing "
            "an apocalypse in Galilee and the Epistula Apostolorum. A secondary Ethiopian Orthodox Bible Project "
            "page associates its Second Dominos edition with the second Covenant book. Candidate crosswalk only; "
            "exact Church-list mapping and edition equivalence have not been checked.",
            TDG_SOURCE_ID,
        ),
    ):
        catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == catalogue_id)
        catalogue.update({
            "alternate_names_or_notes": "The Ethiopian Orthodox Bible Project glosses this Church-list Dominos title as Book of the Covenant. Beta maṣāḥǝft work record proposed as a candidate; exact mapping remains uncertain.",
            "identity_status": "Provisional work-family candidate only; exact title-to-work crosswalk not verified",
            "edition_or_translation": title + "; " + work_description,
            "text_availability_status": "External bibliographic and scholarly work records identified; no reader text bundled",
            "completeness_status": "Not assessed against a Church-list edition or witness",
            "rights_status": "No text copied; rights and terms of the underlying editions not assessed",
            "verification_date": "2026-10-25",
            "source_id": source_id,
            "evidence_source_ids": crosswalk_sources,
            "reviewer_notes": (
                "The Church's numbered canon source supplies the entry; the Ethiopian Orthodox Bible Project "
                "provides a secondary Book-of-the-Covenant alias and describes English editions for the two Dominos "
                "books. Beta maṣāḥǝft records a plausible Geʽez work candidate. These sources support discovery, not "
                "a verified one-to-one crosswalk. Edition, text boundaries, completeness, and rights remain open."
            ),
        })

    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    common = {
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "source_ids": crosswalk_sources,
        "text_bundled": False,
        "rights_status": "No text copied or bundled; rights in the underlying edition and source metadata are not assessed here.",
        "rights_classification": "unknown",
        "review_status": "Bibliographic and scholarly work metadata reviewed. No text or edition was inspected or copied. Canon mapping, exact edition equivalence, completeness, and reuse rights remain unverified.",
    }
    leads["betamasaheft-testamentum-domini-cae2461"] = {
        **common,
        "edition_id": "betamasaheft-testamentum-domini-cae2461",
        "candidate_canon_id": "eotc-nt-32",
        "mapping_state": "uncertain",
        "title": "Testamentum Domini — Geʽez work record CAe 2461",
        "edition_statement": "Beta maṣāḥǝft records Kidān za-ʾǝgziʾǝna ʾIyasus Krǝstos / Testamentum Domini as a 60-chapter Geʽez work in two parts; Beylot 1984 is listed in its editions bibliography.",
        "scope_description": "Plausible work-family candidate for First Book of Dominos based on the Ethiopian Orthodox Bible Project's secondary edition description. The Church-list-to-work crosswalk and identity with any specific printed edition remain unverified.",
    }
    leads["betamasaheft-testamentum-domini-galilea-cae2462"] = {
        **common,
        "edition_id": "betamasaheft-testamentum-domini-galilea-cae2462",
        "candidate_canon_id": "eotc-nt-33",
        "mapping_state": "uncertain",
        "title": "Testamentum Domini in Galilea — Geʽez work record CAe 2462",
        "edition_statement": "Beta maṣāḥǝft records Kidān za-ʾǝgziʾǝna wa-madḫānina ʾIyasus Krǝstos / Testamentum Domini in Galilea as a composite Geʽez work; its description distinguishes chapters 1–11 from chapters 12–62 (Epistula Apostolorum).",
        "scope_description": "Plausible work-family candidate for Second Book of Dominos based on the Ethiopian Orthodox Bible Project's secondary edition description. Beta maṣāḥǝft describes a composite: a Galilee apocalypse (chapters 1–11) and the Epistula Apostolorum (chapters 12–62). The Church-list-to-work crosswalk and boundaries in any edition remain unverified.",
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = (
        "# Dominos source review\n\n"
        "## Evidence\n\n"
        "The [EOTC canon page](https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en) lists the "
        "first and second Books of Dominos. The [Ethiopian Orthodox Bible Project's canon page](https://ethiopianorthodoxbible.wordpress.com/ethiopian-orthodox-canon-of-scripture/) "
        "glosses these as Books of the Covenant I and II. The [Lexham Bible Dictionary](https://biblia.com/books/lbd/word/Book_of_the_Covenant%2C_Ethiopian?ssi=0) "
        "describes the Ethiopian Book of the Covenant as a two-book work and identifies the fuller title Testament of "
        "Our Lord Jesus Christ. Its separate [Sinodos contents entry](https://biblia.com/books/lbd/article/SINODOS%245FWRITING.CONTENTS) "
        "warns that manuscript contents vary.\n\n"
        f"Beta maṣāḥǝft records the Geʽez [Testamentum Domini, CAe 2461]({TD_URL}) as a 60-chapter work in two "
        f"parts, and separately catalogs [Testamentum Domini in Galilea, CAe 2462]({TDG_URL}) as a composite work "
        "with a Galilee apocalypse and the Epistula Apostolorum. The Ethiopian Orthodox Bible Project's [book-edition "
        f"note]({EOB_URL}) says its First Dominos edition uses Cooper and Maclean and its Second Dominos edition uses "
        "M. R. James; it asserts textual proximity to Geʽez but this archive has not checked that assertion against "
        "the editions or manuscripts.\n\n"
        "## Archive treatment\n\n"
        "The two Beta works are entered as uncertain candidate crosswalks for the two Church-list entries, preserving "
        "the distinction between a Geʽez work record and an exact canon mapping. No book text is bundled, translated, "
        "or counted as reader coverage. Edition identity, recension, internal boundaries, completeness, and reuse "
        "rights remain unverified. The broader *Maṣḥafa kidān* record CAe 1938 is not silently treated as either "
        "Dominos book because its catalogued contents (Kidān za-nagh and Kidān za-sark) are not these two complete "
        "works.\n"
    )
    (ROOT / "research" / "dominos-source-review.md").write_text(report, encoding="utf-8")
    print("Recorded two provisional Dominos work leads; no text bundled or canon mapping verified.")


if __name__ == "__main__":
    build()
