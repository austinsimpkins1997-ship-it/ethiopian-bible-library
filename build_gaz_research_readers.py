"""Build research-only readers from eBible.org's licensed West Central Oromo USFM.

The original source archive is retained. The 66 conventional Protestant USFM
books are not crosswalked to the EOTC or Eritrean Orthodox canon.
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
from collections import Counter
from pathlib import Path

from archive_manifest import write_text_atomically
from build_maale_research_readers import BOOK_NAMES, parse_book

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers/source/gaz/gaz_usfm.zip"
MANIFEST = ROOT / "research/gaz-usfm-source-manifest.json"
NOTICE = ROOT / "readers/source/gaz/SOURCE-NOTICE.txt"
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
DETAIL_URL = "https://ebible.org/Scriptures/details.php?id=gaz"
COPYRIGHT_URL = "https://ebible.org/gaz/copyright.htm"
PACKAGE_URL = "https://ebible.org/Scriptures/gaz_usfm.zip"
KEY_URL = "https://mljohnson.org/gpg.htm"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
SOURCE_IDS = ["SRC-387", "SRC-388", "SRC-389"]
RETRIEVED = "2026-10-26"
COPYRIGHT = (
    "Copyright © 2022 Biblica, Inc. Original edition: New Oromo Contemporary Version, "
    "Oromo (West Central / Afaan Oromoo), publisher code GAZBIB or gaz. The source page states CC BY-SA 4.0. "
    "Attribution required: ‘The original work by Biblica, Inc. is available for free at www.biblica.com and open.bible.’ "
    "This archive converted publisher USFM into reader JSON and retained the original USFM ZIP; formatting and asset handling may differ. "
    "This derivative is provided under CC BY-SA 4.0. The Biblica® mark is removed from derivative display metadata as the source terms require; "
    "the publisher does not endorse this conversion. Images are excluded because their reuse terms differ."
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_signature(z: zipfile.ZipFile) -> dict:
    key, signed = z.read("keys.asc"), z.read("signature.txt.asc")
    gpg = shutil.which("gpg")
    bash = None
    if not gpg and os.name == "nt":
        for root in (os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            candidate = Path(root) / "Git/bin/bash.exe" if root else None
            if candidate and candidate.is_file():
                bash = str(candidate)
                break
    if not gpg and not bash:
        raise RuntimeError("GnuPG is required to verify the source checksum signature.")
    with tempfile.TemporaryDirectory(prefix=".gaz-gpg-", dir=ROOT) as temp:
        home = Path(temp) / "gnupg"
        home.mkdir()
        (home / "keys.asc").write_bytes(key)
        (home / "signature.txt.asc").write_bytes(signed)
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
            key_path, sig_path = home / "keys.asc", home / "signature.txt.asc"
            subprocess.run([gpg, "--batch", "--import", str(key_path)], cwd=ROOT, env=env, capture_output=True, check=True)
            results = [subprocess.run([gpg, "--batch", "--status-fd", "1", "--verify", str(sig_path)], cwd=ROOT, env=env, capture_output=True, text=True)]
        result = results[-1]
        if result.returncode:
            raise ValueError(f"OpenPGP signature verification failed: {result.stderr.strip()}")
        validsig = next((line.split() for line in result.stdout.splitlines() if line.startswith("[GNUPG:] VALIDSIG ")), None)
        if not validsig or validsig[2].upper() != "54D714D76956DA6673DC1EEA5F62009D93505F26":
            raise ValueError("The verified signature does not match the published World English Bible editors key fingerprint.")
    return {
        "valid": True,
        "signer_fingerprint": validsig[2],
        "fingerprint_reference": KEY_URL,
        "signature_hash_algorithm": "SHA-1 (legacy)",
        "signing_key_algorithm": "DSA-1024 (legacy)",
        "identity_limit": "The signature verifies with the package key, and its fingerprint matches the key maintainer's published page. This is not independent proof of identity, custody, or authority; legacy DSA-1024/SHA-1 limits apply.",
    }


def build() -> tuple[list[dict], list[dict], list[dict], dict]:
    package = SOURCE.read_bytes()
    with zipfile.ZipFile(SOURCE) as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f"Source ZIP CRC failed at {bad}.")
        signature = verify_signature(z)
        signed_text = z.read("signature.txt.asc").decode("utf-8")
        listed = {m.group(2): m.group(1) for m in re.finditer(r"^([0-9a-f]{64})\s+(\S+)$", signed_text, re.M)}
        members = {name: z.read(name) for name in z.namelist() if name.lower().endswith(".usfm")}
    if len(members) != 66 or set(members) != {name for name in listed if name.lower().endswith(".usfm")}:
        raise ValueError("The package must contain exactly its 66 signed USFM members.")
    hashes = {name: sha(data) for name, data in members.items()}
    if any(listed.get(name) != digest for name, digest in hashes.items()):
        raise ValueError("A USFM member hash does not match the signed checksum list.")

    codes: dict[str, str] = {}
    for name, data in members.items():
        match = re.search(r"^\\id\s+([A-Z0-9]{3})\s+-\s+(.+?)\s*$", data.decode("utf-8-sig"), re.M)
        if not match or match.group(1) not in BOOK_NAMES or match.group(1) in codes:
            raise ValueError(f"Unknown/duplicate USFM book ID in {name}.")
        codes[match.group(1)] = name
    if set(codes) != set(BOOK_NAMES):
        raise ValueError("USFM book IDs differ from expected 66 conventional modules.")

    readers, corpora, inventory = [], [], []
    inline_marker_counts = Counter()
    for code in BOOK_NAMES:
        name, raw = codes[code], members[codes[code]]
        inline_marker_counts.update(re.findall(r"\\(nd|wj|tl|xt)\*?", raw.decode("utf-8-sig")))
        parsed = parse_book(raw, name)
        reader_id = f"gaz-{code.lower()}-research"
        corpus_id = f"gazbib-2022-{code.lower()}"
        title = f"{BOOK_NAMES[code]} — New Oromo Contemporary Version (gaz, 2022)"
        reader = {
            "reader_id": reader_id, "research_corpus_id": corpus_id, "canon_id": None,
            "title": title, "display_name": f"{BOOK_NAMES[code]} · Afaan Oromoo · 2022 edition",
            "text_origin": "published_translation", "translation_id": "gazbib-2022",
            "language": "Oromo, West Central (Afaan Oromoo)", "language_tag": "gaz",
            "language_assignment_status": "Publisher-declared language and edition metadata; no independent language-specialist review.",
            "script_code": "Latn", "translator": "Not identified in the inspected edition notice", "contributor": "Biblica, Inc.",
            "translation_basis_status": "unknown", "translation_basis_note": "The inspected source page does not identify source language or relay path; none is inferred.",
            "edition": "New Oromo Contemporary Version; copyright © 2022 Biblica, Inc.; publisher code GAZBIB or gaz.",
            "edition_scope": "This is one of 66 USFM modules in the retained eBible.org package. English book labels are navigation aids, not Oromo title translations. No EOTC or Eritrean Orthodox canon mapping is asserted.",
            "rights_classification": "open_license", "license_id": "CC-BY-SA-4.0", "license_url": LICENSE_URL,
            "copyright_notice": COPYRIGHT, "commercial_use": "CC BY-SA 4.0 permits commercial sharing and adaptations subject to its attribution, change-indication, ShareAlike, and trademark conditions. Source illustrations have separate terms and are excluded.",
            "unit_label": "USFM chapter/verse labels observed", "unit_count": parsed["unit_count"],
            "verse_marker_count": parsed["unit_count"], "chapter_count": parsed["chapter_count"], "section_label": "Chapter",
            "chapter_structure_note": f"Automated parse found {parsed['chapter_count']} consecutive chapter divisions and {parsed['unit_count']} distinct chapter/verse labels. The source labels and structural markers are retained; counts do not prove printed-edition completeness or translation accuracy.",
            "chapter_structure_status": "source_package_parsed_with_limits",
            "source_numbered_unit_count": parsed["unit_count"],
            "source_unnumbered_unit_count": sum(len(v.get("continuations", [])) for c in parsed["chapters"] for v in c["verses"]),
            "source_pages": f"readers/source/gaz/gaz_usfm.zip::{name}",
            "source_package_sha256": sha(package), "source_snapshot_sha256": hashes[name], "source_ids": SOURCE_IDS,
            "inline_format_markers_rendered_as_plain_text": "nd, wj, tl, and xt content is displayed without its inline USFM formatting; original USFM is retained.",
            "rights_status": COPYRIGHT,
            "verification_status": f"ZIP CRC passed; GnuPG verified the package's clear-signed checksum list. Its fingerprint {signature['signer_fingerprint']} matches the key maintainer's public fingerprint page. Every one of the 66 USFM member hashes matches that signed list. Parsing checked chapter sequence and duplicate chapter/verse labels. Legacy DSA-1024/SHA-1 and key identity limits apply. No independent proofread, community review, print completeness audit, or canon crosswalk was performed.",
            "transcription_note": "Machine extraction from publisher USFM into reader JSON. The original USFM is retained for audit; no independent Oromo wording review has been done.",
            "editorial_signs_note": "The parser retains source verse labels, headings, notes, cross-references, continuations, and recognized USFM structure. Image assets are omitted because their terms are separate; captions and source asset details are retained in notes when present.",
            "front_matter": parsed["front_matter"], "source_book_metadata": parsed["book_metadata"], "chapters": parsed["chapters"],
        }
        readers.append(reader)
        write_text_atomically(ROOT / "readers" / f"{reader_id}.json", json.dumps(reader, ensure_ascii=False, indent=2) + "\n", newline="\n")
        corpora.append({
            "corpus_id": corpus_id, "title": title, "reader_id": reader_id,
            "unit_count": parsed["unit_count"], "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped", "candidate_canon_id": None,
            "canon_mapping_note": "The package contains 66 conventional USFM book modules. This does not establish equivalence to the Ethiopian Orthodox Tewahedo or Eritrean Orthodox 81-entry list; no crosswalk is assigned.",
            "language_description": "Publisher identifies Oromo, West Central (Afaan Oromoo), code gaz.",
            "script_description": "Latin script (Latn) recorded for this publisher's named edition; not a claim about all Oromo varieties or witnesses.",
            "unit_summary": f"{parsed['chapter_count']} consecutive source chapter divisions and {parsed['unit_count']} distinct chapter/verse labels in this source member; counts do not establish print completeness.",
            "rights_classification": "open_license", "rights_status": COPYRIGHT,
            "review_status": "Source ZIP integrity, 66 member hashes, book IDs, chapter sequence, and duplicate chapter/verse labels were checked. The wording, completeness against print, and church-canon mapping have not been independently reviewed.",
            "license_id": "CC-BY-SA-4.0", "license_url": LICENSE_URL, "source_ids": SOURCE_IDS,
            "text_origin": "published_translation", "language_tag": "gaz", "script_code": "Latn",
            "translation_id": "gazbib-2022", "translator": "Not identified in the inspected edition notice",
            "translation_basis_status": "unknown", "translation_basis_note": "Source or relay language is not stated in the inspected edition record.",
            "edition_statement": reader["edition"],
        })
        inventory.append({"usfm_id": code, "path": name, "book_label": BOOK_NAMES[code], "source_title": parsed["source_title"], "byte_length": len(raw), "sha256": hashes[name], "chapter_count": parsed["chapter_count"], "unit_count": parsed["unit_count"], "front_matter_item_count": len(parsed["front_matter"]), "marker_counts": parsed["marker_counts"]})

    manifest = {
        "source_id": SOURCE_IDS[1], "source_url": PACKAGE_URL, "retrieved_at": RETRIEVED,
        "archive_sha256": sha(package), "archive_byte_length": len(package), "signature": signature,
        "zip_member_count": 70, "usfm_book_count": len(inventory), "usfm_members": inventory,
        "inline_marker_tag_counts": dict(sorted(inline_marker_counts.items())),
        "verification": "ZIP CRC passed. GnuPG verified the clear-signed SHA-256 list using the included public key; its fingerprint matches the key maintainer's published page. All 66 USFM member hashes matched. This verifies integrity relative to that key, not independent identity or authority.",
        "limits": "Legacy DSA-1024/SHA-1 signature. The 66 conventional modules do not establish completeness against print, translation accuracy, community review, or EOTC/Eritrean Orthodox canon equivalence.",
    }
    write_text_atomically(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", newline="\n")
    capture_path = SOURCE.parent / "capture-manifest.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    capture["content_scope"] = (
        "Verified: ZIP CRC passed, its clear-signed SHA-256 list was checked with GnuPG, and all 66 USFM member hashes matched. "
        "The separate build manifest records per-book chapter and verse-label counts and parser limits. Chapter/verse continuity and duplicate labels were checked; this does not establish printed-edition completeness, independent wording accuracy, or canon mapping."
    )
    capture["signature_verification"] = signature
    capture["verified_manifest_path"] = "research/gaz-usfm-source-manifest.json"
    write_text_atomically(capture_path, json.dumps(capture, ensure_ascii=False, indent=2) + "\n", newline="\n")
    notice = (
        "New Oromo Contemporary Version (gaz) source notice\n\n"
        "Copyright © 2022 Biblica, Inc.\nLanguage: Oromo, West Central (Afaan Oromoo), publisher code GAZBIB or gaz.\n"
        f"Edition record: {DETAIL_URL}\nCopyright and license notice: {COPYRIGHT_URL}\nOriginal USFM package: {PACKAGE_URL}\nLicense: CC BY-SA 4.0 ({LICENSE_URL})\n\n"
        "Required attribution: The original work by Biblica, Inc. is available for free at www.biblica.com and open.bible.\n"
        "Change made: Publisher USFM was parsed into reader JSON; structural markup is represented in the app's reader format. The original USFM ZIP is preserved. The publisher does not endorse this conversion. This derivative is made available under CC BY-SA 4.0. The Biblica® mark is removed from derivative display metadata as the source terms require. Images are not included because their terms differ.\n\n"
        f"The source ZIP has a valid clear-signed checksum list and all listed USFM hashes match. Signature fingerprint {signature['signer_fingerprint']} matches {KEY_URL}; key identity, custody and signing authority are not independently certified. Signature algorithms are legacy DSA-1024/SHA-1. No independent proofread, community review, print completeness audit, or canon crosswalk is claimed.\n"
    )
    write_text_atomically(NOTICE, notice, newline="\n")
    sources = [
        {"source_id": SOURCE_IDS[0], "source_name": "eBible.org — New Oromo Contemporary Version edition and license notice", "url": DETAIL_URL,
         "local_metadata_url": "readers/source/gaz/details.html",
         "inspection_and_limitations": "Inspected 2026-10-26. The provider identifies the edition as New Oromo Contemporary Version, language Oromo/West Central (gaz), code GAZBIB or gaz, copyright © 2022 Biblica, Inc., contributor Biblica, Inc., and links to a USFM package. Its copyright notice grants CC BY-SA 4.0, requires attribution/change indication/ShareAlike for derivatives, prohibits retaining the Biblica® mark in modified derivatives, and says images have separate restrictions. This does not establish translation accuracy or EOTC/Eritrean canon equivalence.",
         "archive_status": "Provider-stated edition metadata and license recorded; original USFM retained; no accuracy or canon claim.",
         "rights_classification": "unknown",
         "rights_status": "This record is the provider's edition and license-information webpage. Its retained notice states that the scripture text is licensed CC BY-SA 4.0, with attribution, change indication, ShareAlike, and derivative trademark-removal requirements; images have separate terms. This establishes the provider-stated text license, not reuse rights in the webpage itself. Rights for the separately bundled USFM package and converted reader are recorded in their own records.",
         "rights_basis": "The captured edition/copyright notices identify CC BY-SA 4.0 for scripture text but do not establish a license for reproducing the information webpage. The unknown classification is scoped to the webpage resource, not to the separately identified text layer."},
        {"source_id": SOURCE_IDS[1], "source_name": "eBible.org — New Oromo Contemporary Version USFM package", "url": PACKAGE_URL,
         "local_metadata_url": "research/gaz-usfm-source-manifest.json",
         "local_source_package_url": "readers/source/gaz/gaz_usfm.zip",
         "inspection_and_limitations": f"Retrieved 2026-10-26 and retained at readers/source/gaz/gaz_usfm.zip (SHA-256 {sha(package)}; {len(package)} bytes). ZIP CRC passed. GnuPG verified the clear-signed checksum list; fingerprint {signature['signer_fingerprint']} matches the key maintainer's published page. All 66 USFM hashes match. The signature uses legacy DSA-1024/SHA-1. Parser checks package member IDs, sequential chapter labels, and duplicate chapter/verse labels only; it does not establish print completeness or wording accuracy.",
         "archive_status": "Original licensed USFM ZIP retained locally; signed checksums verified, with key-identity and parsing limits documented.",
         "rights_classification": "mixed",
         "rights_status": "The 66 USFM scripture-text members are identified by the retained provider notice as CC BY-SA 4.0; comply with attribution, change-indication, ShareAlike, and derivative trademark-removal conditions. The ZIP also contains a copyright HTML page, stylesheet, public key, and signature files whose reuse terms are not established here. This mixed classification applies to the aggregate package; it does not withdraw or broaden the stated text license. Images are excluded from the converted readers and have separate terms.",
         "rights_basis": "The retained provider notice and edition record state CC BY-SA 4.0 for text. The ZIP inventory independently shows ancillary .htm, .css, and .asc members alongside the USFM files; no separate permission basis was established for every ancillary member. The text-layer license is recorded separately on each reader."},
        {"source_id": SOURCE_IDS[2], "source_name": "Michael Paul Johnson — published OpenPGP fingerprint listing", "url": KEY_URL,
         "inspection_and_limitations": f"Inspected 2026-10-26. The key page lists fingerprint {signature['signer_fingerprint']} for the World English Bible editors key; this matches GnuPG's verified signer fingerprint on the package checksum list. This is a comparison to the key maintainer's own published listing, not independent identity or authority verification.",
         "archive_status": "Key fingerprint cross-reference only; legacy signature and identity limits remain."},
    ]
    return readers, corpora, sources, manifest

