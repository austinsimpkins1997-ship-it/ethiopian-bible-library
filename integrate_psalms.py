"""Integrate the locally audited Psalter reader into archive registries."""
import json
import hashlib
from pathlib import Path
from archive_manifest import write_text_atomically
from coverage_summary import build_coverage_statement

root = Path(__file__).resolve().parent
archive_path = root / "archive.json"
translation_path = root / "translation-registry.json"
archive = json.loads(archive_path.read_text(encoding="utf-8"))
translation = json.loads(translation_path.read_text(encoding="utf-8"))
reader = json.loads((root / "readers" / "psalms-geez-ludolf.json").read_text(encoding="utf-8"))

source = {
    "source_id": "SRC-069",
    "source_name": "University of Tel Aviv - Locally preserved 151-page Ethiopic Psalter capture",
    "url": "readers/source/psalms-tau-2015/SOURCE-CAPTURE.json",
    "inspection_and_limitations": "Local capture manifest enumerates 151 downloaded TAU Rahlfs-numbered page HTML files, their source URLs, and SHA-256 digests. Structural extraction confirms page titles and numbered nonempty text units, not line-by-line transcription accuracy, physical-edition completeness, or an exact Church-list crosswalk. The pages retain the source's numbering irregularities. Reuse remains subject to the TAU digitizer's noncommercial notice; see SRC-036 and the local SOURCE-NOTICE.txt.",
    "archive_status": "Full local page capture; extraction structurally audited with explicit text and rights limits",
}
if not any(s["source_id"] == source["source_id"] for s in archive["sources"]):
    archive["sources"].append(source)

book = next(x for x in archive["catalogue"] if x["catalogue_id"] == "eotc-027")
english_companion = reader.get("parallel_translation")
if english_companion:
    book.update({
        "chapter_count": "151 ordered chapters in the archived Brenton USFM witness; the accompanying Geʽez source is a 151-page TAU sequence",
        "chapter_order_status": "The archived Brenton source has 151 ordered chapter markers and the Geʽez reader preserves 151 ordered TAU page titles. Their numbering systems and contents are separate witnesses; exact textual alignment is unverified.",
        "text_availability_status": "Geʽez TAU transcription of Ludolf's Ethiopic Psalter plus Brenton's historical English translation of the Greek Septuagint; English is not translated from the bundled Geʽez witness.",
        "completeness_status": f"The locally archived digital witnesses contain 151 source sections each. Brenton has {english_companion['unit_count']} English verse labels and {english_companion.get('continuation_segment_count', 0)} preserved unnumbered continuation segments; the Geʽez capture has 2,537 numbered or marked units. This is a source-inventory count, not proof of completeness against print editions, manuscripts, or a Church edition.",
        "reviewer_notes": "The English companion preserves USFM paragraph starts, descriptive-title markers, footnotes, cross-references, and visible brackets for translator-supplied words. English and Geʽez are independent witnesses; the unique-label display is navigational only. Chapter numbering, wording accuracy, edition completeness, and exact Church-list crosswalk remain unverified.",
    })
    book["evidence_source_ids"] = list(dict.fromkeys(book["evidence_source_ids"] + ["SRC-069", "SRC-142"]))
else:
    book.update({
        "chapter_count": "151 source pages in the Rahlfs-numbered TAU online sequence; not a claim about manuscript or canon boundaries",
        "chapter_order_status": "Local structural audit confirms all 151 ordered page titles and nonempty numbered units. Source numbering anomalies are retained; no independent collation.",
        "text_availability_status": "Geʽez reader bundled locally: TAU transcription of Ludolf's Ethiopic Psalter, with source page links and per-page SHA-256 digests. No English or Latin text is bundled.",
        "completeness_status": "The 151-page online sequence is locally captured. Independent completeness against Ludolf's print edition, manuscripts, and Church-list mapping is not established.",
        "reviewer_notes": "The source reader preserves 151 TAU Rahlfs-numbered pages and 2,537 source-numbered units. Duplicate, skipped, and nonnumeric markers found in the source were retained rather than normalized. TAU warns that new transcription typos may remain. The local audit verifies page sequence and extracted structure only; it does not collate wording against the 1701 print or manuscripts. TAU's noncommercial permission notice accompanies the local copy. The Church-list crosswalk remains title-level navigation, not independent canonical/textual proof.",
    })
    book["evidence_source_ids"] = list(dict.fromkeys(book["evidence_source_ids"] + ["SRC-069"]))

for reg in (translation,):
    geez = next(item for item in reg["languages"] if item["language_tag"] == "gez")
    geez["records"] = [record for record in geez["records"] if record.get("reader_id") != reader["reader_id"]]
    geez["records"].append({
        "canon_id": reader["canon_id"], "reader_id": reader["reader_id"],
        "layer_role": "source_text_transcription", "status": "bundled",
        "basis_language_tag": "gez",
        "basis_description": "TAU-hosted retyped Geʽez transcription of Ludolf's 1701 Psalter, presented in 151 Rahlfs-numbered pages. Source markers are preserved including irregularities; no independent collation.",
        "rights_status": "noncommercial_with_required_notice",
        "rights_classification": "permission_limited",
        "source_ids": reader["source_ids"],
    })
    reg["corpus_leads"] = [lead for lead in reg.get("corpus_leads", []) if lead.get("corpus_id") != "ethiopic-psalter-ludolf-1701"]
    reg["coverage_statement"] = build_coverage_statement(reg, archive.get("canon_registry"))
geez["source_ids"] = list(dict.fromkeys(geez["source_ids"] + ["SRC-067", "SRC-068", "SRC-069"]))
archive["translation_registry"] = translation
write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
translation_path.write_text(json.dumps(translation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
capture_dir = root / "readers" / "source" / "psalms-tau-2015"
capture = {
    "source_name": source["source_name"],
    "captured_at": "2026-10-24",
    "source_page_count": 151,
    "numbering_system": "TAU page sequence using Rahlfs Septuagint numbering by default; Ludolf numbering remains available on the source site.",
    "rights_notice_file": "SOURCE-NOTICE.txt",
    "pages": [
        {
            "file": path.name,
            "source_url": f"https://www.tau.ac.il/~hacohen/Psalm/PsalmNrR%20{i}.html",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for i, path in enumerate(sorted(capture_dir.glob("PsalmNrR-*.html")), 1)
    ],
}
(capture_dir / "SOURCE-CAPTURE.json").write_text(json.dumps(capture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
reader_path = root / "readers" / "psalms-geez-ludolf.json"
reader_hash = hashlib.sha256(reader_path.read_bytes()).hexdigest()
layer_id = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/psalms-geez-ludolf-hacohen"
layer_sources = reader["source_ids"]
layer = {
    "schema_version": 2,
    "record_id": layer_id,
    "work_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/ethiopic-psalter",
    "labels": [{"value": "Psalms — Geʽez Ludolf/HaCohen transcription", "language_tag": "en", "label_type": "preferred"}],
    "tradition_assertions": [{
        "tradition_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/tradition/eotc",
        "canon_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/canon/eotc-ot-23",
        "mapping_state": "uncertain", "evidence_source_ids": ["SRC-029", "SRC-067", "SRC-068"],
        "notes": "The archive's navigation associates this Psalter with the Church list's Psalms entry; exact textual and canonical crosswalk is not independently established."
    }],
    "witness": {
        "witness_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/witness/psalms-ludolf-1701-hacohen-transcription",
        "witness_type": "transcription", "title": "Geʽez text of Hiob Ludolf's 1701 Ethiopic Psalter, digitized and retyped by Ran HaCohen",
        "date_statement": "1701 printed edition; digital transcription date not established here",
        "repository_or_publisher": "Tel Aviv University source site; local archival capture by Ethiopian Bible Library",
        "shelfmark_or_edition_id": "Psalterium Davidis aethiopice et latine, Frankfurt am Main, 1701",
        "editorial_policy": "Uses the TAU Rahlfs-numbered page sequence. Source page text and numbering anomalies are preserved. No independent collation.",
        "source_ids": ["SRC-036", "SRC-058", "SRC-059", "SRC-067", "SRC-068", "SRC-069"]
    },
    "layer_type": "source_text_transcription", "text_origin": "source_transcription", "language_tag": "gez", "language_name_as_recorded": "Geʽez (Classical Ethiopic)",
    "script_code": "Ethi", "basis_path": ["gez"], "agents": [
        {"role": "editor", "name": "Hiob Ludolf", "authority_or_affiliation": "1701 edition", "source_ids": ["SRC-067", "SRC-068"]},
        {"role": "digitizer", "name": "Ran HaCohen", "authority_or_affiliation": "Tel Aviv University source site", "source_ids": ["SRC-036", "SRC-058", "SRC-059", "SRC-068"]}
    ],
    "content_package": {"uri": "../readers/psalms-geez-ludolf.json", "media_type": "application/json", "sha256": reader_hash, "format_version": "1"},
    "coverage": {
        "extent_state": "complete_for_declared_edition", "extent_basis": "source_inventory", "unit_count": reader["unit_count"],
        "structure_description": "151 ordered TAU Rahlfs-numbered pages with 2,537 extracted nonempty numbered units; headings retained where separable.",
        "missing_or_lacunose_ranges": [],
        "supplements_and_editorial_signs": "Source label gaps, duplicates, and nonnumeric markers are retained as found; 10 pages contain non-consecutive, duplicate, or nonnumeric labels. No attempt was made to restore text or labels.",
        "numbering_policy": "Preserves the TAU page sequence and marker labels exactly as parsed; these are source labels, not a newly asserted canonical verse system."
    },
    "rights": {
        "status": "permission_limited",
        "statement": "The digitizer permits noncommercial copying/distribution only when copyright and permission notices accompany every copy. Other use requires contacting the copyright owner. This archive carries that notice; it grants no commercial rights.",
        "license_id": None, "rights_holder": "Ran HaCohen (digitized Ethiopic text notice)", "attribution_required": True,
        "territory_or_term_limits": "Commercial use is not granted. For other uses, contact the copyright owner as instructed by the source.",
        "evidence_source_ids": ["SRC-036", "SRC-068", "SRC-069"]
    },
    "review_dimensions": [
        {"dimension": "identity", "state": "checked_with_limits", "scope": "TAU source index and notes identify the Ludolf 1701 Ethiopic Psalter and HaCohen transcription.", "reviewer": None, "review_method": "source_inspection", "review_process": "Archive metadata review", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-067", "SRC-068"]},
        {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "151 ordered page titles and nonempty numbered units in local capture.", "reviewer": None, "review_method": "automated_validation", "review_process": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-069"]},
        {"dimension": "unit_boundaries", "state": "checked_with_limits", "scope": "HTML marker-span structure was extracted; verse wording was not independently compared to print.", "reviewer": None, "review_method": "automated_validation", "review_process": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-069"]},
        {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No independent collation against the 1701 print or manuscript witnesses.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-068"]},
        {"dimension": "completeness", "state": "checked_with_limits", "scope": "The full 151-page local sequence was captured; completeness against print or manuscript witnesses is unknown.", "reviewer": None, "review_method": "automated_validation", "review_process": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-069"]},
        {"dimension": "rights", "state": "checked_with_limits", "scope": "Source notice and required noncommercial attribution are included with each archive copy.", "reviewer": None, "review_method": "source_inspection", "review_process": "Digitizer notice and archive-copy review", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-036", "SRC-068", "SRC-069"]}
    ],
    "publication_state": "bundled", "community_access_note": None,
    "additional_notes": "Geʽez source transcription, not an English translation. Source warnings about possible new typos remain applicable."
}
(root / "examples" / "psalms-geez-layer.json").write_text(json.dumps(layer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Integrated Psalter metadata, source capture, and Ge'ez language record.")
