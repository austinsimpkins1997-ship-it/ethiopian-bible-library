"""Embed archive.json into index.html so the catalogue works without data fetches."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "archive.json"
HTML_PATH = ROOT / "index.html"
EMBED_RE = re.compile(
    r'(<script id="archive-data" type="application/json">).*?(</script>)',
    re.DOTALL,
)


def require_unique(items: list[dict], field: str, label: str) -> set[str]:
    values = [item.get(field) for item in items]
    if any(not value for value in values):
        raise ValueError(f"Every {label} needs a {field}.")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {field} in {label}.")
    return set(values)


def main() -> None:
    archive = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    catalogue = archive.get("catalogue", [])
    sources = archive.get("sources", [])
    related = archive.get("related_texts", [])
    if not all(isinstance(items, list) for items in (catalogue, sources, related)):
        raise ValueError("catalogue, sources, and related_texts must be arrays.")

    require_unique(catalogue, "catalogue_id", "catalogue record")
    source_ids = require_unique(sources, "source_id", "source record")
    require_unique(related, "related_id", "related-text record")

    for record in related:
        missing = set(record.get("source_ids", [])) - source_ids
        if missing:
            raise ValueError(f"{record.get('title')} refers to missing sources: {sorted(missing)}")

    for record in catalogue:
        if record.get("source_id") not in source_ids:
            raise ValueError(f"{record.get('display_name')} has no valid catalogue source.")
        missing = set(record.get("evidence_source_ids", [])) - source_ids
        if missing:
            raise ValueError(f"{record.get('display_name')} refers to missing evidence sources: {sorted(missing)}")
        for field in ("identity_status", "edition_or_translation", "chapter_count", "chapter_order_status",
                      "text_availability_status", "completeness_status", "rights_status", "reviewer_notes"):
            if not record.get(field):
                raise ValueError(f"{record.get('display_name')} is missing {field}; use an explicit unknown status.")

    html = HTML_PATH.read_text(encoding="utf-8")
    if len(EMBED_RE.findall(html)) != 1:
        raise ValueError('Expected exactly one <script id="archive-data"> placeholder.')

    payload = json.dumps(archive, ensure_ascii=False, separators=(",", ":"))
    # Prevent data from closing its containing script element.
    payload = payload.replace("<", "\\u003c")
    HTML_PATH.write_text(EMBED_RE.sub(lambda match: match.group(1) + payload + match.group(2), html), encoding="utf-8")
    print(
        f"Embedded {len(catalogue)} catalogue rows, {len(sources)} sources, "
        f"and {len(related)} related records into index.html."
    )


if __name__ == "__main__":
    main()
