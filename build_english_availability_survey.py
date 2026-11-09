"""Record a bounded English-availability survey from three provider catalogues."""
from __future__ import annotations

from copy import deepcopy

SURVEY_DATE = "2026-10-25"

SOURCES = [
    {
        "source_id": "SRC-319",
        "source_name": "STEP Bible — available versions catalogue, English section",
        "url": "https://www.stepbible.org/versions.jsp",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. The provider catalogue has an English section listing multiple named text versions, "
            "including historical, modern, public-domain-claimed, and copyright-noted editions. The listing establishes "
            "English version availability in this catalogue only; it is not an audited edition inventory or a text, "
            "accuracy, completeness, or rights review."
        ),
        "archive_status": "Provider catalogue inspected for the bounded English availability survey; no text copied or bundled from this page",
    },
    {
        "source_id": "SRC-320",
        "source_name": "Bible.com — English-language versions listing",
        "url": "https://www.bible.com/languages/eng",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. The provider's English-language listing displays numerous English Bible editions "
            "and attributes versions to different publishers. It is a dynamic discovery page, not a stable census, "
            "edition audit, text-completeness review, or reuse-rights grant."
        ),
        "archive_status": "Provider catalogue inspected for the bounded English availability survey; no text copied or bundled from this page",
    },
    {
        "source_id": "SRC-321",
        "source_name": "eBible.org — World English Bible edition record",
        "url": "https://ebible.org/bible/details.php?id=engwebp",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. eBible.org identifies the World English Bible as modern English and offers "
            "multiple downloadable formats. The provider describes this edition as public domain; that statement is "
            "attributed to the provider and is not a legal opinion. This edition omits the Deuterocanon/Apocrypha, "
            "so its listing does not establish coverage of the Ethiopian Church list."
        ),
        "archive_status": "Edition discovery record; provider states public-domain status, but no WEB text was copied or bundled in this survey",
    },
]

SURVEY = {
    "status": "completed",
    "scope": (
        "Inspected three named online provider catalogue pages: STEP Bible's English version section, Bible.com's "
        "English-language versions listing, and eBible.org's World English Bible edition record. All three expose "
        "English Bible text/version availability. result_count is the number of provider pages inspected (3), not the "
        "number of distinct translations, books, complete Bibles, or all English scripture resources. This bounded "
        "survey is not a global or exhaustive census, text audit, chapter-boundary audit, or canon crosswalk."
    ),
    "searched_at": SURVEY_DATE,
    "result": "records_found",
    "result_count": 3,
    "source_ids": ["SRC-319", "SRC-320", "SRC-321"],
    "notes": (
        "English text resources are also bundled elsewhere in this archive, including Brenton's 1851 English "
        "translation of the Greek Septuagint; that witness is not translated from the accompanying Geʽez texts, "
        "and matching labels do not prove alignment. The three catalogue pages do not establish identical scope, "
        "translation basis, canon, reuse permission, accuracy, or completeness. Only eBible.org's provider-stated "
        "World English Bible public-domain status is observed here; it is not adopted as a rights determination for "
        "other versions. Other providers and editions have not been surveyed."
    ),
}


def apply(archive: dict) -> None:
    """Update the in-memory archive idempotently during the standalone build."""
    sources = archive.setdefault("sources", [])
    by_id = {source.get("source_id"): source for source in sources}
    for source in SOURCES:
        by_id[source["source_id"]] = deepcopy(source)
    archive["sources"] = list(by_id.values())

    registry = archive.setdefault("translation_registry", {})
    languages = registry.get("languages", [])
    english = next((item for item in languages if item.get("language_tag") == "en"), None)
    if english is None:
        raise ValueError("English language profile is required before applying its availability survey.")
    english["source_ids"] = sorted(set(english.get("source_ids", [])) | set(SURVEY["source_ids"]))
    english["availability_survey"] = deepcopy(SURVEY)
