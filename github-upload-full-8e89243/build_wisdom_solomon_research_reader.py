"""Build a pinned, research-only Wisdom of Solomon reader from TEI edition 2.

The published package contains a rights-scoped TEI extract of explicitly
Geʽez `ed2`; the separately restricted Dillmann-derived `ed1` is never copied.
The full upstream snapshot is held outside the deployment tree. This reader
remains outside canon-linked coverage because the EOTC catalogue entry is
grouped and its exact work identity is unresolved.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

from coverage_summary import build_coverage_statement


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers" / "source" / "wisdom-of-solomon-LIT2516Wisdom-ed2-only.xml"
OUTPUT = ROOT / "readers" / "wisdom-solomon-betamasaheft-tei-research.json"
REGISTRY = ROOT / "translation-registry.json"
ARCHIVE = ROOT / "archive.json"
SOURCE_ID = "SRC-177"
SOURCE_COMMIT = "7c13d460bef940950b9405320acc34b9d23a2d92"
SOURCE_PATH = "2001-3000/LIT2516Wisdom.xml"
SOURCE_URL = f"https://github.com/BetaMasaheft/Works/blob/{SOURCE_COMMIT}/{SOURCE_PATH}"
SOURCE_RAW_URL = f"https://raw.githubusercontent.com/BetaMasaheft/Works/{SOURCE_COMMIT}/{SOURCE_PATH}"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
CORPUS_ID = "betamasaheft-wisdom-solomon-ed2-research"
READER_ID = "wisdom-solomon-betamasaheft-tei-research"
CANON_CANDIDATE = "eotc-ot-26"
FULL_SOURCE_SHA256 = "c2e15da4893ba597bbf6afee3fb5ddbeac44c02a317a0b4384b4c2624cea5747"
EXPECTED_EXTRACT_SHA256 = "1fb77c264b07f5113b84a207eea4e1a2aedc9bf55bfeb3ee9631f44369019b93"
NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML = "{http://www.w3.org/XML/1998/namespace}"


def plain_text(element: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def build() -> dict:
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_EXTRACT_SHA256:
        raise ValueError("LIT2516Wisdom ed2-only extract checksum mismatch; re-audit the rights-scoped source capture.")

    root = ET.fromstring(raw)
    if root.get(XML + "id") != "LIT2516Wisdom":
        raise ValueError("Expected the pinned LIT2516Wisdom TEI work record.")
    titles = [plain_text(node) for node in root.findall(".//tei:titleStmt/tei:title", NS)]
    if "Wisdom of Solomon" not in titles:
        raise ValueError("Pinned TEI no longer identifies the work as Wisdom of Solomon.")

    editions = root.findall(".//tei:body/tei:div[@type='edition']", NS)
    edition2 = next((node for node in editions if node.get(XML + "id") == "ed2"), None)
    edition1 = next((node for node in editions if node.get(XML + "id") == "ed1"), None)
    if edition2 is None or edition1 is not None:
        raise ValueError("The public source extract must retain ed2 and exclude the separately restricted ed1 body.")
    if edition2.get(XML + "lang") != "gez":
        raise ValueError("Edition 2 no longer explicitly declares Geʽez (gez).")
    if root.get(XML + "lang") != "en":
        raise ValueError("The TEI root language changed; reassess language inheritance before extraction.")

    license_nodes = root.findall(".//tei:publicationStmt/tei:availability/tei:licence", NS)
    if not any(node.get("target", "").rstrip("/") == "http://creativecommons.org/licenses/by-sa/4.0"
               for node in license_nodes):
        raise ValueError("The pinned source no longer carries the inspected CC BY-SA 4.0 file license.")
    license_text = " ".join(plain_text(node) for node in license_nodes)
    if "edition 1" not in license_text.casefold() or "NONCOMMERCIAL" not in license_text:
        raise ValueError("The separate edition 1 noncommercial terms changed; re-audit scope and rights.")

    chapter_divisions = edition2.findall("tei:div[@type='textpart'][@subtype='chapter']", NS)
    expected_chapters = [str(number) for number in range(1, 20)]
    observed_chapters = [chapter.get("n") for chapter in chapter_divisions]
    if observed_chapters != expected_chapters:
        raise ValueError(f"Edition 2 chapter labels/order changed: {observed_chapters!r}.")

    edition_notes = [plain_text(node) for node in edition2.findall("tei:note", NS) if plain_text(node)]
    chapters = []
    total_lines = 0
    for chapter_number, division in enumerate(chapter_divisions, start=1):
        label = division.get("n")
        lines = division.findall(".//tei:l", NS)
        markers = [line.get("n") for line in lines]
        expected_markers = [str(number) for number in range(1, len(lines) + 1)]
        if markers != expected_markers:
            raise ValueError(f"Edition 2 chapter {label} line labels are missing, duplicated, or reordered.")
        units = []
        for order, line in enumerate(lines, start=1):
            text = plain_text(line)
            if not text:
                raise ValueError(f"Empty TEI line at chapter {label}, source label {order}.")
            units.append({
                "unit_order": order,
                "source_marker": line.get("n"),
                "source_element_id": line.get(XML + "id"),
                "text": text,
            })
        total_lines += len(units)
        heading = division.find("tei:label", NS)
        chapters.append({
            "chapter": chapter_number,
            "source_chapter_label": label,
            "heading": [plain_text(heading)] if heading is not None and plain_text(heading) else [],
            "units": units,
        })
    if total_lines != 463:
        raise ValueError(f"Expected 463 edition 2 TEI line elements, found {total_lines}.")

    reader = {
        "reader_id": READER_ID,
        "research_corpus_id": CORPUS_ID,
        "reader_scope": "research_witness_unmapped",
        "title": "Wisdom of Solomon — Beta maṣāḥǝft LIT2516Wisdom TEI edition 2 (Geʽez research text)",
        "display_name": "Wisdom of Solomon (Geʽez TEI ed2; research witness)",
        "text_origin": "source_transcription",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "explicit_on_edition2_div; root_default_en_retained_as_context",
        "script_code": "Ethi",
        "edition": "Beta maṣāḥǝft LIT2516Wisdom, edition ed2; source snapshot pinned to " + SOURCE_COMMIT,
        "edition_scope": (
            "The TEI identifies the work as Wisdom of Solomon and edition ed2 as text of the EOTC printed Bible, "
            "digitized from modern Vulgata printed editions. The physical print exemplar and date are not identified. "
            "The enclosing ed2 div explicitly declares xml:lang=gez; the TEI root's xml:lang=en is preserved as a "
            "document default and is not applied over the more local edition declaration. The separate Dillmann-derived "
            "ed1 is excluded. The source's EOTC label does not establish an exact current edition or its identity with "
            "the Church list's grouped ‘Metsihafe Tibeb (books of wisdom)’ entry."
        ),
        "rights_classification": "open_license",
        "copyright_notice": (
            "The TEI file states CC BY-SA 4.0 and separately gives edition 1 noncommercial terms. This reader extracts "
            "only edition 2; it is an adaptation that flattens inline TEI markup, normalizes whitespace, and converts "
            "the chapter/line structure to JSON. Attribute Beta maṣāḥǝft and cite LIT2516Wisdom ed2, indicate these "
            "changes, link the license, and distribute this adaptation under CC BY-SA 4.0. The source file and its "
            "license do not relicense unrelated website content. The exact legal scope for the underlying printed "
            "exemplar has not been independently determined."
        ),
        "commercial_use": (
            "The selected ed2 text is included under the TEI file's CC BY-SA 4.0 notice, with attribution, change "
            "notice, and share-alike conditions. The distinct ed1 noncommercial text is excluded. This statement is "
            "limited to this source-derived research reader, not the whole site or any unidentified print exemplar."
        ),
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE_URL,
        "chapter_count": len(chapters),
        "unit_count": total_lines,
        "unit_label": "TEI line",
        "section_label": "Chapter",
        "chapter_structure_note": (
            "The pinned ed2 contains 19 ordered divisions labeled 1–19 and 463 nonempty <l> elements. Each chapter's "
            "source line labels run sequentially from 1 through that chapter's final label. The reader retains each "
            "source label and an independent navigation order; these are TEI line elements, not a claim about verse "
            "numbering or printed-edition completeness."
        ),
        "transcription_note": (
            "Text is extracted only from the pinned TEI ed2, in source chapter and line order. Inline markup is flattened "
            "and whitespace normalized for display; the ed2-only TEI extract remains alongside the reader so retained "
            "markup and witness references can be inspected. The full upstream file is not bundled because it also "
            "contains ed1 text with separate noncommercial/no-sale terms. This is not an independent collation against "
            "print or manuscripts."
        ),
        "editorial_signs_note": (
            "The source's edition-level note says ‘Text of the EOTC printed Bible’; this is the record's identification, "
            "not independent confirmation of a specific edition. The TEI lists witnesses BLadd16186#ms_i4, "
            "BLadd16189#ms_i4, and BNFet8#ms_i4. The reader does not identify these as the physical exemplar of ed2."
            + (" TEI edition note(s): " + "; ".join(edition_notes) if edition_notes else "")
        ),
        "verification_status": (
            "Research-only Geʽez text extracted from the pinned LIT2516Wisdom TEI ed2. Automated checks confirm the "
            "source checksum, explicit ed2 xml:lang=gez scope, 19 sequential chapter divisions, and all 463 nonempty "
            "line elements with sequential source labels; every extracted line matches one source element in order. "
            "These checks establish structural extraction from this TEI snapshot only. Completeness against the stated "
            "printed edition, transcription accuracy, exact print exemplar, relationship to the grouped EOTC catalogue "
            "entry, and manuscript collation remain unknown. Not a canon-linked reader and not counted as an EOTC canon reader or toward EOTC book coverage."
        ),
        "source_ids": [SOURCE_ID],
        "source_pages": "readers/source/wisdom-of-solomon-LIT2516Wisdom-ed2-only.xml (rights-scoped TEI extract; ed1 excluded)",
        "source_snapshot_commit": SOURCE_COMMIT,
        "source_snapshot_url": SOURCE_RAW_URL,
        "source_snapshot_sha256": FULL_SOURCE_SHA256,
        "source_extract_sha256": digest,
        "chapters": chapters,
    }

    corpus = {
        "corpus_id": CORPUS_ID,
        "title": "Wisdom of Solomon (LIT2516Wisdom ed2) — Geʽez research transcription",
        "reader_id": READER_ID,
        "unit_count": total_lines,
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": CANON_CANDIDATE,
        "canon_mapping_note": (
            "The EOTC English catalogue groups entry 26 as ‘Metsihafe Tibeb (books of wisdom)’. Beta maṣāḥǝft "
            "identifies this TEI work as Wisdom of Solomon, but that does not prove which work(s) the grouped Church "
            "entry contains. This research text has no canon_id and is excluded from canon-linked coverage."
        ),
        "language_description": (
            "Geʽez (gez), explicitly declared on the enclosing TEI ed2 div. The root xml:lang=en document default is "
            "retained in context; the more local ed2 declaration governs the extracted edition."
        ),
        "script_description": "Ethiopic script (Ethi), observed in the extracted text; script and language are separate metadata.",
        "unit_summary": "463 nonempty TEI line elements across 19 source-labeled chapter divisions; source line labels retained; not a verse count.",
        "rights_classification": "open_license",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE_URL,
        "rights_status": (
            "The pinned TEI file states CC BY-SA 4.0 and separately gives noncommercial terms for edition 1. The reader "
            "extracts only ed2 and follows the file's CC BY-SA 4.0 notice with attribution, change notice, and share-alike. "
            "This does not determine rights for an unidentified print exemplar or unrelated material."
        ),
        "review_status": reader["verification_status"],
        "source_ids": [SOURCE_ID],
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "script_code": "Ethi",
        "edition_statement": reader["edition"],
    }

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry["edition_leads"] = [
        record for record in registry.get("edition_leads", [])
        if record.get("edition_id") != "betamasaheft-wisdom-solomon-eotc-ed2"
    ]
    corpora = registry.setdefault("research_corpora", [])
    corpora = [record for record in corpora if record.get("corpus_id") != CORPUS_ID]
    corpora.append(corpus)
    registry["research_corpora"] = sorted(corpora, key=lambda record: record["corpus_id"])
    canon_registry = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    registry["coverage_statement"] = build_coverage_statement(registry, canon_registry)
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    source = next((item for item in archive.get("sources", []) if item.get("source_id") == SOURCE_ID), None)
    if source is None:
        raise ValueError(f"Archive source record {SOURCE_ID} is missing.")
    source.update({
        "source_name": "Beta maṣāḥǝft — Wisdom of Solomon (LIT2516Wisdom), pinned TEI work record and ed2 source snapshot",
        "url": SOURCE_URL,
        "inspection_and_limitations": (
            "Pinned Beta maṣāḥǝft Works revision " + SOURCE_COMMIT + ". The TEI identifies Wisdom of Solomon (Geʽez title "
            "Ṭǝbaba Salomon); edition ed2 explicitly declares xml:lang=gez and bears the note ‘Text of the EOTC printed Bible’. "
            "The edition statement says it was digitized from modern Vulgata printed editions; the physical exemplar and date "
            "are not identified. The file states CC BY-SA 4.0 and gives separate noncommercial terms for ed1; only ed2 is "
            "extracted. The pinned full upstream file hash is " + FULL_SOURCE_SHA256 + "; the deployed ed2-only extract hash is " + digest + ". "
            "The full TEI is retained outside the site because it contains ed1 text with separate noncommercial/no-sale terms. "
            "Structural audit: 19 chapter divisions and 463 "
            "nonempty numbered TEI line elements. This does not verify text accuracy, completeness, exact print edition, or "
            "the crosswalk to grouped EOTC entry 26."
        ),
        "archive_status": "Pinned full-source revision and hash recorded; only the rights-scoped ed2 TEI extract and research reader are bundled in the site; full TEI with ed1 is retained outside the deployment tree",
    })

    catalogue_rows = [row for row in archive.get("catalogue", []) if row.get("catalogue_id") == "eotc-031"]
    if len(catalogue_rows) != 1:
        raise ValueError("Expected exactly one grouped EOTC catalogue row eotc-031.")
    row = catalogue_rows[0]
    row.update({
        "edition_or_translation": "No exact catalogue match established. Related research text: Beta maṣāḥǝft Wisdom of Solomon ed2 (Geʽez); exact relationship to this grouped entry is unresolved.",
        "chapter_count": "19 chapter divisions in the related TEI source; not established for this catalogue entry",
        "chapter_order_status": "The pinned TEI ed2 has sequential source chapter labels 1–19; this structure is not evidence for the grouped Church-list entry's boundaries.",
        "text_availability_status": "No canon-linked reader is established. A separate 19-chapter Geʽez TEI ed2 research reader is bundled and can be opened from this entry; its title-level relationship remains uncertain.",
        "completeness_status": "The retained ed2 contains 463 nonempty numbered TEI line elements. The count describes the snapshot only; completeness against the printed edition is unknown.",
        "rights_status": "The related pinned TEI file states CC BY-SA 4.0 and separately gives noncommercial terms for ed1; only ed2 is included in the research reader. This does not establish rights or identity for the grouped catalogue entry or an unidentified print exemplar.",
        "verification_date": "2026-10-25",
        "reviewer_notes": (
            "Related research reader only. The pinned LIT2516Wisdom TEI identifies Wisdom of Solomon, explicitly declares "
            "gez on ed2, and labels it ‘Text of the EOTC printed Bible’; these are source statements, not independent "
            "verification of exact print edition or equivalence to the grouped ‘Metsihafe Tibeb (books of wisdom)’ entry. "
            "Root xml:lang=en remains recorded; the ed2 declaration governs the extracted text. A machine-audited 19/463 "
            "chapter/line structure does not establish transcription accuracy or completeness. It is not counted as a "
            "canon-linked reader."
        ),
        "evidence_source_ids": list(dict.fromkeys(row.get("evidence_source_ids", []) + [SOURCE_ID])),
    })
    ARCHIVE.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {READER_ID}: 19 ordered chapters, {total_lines} labeled TEI lines; pinned {SOURCE_COMMIT}; canon link unresolved.")
    return reader


if __name__ == "__main__":
    build()
