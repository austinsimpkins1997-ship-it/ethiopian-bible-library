"""Small helpers for stable, repeatable metadata builds."""

from __future__ import annotations


def ensure_appended_note_once(existing: str, note: str, separator: str = " ") -> str:
    """Keep one copy of a generated note when rebuilding from prior output."""
    if not isinstance(existing, str) or not isinstance(note, str) or not note.strip():
        raise ValueError("Existing text and a non-empty note are required.")
    base = existing.replace(note, "")
    if separator == "; ":
        base = base.rstrip(" ;").strip()
    else:
        base = base.strip()
    return f"{base}{separator if base else ''}{note}".strip()
