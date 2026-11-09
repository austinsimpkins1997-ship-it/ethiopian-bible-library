"""Build separately scoped English research readers from the retained WEBBE USFM package.

The archive package is the authority. This builder never fetches remote material,
assigns Ethiopian canon mappings, or treats the provider's 81 modules as an EOTC list.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import build_brenton_octateuch as usfm
from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "world-english-bible-british"
PACKAGE = SOURCE_DIR / "eng-webbe_usfm.zip"
CAPTURE_MANIFEST = SOURCE_DIR / "capture-manifest.json"
PACKAGE_URL = "https://ebible.org/Scriptures/eng-webbe_usfm.zip"
EDITION_URL = "https://ebible.org/find/show.php?id=eng-webbe"
COPYRIGHT_URL = "https://ebible.org/eng-webbe/copyright.htm"
FAQ_URL = "https://ebible.org/eng-web/webfaq.htm"
PUBLISHER_BASIS_URL = "https://worldenglish.bible/"
PACKAGE_SHA256 = "54ec9e6b277c95c20ac173927fa7a976f37d86f0c0a54f132ba9f6666d93b6f6"
SIGNER_FINGERPRINT = "54D714D76956DA6673DC1EEA5F62009D93505F26"
REVIEWED_AT = "2026-10-26"
SCRIPTURE_CODES_EXCLUDED = {"FRT", "GLO"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_record(source_id: str, name: str, url: str, status: str, limits: str) -> dict:
    return {
        "source_id": source_id,
        "source_name": name,
        "url": url,
        "inspection_and_limitations": limits,
        "archive_status": status,
        "rights_classification": "public_domain_claimed",
        "rights_status": "eBible.org states that the World English Bible British Edition is public domain and notes that the World English Bible name is a trademark. This is a provider claim, not an independent worldwide legal determination. The project's normalized display extraction is not the provider's signed edition file.",
    }


def _upsert_source(existing: list[dict], additions: list[dict], name: str, url: str, status: str, limits: str) -> str:
    match = next((item for item in [*existing, *additions] if item.get("url") == url), None)
    if match:
        return match["source_id"]
    used = {item.get("source_id") for item in [*existing, *additions]}
    numbers = [int(str(item)[4:]) for item in used if re.fullmatch(r"SRC-\d+", str(item))]
    source_id = f"SRC-{max(numbers, default=-1) + 1:03d}"
    additions.append(_source_record(source_id, name, url, status, limits))
    return source_id


def _title_for(source: str, code: str) -> str:
    match = re.search(rf"^\\toc2\s+(.+?)\s*$", source, re.M)
    if not match:
        match = re.search(r"^\\h\s+(.+?)\s*$", source, re.M)
    if not match:
        raise ValueError(f"USFM {code} has no retained heading or TOC title.")
    return usfm.clean_usfm(match.group(1))


def _front_matter(source: str) -> list[dict]:
    items: list[dict] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        if re.match(r"^\\c\s+\d+\s*$", line):
            break
        match = re.match(r"^\\([A-Za-z0-9]+)\s*(.*)$", line)
        if not match:
            if line.strip():
                raise ValueError(f"Unmarked text before first chapter at USFM line {line_number}.")
            continue
        marker, value = match.groups()
        if marker in {"id", "ide"} or not value.strip():
            continue
        notes = []
        note_pattern = re.compile(r"\\([fx])\b(.*?)\\\1\*", re.S)

        def pull_note(note_match: re.Match) -> str:
            body = note_match.group(2)
            body = re.sub(r"\\(?:fr|xo)\s+[^\\]+", "", body)
            body = re.sub(r"\\(?:ft|fqa|fq|xt)\s*", "", body)
            body = usfm.clean_usfm(body, strip_nested_plus=True)
            if body:
                notes.append({"marker": note_match.group(1), "text": body})
            return " "

        value = note_pattern.sub(pull_note, value)
        cleaned = usfm.clean_usfm(value, strip_nested_plus=True)
        if cleaned:
            item = {"marker": marker, "text": cleaned}
            if notes:
                item["notes"] = notes
            items.append(item)
    return items


def _package_data() -> tuple[bytes, dict[str, bytes], list[dict]]:
    raw_package = PACKAGE.read_bytes()
    package_hash = sha256(raw_package)
    if package_hash != PACKAGE_SHA256:
        raise ValueError(f"Retained WEBBE USFM package hash differs from pinned bytes: {package_hash}.")
    with zipfile.ZipFile(PACKAGE) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"WEBBE ZIP CRC validation failed at {bad_member}.")
        members = {name: archive.read(name) for name in archive.namelist()}
    if "keys.asc" not in members or "signature.txt.asc" not in members:
        raise ValueError("Retained WEBBE package has no co-distributed signing key or signed checksum list.")
    signed_text = members["signature.txt.asc"].decode("utf-8-sig", "replace")
    signed_hashes = {
        match.group(2): match.group(1).lower()
        for match in re.finditer(r"^([0-9a-f]{64})\s+(\S+)\s*$", signed_text, re.M)
    }
    ordinary_names = set(members) - {"keys.asc", "signature.txt.asc"}
    if set(signed_hashes) != ordinary_names:
        raise ValueError("WEBBE signed checksum list does not cover exactly the ordinary ZIP members.")
    mismatch = [name for name, digest in signed_hashes.items() if sha256(members[name]) != digest]
    if mismatch:
        raise ValueError(f"WEBBE source members differ from the publisher-signed checksums: {sorted(mismatch)}.")

    inventory = []
    for name, content in members.items():
        is_usfm = name.lower().endswith(".usfm")
        match = re.match(r"^\d{2,3}-([A-Z0-9]{3})eng-webbe\.usfm$", name) if is_usfm else None
        code = match.group(1) if match else None
        if is_usfm and not match:
            raise ValueError(f"Unexpected WEBBE USFM filename {name!r}.")
        if code == "FRT":
            role = "publisher_preface"
        elif code == "GLO":
            role = "publisher_glossary"
        elif code:
            role = "scripture_module"
        else:
            role = "publisher_support_file"
        inventory.append({
            "path": name,
            "byte_length": len(content),
            "sha256": sha256(content),
            "role": role,
            "source_book_code": code,
        })
    scripture_modules = [item for item in inventory if item["role"] == "scripture_module"]
    codes = [item["source_book_code"] for item in scripture_modules]
    if len(scripture_modules) != 81 or len(codes) != len(set(codes)):
        raise ValueError(f"Expected 81 distinct scripture USFM modules; found {len(scripture_modules)}.")
    if not {"FRT", "GLO", "DAG", "DAN", "ESG"}.issubset({item["source_book_code"] for item in inventory if item["source_book_code"]}):
        raise ValueError("WEBBE source inventory is missing the preface, glossary, or expected Greek Daniel/Esther modules.")
    return raw_package, members, inventory


def _capture_manifest(package: bytes, inventory: list[dict]) -> dict:
    return {
        "record_type": "source_capture_manifest",
        "source_edition": "World English Bible British Edition with Deuterocanon (WEBBE), 2020 stable text edition per eBible.org",
        "reviewed_at": REVIEWED_AT,
        "retrieval_url": PACKAGE_URL,
        "official_edition_page": EDITION_URL,
        "official_rights_notice": COPYRIGHT_URL,
        "official_translation_context": FAQ_URL,
        "package_file": PACKAGE.name,
        "package_byte_length": len(package),
        "package_sha256": sha256(package),
        "package_integrity": {
            "zip_crc_check": "passed",
            "co_distributed_signed_hash_list": "all listed ordinary members match the signed SHA-256 values",
            "signature_verification": "GnuPG reported a good signature from the bundled key for World English Bible editors; key fingerprint 54D714D76956DA6673DC1EEA5F62009D93505F26. The key is co-distributed in the same ZIP; its identity and authority were not independently authenticated. GPG reported trust undefined.",
            "signature_algorithm_observed": "DSA/SHA-1",
            "package_sha256_is_pinned_by_builder": True,
        },
        "inventory_summary": {
            "zip_members": len(inventory),
            "scripture_modules": sum(item["role"] == "scripture_module" for item in inventory),
            "publisher_prefaces": sum(item["role"] == "publisher_preface" for item in inventory),
            "publisher_glossaries": sum(item["role"] == "publisher_glossary" for item in inventory),
            "other_support_files": sum(item["role"] == "publisher_support_file" for item in inventory),
            "canonical_scope": "eBible.org module inventory only; not an Ethiopian Orthodox Tewahedo or Eritrean Orthodox canon list",
            "distinct_daniel_modules": ["DAN", "DAG"],
        },
        "member_inventory": inventory,
        "limitations": [
            "The signed bytes and source member hashes establish integrity relative to the bundled key, not independent key identity or translation accuracy.",
            "The WEBBE reader extracts visible text and selected structure from publisher USFM. Original USFM is retained unchanged in the ZIP.",
            "Reader normalization strips USFM word/alignment formatting and normalizes whitespace; publisher-added words marked with USFM \\add are bracketed in the display extraction. The normalized extraction is not presented as the official signed WEBBE text.",
            "The publisher's Deuterocanon/Apocrypha scope is a different tradition-specific list. No EOTC/Eritrean canon crosswalk is assigned to these readers.",
            "The preface and glossary remain in the source ZIP and are inventoried as non-scripture material, not counted as scripture modules.",
        ],
    }


def _parse_module(code: str, name: str, raw: bytes, package_hash: str) -> tuple[dict, dict, dict]:
    source_text = raw.decode("utf-8-sig")
    id_match = re.search(rf"^\\id\s+{code}(?:\s|$)", source_text, re.M)
    if not id_match:
        raise ValueError(f"The USFM member {name} does not declare its filename's code {code}.")
    chapter_markers = [int(value) for value in re.findall(r"^\\c\s+(\d+)\s*$", source_text, re.M)]
    if not chapter_markers or chapter_markers != list(range(1, len(chapter_markers) + 1)):
        raise ValueError(f"{name} has a missing, duplicate, or out-of-order chapter sequence.")
    title = _title_for(source_text, code)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or code.lower()
    parsed = usfm.parse_usfm(
        raw, code, name, package_hash, expected_edition_id=None,
        book_info=(slug, 0, title, len(chapter_markers)),
    )
    front_matter = _front_matter(source_text)
    reader_id = f"webbe-2020-{code.lower()}-research"
    corpus_id = f"webbe-2020-{code.lower()}"
    reader_title = f"{title} — English research reader (eBible.org WEBBE source module {code})"
    source_ids = ["SRC-WEBBE-EDITION", "SRC-WEBBE-RIGHTS", "SRC-WEBBE-FAQ", "SRC-WEBBE-PACKAGE"]
    # These temporary labels are replaced by stable IDs in build().
    parsed.pop("basis_language_tag", None)
    parsed.pop("translation_method", None)
    parsed.update({
        "reader_id": reader_id,
        "research_corpus_id": corpus_id,
        "canon_id": None,
        "candidate_canon_id": None,
        "title": reader_title,
        "display_name": f"{title} · English · eBible.org source module {code}",
        "language": "English",
        "language_tag": "en",
        "language_assignment_status": "provider_declared_in_OFFICIAL_EDITION_PAGE_AND_USFM",
        "script_code": "Latn",
        "text_origin": "published_translation",
        "translation_id": "webbe-2020-english",
        "translator": "The World English Bible revision team; the specific module does not name a translator. The FAQ identifies Michael Paul Johnson as senior editor and main translator for the WEB project.",
        "translation_basis_status": "unknown",
        "translation_basis_note": "The publisher describes the WEB family as based on the 1901 ASV, the Biblia Hebraica Stuttgartensia Old Testament, original ASV source-text choices, and Greek Majority Text New Testament readings; WEBBE is a British/International spelling edition of WEBU. The publisher also gives a separate English-source lineage for the Deuterocanon/Apocrypha. These are edition-family descriptions, not an ordered translation path for this exact digital module, so its individual translation basis remains unknown in this archive.",
        "edition": "World English Bible British Edition with Deuterocanon (WEBBE), 2020 stable text edition as identified by eBible.org; source module " + code + ".",
        "edition_scope": f"One of 81 scripture modules in the retained eBible.org WEBBE USFM package. The module title is {title!r}; source code {code}. {('DAG is separately labeled “Daniel (Greek)” and is kept separate from DAN.' if code == 'DAG' else 'Module boundaries follow the source ZIP, not an Ethiopian Orthodox book crosswalk.')} No Ethiopian Orthodox Tewahedo or Eritrean Orthodox canon mapping is assigned.",
        "rights_classification": "public_domain_claimed",
        "copyright_notice": "eBible.org states that the World English Bible British Edition is public domain and that “World English Bible” is a trademark; its notice asks that altered text or punctuation not be called by that name. The exact signed USFM source package is retained unchanged. This reader is an archive extraction with normalized USFM layout and is not presented as the official signed text or an endorsed edition.",
        "commercial_use": "The provider states that WEBBE may be used commercially and publicly dedicated to the public domain. This archive records that provider claim, not a universal legal determination. The reader is a normalized extraction; it should not be represented as the official signed WEBBE text.",
        "license_id": None,
        "license_url": None,
        "section_label": "Chapter",
        "unit_label": "source USFM verse labels",
        "verse_marker_count": parsed["unit_count"],
        "source_numbered_unit_count": parsed["unit_count"],
        "source_unnumbered_unit_count": 0,
        "source_pages": f"{PACKAGE.relative_to(ROOT).as_posix()}::{name}",
        "source_ids": source_ids,
        "front_matter": front_matter,
        "additional_notes": "The preface (FRT) and glossary (GLO) are separate non-scripture package members, retained in the source ZIP and described in its local capture manifest. DAN and DAG remain separate modules; no composite Daniel text is created.",
        "transcription_note": "Display extraction from the exact retained publisher USFM member. Words and source verse labels are preserved; USFM formatting/word-alignment codes are omitted, layout whitespace is normalized, and publisher-added words marked \\add are displayed in archival brackets. Consult the retained source USFM for original markup; this extraction is not independently proofread against print.",
        "editorial_signs_note": "Source footnotes, cross-references, and recognized structural headings/continuations are carried into reader data. Unrecognized USFM controls fail the builder rather than being silently discarded. The original USFM remains available unchanged in the source package.",
        "chapter_structure_status": "source_package_parsed_with_limits",
        "chapter_structure_note": "This source module has " + str(parsed["chapter_count"]) + " sequential USFM chapter divisions and " + str(parsed["unit_count"]) + " verse labels; " + str(parsed["note_count"]) + " notes and " + str(len(front_matter)) + " pre-chapter front-matter elements were extracted. Counts are from this source module only and do not establish print-edition or canon completeness.",
        "rights_status": "eBible.org states that WEBBE is public domain and specifies a trademark condition for the name. This is a provider claim; the co-distributed key's real-world identity was not independently authenticated. The source ZIP remains intact; this project uses a normalized display extraction and does not imply publisher endorsement.",
        "verification_status": "GnuPG reports a good signature for the ZIP's clear-signed checksum list from the bundled key claiming to be World English Bible editors, fingerprint " + SIGNER_FINGERPRINT + "; trust is undefined and key identity/signing authority were not independently authenticated. The builder verifies the pinned whole-ZIP SHA-256, ZIP CRC, exact coverage of ordinary ZIP members by the signed hash list, and each member hash. It also checks the module ID, contiguous chapter sequence, nonempty/unique verse labels, notes, and parsed structure. This verifies local extraction structure and package integrity relative to the bundled key only—not wording accuracy, print completeness, original-language fidelity, or Ethiopian/Eritrean canon identity.",
    })
    corpus = {
        "corpus_id": corpus_id,
        "title": reader_title,
        "reader_id": reader_id,
        "unit_count": parsed["unit_count"],
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "not_mapped",
        "candidate_canon_id": None,
        "canon_mapping_note": "No Ethiopian Orthodox Tewahedo or Eritrean Orthodox work/title crosswalk has been established for this provider-specific English module. Its presence in WEBBE's 81-module package is not evidence of membership in either canon.",
        "language_description": "English, as identified by eBible.org for WEBBE.",
        "script_description": "Latin script (Latn), observed in the retained USFM text.",
        "language_tag": "en",
        "script_code": "Latn",
        "unit_summary": f"{parsed['chapter_count']} consecutive source chapter markers; {parsed['unit_count']} numbered USFM verse labels; {parsed['note_count']} source notes; {sum(len(v.get('continuations', [])) for c in parsed['chapters'] for v in c['verses'])} unnumbered continuation segments. Counts describe extraction of source module {code} only.",
        "rights_classification": "public_domain_claimed",
        "rights_status": "eBible.org states WEBBE is public domain and that the edition name is a trademark; provider claim only, not a worldwide legal determination.",
        "review_status": "Pinned provider USFM source package, signature/hash-list status, code, module title, chapter sequence, label counts, notes, and retained original markup were checked locally. No independent textual collation, accuracy review, print-completeness review, EOTC/Eritrean crosswalk, or community review was performed.",
        "source_ids": source_ids,
        "text_origin": "published_translation",
        "language_tag": "en",
        "script_code": "Latn",
        "translation_id": "webbe-2020-english",
        "translator": parsed["translator"],
        "translation_basis_status": "unknown",
        "translation_basis_note": parsed["translation_basis_note"],
        "edition_statement": parsed["edition"],
    }
    return parsed, corpus, {
        "code": code,
        "title": title,
        "name": name,
        "chapter_count": parsed["chapter_count"],
        "unit_count": parsed["unit_count"],
    }


def build(existing_sources: list[dict] | None = None) -> tuple[list[dict], list[dict], list[dict], dict]:
    existing_sources = existing_sources or []
    package, members, inventory = _package_data()
    package_hash = sha256(package)
    limits = "Inspected " + REVIEWED_AT + ". eBible.org identifies the English, British/International WEBBE 2020 stable text edition, labels it public domain, and offers USFM. The stored package and its signed checksum list are retained locally. This is source-edition evidence, not EOTC/Eritrean canon evidence or independent translation-accuracy evidence."
    sources: list[dict] = []
    ids = {
        "edition": _upsert_source(existing_sources, sources, "eBible.org — WEBBE official edition and format page", EDITION_URL, "Official WEBBE edition metadata and USFM availability inspected; no Church-canon mapping asserted", limits),
        "rights": _upsert_source(existing_sources, sources, "eBible.org — WEBBE public-domain and trademark notice", COPYRIGHT_URL, "Provider rights statement inspected; public-domain claim is not an independent worldwide legal determination", "eBible.org states that WEBBE is public domain and that the name is trademarked. The provider asks that if actual text or punctuation is changed, the result not be called the World English Bible. The exact signed source package is preserved; the reader view is a normalized extraction."),
        "faq": _upsert_source(existing_sources, sources, "eBible.org — World English Bible FAQ: edition relationships, translation history, and deuterocanon scope", FAQ_URL, "Provider-published WEB/WEBU/WEBBE relationships and translation history inspected; per-module basis remains unverified", "The provider says WEBBE is WEBU with British/International spelling; describes the broader WEB revision as an ASV update with New Testament conformity to Greek Majority Text where significant differences occur; and says WEB Apocrypha/Deuterocanon comes from Revised Version 1894 or LXX2012 where needed. These are edition-family statements, not a verified path for each bundled module."),
        "basis": _upsert_source(existing_sources, sources, "WorldEnglish.Bible — World English Bible textual bases and edition relationships", PUBLISHER_BASIS_URL, "Publisher-stated textual bases for the WEB edition family and distinction between WEBBE and companion Deuterocanon; not a collation of each bundled digital module", "Inspected 2026-10-27. The publisher states that WEB is based on the American Standard Version (1901), Biblia Hebraica Stuttgartensia Old Testament, and a combination of original ASV source-text choices and the Greek Majority Text New Testament. It says WEBBE uses British spelling and LORD/GOD renderings. It separately states that the Deuterocanon/Apocrypha companion derives from the Revised Version Apocrypha and Brenton's English Septuagint translation. These are publisher descriptions of edition lineage, not per-module textual collation or independent accuracy findings."),
        "package": _upsert_source(existing_sources, sources, "eBible.org — retained signed WEBBE USFM source package", PACKAGE_URL, "Pinned 2026-10-22 signed package; checksum signature good for co-distributed key, whose identity remains unauthenticated", f"Package SHA-256 {package_hash}; {len(inventory)} ZIP members; 81 scripture modules, one preface, one glossary, and supporting files. GnuPG reports a good signature from the co-distributed key claiming World English Bible editors ({SIGNER_FINGERPRINT}), but trust is undefined and signing authority was not independently authenticated. All ordinary member hashes match the signed list."),
    }
    for source in [*existing_sources, *sources]:
        if source.get("source_id") in ids.values():
            source["local_metadata_url"] = CAPTURE_MANIFEST.relative_to(ROOT).as_posix()
        if source.get("source_id") == ids["package"]:
            source["local_source_package_url"] = PACKAGE.relative_to(ROOT).as_posix()
    source_ids = [ids["edition"], ids["rights"], ids["faq"], ids["basis"], ids["package"]]

    capture = _capture_manifest(package, inventory)
    write_text_atomically(CAPTURE_MANIFEST, json.dumps(capture, ensure_ascii=False, indent=2) + "\n")

    readers: list[dict] = []
    corpora: list[dict] = []
    module_inventory: list[dict] = []
    for item in inventory:
        if item["role"] != "scripture_module":
            continue
        code, name = item["source_book_code"], item["path"]
        reader, corpus, module = _parse_module(code, name, members[name], package_hash)
        reader["source_ids"] = source_ids
        corpus["source_ids"] = source_ids
        corpus["rights_status"] = reader["rights_status"]
        path = ROOT / "readers" / f"{reader['reader_id']}.json"
        write_text_atomically(path, json.dumps(reader, ensure_ascii=False, indent=2) + "\n")
        readers.append(reader)
        corpora.append(corpus)
        module_inventory.append({
            **module,
            "reader_id": reader["reader_id"],
            "research_corpus_id": corpus["corpus_id"],
            "chapter_count": reader["chapter_count"],
            "verse_label_count": reader["unit_count"],
            "member_sha256": item["sha256"],
        })
    if len(readers) != 81 or len(corpora) != len(readers):
        raise ValueError("WEBBE research reader generation did not create one package per scripture module.")
    for reader in readers:
        # Re-read every emitted package to verify stable serialization and exact counts.
        stored = json.loads((ROOT / "readers" / f"{reader['reader_id']}.json").read_text(encoding="utf-8"))
        if stored != reader or sum(len(chapter["verses"]) for chapter in stored["chapters"]) != stored["unit_count"]:
            raise ValueError(f"Generated reader package failed local verification: {reader['reader_id']}.")
    capture["reader_inventory"] = module_inventory
    capture["reader_inventory_summary"] = {
        "scripture_modules_parsed": len(module_inventory),
        "distinct_chapter_divisions": sum(item["chapter_count"] for item in module_inventory),
        "source_verse_labels": sum(item["verse_label_count"] for item in module_inventory),
        "church_canon_mappings_assigned": 0,
    }
    write_text_atomically(CAPTURE_MANIFEST, json.dumps(capture, ensure_ascii=False, indent=2) + "\n")
    return readers, corpora, sources, capture


if __name__ == "__main__":
    readers, corpora, sources, manifest = build()
    print(
        f"Built {len(readers)} WEBBE English research readers; "
        f"{manifest['reader_inventory_summary']['distinct_chapter_divisions']} source chapters; "
        f"{manifest['reader_inventory_summary']['source_verse_labels']} source verse labels; "
        "no Ethiopian/Eritrean canon mappings assigned."
    )
