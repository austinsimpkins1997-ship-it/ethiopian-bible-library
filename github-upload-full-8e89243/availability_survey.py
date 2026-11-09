"""Validation rules for bounded language-availability survey metadata."""

from __future__ import annotations

from datetime import date
import re


def validate_availability_survey(
    survey: object,
    label: str = "availability_survey",
    known_source_ids: set[str] | None = None,
) -> None:
    """Require a bounded, dated, cited survey before recording an external zero."""
    if not isinstance(survey, dict):
        raise ValueError(f"{label} must be an object with an explicit status.")

    status = survey.get("status")
    if status not in {"not_surveyed", "in_progress", "completed"}:
        raise ValueError(f"{label}.status must be not_surveyed, in_progress, or completed.")

    scope = survey.get("scope")
    searched_at = survey.get("searched_at")
    result = survey.get("result")
    result_count = survey.get("result_count")
    sources = survey.get("source_ids", [])
    if not isinstance(sources, list) or any(not isinstance(source, str) for source in sources) or len(sources) != len(set(sources)):
        raise ValueError(f"{label}.source_ids must be a unique list.")
    if known_source_ids is not None and set(sources) - known_source_ids:
        raise ValueError(f"{label} refers to unknown source IDs: {sorted(set(sources) - known_source_ids)}")

    if status == "not_surveyed":
        if any(value is not None for value in (scope, searched_at, result, result_count)) or sources:
            raise ValueError(f"{label} cannot report survey scope or results while status is not_surveyed.")
        return

    if not isinstance(scope, str) or not scope.strip() or not sources:
        raise ValueError(f"{label} needs a bounded scope and cited source IDs once a survey starts.")
    if status == "in_progress":
        if any(value is not None for value in (searched_at, result, result_count)):
            raise ValueError(f"{label} cannot report a result before the survey is completed.")
        return

    if not isinstance(searched_at, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", searched_at):
        raise ValueError(f"{label} completed status needs searched_at in YYYY-MM-DD form.")
    try:
        date.fromisoformat(searched_at)
    except ValueError as exc:
        raise ValueError(f"{label}.searched_at must be a valid YYYY-MM-DD date.") from exc
    if result not in {"records_found", "none_found"}:
        raise ValueError(f"{label} completed status needs a result of records_found or none_found.")
    if isinstance(result_count, bool) or not isinstance(result_count, int) or result_count < 0:
        raise ValueError(f"{label}.result_count must be a nonnegative integer.")
    if result == "none_found" and result_count != 0:
        raise ValueError(f"{label} none_found result must have result_count 0.")
    if result == "records_found" and result_count == 0:
        raise ValueError(f"{label} records_found result must have a positive result_count.")
