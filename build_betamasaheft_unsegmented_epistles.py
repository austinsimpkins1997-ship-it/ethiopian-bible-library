"""Build research-only Geʽez readers for pinned, unsegmented Beta maṣāḥǝft epistles."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
COMMIT = "ec53d3f4c5de47e463fa56a8465cf1090316a999"
CONFIG = [
    {"name": "II John", "work": "LIT3510Epistle", "canon": "eotc-nt-23", "file": "LIT3510Epistle.xml", "lines": 15, "numbered": 13, "sha256": "13bdbd8aab7f924d1ea5c4b75adeb9ec674844078481fdd3d896b1f7d1c3307b", "source_id": "SRC-271", "catalogue_id": "eotc-078"},
    {"name": "III John", "work": "LIT3511Epistle", "canon": "eotc-nt-24", "file": "LIT3511Epistle.xml", "lines": 17, "numbered": 15, "sha256": "614268415cb8006b21f914b7ec4d406aa1020488a53446437a2ae03f5dcea952", "source_id": "SRC-272", "catalogue_id": "eotc-079"},
    {"name": "Jude", "work": "LIT3513Epistle", "canon": "eotc-nt-26", "file": "LIT3513Epistle.xml", "lines": 28, "numbered": 25, "sha256": "9d4ce8878c332696fb8d4246b83089108d0770f84948f76c984383be696350a6", "source_id": "SRC-273", "catalogue_id": "eotc-080"},
]


def normalized(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def build_one(cfg: dict) -> tuple[dict, dict, dict]:
    relative = f"readers/source/unsegmented-epistles/{cfg['file']}"
    path = ROOT / relative
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != cfg["sha256"]:
        raise ValueError(f"Pinned source hash mismatch for {cfg['work']}: {digest}")
    root = ET.fromstring(raw)
    if root.get(f"{{{XML}}}id") != cfg["work"]:
        raise ValueError(f"Wrong TEI work id for {cfg['work']}")
    edition = next((x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition"), None)
    if edition is None or edition.get(f"{{{XML}}}lang") != "gez":
        raise ValueError(f"{cfg['work']} has no explicit Geʽez edition declaration")
    title_stmt = next((x for x in root.iter(f"{{{TEI}}}titleStmt")), None)
    title_node = next(iter(title_stmt.findall(f"{{{TEI}}}title")), None) if title_stmt is not None else None
    title = normalized(title_node) if title_node is not None else None
    if not title or cfg["name"].split()[-1].lower() not in title.lower():
        raise ValueError(f"Unexpected main title for {cfg['work']}: {title}")
    lic = next((x for x in root.iter(f"{{{TEI}}}licence") if "creativecommons.org/licenses/by-sa/4.0" in x.get("target", "")), None)
    if lic is None:
        raise ValueError(f"No file-level CC BY-SA 4.0 statement in {cfg['work']}")
    if any(x.get("subtype") == "chapter" for x in edition.iter(f"{{{TEI}}}div")):
        raise ValueError(f"{cfg['work']} unexpectedly contains explicit TEI chapter divisions")
    line_nodes = list(edition.iter(f"{{{TEI}}}l"))
    numbered = sum(x.get("n") is not None for x in line_nodes)
    if (len(line_nodes), numbered) != (cfg["lines"], cfg["numbered"]):
        raise ValueError(f"TEI line inventory changed for {cfg['work']}: {(len(line_nodes), numbered)}")
    units = []
    for order, line in enumerate(line_nodes, 1):
        text = normalized(line)
        unit = {"number": order, "unit_order": order, "source_marker": line.get("n"), "source_element_id": line.get(f"{{{XML}}}id"), "source_refs": [r.get("target") for r in line.iter(f"{{{TEI}}}ref") if r.get("target")], "text": text}
        if not text:
            unit["source_text_state"] = "empty_source_element"
        units.append(unit)
    reader_id = f"{cfg['name'].lower().replace(' ', '-')}-betamasaheft-tei-research"
    url = f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/3001-4000/{cfg['file']}"
    reader = {
        "reader_id": reader_id,
        "research_corpus_id": f"betamasaheft-{cfg['name'].lower().replace(' ', '-')}-tei-research",
        "text_origin": "source_transcription",
        "title": f"{cfg['name']} — Geʽez TEI research transcription (chapter structure unverified)",
        "display_name": f"{cfg['name']} · Geʽez · research text; canon link unverified",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "source_declared_inherited_edition_xml_lang",
        "script_code": "Ethi",
        "edition": f"Beta maṣāḥǝft {cfg['work']} TEI source snapshot, pinned at Works commit {COMMIT}",
        "edition_scope": f"The TEI work title is {title!r}; its edition explicitly declares xml:lang=\"gez\". This file does not state that its text is from the EOTC printed Bible. The archive therefore retains it as a research transcription with a provisional title candidate only, not as a verified Church-list crosswalk or canon-linked reader.",
        "section_label": "Source text block",
        "unit_label": "TEI line element (all numbered and unnumbered elements)",
        "source_ids": [cfg["source_id"]],
        "rights_classification": "open_license",
        "copyright_notice": f"The retained Beta maṣāḥǝft {cfg['work']} TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link the source and license, indicate extraction and whitespace normalization, and share adaptations alike. The file-level grant does not establish rights in an unidentified underlying exemplar.",
        "commercial_use": "The file-level CC BY-SA 4.0 permits commercial sharing and adaptation subject to attribution, change notices, and ShareAlike. This does not establish rights in any underlying exemplar.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "chapter_count": 1,
        "unit_count": len(units),
        "source_numbered_unit_count": numbered,
        "source_unnumbered_unit_count": len(units) - numbered,
        "source_empty_unit_count": sum(not x["text"] for x in units),
        "chapter_structure_note": f"The pinned TEI edition contains no explicit chapter divisions. The interface places its {len(units)} source line elements in one navigable source-text block; this display grouping is not a claim that the TEI labels it chapter 1. {numbered} lines have source n labels and {len(units)-numbered} do not.",
        "transcription_note": "Every TEI line element in the declared edition division is retained in source order. Display whitespace is normalized; inline markup is flattened for display while the unchanged source XML is retained. No missing wording or verse labels are supplied.",
        "chapters": [{"chapter": 1, "source_chapter_label": None, "heading": ["Unsegmented source text; the TEI has no chapter divisions"], "units": units, "notes": []}],
        "verification_status": "Automated source hash, language declaration, license declaration, line count, source labels, and exact line extraction checked. No chapter boundaries, textual completeness, transcription accuracy, exact witness identity, or EOTC canon affiliation are verified.",
    }
    source = {
        "source_id": cfg["source_id"],
        "source_name": f"Beta maṣāḥǝft Works — pinned {cfg['work']} TEI source snapshot",
        "url": url,
        "inspection_and_limitations": f"Retrieved from BetaMasaheft/Works commit {COMMIT} and retained unchanged at {relative} ({len(raw):,} bytes; SHA-256 {digest}). The TEI title identifies {title}; the edition explicitly declares Geʽez and the file states CC BY-SA 4.0. Its TEI has {len(line_nodes)} line elements ({numbered} labeled, {len(units)-numbered} unlabeled) in an unsegmented <ab>; no chapter divisions or EOTC printed-Bible note are present. All line elements are retained without inventing chapter boundaries. The file license does not establish rights in any unidentified exemplar. Accuracy, completeness, and canon affiliation are unverified.",
        "archive_status": "Pinned source TEI retained locally; language, file-level license, and line extraction checked; chapter boundaries, accuracy, completeness, and canon affiliation unverified",
    }
    corpus = {
        "corpus_id": reader["research_corpus_id"],
        "title": f"{cfg['name']} (Geʽez) — Beta maṣāḥǝft TEI research transcription",
        "reader_id": reader_id,
        "unit_count": len(units),
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": cfg["canon"],
        "canon_mapping_note": f"The TEI title corresponds by name to Church-list {cfg['name']}, but the file has no EOTC printed-Bible note, chapter divisions, or completeness statement. This is a title candidate only and is excluded from canon-linked coverage.",
        "language_description": "The TEI edition explicitly declares Geʽez (gez).",
        "script_description": "Ethiopic script (Ethi) is used in the retained TEI text.",
        "unit_summary": f"{len(units)} TEI line elements retained in order; {numbered} carry source labels. The source has no TEI chapter divisions.",
        "rights_classification": "open_license",
        "rights_status": "The source file states CC BY-SA 4.0; rights in any underlying exemplar are not established.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "review_status": "Automated structural extraction only; no independent transcription accuracy, completeness, chapter-boundary, witness-identity, or canon-affiliation review.",
        "source_ids": [cfg["source_id"]],
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "script_code": "Ethi",
        "translation_id": None,
        "translator": None,
        "translation_basis_status": "not_applicable_source_transcription",
        "translation_basis_note": "This is a Geʽez source transcription, not an English translation.",
        "edition_statement": f"Beta maṣāḥǝft {cfg['work']} TEI source snapshot pinned at {COMMIT}; exact exemplar unidentified.",
    }
    (ROOT / "readers" / f"{reader_id}.json").write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return reader, source, corpus


def build() -> list[dict]:
    built = [build_one(cfg) for cfg in CONFIG]
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {s["source_id"]: s for s in archive["sources"]}
    for _, source, _ in built:
        sources[source["source_id"]] = source
    archive["sources"] = sorted(sources.values(), key=lambda s: int(s["source_id"].split("-")[1]))
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    corpora = {c["corpus_id"]: c for c in registry["research_corpora"]}
    for _, _, corpus in built:
        corpora[corpus["corpus_id"]] = corpus
    registry["research_corpora"] = sorted(corpora.values(), key=lambda c: c["corpus_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for cfg in CONFIG:
        book_dir = ROOT / "readers" / "source" / "unsegmented-epistles"
        audit = book_dir / f"{cfg['work']}-SOURCE-AUDIT.md"
        source_url = f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/3001-4000/{cfg['file']}"
        text = (
            f"# {cfg['name']} source audit\n\n"
            f"Pinned Beta maṣāḥǝft Works file `{cfg['work']}.xml` at commit `{COMMIT}`. "
            f"The main TEI title names {cfg['name']}; the edition explicitly declares Geʽez. "
            "The file states CC BY-SA 4.0.\n\n"
            f"The retained edition contains {cfg['lines']} TEI line elements "
            f"({cfg['numbered']} with source labels, {cfg['lines'] - cfg['numbered']} without labels) "
            "inside an unsegmented `<ab>`. No TEI chapter divisions or EOTC printed-Bible note were found. "
            "The reader preserves all line elements in order and uses a navigational grouping that is "
            "explicitly not presented as a source chapter.\n\n"
            "The title match is only a candidate. EOTC affiliation, exact witness identity, completeness, "
            "chapter boundaries, and transcription accuracy remain unverified. The file-level license "
            "does not establish rights in an unidentified underlying exemplar.\n\n"
            f"Source: [{cfg['work']} at pinned commit]({source_url}).\n"
        )
        audit.write_text(text, encoding="utf-8")
    print(f"Built {len(built)} unsegmented Geez research readers; none counted as canon-linked coverage.")
    return [r for r, _, _ in built]


if __name__ == "__main__":
    build()
