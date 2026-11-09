"""Validation that declared reader unit counts match the bundled records."""


def validate_observed_unit_count(record: dict, count_field: str, label: str) -> int:
    """Require a declared generic unit count to equal units physically present in chapters."""
    declared = record.get(count_field)
    if isinstance(declared, bool) or not isinstance(declared, int) or declared < 0:
        raise ValueError(f"{label}.{count_field} must be a nonnegative integer.")
    chapters = record.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise ValueError(f"{label} has no chapter/unit inventory to count.")
    actual = 0
    for index, chapter in enumerate(chapters, start=1):
        units = (chapter.get("units", chapter.get("verses"))
                 if isinstance(chapter, dict) else None)
        if not isinstance(units, list) or not units:
            raise ValueError(f"{label} chapter {index} has no unit list to count.")
        actual += len(units)
    if declared != actual:
        raise ValueError(f"{label}.{count_field} declares {declared} units but {actual} are stored.")
    return actual
