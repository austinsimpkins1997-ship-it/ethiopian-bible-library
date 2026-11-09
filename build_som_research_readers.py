"""Build research-only Somali readers from the licensed eBible.org USFM package.

This publisher expressly permits format conversion only when scripture words
and punctuation are unchanged. The original USFM archive is retained verbatim.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from archive_manifest import write_text_atomically
import build_brenton_octateuch as usfm
from build_maale_research_readers import BOOK_NAMES, parse_book

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers/source/som/som_usfm.zip"
MANIFEST = ROOT / "research/som-usfm-source-manifest.json"
FIDELITY_AUDIT = ROOT / "research/som-verse-fidelity-audit.json"
NOTICE = ROOT / "readers/source/som/SOURCE-NOTICE.txt"
DETAIL_URL = "https://ebible.org/find/details.php?id=som"
COPYRIGHT_URL = "https://ebible.org/som/copyright.htm"
PACKAGE_URL = "https://ebible.org/Scriptures/som_usfm.zip"
KEY_URL = "https://mljohnson.org/gpg.htm"
LICENSE_30_URL = "https://creativecommons.org/licenses/by-nc-nd/3.0/"
LICENSE_40_URL = "https://creativecommons.org/licenses/by-nc-nd/4.0/"
SOURCE_IDS = ["SRC-390", "SRC-391", "SRC-392"]
RETRIEVED = "2026-10-26"
LICENSE_ID = "CC-BY-NC-ND-3.0-and-4.0 (both notices appear in source)"
COPYRIGHT = (
    "Copyright © 1979, 2008 Society for International Ministries -- Kenya. Translation by SIM International. "
    "Source edition: The Holy Bible in the Somali language of Somalia, Adan Jim'ale Version (eBible.org code SOMSIM / som). "
    "The provider's archived notice states CC BY-NC-ND 3.0 and also links CC BY-NC-ND 4.0; the version discrepancy is retained. "
    "The notice permits file-format porting only if the Bible's wording and punctuation are unchanged, and prohibits commercial use and text adaptations. "
    "This archive converted USFM structure to reader JSON without intentionally changing scripture words or punctuation and retains the original USFM ZIP verbatim. "
    "This is a format port under the provider's stated terms, not a translation or editorial adaptation; no textual proofread is claimed."
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_verse_text(raw: bytes, parsed: dict, member_name: str) -> dict:
    """Compare every source \v line with the rendered reader verse, excluding USFM controls."""
    source_lines = []
    for line_number, line in enumerate(raw.decode("utf-8-sig").splitlines(), start=1):
        match = re.match(r"^\\v\s+(\d+[a-z]?(?:-\d+[a-z]?)?)\s*(.*)$", line)
        if not match:
            continue
        label, body = match.groups()
        # Notes and figures are separately captured by parse_book; compare only
        # the verse body. clean_usfm removes formatting markers and whitespace,
        # while retaining letters, digits, and punctuation verbatim.
        body = re.sub(r"\\[fx]\b.*?\\[fx]\*", " ", body)
        body = re.sub(r"\\fig\s+.*?\\fig\*", " ", body)
        source_lines.append((label, usfm.clean_usfm(body), line_number))
    reader_lines = [
        (verse["number"], verse["text"])
        for chapter in parsed["chapters"]
        for verse in chapter["verses"]
    ]
    source_pairs = [(label, text) for label, text, _ in source_lines]
    if source_pairs != reader_lines:
        differences = []
        for index in range(max(len(source_pairs), len(reader_lines))):
            source_item = source_pairs[index] if index < len(source_pairs) else None
            reader_item = reader_lines[index] if index < len(reader_lines) else None
            if source_item != reader_item:
                differences.append({
                    "index": index,
                    "source_line": source_lines[index][2] if index < len(source_lines) else None,
                    "source": source_item,
                    "reader": reader_item,
                })
                if len(differences) == 5:
                    break
        raise ValueError(f"Verse text/punctuation fidelity mismatch in {member_name}: {differences!r}")
    payload = json.dumps(source_pairs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "source_verse_lines": len(source_pairs),
        "matched_reader_verses": len(reader_lines),
        "mismatches": 0,
        "normalized_verse_body_sha256": sha(payload),
        "comparison": "Ordered source verse labels and text compared exactly after removing USFM formatting controls, note/figure markup, and normalizing whitespace. Wording and punctuation otherwise remain unchanged.",
    }


def verify_signature(z: zipfile.ZipFile) -> dict:
    gpg = shutil.which("gpg")
    bash = None
    if not gpg and os.name == "nt":
        for root in (os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            candidate = Path(root) / "Git/bin/bash.exe" if root else None
            if candidate and candidate.is_file():
                bash = str(candidate)
                break
    if not gpg and not bash:
        raise RuntimeError("GnuPG is required to verify the Somali source checksum signature.")
    with tempfile.TemporaryDirectory(prefix=".som-gpg-", dir=ROOT) as temp:
        home = Path(temp) / "gnupg"
        home.mkdir()
        (home / "keys.asc").write_bytes(z.read("keys.asc"))
        (home / "signature.txt.asc").write_bytes(z.read("signature.txt.asc"))
        env = os.environ.copy()
        if bash:
            env["GNUPGHOME"] = home.relative_to(ROOT).as_posix()
            commands = [
                'gpg --batch --no-autostart --import "$GNUPGHOME/keys.asc"',
                'gpg --batch --no-autostart --status-fd 1 --verify "$GNUPGHOME/signature.txt.asc"',
            ]
            results = [subprocess.run([bash, "-c", command], cwd=ROOT, env=env, capture_output=True, text=True) for command in commands]
        else:
            env["GNUPGHOME"] = str(home)
            subprocess.run([gpg, "--batch", "--import", str(home / "keys.asc")], cwd=ROOT, env=env, capture_output=True)
            results = [subprocess.run([gpg, "--batch", "--status-fd", "1", "--verify", str(home / "signature.txt.asc")], cwd=ROOT, env=env, capture_output=True, text=True)]
        result = results[-1]
        if result.returncode:
            raise ValueError(f"OpenPGP signature verification failed: {result.stderr.strip()}")
        valid = next((line.split() for line in result.stdout.splitlines() if line.startswith("[GNUPG:] VALIDSIG ")), None)
        if not valid or valid[2].upper() != "54D714D76956DA6673DC1EEA5F62009D93505F26":
            raise ValueError("The verified signer does not match the fingerprint in the maintainer's published key listing.")
    return {
        "valid": True,
        "signer_fingerprint": valid[2],
        "fingerprint_reference": KEY_URL,
        "signing_key_algorithm": "DSA-1024 (legacy)",
        "signature_hash_algorithm": "SHA-1 (legacy)",
        "identity_limit": "The signature verifies using the included key, and its fingerprint matches the key maintainer's published listing. This does not independently establish identity, custody, or signing authority; legacy DSA-1024/SHA-1 limits apply.",
    }


def build() -> tuple[list[dict], list[dict], list[dict], dict]:
    package = SOURCE.read_bytes()
    with zipfile.ZipFile(SOURCE) as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f"Source ZIP CRC failed at {bad}.")
        signature = verify_signature(z)
        signed_text = z.read("signature.txt.asc").decode("utf-8")
        declared = {m.group(2): m.group(1) for m in re.finditer(r"^([0-9a-f]{64})\s+(\S+)$", signed_text, re.M)}
        members = {name: z.read(name) for name in z.namelist() if name.lower().endswith(".usfm")}
    if len(members) != 66 or set(members) != {name for name in declared if name.lower().endswith(".usfm")}:
        raise ValueError("Source package is not the 66-member signed USFM set.")
    hashes = {name: sha(data) for name, data in members.items()}
    if any(declared.get(name) != digest for name, digest in hashes.items()):
        raise ValueError("A Somali USFM member does not match the signed SHA-256 list.")

    by_code: dict[str, str] = {}
    for name, raw in members.items():
        match = re.search(r"^\\id\s+([A-Z0-9]{3})\s*$", raw.decode("utf-8-sig"), re.M)
        if not match or match.group(1) not in BOOK_NAMES or match.group(1) in by_code:
            raise ValueError(f"Unknown or duplicate source book ID in {name}.")
        by_code[match.group(1)] = name
    if set(by_code) != set(BOOK_NAMES):
        raise ValueError("Somali USFM book IDs differ from the 66-member conventional inventory.")

    readers, corpora, inventory, fidelity_records = [], [], [], []
    inline_unrecognized = set()
    for code in BOOK_NAMES:
        name, raw = by_code[code], members[by_code[code]]
        parsed = parse_book(raw, name)
        fidelity = audit_verse_text(raw, parsed, name)
        fidelity_records.append({"usfm_id": code, "path": name, **fidelity})
        reader_id = f"som-1979-2008-{code.lower()}-research"
        corpus_id = f"somsim-1979-2008-{code.lower()}"
        title = f"{BOOK_NAMES[code]} — Kitaabka Quduuska Ah (Somali, SIM 2008)"
        reader = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "canon_id": None,
            "title": title,
            "display_name": f"{BOOK_NAMES[code]} · Somali · SIM 2008",
            "text_origin": "published_translation",
            "translation_id": "somsim-1979-2008",
            "language": "Somali, language of Somalia (edition description)",
            "language_tag": "so",
            "language_assignment_status": "eBible.org identifies Somali (language code som); the archive maps it to BCP 47 so. No dialect or community review is asserted.",
            "script_code": "Latn",
            "translator": "SIM International",
            "contributor": "Society for International Ministries -- Kenya",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The inspected edition page does not state its source language or any relay path.",
            "edition": "Kitaabka Quduuska Ah; The Holy Bible in the Somali language of Somalia, Adan Jim'ale Version; copyright © 1979, 2008; publisher code SOMSIM / som.",
            "edition_scope": "One of 66 conventional USFM modules in the retained publisher package. The English book name is a navigation aid. No Ethiopian or Eritrean Orthodox canon crosswalk is assigned.",
            "rights_classification": "permission_limited",
            "license_id": LICENSE_ID,
            "license_url": LICENSE_40_URL,
            "copyright_notice": COPYRIGHT,
            "commercial_use": "The provider's terms prohibit selling the work for profit. The 3.0/4.0 version discrepancy is retained; do not infer permissions beyond the source's express format-porting allowance.",
            "unit_label": "Publisher USFM chapter/verse labels observed",
            "unit_count": parsed["unit_count"],
            "verse_marker_count": parsed["unit_count"],
            "chapter_count": parsed["chapter_count"],
            "section_label": "Chapter",
            "chapter_structure_note": f"The parser found {parsed['chapter_count']} consecutive chapter divisions and {parsed['unit_count']} distinct chapter/verse labels. Publisher labels, native book headings, front matter, section headings, paragraph structure, and footnotes are retained; these counts do not prove completeness against print or wording accuracy.",
            "chapter_structure_status": "source_package_parsed_with_limits",
            "source_numbered_unit_count": parsed["unit_count"],
            "source_unnumbered_unit_count": sum(len(v.get("continuations", [])) for c in parsed["chapters"] for v in c["verses"]),
            "source_pages": f"readers/source/som/som_usfm.zip::{name}",
            "source_package_sha256": sha(package),
            "source_snapshot_sha256": hashes[name],
            "source_ids": SOURCE_IDS,
            "rights_status": COPYRIGHT,
            "verification_status": f"The 70-entry ZIP passed CRC. GnuPG verified the clear-signed SHA-256 list; the signer fingerprint {signature['signer_fingerprint']} matches the key maintainer's public fingerprint list, subject to identity/custody and legacy DSA-1024/SHA-1 limitations. All 66 USFM member hashes match. Chapter sequences and duplicate chapter/verse labels were checked. An automated exact comparison matched all {fidelity['source_verse_lines']} labeled source verse lines to this reader's verse text after stripping USFM formatting and separating note/figure markup; whitespace was normalized. This is not human proofreading, a print collation, a completeness review, or translation validation.",
            "transcription_note": "Format conversion from the retained publisher USFM to reader JSON. The source notice expressly allows file-format porting if scripture words and punctuation do not change. The original USFM is preserved verbatim; the rendered layer removes USFM controls and normalizes whitespace only. No text adaptation or translation is made.",
            "editorial_signs_note": "Native book headings and title markers, verse labels, section headings, paragraphs, poetry markers, notes, and available front matter are represented in structured form. Source USFM remains available to inspect the original markup. Images are not included because their terms differ.",
            "front_matter": parsed["front_matter"],
            "source_book_metadata": parsed["book_metadata"],
            "chapters": parsed["chapters"],
        }
        readers.append(reader)
        write_text_atomically(ROOT / "readers" / f"{reader_id}.json", json.dumps(reader, ensure_ascii=False, indent=2) + "\n", newline="\n")
        corpora.append({
            "corpus_id": corpus_id,
            "title": title,
            "reader_id": reader_id,
            "unit_count": parsed["unit_count"],
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped",
            "candidate_canon_id": None,
            "canon_mapping_note": "This publisher package supplies 66 conventional modules; that does not establish equivalence to any Ethiopian or Eritrean Orthodox canon. No crosswalk is assigned.",
            "language_description": "Publisher identifies Somali (ISO 639-3 som); the archive profile uses Somali (so).",
            "script_description": "Latin script observed in this source package; not a claim about all Somali witnesses.",
            "unit_summary": f"{parsed['chapter_count']} consecutive source chapter divisions and {parsed['unit_count']} source chapter/verse labels in this member; counts do not prove printed completeness.",
            "rights_classification": "permission_limited",
            "rights_status": COPYRIGHT,
            "review_status": f"Source ZIP signature, all member hashes, CRC, book IDs, chapter sequence, and label uniqueness were checked. All {fidelity['source_verse_lines']} labeled source verse lines matched exactly after removing USFM formatting and separating note/figure markup; whitespace was normalized. The source permits exact-text format porting only. This automated check is not human proofreading, print collation, completeness, canon, or translation-accuracy review.",
            "license_id": LICENSE_ID,
            "license_url": LICENSE_40_URL,
            "source_ids": SOURCE_IDS,
            "text_origin": "published_translation",
            "language_tag": "so",
            "script_code": "Latn",
            "translation_id": "somsim-1979-2008",
            "translator": "SIM International",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The inspected edition page does not state a source language or relay path.",
            "edition_statement": reader["edition"],
        })
        inventory.append({
            "usfm_id": code,
            "path": name,
            "navigation_label": BOOK_NAMES[code],
            "native_book_metadata": parsed["book_metadata"],
            "member_sha256": hashes[name],
            "member_bytes": len(raw),
            "chapter_count": parsed["chapter_count"],
            "unit_count": parsed["unit_count"],
            "front_matter_item_count": len(parsed["front_matter"]),
            "marker_counts": parsed["marker_counts"],
        })

    fidelity_audit = {
        "source_id": SOURCE_IDS[1],
        "source_url": PACKAGE_URL,
        "retrieved_at": RETRIEVED,
        "source_archive_sha256": sha(package),
        "method": "For each of 66 retained USFM members, compare ordered source \\v labels and verse text against the corresponding reader JSON. Remove USFM format controls and separately delimited footnote/cross-reference/figure markup; normalize whitespace only. Keep punctuation, spelling, and word sequence exact.",
        "scope_limitations": "This audit covers text on labeled source verse lines only. Notes, headings, front matter, paragraph continuations, chapter boundaries, printed completeness, translation accuracy, and human review are not established by this comparison. The original USFM is retained for inspection.",
        "book_count": len(fidelity_records),
        "source_verse_line_count": sum(item["source_verse_lines"] for item in fidelity_records),
        "matched_reader_verse_count": sum(item["matched_reader_verses"] for item in fidelity_records),
        "mismatch_count": sum(item["mismatches"] for item in fidelity_records),
        "books": fidelity_records,
    }
    write_text_atomically(FIDELITY_AUDIT, json.dumps(fidelity_audit, ensure_ascii=False, indent=2) + "\n", newline="\n")

    manifest = {
        "source_id": SOURCE_IDS[1],
        "source_url": PACKAGE_URL,
        "retrieved_at": RETRIEVED,
        "archive_sha256": sha(package),
        "archive_byte_length": len(package),
        "signature": signature,
        "zip_member_count": 70,
        "usfm_book_count": 66,
        "verse_text_fidelity_audit": "research/som-verse-fidelity-audit.json",
        "source_verse_line_count": fidelity_audit["source_verse_line_count"],
        "matched_reader_verse_count": fidelity_audit["matched_reader_verse_count"],
        "verse_text_mismatches": fidelity_audit["mismatch_count"],
        "usfm_members": inventory,
        "verification": "CRC passed; GnuPG signature on the clear-signed checksum list verified with its included key. Its fingerprint matches the maintainer's published listing. Every USFM member hash matches the signed list.",
        "limits": "The source license notice contains both CC BY-NC-ND 3.0 and 4.0 references; the discrepancy is preserved. Exact wording/punctuation format-port permission is observed, but any adaptation is prohibited. Legacy signature algorithms and signer identity limitations apply. This conventional 66-module set is not an Ethiopian/Eritrean Orthodox canon crosswalk, printed-edition completeness audit, or translation review.",
    }
    write_text_atomically(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", newline="\n")
    capture_path = SOURCE.parent / "capture-manifest.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    capture["verified_manifest_path"] = "research/som-usfm-source-manifest.json"
    capture["signature_verification"] = signature
    capture["content_scope"] = "CRC, signed member hashes, IDs, consecutive chapters, unique labels, and native book metadata were checked. These checks do not prove text completeness or accuracy. The source notice permits porting formats only if wording and punctuation remain unchanged; two CC license version references in the notice are disclosed."
    write_text_atomically(capture_path, json.dumps(capture, ensure_ascii=False, indent=2) + "\n", newline="\n")
    notice = (
        "Kitaabka Quduuska Ah — Somali Bible (SOMSIM / som) source notice\n\n"
        "Copyright © 1979, 2008 Society for International Ministries -- Kenya. Translation by SIM International.\n"
        f"Edition record: {DETAIL_URL}\nCopyright notice: {COPYRIGHT_URL}\nOriginal USFM: {PACKAGE_URL}\n"
        "The source ZIP identifies source files dated 29 January 2022.\n\n"
        "License notice discrepancy: the archived copyright page first names CC BY-NC-ND 3.0 and explicitly allows conversion to different file formats only when Bible wording and punctuation are unchanged. It later links CC BY-NC-ND 4.0 and repeats the no-sale/no-text-change conditions. This archive preserves both notices without deciding their legal relationship. The common requirements are attribution, noncommercial sharing, no text adaptation, and no changes to scripture words or punctuation.\n\n"
        "This archive converted USFM structure to reader JSON under the provider's express file-format porting permission. No wording or punctuation change was intended; original source files are included verbatim. USFM controls and whitespace presentation are normalized into structured fields. This is not a translation, textual revision, or endorsement. Rights for included pictures are separate; image assets are excluded.\n\n"
        f"The ZIP CRC passed and all 66 USFM hashes match its cryptographically verified checksum list. The signer fingerprint {signature['signer_fingerprint']} matches the maintainer's published page, but identity/custody are not independently certified. Signature algorithms are legacy DSA-1024/SHA-1. No independent text collation, completeness audit, or translation proofread is claimed. These readers are unmapped research witnesses.\n"
    )
    write_text_atomically(NOTICE, notice, newline="\n")
    sources = [
        {
            "source_id": SOURCE_IDS[0],
            "source_name": "eBible.org — Somali Bible (SOMSIM / som) edition and rights notice",
            "url": DETAIL_URL,
            "local_metadata_url": "readers/source/som/details.html",
            "inspection_and_limitations": "Inspected 2026-10-26. eBible.org identifies the edition as the Somali Bible / Kitaabka Quduuska Ah, Adan Jim'ale Version, Somali code som, copyright © 1979, 2008 Society for International Ministries—Kenya, and translator SIM International. Its copyright text contains both CC BY-NC-ND 3.0 and 4.0 references; it explicitly permits format conversion if scripture wording and punctuation are not changed, and prohibits commercial sale and textual changes. The version discrepancy is retained, not adjudicated. The title/publisher/year resemble Bible.com SOM08, but edition identity between those records is not established.",
            "archive_status": "Edition and restricted reuse terms inspected; exact-text format conversion only; no canon or accuracy claim.",
            "rights_classification": "unknown",
            "rights_status": "This record is the provider's edition and copyright-information webpage. The retained text notice contains both CC BY-NC-ND 3.0 and 4.0 references and expressly allows file-format conversion only when scripture wording and punctuation remain unchanged; it prohibits sale for profit and textual changes. This establishes the provider-stated text conditions, not reuse rights in the webpage itself. The license-version discrepancy is preserved without legal interpretation.",
            "rights_basis": "The captured copyright notice supports a permission-limited text-use statement but names no separate reuse terms for reproducing the information webpage. Unknown is scoped to the webpage resource; the text conditions are recorded on the separate reader and package records.",
        },
        {
            "source_id": SOURCE_IDS[1],
            "source_name": "eBible.org — Somali Bible publisher USFM package",
            "url": PACKAGE_URL,
            "local_metadata_url": "research/som-usfm-source-manifest.json",
            "local_fidelity_audit_url": "research/som-verse-fidelity-audit.json",
            "local_source_package_url": "readers/source/som/som_usfm.zip",
            "inspection_and_limitations": f"Retrieved 2026-10-26 and retained at readers/source/som/som_usfm.zip (SHA-256 {sha(package)}; {len(package)} bytes). ZIP contains 70 members, including 66 USFM book files. CRC passed; GnuPG verified the included clear-signed checksum list and all 66 member hashes match. Signer fingerprint {signature['signer_fingerprint']} matches the key maintainer's listing. The signature uses legacy DSA-1024/SHA-1. Parser checks do not prove printed-edition completeness or text accuracy.",
            "archive_status": "Original publisher USFM retained; signature and checksums verified with documented limits.",
            "rights_classification": "mixed",
            "rights_status": "The 66 USFM scripture-text members carry the provider's conflicting CC BY-NC-ND 3.0 and 4.0 references. Both notices prohibit sale for profit and changes to scripture wording or punctuation; the provider expressly allows file-format conversion only when those remain unchanged. The license-version conflict is not adjudicated. The ZIP also contains a copyright HTML page, stylesheet, public key, and signature files whose reuse terms are not established here. This mixed classification applies to the aggregate package; the separate Somali reader is classified permission-limited under the stated text conditions.",
            "rights_basis": "The retained copyright notice establishes the text's express no-sale/no-text-change conditions and format-porting permission, while naming two license versions. ZIP inventory also contains ancillary .htm, .css, and .asc members with no separately established reuse basis. The aggregate package classification preserves both the text-license conflict and the ancillary-file gap.",
        },
        {
            "source_id": SOURCE_IDS[2],
            "source_name": "Michael Paul Johnson — published OpenPGP key fingerprint listing",
            "url": KEY_URL,
            "inspection_and_limitations": f"Inspected 2026-10-26. The listing gives fingerprint {signature['signer_fingerprint']} for the World English Bible editors key, matching the signer reported by GnuPG for the Somali package. This is a match to the key maintainer's listing, not independent proof of identity, custody, or authority.",
            "archive_status": "Fingerprint cross-reference only; identity limits and legacy algorithms disclosed.",
        },
    ]
    return readers, corpora, sources, manifest

