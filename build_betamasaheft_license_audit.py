"""Attach current provider license-context evidence to bundled Beta maṣāḥǝft readers."""

from __future__ import annotations

import json
import re
import re
from archive_manifest import write_text_atomically
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
GUIDELINES_ID = "SRC-296"
DATASET_ID = "SRC-297"
GUIDELINES_URL = "https://betamasaheft.awhamburg.de/Guidelines/?id=catalogueworkflow"
DATASET_URL = "https://www.fdr.uni-hamburg.de/record/9784"
FILE_LICENSE = "CC BY-SA 4.0"
GUIDELINES_LICENSE = "CC BY-NC-SA 4.0"
RIGHTS_NOTE = (
    "The pinned TEI file states CC BY-SA 4.0. Beta maṣāḥǝft's current Guidelines describe project data and "
    "remixes under CC BY-NC-SA 4.0; the University of Hamburg's 2022 version 5.2 dataset record carries "
    "dataset-level CC BY 4.0 metadata and says individual files contain specific attribution. These notices "
    "do not clearly establish which terms control this file or the unidentified underlying printed exemplar. "
    "Rights are therefore classified as mixed pending clarification; no commercial or unrestricted reuse "
    "permission is asserted by this archive."
)
WITHHELD_MAPPING_NOTE = "Source text is withheld pending rights clarification; see SRC-296–SRC-297."
WITHHELD_REVIEW_NOTE = "Text withheld pending rights clarification; this is a metadata-only lead."

KNOWN_BETA_SCRIPTURE_READERS = {
    "mark-betamasaheft-tei-research",
    "daniel-betamasaheft-tei",
    "jubilees-geez-hacohen",
    "enoch-geez-eotc",
}
KNOWN_BETA_PUBLIC_PAYLOADS = {
    "mark-betamasaheft-tei-research": ("readers/mark-research-tei.json", "readers/source/mark/LIT2711Mark-original.xml", "examples/mark-research-tei-layer.json"),
    "daniel-betamasaheft-tei": ("readers/daniel-betamasaheft-tei.json", "readers/source/daniel/LIT3529Daniel-original.xml", "examples/daniel-betamasaheft-tei-layer.json"),
    "jubilees-geez-hacohen": ("readers/jubilees-geez-hacohen.json", "readers/source/jubilees/LIT1697Jubilees-Ran.xml", "examples/jubilees-geez-layer.json"),
    "enoch-geez-eotc": ("readers/enoch-geez-eotc.json", "readers/source/enoch/LIT1340EnochE-EOTCed.xml", "examples/enoch-geez-eotc-layer.json"),
}


def _is_beta_work_source(source: dict) -> bool:
    """Recognize Beta maṣāḥǝft work files across GitHub, raw GitHub, and the project API."""
    url = source.get("url", "")
    parsed = urlparse(url)
    host = (parsed.hostname or "").casefold()
    path = parsed.path.casefold()
    if host in {"github.com", "raw.githubusercontent.com"}:
        return "/betamasaheft/works/" in path
    if host in {"betamasaheft.eu", "betamasaheft.awhamburg.de"}:
        return bool(
            re.search(r"/works/lit[^/]+/(?:main|text)(?:/|$)", path)
            or re.search(r"/api/lit[^/]+/tei(?:/|$)", path)
        )
    return False


def public_payload_paths(archive: dict, root: Path = ROOT) -> list[Path]:
    """Return locally stored text payloads that the audit will withhold."""
    affected = set(KNOWN_BETA_SCRIPTURE_READERS)
    paths: set[Path] = set()
    for reader_path, source_path, layer_path in KNOWN_BETA_PUBLIC_PAYLOADS.values():
        paths.add(root / reader_path)
        paths.add(root / source_path)
        paths.add(root / layer_path)
    for reader in archive.get("readers", []):
        reader_id = reader.get("reader_id")
        cited = [item for item in archive.get("sources", [])
                 if item.get("source_id") in reader.get("source_ids", [])]
        if reader.get("license_id") != "CC-BY-SA-4.0":
            continue
        if reader_id in KNOWN_BETA_SCRIPTURE_READERS or any(_is_beta_work_source(item) for item in cited):
            affected.add(reader_id)
            paths.add(root / "readers" / f"{reader_id}.json")
            local_source = reader.get("source_path") or reader.get("source_pages")
            if isinstance(local_source, str):
                # source_pages may append an explanatory parenthetical after the path.
                local_source = local_source.split(" (", 1)[0].strip()
                candidate = (root / local_source).resolve()
                if candidate.is_relative_to(root.resolve()):
                    relative = candidate.relative_to(root.resolve())
                    if relative.parts[:2] == ("readers", "source") and candidate.suffix.casefold() == ".xml" and candidate.is_file():
                        paths.add(candidate)
    return sorted(paths)


def remove_public_payloads(paths: list[Path], root: Path = ROOT) -> list[str]:
    """Remove only the explicitly selected public text payload paths after preservation."""
    root = root.resolve()
    removed = []
    for path in paths:
        candidate = path.resolve()
        if not candidate.is_relative_to(root):
            raise ValueError(f"Refusing to remove a path outside the public package: {candidate}")
        if candidate.is_file():
            candidate.unlink()
            removed.append(candidate.relative_to(root).as_posix())
    return removed


def _ensure_note_once(existing: str, note: str) -> str:
    """Normalize a generated notice that may already occur in prior output."""
    base = existing.replace(note, "").strip()
    return f"{base} {note}".strip()


def _source_records() -> list[dict]:
    return [
        {
            "source_id": GUIDELINES_ID,
            "source_name": "Beta maṣāḥǝft Guidelines — copyright of remixed content",
            "url": GUIDELINES_URL,
            "inspection_and_limitations": (
                "The current Beta maṣāḥǝft Guidelines' ‘Copyright of remixed content’ section says project data "
                "on site pages and in dataset files is shared under CC BY-NC-SA 4.0 and says publications that "
                "remix the data should carry the same or a more permissive license negotiated with the publisher. "
                "This is current provider guidance, not a file-specific clarification for the scripture TEI files "
                "listed in the archive. Last successful content inspection: 2026-10-25; an access attempt on 2026-10-27 returned HTTP 502, so no new page content was inferred."
            ),
            "archive_status": "Current primary provider license guidance; scope relative to explicit per-file CC BY-SA notices remains unresolved",
        },
        {
            "source_id": DATASET_ID,
            "source_name": "University of Hamburg repository — Beta maṣāḥǝft Data version 5.2",
            "url": DATASET_URL,
            "inspection_and_limitations": (
                "The University of Hamburg repository identifies this as the 2022 version 5.2 Beta maṣāḥǝft "
                "dataset and records dataset-level CC BY 4.0 metadata. Its description says each file contains "
                "specific attribution. This dataset-level record does not resolve conflicts between specific TEI "
                "file notices and the current Beta maṣāḥǝft Guidelines, nor does it establish rights in the "
                "underlying printed exemplars. Inspected 2026-10-27."
            ),
            "archive_status": "Primary institutional versioned dataset metadata; not a substitute for per-file terms",
        },
    ]


def build(archive: dict) -> int:
    """Withhold mixed-rights Works text while preserving source and crosswalk metadata."""
    sources = {item["source_id"]: item for item in archive.get("sources", [])}
    sources.update({item["source_id"]: item for item in _source_records()})
    archive["sources"] = sorted(
        sources.values(), key=lambda item: int(item["source_id"].split("-")[1])
    )

    readers = archive.get("readers", [])
    reader_ids: set[str] = set()
    canon_ids: set[str] = set()
    matched_files: list[tuple[str, str, str, str]] = []
    matched_readers: dict[str, dict] = {}
    source_ids = {item["source_id"] for item in archive["sources"]}
    for reader in readers:
        cited = [sources.get(value, {}) for value in reader.get("source_ids", [])]
        is_file_licensed_works_text = (
            reader.get("license_id") == "CC-BY-SA-4.0"
            and (reader.get("reader_id") in KNOWN_BETA_SCRIPTURE_READERS
                 or any(_is_beta_work_source(item) for item in cited))
        )
        if not is_file_licensed_works_text:
            continue
        reader_ids.add(reader["reader_id"])
        matched_readers[reader["reader_id"]] = reader
        work_source = next(
            (item for item in cited if "/api/" in urlparse(item.get("url", "")).path.casefold()),
            None,
        ) or next((item for item in cited if _is_beta_work_source(item)), None)
        if work_source is None:
            # Mark's current local source locator is SRC-092; its official work
            # page is the best public pointer until the audited source is withheld.
            work_source = next((item for item in cited if item.get("source_id") in {"SRC-083", "SRC-091"}), None)
        if work_source is None:
            raise ValueError(f"No public Beta maṣāḥǝft source URL is recorded for {reader['reader_id']}.")
        source_digest = (reader.get("source_snapshot_sha256") or reader.get("parent_source_sha256")
                         or reader.get("source_sha256") or "unknown")
        text_digest = reader.get("source_sha256") or reader.get("source_snapshot_sha256") or "unknown"
        matched_files.append((reader["reader_id"], work_source["url"], source_digest, text_digest))
        reader["source_ids"] = sorted(
            set(reader.get("source_ids", [])) | {GUIDELINES_ID, DATASET_ID},
            key=lambda value: int(value.split("-")[1]),
        )
        reader["rights_classification"] = "mixed"
        for field in ("copyright_notice", "commercial_use", "verification_status"):
            current = reader.get(field, "")
            if RIGHTS_NOTE not in current:
                reader[field] = f"{current} {RIGHTS_NOTE}".strip()
        if reader.get("canon_id"):
            canon_ids.add(reader["canon_id"])

    if not reader_ids:
        existing = archive.get("rights_withheld_texts", [])
        if existing:
            reader_ids = {item["reader_id"] for item in existing}
            matched_files = [
                (item["reader_id"], item.get("source_url", "source URL not recorded"),
                 item.get("source_snapshot_sha256") or "unknown",
                 item.get("withheld_text_sha256") or item.get("source_snapshot_sha256") or "unknown")
                for item in existing
            ]
        else:
            raise ValueError("No bundled or rights-withheld Beta maṣāḥǝft Works reader found for the license audit.")

    # Preserve citations and measurements, but make the public source register
    # explicit that the captured scripture payload itself is not distributed.
    matched_source_ids = {
        source_id for reader in matched_readers.values() for source_id in reader.get("source_ids", [])
    }
    # A subsequent standalone rebuild starts from already-withheld metadata;
    # keep source citations' measured scope and mark their content unavailable.
    matched_source_ids.update(
        source_id
        for item in archive.get("rights_withheld_texts", [])
        if item.get("reader_id") in reader_ids
        for source_id in item.get("source_ids", [])
    )
    for source in archive["sources"]:
        if (_is_beta_work_source(source) or source.get("source_id") == "SRC-092") and source.get("source_id") in matched_source_ids:
            source["archive_status"] = (
                "Metadata citation retained; source scripture file withheld from this public bundle pending rights clarification."
            )
            prior = source.get("inspection_and_limitations", "")
            stale_prefix = ". The cited file's scripture content is not included in this public bundle."
            if prior.startswith("Pinned source URL:") and stale_prefix in prior:
                prior = prior.split(stale_prefix, 1)[1].lstrip()
            prior = prior.replace(
                "The cited scripture payload is not included in this public bundle. Its file-level notice, current provider guidance, versioned dataset metadata, and rights in any underlying printed exemplar remain unresolved; a private preservation copy is not a public distribution grant.",
                "",
            ).strip()
            source["inspection_and_limitations"] = _ensure_note_once(
                prior,
                "Scripture content from this cited file is withheld from the public bundle. Its file-level notice, current provider guidance, versioned dataset metadata, and rights in any underlying printed exemplar remain unresolved; preservation copies are not a public distribution grant.",
            )
            associated = [
                item for item in archive.get("rights_withheld_texts", [])
                if source.get("source_id") in item.get("source_ids", [])
                and item.get("reader_id") in reader_ids
                and isinstance(item.get("chapter_count"), int)
                and isinstance(item.get("unit_count"), int)
            ]
            for item in associated:
                if item["reader_id"] == "daniel-betamasaheft-tei":
                    scope = "The pinned Daniel TEI structure has 14 ordered chapter divisions and 437 labeled line elements; this count is retained as metadata while the wording is withheld."
                elif item["reader_id"] == "mark-betamasaheft-tei-research":
                    scope = "The pinned Mark TEI structure has 16 chapter divisions and 765 line elements; this count is retained as metadata while the wording is withheld."
                else:
                    scope = (
                        f"The pinned {item.get('title', item['reader_id'])} TEI structure records "
                        f"{item['chapter_count']} chapter divisions and {item['unit_count']} line elements; "
                        "these are source-structure counts, not completeness or accuracy findings, and wording is withheld."
                    )
                source["inspection_and_limitations"] = _ensure_note_once(
                    source["inspection_and_limitations"], scope
                )
            if source.get("source_id") == "SRC-092":
                source["url"] = "https://betamasaheft.eu/api/LIT2711Mark/tei"
                source["local_metadata_url"] = "readers/source/mark/structure-audit.json"
                source["source_name"] = "Beta maṣāḥǝft — Mark TEI snapshot locator and retained structure audit"

    registry = archive.get("translation_registry", {})
    corpus_reader_ids: set[str] = set()
    corpus_by_reader: dict[str, dict] = {}
    newly_withheld_corpora: list[dict] = []
    language_names = {item.get("language_tag"): item.get("language_name", item.get("name", "Unknown language"))
                      for item in registry.get("languages", [])}
    for corpus in registry.get("research_corpora", []):
        if corpus.get("reader_id") not in reader_ids:
            continue
        corpus_reader_id = corpus["reader_id"]
        corpus_reader_ids.add(corpus_reader_id)
        corpus_by_reader[corpus_reader_id] = corpus
        reader = matched_readers.get(corpus_reader_id)
        if reader is None:
            continue
        source_list = sorted(
            set(corpus.get("source_ids", [])) | set(reader.get("source_ids", [])) | {GUIDELINES_ID, DATASET_ID},
            key=lambda value: int(value.split("-")[1]),
        )
        newly_withheld_corpora.append({
            "corpus_id": corpus["corpus_id"],
            "title": corpus.get("title", reader.get("title", corpus["corpus_id"])),
            "language_tag": corpus.get("language_tag", reader.get("language_tag", "und")),
            "language_name": language_names.get(corpus.get("language_tag", reader.get("language_tag")), "Geʽez (Classical Ethiopic)"),
            "script_code": corpus.get("script_code", reader.get("script_code", "Ethi")),
            "script_status": "identified",
            "publisher": "Beta maṣāḥǝft",
            "publication_year": "unknown",
            "scope_description": (
                f"Metadata lead for the pinned Beta maṣāḥǝft TEI file. {reader.get('edition_scope', corpus.get('unit_summary', ''))} "
                "The text is withheld from this public bundle pending clarification of conflicting rights notices."
            ),
            "basis_language_tag": reader.get("language_tag", "gez"),
            "basis_description": "The source transcription is in the stated source language; no translation path is asserted.",
            "translation_path": None,
            "contributors": "Beta maṣāḥǝft TEI source; individual transcription roles for this selected text layer are not established here.",
            "text_bundled": False,
            "rights_status": RIGHTS_NOTE,
            "rights_classification": "mixed",
            "review_status": f"{corpus.get('review_status', 'Text and attribution review incomplete')} Text withheld pending rights clarification.",
            "source_ids": source_list,
            "notes": corpus.get("canon_mapping_note", "Research-text crosswalk not established."),
            "candidate_canon_id": corpus.get("candidate_canon_id"),
            "canon_mapping_state": corpus.get("canon_mapping_state", "not_mapped"),
            "canon_mapping_note": corpus.get("canon_mapping_note", "Research-text crosswalk not established."),
        })
        if corpus.get("candidate_canon_id"):
            canon_ids.add(corpus["candidate_canon_id"])
    if newly_withheld_corpora:
        registry["research_corpora"] = [
            item for item in registry.get("research_corpora", [])
            if item.get("reader_id") not in reader_ids
        ]
        registry["corpus_leads"] = sorted(
            registry.get("corpus_leads", []) + newly_withheld_corpora,
            key=lambda item: item["corpus_id"],
        )

    for lead in registry.get("edition_leads", []):
        # Normalize all Beta rights leads, including records already converted
        # to metadata-only state by an earlier build (which has removed their
        # bundled_reader_id).
        if (
            lead.get("rights_classification") == "mixed"
            and {GUIDELINES_ID, DATASET_ID}.issubset(set(lead.get("source_ids", [])))
        ):
            lead["review_status"] = _ensure_note_once(lead.get("review_status", ""), RIGHTS_NOTE)
        if lead.get("bundled_reader_id") not in reader_ids:
            continue
        lead["rights_classification"] = "mixed"
        lead["review_status"] = _ensure_note_once(lead.get("review_status", ""), RIGHTS_NOTE)
        lead["source_ids"] = sorted(
            set(lead.get("source_ids", [])) | {GUIDELINES_ID, DATASET_ID},
            key=lambda value: int(value.split("-")[1]),
        )

    for language in registry.get("languages", []):
        for layer in language.get("records", []):
            if layer.get("reader_id") not in reader_ids:
                continue
            layer["rights_classification"] = "mixed"
            layer["rights_status"] = RIGHTS_NOTE
            layer["status"] = "candidate"
            layer["reader_id"] = None
            layer["source_ids"] = sorted(
                set(layer.get("source_ids", [])) | {GUIDELINES_ID, DATASET_ID},
                key=lambda value: int(value.split("-")[1]),
            )

    withheld_by_id = {item["reader_id"]: item for item in archive.get("rights_withheld_texts", [])}
    affected_canon_ids = canon_ids | {
        item.get("canon_id") for item in withheld_by_id.values() if item.get("canon_id")
    }
    for book in archive.get("canon_registry", {}).get("books", []):
        if book.get("reader_id") not in reader_ids and book.get("canon_id") not in affected_canon_ids:
            continue
        book["reader_id"] = None
        book["reader_status"] = "Not bundled: source text withheld pending rights clarification."
        mapping_note = book.get("mapping_note", "").strip()
        while mapping_note.endswith(WITHHELD_MAPPING_NOTE):
            mapping_note = mapping_note[: -len(WITHHELD_MAPPING_NOTE)].rstrip()
        book["mapping_note"] = f"{mapping_note} {WITHHELD_MAPPING_NOTE}".strip()
        book["source_ids"] = sorted(
            set(book.get("source_ids", [])) | {GUIDELINES_ID, DATASET_ID},
            key=lambda value: int(value.split("-")[1]),
        )
    for row in archive.get("catalogue", []):
        related = any(
            row.get("catalogue_id") in book.get("catalogue_ids", [])
            and book.get("canon_id") in canon_ids
            for book in archive.get("canon_registry", {}).get("books", [])
        )
        if related:
            row["text_availability_status"] = "Not bundled: source text withheld pending rights clarification; see SRC-296–SRC-297."
            row["rights_status"] = "Mixed rights evidence; text withheld pending clarification. See SRC-296–SRC-297."
            row["evidence_source_ids"] = sorted(
                set(row.get("evidence_source_ids", [])) | {GUIDELINES_ID, DATASET_ID},
                key=lambda value: int(value.split("-")[1]),
            )
    for lead in registry.get("edition_leads", []):
        if lead.get("bundled_reader_id") not in reader_ids:
            continue
        lead.pop("bundled_reader_id", None)
        lead["review_status"] = _ensure_note_once(lead.get("review_status", ""), WITHHELD_REVIEW_NOTE)
    for reader_id, reader in matched_readers.items():
        source = next(
            (item for item in sources.values()
             if "/api/" in urlparse(item.get("url", "")).path.casefold()
             and item["source_id"] in reader.get("source_ids", [])),
            None,
        ) or next(
            item for item in sources.values()
            if _is_beta_work_source(item) and item["source_id"] in reader.get("source_ids", [])
        )
        source_digest = (reader.get("source_snapshot_sha256") or reader.get("parent_source_sha256")
                         or reader.get("source_sha256"))
        text_digest = reader.get("source_sha256") or reader.get("source_snapshot_sha256")
        withheld_by_id[reader_id] = {
            "reader_id": reader_id,
            "title": reader.get("title", reader_id),
            "display_name": reader.get("display_name", reader.get("title", reader_id)),
            "canon_id": reader.get("canon_id"),
            "candidate_canon_id": corpus_by_reader.get(reader_id, {}).get("candidate_canon_id"),
            "language_tag": reader.get("language_tag", "und"),
            "script_code": reader.get("script_code", "Zzzz"),
            "edition": reader.get("edition", ""),
            "edition_scope": reader.get("edition_scope", ""),
            "chapter_count": reader.get("chapter_count"),
            "unit_count": reader.get("unit_count"),
            "source_snapshot_sha256": source_digest,
            "withheld_text_sha256": text_digest,
            "source_ids": sorted(set(reader.get("source_ids", [])) | {GUIDELINES_ID, DATASET_ID}, key=lambda value: int(value.split("-")[1])),
            "source_url": source["url"],
            "license_id": reader.get("license_id"),
            "rights_classification": "mixed",
            "distribution_state": "withheld_pending_rights_clarification",
            "public_text_included": False,
            "rights_status": RIGHTS_NOTE,
            "verification_status": reader.get("verification_status", "Review status not recorded."),
        }
    archive["rights_withheld_texts"] = [withheld_by_id[key] for key in sorted(withheld_by_id)]
    for item in archive["rights_withheld_texts"]:
        if item.get("reader_id") in reader_ids:
            clarification = (
                "This status describes structural inspection of a preserved source snapshot before withholding; "
                "the scripture wording and reader package are not present in this public build."
            )
            item["verification_status"] = _ensure_note_once(
                item.get("verification_status", ""), clarification
            )
    archive["readers"] = [reader for reader in archive.get("readers", []) if reader.get("reader_id") not in reader_ids]
    for row in archive.get("catalogue", []):
        if set(row.get("evidence_source_ids", [])) & source_ids and row.get("catalogue_id"):
            related = any(
                row["catalogue_id"] in book.get("catalogue_ids", [])
                and book.get("canon_id") in canon_ids
                for book in archive.get("canon_registry", {}).get("books", [])
            )
            if related:
                row["evidence_source_ids"] = sorted(
                    set(row.get("evidence_source_ids", [])) | {GUIDELINES_ID, DATASET_ID},
                    key=lambda value: int(value.split("-")[1]),
                )

    if corpus_reader_ids - reader_ids:
        raise ValueError("License-audit corpus points to a reader that was not matched.")

    report = [
        "# Beta maṣāḥǝft scripture-file license audit",
        "",
        "## Evidence",
        "",
        f"The [current Beta maṣāḥǝft Guidelines]({GUIDELINES_URL}) describe data on project pages and in files, and remixes of that data, under **{GUIDELINES_LICENSE}**. The [University of Hamburg version 5.2 dataset record]({DATASET_URL}) reports dataset-level **CC BY 4.0** metadata and says each file carries specific attribution. The UHH [TEI-XML data note](https://www.fdm.uni-hamburg.de/en/uhh-data-notes/data-notes/issue-2020/dano-01-001.html) describes the dataset as CC BY-SA 4.0 and says each file carries a specific license, defaulting to CC BY-SA 4.0 when none is stated.",
        "",
        "The archived Works TEI files each state **CC BY-SA 4.0**. The current Guidelines and versioned repository metadata do not explain its precedence or the underlying printed-source rights. The archive therefore marks the affected records **mixed**, withholds their text from the public bundle, and links both provider records. It does not claim that the conflict is resolved or that the file license clears rights in the printed exemplar. Do not infer commercial or unrestricted reuse from this archive.",
        "",
        "## Withheld reader records",
        "",
        f"This audit covers {len(reader_ids)} Beta maṣāḥǝft scripture records with unresolved mixed rights notices. Their text payloads are withheld from the public package. {len(canon_ids)} distinct Church-list candidate or linked entries are affected; candidate links retain their existing provisional status.",
        "",
    ]
    report.extend(f"- `{reader_id}`" for reader_id in sorted(reader_ids))
    (ROOT / "research" / "betamasaheft-license-audit.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    request = [
        "# Draft: rights clarification request for Beta maṣāḥǝft scripture TEI files",
        "",
        "**Status:** draft only; not sent. This document records a request for clarification, not a legal conclusion or permission grant.",
        "",
        "To the Beta maṣāḥǝft project and the relevant rights holders,",
        "",
        "The Ethiopian Bible Library is assessing whether it may continue to include text derived from the pinned Works TEI files listed below in its public, offline reader and GitHub repository. Each listed TEI file contains a file-level CC BY-SA 4.0 notice. The current Beta maṣāḥǝft Guidelines describe project data and remixes under CC BY-NC-SA 4.0, while the University of Hamburg's version 5.2 data repository record lists CC BY 4.0 for the dataset and says individual files contain specific attribution. The TEI-XML data note also describes file-specific license statements. We have not inferred that any one notice overrides another.",
        "",
        "Could you please clarify the following for these exact pinned files?",
        "",
        "1. Does the CC BY-SA 4.0 notice inside each listed TEI file authorize redistribution and adaptation of that file under CC BY-SA 4.0, including the noncommercial public GitHub Pages reader and its downloadable/offline package?",
        "2. If the applicable terms are instead CC BY-NC-SA 4.0, may the archive reproduce the files and its faithful text-only extractions for noncommercial public access? What attribution, change notice, and share-alike wording is required?",
        "3. For TEI editions labeled as text of a printed EOTC Bible or digitized from modern Vulgata printed editions, does the project’s permission cover only the TEI encoding, or also the underlying printed translation/text? If the latter requires separate permission, who is the appropriate rights holder or contact?",
        "4. Does the 2022 repository-level CC BY 4.0 metadata apply only to the deposited dataset as a package, or does it affect the per-file notices?",
        "5. Are there file-specific exceptions, attribution requirements, or access conditions for any entries below?",
        "",
        "Until this is clarified, the archive records these cases as mixed and does not claim commercial or unrestricted reuse permission. The file list and SHA-256 values below identify the exact snapshots under review.",
        "",
        "## Pinned files under review",
        "",
        "| Archive reader ID | Pinned source | Source snapshot SHA-256 | Withheld reader-text SHA-256 |",
        "| --- | --- | --- | --- |",
    ]
    request.extend(
        f"| `{reader_id}` | [{url.rsplit('/', 1)[-1]}]({url}) | `{digest}` | `{text_digest}` |"
        for reader_id, url, digest, text_digest in sorted(matched_files)
    )
    request.extend([
        "",
        "## Evidence reviewed",
        "",
        f"- [Current Beta maṣāḥǝft Guidelines]({GUIDELINES_URL})",
        f"- [University of Hamburg Beta maṣāḥǝft Data version 5.2 record]({DATASET_URL})",
        "- [University of Hamburg Beta maṣāḥǝft TEI-XML Data Note](https://www.fdm.uni-hamburg.de/en/uhh-data-notes/data-notes/issue-2020/dano-01-001.html)",
        "- The exact file-specific license statements and pinned commits in the table above.",
        "",
        "Please identify the responsible copyright holder or project contact if this request is misdirected. No response or silence will be treated as permission.",
    ])
    (ROOT / "research" / "betamasaheft-rights-clarification-request.md").write_text(
        "\n".join(request) + "\n", encoding="utf-8"
    )
    total_withheld = len(archive["rights_withheld_texts"])
    print(f"Withheld {total_withheld} Beta scripture readers with unresolved mixed-rights context; retained metadata and checksums.")
    return total_withheld


if __name__ == "__main__":
    archive_path = ROOT / "archive.json"
    data = json.loads(archive_path.read_text(encoding="utf-8"))
    payload_paths = public_payload_paths(data)
    build(data)
    remove_public_payloads(payload_paths)
    write_text_atomically(archive_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
