"""Build research-only Lingala readers from the eBible.org USFM package."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import build_brenton_octateuch as usfm
from archive_manifest import write_text_atomically
from build_maale_research_readers import BOOK_NAMES, parse_book
from build_som_research_readers import verify_signature

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers/source/lin/lin_usfm.zip"
DETAIL_URL = "https://ebible.org/find/details.php?id=lin"
COPYRIGHT_URL = "https://ebible.org/lin/copyright.htm"
PACKAGE_URL = "https://ebible.org/Scriptures/lin_usfm.zip"
KEY_URL = "https://mljohnson.org/gpg.htm"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
SOURCE_IDS = ["SRC-393", "SRC-394", "SRC-395"]
RETRIEVED = "2026-10-26"
LICENSE_ID = "CC-BY-SA-4.0"
COPYRIGHT = (
    "Copyright © 2002, 2020 Biblica, Inc. Original work: Salela na bonsomi Mokanda na Bomoi / Open Lingala Contemporary Bible, "
    "eBible.org code LINBIB / lin. The inspected source identifies Biblica, Inc. as publisher and contributor; it does not name an individual translator. "
    "This reader is a derivative format conversion from USFM to JSON; source-format controls are structured or omitted, whitespace is normalized, "
    "and image assets are excluded. The derivative omits the registered Biblica mark, identifies the changes, attributes the original to Biblica, Inc., "
    "links https://www.biblica.com and https://open.bible, and is distributed under CC BY-SA 4.0. No endorsement is implied."
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_verse_and_table_text(raw: bytes, parsed: dict, member_name: str) -> dict:
    source_verses = []
    source_tables: list[list[list[dict]]] = []
    in_table = False
    for line_number, line in enumerate(raw.decode("utf-8-sig").splitlines(), start=1):
        table_row = re.match(r"^\\tr[ \t]*(.*)$", line)
        table_cell = re.match(r"^\\(tc|tcr|th|thr)(\d+)[ \t]*(.*)$", line)
        if table_row:
            if not in_table:
                source_tables.append([])
            source_tables[-1].append([])
            in_table = True
            if table_row.group(1).strip():
                source_tables[-1][-1].append({"marker": "tr", "text": usfm.clean_usfm(table_row.group(1))})
            continue
        if table_cell and in_table:
            marker = table_cell.group(1) + table_cell.group(2)
            source_tables[-1][-1].append({"marker": marker, "text": usfm.clean_usfm(table_cell.group(3))})
            continue
        verse = re.match(r"^\\v[ \t]+(\d+[a-z]?(?:-\d+[a-z]?)?)[ \t]*(.*)$", line)
        if verse:
            label, body = verse.groups()
            body = re.sub(r"\\[fx]\b.*?\\[fx]\*", " ", body)
            body = re.sub(r"\\fig\s+.*?\\fig\*", " ", body)
            text = usfm.clean_usfm(body)
            if in_table:
                source_tables[-1][-1].append({"marker": "v", "number": label, "text": text})
            source_verses.append((label, text, line_number))
            continue
        if line.strip() and not line.startswith("\\"):
            in_table = False
        elif line.startswith("\\") and not re.match(r"^\\(?:tc|tcr|th|thr)\d+", line):
            in_table = False

    reader_verses = [
        (verse["number"], verse["text"])
        for chapter in parsed["chapters"]
        for verse in chapter["verses"]
    ]
    source_pairs = [(label, text) for label, text, _ in source_verses]
    if source_pairs != reader_verses:
        differences = []
        for index in range(max(len(source_pairs), len(reader_verses))):
            left = source_pairs[index] if index < len(source_pairs) else None
            right = reader_verses[index] if index < len(reader_verses) else None
            if left != right:
                differences.append({"index": index, "source": left, "reader": right,
                                    "source_line": source_verses[index][2] if index < len(source_verses) else None})
                if len(differences) == 5:
                    break
        raise ValueError(f"Lingala verse fidelity mismatch in {member_name}: {differences!r}")

    reader_tables = []
    for chapter in parsed["chapters"]:
        for table in chapter.get("source_tables", []):
            reader_tables.append(table["rows"])
    if source_tables != reader_tables:
        raise ValueError(f"Lingala source table fidelity mismatch in {member_name}.")
    serialized = json.dumps(source_pairs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "source_verse_lines": len(source_pairs),
        "matched_reader_verses": len(reader_verses),
        "verse_mismatches": 0,
        "source_table_count": len(source_tables),
        "source_table_rows": sum(len(table) for table in source_tables),
        "matched_reader_table_count": len(reader_tables),
        "matched_reader_table_rows": sum(len(table) for table in reader_tables),
        "table_row_mismatches": 0,
        "normalized_verse_body_sha256": sha(serialized),
    }


def build() -> tuple[list[dict], list[dict], list[dict], dict]:
    package = SOURCE.read_bytes()
    with zipfile.ZipFile(SOURCE) as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f"Lingala source ZIP CRC failed at {bad}.")
        signature = verify_signature(z)
        signed_text = z.read("signature.txt.asc").decode("utf-8")
        declared = {m.group(2): m.group(1) for m in re.finditer(r"^([0-9a-f]{64})\s+(\S+)$", signed_text, re.M)}
        members = {name: z.read(name) for name in z.namelist() if name.lower().endswith(".usfm")}
    if len(members) != 66 or set(members) != {name for name in declared if name.lower().endswith(".usfm")}:
        raise ValueError("Lingala package does not contain the 66 signed USFM members.")
    hashes = {name: sha(data) for name, data in members.items()}
    if any(declared.get(name) != digest for name, digest in hashes.items()):
        raise ValueError("A Lingala USFM member does not match the signed SHA-256 list.")

    by_code = {}
    for name, raw in members.items():
        match = re.search(r"^\\id[ \t]+([A-Z0-9]{3})\b", raw.decode("utf-8-sig"), re.M)
        if not match or match.group(1) not in BOOK_NAMES or match.group(1) in by_code:
            raise ValueError(f"Unknown or duplicate Lingala book ID in {name}.")
        by_code[match.group(1)] = name
    if set(by_code) != set(BOOK_NAMES):
        raise ValueError("Lingala USFM IDs differ from the expected 66 conventional book modules.")

    readers, corpora, inventory, fidelity_records = [], [], [], []
    for code in BOOK_NAMES:
        name, raw = by_code[code], members[by_code[code]]
        parsed = parse_book(raw, name)
        fidelity = audit_verse_and_table_text(raw, parsed, name)
        fidelity_records.append({"usfm_id": code, "path": name, **fidelity})
        reader_id = f"lin-2020-{code.lower()}-research"
        corpus_id = f"linbibo-2020-{code.lower()}"
        title = f"{BOOK_NAMES[code]} — Open Lingala Contemporary Bible"
        reader = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "canon_id": None,
            "title": title,
            "display_name": f"{BOOK_NAMES[code]} · Lingala · 2020",
            "text_origin": "published_translation",
            "translation_id": "linbibo-2020",
            "language": "Lingála (publisher edition label)",
            "language_tag": "ln",
            "language_assignment_status": "The publisher identifies the language as Lingala and uses source code lin; the archive maps that witness to BCP 47 ln. IANA confirms ln as Lingala. Community review of this edition's language variety is not asserted.",
            "script_code": "Latn",
            "translator": "No individual translator named in the inspected edition record; Biblica, Inc. is identified as publisher and contributor.",
            "contributor": "Biblica, Inc.",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The inspected edition record does not state its source language or relay path.",
            "edition": "Salela na bonsomi Mokanda na Bomoi / Open Lingala Contemporary Bible; publisher code LINBIB / lin; copyright © 2002, 2020 Biblica, Inc.",
            "edition_scope": "One of 66 conventional USFM modules in the retained publisher package. The English book name is a navigation aid. No Ethiopian or Eritrean Orthodox canon crosswalk is assigned.",
            "rights_classification": "open_license",
            "license_id": LICENSE_ID,
            "license_url": LICENSE_URL,
            "copyright_notice": COPYRIGHT,
            "commercial_use": "CC BY-SA 4.0 permits redistribution, including commercially, and adaptation with attribution, change indication, and ShareAlike. The derivative removes the registered mark, includes Biblica attribution and source links, and is distributed under the same license. Image assets are excluded; no endorsement is implied.",
            "unit_label": "Publisher USFM chapter/verse labels observed",
            "unit_count": parsed["unit_count"],
            "verse_marker_count": parsed["unit_count"],
            "chapter_count": parsed["chapter_count"],
            "section_label": "Chapter",
            "chapter_structure_note": f"The parser found {parsed['chapter_count']} consecutive chapter divisions and {parsed['unit_count']} distinct source chapter/verse labels. Publisher book headings, source table rows/cells, section headings, paragraph structure, and notes are retained as structured fields; this does not prove print completeness.",
            "chapter_structure_status": "source_package_parsed_with_limits",
            "source_numbered_unit_count": parsed["unit_count"],
            "source_unnumbered_unit_count": sum(len(v.get("continuations", [])) for c in parsed["chapters"] for v in c["verses"]),
            "source_pages": f"readers/source/lin/lin_usfm.zip::{name}",
            "source_package_sha256": sha(package),
            "source_snapshot_sha256": hashes[name],
            "source_ids": SOURCE_IDS + ["SRC-077", "SRC-078"],
            "rights_status": COPYRIGHT,
            "verification_status": f"The 70-member ZIP passed CRC; GnuPG verified its clear-signed SHA-256 list and all 66 USFM member hashes. The signer fingerprint {signature['signer_fingerprint']} matches the key maintainer's published listing, subject to identity/custody and legacy DSA-1024/SHA-1 limitations. All {fidelity['source_verse_lines']} source verse lines and {fidelity['source_table_rows']} source table rows match their structured reader text exactly after stripping USFM controls and normalizing whitespace. This is an automated format-conversion comparison, not human proofreading, completeness review, or translation validation.",
            "transcription_note": "This is a format conversion of the publisher's USFM into reader JSON, not a new translation. USFM markers are structured or removed, whitespace is normalized, and punctuation/word sequence in checked verse lines and table cells is retained. Changes are identified for CC BY-SA 4.0. The registered trademark mark is removed from this derivative as required by the source notice. Original USFM is retained verbatim.",
            "editorial_signs_note": "Book identity and headings, source table cells, verse labels, section headings, paragraph/poetry/list structure, front matter, and notes are represented in structured fields. The reader exposes source tables in a responsive, horizontally scrollable semantic table. Original USFM remains available for markup inspection; images are excluded under their separate terms.",
            "front_matter": parsed["front_matter"],
            "source_book_metadata": parsed["book_metadata"],
            "chapters": parsed["chapters"],
        }
        readers.append(reader)
        write_text_atomically(ROOT / "readers" / f"{reader_id}.json", json.dumps(reader, ensure_ascii=False, indent=2) + "\n", newline="\n")
        corpora.append({
            "corpus_id": corpus_id, "title": title, "reader_id": reader_id,
            "unit_count": parsed["unit_count"], "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped", "candidate_canon_id": None,
            "canon_mapping_note": "The publisher package supplies 66 conventional modules, not an Ethiopian or Eritrean Orthodox canon crosswalk. No such mapping is asserted.",
            "language_description": "Publisher edition label is Lingala; publisher source code is lin; archive language tag ln is confirmed by IANA.",
            "script_description": "Latin script observed in this digital source witness. IANA records Latn as the language's suppress-script; that registry fact does not prove every community uses one script.",
            "unit_summary": f"{parsed['chapter_count']} consecutive source chapter divisions and {parsed['unit_count']} source verse labels; table and continuation structures retained where observed. Counts do not prove printed completeness.",
            "rights_classification": "open_license", "rights_status": COPYRIGHT,
            "review_status": f"CRC, signed hashes, book IDs, chapter sequence, duplicate labels, all {fidelity['source_verse_lines']} source verse lines, and {fidelity['source_table_rows']} table rows checked. Automated source-to-reader text comparison only; no collation, completeness, canon, community, or translation-accuracy review is claimed.",
            "license_id": LICENSE_ID, "license_url": LICENSE_URL,
            "source_ids": SOURCE_IDS + ["SRC-077", "SRC-078"],
            "text_origin": "published_translation", "language_tag": "ln", "script_code": "Latn",
            "translation_id": "linbibo-2020", "translator": reader["translator"],
            "translation_basis_status": "unknown", "translation_basis_note": reader["translation_basis_note"],
            "edition_statement": reader["edition"],
        })
        inventory.append({
            "usfm_id": code, "path": name, "navigation_label": BOOK_NAMES[code],
            "native_book_metadata": parsed["book_metadata"], "member_sha256": hashes[name],
            "member_bytes": len(raw), "chapter_count": parsed["chapter_count"],
            "unit_count": parsed["unit_count"], "front_matter_item_count": len(parsed["front_matter"]),
            "table_count": sum(len(c.get("source_tables", [])) for c in parsed["chapters"]),
            "table_row_count": fidelity["source_table_rows"], "marker_counts": parsed["marker_counts"],
        })

    audit = {
        "source_id": SOURCE_IDS[1], "source_url": PACKAGE_URL, "retrieved_at": RETRIEVED,
        "source_archive_sha256": sha(package),
        "method": "Compare ordered source verse labels and their text with reader JSON after removing USFM format controls and separately delimited note/figure markup; normalize whitespace only. Compare table cell text and row order after removing cell marker controls.",
        "scope_limitations": "This checks source verse lines and recognized table cells only. It does not establish notes/headings/front-matter/continuation fidelity, print completeness, translation accuracy, community review, or Ethiopian/Eritrean canon equivalence. The original USFM is retained for inspection.",
        "book_count": len(fidelity_records),
        "source_verse_line_count": sum(x["source_verse_lines"] for x in fidelity_records),
        "matched_reader_verse_count": sum(x["matched_reader_verses"] for x in fidelity_records),
        "verse_mismatch_count": sum(x["verse_mismatches"] for x in fidelity_records),
        "source_table_row_count": sum(x["source_table_rows"] for x in fidelity_records),
        "matched_reader_table_row_count": sum(x["matched_reader_table_rows"] for x in fidelity_records),
        "table_row_mismatch_count": sum(x["table_row_mismatches"] for x in fidelity_records),
        "books": fidelity_records,
    }
    audit_path = ROOT / "research/lin-verse-fidelity-audit.json"
    write_text_atomically(audit_path, json.dumps(audit, ensure_ascii=False, indent=2) + "\n", newline="\n")
    manifest = {
        "source_id": SOURCE_IDS[1], "source_url": PACKAGE_URL, "retrieved_at": RETRIEVED,
        "archive_sha256": sha(package), "archive_byte_length": len(package), "signature": signature,
        "zip_member_count": 70, "usfm_book_count": 66, "usfm_members": inventory,
        "verse_text_fidelity_audit": "research/lin-verse-fidelity-audit.json",
        "source_verse_line_count": audit["source_verse_line_count"],
        "matched_reader_verse_count": audit["matched_reader_verse_count"],
        "verse_text_mismatches": audit["verse_mismatch_count"],
        "source_table_row_count": audit["source_table_row_count"],
        "source_table_count": sum(x["source_table_count"] for x in fidelity_records),
        "matched_reader_table_row_count": audit["matched_reader_table_row_count"],
        "table_row_mismatches": audit["table_row_mismatch_count"],
        "verification": "ZIP CRC passed; GnuPG signature verified with the included key, whose fingerprint matches the key maintainer's public listing; all signed USFM hashes match. Verse and table text comparisons pass with documented scope limits.",
        "limits": "The source claims CC BY-SA 4.0 for text, requires attribution, change indication, and ShareAlike, and requires removal of the Biblica registered mark from derivatives. Image assets are excluded. Legacy DSA-1024/SHA-1 and signer identity limits apply. No printed completeness, translation accuracy, community review, or canon crosswalk is asserted.",
    }
    write_text_atomically(ROOT / "research/lin-usfm-source-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", newline="\n")

    capture_path = SOURCE.parent / "capture-manifest.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    capture["verified_manifest_path"] = "research/lin-usfm-source-manifest.json"
    capture["fidelity_audit_path"] = "research/lin-verse-fidelity-audit.json"
    capture["signature_verification"] = signature
    capture["content_scope"] = "66 signed USFM members; CRC, signature, signed hashes, book identities, chapters, verse labels, table rows, and scoped text fidelity were checked. No completeness, translation accuracy, community, or canon-equivalence claim."
    write_text_atomically(capture_path, json.dumps(capture, ensure_ascii=False, indent=2) + "\n", newline="\n")
    notice = (
        "Open Lingala Contemporary Bible (LINBIB / lin) source and license notice\n\n"
        "Copyright © 2002, 2020 Biblica, Inc. The source edition identifies Biblica, Inc. as publisher and contributor; it does not name an individual translator.\n"
        f"Edition record: {DETAIL_URL}\nCopyright notice: {COPYRIGHT_URL}\nOriginal USFM package: {PACKAGE_URL}\n\n"
        "The provider states CC BY-SA 4.0 for the text. Redistribution and adaptations require attribution, indication of changes, and ShareAlike. The source further states that the Biblica registered trademark must remain on unmodified content but must be removed from derivative works; this converted reader removes the mark, identifies format/markup/whitespace changes, attributes the original to Biblica, Inc., links www.biblica.com and open.bible, and is distributed under the same license. The exact source package and copyright page are retained unchanged. Image rights are separate; images and stylesheet are not used in the reader.\n\n"
        f"The ZIP CRC passed; its clear-signed SHA-256 list verified using fingerprint {signature['signer_fingerprint']}, which matches the key maintainer's published listing. Identity/custody and legacy DSA-1024/SHA-1 limits remain. The automated audit matched all {audit['source_verse_line_count']} source verse lines and {audit['source_table_row_count']} table rows in the converted reader, within its stated scope. This is not human proofreading, textual collation, completeness review, translation validation, community review, or endorsement. The readers are not mapped to the Ethiopian or Eritrean Orthodox canon.\n"
    )
    write_text_atomically(SOURCE.parent / "SOURCE-NOTICE.txt", notice, newline="\n")

    sources = [
        {
            "source_id": SOURCE_IDS[0], "source_name": "eBible.org — Open Lingala Contemporary Bible edition and license record",
            "url": DETAIL_URL, "local_metadata_url": "readers/source/lin/details.html",
            "inspection_and_limitations": "Inspected 2026-10-26. eBible.org identifies Lingala, source code LINBIB / lin, title Salela na bonsomi Mokanda na Bomoi / Open Lingala Contemporary Bible, copyright © 2002, 2020 Biblica, Inc., contributor Biblica, Inc., and CC BY-SA 4.0. Its notice requires attribution, change indication, ShareAlike, and removal of the registered mark from derivatives; image rights are separate. It does not name an individual translator or state a translation basis.",
            "archive_status": "Edition and text license inspected; source page and notice retained; no canon or translation-accuracy claim.",
            "rights_classification": "unknown",
            "rights_status": "This record is the provider's edition and license-information webpage. Its retained notice states that the Lingala scripture text is licensed CC BY-SA 4.0, with attribution, change indication, ShareAlike, and removal of the registered mark from derivatives; image rights are separate. This establishes the provider-stated text license, not reuse rights in the webpage itself. Rights for the separately bundled USFM package and converted readers are recorded in their own records.",
            "rights_basis": "The captured edition/copyright notices identify CC BY-SA 4.0 for scripture text but do not establish a license for reproducing the information webpage. The unknown classification is scoped to the webpage resource, not to the separately identified text layer.",
        },
        {
            "source_id": SOURCE_IDS[1], "source_name": "eBible.org — Lingala publisher USFM package",
            "url": PACKAGE_URL, "local_metadata_url": "research/lin-usfm-source-manifest.json",
            "local_fidelity_audit_url": "research/lin-verse-fidelity-audit.json",
            "local_source_package_url": "readers/source/lin/lin_usfm.zip",
            "inspection_and_limitations": f"Retrieved 2026-10-26 and retained unchanged at readers/source/lin/lin_usfm.zip (SHA-256 {sha(package)}; {len(package)} bytes). Its 70-member ZIP contains 66 USFM book files. CRC passed; GnuPG verified the included signed hash list and all member hashes match. All {audit['source_verse_line_count']} source verse lines and {audit['source_table_row_count']} table rows compare exactly to the structured reader under the audit's normalization scope. These structural checks do not prove printed completeness or translation accuracy.",
            "archive_status": "Original publisher USFM retained; signature, hashes, and scoped reader conversion comparison verified with limits.",
            "rights_classification": "mixed",
            "rights_status": "The 66 USFM scripture-text members are identified by the retained provider notice as CC BY-SA 4.0; comply with attribution, change-indication, ShareAlike, and derivative trademark-removal conditions. The ZIP also contains a copyright HTML page, stylesheet, public key, and signature files whose reuse terms are not established here. This mixed classification applies to the aggregate package; it does not withdraw or broaden the stated text license. Images are excluded from the converted readers and have separate terms.",
            "rights_basis": "The retained provider notice and edition record state CC BY-SA 4.0 for text. The ZIP inventory independently shows ancillary .htm, .css, and .asc members alongside the USFM files; no separate permission basis was established for every ancillary member. The text-layer license is recorded separately on each reader.",
        },
        {
            "source_id": SOURCE_IDS[2], "source_name": "Michael Paul Johnson — published OpenPGP key fingerprint listing",
            "url": KEY_URL,
            "inspection_and_limitations": f"Inspected 2026-10-26. The listing gives fingerprint {signature['signer_fingerprint']}, matching the signer GnuPG reports for the Lingala package. This is a fingerprint cross-reference, not independent proof of signer identity, custody, or signing authority; DSA-1024/SHA-1 are legacy algorithms.",
            "archive_status": "Fingerprint cross-reference only; identity and legacy algorithm limits disclosed.",
        },
    ]
    return readers, corpora, sources, manifest
