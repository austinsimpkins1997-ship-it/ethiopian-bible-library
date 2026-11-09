"""Bundle Brenton's English Job as a separately scoped research reader."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import zipfile
from pathlib import Path

import build_brenton_octateuch as brenton
from coverage_summary import build_coverage_statement
from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
CODE = "JOB"
MEMBER = "19-JOBeng-Brenton.usfm"
SLUG = "job-brenton-lxx-1851"
READER_ID = "job-brenton-lxx-1851-research"
CORPUS_ID = "brenton-job-lxx-1851"
TRANSLATION_ID = "job-english-brenton-lxx-1851"
CANON_ID = "eotc-ot-22"
SOURCE_IDS = ["SRC-029", "SRC-038", "SRC-142", "SRC-143", "SRC-146"]
READER_PATH = ROOT / "readers" / f"{SLUG}.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_job_member(raw: bytes, package_hash: str) -> dict:
    previous = brenton.BOOKS.get(CODE)
    brenton.BOOKS[CODE] = (SLUG, 22, "Job", 42)
    try:
        return brenton.parse_usfm(raw, CODE, MEMBER, package_hash)
    finally:
        if previous is None:
            brenton.BOOKS.pop(CODE, None)
        else:
            brenton.BOOKS[CODE] = previous


def build() -> dict:
    package = brenton.PACKAGE.read_bytes()
    package_hash = sha256(package)
    with zipfile.ZipFile(brenton.PACKAGE) as archive_zip:
        raw = archive_zip.read(MEMBER)
    companion = parse_job_member(raw, package_hash)
    if companion["chapter_count"] != 42 or companion["unit_count"] != 1082:
        raise ValueError("The archived Job member no longer matches its observed 42-chapter, 1,082-label inventory.")

    manifest = json.loads(brenton.MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("archive_sha256") != package_hash:
        raise ValueError("Brenton package hash does not match the capture manifest.")
    manifest.setdefault("selected_members", {})[MEMBER] = {
        "sha256": sha256(raw),
        "byte_length": len(raw),
    }
    manifest["scope"] = (
        "Seven source package members are used: Psalms, Leviticus, Numbers, Deuteronomy, Joshua, and Judges "
        "as English companions, plus Job as a separately scoped English research reader. Other package members "
        "remain unimported until their structure and catalogue relationship are assessed."
    )
    brenton.MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reader = {
        "reader_id": READER_ID,
        "research_corpus_id": CORPUS_ID,
        "reader_scope": "research_witness_uncertain_catalogue_mapping",
        "title": "Job — Brenton Septuagint English (1851)",
        "display_name": "Research reader — Job (Brenton English Septuagint, 1851)",
        "text_origin": "published_translation",
        "translation_id": TRANSLATION_ID,
        "language": "English",
        "language_tag": "en",
        "script_code": "Latn",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_language_tag": "grc",
        "translation_path": ["grc", "en"],
        "translation_basis_status": "established",
        "translation_basis_note": "eBible.org identifies Brenton's 1851 English translation as from the Greek Septuagint; the edition title specifies the Vatican Text. This records the edition-stated Greek-to-English basis, not an independently audited translator workflow, textual accuracy, or alignment to Geʽez.",
        "edition": "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851).",
        "edition_scope": "Historical English translation of the Greek Septuagint. It is a related English research witness, not a Geʽez transcription, an EOTC printed-edition claim, or a verified translation of a specific Geʽez witness.",
        "chapter_count": companion["chapter_count"],
        "unit_count": companion["unit_count"],
        "unit_label": "English verse labels observed in the archived USFM member",
        "verse_marker_count": companion["unit_count"],
        "section_label": "Chapter",
        "chapter_structure_note": (
            "The selected archived eBible.org USFM member contains 42 ordered chapter markers, 1,082 numbered "
            "verse labels, and 2 unnumbered continuation segments. These are observed package counts; they do not "
            "prove completeness against the 1851 printed edition, the Greek Septuagint, a Geʽez witness, or a Church edition."
        ),
        "transcription_note": "Reader wording is parsed from the archived USFM member; it has not been collated against the printed 1851 edition or the Greek source.",
        "editorial_signs_note": "USFM \\add translator-supplied words are displayed in visible archival brackets. Footnotes, cross-references, paragraph starts, descriptive titles, and unnumbered continuation segments are preserved as separate structural data.",
        "source_ids": SOURCE_IDS,
        "source_pages": f"readers/source/brenton-septuagint/{MEMBER} (member of the locally archived package)",
        "source_package_sha256": package_hash,
        "source_member_sha256": sha256(raw),
        "rights_classification": "public_domain_claimed",
        "copyright_notice": "eBible.org identifies Brenton's 1851 English translation as public domain. This archive records the provider's statement, not a worldwide legal determination; other source layers and website design have separate rights.",
        "commercial_use": "The provider identifies the 1851 translation as public domain. This is a provider-reported status and not jurisdiction-specific legal advice or a rights determination for other materials.",
        "verification_status": (
            f"A local parser checked the archived member checksum, {companion['chapter_count']} ordered chapters, "
            f"{companion['unit_count']} nonempty verse labels, {companion['continuation_segment_count']} preserved "
            "continuation segments, and source markup. This confirms extraction structure only. No independent collation "
            "against the printed edition or Greek Septuagint was performed; wording accuracy, print-edition completeness, "
            "and the exact relationship to the Ethiopian Orthodox Church list remain unverified. It is not a "
            "canon-linked EOTC reader and is not counted as an EOTC canon reader or toward canon reader coverage."
        ),
        "chapters": companion["chapters"],
    }
    READER_PATH.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    example = brenton.make_layer(SLUG, "Job", CANON_ID, companion, READER_PATH.name)
    example["record_id"] = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/{TRANSLATION_ID}"
    example["work_id"] = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/{SLUG}"
    example["tradition_assertions"][0].update({
        "mapping_state": "uncertain",
        "evidence_source_ids": ["SRC-029", "SRC-146"],
        "notes": "The EOTC English list has a Job entry and eBible.org identifies this digital text as Brenton's Greek Septuagint Job. The relationship is a title-level candidate only; it does not establish identity with a Geʽez witness or current Church edition.",
    })
    example["witness"]["title"] = reader["title"]
    example["witness"]["source_ids"] = SOURCE_IDS
    example["witness"]["editorial_policy"] = reader["editorial_signs_note"]
    example["content_package"].update({"uri": f"../readers/{READER_PATH.name}", "json_pointer": ""})
    example["coverage"].update({
        "unit_count": companion["unit_count"],
        "structure_description": "The archived eBible.org USFM member contains 42 ordered chapter divisions, 1,082 numbered labels, and two unnumbered continuation segments. These are counts from the selected digital member, not proof of printed-edition completeness.",
        "supplements_and_editorial_signs": "Footnotes, cross-references, paragraph starts, descriptive titles, translator-added words in visible archival brackets, and two unnumbered continuation segments are preserved.",
        "numbering_policy": "Source chapter and verse labels are preserved as strings, including appended letters. No missing label is synthesized; label matches do not establish alignment to a Geʽez text.",
    })
    example["rights"]["evidence_source_ids"] = ["SRC-038", "SRC-142"]
    for review in example["review_dimensions"]:
        review["evidence_source_ids"] = SOURCE_IDS
    example["additional_notes"] = reader["verification_status"]
    example_path = ROOT / "examples" / "job-brenton-translation-layer.json"
    example_path.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(example_path, READER_PATH)

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    source = {
        "source_id": "SRC-143",
        "source_name": "Local Brenton Job USFM member capture",
        "url": "readers/source/brenton-septuagint/capture-manifest.json",
        "inspection_and_limitations": (
            f"Records the selected {MEMBER} package member's {len(raw)} bytes and SHA-256 {sha256(raw)}. "
            "The archive parser observes 42 ordered chapters, 1,082 numbered labels, and 2 unnumbered continuation "
            "segments. These package checks do not establish print-edition completeness, translation accuracy, or exact "
            "mapping to an Ethiopian Orthodox Church edition."
        ),
        "archive_status": "One Brenton Job member retained and parsed as a separate English research reader; crosswalk and textual accuracy unverified",
    }
    sources = archive.setdefault("sources", [])
    existing = next((item for item in sources if item.get("source_id") == source["source_id"]), None)
    if existing is None:
        sources.append(source)
    elif existing != source:
        raise ValueError("SRC-143 conflicts with a different existing source record.")
    page_source = {
        "source_id": "SRC-146",
        "source_name": "eBible.org — Brenton Septuagint Job chapter index and chapter 42",
        "url": "https://ebible.org/eng-Brenton/JOB.htm",
        "inspection_and_limitations": "The provider index lists chapter pages 1–42, and page 42 displays the final chapter and its lettered continuation labels. This boundary evidence was inspected online; the reader wording itself comes from the separately checksummed local USFM member. No complete-page collation or print-edition/Greek accuracy review is claimed.",
        "archive_status": "Job index and final chapter inspected for source chapter scope; full wording remains separately tied to the local USFM member",
    }
    existing_page = next((item for item in sources if item.get("source_id") == "SRC-146"), None)
    if existing_page and existing_page.get("source_name") != page_source["source_name"]:
        raise ValueError("SRC-146 conflicts with a different source record.")
    if existing_page:
        sources[sources.index(existing_page)] = page_source
    else:
        sources.append(page_source)
    archive["sources"].sort(key=lambda item: int(item["source_id"].split("-")[1]))
    job_entry = next(item for item in archive["catalogue"] if item.get("display_name", "").casefold() == "job")
    job_entry.update({
        "text_availability_status": "A separate Brenton English translation from Greek is bundled as a research reader; no canon-linked Geʽez source-text reader is bundled for this entry.",
        "completeness_status": "The archived English USFM member contains 42 ordered chapters, 1,082 verse labels, and 2 continuation segments. This observed digital-package inventory does not establish printed-edition completeness, translation accuracy, or equivalence to an EOTC witness.",
        "rights_status": "eBible.org identifies the 1851 Brenton English translation as public domain. This provider claim is recorded separately from rights in other witnesses and source materials.",
        "reviewer_notes": "A separate research reader provides the English Brenton Septuagint (Greek basis). The EOTC title-level candidate relationship is provisional; no Geʽez translation, current EOTC edition, printed-source collation, or translation accuracy claim is made.",
    })
    job_entry["evidence_source_ids"] = list(dict.fromkeys(job_entry.get("evidence_source_ids", []) + SOURCE_IDS))
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    english = next(item for item in registry["languages"] if item["language_tag"] == "en")
    english["records"] = [item for item in english["records"] if item.get("translation_id") != TRANSLATION_ID]
    english["records"].append({
        "canon_id": CANON_ID,
        "reader_id": READER_ID,
        "translation_id": TRANSLATION_ID,
        "layer_role": "historical_companion_translation",
        "status": "bundled",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_language_tag": "grc",
        "basis_description": "Brenton's 1851 English translation is based on Greek; it is not a direct translation from an accompanying Geʽez witness.",
        "rights_status": "public_domain_per_cited_source",
        "rights_classification": "public_domain_claimed",
        "source_ids": SOURCE_IDS,
        "translation_path": ["grc", "en"],
    })
    english["records"].sort(key=lambda item: (item["canon_id"], item.get("translation_id", "")))
    english["source_ids"] = sorted(set(english.get("source_ids", [])) | set(SOURCE_IDS))
    registry["research_corpora"] = [item for item in registry.get("research_corpora", []) if item.get("corpus_id") != CORPUS_ID]
    registry["research_corpora"].append({
        "corpus_id": CORPUS_ID,
        "title": reader["title"],
        "reader_id": READER_ID,
        "unit_count": reader["unit_count"],
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": CANON_ID,
        "canon_mapping_note": "Title-level candidate only. Brenton's English translation represents the Greek Septuagint; this record does not establish that its textual scope is identical to an Ethiopian Orthodox Church witness or edition. It is excluded from canon-linked reader coverage.",
        "language_description": "English translation (en), translated from Greek (grc).",
        "script_description": "Latin script (Latn) for this digital English witness.",
        "unit_summary": "1,082 English verse labels and 2 preserved unnumbered continuation segments observed in 42 ordered USFM chapter divisions; package inventory only.",
        "rights_classification": "public_domain_claimed",
        "rights_status": reader["copyright_notice"],
        "review_status": reader["verification_status"],
        "source_ids": SOURCE_IDS,
        "text_origin": "published_translation",
        "language_tag": "en",
        "script_code": "Latn",
        "basis_language_tag": "grc",
        "translation_path": ["grc", "en"],
        "translation_basis_status": "established",
        "translation_basis_note": "eBible.org identifies Brenton's 1851 English translation as from the Greek Septuagint; the edition title specifies the Vatican Text. This records the edition-stated Greek-to-English basis, not an independently audited translator workflow, textual accuracy, or alignment to Geʽez.",
        "translation_basis_source_ids": ["SRC-142"],
        "translation_id": TRANSLATION_ID,
        "translator": reader["translator"],
        "edition_statement": reader["edition"],
    })
    registry["research_corpora"].sort(key=lambda item: item["corpus_id"])
    canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    registry["coverage_statement"] = build_coverage_statement(registry, canon)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Keep the package provenance record synchronized with the now seven selected members.
    source_record = next(item for item in archive["sources"] if item.get("source_id") == "SRC-142")
    source_record["inspection_and_limitations"] = (
        f"eBible.org identifies Sir Lancelot Charles Lee Brenton's translation as an English translation from the Greek Septuagint, published in 1851, and reports it as public domain. The archived USFM zip (SHA-256 {package_hash}) contains the selected members recorded in readers/source/brenton-septuagint/capture-manifest.json, including Job. Local parsing checks structure and extraction only; wording, print completeness, and alignment to Geʽez remain unverified. The rights statement is a provider claim, not a worldwide legal determination."
    )
    source_record["archive_status"] = "Full source package stored; six selected English companions and a separately scoped Job research reader are bundled with explicit limits"
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    print(f"Built separate Brenton Job research reader: {reader['chapter_count']} chapters, {reader['unit_count']} labels, {companion['continuation_segment_count']} continuations; no print-collation or canon-equivalence claim.")
    return reader


if __name__ == "__main__":
    build()
