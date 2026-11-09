"""Register the exact Gutenberg plain-text source snapshot for Charles 1 Enoch."""

from __future__ import annotations

import hashlib
from pathlib import Path

from archive_manifest import write_text_atomically


ROOT = Path(__file__).resolve().parent
SOURCE_PATH = "readers/source/enoch/charles-1917-gutenberg-77935.txt"
SOURCE_URL = "https://www.gutenberg.org/cache/epub/77935/pg77935.txt"
SOURCE_SHA256 = "10d325355a810badf67bbbd1fe6bda77dc6e294eae78c2f6c69290188af45b14"
REVIEW_PATH = "research/enoch-charles-1917-source.html"
AUDIT_PATH = "research/enoch-charles-1917-structure-audit.md"
TRANSLATION_ID = "enoch-en-charles-1912-gutenberg-77935"
STATUS = "exact-source-rendition; reader structure and text accuracy not independently verified"


def _html() -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>1 Enoch — Charles English source snapshot</title>
  <style>
    :root {{ color-scheme: light; --ink:#123e39; --muted:#53645f; --line:#e3ddd1; --paper:#fbfaf7; --accent:#b27d32; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.65 system-ui,sans-serif; }}
    main {{ width:min(850px,calc(100% - 32px)); margin:0 auto; padding:36px 0 64px; }}
    h1,h2 {{ font-family:Georgia,serif; font-weight:500; line-height:1.2; }}
    h1 {{ font-size:clamp(2rem,6vw,3.2rem); margin:0 0 12px; }}
    h2 {{ font-size:1.5rem; margin:30px 0 8px; }}
    p,li {{ max-width:76ch; }}
    a {{ color:#075c53; text-underline-offset:.18em; overflow-wrap:anywhere; }}
    .kicker {{ color:var(--accent); letter-spacing:.12em; text-transform:uppercase; font-size:.78rem; font-weight:700; }}
    .notice {{ border-left:4px solid var(--accent); background:#f3efe5; padding:14px 18px; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:10px; margin:18px 0; }}
    .button {{ display:inline-block; border:1px solid #8e795b; border-radius:4px; padding:10px 14px; text-decoration:none; font-weight:650; }}
    .small {{ color:var(--muted); font-size:.92rem; }}
    code {{ overflow-wrap:anywhere; }}
  </style>
</head>
<body><main>
  <p class="kicker">Ethiopian Bible Library · source snapshot</p>
  <h1>1 Enoch — R. H. Charles’s English edition</h1>
  <p>This is a byte-verified local copy of Project Gutenberg eBook 77935’s original plain-text rendition. The eBook names R. H. Charles as translator and W. O. E. Oesterley as contributor; it identifies the 1917 first publication and says the translation reprints Charles’s 1912 second edition.</p>
  <div class="notice"><strong>Reading status:</strong> Open the captured source as published. The archive has not proofread or chapter-normalized this text and has not aligned it with the separate Geʽez reader. This source snapshot does not increase structured-reader coverage.</div>
  <div class="actions">
    <a class="button" href="../{SOURCE_PATH}">Open the captured source text</a>
    <a class="button" href="../index.html?reader=enoch-geez-eotc#reader">Open separate Geʽez reader</a>
    <a class="button" href="{SOURCE_URL}">Project Gutenberg source record</a>
  </div>
  <h2>Edition and structure</h2>
  <p>The historical English witness is its own edition. Its HTML and plain-text renditions contain grouped section headings, irregular chapter openings, and editorial apparatus. A simple numeral scan does not establish missing chapters or complete chapter boundaries. The printed edition must be audited before building a normalized chapter reader or claiming alignment.</p>
  <p>See the <a href="enoch-charles-1917-structure-audit.md">local structure and rights audit</a>. Source SHA-256: <code>{SOURCE_SHA256}</code>.</p>
  <h2>Rights</h2>
  <p>Project Gutenberg marks the eBook public domain in the United States and includes its license in the captured file. This is a source-reported U.S. claim, not a worldwide rights determination. Check applicable law outside the United States before reuse.</p>
  <p class="small">The local copy is unmodified at the byte level from the linked plain-text rendition; its checksum is recorded in the source and translation registries.</p>
</main></body></html>
'''


def apply(archive: dict) -> None:
    source_path = ROOT / SOURCE_PATH
    if not source_path.is_file():
        raise ValueError(f"Missing captured Project Gutenberg source: {SOURCE_PATH}")
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"Gutenberg source snapshot hash mismatch: {digest}")

    sources = {item["source_id"]: item for item in archive.get("sources", [])}
    for source_id in ("SRC-094", "SRC-125"):
        if source_id not in sources:
            raise ValueError(f"Missing Enoch Gutenberg source record {source_id}")
        record = sources[source_id]
        record["local_review_url"] = REVIEW_PATH
        if source_id == "SRC-125":
            record["local_research_view_url"] = REVIEW_PATH
        record["local_snapshot_path"] = SOURCE_PATH
        record["local_snapshot_sha256"] = digest
        record["local_snapshot_status"] = STATUS
        record["archive_status"] = (
            "Captured Project Gutenberg plain-text source companion available locally; unstructured, "
            "not a normalized or verified reader"
        )
        note = (
            f"The exact Project Gutenberg plain-text rendition is captured locally at {SOURCE_PATH} "
            f"(SHA-256 {digest}). It remains original source form: chapter boundaries, textual accuracy, "
            "completeness, worldwide rights, and alignment with the Geʽez reader are not established. "
            "The HTML rendition was inspected online but is not locally captured."
        )
        base = record.get("inspection_and_limitations", "")
        marker = "The exact Project Gutenberg plain-text rendition is captured locally at "
        if marker not in base:
            if base.endswith("No English text is bundled."):
                base = base[: -len("No English text is bundled.")].rstrip()
            record["inspection_and_limitations"] = f"{base} {note}".strip()
        record["local_snapshot_note"] = note

    registry = archive.get("translation_registry", {})
    lead = next(
        (item for item in registry.get("translation_leads", []) if item.get("translation_id") == TRANSLATION_ID),
        None,
    )
    if lead is None:
        raise ValueError(f"Missing Charles translation lead {TRANSLATION_ID}")
    lead["source_snapshot"] = {
        "path": SOURCE_PATH,
        "sha256": digest,
        "source_url": SOURCE_URL,
        "format": "text/plain",
        "status": STATUS,
    }
    lead["scope_description"] = (
        "The source edition is identified as Charles’s English translation based on an Ethiopic text, with Greek fragments "
        "separately reprinted. The exact Project Gutenberg plain-text rendition is captured locally as source data; it is "
        "not a proofread or normalized reader. Its chapter map, accuracy, completeness, and alignment with the archive’s "
        "separate Geʽez reader remain unverified."
    )
    lead["review_status"] = (
        "The official eBook metadata, front matter, and source text were checked. The local plain-text file matches the "
        "audited Project Gutenberg rendition byte for byte and retains its included license. No custom chapter map, "
        "printed-page collation, completeness review, wording verification, or Geʽez alignment has been completed. "
        "This source copy is not counted as a structured reader."
    )
    lead["rights_status"] = (
        "Project Gutenberg marks this eBook public domain in the United States and distributes it under the included "
        "Project Gutenberg License; its notice directs readers elsewhere to check local law. The archive preserves that "
        "source claim with the exact snapshot but has not independently determined worldwide rights."
    )
    lead["notes"] = (
        "The 1912 title identifies Ethiopic as the immediate translation base and separately reprints Greek fragments. "
        "‘gez → en’ records that edition-level statement, not a verified line-by-line basis for every reading. The exact "
        "plain-text source file is locally available, but its grouped/irregular section structure is not a verified chapter "
        "map and is not aligned with the archive’s Geʽez reader. The title statement does not prove Charles used the same "
        "Ethiopic recension as that reader. No coverage count is increased."
    )

    write_text_atomically(ROOT / REVIEW_PATH, _html())


if __name__ == "__main__":
    import json

    path = ROOT / "archive.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    apply(data)
    write_text_atomically(path, json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Registered exact Enoch source capture: {SOURCE_PATH} ({SOURCE_SHA256})")
