"""Controlled rights categories used without replacing source-specific terms."""

VALID_RIGHTS_CLASSIFICATIONS = frozenset({
    "public_domain_claimed",
    "open_license",
    "permission_limited",
    "all_rights_reserved",
    "unknown",
    "mixed",
})


def validate_rights_classification(record: dict, label: str) -> None:
    """Require an explicit known category; detailed source terms remain separate."""
    classification = record.get("rights_classification")
    if classification not in VALID_RIGHTS_CLASSIFICATIONS:
        raise ValueError(
            f"{label} needs one controlled rights_classification; "
            "use unknown when terms are not established."
        )
