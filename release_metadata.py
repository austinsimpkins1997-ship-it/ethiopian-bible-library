"""Explicit release dates keep offline rebuilds independent of the wall clock."""
from datetime import date
import json
from pathlib import Path


def release_date() -> str:
    record = json.loads((Path(__file__).resolve().parent / "release-metadata.json").read_text(encoding="utf-8"))
    value = record["release_date"]
    if record.get("schema_version") != 1 or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Invalid explicit release date.")
    return value
