"""Build research-only Chronicles readers from pinned Beta maṣāḥǝft TEI files."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMMIT = "ec53d3f4c5de47e463fa56a8465cf1090316a999"
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
WORKS = [
    {
        "work_id": "LIT3499Chroni",
        "book": "1 Chronicles",
        "canon_id": "eotc-ot-11",
        "source_id": "SRC-290",
        "reader_id": "first-chronicles-betamasaheft-tei-research",
        "corpus_id": "betamasaheft-first-chronicles-tei-research",
        "path": "3001-4000/LIT3499Chroni.xml",
        "sha256": "fb040b6b5a821ee81626a8d848de3c6ade85e31c860aacd534425e104c3d46e6",
        "chapters": 29,
        "lines": 950,
        "label_gaps": {"1": ["13"], "26": ["28"]},
    },
    {
        "work_id": "LIT3500Chroni",
        "book": "2 Chronicles",
        "canon_id": "eotc-ot-12",
        "source_id": "SRC-291",
        "reader_id": "second-chronicles-betamasaheft-tei-research",
        "corpus_id": "betamasaheft-second-chronicles-tei-research",
        "path": "3001-4000/LIT3500Chroni.xml",
        "sha256": "e34dbe7cb15758d39f6739ceb06c81aca1bec0fa40a50df82b7bd7280fea54d8",
        "chapters": 36,
        "lines": 854,
        "label_gaps": {},
    },
]


def norm(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def build_one(spec: dict) -> tuple[dict, dict]:
    source_path = ROOT / "readers" / "source" / "chronicles" / f"{spec['work_id']}.xml"
    raw = source_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != spec["sha256"]:
        raise ValueError(f"Pinned {spec['work_id']} checksum changed: {digest}")
    root = ET.fromstring(raw)
    if root.get(f"{{{XML}}}id") != spec["work_id"] or root.get(f"{{{XML}}}lang") != "en":
        raise ValueError(f"Unexpected {spec['work_id']} TEI identity or document-default language")
    license_node = next(
        (x for x in root.iter(f"{{{TEI}}}licence") if x.get("target", "").rstrip("/").endswith("by-sa/4.0")),
        None,
    )
    if license_node is None:
        raise ValueError(f"No file-level CC BY-SA 4.0 statement in pinned {spec['work_id']} TEI")
    edition = next((x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition"), None)
    if edition is None or edition.get(f"{{{XML}}}lang") != "gez":
        raise ValueError(f"No explicit Geʽez edition division in {spec['work_id']}")
    chapters = [x for x in edition if x.get("type") == "textpart" and x.get("subtype") == "chapter"]
    if [x.get("n") for x in chapters] != [str(i) for i in range(1, spec["chapters"] + 1)]:
        raise ValueError(f"Unexpected ordered chapter divisions in {spec['work_id']}")

    chapter_data = []
    total_lines = 0
    observed_gaps = {}
    for chapter_order, chapter in enumerate(chapters, 1):
        lines = list(chapter.iter(f"{{{TEI}}}l"))
        labels = [line.get("n") for line in lines]
        numeric_labels = [int(label) for label in labels if label and label.isdigit()]
        missing = sorted(set(str(i) for i in range(1, max(numeric_labels, default=0) + 1)) - set(labels), key=int)
        if missing:
            observed_gaps[str(chapter_order)] = missing
        units = []
        for order, line in enumerate(lines, 1):
            text = norm(line)
            unit = {
                "number": order,
                "unit_order": order,
                "source_marker": line.get("n"),
                "source_element_id": line.get(f"{{{XML}}}id"),
                "source_refs": [x.get("target") for x in line.iter(f"{{{TEI}}}ref") if x.get("target")],
                "text": text,
            }
            if not text:
                unit["source_text_state"] = "empty_source_element"
            units.append(unit)
        label = next((norm(x) for x in chapter if x.tag == f"{{{TEI}}}label"), f"Chapter {chapter_order}")
        chapter_data.append({
            "chapter": chapter_order,
            "source_chapter_label": chapter.get("n"),
            "heading": [label],
            "units": units,
            "notes": [],
        })
        total_lines += len(lines)
    if total_lines != spec["lines"] or observed_gaps != spec["label_gaps"]:
        raise ValueError(f"Unexpected line count or source-label gaps in {spec['work_id']}: {total_lines}, {observed_gaps}")

    source_url = f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/{spec['path']}"
    reader = {
        "reader_id": spec["reader_id"],
        "research_corpus_id": spec["corpus_id"],
        "text_origin": "source_transcription",
        "title": f"{spec['book']} — Geʽez TEI research transcription (EOTC link unverified)",
        "display_name": f"{spec['book']} · Geʽez · research text; EOTC link unverified",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "explicit_xml_lang_on_edition_division; document root separately declares English",
        "script_code": "Ethi",
        "edition": f"Beta maṣāḥǝft {spec['work_id']} TEI, pinned at Works commit {COMMIT}",
        "edition_scope": (
            f"The TEI title names {spec['book']} and its edition division declares Geʽez. The TEI sourceDesc is generic and it does not identify the print edition or manuscript basis of this transcription, nor state that it represents the current EOTC printed Bible. The title association is a research candidate, not a verified canon crosswalk."
        ),
        "section_label": spec["book"],
        "unit_label": "TEI line element (source n marker retained; not assumed to be a verse number)",
        "source_ids": ["SRC-029", "SRC-034", spec["source_id"]],
        "source_snapshot_sha256": digest,
        "rights_classification": "open_license",
        "copyright_notice": (
            "The retained Beta maṣāḥǝft TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link the pinned source and license, disclose extraction and whitespace normalization, and share adaptations alike. Beta maṣāḥǝft’s displayed site footer separately states CC BY-NC-SA 4.0; the relationship between those notices remains unresolved. Neither notice is treated as proof of rights in an unidentified historical print edition or manuscript witness."
        ),
        "commercial_use": "The TEI file states CC BY-SA 4.0, subject to attribution, change notice, and ShareAlike. The site also displays a separate CC BY-NC-SA 4.0 footer; the relationship between the notices and rights in the underlying, unidentified source are unresolved.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "chapter_count": len(chapter_data),
        "unit_count": total_lines,
        "source_numbered_unit_count": sum(bool(u["source_marker"]) for c in chapter_data for u in c["units"]),
        "source_unnumbered_unit_count": sum(not u["source_marker"] for c in chapter_data for u in c["units"]),
        "source_empty_unit_count": sum(not u["text"] for c in chapter_data for u in c["units"]),
        "chapter_structure_note": (
            f"The pinned TEI has {spec['chapters']} ordered chapter divisions and {total_lines} line elements. Source line labels are retained exactly. The file has unlabelled gaps in source line numbering in chapters {', '.join(observed_gaps) if observed_gaps else 'none'}; no missing labels or text are supplied. This structural audit does not establish textual completeness or accuracy."
        ),
        "transcription_note": "Every TEI line element in the Geʽez edition divisions is retained in order, with its exact source n marker and reference targets. Display whitespace is normalized and inline markup is flattened; the original pinned TEI is bundled unchanged. No wording, verse numbers, or labels are generated or corrected.",
        "chapters": chapter_data,
        "verification_status": "Pinned source hash, TEI work identity, file-level license notice, Geʽez edition declaration, ordered chapter divisions, line elements, source markers, and extraction checked. The source edition basis, textual accuracy, completeness, underlying witness rights, and EOTC canon affiliation remain unverified.",
    }
    (ROOT / "readers" / f"{spec['reader_id']}.json").write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source_record = {
        "source_id": spec["source_id"],
        "source_name": f"Beta maṣāḥǝft Works — pinned {spec['work_id']} Geʽez Chronicles TEI",
        "url": source_url,
        "inspection_and_limitations": (
            f"Retrieved from BetaMasaheft/Works commit {COMMIT} and retained unchanged at readers/source/chronicles/{spec['work_id']}.xml ({len(raw):,} bytes; SHA-256 {digest}). The TEI title is {spec['book']}; its root declares xml:lang=en and its edition div declares xml:lang=gez. The file-level licence element states CC BY-SA 4.0; the provider page separately displays a CC BY-NC-SA 4.0 site footer, and their relationship is unresolved. Its sourceDesc is generic and does not identify this transcription's printed edition or manuscript basis. The file contains {spec['chapters']} ordered chapter divisions and {total_lines} line elements; source labels are preserved verbatim. Label gaps occur in chapters {', '.join(observed_gaps) if observed_gaps else 'none'}; missing markers are not inferred. Structural checks do not establish completeness or accuracy. No current EOTC printed-Bible identification is present. Inspected 2026-10-25; no wording was generated or corrected."
        ),
        "archive_status": "Pinned file-level CC BY-SA TEI retained locally; declared language, chapter/line structure and extraction checked; conflicting site-level license notice, underlying source basis and rights, accuracy, completeness, and EOTC relationship remain unresolved",
    }
    corpus = {
        "corpus_id": spec["corpus_id"],
        "title": f"{spec['book']} (Geʽez) — Beta maṣāḥǝft TEI research transcription",
        "reader_id": spec["reader_id"],
        "unit_count": total_lines,
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": spec["canon_id"],
        "canon_mapping_note": f"The title matches the Church-list {spec['book']} entry, but the TEI does not identify a current EOTC edition or establish textual completeness, accuracy, or edition identity. This title match is a research candidate only and is excluded from canon-linked reader coverage.",
        "language_description": "The edition division explicitly declares Geʽez (gez); the TEI root separately declares English.",
        "script_description": "The retained text uses Ethiopic script (Ethi).",
        "unit_summary": f"{spec['chapters']} ordered chapter divisions and {total_lines} TEI line elements; source n markers retained exactly; label gaps recorded rather than filled.",
        "rights_classification": "open_license",
        "rights_status": "The retained TEI file states CC BY-SA 4.0. Beta maṣāḥǝft’s site footer separately states CC BY-NC-SA 4.0; their relationship is unresolved. Neither statement independently proves rights in the unidentified underlying printed text or manuscript witnesses.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "review_status": "Automated source hash, language declarations, file-level license notice, chapter sequence, line count, source markers, and extraction checked. No independent proofreading, completeness review, source-edition identification, underlying rights adjudication, or EOTC affiliation review has been performed.",
        "source_ids": ["SRC-029", "SRC-034", spec["source_id"]],
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "script_code": "Ethi",
        "translation_id": None,
        "translator": None,
        "translation_basis_status": "not_applicable_source_transcription",
        "translation_basis_note": "This is a Geʽez source transcription, not an English translation.",
        "edition_statement": f"Beta maṣāḥǝft {spec['work_id']} TEI, pinned at {COMMIT}; exact print edition and manuscript basis are not identified in the TEI sourceDesc.",
    }
    (ROOT / "readers" / "source" / "chronicles" / f"{spec['work_id']}-SOURCE-AUDIT.md").write_text(
        f"# {spec['book']} TEI source audit\n\n"
        f"Pinned BetaMasaheft/Works `{spec['work_id']}.xml` at commit `{COMMIT}`. The unchanged source file is {len(raw):,} bytes; SHA-256 `{digest}`. The title names {spec['book']}. The document root declares English while the edition division explicitly declares Geʽez (`gez`); the reader follows the edition division and preserves the conflict. The TEI file states CC BY-SA 4.0, while the provider site footer separately states CC BY-NC-SA 4.0; the relationship is unresolved. The TEI source description does not identify the exact print edition or manuscript basis.\n\n"
        f"The pinned file contains {spec['chapters']} ordered chapter divisions and {total_lines} line elements. Every line is retained in order with its source marker and reference targets. Source label gaps appear in chapters {', '.join(observed_gaps) if observed_gaps else 'none'} and remain unfilled; line markers are not assumed to be verse numbers. Display whitespace is normalized and inline markup is flattened, while the original TEI is bundled unchanged. These checks verify extraction against this file only, not completeness, accuracy, or alignment with an EOTC printed Bible. This research-only title candidate is excluded from canon-linked reader coverage.\n\n"
        f"Source: [{spec['work_id']} at pinned commit]({source_url}) · [Beta maṣāḥǝft work record](https://betamasaheft.awhamburg.de/works/{spec['work_id']}/main) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).\n",
        encoding="utf-8",
    )
    return reader, (source_record, corpus)


def build() -> list[dict]:
    built = [build_one(spec) for spec in WORKS]
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {x["source_id"]: x for x in archive["sources"]}
    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    corpora = {x["corpus_id"]: x for x in registry.get("research_corpora", [])}
    for source, corpus in (metadata for _, metadata in built):
        sources[source["source_id"]] = source
        corpora[corpus["corpus_id"]] = corpus
    archive["sources"] = sorted(sources.values(), key=lambda x: int(x["source_id"].split("-")[1]))
    registry["research_corpora"] = sorted(corpora.values(), key=lambda x: x["corpus_id"])
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return [reader for reader, _ in built]


if __name__ == "__main__":
    for result in build():
        print(f"Built {result['reader_id']}: {result['chapter_count']} chapters, {result['unit_count']} lines; EOTC affiliation remains unverified.")
