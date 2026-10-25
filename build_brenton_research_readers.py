"""Build separate, un-mapped Brenton English Septuagint research readers.

The source package is retained locally. These readers preserve USFM structure
and remain outside EOTC canon-linked coverage unless a future review supplies
an evidence-backed, explicitly scoped crosswalk.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import build_brenton_octateuch as brenton
from coverage_summary import build_coverage_statement

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "translation-registry.json"
MANIFEST_PATH = brenton.MANIFEST
PACKAGE_PATH = brenton.PACKAGE
READER_PREFIX = "brenton-lxx-"
READER_SUFFIX = "-research.json"
RESEARCH_CODES = {
    "1SA", "2SA", "1CH", "2CH", "EZR", "ECC", "SNG", "JER", "EZK",
    "1KI", "PRO", "LAM", "HOS", "JOL", "AMO", "OBA", "JON", "MIC", "NAM", "HAB", "ZEP",
    "HAG", "ZEC", "MAL", "JDT", "ESG", "WIS", "BAR", "LJE", "SUS",
    "BEL", "1MA", "2MA", "1ES", "MAN", "3MA", "4MA", "DAG",
}
ALREADY_REPRESENTED = {"GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "JOB", "PSA", "TOB", "SIR"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_heading(source: str, marker: str) -> str:
    match = re.search(rf"^\\{marker}\s+(.+?)\s*$", source, re.M)
    return match.group(1).strip() if match else ""


def build_records() -> tuple[list[dict], list[dict], dict]:
    package_bytes = PACKAGE_PATH.read_bytes()
    package_hash = sha256(package_bytes)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("archive_sha256") != package_hash:
        raise ValueError("Brenton USFM package checksum differs from its capture manifest.")
    with zipfile.ZipFile(PACKAGE_PATH) as archive:
        members: dict[str, tuple[str, bytes]] = {}
        for member_name in archive.namelist():
            if not member_name.endswith(".usfm"):
                continue
            raw = archive.read(member_name)
            match = re.search(rb"^\\id\s+([A-Z0-9]{3})\s+-\s+Brenton English Septuagint\s*$", raw, re.M)
            if match:
                members[match.group(1).decode("ascii")] = (member_name, raw)

    missing = RESEARCH_CODES - members.keys()
    if missing:
        raise ValueError(f"Expected USFM members are absent from the package: {sorted(missing)}")
    if RESEARCH_CODES & ALREADY_REPRESENTED:
        raise ValueError("Research set overlaps an already bundled reader.")

    readers: list[dict] = []
    corpora: list[dict] = []
    selected_members = manifest.setdefault("selected_members", {})
    notice = (
        "eBible.org identifies Brenton's 1851 English translation as public domain. "
        "This is a provider-reported status, not a jurisdiction-specific legal determination; "
        "other source layers and archive materials have separate rights."
    )
    for code in sorted(RESEARCH_CODES):
        member_name, raw = members[code]
        source = raw.decode("utf-8-sig")
        chapter_count = len(re.findall(r"^\\c\s+\d+\s*$", source, re.M))
        source_title = source_heading(source, "h") or source_heading(source, "toc1") or code
        mt_title = source_heading(source, "mt1")
        title = f"{source_title} — Brenton English Septuagint (1851)"
        slug = code.lower().replace("1", "first-").replace("2", "second-").replace("3", "third-").replace("4", "fourth-").strip("-")
        reader_id = f"brenton-lxx-{slug}-research"
        corpus_id = f"brenton-lxx-{slug}-research"
        previous_book = brenton.BOOKS.get(code)
        brenton.BOOKS[code] = (slug, 0, source_title, chapter_count)
        try:
            parsed = brenton.parse_usfm(raw, code, member_name, package_hash)
        finally:
            if previous_book is None:
                brenton.BOOKS.pop(code, None)
            else:
                brenton.BOOKS[code] = previous_book
        member_hash = sha256(raw)
        selected_members[member_name] = {"sha256": member_hash, "byte_length": len(raw)}
        chapters = parsed["chapters"]
        unit_count = parsed["unit_count"]
        notes = parsed["note_count"]
        continuations = parsed["continuation_segment_count"]
        marker_only_count = parsed.get("marker_only_unit_count", 0)
        record = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "reader_scope": "research_witness_not_mapped_to_eotc_canon",
            "title": title,
            "display_name": f"{source_title} (Brenton English LXX, 1851)",
            "text_origin": "published_translation",
            "translation_id": parsed["translation_id"],
            "language": "English",
            "language_tag": "en",
            "script_code": "Latn",
            "translator": "Sir Lancelot Charles Lee Brenton",
            "basis_language_tag": "grc",
            "translation_path": ["grc", "en"],
            "edition": "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851).",
            "edition_scope": (
                "Historical English translation of a Greek Septuagint text as represented by this eBible.org USFM member. "
                "This is a separate research witness; it is not a Geʽez transcription, an EOTC printed-edition claim, "
                "or a verified translation from Geʽez. No EOTC canon crosswalk is assigned."
            ),
            "chapter_count": len(chapters),
            "unit_count": unit_count,
            "unit_label": "English verse labels observed in the archived USFM member",
            "verse_marker_count": unit_count,
            "section_label": "Chapter",
            "chapter_structure_note": (
                f"The local USFM member {member_name} contains {len(chapters)} ordered chapter markers, "
                f"{unit_count:,} numbered source labels, {notes:,} preserved notes/cross-references, and "
                f"{continuations:,} unnumbered continuation segments. Marker-only source labels without inline text: "
                f"{marker_only_count}. These are package observations, "
                "not proof of completeness against a print edition, Greek witness, or any community's canon."
            ),
            "transcription_note": "Reader wording is parsed from the archived USFM member and has not been independently collated against the printed 1851 edition or the Greek source.",
            "editorial_signs_note": "USFM translator-supplied-word markers are displayed in visible archival brackets ⟦…⟧. Source notes, cross-references, headings, paragraph markers, and continuation segments are retained as structured data.",
            "source_ids": ["SRC-038", "SRC-142"],
            "source_pages": f"readers/source/brenton-septuagint/{member_name} (member of the locally archived package)",
            "source_package_sha256": package_hash,
            "source_member_sha256": member_hash,
            "rights_classification": "public_domain_claimed",
            "copyright_notice": notice,
            "commercial_use": "The provider identifies Brenton's 1851 translation as public domain; this is not a jurisdiction-specific rights determination.",
            "verification_status": (
                f"Automated parsing checked the local member checksum, {len(chapters)} sequential chapter markers, "
                f"{unit_count:,} source labels, {notes:,} notes/cross-references, and {continuations:,} continuation segments. "
                f"{marker_only_count:,} source label(s) have no inline text and remain explicitly marked as such. "
                "This confirms local package-to-reader structural fidelity only. Exact wording, accuracy against Greek or print, "
                "printed-edition completeness, and relationship to any EOTC text remain unreviewed. It is not canon-linked and is not counted as an EOTC canon reader or toward EOTC coverage."
            ),
            "chapters": chapters,
        }
        readers.append(record)
        corpora.append({
            "corpus_id": corpus_id,
            "title": title,
            "reader_id": reader_id,
            "unit_count": unit_count,
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped",
            "candidate_canon_id": None,
            "canon_mapping_note": "No EOTC canon crosswalk is assigned. Similar English titles in other catalogues do not establish work identity, Geʽez text identity, or the same chapter boundaries. This English Septuagint research reader is excluded from canon-linked coverage.",
            "language_description": "English (en), translated by Sir Lancelot Charles Lee Brenton from Greek (grc).",
            "script_description": "Latin script (Latn), as used by the English digital witness.",
            "unit_summary": f"{unit_count:,} English labels in {len(chapters)} ordered chapter divisions, with {notes:,} notes/cross-references, {marker_only_count:,} labels without inline text, and {continuations:,} continuation segments observed in the local USFM member.",
            "rights_classification": "public_domain_claimed",
            "rights_status": notice,
            "review_status": record["verification_status"],
            "source_ids": ["SRC-038", "SRC-142"],
            "text_origin": "published_translation",
            "language_tag": "en",
            "script_code": "Latn",
            "basis_language_tag": "grc",
            "translation_path": ["grc", "en"],
            "translation_id": parsed["translation_id"],
            "translator": "Sir Lancelot Charles Lee Brenton",
            "edition_statement": record["edition"],
        })

    # Keep selected-member hashes deterministic and the scope statement exact.
    manifest["selected_members"] = dict(sorted(selected_members.items()))
    manifest["scope"] = (
        "The capture manifest lists all selected members. Existing English companions and research texts are retained separately; "
        f"{len(RESEARCH_CODES)} additional members are parsed as independent English research readers with no EOTC canon crosswalk. "
        "Genesis, Exodus, and Ruth also occur in the provider zip but remain represented by separately archived page-capture or companion sources. "
        "Seven members fail the strict parser and remain unbundled."
    )
    manifest["limitations"] = (
        "The provider identifies Brenton's translation as 1851 and public domain. Checks establish local package identity and "
        "parser extraction structure only; they do not establish print-edition completeness, Greek translation accuracy, "
        "or identity with any Geʽez/EOTC witness. Seven members fail the current strict parser and are excluded; three other "
        "parseable members (Genesis, Exodus, and Ruth) are not imported from this package because separate local source records are used. "
        "No source text is silently repaired."
    )
    return readers, corpora, manifest


def main() -> None:
    readers, corpora, manifest = build_records()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reader_dir = ROOT / "readers"
    for reader in readers:
        code_slug = reader["reader_id"].removeprefix(READER_PREFIX).removesuffix("-research")
        path = reader_dir / f"{READER_PREFIX}{code_slug}{READER_SUFFIX}"
        path.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    other_corpora = [item for item in registry.get("research_corpora", []) if item.get("reader_id") not in {r["reader_id"] for r in readers}]
    registry["research_corpora"] = other_corpora + corpora
    canon_registry = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    registry["coverage_statement"] = build_coverage_statement(registry, canon_registry)
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(readers)} standalone Brenton research readers; no EOTC mappings assigned.")


if __name__ == "__main__":
    main()
