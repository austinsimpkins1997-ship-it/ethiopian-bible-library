"""Build a source-backed Maale Bible reader from eBible.org's licensed USFM package.

The 66 extracted books stay research-only and are not crosswalked to the EOTC
81-entry list. Original USFM is retained so unrendered formatting remains
available for audit; the parser preserves verse labels, notes, headings,
continuations, and book introductory matter.
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

import build_brenton_octateuch as usfm
from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers" / "source" / "maale" / "mdyeth_usfm.zip"
OUTPUT = ROOT / "readers"
MANIFEST = ROOT / "research" / "maale-usfm-source-manifest.json"
SOURCE_NOTICE = ROOT / "readers" / "source" / "maale" / "SOURCE-NOTICE.txt"
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
DETAIL_URL = "https://ebible.org/Bible/details.php?id=mdyeth"
PACKAGE_URL = "https://ebible.org/Scriptures/mdyeth_usfm.zip"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
KEY_FINGERPRINT_URL = "https://mljohnson.org/gpg.htm"
KEY_FINGERPRINT = "54D714D76956DA6673DC1EEA5F62009D93505F26"
SOURCE_IDS = ["SRC-363", "SRC-364", "SRC-365"]
REVIEWED_AT = "2026-10-26"
COPYRIGHT = (
    "Copyright © 2008 The Word for the World International and The Bible Society of Ethiopia. "
    "Translation by The Word for the World; contributor: Bible Society of Ethiopia. "
    "Source: eBible.org Maale Bible (MDYTWF / mdyeth), using Ethiopic script. "
    "Text licensed CC BY-SA 4.0. This archive parsed USFM into reader JSON and preserves the original USFM package; "
    "Change made: USFM structure was converted to this reader JSON format, and image assets were omitted while their captions, alt text, "
    "and source filenames were retained as notes. The conversion does not imply publisher endorsement. Images and other media are excluded because their terms differ."
)

# USFM book identifiers are the publisher's identifiers; English labels are
# interface labels only and do not translate or normalize the Maale book titles.
BOOK_NAMES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers", "DEU": "Deuteronomy",
    "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth", "1SA": "1 Samuel", "2SA": "2 Samuel",
    "1KI": "1 Kings", "2KI": "2 Kings", "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra",
    "NEH": "Nehemiah", "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Songs", "ISA": "Isaiah", "JER": "Jeremiah",
    "LAM": "Lamentations", "EZK": "Ezekiel", "DAN": "Daniel", "HOS": "Hosea", "JOL": "Joel",
    "AMO": "Amos", "OBA": "Obadiah", "JON": "Jonah", "MIC": "Micah", "NAM": "Nahum",
    "HAB": "Habakkuk", "ZEP": "Zephaniah", "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
    "MAT": "Matthew", "MRK": "Mark", "LUK": "Luke", "JHN": "John", "ACT": "Acts", "ROM": "Romans",
    "1CO": "1 Corinthians", "2CO": "2 Corinthians", "GAL": "Galatians", "EPH": "Ephesians",
    "PHP": "Philippians", "COL": "Colossians", "1TH": "1 Thessalonians", "2TH": "2 Thessalonians",
    "1TI": "1 Timothy", "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon", "HEB": "Hebrews",
    "JAS": "James", "1PE": "1 Peter", "2PE": "2 Peter", "1JN": "1 John", "2JN": "2 John",
    "3JN": "3 John", "JUD": "Jude", "REV": "Revelation",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_checksum_signature(key_data: bytes, signed_data: bytes) -> dict:
    """Verify the publisher's signed checksum list with the included key and pinned fingerprint."""
    gpg = shutil.which("gpg")
    bash = None
    if not gpg and os.name == "nt":
        for program_files in (os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if program_files:
                candidate = Path(program_files) / "Git" / "bin" / "bash.exe"
                if candidate.is_file():
                    bash = str(candidate)
                    break
    if not gpg and not bash:
        raise RuntimeError("GnuPG is required to verify the retained Maale source package signature.")

    with tempfile.TemporaryDirectory(prefix=".maale-gpg-", dir=ROOT) as temporary:
        temporary_path = Path(temporary)
        home = temporary_path / "gnupg"
        home.mkdir()
        key_path = home / "keys.asc"
        signed_path = home / "signature.txt.asc"
        key_path.write_bytes(key_data)
        signed_path.write_bytes(signed_data)
        env = os.environ.copy()
        command = ["gpg", "--batch", "--no-autostart", "--import", '"$GNUPGHOME/keys.asc"']
        verify = ["gpg", "--batch", "--no-autostart", "--status-fd", "1", "--verify", '"$GNUPGHOME/signature.txt.asc"']
        if bash:
            env["GNUPGHOME"] = home.relative_to(ROOT).as_posix()
            import_command = "gpg --batch --no-autostart --import \"$GNUPGHOME/keys.asc\""
            verify_command = "gpg --batch --no-autostart --status-fd 1 --verify \"$GNUPGHOME/signature.txt.asc\""
            import_args = [bash, "-c", import_command]
            verify_args = [bash, "-c", verify_command]
        else:
            env["GNUPGHOME"] = str(home)
            import_args = [gpg, *command[1:-1], str(key_path)]
            verify_args = [gpg, *verify[:-1], str(signed_path)]
        imported = subprocess.run(import_args, cwd=ROOT, env=env, capture_output=True, text=True)
        checked = subprocess.run(verify_args, cwd=ROOT, env=env, capture_output=True, text=True)
        if checked.returncode:
            raise ValueError(f"Maale package checksum-list signature did not verify: {checked.stderr.strip()}")
        valid = [line.split() for line in checked.stdout.splitlines() if line.startswith("[GNUPG:] VALIDSIG ")]
        if not valid or valid[0][2].upper() != KEY_FINGERPRINT:
            actual = valid[0][2] if valid and len(valid[0]) > 2 else "no valid signing fingerprint"
            raise ValueError(f"Maale source signature used unexpected signing key {actual}; expected {KEY_FINGERPRINT}.")
    return {
        "valid": True,
        "signer_fingerprint": KEY_FINGERPRINT,
        "fingerprint_reference": KEY_FINGERPRINT_URL,
        "signature_hash_algorithm": "SHA-1 (legacy)",
        "signing_key_algorithm": "DSA-1024 (legacy)",
        "key_identity_limit": "The signature verifies against the public key included in the same source ZIP. Its fingerprint matches the maintainer's published page, but this does not independently establish identity, key custody, or signing authority.",
    }


def source_hashes(package: bytes) -> tuple[dict[str, bytes], dict[str, str], dict]:
    with zipfile.ZipFile(SOURCE) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Maale source ZIP failed its CRC check at {bad}.")
        members = {name: archive.read(name) for name in archive.namelist() if name.lower().endswith(".usfm")}
        signed_data = archive.read("signature.txt.asc")
        signed_text = signed_data.decode("utf-8", "replace")
        key_data = archive.read("keys.asc")
    signature = verify_checksum_signature(key_data, signed_data)
    declared = {
        match.group(2): match.group(1)
        for match in re.finditer(r"^([0-9a-f]{64})\s+(\S+)$", signed_text, re.M)
    }
    if len(members) != 66 or set(members) != {n for n in declared if n.lower().endswith(".usfm")}:
        raise ValueError("The Maale package no longer has the 66 expected, checksum-listed USFM members.")
    actual = {name: sha256(data) for name, data in members.items()}
    if any(declared[name] != actual[name] for name in members):
        raise ValueError("At least one Maale USFM member differs from the package's included SHA-256 list.")
    codes = {}
    for name, data in members.items():
        text = data.decode("utf-8-sig")
        match = re.search(r"^\\id\s+([A-Z0-9]{3})\s+-\s+(.+?)\s*$", text, re.M)
        if not match:
            raise ValueError(f"Missing USFM identity header in {name}.")
        code, source_title = match.groups()
        if code not in BOOK_NAMES or code in codes:
            raise ValueError(f"Unknown or duplicate Maale USFM book identifier {code!r} in {name}.")
        if "MAALE Full Bible" not in source_title:
            raise ValueError(f"{name} no longer identifies the expected Maale Bible source.")
        codes[code] = name
    if set(codes) != set(BOOK_NAMES):
        raise ValueError("Maale package book identifiers differ from the expected 66-book source inventory.")
    return members, actual, signature


def clean_note_body(raw: str, verse: str, chapter: int) -> dict:
    """Retain note wording and markers; describe excluded figure assets without fetching them."""
    reference = re.search(r"\\(?:fr|xo)\s+([^\\]+)", raw)
    ref_text = reference.group(1).strip() if reference else None
    figure_notes = []
    def figure(match: re.Match) -> str:
        body = match.group(1).strip()
        parts = body.split("|", 1)
        caption = parts[0].strip()
        attributes = parts[1] if len(parts) > 1 else ""
        alt = re.search(r'alt="([^"]*)"', attributes)
        src = re.search(r'src="([^"]*)"', attributes)
        figure_notes.append("Source illustration omitted (image reuse terms not established). "
                            f"Caption: {caption or 'not recorded'}. "
                            f"Alt text: {alt.group(1) if alt else 'not recorded'}. "
                            f"Source asset: {src.group(1) if src else 'not identified'}.")
        return " "
    raw = re.sub(r"\\fig\s+(.*?)\\fig\*", figure, raw, flags=re.S)
    labels = [m.group(1) for m in re.finditer(r"\\([A-Za-z][A-Za-z0-9]*)\b", raw)]
    content = re.sub(r"\\(?:fr|xo)\s+[^\\]+", " ", raw)
    # The enclosing \f / \x marker remains after extracting a note from a
    # verse. It is represented by note_type below; remove only that wrapper,
    # while retaining all note body wording and its typed fields.
    content = re.sub(r"^\s*\\(?:f|x)\b(?:\s+\+)?\s*", " ", content)
    content = re.sub(r"\\(?:ft|fqa|fq|fk|xt)\s*", " ", content)
    content = re.sub(r"\\[+*]\s*", " ", content)
    text = usfm.clean_usfm(content)
    if figure_notes:
        text = (text + " " if text else "") + " ".join(figure_notes)
    if ref_text and ref_text != f"{chapter}:{verse}":
        text = f"Source note reference {ref_text}. {text}" if text else f"Source note reference {ref_text}."
    if not text:
        text = None
    note_kind = "cross_reference" if "x" in labels else "translator_note"
    if figure_notes:
        note_kind = "source_asset_omitted"
    return {
        "verse": verse,
        "marker": "Cross-reference" if note_kind == "cross_reference" else "Translator/editor note",
        "text": text,
        "note_type": note_kind,
        "source_reference": ref_text,
    }


def parse_book(raw: bytes, member_name: str) -> dict:
    text = raw.decode("utf-8-sig")
    code_match = re.search(r"^\\id[ \t]+([A-Z0-9]{3})(?:[ \t]+(.+?))?[ \t]*$", text, re.M)
    if not code_match:
        raise ValueError(f"No book identity marker in {member_name}.")
    code = code_match.group(1)
    chapter_count = len(re.findall(r"^\\c\s+\d+\s*$", text, re.M))
    if chapter_count < 1:
        raise ValueError(f"No chapter markers in {member_name}.")
    chapters: list[dict] = []
    front_matter: list[dict] = []
    book_metadata: list[dict] = []
    current: dict | None = None
    pending_markers: list[str] = []
    pending_headings: list[str] = []
    marker_counts: dict[str, int] = {}
    unit_labels: list[tuple[int, str]] = []
    table_row_active = False

    def count(marker: str) -> None:
        marker_counts[marker] = marker_counts.get(marker, 0) + 1

    def retain_front(marker: str, body: str) -> None:
        notes: list[dict] = []
        if body.strip():
            body, notes = extract_notes(body, "front-matter", 0)
            body, figure_notes = extract_figures(body, "front-matter")
            notes.extend(figure_notes)
            body = usfm.clean_usfm(body) if body.strip() else ""
        if body:
            item = {"marker": marker, "text": body}
            if notes:
                item["notes"] = notes
            front_matter.append(item)
        elif notes:
            front_matter.append({"marker": marker, "text": None, "notes": notes})

    def extract_notes(raw: str, verse_label: str, chapter_number: int) -> tuple[str, list[dict]]:
        notes = []
        def pull_note(match: re.Match) -> str:
            notes.append(clean_note_body(match.group(2), verse_label, chapter_number))
            return " "
        return re.sub(r"\\([fx])\b(.*?)\\\1\*", pull_note, raw, flags=re.S), notes

    def extract_figures(raw: str, verse_label: str) -> tuple[str, list[dict]]:
        notes = []
        def omit_figure(match: re.Match) -> str:
            body = match.group(1).strip()
            caption, _, attributes = body.partition("|")
            alt = re.search(r'alt="([^"]*)"', attributes)
            src = re.search(r'src="([^"]*)"', attributes)
            description = (
                "Source illustration omitted (image reuse terms not established). "
                f"Caption: {caption.strip() or 'not recorded'}. "
                f"Alt text: {alt.group(1) if alt else 'not recorded'}. "
                f"Source asset: {src.group(1) if src else 'not identified'}."
            )
            notes.append({"verse": verse_label, "marker": "Source illustration omitted", "text": description,
                          "note_type": "source_asset_omitted", "source_reference": None})
            return " "
        return re.sub(r"\\fig\s+(.*?)\\fig\*", omit_figure, raw), notes

    def close_chapter() -> None:
        nonlocal current, pending_markers, pending_headings
        if current is None:
            return
        if pending_headings or pending_markers:
            current.setdefault("source_trailing_elements", []).extend(
                [{"marker": "heading", "text": item} for item in pending_headings]
                + [{"marker": marker, "text": None} for marker in pending_markers]
            )
        if not current["verses"]:
            raise ValueError(f"Empty chapter {current['chapter']} in {member_name}.")
        chapters.append(current)
        current = None
        pending_markers = []
        pending_headings = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        marker_match = re.match(r"^\\([A-Za-z][A-Za-z0-9]*)\b\s*(.*)$", line)
        if not marker_match:
            if current is not None and current["verses"]:
                current["verses"][-1].setdefault("continuations", []).append(
                    {"source_marker": "unmarked line", "text": usfm.clean_usfm(line.strip())}
                )
            else:
                retain_front("unmarked line", line.strip())
            continue
        marker, body = marker_match.groups()
        count(marker)
        if table_row_active and marker != "tr" and marker != "v" and not re.fullmatch(r"t(?:c|cr|h|hr)\d+", marker):
            table_row_active = False
        if marker == "c":
            close_chapter()
            label = body.strip()
            if not label.isdigit():
                raise ValueError(f"Invalid chapter label at {member_name}:{line_number}.")
            current = {"chapter": int(label), "verses": [], "notes": []}
            continue
        if marker == "v":
            if current is None:
                raise ValueError(f"Verse before chapter marker at {member_name}:{line_number}.")
            # Preserve publisher compound labels (for example 9-10) exactly;
            # never expand them into two invented verse records.
            match = re.match(r"^(\d+[a-z]?(?:-\d+[a-z]?)?)\s*(.*)$", body)
            if not match:
                raise ValueError(f"Invalid verse label at {member_name}:{line_number}.")
            label, verse_body = match.groups()
            verse_body, notes = extract_notes(verse_body, label, current["chapter"])
            verse_body, figure_notes = extract_figures(verse_body, label)
            notes.extend(figure_notes)
            verse_text = usfm.clean_usfm(verse_body)
            verse = {"number": label, "text": verse_text}
            if table_row_active and current.get("source_tables"):
                current["source_tables"][-1]["rows"][-1].append(
                    {"marker": "v", "number": label, "text": verse_text}
                )
            if not verse_text:
                if notes:
                    verse["source_text_state"] = "marker_only"
                else:
                    raise ValueError(f"Empty verse without note at {member_name}:{line_number} ({label}).")
            if pending_markers:
                verse["source_markers_before"] = list(pending_markers)
                pending_markers.clear()
            if pending_headings:
                verse["source_headings_before"] = list(pending_headings)
                pending_headings.clear()
            current["verses"].append(verse)
            current["notes"].extend(notes)
            unit_labels.append((current["chapter"], label))
            continue

        if marker in {"id", "h", "toc1", "toc2", "toc3", "mt1", "mt2", "mt3"}:
            if marker != "id" and body.strip():
                book_metadata.append({"marker": marker, "text": usfm.clean_usfm(body)})
            continue
        if marker in {"imt1", "ip", "ipi", "iot", "io1", "io2", "ili", "ili1", "is2", "is1", "is3", "imt2", "imt3", "ie"}:
            retain_front(marker, body)
            continue
        if marker in {"s1", "s2", "s3", "r", "sp", "ms1", "ms2", "mr"}:
            heading = ""
            if current is None:
                retain_front(marker, body)
            elif current["verses"]:
                body, notes = extract_notes(body, "section-heading", current["chapter"])
                body, figure_notes = extract_figures(body, "section-heading")
                notes.extend(figure_notes)
                current["notes"].extend(notes)
                heading = usfm.clean_usfm(body) if body.strip() else ""
                pending_markers.append(marker)
                if heading:
                    pending_headings.append(heading)
            else:
                body, notes = extract_notes(body, "chapter-heading", current["chapter"])
                body, figure_notes = extract_figures(body, "chapter-heading")
                notes.extend(figure_notes)
                current.setdefault("notes", []).extend(notes)
                heading = usfm.clean_usfm(body) if body.strip() else ""
                if heading:
                    current.setdefault("heading", []).append(heading)
            continue
        if marker == "cl":
            if current is not None:
                current["source_chapter_label"] = usfm.clean_usfm(body) if body.strip() else ""
            elif body.strip():
                retain_front(marker, body)
            continue
        if marker == "tr":
            if current is None:
                retain_front(marker, body)
            else:
                tables = current.setdefault("source_tables", [])
                if not table_row_active or not tables:
                    tables.append({"rows": []})
                tables[-1]["rows"].append([])
                table_row_active = True
            continue
        if re.fullmatch(r"t(?:c|cr|h|hr)\d+", marker):
            if current is None or not current.get("source_tables"):
                raise ValueError(f"Table cell without a preceding source table row in {member_name}:{line_number}.")
            body, notes = extract_notes(body, "table-cell", current["chapter"])
            body, figure_notes = extract_figures(body, "table-cell")
            current["notes"].extend(notes + figure_notes)
            current["source_tables"][-1]["rows"][-1].append({
                "marker": marker,
                "text": usfm.clean_usfm(body) if body.strip() else "",
            })
            table_row_active = True
            continue
        if marker in {
            "d", "p", "m", "q1", "q2", "q3", "qm1", "qm2", "b", "nb", "pm", "pmo", "pmc", "mi", "pc",
            "pi1", "pr", "po", "qr", "qa", "qc", "lh", "lf", "li1", "li2", "li3", "li4",
        }:
            if body.strip():
                if current is None:
                    retain_front(marker, body)
                    continue
                if current is not None and current["verses"]:
                    verse_label = current["verses"][-1]["number"]
                    body, notes = extract_notes(body, verse_label, current["chapter"])
                    body, figure_notes = extract_figures(body, verse_label)
                    notes.extend(figure_notes)
                    current["notes"].extend(notes)
                elif current is not None:
                    body, notes = extract_notes(body, "chapter-heading", current["chapter"])
                    body, figure_notes = extract_figures(body, "chapter-heading")
                    notes.extend(figure_notes)
                    current.setdefault("notes", []).extend(notes)
                content = usfm.clean_usfm(body)
                if not current["verses"]:
                    current.setdefault("heading", []).append(content)
                else:
                    current["verses"][-1].setdefault("continuations", []).append(
                        {"source_marker": marker, "text": content}
                    )
            else:
                pending_markers.append(marker)
            continue
        # Inline USFM containers outside verse or note fields would otherwise be lost.
        raise ValueError(f"Unreviewed USFM structural marker \\{marker} at {member_name}:{line_number}.")

    close_chapter()
    observed_chapters = [chapter["chapter"] for chapter in chapters]
    if observed_chapters != list(range(1, chapter_count + 1)):
        raise ValueError(f"Nonconsecutive chapter sequence in {member_name}: {observed_chapters!r}.")
    if len(unit_labels) != len(set(unit_labels)):
        raise ValueError(f"Duplicate chapter/verse labels in {member_name}; inspect without normalizing.")
    return {
        "code": code,
        "source_title": code_match.group(2) or "No title text in USFM identity marker",
        "chapter_count": len(chapters),
        "unit_count": len(unit_labels),
        "chapters": chapters,
        "front_matter": front_matter,
        "book_metadata": book_metadata,
        "marker_counts": dict(sorted(marker_counts.items())),
        "unit_labels": unit_labels,
    }


def build() -> tuple[list[dict], list[dict], list[dict], dict]:
    package = SOURCE.read_bytes()
    package_hash = sha256(package)
    members, member_hashes, signature = source_hashes(package)
    readers = []
    corpora = []
    inventory = []
    for code in sorted(BOOK_NAMES, key=lambda item: list(BOOK_NAMES).index(item)):
        name = next(name for name in members if re.search(rf"-{code}mdyeth\.usfm$", name))
        raw = members[name]
        parsed = parse_book(raw, name)
        if parsed["code"] != code:
            raise ValueError(f"USFM file name and book code disagree: {name}.")
        reader_id = f"maale-{code.lower()}-research"
        corpus_id = f"maale-mdytwf-2008-{code.lower()}"
        english_title = BOOK_NAMES[code]
        title = f"{english_title} — Maale Bible (MDYTWF / mdyeth, 2008)"
        scope = (
            "This is one of 66 USFM book members in eBible.org's Maale Bible (MDYTWF / mdyeth) package. "
            "The publisher describes the work as a Maale Full Bible; this package inventory contains the conventional 39 OT and 27 NT books, "
            "not the EOTC 81-entry canon. No EOTC or Eritrean Orthodox crosswalk is assigned. Counts describe this digital member only."
        )
        status = (
            f"The locally retained USFM source member {name} has SHA-256 {member_hashes[name]}; its digest matches the SHA-256 list "
            f"whose OpenPGP signature verifies against included key fingerprint {signature['signer_fingerprint']} "
            f"({signature['signing_key_algorithm']}/{signature['signature_hash_algorithm']}). The fingerprint matches the "
            f"maintainer's published page ({KEY_FINGERPRINT_URL}); identity and key custody are not independently established. "
            "Automated parsing retained the ordered chapter labels, all verse labels, "
            "available footnotes/cross-references, visible section headings and source structure markers, and recorded pre-chapter matter. "
            "USFM figure assets are excluded because their terms are separate; captions, alt text and source filenames are retained as notes. "
            "These checks establish signed-checksum consistency and local source-package structure only, "
            "not translation accuracy, completeness against print, local community review, or canon identity."
        )
        reader = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "canon_id": None,
            "title": title,
            "display_name": f"{english_title} · Maale · eBible.org MDYTWF",
            "text_origin": "published_translation",
            "translation_id": "maale-mdytwf-2008",
            "language": "Maale (Male)",
            "language_tag": "mdy",
            "language_assignment_status": "publisher_declared_in_source_package",
            "script_code": "Ethi",
            "translator": "The Word for the World",
            "contributor": "Bible Society of Ethiopia",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The inspected eBible.org edition notice identifies translator and contributor but does not identify the source language or any relay-language path; no basis is inferred.",
            "edition": "The Holy Bible in the Maale language of Ethiopia, using Ethiopic script; copyright © 2008; digital USFM source files dated 2025-05-13.",
            "edition_scope": scope,
            "rights_classification": "open_license",
            "license_id": "CC-BY-SA-4.0",
            "license_url": LICENSE_URL,
            "copyright_notice": COPYRIGHT,
            "commercial_use": "The provider's CC BY-SA 4.0 terms allow commercial reuse subject to attribution, indication of changes, and ShareAlike for adaptations. Images and media have separate terms and are not bundled.",
            "unit_label": "USFM verse labels observed",
            "unit_count": parsed["unit_count"],
            "verse_marker_count": parsed["unit_count"],
            "chapter_count": parsed["chapter_count"],
            "section_label": "Chapter",
            "chapter_structure_note": (
                f"This selected source member contains {parsed['chapter_count']} consecutive chapter markers, "
                f"{parsed['unit_count']} distinct chapter/verse labels, {sum(len(c['notes']) for c in parsed['chapters'])} notes, "
                f"and USFM structural marker counts {parsed['marker_counts']}. Publisher-supplied labels and structural irregularities are retained; "
                "counts do not establish completeness against a printed edition or any community's canon."
            ),
            "chapter_structure_status": "source_package_parsed_with_limits",
            "source_numbered_unit_count": parsed["unit_count"],
            "source_unnumbered_unit_count": sum(len(v.get("continuations", [])) for c in parsed["chapters"] for v in c["verses"]),
            "source_pages": f"readers/source/maale/mdyeth_usfm.zip::{name}",
            "source_package_sha256": package_hash,
            "source_snapshot_sha256": member_hashes[name],
            "source_ids": SOURCE_IDS,
            "rights_status": COPYRIGHT,
            "verification_status": status,
            "transcription_note": "Machine-readable display extraction from the publisher's source USFM; see the retained original USFM member for unrendered formatting and structural details. Wording has not been independently proofread or collated.",
            "editorial_signs_note": "USFM verse labels, footnotes, cross-references, paragraph/poetry/break markers, and section headings are preserved in reader structure. Figure images are not included; their caption, alt text and source filename are noted under the associated verse when present.",
            "front_matter": parsed["front_matter"],
            "source_book_metadata": parsed["book_metadata"],
            "chapters": parsed["chapters"],
        }
        reader_path = OUTPUT / f"{reader_id}.json"
        write_text_atomically(reader_path, json.dumps(reader, ensure_ascii=False, indent=2) + "\n", newline="\n")
        readers.append(reader)
        corpus = {
            "corpus_id": corpus_id,
            "title": title,
            "reader_id": reader_id,
            "unit_count": parsed["unit_count"],
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped",
            "candidate_canon_id": None,
            "canon_mapping_note": "No Ethiopian Orthodox Tewahedo or Eritrean Orthodox canon crosswalk is assigned. The source package supplies 66 conventional book members; the title 'Full Bible' does not establish equivalence to the EOTC or Eritrean Orthodox 81-entry lists.",
            "language_description": "Maale (Male), publisher-declared language tag mdy.",
            "script_description": "Ethiopic script (Ethi), declared by the source edition record.",
            "unit_summary": f"{parsed['unit_count']} distinct source chapter/verse labels in {parsed['chapter_count']} consecutive USFM chapter divisions; package count only.",
            "rights_classification": "open_license",
            "rights_status": COPYRIGHT,
            "license_id": "CC-BY-SA-4.0",
            "license_url": LICENSE_URL,
            "review_status": status,
            "source_ids": SOURCE_IDS,
            "text_origin": "published_translation",
            "language_tag": "mdy",
            "script_code": "Ethi",
            "translation_id": "maale-mdytwf-2008",
            "translator": "The Word for the World",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The provider notice does not identify the source language or a relay path.",
            "edition_statement": reader["edition"],
        }
        corpora.append(corpus)
        inventory.append({"usfm_id": code, "path": name, "title": english_title, "source_title": parsed["source_title"],
                          "byte_length": len(raw), "sha256": member_hashes[name], "chapter_count": parsed["chapter_count"],
                          "unit_count": parsed["unit_count"], "front_matter_item_count": len(parsed["front_matter"]),
                          "marker_counts": parsed["marker_counts"]})

    source_manifest = {
        "source_id": SOURCE_IDS[1],
        "source_url": PACKAGE_URL,
        "retrieved_at": REVIEWED_AT,
        "archive_sha256": package_hash,
        "archive_byte_length": len(package),
        "signature": signature,
        "member_count": len(members),
        "usfm_book_count": len(inventory),
        "usfm_members": inventory,
        "verification": "ZIP CRC checked; GnuPG verified the clear-signed SHA-256 list against the public key bundled in the ZIP; the key fingerprint matches the maintainer's published fingerprint page; every selected .usfm member matches the signed SHA-256 list.",
        "limits": "The signature uses legacy DSA-1024 and SHA-1. The bundled-key signature and external fingerprint comparison support tamper-evidence but do not independently establish identity, key custody, or authority. The provider's edition notice states Maale Full Bible; the 66-member inventory is not an EOTC 81-book crosswalk, print-completeness audit, community review, or translation-accuracy check."
    }
    write_text_atomically(MANIFEST, json.dumps(source_manifest, ensure_ascii=False, indent=2) + "\n", newline="\n")
    notice = (
        "Maale Bible (MDYTWF / mdyeth) source notice\n"
        "\n"
        "Copyright © 2008 The Word for the World International and The Bible Society of Ethiopia.\n"
        "Translation by The Word for the World; contributor: Bible Society of Ethiopia.\n"
        f"Source edition record: {DETAIL_URL}\n"
        f"Original USFM distribution: {PACKAGE_URL}\n"
        "License stated by the source: Creative Commons Attribution-ShareAlike 4.0 International\n"
        f"License: {LICENSE_URL}\n"
        "Changes in this archive: publisher USFM was parsed into reader JSON; source verse labels, headings, notes, front matter, and identified structure were retained; image files were omitted while captions, alt text, and asset names were recorded as notes. The publisher has not endorsed these changes.\n"
        "The provider says included pictures have separate terms and may be used only with the associated Scriptures and documents; no picture assets are included here.\n"
        f"The original source ZIP is retained beside this notice. GnuPG verified its clear-signed SHA-256 list against included key fingerprint {KEY_FINGERPRINT}; the fingerprint matches the maintainer's published GPG page ({KEY_FINGERPRINT_URL}). The signature uses legacy DSA-1024/SHA-1 and the key identity/custody is not independently established. Translation accuracy, print completeness, and EOTC/Eritrean canon equivalence have not been established.\n"
        "Rights and edition distinction: the current eBible.org mdyeth edition page, last updated 2025-05-13, links the retained USFM package and states CC BY-SA 4.0. A third-party mirror of an older copyright page, generated 2024-02-21 from source files dated 2023-04-14, displays CC BY-ND 4.0; this dated discrepancy is recorded as SRC-372 and is not silently merged with the directly linked current package notice. The separate Digital Bible Society product MDYBSE is recorded as SRC-373; its RESERVED metadata is not treated as a license statement for MDYTWF / mdyeth. No legal conclusion about license history or retroactive effect is asserted.\n"
    )
    write_text_atomically(SOURCE_NOTICE, notice, newline="\n")
    sources = [
        {
            "source_id": SOURCE_IDS[0],
            "source_name": "eBible.org — Maale Bible (MDYTWF / mdyeth) edition and rights record",
            "url": DETAIL_URL,
            "inspection_and_limitations": (
                "Inspected 2026-10-26; the live page states last updated 2025-05-13 and links directly to the retained mdyeth USFM package. The provider identifies the language as Maale (Male), tag mdy, title as Maale Bible (Ethiopic script), "
                "translation by The Word for the World, contributor Bible Society of Ethiopia, and copyright © 2008. It calls this a “Maale Full Bible” "
                "and states CC BY-SA 4.0 terms for sharing and adaptation with attribution, change indication, and ShareAlike. The provider separately says "
                "included pictures are licensed only for use with the Scriptures and related documents; those media are excluded from this package. This metadata "
                "does not verify printed-edition completeness, local review, translation accuracy, or equivalence to EOTC/Eritrean Orthodox canon lists. A dated CC BY-ND notice on a third-party mirror and separate MDYBSE catalogue metadata are recorded in SRC-372 and SRC-373; neither is silently substituted for the current MDYTWF page."
            ),
            "archive_status": "Edition metadata and source-stated license inspected; no canon crosswalk or accuracy certification."
        },
        {
            "source_id": SOURCE_IDS[1],
            "source_name": "eBible.org — Maale (mdyeth) publisher USFM package",
            "url": PACKAGE_URL,
            "inspection_and_limitations": (
                f"Retrieved 2026-10-26 and stored locally at readers/source/maale/mdyeth_usfm.zip (SHA-256 {package_hash}; {len(package)} bytes). "
                f"The ZIP contains {len(members)} .usfm book members. GnuPG verified the clear-signed checksum list against the package-included key "
                f"({signature['signing_key_algorithm']}/{signature['signature_hash_algorithm']}, fingerprint {signature['signer_fingerprint']}); the fingerprint "
                f"matches the maintainer's published key page ({KEY_FINGERPRINT_URL}). The signature uses legacy algorithms and key identity/custody are not "
                f"independently established. All {len(members)} member hashes match the signed list and ZIP CRC passed. Automated extraction checked chapter order and source labels; "
                "the inventory does not prove completeness against a print edition, independent textual accuracy, or church-canon mapping."
            ),
            "archive_status": "Original publisher USFM package retained locally; signed checksum list verified with included key and maintainer-page fingerprint cross-check; legacy algorithm and key identity limits recorded."
        },
        {
            "source_id": SOURCE_IDS[2],
            "source_name": "Michael Paul Johnson — GPG key fingerprint page for World English Bible editors",
            "url": KEY_FINGERPRINT_URL,
            "inspection_and_limitations": (
                f"Inspected 2026-10-26. The page lists the World English Bible editors key fingerprint {KEY_FINGERPRINT}, which matches the signing key "
                "reported by GnuPG when verifying the clear-signed checksum list embedded in the eBible.org Maale USFM package. This is a fingerprint comparison "
                "to the key maintainer's own published page, not a certificate authority, independent identity proof, or cryptographic audit of the DSA-1024/SHA-1 algorithms."
            ),
            "archive_status": "Key-fingerprint cross-reference only; signer identity, custody, and authority are not independently certified."
        },
        {
            "source_id": "SRC-372",
            "source_name": "Divine Revelations mirror — older Maale (mdyeth) copyright page",
            "url": "https://divinerevelations.info/documents/bible/All_HTML/Maale_Bible_Ethiopic_script/copyright.htm",
            "inspection_and_limitations": (
                "Inspected 2026-10-26. This third-party-hosted page repeats the Maale Bible title, 2008 copyright holders, translator and contributor stated on the eBible.org edition page, but gives a different license label: CC BY-ND 4.0. Its footer says Haiola generated the HTML through eBible.org on 2024-02-21 from source files dated 2023-04-14. This is evidence of a dated older notice, not proof that CC BY-ND terms govern the separately retained mdyeth_usfm.zip package, which the current eBible.org mdyeth page directly links and labels CC BY-SA 4.0. The cause or legal effect of the difference is not established; no legal conclusion is asserted."
            ),
            "archive_status": "Dated third-party mirror notice preserved as a rights-history discrepancy; not treated as controlling evidence for the current publisher-linked USFM package."
        },
        {
            "source_id": "SRC-373",
            "source_name": "Digital Bible Society ARC — separate Maale Bible product record (MDYBSE)",
            "url": "https://arc.dbs.org/data/scripture/MDYBSE/",
            "inspection_and_limitations": (
                "Inspected 2026-10-26. The Digital Bible Society record uses product ID MDYBSE, identifies Male (mdy), Ethiopic (Geʽez) script, describes a full Protestant-canon Bible published in 2008, names Bible Society of Ethiopia as publisher and The Word for the World International plus Bible Society of Ethiopia as translation agencies, and displays license status RESERVED. It is a separately identified product record, not the eBible.org MDYTWF / mdyeth record (SRC-363) or proof of the retained USFM package's textual identity, license, Orthodox canon scope, or accuracy. No text was retrieved or copied."
            ),
            "archive_status": "Separate bibliographic/product metadata only; license marked RESERVED; not crosswalked to MDYTWF / mdyeth or counted as reader coverage."
        },
        {
            "source_id": "SRC-374",
            "source_name": "The Word for the World Training — Tamene Lale Gego staff biography",
            "url": "https://training.twftw.org/our-faculty/",
            "inspection_and_limitations": (
                "Inspected 2026-10-26. The agency's team page identifies Tamene Lale Gego as its Ethiopia Scripture and Evangelism Engagement Director and says he translated the complete Bible into his mother tongue Maale. This is agency-published evidence for a named Maale Bible translator. The page does not date the translation, name the MDYTWF / mdyeth code, identify the 2008 edition or its team role, or state a source language or relay path; this archive therefore does not add his name to that edition's translator field without a direct edition link."
            ),
            "archive_status": "Agency biography names a Maale Bible translator; exact relationship to the 2008 MDYTWF / mdyeth edition remains unverified."
        }
    ]
    return readers, corpora, sources, source_manifest


if __name__ == "__main__":
    readers, corpora, _, manifest = build()
    print(f"Built {len(readers)} Maale research readers; {sum(r['unit_count'] for r in readers)} USFM labels; archive {manifest['archive_sha256']}.")
