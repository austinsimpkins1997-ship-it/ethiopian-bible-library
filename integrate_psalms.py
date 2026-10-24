"""Integrate the locally audited Psalter reader into archive registries."""
import json
import hashlib
from pathlib import Path

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
        "source_ids": reader["source_ids"],
    })
    reg["corpus_leads"] = [lead for lead in reg.get("corpus_leads", []) if lead.get("corpus_id") != "ethiopic-psalter-ludolf-1701"]
    reg["coverage_statement"] = "This prototype records bundled Geʽez source transcriptions/editions for Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Joshua, Judges, Ruth, Psalms, Jubilees, and 1 Enoch, plus a historical Greek-to-English Genesis companion. It also records scoped Eritrean language/script profiles and unbundled Bible corpus leads. Tigrinya, Tigre, Kunama, Blin, and Saho leads are not bundled and do not establish Eritrean Orthodox canon coverage. Script profiles reflect dated cited sources and may vary by region and witness. Eleven of the EOTC English list’s 81 entries have bundled reader text; this is not global language or canon coverage."
geez["source_ids"] = list(dict.fromkeys(geez["source_ids"] + ["SRC-067", "SRC-068", "SRC-069"]))
archive["translation_registry"] = translation
archive_path.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    "schema_version": 1,
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
    "layer_type": "source_text_transcription", "language_tag": "gez", "language_name_as_recorded": "Geʽez (Classical Ethiopic)",
    "script_code": "Ethi", "basis_path": ["gez"], "agents": [
        {"role": "editor", "name": "Hiob Ludolf", "authority_or_affiliation": "1701 edition", "source_ids": ["SRC-067", "SRC-068"]},
        {"role": "digitizer", "name": "Ran HaCohen", "authority_or_affiliation": "Tel Aviv University source site", "source_ids": ["SRC-036", "SRC-058", "SRC-059", "SRC-068"]}
    ],
    "content_package": {"uri": "../readers/psalms-geez-ludolf.json", "media_type": "application/json", "sha256": reader_hash, "format_version": "1"},
    "coverage": {
        "extent_state": "complete_for_declared_edition", "extent_basis": "source_inventory", "unit_count": reader["verse_marker_count"],
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
        {"dimension": "identity", "state": "checked_with_limits", "scope": "TAU source index and notes identify the Ludolf 1701 Ethiopic Psalter and HaCohen transcription.", "reviewer": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-067", "SRC-068"]},
        {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "151 ordered page titles and nonempty numbered units in local capture.", "reviewer": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-069"]},
        {"dimension": "unit_boundaries", "state": "checked_with_limits", "scope": "HTML marker-span structure was extracted; verse wording was not independently compared to print.", "reviewer": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-069"]},
        {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No independent collation against the 1701 print or manuscript witnesses.", "reviewer": None, "reviewed_at": None, "evidence_source_ids": ["SRC-068"]},
        {"dimension": "completeness", "state": "checked_with_limits", "scope": "The full 151-page local sequence was captured; completeness against print or manuscript witnesses is unknown.", "reviewer": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-069"]},
        {"dimension": "rights", "state": "checked_with_limits", "scope": "Source notice and required noncommercial attribution are included with each archive copy.", "reviewer": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-036", "SRC-068", "SRC-069"]}
    ],
    "publication_state": "bundled", "community_access_note": None,
    "additional_notes": "Geʽez source transcription, not an English translation. Source warnings about possible new typos remain applicable."
}
(root / "examples" / "psalms-geez-layer.json").write_text(json.dumps(layer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Integrated Psalter metadata, source capture, and Geʽez language record.")
