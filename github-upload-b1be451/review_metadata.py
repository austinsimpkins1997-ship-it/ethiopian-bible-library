"""Validation for bounded review records; automation is not human verification."""

VALID_REVIEW_METHODS = frozenset({
    "automated_validation",
    "source_inspection",
    "human_review",
    "scholarly_review",
    "community_review",
    "combined_source_and_automated_validation",
    "unknown",
})
HUMAN_REVIEW_METHODS = frozenset({"human_review", "scholarly_review", "community_review"})
AUTOMATED_METHODS = frozenset({"automated_validation", "combined_source_and_automated_validation"})


def validate_review_record(review: dict, label: str = "review record") -> None:
    method = review.get("review_method")
    state = review.get("state")
    if method not in VALID_REVIEW_METHODS:
        raise ValueError(f"{label} needs a controlled review_method; use unknown when the method is not established.")
    if method in AUTOMATED_METHODS and not review.get("review_process"):
        raise ValueError(f"{label} must identify the automated review process.")
    if method in AUTOMATED_METHODS and review.get("reviewer") is not None:
        raise ValueError(f"{label} must not identify an automated process as a human reviewer.")
    if state == "reviewed":
        if method not in HUMAN_REVIEW_METHODS or not review.get("reviewer") or not review.get("reviewed_at"):
            raise ValueError(f"{label} cannot mark automated or unattributed work as fully reviewed.")
