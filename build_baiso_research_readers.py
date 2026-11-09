"""Build Baiso New Testament readers from two retained eBible.org USFM editions.

The Ethiopic-script package has 27 conventional NT book modules. The separate
Latin-script package has only 16; its absent modules are recorded, never filled
from another edition. Both stay research-only, outside Church-canon mappings.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import zipfile
from pathlib import Path

import build_maale_research_readers as maale
from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "baiso"
MANIFEST_DIR = ROOT / "research"
DETAIL_BASE = "https://ebible.org/Bible/details.php?id="
PACKAGE_BASE = "https://www.ebible.org/Scriptures/"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
REVIEWED_AT = "2026-10-26"
BOOK_ORDER = [
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL",
    "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN",
    "3JN", "JUD", "REV",
]
EDITION_CONFIG = [
    {
        "edition_id": "bswl", "key": "latin", "script": "Latn", "script_label": "Latin script",
        "title": "Baiso NT (Latin)", "year": 2024, "source_ids": ["SRC-410", "SRC-411"],
        "expected_codes": [
            "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "GAL", "EPH", "PHP", "COL", "TIT", "PHM",
            "HEB", "JAS", "JUD", "REV",
        ],
        "expected_sha256": "3f06279eccae05b1f12663cf7915109bb37fc1f29e8ad30fe6b22346571c5de5",
        "copyright": "Copyright © The Word for the World International (edition record accessed 2026-10-26; the record does not state a year).",
    },
    {
        "edition_id": "bswe", "key": "ethiopic", "script": "Ethi", "script_label": "Ethiopic script",
        "title": "Baiso: አማቶ ኦኡሱብ (New Testament)", "year": 2024,
        "source_ids": ["SRC-412", "SRC-413"], "expected_codes": BOOK_ORDER,
        "expected_sha256": "46736a655c08e80cc1c5c3d46cfc26c1b2c5a58d5a99f91bd697a86db36ce0ba",
        "copyright": "Copyright © 2024 The Word for the World International.",
    },
]
ALL_SOURCE_IDS = [source_id for config in EDITION_CONFIG for source_id in config["source_ids"]]
COPYRIGHT = (
    "The eBible.org edition record identifies the Baiso language (bsw), The Word for the World International as contributor, "
    "and CC BY-SA 4.0 terms for the translation text. This archive converted the retained USFM source into reader JSON; "
    "the original package is included. Attribution is retained, changes are identified, and this archive does not imply publisher endorsement. "
    "Image terms are separate; no images are bundled."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_members(config: dict) -> tuple[bytes, dict[str, bytes], dict[str, str], dict]:
    package_path = SOURCE_DIR / f"{config['edition_id']}_usfm.zip"
    package = package_path.read_bytes()
    if sha256(package) != config["expected_sha256"]:
        raise ValueError(f"Pinned {config['edition_id']} package bytes changed; review the new source before rebuilding.")
    with zipfile.ZipFile(package_path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"{config['edition_id']} source ZIP CRC failed at {bad}.")
        members = {name: archive.read(name) for name in archive.namelist()}
    if not {"keys.asc", "signature.txt.asc"}.issubset(members):
        raise ValueError(f"{config['edition_id']} package lacks its signed checksum list or included key.")
    signature = maale.verify_checksum_signature(members["keys.asc"], members["signature.txt.asc"])
    signed = {
        match.group(2): match.group(1).lower()
        for match in re.finditer(r"^([0-9a-f]{64})\s+(\S+)\s*$", members["signature.txt.asc"].decode("utf-8", "replace"), re.M)
    }
    expected_names = set(members) - {"keys.asc", "signature.txt.asc"}
    if set(signed) != expected_names:
        raise ValueError(f"{config['edition_id']} signed list does not cover exactly its ordinary package members.")
    mismatched = [name for name, digest in signed.items() if sha256(members[name]) != digest]
    if mismatched:
        raise ValueError(f"{config['edition_id']} members disagree with signed hashes: {sorted(mismatched)}")
    return package, members, signed, signature


def build_edition(config: dict) -> tuple[list[dict], list[dict], dict, dict]:
    package, members, hashes, signature = package_members(config)
    edition = config["edition_id"]
    details_path = SOURCE_DIR / f"{edition}-details.html"
    details = details_path.read_text(encoding="utf-8", errors="replace")
    required = (
        "Baiso", config["title"], "Creative Commons Attribution Share-Alike license 4.0",
        f"{edition}_usfm.zip", "The Word for the World International",
    )
    if any(item not in details for item in required):
        raise ValueError(f"Captured {edition} provider page lacks title, license, contributor, or package evidence.")
    usfm_members = {
        name: content for name, content in members.items() if name.lower().endswith(".usfm")
    }
    inventory = []
    parsed_by_code = {}
    for name, content in usfm_members.items():
        parsed = maale.parse_book(content, name)
        if not re.fullmatch(rf"\d{{2}}-[A-Z0-9]{{3}}{edition}\.usfm", name):
            raise ValueError(f"Unexpected {edition} source member name: {name}.")
        if not name.endswith(f"-{parsed['code']}{edition}.usfm") or parsed["code"] in parsed_by_code:
            raise ValueError(f"Duplicate or mismatched USFM book identity in {name}.")
        parsed_by_code[parsed["code"]] = (name, parsed)
    source_codes = list(parsed_by_code)
    if source_codes != config["expected_codes"]:
        raise ValueError(
            f"{edition} book inventory changed. Expected {config['expected_codes']}, found {source_codes}; do not silently normalize."
        )

    readers, corpora, labels = [], [], []
    for position, code in enumerate(source_codes, start=1):
        member_name, parsed = parsed_by_code[code]
        title = maale.BOOK_NAMES[code]
        toc2 = next((item["text"] for item in parsed["book_metadata"] if item["marker"] == "toc2"), None)
        source_title = toc2 or parsed["source_title"]
        labels.append({"position": position, "book_code": code, "source_title_label": source_title})
        reader_id = f"baiso-{config['key']}-{code.lower()}-research"
        corpus_id = f"bsw-{edition}-{code.lower()}"
        unit_count = parsed["unit_count"]
        note_count = sum(len(chapter.get("notes", [])) for chapter in parsed["chapters"])
        continuation_count = sum(
            len(verse.get("continuations", [])) for chapter in parsed["chapters"] for verse in chapter["verses"]
        )
        scope = (
            f"One of {len(source_codes)} USFM book members actually present in eBible.org edition {edition.upper()} ({config['title']}). "
            "The Latin-script edition omits 11 conventional NT modules in this package; the Ethiopic-script package has 27. "
            "These provider/module scopes do not establish equivalence to any Ethiopian or Eritrean Orthodox canon. No canon crosswalk is assigned."
            if edition == "bswl" else
            f"One of {len(source_codes)} USFM book members in eBible.org edition {edition.upper()} ({config['title']}). "
            "The provider calls it a New Testament; this conventional 27-module inventory does not establish equivalence to any Ethiopian or Eritrean Orthodox canon. No canon crosswalk is assigned."
        )
        verification = (
            f"The exact source member {member_name} has SHA-256 {hashes[member_name]}, matching the clear-signed member list in the retained ZIP. "
            f"GnuPG verifies the list against the key included with that ZIP ({signature['signer_fingerprint']}); this is tamper evidence, not independent "
            "proof of signer identity, custody, or authority. The signature uses legacy DSA-1024/SHA-1. Extraction preserves publisher verse labels, "
            "chapter divisions, recognized headings, introduction material, notes, continuations, and other supported USFM structures. "
            "These checks do not establish print completeness, wording accuracy, language-community review, translation basis, or Church-canon identity."
        )
        reader = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "canon_id": None,
            "title": f"{title} — Baiso New Testament ({edition.upper()}, {config['script_label']})",
            "display_name": f"{title} · Baiso · {config['script_label']} · eBible.org",
            "text_origin": "published_translation",
            "translation_id": f"bsw-{edition}-2024",
            "language": "Baiso (Bayso)",
            "language_tag": "bsw",
            "language_assignment_status": "publisher_declared_in_source_page_and_USFM_package",
            "script_code": config["script"],
            "translator": "Not named in the inspected edition page or retained USFM headers",
            "contributor": "The Word for the World International",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The inspected edition page does not identify the source language or a relay-language path; none is inferred.",
            "edition": f"{config['title']}; {config['script_label']}; {config['copyright']}",
            "edition_scope": scope,
            "rights_classification": "open_license",
            "license_id": "CC-BY-SA-4.0",
            "license_url": LICENSE_URL,
            "copyright_notice": COPYRIGHT,
            "commercial_use": "The provider-stated CC BY-SA 4.0 terms allow commercial sharing and adaptations with attribution, change indication, and ShareAlike. Images and other media have separate terms and are not included.",
            "unit_label": "USFM verse labels observed",
            "unit_count": unit_count,
            "verse_marker_count": unit_count,
            "chapter_count": parsed["chapter_count"],
            "section_label": "Chapter",
            "chapter_structure_note": (
                f"This source member contains {parsed['chapter_count']} consecutive chapter divisions, {unit_count} distinct source verse labels, "
                f"{note_count} notes, {len(parsed['front_matter'])} front-matter elements, and USFM marker counts {parsed['marker_counts']}. "
                "Labels and recognized structure are preserved; counts describe extraction from this exact source member only."
            ),
            "chapter_structure_status": "source_package_parsed_with_limits",
            "source_numbered_unit_count": unit_count,
            "source_unnumbered_unit_count": continuation_count,
            "source_pages": f"readers/source/baiso/{edition}_usfm.zip::{member_name}",
            "source_package_sha256": sha256(package),
            "source_snapshot_sha256": hashes[member_name],
            "source_ids": config["source_ids"],
            "rights_status": COPYRIGHT,
            "verification_status": verification,
            "transcription_note": "Display-reader extraction from the publisher's USFM. The exact USFM member and complete signed source package remain locally available; no independent wording proofread or print collation is claimed.",
            "editorial_signs_note": "The source USFM remains bundled so supported structure, unrendered styles, and extraction decisions can be inspected; this reader is not a replacement for the publisher's original encoding.",
            "front_matter": parsed["front_matter"],
            "source_book_metadata": parsed["book_metadata"],
            "chapters": parsed["chapters"],
        }
        path = ROOT / "readers" / f"{reader_id}.json"
        write_text_atomically(path, json.dumps(reader, ensure_ascii=False, indent=2) + "\n", newline="\n")
        readers.append(reader)
        corpora.append({
            "corpus_id": corpus_id, "title": reader["title"], "reader_id": reader_id,
            "unit_count": unit_count, "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped", "candidate_canon_id": None,
            "canon_mapping_note": "No Ethiopian Orthodox Tewahedo or Eritrean Orthodox canon crosswalk is assigned. The edition and its conventional NT module inventory do not establish correspondence to either Church's canon.",
            "language_description": "Baiso (Bayso), IANA language tag bsw; provider edition identifies Baiso.",
            "script_description": f"{config['script_label']} (ISO 15924 {config['script']}) as identified by the provider and observed in the retained USFM.",
            "unit_summary": f"{unit_count} distinct source verse labels across {parsed['chapter_count']} consecutive USFM chapter divisions; this source member only.",
            "rights_classification": "open_license", "rights_status": COPYRIGHT,
            "license_id": "CC-BY-SA-4.0", "license_url": LICENSE_URL,
            "review_status": verification, "source_ids": config["source_ids"],
            "text_origin": "published_translation", "language_tag": "bsw",
            "script_code": config["script"], "translation_id": f"bsw-{edition}-2024",
            "translator": "Not named in the inspected edition page or retained USFM headers",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The inspected edition page does not identify the source language or a relay-language path.",
            "edition_statement": reader["edition"],
        })
        inventory.append({
            "position": position, "book_code": code, "member_name": member_name,
            "source_title": parsed["source_title"], "source_title_label": source_title,
            "byte_length": len(members[member_name]), "sha256": hashes[member_name],
            "chapter_count": parsed["chapter_count"], "verse_label_count": unit_count,
            "note_count": note_count, "front_matter_item_count": len(parsed["front_matter"]),
            "unnumbered_continuation_count": continuation_count,
            "marker_counts": parsed["marker_counts"],
        })

    absent = [code for code in BOOK_ORDER if code not in source_codes]
    source_manifest = {
        "manifest_version": 1,
        "title": f"eBible.org Baiso {config['script_label']} USFM package audit ({edition.upper()})",
        "edition_id": edition.upper(), "language_tag": "bsw", "script_code": config["script"],
        "source_ids": config["source_ids"], "edition_page_url": DETAIL_BASE + edition,
        "package_url": PACKAGE_BASE + f"{edition}_usfm.zip", "captured_at": REVIEWED_AT,
        "source_edition_page": {
            "local_path": f"readers/source/baiso/{edition}-details.html",
            "byte_length": (SOURCE_DIR / f"{edition}-details.html").stat().st_size,
            "sha256": sha256((SOURCE_DIR / f"{edition}-details.html").read_bytes()),
        },
        "archive_byte_length": len(package), "archive_sha256": sha256(package),
        "member_count": len(members), "zip_crc_check": "passed",
        "signed_member_count": len(hashes), "signature": signature,
        "usfm_book_count": len(inventory), "usfm_members": inventory,
        "conventional_new_testament_module_inventory": BOOK_ORDER,
        "absent_conventional_module_codes": absent,
        "verification": "ZIP CRCs passed; GnuPG verified the clear-signed member SHA-256 list against the co-distributed key; all listed file hashes match; the USFM source labels were compared against extracted reader labels per chapter.",
        "limits": (
            "The signing key is included in the same ZIP as the signed hash list. Fingerprint comparison to the key maintainer's published page is corroboration only, not independent proof of identity, custody, or authority. DSA-1024/SHA-1 is legacy cryptography. "
            + ("This Latin-script source package contains only 16 conventional NT modules; absent codes are listed explicitly and no text was inferred from the Ethiopic-script edition." if edition == "bswl" else "This package contains 27 conventional NT modules; that digital module inventory does not establish printed completeness or an Ethiopian/Eritrean Orthodox canon crosswalk.")
            + " Neither extraction integrity nor a module count certifies translation accuracy, source-language basis, community review, or completeness."
        ),
    }
    manifest_path = MANIFEST_DIR / f"baiso-{config['key']}-usfm-source-manifest.json"
    write_text_atomically(manifest_path, json.dumps(source_manifest, ensure_ascii=False, indent=2) + "\n", newline="\n")
    return readers, corpora, source_manifest, {"labels": labels, "absent": absent, "inventory": inventory}


def build() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    editions, corpora, manifests = [], [], []
    for config in EDITION_CONFIG:
        readers, edition_corpora, manifest, menu_data = build_edition(config)
        editions.extend(readers)
        corpora.extend(edition_corpora)
        manifests.append(manifest)
        detail_url = DETAIL_BASE + config["edition_id"]
        package_url = PACKAGE_BASE + f"{config['edition_id']}_usfm.zip"
        menu_json_path = MANIFEST_DIR / f"baiso-{config['key']}-menu.json"
        menu_html_path = MANIFEST_DIR / f"baiso-{config['key']}-menu.html"
        entries = menu_data["labels"]
        menu = {
            "title": f"eBible.org {config['title']} — {config['script_label']}",
            "edition_id": config["edition_id"].upper(), "language_tag": "bsw",
            "script_code": config["script"], "source_ids": config["source_ids"],
            "canon_mapping_state": "not_mapped",
            "menu_basis": "USFM member order in the retained provider ZIP; English display names are navigation labels only.",
            "entries": entries, "absent_conventional_nt_module_codes": menu_data["absent"],
            "scope_note": "Reader text exists only for modules listed here. No Ethiopian or Eritrean Orthodox canon mapping or completeness claim is made.",
        }
        write_text_atomically(menu_json_path, json.dumps(menu, ensure_ascii=False, indent=2) + "\n", newline="\n")
        li = "\n".join(
            f'<li lang="bsw" translate="no"><span>{html.escape(item["source_title_label"])}</span> '
            f'<a href="../index.html?reader=baiso-{config["key"]}-{item["book_code"].lower()}-research#reader">Open research reader · {html.escape(maale.BOOK_NAMES[item["book_code"]])}</a></li>'
            for item in entries
        )
        absent_text = ", ".join(maale.BOOK_NAMES[code] for code in menu_data["absent"]) or "None in the conventional 27-module inventory"
        html_doc = (
            '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Baiso New Testament — {config["script_label"]}</title><link rel="stylesheet" href="../styles.css">'
            '<main class="research-menu"><p><a href="../index.html">Ethiopian Bible Library</a></p>'
            f'<h1>Baiso New Testament · {config["script_label"]}</h1>'
            f'<p>Publisher: eBible.org, edition {config["edition_id"].upper()}, {config["copyright"]} '
            'The provider states CC BY-SA 4.0 terms for the translation text; images are separately licensed and are not bundled. '
            'Readers are research-only and are not mapped to an Ethiopian or Eritrean Orthodox canon.</p>'
            f'<p><a href="{detail_url}">Publisher edition and license record</a> · '
            f'<a href="{package_url}">Original USFM package</a> · '
            f'<a href="baiso-{config["key"]}-usfm-source-manifest.json">Local structure and checksum audit</a></p>'
            f'<p>Modules present: {len(entries)}. Conventional NT module codes absent from this exact package: {html.escape(absent_text)}.</p>'
            f'<ol lang="bsw" translate="no">{li}</ol>'
            '<p>Counts describe source package members and extraction only. They do not establish textual accuracy, printed completeness, translation basis, community review, or Church-canon identity.</p></main></html>\n'
        )
        write_text_atomically(menu_html_path, html_doc, newline="\n")

    source_notice = (
        "Baiso New Testament editions — source and rights notice\n\n"
        "Language: Baiso (Bayso), IANA tag bsw. Both eBible.org edition pages identify The Word for the World International as contributor and state CC BY-SA 4.0 terms for translation text. The provider's Latin-script package (BSWLTW / bswl) contains 16 USFM books; the Ethiopic-script package (BSWETW / bswe) contains 27. These are separate editions and their texts are not merged.\n\n"
        f"Latin edition and terms: {DETAIL_BASE}bswl\nOriginal package: {PACKAGE_BASE}bswl_usfm.zip\n"
        f"Ethiopic edition and terms: {DETAIL_BASE}bswe\nOriginal package: {PACKAGE_BASE}bswe_usfm.zip\n"
        f"License: {LICENSE_URL}\n\n"
        "Changes in this archive: USFM was parsed into JSON display readers; publisher labels and supported structural markers were retained, with the original packages kept for inspection. The publisher has not endorsed this conversion. Attribution, change indication, and ShareAlike obligations apply to redistributed adaptations. The publisher gives images separate terms; images are not bundled.\n"
        "Both ZIPs pass CRC and signed-member hash validation against a checksum list signed with a key included in the same ZIP. The fingerprint matches the key maintainer's published page, but that is not independent proof of signer identity, custody, or authority. DSA-1024/SHA-1 is legacy cryptography.\n"
        "No individual translator, source language, relay-language path, text accuracy review, printed completeness, or community review is established by the inspected sources. Neither edition is mapped to an Ethiopian Orthodox Tewahedo or Eritrean Orthodox canon. The Latin-script package's missing conventional module codes are recorded in its manifest and menu; no absent text is supplied from the Ethiopic edition.\n"
    )
    write_text_atomically(SOURCE_DIR / "SOURCE-NOTICE.txt", source_notice, newline="\n")

    sources = []
    for config in EDITION_CONFIG:
        edition = config["edition_id"]
        detail_path = SOURCE_DIR / f"{edition}-details.html"
        package_path = SOURCE_DIR / f"{edition}_usfm.zip"
        manifest_path = MANIFEST_DIR / f"baiso-{config['key']}-usfm-source-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        sources.extend([
            {
                "source_id": config["source_ids"][0],
                "source_name": f"eBible.org — Baiso {config['script_label']} edition and rights record ({edition.upper()})",
                "url": DETAIL_BASE + edition,
                "local_copy_url": detail_path.relative_to(ROOT).as_posix(),
                "inspection_and_limitations": (
                    f"Inspected 2026-10-26. The retained provider page identifies Baiso language tag bsw, title {config['title']}, "
                    f"{config['script_label']}, The Word for the World International as contributor, and a linked USFM download. "
                    "It states CC BY-SA 4.0 for translation text and separate terms for images. The page does not establish individual translator, "
                    "translation basis, accuracy, printed completeness, community review, or Ethiopian/Eritrean Orthodox canon identity."
                ),
                "archive_status": "Edition identity, script, provider-stated translation-text license, and page capture retained; research-only, with no canon crosswalk.",
                "rights_classification": "unknown",
                "rights_status": (
                    f"This record is the provider's {config['script_label']} edition and license-information webpage. It states CC BY-SA 4.0 for the Baiso translation text and separate terms for images. "
                    "This establishes the provider-stated text license, not reuse rights in the webpage itself. Rights for the separately bundled USFM package and converted readers are recorded in their own records."
                ),
                "rights_basis": "The captured edition page identifies CC BY-SA 4.0 for translation text but does not establish a license for reproducing the information webpage. The unknown classification is scoped to the webpage resource, not to the separately identified text layer.",
            },
            {
                "source_id": config["source_ids"][1],
                "source_name": f"eBible.org — Baiso {config['script_label']} USFM package ({edition.upper()})",
                "url": PACKAGE_BASE + f"{edition}_usfm.zip",
                "local_copy_url": package_path.relative_to(ROOT).as_posix(),
                "local_metadata_url": manifest_path.relative_to(ROOT).as_posix(),
                "inspection_and_limitations": (
                    f"Exact provider package retained ({manifest['archive_byte_length']} bytes; SHA-256 {manifest['archive_sha256']}). "
                    f"Its {manifest['member_count']}-member ZIP passes CRC validation; GnuPG verified its signed SHA-256 list against the co-distributed key, "
                    f"and all {manifest['signed_member_count']} signed file hashes match. The key reports fingerprint {manifest['signature']['signer_fingerprint']}; "
                    "the same fingerprint appears on the key maintainer's page, which does not independently prove identity, custody, or authority. "
                    f"The package has {manifest['usfm_book_count']} USFM book modules, {sum(row['chapter_count'] for row in manifest['usfm_members'])} chapter divisions, "
                    f"and {sum(row['verse_label_count'] for row in manifest['usfm_members'])} observed verse labels. These counts verify source-to-reader structure only. "
                    + ("The package omits 11 conventional NT module codes; the archive records these absences and does not fill them from another script edition." if edition == "bswl" else "The 27-module conventional NT inventory is not an Orthodox-canon crosswalk or proof of printed completeness.")
                ),
                "archive_status": "Original package stored offline; CRC, signed member inventory, SHA-256 hashes, and ordered chapter/label extraction audited; research-only.",
                "rights_classification": "mixed",
                "rights_status": (
                    f"The {manifest['usfm_book_count']} USFM scripture-text members are identified by the retained provider notice as CC BY-SA 4.0; follow its attribution, change-indication, and ShareAlike terms. "
                    "The ZIP also contains a copyright HTML page, stylesheet, public key, and signature files whose reuse terms are not established here. This mixed classification applies to the aggregate package; it does not withdraw or broaden the stated text license. Images are not bundled."
                ),
                "rights_basis": "The retained provider notice states CC BY-SA 4.0 for translation text. The ZIP inventory shows .htm, .css, and .asc files alongside USFM; no separate permission basis was established for every ancillary file. The text-layer license is recorded separately on each reader.",
            },
        ])
    module_counts = [
        f"{config['edition_id']} {len(json.loads((MANIFEST_DIR / ('baiso-' + config['key'] + '-usfm-source-manifest.json')).read_text(encoding='utf-8'))['usfm_members'])} modules"
        for config in EDITION_CONFIG
    ]
    print(
        "Built Baiso research readers: "
        + ", ".join(module_counts)
        + f"; {sum(reader['chapter_count'] for reader in editions)} chapter divisions; "
        + f"{sum(reader['unit_count'] for reader in editions)} observed verse labels."
    )
    return editions, corpora, sources, manifests


if __name__ == "__main__":
    build()
