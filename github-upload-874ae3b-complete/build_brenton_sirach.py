"""Build Brenton's English Sirach as a separately scoped research reader."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import build_brenton_octateuch as brenton
from coverage_summary import build_coverage_statement
from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
CODE = "SIR"
MEMBER = "46-SIReng-Brenton.usfm"
SLUG = "sirach-brenton-lxx-1851"
READER_ID = "sirach-brenton-lxx-1851-research"
CORPUS_ID = "brenton-sirach-lxx-1851"
TRANSLATION_ID = "sirach-english-brenton-lxx-1851"
CANON_ID = "eotc-ot-45"
CATALOGUE_ID = "eotc-053"
SOURCE_IDS = ["SRC-029", "SRC-038", "SRC-142", "SRC-145"]
READER_PATH = ROOT / "readers" / f"{SLUG}.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_sirach_member(raw: bytes, package_hash: str) -> dict:
    previous = brenton.BOOKS.get(CODE)
    brenton.BOOKS[CODE] = (SLUG, 45, "Sirach", 51)
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
    manifest_path = brenton.MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("archive_sha256") != package_hash:
        raise ValueError("Brenton package hash does not match its capture manifest.")
    with zipfile.ZipFile(brenton.PACKAGE) as archive_zip:
        raw = archive_zip.read(MEMBER)
    parsed = parse_sirach_member(raw, package_hash)
    if (parsed["chapter_count"], parsed["unit_count"], parsed["continuation_segment_count"]) != (51, 1368, 1):
        raise ValueError("The archived Sirach member differs from its measured 51-chapter, 1,368-label inventory.")
    if parsed["chapters"][0].get("heading") != ["⟦The Prologue to the Wisdom of⟧ Jesus ⟦the son of⟧ Sirach"]:
        raise ValueError("The Sirach prologue heading was not preserved from the source USFM.")
    if not all(f"1{letter}" in {verse["number"] for verse in parsed["chapters"][0]["verses"]} for letter in "abcdefg"):
        raise ValueError("The source-labeled prologue units 1a–1g were not all retained in chapter 1.")

    manifest.setdefault("selected_members", {})[MEMBER] = {"sha256": sha256(raw), "byte_length": len(raw)}
    manifest["scope"] = (
        "Nine source package members are selected: Psalms, Leviticus, Numbers, Deuteronomy, Joshua, and Judges "
        "as English companion layers; Job, Tobit, and Sirach as separately scoped English research readers. "
        "Other package members remain unimported until their structure, boundaries, and catalogue relationship are assessed."
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rights = "eBible.org identifies Brenton's English translation, published in 1851 from the Greek Septuagint, as public domain. This is a provider-reported status, not a worldwide legal determination; source-package and archive materials have separate rights."
    verification = (
        "The local parser checks the member checksum, 51 ordered USFM chapter divisions (1–51), 1,368 source-numbered labels, "
        "one unnumbered continuation, the chapter-1 prologue heading and labels 1a–1g, source paragraph/break markers, and the "
        "chapter-1 omission gaps. eBible.org's index includes a page numbered 0, but that page contains only the prologue heading; "
        "the prologue text is on its page 1 and within USFM chapter 1, so no verse-bearing chapter is omitted or invented. These are "
        "digital-source structure checks only, not collation against the 1851 print edition or Greek source. Accuracy and printed-edition "
        "completeness remain unverified. The title-level relationship to EOTC entry 45 remains uncertain, and it is not counted as an EOTC canon reader or toward canon reader coverage."
    )
    reader = {
        "reader_id": READER_ID,
        "research_corpus_id": CORPUS_ID,
        "reader_scope": "research_witness_uncertain_catalogue_mapping",
        "title": "Sirach — Brenton Septuagint English (1851)",
        "display_name": "Research reader — Sirach (Brenton English Septuagint, 1851)",
        "text_origin": "published_translation",
        "translation_id": TRANSLATION_ID,
        "language": "English",
        "language_tag": "en",
        "script_code": "Latn",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_language_tag": "grc",
        "translation_path": ["grc", "en"],
        "edition": "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851).",
        "edition_scope": "Historical English translation from the Greek Septuagint, recorded as a related research witness. It is not a Geʽez transcription or an identified Ethiopian Orthodox Tewahedo edition.",
        "chapter_count": parsed["chapter_count"],
        "unit_count": parsed["unit_count"],
        "verse_marker_count": parsed["unit_count"],
        "unit_label": "English source verse labels",
        "section_label": "Chapter",
        "chapter_structure_note": "The archived USFM member has chapters 1–51. Chapter 1 includes the translator's prologue, with source labels 1a–1g and then 1h onward; numbering gaps are preserved. eBible.org also exposes a page numbered 0 that contains only the prologue heading, while its page 1 contains the prologue text. The title-only page is not counted as a separate chapter.",
        "transcription_note": "Parsed from the locally retained eBible.org Brenton USFM member; not collated against the 1851 print edition or the Greek Septuagint.",
        "editorial_signs_note": "USFM descriptive heading, verse labels, paragraph starts, source break marker, unnumbered continuation, and translator-added-word markers are retained. Translator additions are shown in visible archival brackets.",
        "source_ids": SOURCE_IDS,
        "source_pages": f"readers/source/brenton-septuagint/{MEMBER} (member of the locally archived package)",
        "source_package_sha256": package_hash,
        "source_member_sha256": sha256(raw),
        "rights_classification": "public_domain_claimed",
        "copyright_notice": rights,
        "commercial_use": "The provider reports the 1851 translation as public domain; no jurisdiction-specific rights determination is claimed for all package materials.",
        "verification_status": verification,
        "chapters": parsed["chapters"],
    }
    READER_PATH.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    example = brenton.make_layer(SLUG, "Sirach", CANON_ID, parsed, READER_PATH.name)
    example["record_id"] = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/{TRANSLATION_ID}"
    example["work_id"] = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/{SLUG}"
    example["tradition_assertions"][0].update({
        "mapping_state": "uncertain",
        "evidence_source_ids": ["SRC-029", "SRC-145"],
        "notes": "The EOTC English list names 'Book of Joshua the Son of Sirac' at entry 45, and the archive indexes Sirach/Ecclesiasticus as a candidate title. This establishes a title-level research connection only, not identity between the English Brenton Septuagint text, a Geʽez witness, or a current Church edition.",
    })
    example["witness"]["title"] = reader["title"]
    example["witness"]["source_ids"] = SOURCE_IDS
    example["witness"]["editorial_policy"] = reader["editorial_signs_note"]
    example["content_package"].update({"uri": f"../readers/{READER_PATH.name}", "json_pointer": ""})
    example["coverage"].update({
        "unit_count": parsed["unit_count"],
        "structure_description": "The locally archived member contains chapters 1–51 and 1,368 numbered labels; chapter 1 contains the prologue labels 1a–1g and onward. The source site's page 0 is title-only; its page 1 holds the prologue text. These are measured digital-source counts, not proof of print-edition completeness.",
        "supplements_and_editorial_signs": "One unnumbered continuation is preserved, as are the chapter-1 prologue heading, paragraph starts, a source break marker, numbering gaps, and translator-supplied additions in visible archival brackets.",
        "numbering_policy": "Source chapter and verse labels are retained as strings. The title-only HTML page 0 is not a verse-bearing chapter; its prologue text appears in chapter 1, including labels 1a–1g. No missing labels are synthesized.",
    })
    example["rights"].update({"statement": rights, "evidence_source_ids": ["SRC-038", "SRC-142"]})
    for review in example["review_dimensions"]:
        review["evidence_source_ids"] = SOURCE_IDS
    example["additional_notes"] = verification
    example_path = ROOT / "examples" / "sirach-brenton-translation-layer.json"
    example_path.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(example_path, READER_PATH)

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    source = {
        "source_id": "SRC-145",
        "source_name": "eBible.org — Brenton Sirach chapter index and chapter pages",
        "url": "https://ebible.org/eng-Brenton/SIR.htm",
        "inspection_and_limitations": (
            "The index lists page links 0 through 51. Its page 0 contains a prologue heading only; page 1 contains the prologue text "
            "followed by chapter 1, and page 51 contains chapter 51. The bundled text is parsed from the local USFM member "
            f"{MEMBER} (SHA-256 {sha256(raw)}, {len(raw)} bytes), with USFM chapter divisions 1–51, 1,368 numbered labels, and "
            "one unnumbered continuation. The browser-visible boundary checks do not collate every word or establish completeness "
            "against the printed edition or Greek. Its relationship to EOTC entry 45 is a title-level candidate only."
        ),
        "archive_status": "Sirach index and boundary pages inspected; checksum-pinned USFM member retained as separately scoped English research text",
    }
    sources = archive.setdefault("sources", [])
    old = next((item for item in sources if item.get("source_id") == "SRC-145"), None)
    if old and old.get("source_name") != source["source_name"]:
        raise ValueError("SRC-145 is assigned to another source record.")
    if old:
        sources[sources.index(old)] = source
    else:
        sources.append(source)
    sources.sort(key=lambda item: int(item["source_id"].split("-")[1]))
    entry = next(item for item in archive["catalogue"] if item.get("catalogue_id") == CATALOGUE_ID)
    entry.update({
        "text_availability_status": "A separate English Brenton translation from Greek is bundled as a research reader. No Geʽez reader is bundled for this catalogue row.",
        "chapter_count": "51 observed divisions in the Brenton USFM member; Church-list edition boundaries unknown",
        "chapter_order_status": "The selected member has ordered USFM chapters 1–51. The provider index page numbered 0 is title-only; its prologue text occurs within chapter 1.",
        "completeness_status": "1,368 source-labeled units and one unnumbered continuation observed in the selected member; no printed-edition collation or accuracy review performed.",
        "rights_status": "eBible.org reports Brenton's 1851 English translation as public domain; this provider claim does not license other source layers or establish a jurisdiction-specific legal conclusion.",
        "reviewer_notes": "The candidate link to Church-list entry 45 ('Book of Joshua the Son of Sirac') remains a title-level uncertain crosswalk. This reader represents Brenton's English translation of Greek Septuagint Sirach, not a verified Geʽez witness or current EOTC edition.",
    })
    entry["evidence_source_ids"] = list(dict.fromkeys(entry.get("evidence_source_ids", []) + SOURCE_IDS))

    package_source = next(item for item in sources if item.get("source_id") == "SRC-142")
    package_source["inspection_and_limitations"] = (
        f"eBible.org identifies Brenton's translation as an English translation from Greek, published in 1851, and reports it as public domain. "
        f"The archived USFM zip (SHA-256 {package_hash}) includes {MEMBER} among the selected source members; the selected Sirach member "
        f"has SHA-256 {sha256(raw)}. Local parser checks establish source-package structure only. Wording, print completeness, Greek accuracy, "
        "and alignment to Geʽez remain unverified. The rights statement is a provider claim, not a worldwide legal determination."
    )
    package_source["archive_status"] = "Full source package stored; six English companions and three separately scoped Brenton research readers are bundled with explicit limits"
    archive_path.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
        "translator": reader["translator"],
        "basis_language_tag": "grc",
        "basis_description": "Brenton's 1851 English translation is from Greek; the possible Church-list relation is an uncertain title-level candidate.",
        "rights_status": "public_domain_per_cited_source",
        "rights_classification": "public_domain_claimed",
        "source_ids": SOURCE_IDS,
        "translation_path": ["grc", "en"],
    })
    english["records"].sort(key=lambda item: (item.get("canon_id") or "", item.get("translation_id", "")))
    english["source_ids"] = sorted(set(english.get("source_ids", [])) | {"SRC-145"})
    registry["research_corpora"] = [item for item in registry.get("research_corpora", []) if item.get("corpus_id") != CORPUS_ID]
    registry["research_corpora"].append({
        "corpus_id": CORPUS_ID,
        "title": reader["title"],
        "reader_id": READER_ID,
        "unit_count": reader["unit_count"],
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": CANON_ID,
        "canon_mapping_note": "The Church's English list entry 45 and this Brenton title suggest a related-work candidate. The exact identity, Geʽez textual basis, and relation to a current Church edition are not established. Excluded from canon-linked reader coverage.",
        "language_description": "English translation (en), translated from Greek (grc).",
        "script_description": "Latin script (Latn) for this digital English witness.",
        "unit_summary": "1,368 labels in 51 USFM chapter divisions plus one continuation, measured in the local package. The provider's page 0 contains only a heading; the prologue text is in chapter 1.",
        "rights_classification": "public_domain_claimed",
        "rights_status": rights,
        "review_status": verification,
        "source_ids": SOURCE_IDS,
        "text_origin": "published_translation",
        "language_tag": "en",
        "script_code": "Latn",
        "basis_language_tag": "grc",
        "translation_path": ["grc", "en"],
        "translation_id": TRANSLATION_ID,
        "translator": reader["translator"],
        "edition_statement": reader["edition"],
    })
    registry["research_corpora"].sort(key=lambda item: item["corpus_id"])
    registry["coverage_statement"] = build_coverage_statement(registry, json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8")))
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Built separate Brenton Sirach research reader: 51 chapters, 1,368 labels, one continuation; chapter-zero webpage is heading-only; no print-collation or certain EOTC mapping claim.")
    return reader


if __name__ == "__main__":
    build()
