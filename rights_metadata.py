"""Controlled rights categories used without replacing source-specific terms."""

VALID_RIGHTS_CLASSIFICATIONS = frozenset({
    "public_domain_claimed",
    "open_license",
    "permission_limited",
    "all_rights_reserved",
    "unknown",
    "mixed",
})


def same_source_identity(left: dict, right: dict) -> bool:
    """Compare a generated source's bibliographic fields while preserving its rights assessment."""
    rights_fields = {"rights_classification", "rights_status", "rights_basis"}
    return (
        {key: value for key, value in left.items() if key not in rights_fields}
        == {key: value for key, value in right.items() if key not in rights_fields}
    )


def validate_rights_classification(record: dict, label: str) -> None:
    """Require an explicit category and a machine-readable license for open content."""
    classification = record.get("rights_classification")
    if classification not in VALID_RIGHTS_CLASSIFICATIONS:
        raise ValueError(
            f"{label} needs one controlled rights_classification; "
            "use unknown when terms are not established."
        )
    if classification == "open_license":
        for field in ("license_id", "license_url"):
            value = record.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} claims an open license but has no {field}.")


def reader_rights_status(record: dict) -> str:
    """Explain a reader's existing rights notice without expanding its scope."""
    classification = record.get("rights_classification")
    if classification not in VALID_RIGHTS_CLASSIFICATIONS:
        raise ValueError("Cannot summarize reader rights without a controlled classification.")
    existing = record.get("rights_status")
    if isinstance(existing, str) and existing.strip():
        return existing
    notice = record.get("copyright_notice")
    commercial = record.get("commercial_use")
    if not isinstance(notice, str) or not notice.strip() or not isinstance(commercial, str) or not commercial.strip():
        raise ValueError(f"{record.get('reader_id', 'Reader')} cannot receive a rights summary without its item notice and commercial-use scope.")
    if classification == "public_domain_claimed":
        return (
            "This bundled reader is classified as public domain claimed based on its recorded source notice. "
            "The claim is not an independent determination for every jurisdiction. Item-specific notice: "
            f"{notice} Commercial-use and excluded-material scope: {commercial}"
        )
    if classification == "open_license":
        license_id = record.get("license_id")
        if not license_id:
            raise ValueError(f"{record.get('reader_id', 'Reader')} claims open rights without a license identifier.")
        return (
            f"This bundled reader is classified under {license_id}. Follow the item-specific notice and obligations: "
            f"{notice} Commercial-use scope: {commercial} This applies only to the selected reader layer, not excluded media or other site material."
        )
    if classification == "permission_limited":
        return (
            "Reuse of this bundled reader is limited to the stated permission; no open or broader license is inferred. "
            f"Item-specific notice: {notice} Commercial-use and other-use boundary: {commercial}"
        )
    if classification == "all_rights_reserved":
        return f"This bundled reader is classified all rights reserved. Item-specific notice: {notice} Commercial-use scope: {commercial}"
    if classification == "mixed":
        return f"This bundled reader has mixed or unresolved rights terms. Item-specific notice: {notice} Commercial-use scope: {commercial}"
    return f"Reuse rights for this bundled reader are unknown or not established. Item-specific notice: {notice} Commercial-use scope: {commercial}"
