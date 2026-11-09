"""Validate archive language subtags against its bundled IANA registry snapshot."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


SNAPSHOT_RELATIVE_PATH = Path("readers/source/authority/language-subtag-registry.txt")


def _verify_snapshot_hash(language_audit: dict, root: Path) -> str:
    """Ensure the cited authority snapshot is the exact retained file audited."""
    expected = language_audit.get("snapshot_sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise ValueError("IANA language-subtag audit must include the retained snapshot SHA-256.")
    path = root / SNAPSHOT_RELATIVE_PATH
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"IANA language-subtag snapshot SHA-256 mismatch: expected {expected}, found {actual}.")
    return actual


def parse_iana_language_subtags(path: Path) -> tuple[str, dict[str, list[dict[str, str]]]]:
    """Return File-Date and current language/extlang/script records keyed by Subtag."""
    text = path.read_text(encoding="utf-8")
    date_match = re.search(r"(?m)^File-Date:\s*(\d{4}-\d{2}-\d{2})\s*$", text)
    if not date_match:
        raise ValueError("Bundled IANA language registry has no valid File-Date.")

    current: dict[str, list[dict[str, str]]] = {}
    for block in text.split("%%"):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            if not line or line[0].isspace() or ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
        if fields.get("Type") not in {"language", "extlang", "script"}:
            continue
        subtag = fields.get("Subtag")
        if subtag and "Deprecated" not in fields:
            current.setdefault(subtag.lower(), []).append(fields)
    return date_match.group(1), current


def validate_language_subtag_audit(
    audit: dict,
    translation_registry: dict,
    root: Path,
    source_record: dict,
) -> set[str]:
    """Verify every audited and used language tag against the retained IANA snapshot."""
    language_audit = audit.get("language_subtags", {})
    codes = language_audit.get("codes", [])
    if not codes or len(codes) != len(set(codes)):
        raise ValueError("IANA language-subtag audit must contain a nonempty unique code list.")
    expected_date = language_audit.get("registry_file_date")
    snapshot = root / SNAPSHOT_RELATIVE_PATH
    _verify_snapshot_hash(language_audit, root)
    registry_date, registered = parse_iana_language_subtags(snapshot)
    if registry_date != expected_date:
        raise ValueError(
            f"IANA language audit date {expected_date!r} does not match bundled snapshot {registry_date!r}."
        )

    unresolved = [
        code for code in codes
        if not any(record.get("Type") in {"language", "extlang"} for record in registered.get(code.lower(), []))
    ]
    if unresolved:
        raise ValueError(f"Language subtags are absent or deprecated in the bundled IANA snapshot: {unresolved}")

    if source_record.get("local_metadata_url") != SNAPSHOT_RELATIVE_PATH.as_posix():
        raise ValueError("IANA authority source must point to the retained registry snapshot.")
    if source_record.get("source_id") != language_audit.get("source_id"):
        raise ValueError("IANA language audit does not cite the source record that identifies its local snapshot.")

    used = {
        item.get("language_tag")
        for item in translation_registry.get("languages", []) + translation_registry.get("basis_languages", [])
    }
    used.discard(None)
    missing_audit = used - set(codes)
    if missing_audit:
        raise ValueError(f"Used language tags have not been included in the IANA audit: {sorted(missing_audit)}")
    return {code.lower() for code in codes}


def validate_iana_special_script_audit(audit: dict, root: Path, source_record: dict) -> None:
    """Check IANA-only script values (such as Zzzz) against the local registry copy."""
    language_audit = audit.get("language_subtags", {})
    script_audit = audit.get("script_codes", {})
    codes = script_audit.get("iana_special_codes", [])
    if not codes or len(codes) != len(set(codes)):
        raise ValueError("IANA special-script audit must contain a nonempty unique code list.")
    registry_date, entries = parse_iana_language_subtags(root / SNAPSHOT_RELATIVE_PATH)
    _verify_snapshot_hash(language_audit, root)
    if registry_date != language_audit.get("registry_file_date"):
        raise ValueError("IANA special-script audit date does not match the bundled registry snapshot.")
    unresolved = [
        code for code in codes
        if not any(record.get("Type") == "script" for record in entries.get(code.lower(), []))
    ]
    if unresolved:
        raise ValueError(f"IANA special script codes are absent from the bundled snapshot: {unresolved}")
    if (script_audit.get("iana_special_source_id") != language_audit.get("source_id")
            or source_record.get("source_id") != script_audit.get("iana_special_source_id")
            or source_record.get("local_metadata_url") != SNAPSHOT_RELATIVE_PATH.as_posix()):
        raise ValueError("IANA special-script audit must cite the source record for its retained snapshot.")
