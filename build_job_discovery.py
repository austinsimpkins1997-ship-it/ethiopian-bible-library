"""Record a Geʽez Job source lead without copying text under conflicting notices."""

from __future__ import annotations

import json
from archive_manifest import write_text_atomically
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-283"
EDITION_ID = "betamasaheft-job-tei-l1688"
WORK_URL = "https://betamasaheft.awhamburg.de/works/LIT1688Job/main"
TEXT_URL = "https://betamasaheft.awhamburg.de/works/LIT1688Job/text"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Beta maṣāḥǝft — Book of Job (LIT1688Job) work and text records",
        "url": WORK_URL,
        "inspection_and_limitations": (
            "The Beta maṣāḥǝft work record identifies the Geʽez title ኢዮብ፡ (ʾIyob; Book of Job), "
            "normalized as Maṣḥāfa ʾIyob, and lists Pereira 1905 in its editions bibliography. It reports "
            "31 manuscript records containing this work; that catalogue count is not a census of Job "
            "witnesses or proof that this text matches an EOTC printed edition. The separate text view "
            "is available at the linked text URL. Its page says the file is licensed CC BY-SA 4.0, while "
            "the same page separately displays a CC BY-NC-SA 4.0 site notice. Their relationship and "
            "rights in the underlying edition or manuscripts are unresolved. No text or XML is copied. "
            "Inspected 2026-10-25."
        ),
        "archive_status": (
            "Geʽez title, bibliography, manuscript-catalogue count, and text-view lead recorded; "
            "text withheld because file/site license notices conflict and the exact Church-list crosswalk is unverified"
        ),
    }
    archive["sources"] = sorted(
        sources.values(), key=lambda item: int(item["source_id"].split("-")[1])
    )
    catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-022")
    catalogue["edition_or_translation"] = (
        "Pereira, Le livre de Job: version éthiopienne (1907 bibliographic lead); "
        "separate Beta maṣāḥǝft LIT1688Job Geʽez text-view lead; no reader bundled"
    )
    catalogue["text_availability_status"] = (
        "Geʽez text view identified at Beta maṣāḥǝft; not copied or bundled because file/site license notices conflict"
    )
    catalogue["rights_status"] = (
        "Mixed/conflicting notices: text page states file-level CC BY-SA 4.0 and separately displays site-level "
        "CC BY-NC-SA 4.0; relationship and underlying edition/manuscript rights unresolved"
    )
    catalogue["verification_date"] = "2026-10-25"
    catalogue["source_id"] = SOURCE_ID
    catalogue["evidence_source_ids"] = sorted(
        set(catalogue.get("evidence_source_ids", [])) | {"SRC-029", SOURCE_ID},
        key=lambda value: int(value.split("-")[1]),
    )
    catalogue["reviewer_notes"] = (
        "Beta maṣāḥǝft separately records the Geʽez work ኢዮብ፡ (ʾIyob) and provides a text view. "
        "Its work bibliography cites Pereira 1905, while existing national-library evidence dates the "
        "Pereira contribution in Patrologia Orientalis II to 1907; these references are retained as "
        "separate records pending reconciliation. The Beta text-page file-level CC BY-SA 4.0 statement "
        "conflicts with its site-level CC BY-NC-SA 4.0 notice. No text is copied under the archive's "
        "rights policy. The source title is a candidate for the Church-list Job entry, not proof of an "
        "exact EOTC edition, completeness, or wording accuracy."
    )
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[EDITION_ID] = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": "eotc-ot-22",
        "mapping_state": "uncertain",
        "title": "Book of Job (LIT1688Job), Beta maṣāḥǝft Geʽez text-view lead",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            f"Beta maṣāḥǝft work record {WORK_URL}; separate text view {TEXT_URL}. The work record "
            "lists Pereira 1905 in its editions bibliography. This is kept distinct from the national-library "
            "bibliography's Pereira 1907 record for Patrologia Orientalis II."
        ),
        "scope_description": (
            "The work record names ኢዮብ፡ (ʾIyob, Book of Job) in Geʽez and reports 31 manuscript records "
            "containing the work. This supports an uncertain title-level candidate for Church-list Job only; "
            "it does not identify a specific EOTC print exemplar, establish that the text view is complete, "
            "or reconcile its Pereira 1905 bibliography with the separately catalogued 1907 contribution. "
            "The text view is not copied."
        ),
        "source_ids": ["SRC-029", SOURCE_ID, "SRC-109", "SRC-111"],
        "text_bundled": False,
        "rights_status": (
            "Not cleared for redistribution: the text page says the file is CC BY-SA 4.0 and separately "
            "displays a CC BY-NC-SA 4.0 site notice. Their relationship and rights in the underlying edition "
            "or manuscript witnesses are unresolved. No text is copied."
        ),
        "rights_classification": "mixed",
        "review_status": (
            "Provider work and text-page metadata inspected; title/language, bibliography pointer, and "
            "reported manuscript-record count recorded. The text and TEI were not copied or structurally "
            "audited. Edition identity, completeness, textual accuracy, Church-list crosswalk, and reuse "
            "rights remain unresolved."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = (
        "# Job source review\n\n"
        f"The [Beta maṣāḥǝft work record]({WORK_URL}) identifies the Geʽez title ኢዮብ፡ "
        "(ʾIyob, Book of Job), normalized as Maṣḥāfa ʾIyob. It lists Pereira 1905 in the editions "
        "bibliography and reports 31 manuscript records containing the work. Its separate [text view]"
        f"({TEXT_URL}) is a discovery lead; the text was not copied or structurally audited.\n\n"
        "The text page states that the file is licensed CC BY-SA 4.0 and separately displays a site-level "
        "CC BY-NC-SA 4.0 notice. The relationship between these notices and rights in the underlying "
        "edition or manuscripts is unresolved. Under the archive's [content policy](../CONTENT-LICENSES.md), "
        "no wording or TEI is bundled until terms are clarified.\n\n"
        "This source is separate from the existing Pereira Job lead: Beta maṣāḥǝft cites Pereira 1905, "
        "while the Biblioteca Nacional de Portugal bibliography dates the Patrologia Orientalis II "
        "contribution to 1907. The entries are not assumed to describe an identical release. The shared "
        "title supports only an uncertain candidate link to Church-list Job; it does not establish the "
        "EOTC edition, scope, completeness, or accuracy.\n"
    )
    (ROOT / "research" / "job-source-review.md").write_text(report, encoding="utf-8")
    print("Recorded Beta Masaheft Job as an unbundled, rights-unresolved Ge'ez source lead.")


if __name__ == "__main__":
    build()
