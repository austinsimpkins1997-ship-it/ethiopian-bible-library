"""Build a separate, denominator-explicit rights snapshot for archive records."""

from __future__ import annotations

from datetime import date
from html import escape
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
JSON_PATH = Path("examples/rights-coverage.json")
HTML_PATH = Path("research/rights-coverage.html")
RIGHTS_CLASSES = (
    "open_license",
    "public_domain_claimed",
    "permission_limited",
    "all_rights_reserved",
    "mixed",
    "unknown",
)
LABELS = {
    "open_license": "Open license stated",
    "public_domain_claimed": "Public domain claimed",
    "permission_limited": "Permission limited",
    "all_rights_reserved": "All rights reserved",
    "mixed": "Mixed terms or jurisdictions",
    "unknown": "Unknown / not established",
}


def _counts(records: list[dict]) -> dict[str, int]:
    counts = {value: 0 for value in RIGHTS_CLASSES}
    for record in records:
        value = record.get("rights_classification")
        if value not in counts:
            raise ValueError(f"{record.get('source_id', record.get('reader_id', 'Record'))}: invalid or missing rights category {value!r}.")
        if not isinstance(record.get("rights_status"), str) or not record["rights_status"].strip():
            raise ValueError(f"{record.get('source_id', record.get('reader_id', 'Record'))}: no detailed rights notice.")
        counts[value] += 1
    if sum(counts.values()) != len(records):
        raise ValueError("Rights-class counts do not match the records in scope.")
    return counts


def _open_license_terms(records: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], int] = {}
    for record in records:
        if record.get("rights_classification") != "open_license":
            continue
        license_id = record.get("license_id")
        license_url = record.get("license_url")
        if not isinstance(license_id, str) or not license_id.strip() or not isinstance(license_url, str) or not license_url.startswith("https://"):
            raise ValueError(f"{record.get('reader_id', 'Open-license reader')}: specific license ID and HTTPS URL are required.")
        key = (license_id.strip(), license_url)
        grouped[key] = grouped.get(key, 0) + 1
    return [
        {"license_id": license_id, "license_url": license_url, "reader_record_count": count}
        for (license_id, license_url), count in sorted(grouped.items())
    ]


def build_summary(archive: dict) -> dict:
    sources = archive.get("sources", [])
    readers = archive.get("readers", [])
    if not isinstance(sources, list) or not isinstance(readers, list):
        raise ValueError("Archive sources and readers must be lists.")
    canon = [record for record in readers if record.get("canon_id")]
    research = [record for record in readers if record.get("research_corpus_id")]
    if len(canon) + len(research) != len(readers):
        raise ValueError("Every reader must be either canon-linked or separately scoped research.")
    return {
        "schema_version": 1,
        "as_of": date.today().isoformat(),
        "scope": "A snapshot of the rights categories recorded on source and reader records in this built package. These counts are not a legal opinion or a worldwide rights determination.",
        "sources": {
            "record_count": len(sources),
            "rights_class_counts": _counts(sources),
            "rights_basis_record_count": sum(
                isinstance(record.get("rights_basis"), str) and bool(record["rights_basis"].strip())
                for record in sources
            ),
            "interpretation": "A source record may describe a catalogue, bibliography, webpage, scan, or text. Its category does not grant reuse rights to any linked reader or media.",
        },
        "readers": {
            "record_count": len(readers),
            "canon_linked_record_count": len(canon),
            "research_only_record_count": len(research),
            "rights_class_counts": _counts(readers),
            "canon_linked_rights_class_counts": _counts(canon),
            "research_only_rights_class_counts": _counts(research),
            "open_license_terms": _open_license_terms(readers),
            "interpretation": "Reader categories describe the rights evidence recorded for each bundled text layer. Consult its exact notice and linked sources before reuse; archive canon links do not establish rights, edition identity, completeness, or accuracy.",
        },
        "classification_limits": {
            "open_license": "A license is stated in the record; its exact terms and scope still control.",
            "public_domain_claimed": "A source or record claims public-domain status; the archive has not established a worldwide legal conclusion.",
            "permission_limited": "Use is recorded with permission or other specific limits; follow the detailed notice.",
            "all_rights_reserved": "The source records an all-rights-reserved notice; no broader permission is inferred.",
            "mixed": "The record contains differing rights statements, jurisdictions, or components that must remain distinct.",
            "unknown": "The record does not establish reuse terms. Unknown is neither permission nor a finding that reuse is forbidden.",
        },
        "interpretation_limits": [
            "A source-record count is not a count of works, translations, or reader texts.",
            "A reader-record count is not a count of unique books or complete editions; several records may describe separate language or edition layers.",
            "An open-source software license or metadata license does not relicense scripture, translations, scans, images, or other third-party content.",
        ],
    }


def render_html(summary: dict) -> str:
    def table(title: str, counts: dict[str, int], denominator: int) -> str:
        rows = "".join(
            f"<tr><th scope=\"row\">{escape(LABELS[key])}</th><td>{counts[key]}</td><td>{(counts[key] / denominator * 100):.1f}%</td></tr>"
            if denominator else f"<tr><th scope=\"row\">{escape(LABELS[key])}</th><td>{counts[key]}</td><td>—</td></tr>"
            for key in RIGHTS_CLASSES
        )
        return f"<h3>{escape(title)} ({denominator} records)</h3><table><thead><tr><th scope=\"col\">Recorded category</th><th scope=\"col\">Records</th><th scope=\"col\">Share</th></tr></thead><tbody>{rows}</tbody></table>"

    sources = summary["sources"]
    readers = summary["readers"]
    source_table = table("Provenance/source records", sources["rights_class_counts"], sources["record_count"])
    reader_table = table("All bundled reader text records", readers["rights_class_counts"], readers["record_count"])
    canon_table = table("Canon-linked reader records", readers["canon_linked_rights_class_counts"], readers["canon_linked_record_count"])
    research_table = table("Research-only reader records", readers["research_only_rights_class_counts"], readers["research_only_record_count"])
    open_terms = readers["open_license_terms"]
    if open_terms:
        term_rows = "".join(
            f"<tr><th scope=\"row\">{escape(item['license_id'])}</th><td>{item['reader_record_count']}</td><td><a href=\"{escape(item['license_url'], quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">View license terms</a></td></tr>"
            for item in open_terms
        )
        open_terms_table = f"<table><caption>Reader records by license ID recorded in this archive</caption><thead><tr><th scope=\"col\">License ID</th><th scope=\"col\">Reader records</th><th scope=\"col\">License text</th></tr></thead><tbody>{term_rows}</tbody></table>"
    else:
        open_terms_table = "<p>No bundled reader records are currently classified as open-license.</p>"
    limits = "".join(f"<li>{escape(item)}</li>" for item in summary["interpretation_limits"])
    classifications = "".join(
        f"<dt>{escape(LABELS[key])}</dt><dd>{escape(value)}</dd>"
        for key, value in summary["classification_limits"].items()
    )
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Rights categories recorded for bundled reader text and archive source records, with separate counts and limits.">
  <title>Rights and reuse snapshot · Ethiopian Bible Library</title>
  <link rel="stylesheet" href="../styles.css">
  <style>
    .rights-report{{max-width:1120px;margin:2rem auto;padding:0 1rem;color:#183b35}}
    .rights-report h1,.rights-report h2,.rights-report h3{{font-family:Georgia,serif}}
    .rights-report table{{width:100%;border-collapse:collapse;margin:1rem 0 2rem}}
    .rights-report th,.rights-report td{{border:1px solid #ddd4c6;padding:.65rem;text-align:left}}
    .rights-report th[scope=row]{{font-weight:600}}
    .rights-report .notice{{border-left:4px solid #b68437;padding:.7rem 1rem;background:#f7f3eb}}
    .rights-report dl{{display:grid;grid-template-columns:minmax(11rem,1fr) 3fr;gap:.5rem 1rem}}
    @media(max-width:560px){{.rights-report dl{{grid-template-columns:1fr;gap:.15rem}}}}
  </style>
</head>
<body><main class="rights-report">
  <p><a href="../index.html">← Back to the archive</a></p>
  <h1>Rights and reuse snapshot</h1>
  <p>Built {escape(summary['as_of'])}. {escape(summary['scope'])}</p>
  <p class="notice">A source citation or an open-source software license does not grant permission to reuse scripture or a linked translation. Read the exact record and linked notice before reuse.</p>
  {source_table}
  <p>Source rights-basis fields are populated for {sources['rights_basis_record_count']} of {sources['record_count']} records. A populated basis may explicitly say evidence is missing; it is not a measure of how many items received independent legal review.</p>
  <p>{escape(sources['interpretation'])}</p>
  {reader_table}
  <p>{escape(readers['interpretation'])}</p>
  <p>Of {readers['record_count']} bundled reader records, {readers['canon_linked_record_count']} are canon-linked and {readers['research_only_record_count']} are separately scoped research layers. Neither grouping proves completeness or textual accuracy.</p>
  <h2>Specific open-license IDs recorded for reader text</h2>
  <p>These counts show which license identifiers the reader records name. They do not independently validate the source's authority to apply that license; retain the source attribution and follow the license text.</p>
  {open_terms_table}
  {canon_table}
  {research_table}
  <h2>What categories mean here</h2>
  <dl>{classifications}</dl>
  <h2>Limits</h2><ul>{limits}</ul>
  <p>Inspect the <a href="../CONTENT-LICENSES.md">content license guide</a>, <a href="../DATA-LICENSE.md">metadata license</a>, <a href="../archive.json">full archive records</a>, and <a href="../package-inventory.json">package snapshot inventory</a>. <a href="../examples/rights-coverage.json" download>Download this report as JSON</a>.</p>
</main></body></html>'''


def write_reports(root: Path, archive: dict) -> dict:
    summary = build_summary(archive)
    inventory_path = root / "package-inventory.json"
    if inventory_path.exists():
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        source_counts = summary["sources"]
        reader_counts = summary["readers"]
        if (
            inventory.get("source_record_count") != source_counts["record_count"]
            or inventory.get("source_rights_class_counts") != {
                key: count for key, count in source_counts["rights_class_counts"].items() if count
            }
        ):
            raise ValueError("Rights report source counts disagree with the package inventory.")
        reader_inventory = inventory.get("reader_records", {})
        if (
            reader_inventory.get("total") != reader_counts["record_count"]
            or reader_inventory.get("canon_linked") != reader_counts["canon_linked_record_count"]
            or reader_inventory.get("research_only") != reader_counts["research_only_record_count"]
            or reader_inventory.get("rights_class_counts") != {
                key: count for key, count in reader_counts["rights_class_counts"].items() if count
            }
        ):
            raise ValueError("Rights report reader counts disagree with the package inventory.")
    json_path = root / JSON_PATH
    html_path = root / HTML_PATH
    json_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(summary), encoding="utf-8")
    return summary
