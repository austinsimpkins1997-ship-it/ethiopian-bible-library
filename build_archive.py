"""Synchronize the human-readable CSV exports from the site archive source."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE_ARCHIVE = ROOT / "site" / "archive.json"
CATALOGUE_FIELDS = [
    "catalogue_id", "display_name", "alternate_names_or_notes", "tradition_group",
    "canon_view", "identity_status", "edition_or_translation", "chapter_count",
    "chapter_order_status", "text_availability_status", "completeness_status",
    "rights_status", "source_id", "catalogue_seed_url", "evidence_source_ids",
    "verification_date", "reviewer_notes",
]
SOURCE_FIELDS = ["source_id", "source_name", "url", "inspection_and_limitations", "archive_status"]


def main() -> None:
    archive = json.loads(SITE_ARCHIVE.read_text(encoding="utf-8"))
    catalogue = archive.get("catalogue", [])
    sources = archive.get("sources", [])
    source_ids = {source["source_id"] for source in sources}
    if len(source_ids) != len(sources):
        raise ValueError("Duplicate source IDs in site/archive.json.")
    if len({row["catalogue_id"] for row in catalogue}) != len(catalogue):
        raise ValueError("Duplicate catalogue IDs in site/archive.json.")
    for row in catalogue:
        missing = set(row.get("evidence_source_ids", [])) - source_ids
        if row.get("source_id") not in source_ids or missing:
            raise ValueError(f"Invalid source references in {row['catalogue_id']}: {sorted(missing)}")
    archive["catalogue_policy"] = archive.get("catalogue_policy", "")
    (ROOT / "archive.json").write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "catalogue.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CATALOGUE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in catalogue:
            export = dict(row)
            export["evidence_source_ids"] = json.dumps(row.get("evidence_source_ids", []), ensure_ascii=False)
            writer.writerow(export)
    with (ROOT / "sources.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SOURCE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sources)
    print(f"Synced {len(catalogue)} catalogue rows and {len(sources)} sources from site/archive.json.")


if __name__ == "__main__":
    main()
