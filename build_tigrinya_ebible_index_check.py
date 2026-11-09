"""Add a dated, bounded negative discovery check for Tigrinya on eBible.org."""

from __future__ import annotations

from rights_metadata import same_source_identity


SOURCE = {
    "source_id": "SRC-399",
    "source_name": "eBible.org — public Bible List and Study Text index (Tigrinya discovery check)",
    "url": "https://ebible.org/find/",
    "inspection_and_limitations": (
        "Inspected 2026-10-26. The public eBible.org Bible List and Study Text index were searched "
        "for the names ‘Tigrinya’ and ‘Tigre’; neither string appeared in the inspected index text. "
        "This is a bounded discovery check of two provider indexes, not proof that eBible.org has "
        "no Tigrinya scripture: alternate labels, unindexed material, or index omissions were not "
        "ruled out. No text was downloaded or copied."
    ),
    "archive_status": (
        "Two current provider indexes checked for discovery only; no matching entry found under "
        "the searched names. This does not establish global or provider-wide absence."
    ),
}


SCOPE_ADDENDUM = (
    "Also searched the eBible.org public Bible List and Study Text index for Tigrinya and Tigre. "
    "This provider-index check is discovery-only and is not treated as a complete catalogue survey."
)
NOTES_ADDENDUM = (
    " The eBible.org Bible List and Study Text index were also checked on 2026-10-26; searches "
    "for the names Tigrinya and Tigre returned no matching index text (SRC-399). This is a bounded "
    "negative finding only. It does not prove that no Tigrinya material exists at eBible.org or "
    "elsewhere; alternate names, unindexed files, and catalogue omissions remain possible. It adds "
    "no reader, text, or canon mapping."
)


def apply(archive: dict) -> None:
    """Add the bounded provider-index finding without changing edition coverage."""
    sources = archive.setdefault("sources", [])
    existing_source = next(
        (item for item in sources if item.get("source_id") == SOURCE["source_id"]), None
    )
    if existing_source is not None and not same_source_identity(existing_source, SOURCE):
        raise ValueError(f"Conflicting source record {SOURCE['source_id']}.")
    if existing_source is None:
        sources.append(dict(SOURCE))
        sources.sort(key=lambda item: item["source_id"])

    registry = archive.get("translation_registry", {})
    language = next(
        (item for item in registry.get("languages", []) if item.get("language_tag") == "ti"),
        None,
    )
    if language is None:
        raise ValueError("The Tigrinya language profile (ti) is missing.")
    survey = language.get("availability_survey")
    if not isinstance(survey, dict):
        raise ValueError("The Tigrinya availability survey is missing.")
    for field, addition in (("scope", SCOPE_ADDENDUM), ("notes", NOTES_ADDENDUM)):
        current = survey.get(field)
        if not isinstance(current, str) or not current.strip():
            raise ValueError(f"The Tigrinya availability survey needs {field} text.")
        if addition not in current:
            survey[field] = current.rstrip() + " " + addition
    source_ids = set(survey.get("source_ids", []))
    source_ids.add(SOURCE["source_id"])
    survey["source_ids"] = sorted(source_ids, key=lambda value: int(value.split("-")[1]))
