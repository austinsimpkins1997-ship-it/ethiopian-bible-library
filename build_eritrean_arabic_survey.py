"""Record bounded Arabic scripture discovery for the Eritrea country profile."""
from __future__ import annotations

from copy import deepcopy

SURVEY_DATE = "2026-10-25"

SOURCES = [
    {
        "source_id": "SRC-322",
        "source_name": "eBible.org — scripture versions listed for Eritrea (territory filter)",
        "url": "https://ebible.org/bible/country.php?c=ER",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. The Eritrea-filtered territory catalogue displays three Arabic entries: "
            "Arabic Van Dyck Bible, WBTC Arabic Bible, and New Arabic Version (Book of Life). The rows label these "
            "as Arabic or Arabic, Standard; they do not identify an Eritrean-specific translation or establish "
            "which Arabic-speaking community uses each edition. The count is limited to Arabic-labeled rows on this "
            "provider's Eritrea page."
        ),
        "archive_status": "Provider territory catalogue inspected; discovery metadata only, no text copied or bundled",
    },
    {
        "source_id": "SRC-323",
        "source_name": "eBible.org — Arabic Van Dyck Bible edition record",
        "url": "https://ebible.org/bible/details.php?id=arb-vd",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. The provider labels the text Arabic [arb], dialect standard, and calls it the "
            "Arabic Van Dyck Bible. The provider states public-domain status and credits the Syrian Mission and "
            "American Bible Society. This is provider metadata, not proof of an Eritrean edition or independent "
            "rights advice; no text was copied."
        ),
        "archive_status": "Standard-Arabic edition discovery record; provider-stated public domain, not bundled",
    },
    {
        "source_id": "SRC-324",
        "source_name": "eBible.org — WBTC Arabic Easy Reading Version edition record",
        "url": "https://ebible.org/bible/details.php?id=arbwbtc",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. The provider labels the edition Arabic [arb], Standard, and identifies World "
            "Bible Translation Center copyright (2007). Its notice permits limited quotation under stated terms and "
            "requires written permission for larger uses; it is not an open license to republish the complete text. "
            "No text was copied."
        ),
        "archive_status": "Standard-Arabic edition discovery record; copyright and quotation limits recorded, not bundled",
    },
    {
        "source_id": "SRC-325",
        "source_name": "eBible.org — Biblica Open New Arabic Version edition record",
        "url": "https://ebible.org/bible/details.php?id=arbnav",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. The provider labels the edition Arabic, Standard [arb], dates the version "
            "2012, and reproduces a CC BY-SA 4.0 notice with separate Biblica trademark conditions. These are the "
            "provider's stated terms; before redistributing this text, assess the notice and trademark conditions "
            "for the proposed use. No text was copied."
        ),
        "archive_status": "Standard-Arabic edition discovery record; provider-stated CC BY-SA 4.0 with trademark conditions, not bundled",
    },
    {
        "source_id": "SRC-326",
        "source_name": "Joshua Project — Eritrea country language and scripture-status tables",
        "url": "https://joshuaproject.net/countries/er",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. The country page separately lists Arabic, Hijazi (acw), Arabic, Levantine "
            "(apc), Arabic, Sudanese (apd), and Arabic, Ta'izzi-Adeni (acq) among primary-language categories for "
            "people groups associated with Eritrea; its table reports differing scripture-status labels. Joshua "
            "Project says its data combines diverse sources with varying methods and describes estimates as ballpark. "
            "This is secondary discovery evidence, not a census, direct inspection of the translations, or proof that "
            "the standard-Arabic versions in SRC-322 serve these communities."
        ),
        "archive_status": "Secondary, composite people-group/language discovery evidence; estimates and scripture statuses require independent confirmation",
    },
    {
        "source_id": "SRC-327",
        "source_name": "Joshua Project — Arabic, Hijazi language resource profile",
        "url": "https://joshuaproject.net/languages/acw",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. Joshua Project identifies the language code as acw, lists a Bible-Portions "
            "status dated 2024, and associates Rashaida with Eritrea. Its profile describes its data as sourced from "
            "multiple organizations and warns that population/map estimates are approximate. It provides discovery "
            "links rather than the underlying scripture text; exact portion, edition, rights, and local use were not "
            "verified."
        ),
        "archive_status": "Secondary Arabic-variety discovery lead; source text, precise coverage, and reuse rights unverified",
    },
    {
        "source_id": "SRC-328",
        "source_name": "Glottolog 5.3 — Hijazi Arabic language profile",
        "url": "https://glottolog.org/resource/languoid/id/hija1235",
        "inspection_and_limitations": (
            f"Inspected {SURVEY_DATE}. Glottolog identifies Hijazi Arabic (ISO 639-3 acw; Glottocode hija1235) and "
            "lists Saudi Arabia and Yemen under Countries; it does not list Eritrea on this profile. This differs in "
            "scope from Joshua Project's association of the Rashaida in Eritrea with Arabic, Hijazi. The archive "
            "preserves the discrepancy as unresolved rather than inferring that the people-group mapping is a "
            "linguistic consensus. Glottolog's language classification does not establish scripture availability."
        ),
        "archive_status": "Language-classification source; country attribution discrepancy with Joshua Project remains unresolved",
    },
]

SURVEY = {
    "status": "completed",
    "scope": (
        "Inspected eBible.org's Eritrea-filtered territory catalogue and the three Arabic edition records it links: "
        "Van Dyck, WBTC Easy Reading Version, and Biblica Open New Arabic Version. The result_count of three is "
        "the number of Arabic-labeled edition rows on that one country-filtered catalogue, not a count of "
        "Eritrean-specific translations, Arabic varieties, or all scripture resources. All three edition records "
        "identify standard Arabic [arb], not a distinct Eritrean Arabic witness. Separate Joshua Project country and "
        "language-profile pages report Arabic varieties associated with Eritrean people groups, including Hijazi "
        "Arabic [acw] and a Bible-Portions status; this is secondary composite discovery data, not direct text "
        "verification or a crosswalk to the three standard-Arabic editions. Glottolog lists Hijazi Arabic's countries "
        "as Saudi Arabia and Yemen, while Joshua Project associates Rashaida in Eritrea with that code; the "
        "discrepancy remains unresolved. The survey is bounded to these cited "
        "pages; it is not a census or rights/completeness/accuracy review."
    ),
    "searched_at": SURVEY_DATE,
    "result": "records_found",
    "result_count": 3,
    "source_ids": ["SRC-322", "SRC-323", "SRC-324", "SRC-325", "SRC-326", "SRC-327", "SRC-328"],
    "notes": (
        "The profile label Arabic (Eritrea) is country-context metadata under the general BCP 47 Arabic tag [ar], "
        "not a claim that Eritrea has one distinct Arabic language or that standard-Arabic editions are local "
        "community translations. The eBible.org catalogue's country filter establishes that its listed versions "
        "are offered in its Eritrea index, not their adoption, accessibility, or ecclesial status in Eritrea. The "
        "three editions have different reuse notices; none is bundled here. Joshua Project's Hijazi entry is "
        "retained as a separate, secondary discovery lead; its reported portions were not obtained or audited. "
        "Glottolog's Hijazi Arabic profile does not list Eritrea, so the Eritrea association remains unresolved "
        "between these sources and is not adopted as settled language geography."
    ),
}


def apply(archive: dict) -> None:
    """Idempotently add source notes and complete the bounded profile survey."""
    sources = archive.setdefault("sources", [])
    by_id = {source.get("source_id"): source for source in sources}
    for source in SOURCES:
        by_id[source["source_id"]] = deepcopy(source)
    archive["sources"] = list(by_id.values())

    registry = archive.setdefault("translation_registry", {})
    languages = registry.get("languages", [])
    arabic = next((item for item in languages if item.get("language_tag") == "ar"), None)
    if arabic is None:
        raise ValueError("Arabic [ar] country-context language profile is required before applying its survey.")
    arabic["source_ids"] = sorted(set(arabic.get("source_ids", [])) | set(SURVEY["source_ids"]))
    arabic["availability_survey"] = deepcopy(SURVEY)
    arabic["script_profile_note"] = (
        "Arabic [ar] in this registry is country-context metadata for Eritrea and uses Arabic script (Arab). "
        "The bounded eBible.org country listing contains three standard-Arabic editions; it does not identify an "
        "Eritrean-specific translation or prove which communities use them. Separate Arabic varieties and their "
        "reported scripture statuses remain distinct, secondary discovery leads."
    )
