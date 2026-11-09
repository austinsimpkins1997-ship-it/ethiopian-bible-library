"""Bundle Brenton's English Tobit as a separately scoped research reader."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import zipfile
from pathlib import Path

import build_brenton_octateuch as brenton
from coverage_summary import build_coverage_statement

ROOT = Path(__file__).resolve().parent
CODE = "TOB"
MEMBER = "41-TOBeng-Brenton.usfm"
SLUG = "tobit-brenton-lxx-1851"
READER_ID = "tobit-brenton-lxx-1851-research"
CORPUS_ID = "brenton-tobit-lxx-1851"
TRANSLATION_ID = "tobit-english-brenton-lxx-1851"
CANON_ID = "eotc-ot-17"
SOURCE_IDS = ["SRC-142", "SRC-144"]
READER_PATH = ROOT / "readers" / f"{SLUG}.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_tobit_member(raw: bytes, package_hash: str) -> dict:
    previous = brenton.BOOKS.get(CODE)
    brenton.BOOKS[CODE] = (SLUG, 17, "Tobit", 14)
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
    manifest = json.loads(brenton.MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("archive_sha256") != package_hash:
        raise ValueError("Brenton package hash does not match the capture manifest.")
    with zipfile.ZipFile(brenton.PACKAGE) as archive_zip:
        raw = archive_zip.read(MEMBER)
    companion = parse_tobit_member(raw, package_hash)
    if companion["chapter_count"] != 14 or companion["unit_count"] != 245 or companion["continuation_segment_count"] != 2:
        raise ValueError("The archived Tobit member no longer matches its observed 14-chapter, 245-label inventory.")

    manifest.setdefault("selected_members", {})[MEMBER] = {
        "sha256": sha256(raw),
        "byte_length": len(raw),
    }
    manifest["scope"] = (
        "Eight source package members are selected: Psalms, Leviticus, Numbers, Deuteronomy, Joshua, and Judges "
        "as English companions, plus Job and Tobit as separately scoped English research readers. Other package "
        "members remain unimported until their structure and catalogue relationship are assessed."
    )
    brenton.MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    edition = "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851)."
    rights = "eBible.org identifies Brenton's 1851 English translation as public domain. This archive records the provider's statement, not a worldwide legal determination; other source layers and website design have separate rights."
    verification = (
        "The local parser checks the archived member checksum, 14 ordered chapter divisions, 245 numbered labels, "
        "two unnumbered continuation segments, and source markup. This is extraction-structure evidence only. It does "
        "not establish completeness against the 1851 print edition or Greek source, translation accuracy, identity with "
        "a Geʽez witness, or equivalence to an Ethiopian Orthodox Church edition. The candidate link to Church-list "
        "entry 17 (Tobit) is title-level and provisional. It is not counted as an EOTC canon reader or toward canon reader coverage."
    )
    reader = {
        "reader_id": READER_ID,
        "research_corpus_id": CORPUS_ID,
        "reader_scope": "research_witness_uncertain_catalogue_mapping",
        "title": "Tobit — Brenton Septuagint English (1851)",
        "display_name": "Research reader — Tobit (Brenton English Septuagint, 1851)",
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
        "edition": edition,
        "edition_scope": "Historical English translation of Greek Septuagint Tobit. This is a related English research witness, not a Geʽez transcription or verified translation of a specific Geʽez witness.",
        "chapter_count": companion["chapter_count"],
        "unit_count": companion["unit_count"],
        "unit_label": "English verse labels observed in the archived USFM member",
        "verse_marker_count": companion["unit_count"],
        "section_label": "Chapter",
        "chapter_structure_note": "The selected archived eBible.org USFM member contains 14 ordered chapter divisions, 245 numbered verse labels, and two unnumbered continuation segments. These are measured package counts, not proof of completeness against print, Greek, Geʽez, or an EOTC edition.",
        "transcription_note": "Reader wording is parsed from the archived USFM member; it has not been collated against the 1851 printed edition or the Greek source.",
        "editorial_signs_note": "USFM translator additions are visibly bracketed. Footnotes, cross-references, paragraph starts, descriptive titles, and unnumbered continuation segments are retained as separate structure.",
        "source_ids": SOURCE_IDS,
        "source_pages": f"readers/source/brenton-septuagint/{MEMBER} (member of the locally archived package)",
        "source_package_sha256": package_hash,
        "source_member_sha256": sha256(raw),
        "rights_classification": "public_domain_claimed",
        "copyright_notice": rights,
        "commercial_use": "The provider identifies Brenton's 1851 translation as public domain. This is a provider-reported status, not a jurisdiction-specific legal determination for the complete archive.",
        "verification_status": verification,
        "chapters": companion["chapters"],
    }
    READER_PATH.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    source = {
        "source_id": "SRC-144",
        "source_name": "Brenton Tobit source and USFM member inventory",
        "url": "https://ebible.org/eng-Brenton/TOB.htm",
        "inspection_and_limitations": (
            f"eBible.org's Tobit index lists chapter links 1–14. The bundled wording is parsed from member {MEMBER} "
            f"of the locally archived USFM package; member SHA-256 {sha256(raw)}, {len(raw)} bytes. The parser observes "
            "14 ordered chapter divisions, 245 numbered labels, and two unnumbered continuation segments. No raw "
            "HTML capture or print/Greek collation is claimed; accuracy, print completeness, and the Church-list "
            "crosswalk remain unverified. It is not counted as an EOTC canon reader or toward canon reader coverage."
        ),
        "archive_status": "Tobit source page and checksum-pinned USFM member retained; parsed as English research text only",
    }
    sources = archive.setdefault("sources", [])
    existing = next((item for item in sources if item.get("source_id") == source["source_id"]), None)
    if existing is None:
        sources.append(source)
    elif existing != source:
        if existing.get("source_name") != source["source_name"]:
            raise ValueError("SRC-144 is already assigned to a different source record.")
        sources[sources.index(existing)] = source
    archive["sources"].sort(key=lambda item: int(item["source_id"].split("-")[1]))
    entry = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-020")
    entry.update({
        "text_availability_status": "A separate English Brenton translation from Greek is bundled as a research reader; no canon-linked Geʽez source-text reader is bundled for this catalogue row.",
        "completeness_status": "The selected digital USFM member contains 14 ordered chapter divisions, 245 numbered labels, and two continuation segments. This observed inventory does not establish printed-edition completeness or translation accuracy.",
        "rights_status": "eBible.org identifies the 1851 Brenton English translation as public domain. This provider claim is recorded separately from rights in other witnesses and source materials.",
        "reviewer_notes": "The English Brenton reader is a distinct translation from Greek. Its candidate relationship to Church-list entry 17 Tobit is provisional; no Geʽez text, EOTC edition identification, print collation, or accuracy review is claimed.",
    })
    entry["evidence_source_ids"] = list(dict.fromkeys(entry.get("evidence_source_ids", []) + SOURCE_IDS))
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
        "translator": reader["translator"],
        "basis_language_tag": "grc",
        "basis_description": "Brenton's 1851 English translation is based on Greek; it is not a translation of an accompanying Geʽez witness.",
        "rights_status": "public_domain_per_cited_source",
        "rights_classification": "public_domain_claimed",
        "source_ids": SOURCE_IDS,
        "translation_path": ["grc", "en"],
    })
    english["records"].sort(key=lambda item: (item["canon_id"], item.get("translation_id", "")))
    english["source_ids"] = sorted(set(english.get("source_ids", [])) | {"SRC-144"})
    registry["research_corpora"] = [item for item in registry.get("research_corpora", []) if item.get("corpus_id") != CORPUS_ID]
    registry["research_corpora"].append({
        "corpus_id": CORPUS_ID,
        "title": reader["title"],
        "reader_id": READER_ID,
        "unit_count": reader["unit_count"],
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": CANON_ID,
        "canon_mapping_note": "A provisional title-level candidate only. This Brenton text represents Greek Septuagint Tobit and does not establish identity with an Ethiopian Orthodox Church Geʽez witness or edition. It is excluded from canon-linked reader coverage.",
        "language_description": "English translation (en), translated from Greek (grc).",
        "script_description": "Latin script (Latn) for this digital English witness.",
        "unit_summary": "245 English verse labels and two preserved unnumbered continuation segments observed in 14 ordered USFM chapter divisions; package inventory only.",
        "rights_classification": "public_domain_claimed",
        "rights_status": rights,
        "review_status": verification,
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
        "edition_statement": edition,
    })
    registry["research_corpora"].sort(key=lambda item: item["corpus_id"])
    canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    registry["coverage_statement"] = build_coverage_statement(registry, canon)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    package_source = next(item for item in archive["sources"] if item.get("source_id") == "SRC-142")
    package_source["inspection_and_limitations"] = (
        f"eBible.org identifies Sir Lancelot Charles Lee Brenton's translation as an English translation from Greek, published in 1851, and reports it as public domain. The archived USFM zip (SHA-256 {package_hash}) contains the selected members recorded in readers/source/brenton-septuagint/capture-manifest.json, including separate Job and Tobit research readers. Parsing checks local structure and extraction only; wording, print completeness, and alignment to Geʽez remain unverified. The rights statement is a provider claim, not a worldwide legal determination."
    )
    package_source["archive_status"] = "Full source package stored; six English companions and two separately scoped research readers are bundled with explicit limits"
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    print("Built separate Brenton Tobit research reader: 14 chapters, 245 labels, 2 continuations; no print-collation or canon-equivalence claim.")
    return reader


if __name__ == "__main__":
    build()
