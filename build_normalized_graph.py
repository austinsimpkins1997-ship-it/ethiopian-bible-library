"""Build the normalized graph from the archive's validated portable layer records."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


SITE_BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library"


def _id(kind: str, value: str) -> str:
    return f"{SITE_BASE}/id/{kind}/{value}"


def build_graph(site_root: Path, archive: dict, records: list[dict]) -> dict:
    """Normalize only records already in the validated, source-linked manifest."""
    if not records:
        raise ValueError("Cannot build a normalized graph without validated layer records.")

    works: dict[str, dict] = {}
    witnesses: dict[str, dict] = {}
    layers: list[dict] = []
    structures: list[dict] = []
    rights_records: list[dict] = []
    reviews: list[dict] = []
    for record in records:
        work_id = record["work_id"]
        witness = record["witness"]
        witness_id = witness["witness_id"]
        layer_id = record["record_id"]
        layer_slug = layer_id.rsplit("/", 1)[-1]
        source_ids = sorted(set(witness["source_ids"]))
        labels = record.get("labels", [])
        work = works.setdefault(work_id, {
            "id": work_id,
            "titles": [],
            "work_type": "scriptural_work",
            "source_ids": [],
        })
        for label in labels:
            mapped = {"value": label["value"], "language_tag": label["language_tag"],
                      "title_type": label.get("label_type", "preferred")}
            if mapped not in work["titles"]:
                work["titles"].append(mapped)
        work["source_ids"] = sorted(set(work["source_ids"]) | set(source_ids))

        if witness_id in witnesses:
            if witnesses[witness_id]["work_id"] != work_id:
                raise ValueError(f"Witness {witness_id} is associated with more than one work.")
            witness_record = witnesses[witness_id]
            witness_record["source_ids"] = sorted(set(witness_record["source_ids"]) | set(source_ids))
        else:
            witnesses[witness_id] = {
                "id": witness_id,
                "work_id": work_id,
                "witness_type": witness["witness_type"],
                "title": witness["title"],
                "date_statement": witness.get("date_statement"),
                "repository_or_publisher": witness.get("repository_or_publisher"),
                "identifier": witness.get("shelfmark_or_edition_id"),
                "editorial_policy": witness.get("editorial_policy"),
                "source_ids": source_ids,
            }

        structure_id = _id("structure", layer_slug)
        rights_id = _id("rights", layer_slug)
        review_ids = []
        for item in record.get("review_dimensions", []):
            review_id = _id("review", layer_slug + "-" + re.sub(r"[^a-z0-9]+", "-", item["dimension"].lower()).strip("-"))
            review_ids.append(review_id)
            method = item.get("review_method", "unknown")
            if method not in {"automated_validation", "source_inspection", "human_review", "scholarly_review", "community_review", "combined_source_and_automated_validation", "unknown"}:
                method = "unknown"
            reviews.append({
                "id": review_id,
                "layer_id": layer_id,
                "dimension": item["dimension"],
                "state": item["state"],
                "scope": item["scope"],
                "method": method,
                "reviewer": item.get("reviewer"),
                "reviewed_at": item.get("reviewed_at"),
                "process": item.get("review_process"),
                "evidence_source_ids": sorted(set(item.get("evidence_source_ids", []))),
                "notes": item.get("notes", ""),
            })

        package = dict(record["content_package"])
        package["uri"] = package["uri"].removeprefix("../")
        package.pop("format_version", None)
        origin = record["text_origin"]
        extent = record["coverage"]["extent_state"]
        extent_basis = record["coverage"]["extent_basis"]
        if extent_basis not in {"edition_contents_statement", "source_inventory", "independent_collation", "unknown"}:
            extent_basis = "unknown"
        chapter_match = re.search(r"\b(\d+)\s+(?:ordered\s+)?chapters?\b", record["coverage"].get("structure_description", ""), re.I)
        structures.append({
            "id": structure_id,
            "layer_id": layer_id,
            "unit_label": "source-labeled verse or text unit",
            "unit_count": record["coverage"].get("unit_count"),
            "extent_state": extent,
            "extent_basis": extent_basis,
            "observed_chapter_count": int(chapter_match.group(1)) if chapter_match else None,
            "missing_or_lacunose_ranges": record["coverage"].get("missing_or_lacunose_ranges", []),
            "numbering_policy": record["coverage"].get("numbering_policy", record["coverage"].get("structure_description", "Source unit boundaries are not further asserted.")),
            "source_ids": source_ids,
        })

        rights = record["rights"]
        rights_records.append({
            "id": rights_id,
            "layer_id": layer_id,
            "status": rights["status"],
            "statement": rights["statement"],
            "rights_holder": rights.get("rights_holder"),
            "license_id": rights.get("license_id"),
            "attribution_required": rights.get("attribution_required", False),
            "territory_or_term_limits": rights.get("territory_or_term_limits"),
            "distribution_decision": "include_text" if record.get("publication_state") == "bundled" and rights["status"] not in {"unknown", "all_rights_reserved", "mixed"} else "pending",
            "evidence_source_ids": sorted(set(rights.get("evidence_source_ids", []))),
        })

        access_note = record.get("community_access_note")
        layers.append({
            "id": layer_id,
            "witness_id": witness_id,
            "layer_type": record["layer_type"],
            "text_origin": origin,
            "language_tag": record["language_tag"],
            "language_name_as_recorded": record.get("language_name_as_recorded"),
            "script_code": record["script_code"],
            "basis_path": record.get("basis_path"),
            "content_package": package,
            "rights_id": rights_id,
            "structure_id": structure_id,
            "review_event_ids": review_ids,
            "source_ids": source_ids,
            "agents": [{"role": a["role"], "name": a["name"], "source_ids": a["source_ids"]} for a in record.get("agents", [])],
            "community_access": {
                "state": "not_assessed" if not access_note else "review_pending",
                "statement": access_note or "No community or custodian access review is recorded in this layer's metadata. This does not establish either permission or restriction.",
                "evidence_source_ids": [],
            },
            "publication_state": record.get("publication_state", "metadata_only"),
            "notes": record.get("additional_notes", ""),
        })

    # Bring across every bundled root reader not already represented by a
    # portable layer. The reader IDs are the matching key; source assertions
    # and provisional research candidates retain their respective states and
    # never become canon-linked reader coverage.
    represented_reader_ids: set[str] = set()
    reader_work_ids: dict[str, str] = {}
    for record in records:
        package_path = (site_root / record["content_package"]["uri"].removeprefix("../")).resolve()
        package_root = json.loads(package_path.read_text(encoding="utf-8"))
        reader_id = package_root.get("reader_id")
        if reader_id:
            represented_reader_ids.add(reader_id)
            reader_work_ids[reader_id] = record["work_id"]

    corpora_by_reader = {
        item["reader_id"]: item
        for item in archive.get("translation_registry", {}).get("research_corpora", [])
    }

    for reader in archive.get("readers", []):
        reader_id = reader["reader_id"]
        if reader_id in represented_reader_ids:
            continue
        package_path = site_root / "readers" / f"{reader_id}.json"
        if not package_path.is_file():
            raise ValueError(f"Cannot normalize bundled reader {reader_id}: its local package is not named by reader_id and no portable layer maps it.")
        package_digest = hashlib.sha256(package_path.read_bytes()).hexdigest()
        work_id = _id("work", "reader-" + reader_id)
        reader_work_ids[reader_id] = work_id
        witness_id = _id("witness", "reader-" + reader_id)
        layer_id = _id("layer", "reader-" + reader_id)
        structure_id = _id("structure", "reader-" + reader_id)
        rights_id = _id("rights", "reader-" + reader_id)
        source_ids = sorted(set(reader.get("source_ids", [])))
        language_tag = reader["language_tag"]
        text_origin = reader["text_origin"]
        title = reader.get("display_name") or reader["title"]
        research_note = ""
        if reader.get("research_corpus_id"):
            corpus = corpora_by_reader.get(reader_id, {})
            scope = reader.get("edition_scope") or reader.get("reader_scope")
            parts = [f"Research corpus ID: {reader['research_corpus_id']}"]
            if scope:
                parts.append(f"scope: {scope}")
            parts.append(corpus.get("canon_mapping_note") or "No canon candidate is assigned by the source record.")
            research_note = ". ".join(part.rstrip(". ") for part in parts if part) + "."
        works[work_id] = {
            "id": work_id,
            "titles": [{"value": reader["title"], "language_tag": "en", "title_type": "preferred"}],
            "work_type": "scriptural_work",
            "source_ids": source_ids,
            "notes": research_note,
        }
        witnesses[witness_id] = {
            "id": witness_id,
            "work_id": work_id,
            "witness_type": "digital_edition",
            "title": title,
            "date_statement": reader.get("edition"),
            "repository_or_publisher": None,
            "identifier": reader.get("publisher_book_code") or reader.get("research_corpus_id"),
            "editorial_policy": " ".join(filter(None, [reader.get("chapter_structure_note"), reader.get("editorial_signs_note"), reader.get("transcription_note")])),
            "source_ids": source_ids,
        }

        # Preserve only an explicitly named source language. Unknown Gamo
        # translation paths remain null rather than inferred from the output.
        basis_language = reader.get("basis_language_tag")
        basis_path = [basis_language, language_tag] if basis_language else None
        notes = " ".join(filter(None, [reader.get("translation_basis_note"), reader.get("additional_notes")] ))
        if text_origin == "published_translation" and not basis_path:
            notes = (notes + " Translation source language/path is not established in the available record.").strip()

        review_ids = []
        review_id = _id("review", "reader-" + reader_id + "-source-structure")
        review_ids.append(review_id)
        reviews.append({
            "id": review_id,
            "layer_id": layer_id,
            "dimension": "unit_boundaries",
            "state": "checked_with_limits",
            "scope": reader.get("verification_status", "Only the locally recorded source inventory is available; no broader completeness claim is made."),
            "method": "automated_validation",
            "reviewer": None,
            "reviewed_at": None,
            "process": "Reader structural verification recorded in the source archive metadata.",
            "evidence_source_ids": source_ids,
            "notes": "Structural extraction status is not a translation-accuracy review or proof of manuscript/edition completeness.",
        })
        if text_origin == "published_translation" and reader.get("translation_basis_status") == "unknown":
            basis_review_id = _id("review", "reader-" + reader_id + "-translation-basis")
            review_ids.append(basis_review_id)
            reviews.append({
                "id": basis_review_id,
                "layer_id": layer_id,
                "dimension": "translation_accuracy",
                "state": "unknown",
                "scope": reader.get("translation_basis_note", "Translation basis is not identified in the inspected source record."),
                "method": "source_inspection",
                "reviewer": None,
                "reviewed_at": None,
                "process": None,
                "evidence_source_ids": source_ids,
                "notes": "Unknown basis is retained as unknown; no source language or relay path is inferred.",
            })

        rights_status = reader["rights_classification"]
        rights_records.append({
            "id": rights_id,
            "layer_id": layer_id,
            "status": rights_status,
            "statement": reader.get("copyright_notice", "Rights statement not supplied in reader metadata."),
            "rights_holder": None,
            "license_id": reader.get("license_id"),
            "attribution_required": bool(reader.get("copyright_notice")),
            "territory_or_term_limits": reader.get("commercial_use"),
            "distribution_decision": "include_text" if rights_status in {"public_domain_claimed", "open_license", "permission_limited"} else "pending",
            "evidence_source_ids": source_ids,
        })
        layers.append({
            "id": layer_id,
            "witness_id": witness_id,
            "layer_type": "translation" if text_origin == "published_translation" else "source_text_transcription",
            "text_origin": text_origin,
            "language_tag": language_tag,
            "language_name_as_recorded": reader.get("language"),
            "script_code": reader["script_code"],
            "basis_path": basis_path if text_origin == "published_translation" else [language_tag],
            "content_package": {"uri": f"readers/{reader_id}.json", "media_type": "application/json", "sha256": package_digest},
            "rights_id": rights_id,
            "structure_id": structure_id,
            "review_event_ids": review_ids,
            "source_ids": source_ids,
            "agents": ([{"role": "translator", "name": reader["translator"], "source_ids": source_ids}] if reader.get("translator") and reader["translator"] != "Not identified in the cited publisher edition record" else []),
            "community_access": {
                "state": "not_assessed",
                "statement": "No community or custodian access review is recorded for this layer. This does not establish either permission or restriction.",
                "evidence_source_ids": [],
            },
            "publication_state": "bundled",
            "notes": notes,
        })
        structures.append({
            "id": structure_id,
            "layer_id": layer_id,
            "unit_label": reader.get("unit_label", "source-labeled text unit"),
            "unit_count": reader.get("unit_count"),
            "extent_state": "unknown",
            "extent_basis": "source_inventory",
            "observed_chapter_count": reader.get("chapter_count"),
            "missing_or_lacunose_ranges": [],
            "numbering_policy": reader.get("chapter_structure_note", "Source labels are preserved as provided; broader completeness is not established."),
            "source_ids": source_ids,
        })

    tradition_id = _id("tradition", "eotc")
    canon_registry = archive["canon_registry"]
    canon_entries = []
    for ordinal, book in enumerate(canon_registry["books"], start=1):
        assertions = []
        for record in records:
            for assertion in record.get("tradition_assertions", []):
                if assertion.get("canon_id") != _id("canon", book["canon_id"]):
                    continue
                assertions.append({
                    "work_id": record["work_id"],
                    "state": assertion["mapping_state"],
                    "evidence_source_ids": sorted(set(assertion["evidence_source_ids"])),
                    "notes": assertion["notes"],
                })
        for corpus in archive.get("translation_registry", {}).get("research_corpora", []):
            if corpus.get("candidate_canon_id") != book["canon_id"]:
                continue
            work_id = reader_work_ids.get(corpus.get("reader_id"))
            if not work_id or any(assertion["work_id"] == work_id for assertion in assertions):
                continue
            assertions.append({
                "work_id": work_id,
                "state": corpus.get("canon_mapping_state", "uncertain"),
                "evidence_source_ids": sorted(set(corpus.get("source_ids", [])) | set(book.get("source_ids", []))),
                "notes": corpus.get("canon_mapping_note", "Provisional research-reader candidate; exact mapping remains unresolved."),
            })
        canon_entries.append({
            "id": _id("canon-entry", book["canon_id"]),
            "ordinal": ordinal,
            "source_label": book["source_label"],
            "group_label": book["section"],
            "work_assertions": assertions,
            "evidence_source_ids": sorted(set(book["source_ids"])),
        })

    canon_sources = sorted({canon_registry["source_id"], *canon_registry.get("context_source_ids", [])})
    all_records = [*works.values(), *witnesses.values(), *layers, *structures, *rights_records, *reviews]
    all_records.extend([{
        "source_ids": canon_sources,
        "entries": canon_entries,
    }])
    referenced_sources: set[str] = set()

    def collect_sources(value: object) -> None:
        if isinstance(value, dict):
            for key in ("source_ids", "evidence_source_ids"):
                if isinstance(value.get(key), list):
                    referenced_sources.update(value[key])
            for child in value.values():
                collect_sources(child)
        elif isinstance(value, list):
            for child in value:
                collect_sources(child)

    collect_sources(all_records)
    source_registry = {source["source_id"]: source for source in archive.get("sources", [])}
    missing_source_metadata = referenced_sources - set(source_registry)
    if missing_source_metadata:
        raise ValueError(f"Normalized graph source metadata is missing: {sorted(missing_source_metadata)}")
    citations = []
    for source_id in sorted(referenced_sources):
        source = source_registry[source_id]
        inspection = source.get("inspection_and_limitations", "")
        checked_match = re.match(r"^(?:Inspected|Checked|Reviewed)(?: on)?\s+(\d{4}-\d{2}-\d{2})\b", inspection)
        citations.append({
            "id": _id("citation", source_id),
            "source_id": source_id,
            "supports_claim": inspection or source.get("source_name", "Source record linked by archive metadata."),
            "locator": source.get("url"),
            "checked_at": checked_match.group(1) if checked_match else None,
        })
    eritrea_transcription_path = site_root / "research" / "eritrea-canon-source-transcription.json"
    eritrea_transcription = json.loads(eritrea_transcription_path.read_text(encoding="utf-8"))
    if eritrea_transcription.get("record_type") != "institutional_webpage_list_transcription":
        raise ValueError("Eritrean page list must remain identified as a transcription of an institutional webpage.")
    eritrea_source_ids = [eritrea_transcription["source_id"]]
    eritrea_tradition_id = _id("tradition", "eritrean-orthodox-tewahdo")
    eritrea_canon_entries = []
    page_ordinal = 0
    for group, section in eritrea_transcription["counts_as_numbered_by_page"].items():
        if not isinstance(section, dict):
            continue
        entries = section["entries"]
        if len(entries) != section["count"]:
            raise ValueError(f"Eritrean page transcription count mismatch for {group}.")
        for source_label in entries:
            page_ordinal += 1
            eritrea_canon_entries.append({
                "id": _id("canon-entry", f"eritrea-diocese-page-{page_ordinal:02d}"),
                "ordinal": page_ordinal,
                "source_label": source_label,
                "group_label": group,
                "work_assertions": [],
                "evidence_source_ids": eritrea_source_ids,
            })
    if page_ordinal != eritrea_transcription["counts_as_numbered_by_page"].get("total_numbered_entries"):
        raise ValueError(f"Eritrean page transcription has {page_ordinal} numbered labels; expected its reported 81.")
    if eritrea_source_ids[0] not in {item["source_id"] for item in citations}:
        source = source_registry[eritrea_source_ids[0]]
        inspection = source.get("inspection_and_limitations", "")
        checked_match = re.match(r"^(?:Inspected|Checked|Reviewed)(?: on)?\s+(\d{4}-\d{2}-\d{2})\b", inspection)
        citations.append({
            "id": _id("citation", eritrea_source_ids[0]),
            "source_id": eritrea_source_ids[0],
            "supports_claim": inspection or source.get("source_name", "Source record linked by archive metadata."),
            "locator": source.get("url"),
            "checked_at": checked_match.group(1) if checked_match else None,
        })
    return {
        "schema_version": 1,
        "package_id": _id("package", "selected-registered-layers-v1"),
        "scope_state": "bounded_collection",
        "scope_note": (
            f"Normalized graph generated from {len(records)} validated portable records plus every additional bundled root reader "
            f"with an explicitly named local package, covering {len(layers)} distinct text layers. It carries the archive's 81-entry English EOTC list "
            "as a cited list, not as an independent canon determination. It also includes a separate transcription of the 81 numbered labels on an Eritrean Orthodox Diocese page; that page list is not an independently established synodical canon, and no EOTC–Eritrean work crosswalk is inferred. Only documented crosswalk assertions are included; "
            "unmapped identities and verse-level alignments remain unresolved. It is not a complete scripture collection, "
            "complete language coverage, or a claim that all layer texts are accurate or complete."
        ),
        "traditions": [
            {"id": tradition_id, "labels": [{"value": "Ethiopian Orthodox Tewahedo Church", "language_tag": "en", "title_type": "preferred"}], "source_ids": canon_sources, "notes": "A tradition label for the cited English list; no claim is made that the list settles all community canon usage."},
            {"id": eritrea_tradition_id, "labels": [{"value": eritrea_transcription["tradition_label"], "language_tag": "en", "title_type": "preferred"}], "source_ids": eritrea_source_ids, "notes": "The cited page is hosted by the Eritrean Orthodox Tewahdo Church Diocese of the U.S.A. and Canada. Its 81 numbered labels are transcribed as that page presents them; the page cites the Ethiopian Church list and Wikipedia. This record does not establish a synod-approved Eritrean canon or an equivalence with the Ethiopian list."},
        ],
        "canons": [{
            "id": _id("canon", "eotc-english-list"),
            "tradition_id": tradition_id,
            "title": {"value": "Church-cited English 81-entry list", "language_tag": "en", "title_type": "preferred"},
            "entries_scope": "full_list",
            "entries": canon_entries,
            "source_ids": canon_sources,
            "scope_note": "Full reproduction of the archive's cited 81-entry English list and its 46/35 headings. This is completeness relative to that source list only, not a universal or independently adjudicated canon.",
        }, {
            "id": _id("canon", "eritrea-diocese-english-page-list"),
            "tradition_id": eritrea_tradition_id,
            "title": {"value": "Eritrean Orthodox Diocese page: numbered English list transcription", "language_tag": "en", "title_type": "preferred"},
            "entries_scope": "full_list",
            "entries": eritrea_canon_entries,
            "source_ids": eritrea_source_ids,
            "scope_note": "Complete transcription of the 81 numbered Old Testament and New Testament labels shown on the cited Eritrean Orthodox Church Diocese webpage, preserving page spelling, order, grouping, and its final slash-separated label. This describes the webpage only; it is not a determination of the Eritrean Church's official canon, a manuscript or printed Bible contents list, or a crosswalk to the Ethiopian Church list. The webpage itself cites the Ethiopian Church list and Wikipedia.",
        }],
        "works": sorted(works.values(), key=lambda item: item["id"]),
        "witnesses": sorted(witnesses.values(), key=lambda item: item["id"]),
        "layers": sorted(layers, key=lambda item: item["id"]),
        "structures": sorted(structures, key=lambda item: item["id"]),
        "alignments": [],
        "citations": sorted(citations, key=lambda item: item["source_id"]),
        "rights": sorted(rights_records, key=lambda item: item["id"]),
        "review_events": sorted(reviews, key=lambda item: item["id"]),
    }


def write_graph(site_root: Path, archive: dict, records: list[dict]) -> Path:
    graph = build_graph(site_root, archive, records)
    path = site_root / "examples" / "archive-graph-registered-layers.json"
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
