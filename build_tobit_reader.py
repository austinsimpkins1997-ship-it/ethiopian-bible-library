from __future__ import annotations
import hashlib, json, re, xml.etree.ElementTree as ET
from pathlib import Path
from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers/source/tobit/LIT2473TobitB-original.xml"
READER_ID = "tobit-geez-betamasaheft-eotced"
READER = ROOT / "readers" / f"{READER_ID}.json"
SHA256 = "d732fb21c75002ff4b8e03affc12c9dc10883d6db73154f8b0ca84334c03943e"
NS = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
SOURCES = ["SRC-029", "SRC-134", "SRC-217", "SRC-218"]


def main() -> None:
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SHA256:
        raise ValueError(f"Pinned Tobit TEI hash mismatch: {digest}")
    root = ET.fromstring(raw)
    if root.get(f"{{{XML}}}id") != "LIT2473TobitB" or root.get(f"{{{XML}}}lang") != "en":
        raise ValueError("Unexpected Tobit TEI identity or root language")
    edition = next((e for e in root.iter(f"{{{NS}}}div") if e.get("type") == "edition"), None)
    if edition is None or edition.get(f"{{{XML}}}lang") != "gez":
        raise ValueError("Tobit edition-level Ge'ez language declaration is missing")
    note = " ".join(" ".join("".join(e.itertext()).split()) for e in edition.findall(f"{{{NS}}}note"))
    if "Text of the EOTC printed Bible" not in note:
        raise ValueError("Expected the source's EOTC printed Bible note")
    license_el = next((e for e in root.iter(f"{{{NS}}}licence") if "creativecommons.org/licenses/by-sa/4.0" in e.get("target", "")), None)
    if license_el is None:
        raise ValueError("File-level CC BY-SA 4.0 license declaration missing")
    chapters = [e for e in edition if e.get("subtype") == "chapter"]
    if [c.get("n") for c in chapters] != [str(i) for i in range(1, 15)]:
        raise ValueError("Expected ordered chapter divisions 1 through 14")
    out_chapters = []
    total = 0
    for number, ch in enumerate(chapters, 1):
        label = ch.find(f"{{{NS}}}label")
        label_text = " ".join("".join(label.itertext()).split()) if label is not None else ""
        if label_text != f"Chapter {number}":
            raise ValueError(f"Unexpected chapter heading: {label_text!r}")
        lines = list(ch.iter(f"{{{NS}}}l"))
        labels = [line.get("n") for line in lines]
        if labels != [str(i) for i in range(1, len(lines) + 1)]:
            raise ValueError(f"Chapter {number} source labels are not contiguous")
        verses = []
        for line in lines:
            if list(line):
                raise ValueError(f"Unexpected inline markup in chapter {number}, line {line.get('n')}")
            text = " ".join("".join(line.itertext()).split())
            if not text:
                raise ValueError(f"Empty line in chapter {number}, label {line.get('n')}")
            verses.append({"number": int(line.get("n")), "source_marker": line.get("n"), "text": text})
        total += len(verses)
        out_chapters.append({"chapter": number, "source_chapter_label": ch.get("n"), "heading": [label_text], "verses": verses})
    if total != 242:
        raise ValueError(f"Expected 242 source lines inside chapter divisions, got {total}")
    copyright_text = "Beta maṣāḥǝft TEI file LIT2473TobitB, licensed CC BY-SA 4.0. Attribute Beta maṣāḥǝft and its contributors, identify the source snapshot and indicate this extraction; share adaptations under CC BY-SA 4.0. This file-level license applies to the TEI file and does not establish rights in the unidentified printed exemplar. The website footer carries a separate site-level license."
    reader = {
      "reader_id": READER_ID, "text_origin": "source_transcription", "canon_id": "eotc-ot-17",
      "title": "Tobit — Geʽez source transcription (Beta maṣāḥǝft TEI)",
      "language": "Geʽez (Classical Ethiopic)", "language_tag": "gez", "language_assignment_status": "source_declared_inherited_edition_xml_lang", "script_code": "Ethi",
      "section_label": "Chapter", "source_ids": SOURCES,
      "edition": "Beta maṣāḥǝft LIT2473TobitB TEI snapshot, pinned at Works commit 9029473659ab6efc4035ee52b9922192c99ba75e",
      "edition_scope": "The retained TEI contains one edition division explicitly tagged xml:lang=\"gez\" and a source note reading \"Text of the EOTC printed Bible\". Its root has xml:lang=\"en\"; TEI language inheritance means the explicit edition-level gez applies to the nested text. The file cites Dillmann 1894, pp. 11–27, and says this text was digitized from modern Vulgata printed editions, but does not identify the exact printed exemplar. This archive links it provisionally to Church-list Tobit (eotc-ot-17); identity with the list's intended text, print collation, completeness, and transcription accuracy are not established.",
      "transcription_note": "Extracted all 242 numbered TEI line elements from the 14 explicit chapter divisions in source order. Ge'ez text is retained, with whitespace normalized to single spaces. Chapter and line labels are preserved; no labels, wording, translation, or alignment have been invented. The unchanged XML is retained locally.",
      "editorial_signs_note": "No inline markup occurs within the extracted line elements. TEI header, bibliography, and surrounding metadata remain in the source XML; the display reader is an extraction, not a replacement for that file.",
      "chapter_structure_note": "Fourteen chapter divisions labeled 1–14; each chapter's line labels are contiguous from 1 through its observed final label; 242 nonempty numbered lines total. These counts establish the retained TEI's structure only, not completeness against the printed source or a manuscript.",
      "rights_classification": "open_license", "copyright_notice": copyright_text,
      "commercial_use": "The file-level CC BY-SA 4.0 permits sharing and adaptation, including commercially, subject to attribution, indication of changes, and ShareAlike terms. This is the TEI file's stated license; it does not establish rights in the unidentified printed exemplar or alter the website's separate footer license.",
      "license_id": "CC-BY-SA-4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
      "chapter_count": 14, "unit_count": 242, "unit_label": "numbered TEI line element within an explicitly labeled chapter", "source_numbered_unit_count": 242, "source_unnumbered_unit_count": 0,
      "verification_status": "Pinned source hash and TEI structure verified locally: one edition-level gez declaration; source note identifies an EOTC printed Bible; 14 ordered chapters and 242 contiguous numbered, nonempty lines; no inline line markup. This does not verify wording against print/manuscripts, exact print exemplar, textual accuracy, complete coverage of the physical edition, or the Church-list crosswalk.",
      "source_pages": "readers/source/tobit/LIT2473TobitB-original.xml (unchanged TEI snapshot; SHA-256 recorded below)", "source_snapshot_sha256": digest,
      "additional_notes": "No English companion is included. Brenton's English Tobit is a separate translation from a Greek Septuagint base; alignment with this Ge'ez text is unverified.", "chapters": out_chapters
    }
    READER.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    archive["sources"] = [s for s in archive["sources"] if s.get("source_id") != "SRC-218"]
    for source in archive["sources"]:
      if source.get("source_id") == "SRC-217":
        source["inspection_and_limitations"] = "The provider text page identifies Tobit (LIT2473TobitB), a text added 2025-06-05, digitized from modern Vulgata printed editions and converted to XML; it cites Dillmann 1894, pp. 11–27. Direct retrieval of this page returned 502 in this environment, so the page itself was not captured. The corresponding pinned BetaMasaheft/Works TEI file was independently retrieved and audited as SRC-218 and retained locally; that file explicitly declares the edition language gez, identifies its source as text of the EOTC printed Bible, states a file-level CC BY-SA 4.0 license, and contains 14 ordered chapters/242 numbered lines. The exact printed exemplar, physical-edition completeness, transcription accuracy, and precise Church-list crosswalk remain unverified. Retrieved/audited 2026-10-25."
    archive["sources"].append({
      "source_id": "SRC-218", "source_name": "Beta maṣāḥǝft Works — pinned LIT2473TobitB TEI source snapshot",
      "url": "https://github.com/BetaMasaheft/Works/blob/9029473659ab6efc4035ee52b9922192c99ba75e/2001-3000/LIT2473TobitB.xml",
      "inspection_and_limitations": "Retrieved 2026-10-25 from BetaMasaheft/Works commit 9029473659ab6efc4035ee52b9922192c99ba75e and retained unchanged at readers/source/tobit/LIT2473TobitB-original.xml (67,610 bytes; SHA-256 d732fb21c75002ff4b8e03affc12c9dc10883d6db73154f8b0ca84334c03943e). TEI root xml:id is LIT2473TobitB and xml:lang=en; the enclosing edition division explicitly declares xml:lang=gez and contains the note 'Text of the EOTC printed Bible'. The file-level availability statement declares CC BY-SA 4.0. Structural audit: 14 ordered chapter divisions, 242 numbered nonempty lines with contiguous labels within chapters. TEI header cites Dillmann 1894, pp. 11–27, and says the text was digitized from modern Vulgata printed editions; no exact exemplar is identified. Structural extraction is not a collation: text accuracy, completeness against print/manuscripts, and exact EOTC Church-list identity remain unverified. The file-level license does not establish rights in the source print exemplar. Retrieved and audited 2026-10-25.",
      "archive_status": "Pinned source TEI retained locally; edition structure, explicit language declaration, source note, and file-level license inspected; text accuracy and physical-edition completeness unverified"
    })
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for lead in registry.get("edition_leads", []):
      if lead.get("edition_id") == "betamasaheft-tobit-tei-vulgata-2025":
        lead.update({"mapping_state": "uncertain", "text_bundled": False, "bundled_reader_id": READER_ID,
          "scope_description": "The pinned TEI edition division explicitly declares Ge'ez (xml:lang=gez) and states 'Text of the EOTC printed Bible'; these support a provisional title-level link to Church-list Tobit. The reader bundles a structural extraction of 14 chapter divisions and 242 numbered lines. The root xml:lang=en is retained as a document-default conflict; the edition-level declaration applies to its nested text. The exact printed exemplar, textual accuracy, completeness against the physical edition, and exact Church-list crosswalk remain unverified. The cited 1894 Dillmann pages and modern Vulgata statement do not identify this exact witness.",
          "source_ids": ["SRC-134", "SRC-217", "SRC-218", "SRC-029"],
          "rights_status": "The retained TEI file itself declares CC BY-SA 4.0; attribute Beta maṣāḥǝft, indicate this extraction and changes, and share adaptations alike. The website footer is a separate site-level notice. This file-level license does not establish rights in the unidentified printed exemplar.",
          "rights_classification": "open_license", "license_id": "CC-BY-SA-4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
          "review_status": "Pinned TEI snapshot audited for file hash, edition-level language, source note, chapter divisions, labels, nonempty lines, and file-level license. Reader extraction covers all 242 TEI lines in its 14 chapter divisions. Text accuracy, physical-print completeness, exact exemplar, and EOTC list crosswalk remain unverified."})
    gez = next(x for x in registry.get("languages", []) if x.get("language_tag") == "gez")
    gez["records"] = [r for r in gez.get("records", []) if r.get("reader_id") != READER_ID]
    gez["records"].append({"canon_id": "eotc-ot-17", "reader_id": READER_ID, "layer_role": "source_text_transcription", "status": "bundled", "basis_language_tag": "gez", "basis_description": "Beta maṣāḥǝft TEI edition explicitly tagged Ge'ez; extraction preserves source chapter and line labels. Accuracy and physical-edition completeness remain unverified.", "rights_status": "CC BY-SA 4.0 (file-level TEI license; exemplar rights not established)", "rights_classification": "open_license", "source_ids": SOURCES})
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit = f'''# Tobit TEI source snapshot and structural audit\n\n- Source: [Beta maṣāḥǝft LIT2473TobitB](https://betamasaheft.awhamburg.de/works/LIT2473TobitB/main); pinned source file: [Works commit 9029473659ab6efc4035ee52b9922192c99ba75e](https://github.com/BetaMasaheft/Works/blob/9029473659ab6efc4035ee52b9922192c99ba75e/2001-3000/LIT2473TobitB.xml).\n- Local snapshot: `LIT2473TobitB-original.xml` (67,610 bytes; SHA-256 `{digest}`).\n- The TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, identify the source and changes, and share adaptations under CC BY-SA 4.0. This item-level license is distinct from the website footer and does not establish rights in the unidentified printed exemplar.\n- TEI root `xml:lang="en"`; enclosing `div type="edition"` explicitly has `xml:lang="gez"`. Under TEI language inheritance the edition declaration applies to nested text. The source note reads “Text of the EOTC printed Bible.”\n- The edition contains 14 ordered chapter divisions and 242 numbered, nonempty `l` elements. Labels in every chapter are contiguous from 1 to that chapter's final observed label. The unchanged XML is retained; display extraction normalizes whitespace only.\n\nThis audit establishes file identity, declared language, license statement, and structural extraction. It does not collate the TEI against Dillmann's 1894 edition or any other printed witness, identify the exact print exemplar, establish accuracy or physical-edition completeness, or prove that this is the exact text intended by the Church-list Tobit entry. The Church-list crosswalk remains provisional. No English translation or cross-witness alignment is asserted.\n'''
    (ROOT / "readers/source/tobit/SOURCE-BOUNDARY.md").write_text(audit, encoding="utf-8")
    # Portable v2 metadata example is generated from a complete existing schema record.
    template = json.loads((ROOT / "examples/amos-geez-pereira-layer.json").read_text(encoding="utf-8"))
    reader_hash = hashlib.sha256(READER.read_bytes()).hexdigest()
    record = template
    base = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
    record.update({
      "record_id": f"{base}/layer/{READER_ID}", "work_id": f"{base}/work/tobit-betamasaheft-tei-candidate",
      "labels": [{"value": "Tobit — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"}],
      "tradition_assertions": [{"tradition_id": f"{base}/tradition/eotc", "canon_id": f"{base}/canon/eotc-ot-17", "mapping_state": "uncertain", "evidence_source_ids": SOURCES, "notes": "The TEI edition note says EOTC printed Bible and declares Geʽez; this supports a candidate link only. Exact Church-list witness identity remains unverified."}],
      "witness": {"witness_id": f"{base}/witness/betamasaheft-LIT2473TobitB", "witness_type": "digital_edition", "title": "Beta maṣāḥǝft LIT2473TobitB TEI text", "date_statement": "Text added to the TEI record 2025-06-05; exact print exemplar date not stated", "repository_or_publisher": "Beta maṣāḥǝft, University of Hamburg", "shelfmark_or_edition_id": "LIT2473TobitB; CAe 2473", "editorial_policy": "Provider says the text was digitized from modern Vulgata printed editions and converted to XML; exact exemplar is not identified.", "source_ids": ["SRC-134", "SRC-217", "SRC-218"]},
      "layer_type": "source_text_transcription", "text_origin": "source_transcription", "language_tag": "gez", "language_name_as_recorded": "Geʽez (Classical Ethiopic)", "script_code": "Ethi", "basis_path": ["gez"], "agents": [],
      "content_package": {"uri": "../readers/tobit-geez-betamasaheft-eotced.json", "media_type": "application/json", "sha256": reader_hash, "format_version": "1"},
      "coverage": {"extent_state": "complete_for_declared_edition", "extent_basis": "source_inventory", "unit_count": 242, "structure_description": "All 242 numbered line elements in the retained edition division are included across 14 explicit chapters. Completeness against the physical printed source has not been independently checked.", "missing_or_lacunose_ranges": [], "supplements_and_editorial_signs": "Whitespace normalized; no line-level inline markup was present. Unchanged TEI retained locally.", "numbering_policy": "Preserve TEI chapter and line labels as observed; archive display order matches those labels. No labels are inferred."},
      "rights": {"status": "open_license", "statement": "The TEI file declares CC BY-SA 4.0. Attribute Beta maṣāḥǝft, indicate changes, and share adaptations alike. The license does not establish rights in the unidentified printed exemplar.", "license_id": "CC-BY-SA-4.0", "rights_holder": "Beta maṣāḥǝft TEI file; underlying print rights not established", "attribution_required": True, "territory_or_term_limits": "Apply the file-level license to the TEI file and its adaptation only; do not infer rights in the unidentified printed source.", "evidence_source_ids": ["SRC-218"]},
      "review_dimensions": [
        {"dimension": "identity", "state": "checked_with_limits", "scope": "TEI work id and title checked; physical exemplar and exact Church-list identity unresolved.", "reviewer": None, "review_method": "source_inspection", "review_process": "Pinned TEI header and edition inspected", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-134", "SRC-218"], "notes": "Candidate mapping only."},
        {"dimension": "language_identification", "state": "checked_with_limits", "scope": "Root xml:lang=en and enclosing edition xml:lang=gez inspected.", "reviewer": None, "review_method": "source_inspection", "review_process": "TEI language inheritance and edition division inspected", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-218"], "notes": "Explicit edition language governs nested text; root default retained as conflict."},
        {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "14 ordered chapter divisions and 242 nonempty numbered lines validated against pinned TEI.", "reviewer": None, "review_method": "automated_validation", "review_process": "build_tobit_reader.py checksum and TEI structure assertions", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-218"], "notes": "Structure only; no independent print completeness claim."},
        {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No collation against the cited Dillmann 1894 pages, another printed exemplar, or manuscripts.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-134", "SRC-218"], "notes": "Accuracy remains unverified."},
        {"dimension": "completeness", "state": "unknown", "scope": "Completeness against the physical print edition or manuscript tradition not assessed.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-134", "SRC-218"], "notes": "All source TEI chapter lines were extracted; physical-edition completeness is unknown."},
        {"dimension": "rights", "state": "checked_with_limits", "scope": "File-level TEI availability licence inspected.", "reviewer": None, "review_method": "source_inspection", "review_process": "Retained TEI license declaration and separated it from the site footer", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-218"], "notes": "Underlying print rights not established."}
      ],
      "publication_state": "bundled", "community_access_note": None,
      "additional_notes": "No English translation is included. Brenton's English Tobit has a Greek Septuagint basis and is an independent witness; alignment is unverified."
    })
    (ROOT / "examples/tobit-geez-betamasaheft-layer.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {READER_ID}: 14 chapters, {total} numbered lines; source SHA-256 {digest}")

if __name__ == "__main__":
    main()



