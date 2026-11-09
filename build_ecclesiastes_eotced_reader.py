"""Build the scoped EOTCed Ecclesiastes reader from its checked extract."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "readers/source/ecclesiastes/LIT1320Eccles-EOTCed.xml"
SOURCE_SHA256 = "13f0c8e77d7a202b083cf74666a1877bf6533d036a4042b4f2841999587833e1"
UPSTREAM_SHA256 = "3af9fd2b36b52278058cd3278717690eeff3d30e4054b743eca70c96c1311b35"
COMMIT = "2574a6c84ed477af76122a6b112df3bbf45a96f5"
WORK_ID = "LIT1320Eccles"
READER_ID = "ecclesiastes-geez-betamasaheft-eotced"
CANON_ID = "eotc-ot-27"
CATALOGUE_ID = "eotc-032"
SOURCE_FILE_ID = "SRC-294"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"


def norm(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def build() -> dict:
    raw = SOURCE_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"EOTCed Ecclesiastes extract checksum changed: {digest}")
    root = ET.fromstring(raw)
    if root.tag != f"{{{TEI}}}TEI" or root.get(f"{{{XML}}}lang") != "en":
        raise ValueError("Unexpected TEI extract wrapper")
    editions = [x for x in root.iter(f"{{{TEI}}}div") if x.get(f"{{{XML}}}id") == "EOTCed"]
    if len(editions) != 1 or editions[0].get(f"{{{XML}}}lang") != "gez":
        raise ValueError("Extract must contain exactly one Geʽez EOTCed division")
    edition = editions[0]
    if "Text of the EOTC printed Bible" not in [norm(x) for x in edition.iter(f"{{{TEI}}}note")]:
        raise ValueError("Source scope note missing")
    chapters_source = [x for x in edition if x.tag == f"{{{TEI}}}div"]
    if [x.get("n") for x in chapters_source] != [str(i) for i in range(1, 13)]:
        raise ValueError("Expected the 12 ordered source chapter divisions")

    chapters = []
    total_lines = total_refs = empty = 0
    for number, division in enumerate(chapters_source, 1):
        lines = list(division.iter(f"{{{TEI}}}l"))
        units = []
        for order, line in enumerate(lines, 1):
            text = norm(line)
            refs = [ref.get("target") for ref in line.iter(f"{{{TEI}}}ref") if ref.get("target")]
            units.append({
                "number": order,
                "unit_order": order,
                "source_marker": line.get("n"),
                "source_element_id": line.get(f"{{{XML}}}id"),
                "source_refs": refs,
                "text": text,
            })
            total_refs += len(refs)
            empty += not bool(text)
        label = next((norm(x) for x in division if x.tag == f"{{{TEI}}}label"), str(number))
        chapters.append({
            "chapter": number,
            "source_chapter_label": division.get("n"),
            "heading": [label],
            "units": units,
            "notes": [],
        })
        total_lines += len(lines)
    if (total_lines, total_refs, empty) != (226, 222, 0):
        raise ValueError(f"Unexpected source structure: lines={total_lines}, refs={total_refs}, empty={empty}")
    last = chapters[-1]["units"]
    if [(u["source_marker"], u["source_refs"][0].rsplit("=", 1)[-1] if u["source_refs"] else None)
            for u in last[12:]] != [(str(i), str(i - 3)) for i in range(13, 18)]:
        raise ValueError("Chapter 12 source markers and linked reference targets changed")

    reader = {
        "reader_id": READER_ID,
        "canon_id": CANON_ID,
        "text_origin": "source_transcription",
        "title": "Ecclesiastes — Geʽez EOTCed text transcription",
        "display_name": "Ecclesiastes · Geʽez · EOTCed text",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "explicit_xml_lang_on_EOTCed_edition; document root separately declares English",
        "script_code": "Ethi",
        "edition": f"Beta maṣāḥǝft {WORK_ID} TEI, EOTCed division, source file pinned at Works commit {COMMIT}",
        "edition_scope": (
            "The selected division is explicitly tagged Geʽez and labeled ‘Text of the EOTC printed Bible.’ "
            "The source record says the text was digitized from modern Vulgata printed editions and converted "
            "to XML; the exact print exemplar and relation between these descriptions are not identified. "
            "The separate Mercer edition and its noncommercial transcription are excluded from this extract. "
            "This supports a source-asserted title link, not exact print-edition identity."
        ),
        "section_label": "Ecclesiastes",
        "unit_label": "TEI line element (source n marker and reference target preserved separately; not verified as a verse number)",
        "source_ids": ["SRC-029", "SRC-176", "SRC-279", SOURCE_FILE_ID],
        "source_snapshot_sha256": digest,
        "upstream_source_sha256": UPSTREAM_SHA256,
        "rights_classification": "open_license",
        "copyright_notice": (
            "The pinned TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link the pinned source and "
            "license, disclose extraction and whitespace normalization, and share adaptations alike. The source "
            "file also contains a distinct Mercer transcription with noncommercial terms; that division is not "
            "included here. The exact EOTC print exemplar and underlying print rights remain unresolved, so the file-level "
            "notice is not treated as proof of rights in that printed edition. The provider site footer separately "
            "states CC BY-NC-SA 4.0; the relationship between notices remains unresolved."
        ),
        "commercial_use": "The file states CC BY-SA 4.0; site footer separately states CC BY-NC-SA 4.0 and their relationship is unresolved. The separate Mercer transcription is excluded; underlying print rights are not established.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE_URL,
        "chapter_count": 12,
        "unit_count": total_lines,
        "source_numbered_unit_count": total_lines,
        "source_unnumbered_unit_count": 0,
        "source_empty_unit_count": empty,
        "chapter_structure_note": (
            "The EOTCed division has 12 ordered TEI chapter divisions, 226 nonempty line elements and 222 "
            "reference links. Line n markers are not assumed to be verse numbers. In chapter 12, markers 13–17 "
            "link to targets 10–14; both values are retained distinctly. Structure alone does not establish "
            "accuracy or completeness against the unidentified print exemplar."
        ),
        "transcription_note": (
            "Every TEI line element from the selected EOTCed division is retained in order with its source n "
            "marker and linked reference targets. Display whitespace is normalized and inline markup flattened. "
            "The bundled XML extract contains only the EOTCed division, not the separate Mercer transcription. "
            "No wording or source markers are corrected."
        ),
        "chapters": chapters,
        "verification_status": (
            "Pinned upstream file identity and SHA-256, EOTCed-only extract hash, TEI identity, Geʽez declaration, "
            "EOTC printed-Bible note, 12 chapter divisions, 226 line elements, 222 reference links, and the "
            "chapter 12 marker/target offset checked. The separate Mercer division is excluded. Exact print "
            "exemplar, underlying print rights, relationship of license notices, textual accuracy, and completeness "
            "remain unresolved; no independent collation was performed."
        ),
    }
    reader_path = ROOT / "readers" / f"{READER_ID}.json"
    reader_path.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    layer_path = ROOT / "examples/ecclesiastes-geez-betamasaheft-layer.json"
    if layer_path.exists():
        layer = json.loads(layer_path.read_text(encoding="utf-8"))
        layer["content_package"]["sha256"] = hashlib.sha256(reader_path.read_bytes()).hexdigest()
        layer_path.write_text(json.dumps(layer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    source_map = {x["source_id"]: x for x in archive["sources"]}
    source_map[SOURCE_FILE_ID] = {
        "source_id": SOURCE_FILE_ID,
        "source_name": f"Beta maṣāḥǝft Works — pinned {WORK_ID} EOTCed-only extract",
        "url": f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/1001-2000/{WORK_ID}.xml",
        "inspection_and_limitations": (
            f"Upstream source pinned at {COMMIT}; full file SHA-256 {UPSTREAM_SHA256} (152,281 bytes). "
            f"The public extract at readers/source/ecclesiastes/LIT1320Eccles-EOTCed.xml is {len(raw):,} bytes, "
            f"SHA-256 {digest}, and contains only the division tagged xml:id=EOTCed and xml:lang=gez. It is "
            "labeled ‘Text of the EOTC printed Bible.’ It has 12 ordered chapter divisions, 226 nonempty TEI "
            "lines, and 222 reference links. Chapter 12 line markers 13–17 link to targets 10–14; marker and "
            "target are kept separately. The distinct Mercer division with noncommercial terms is excluded. "
            "The TEI file states CC BY-SA 4.0; exact print exemplar and underlying rights are not identified, and "
            "the provider site's separate CC BY-NC-SA footer remains unexplained. Accuracy and completeness were "
            "not independently checked."
        ),
        "archive_status": "EOTCed-only extract and structure checked; separate Mercer transcription excluded; exact print exemplar, underlying rights, accuracy, and completeness unresolved",
    }
    archive["sources"] = sorted(source_map.values(), key=lambda x: int(x["source_id"].split("-")[1]))
    entry = next(x for x in archive["catalogue"] if x.get("catalogue_id") == CATALOGUE_ID)
    entry.update({
        "identity_status": "Beta maṣāḥǝft has a Geʽez division labeled ‘Text of the EOTC printed Bible’; exact print exemplar not identified",
        "edition_or_translation": f"Beta maṣāḥǝft {WORK_ID}, EOTCed division; pinned at Works commit {COMMIT}",
        "chapter_count": "12 ordered EOTCed source divisions; completeness against print exemplar unverified",
        "chapter_order_status": "Explicit EOTCed divisions 1–12 observed; no collation against print exemplar",
        "text_availability_status": "Scoped EOTCed-only Geʽez transcription bundled; underlying print rights remain unresolved, and exact printed exemplar, accuracy, and completeness remain unverified",
        "completeness_status": "226 TEI lines and 222 reference links; line markers are not treated as verse counts; completeness against the unidentified print exemplar not assessed",
        "rights_status": "Pinned TEI file states CC BY-SA 4.0; separate Mercer noncommercial division is excluded; provider site footer separately states CC BY-NC-SA 4.0; exact EOTC print rights and notice relationship remain unresolved",
        "verification_date": "2026-10-25",
        "reviewer_notes": reader["verification_status"],
        "source_id": "SRC-279",
        "evidence_source_ids": list(dict.fromkeys(entry.get("evidence_source_ids", []) + reader["source_ids"])),
    })
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {x["edition_id"]: x for x in registry.get("edition_leads", [])}
    leads["betamasaheft-ecclesiastes-eotced"] = {
        "edition_id": "betamasaheft-ecclesiastes-eotced",
        "candidate_canon_id": CANON_ID,
        "mapping_state": "asserted_by_source",
        "title": "Ecclesiastes — Beta maṣāḥǝft EOTCed Geʽez text",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": "EOTCed division explicitly labels itself ‘Text of the EOTC printed Bible’; source also describes digitization from modern Vulgata printed editions. Exact exemplar and relation between descriptions unresolved.",
        "scope_description": "A scoped extract bundles 12 ordered chapters and 226 source line elements with 222 linked references. Source marker and reference target remain separate. This supports a source-asserted title link, not proof of exact print edition, accuracy, or completeness.",
        "source_ids": reader["source_ids"],
        "text_bundled": False,
        "bundled_reader_id": READER_ID,
        "rights_status": reader["copyright_notice"],
        "rights_classification": "open_license",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE_URL,
        "review_status": reader["verification_status"],
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda x: x["edition_id"])
    gez = next(x for x in registry["languages"] if x.get("language_tag") == "gez")
    records = {x["reader_id"]: x for x in gez.get("records", [])}
    records[READER_ID] = {
        "canon_id": CANON_ID,
        "reader_id": READER_ID,
        "layer_role": "source_text_transcription",
        "status": "bundled",
        "basis_language_tag": "gez",
        "basis_description": "EOTCed is explicitly tagged Geʽez and labeled EOTC printed-Bible text; the source also gives a generic modern-Vulgata digitization statement. Exact printed exemplar, accuracy, and completeness unresolved.",
        "rights_status": reader["copyright_notice"],
        "rights_classification": "open_license",
        "source_ids": reader["source_ids"],
    }
    gez["records"] = sorted(records.values(), key=lambda x: x["reader_id"])
    registry["edition_leads"] = sorted(leads.values(), key=lambda x: x["edition_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (ROOT / "research/ecclesiastes-source-audit.md").write_text(
        "# Ecclesiastes source review\n\n"
        f"Inspected the pinned [Beta maṣāḥǝft TEI file](https://github.com/BetaMasaheft/Works/blob/{COMMIT}/1001-2000/{WORK_ID}.xml) "
        f"and its [work text page](https://betamasaheft.awhamburg.de/works/{WORK_ID}/text). The full upstream file is 152,281 bytes "
        f"(SHA-256 `{UPSTREAM_SHA256}`). The public extract `{SOURCE_PATH.relative_to(ROOT).as_posix()}` is {len(raw):,} bytes "
        f"(SHA-256 `{digest}`) and contains only the EOTCed division; the separate Mercer division is excluded.\n\n"
        "The selected division declares Geʽez and is labeled ‘Text of the EOTC printed Bible.’ The work record says it was digitized "
        "from modern Vulgata printed editions and converted to XML; the exact print exemplar and relation between these descriptions "
        "are not specified. The pinned TEI file has a CC BY-SA 4.0 notice. The same compound file gives the separate Mercer transcription "
        "noncommercial terms. The source site's footer separately states CC BY-NC-SA 4.0. These notices do not establish rights in the "
        "unidentified EOTC printed exemplar; the uncertainty is disclosed with the reader.\n\n"
        "Structural observation: the selected division has 12 ordered chapters, 226 nonempty TEI line elements, and 222 reference links. "
        "Every line's `n` marker and every linked target are retained separately. In chapter 12, line markers 13–17 link to targets 10–14. "
        "These are structural observations, not a claim that line markers equal verse numbers. No independent proofreading, collation, or "
        "completeness check against a specific printed exemplar was performed. The text is source-asserted to the catalogue title; exact "
        "edition identity, accuracy, and completeness remain unverified.\n",
        encoding="utf-8",
    )
    return reader


if __name__ == "__main__":
    result = build()
    print(f"Built {result['reader_id']}: {result['chapter_count']} chapters, {result['unit_count']} source lines, 222 source references.")
