"""Build a cautious, human-readable summary of normalized review events."""

from __future__ import annotations

from collections import Counter, defaultdict
from html import escape
import json
from pathlib import Path


GRAPH_PATH = Path("examples/archive-graph-registered-layers.json")
JSON_PATH = Path("examples/review-coverage.json")
HTML_PATH = Path("research/review-coverage.html")


def build_summary(graph: dict) -> dict:
    layers = graph.get("layers", [])
    events = graph.get("review_events", [])
    translations = [layer for layer in layers if layer.get("layer_type") == "translation"]
    translation_paths = Counter(
        "documented" if isinstance(layer.get("basis_path"), list) and len(layer["basis_path"]) >= 2
        else "unknown"
        for layer in translations
    )
    by_language_script: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for layer in layers:
        by_language_script[(layer.get("language_tag") or "und", layer.get("script_code") or "Zyyy")].append(layer)
    language_script_counts = []
    for (language_tag, script_code), records in sorted(by_language_script.items()):
        language_translations = [record for record in records if record.get("layer_type") == "translation"]
        language_script_counts.append({
            "language_tag": language_tag,
            "script_code": script_code,
            "layer_count": len(records),
            "translation_layer_count": len(language_translations),
            "translations_with_documented_basis": sum(
                isinstance(record.get("basis_path"), list) and len(record["basis_path"]) >= 2
                for record in language_translations
            ),
            "translations_with_unknown_basis": sum(
                not isinstance(record.get("basis_path"), list) or len(record["basis_path"]) < 2
                for record in language_translations
            ),
        })
    layer_ids = {layer.get("id") for layer in layers}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        layer_id = event.get("layer_id")
        if layer_id not in layer_ids:
            raise ValueError(f"Review event {event.get('id')} points to an unknown layer.")
        dimension = event.get("dimension")
        state = event.get("state")
        if not isinstance(dimension, str) or not dimension.strip():
            raise ValueError(f"Review event {event.get('id')} has no review dimension.")
        if not isinstance(state, str) or not state.strip():
            raise ValueError(f"Review event {event.get('id')} has no review state.")
        grouped[dimension].append(event)

    dimensions = []
    for name, records in sorted(grouped.items()):
        states = Counter(event["state"] for event in records)
        methods = Counter(event.get("method") or "not_recorded" for event in records)
        dimensions.append({
            "dimension": name,
            "event_count": len(records),
            "distinct_layer_count": len({event["layer_id"] for event in records}),
            "state_counts": dict(sorted(states.items())),
            "method_counts": dict(sorted(methods.items())),
            "events_with_named_reviewer": sum(
                isinstance(event.get("reviewer"), str) and bool(event["reviewer"].strip())
                for event in records
            ),
        })

    return {
        "schema_version": 1,
        "source_graph": GRAPH_PATH.as_posix(),
        "layer_count": len(layers),
        "review_event_count": len(events),
        "layers_with_review_events": len({event["layer_id"] for event in events}),
        "events_with_named_reviewer": sum(
            isinstance(event.get("reviewer"), str) and bool(event["reviewer"].strip())
            for event in events
        ),
        "translation_traceability": {
            "translation_layer_count": len(translations),
            "basis_path_counts": dict(sorted(translation_paths.items())),
            "language_script_counts": language_script_counts,
            "interpretation_limit": "A documented path records what this archive's cited metadata says; it does not independently verify that path or translation accuracy. An unknown path is not inferred from the output language.",
        },
        "interpretation_limits": [
            "Counts describe recorded review-event rows, not unique books or independent reviews; a layer may have several events.",
            "checked_with_limits describes only the scope recorded in that event. It does not establish completeness, accuracy, canon identity, or universal agreement.",
            "unknown and not_checked are preserved as recorded; missing evidence is not treated as a successful review.",
            "A missing reviewer name means the record does not identify a reviewer; it does not prove that no person contributed.",
        ],
        "dimensions": dimensions,
    }


def render_html(summary: dict) -> str:
    rows = []
    for dimension in summary["dimensions"]:
        states = "; ".join(f"{escape(state)}: {count}" for state, count in dimension["state_counts"].items())
        methods = "; ".join(f"{escape(method)}: {count}" for method, count in dimension["method_counts"].items())
        rows.append(
            "<tr>"
            f"<th scope=\"row\">{escape(dimension['dimension'])}</th>"
            f"<td>{dimension['event_count']}</td>"
            f"<td>{dimension['distinct_layer_count']}</td>"
            f"<td>{states}</td>"
            f"<td>{methods}</td>"
            f"<td>{dimension['events_with_named_reviewer']}</td>"
            "</tr>"
        )
    limits = "".join(f"<li>{escape(note)}</li>" for note in summary["interpretation_limits"])
    traceability = summary["translation_traceability"]
    translation_rows = []
    for item in traceability["language_script_counts"]:
        translation_rows.append(
            "<tr>"
            f"<th scope=\"row\"><code>{escape(item['language_tag'])}</code></th>"
            f"<td><code>{escape(item['script_code'])}</code></td>"
            f"<td>{item['layer_count']}</td>"
            f"<td>{item['translation_layer_count']}</td>"
            f"<td>{item['translations_with_documented_basis']}</td>"
            f"<td>{item['translations_with_unknown_basis']}</td>"
            "</tr>"
        )
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A bounded summary of review events recorded for bundled archive layers.">
  <title>Review coverage · Ethiopian Bible Library</title>
  <link rel="stylesheet" href="../styles.css">
  <style>
    .review-report{{max-width:1120px;margin:2rem auto;padding:0 1rem;color:#183b35}}
    .review-report h1,.review-report h2{{font-family:Georgia,serif}}
    .review-table-wrap{{overflow-x:auto;margin:1.5rem 0}}
    .review-table{{border-collapse:collapse;width:100%;min-width:760px;background:#fff}}
    .review-table th,.review-table td{{border:1px solid #ded8ca;padding:.65rem;text-align:left;vertical-align:top;font-size:.9rem}}
    .review-table thead{{background:#f2eee4}}
    .review-limits{{background:#f6f2e8;padding:1rem 1.25rem}}
    .review-report a{{color:#155e50}}
  </style>
</head>
<body>
  <main class="review-report">
    <p><a href="../index.html#about">← Ethiopian Bible Library</a></p>
    <p class="eyebrow">MEASURED REVIEW RECORDS</p>
    <h1>Review coverage in this package</h1>
    <p>This snapshot contains <strong>{summary['layer_count']}</strong> bundled text layers and <strong>{summary['review_event_count']}</strong> recorded review events across <strong>{summary['layers_with_review_events']}</strong> layers. Events with an identified reviewer: <strong>{summary['events_with_named_reviewer']}</strong>.</p>
    <section aria-labelledby="translation-traceability-title">
      <h2 id="translation-traceability-title">Translation source paths</h2>
      <p>Of <strong>{traceability['translation_layer_count']}</strong> translation layers, <strong>{traceability['basis_path_counts'].get('documented', 0)}</strong> have a recorded source-language path and <strong>{traceability['basis_path_counts'].get('unknown', 0)}</strong> have no established path in the cited metadata.</p>
      <p>{escape(traceability['interpretation_limit'])}</p>
      <div class="review-table-wrap"><table class="review-table">
        <thead><tr><th scope="col">Language tag</th><th scope="col">Script</th><th scope="col">All layers</th><th scope="col">Translation layers</th><th scope="col">Basis recorded</th><th scope="col">Basis unknown</th></tr></thead>
        <tbody>{''.join(translation_rows)}</tbody>
      </table></div>
    </section>
    <p>Rows are grouped by review dimension. Event counts and distinct-layer counts are separate because a layer can have multiple records for one dimension.</p>
    <div class="review-table-wrap">
      <table class="review-table">
        <thead><tr><th scope="col">Review dimension</th><th scope="col">Events</th><th scope="col">Distinct layers</th><th scope="col">Recorded states</th><th scope="col">Recorded methods</th><th scope="col">Named reviewer events</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    <section class="review-limits" aria-labelledby="limits-title">
      <h2 id="limits-title">How to read these counts</h2>
      <ul>{limits}</ul>
      <p>Inspect the <a href="../examples/archive-graph-registered-layers.json">normalized source graph</a> for event-level scope, evidence IDs, and notes, or <a href="../examples/review-coverage.json" download>download this summary as JSON</a>.</p>
    </section>
  </main>
</body>
</html>
'''


def write_review_coverage(site_root: Path, graph: dict) -> dict:
    summary = build_summary(graph)
    (site_root / JSON_PATH).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (site_root / HTML_PATH).write_text(render_html(summary), encoding="utf-8")
    return summary
