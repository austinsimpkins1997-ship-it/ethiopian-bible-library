"""Build separate Brenton English Septuagint research readers.

The source package is retained locally. These readers preserve USFM structure;
provisional book-title candidates aid discovery but never create EOTC canon-linked
coverage or imply agreement with a Geʽez witness.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import build_brenton_octateuch as brenton
from coverage_summary import build_coverage_statement

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "translation-registry.json"
MANIFEST_PATH = brenton.MANIFEST
PACKAGE_PATH = brenton.PACKAGE
READER_PREFIX = "brenton-lxx-"
READER_SUFFIX = "-research.json"
RESEARCH_CODES = {
    "1SA", "2SA", "1CH", "2CH", "EZR", "ECC", "SNG", "JER", "EZK",
    "1KI", "2KI", "PRO", "LAM", "HOS", "JOL", "AMO", "OBA", "JON", "MIC", "NAM", "HAB", "ZEP",
    "HAG", "ZEC", "MAL", "JDT", "ESG", "WIS", "BAR", "LJE", "SUS",
    "BEL", "1MA", "2MA", "1ES", "MAN", "3MA", "4MA", "DAG",
}
ALREADY_REPRESENTED = {"GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "JOB", "PSA", "TOB", "SIR"}
CANDIDATE_CANON_LINKS = {
    "1SA": (
        "eotc-ot-09",
        "The Church list groups ‘I and II Samuel’ (SRC-029). This Brenton member is titled ‘Kings I’ and carries USFM code 1SA (SRC-038, SRC-142, SRC-384); the code reference identifies 1SA as 1 Samuel and notes ‘1 Kings/Kingdoms’ as an Orthodox naming variant. "
        "This is a provisional link to one component of the grouped entry only. It does not establish EOTC edition identity, textual agreement, or coverage of the whole grouped entry. It remains outside canon-linked coverage.",
    ),
    "2SA": (
        "eotc-ot-09",
        "The Church list groups ‘I and II Samuel’ (SRC-029). This Brenton member is titled ‘Kings II’ and carries USFM code 2SA (SRC-038, SRC-142, SRC-384); the code reference identifies 2SA as 2 Samuel and notes ‘2 Kings/Kingdoms’ as an Orthodox naming variant. "
        "This is a provisional link to one component of the grouped entry only. It does not establish EOTC edition identity, textual agreement, or coverage of the whole grouped entry. It remains outside canon-linked coverage.",
    ),
    "1KI": (
        "eotc-ot-10",
        "The Church list groups ‘I and II Kings’ (SRC-029). This Brenton member is titled ‘Kings III’ and carries USFM code 1KI (SRC-038, SRC-142, SRC-384); the code reference identifies 1KI as 1 Kings and notes ‘3 Kings/Kingdoms’ as an Orthodox naming variant. "
        "This is a provisional link to one component of the grouped entry only. It does not establish EOTC edition identity, textual agreement, or coverage of the whole grouped entry. It remains outside canon-linked coverage.",
    ),
    "2KI": (
        "eotc-ot-10",
        "The Church list groups ‘I and II Kings’ (SRC-029). This Brenton member is titled ‘Kings IV’ and carries USFM code 2KI (SRC-038, SRC-142, SRC-384); the code reference identifies 2KI as 2 Kings and notes ‘4 Kings/Kingdoms’ as an Orthodox naming variant. "
        "This is a provisional link to one component of the grouped entry only. It does not establish EOTC edition identity, textual agreement, or coverage of the whole grouped entry. It remains outside canon-linked coverage.",
    ),
    "EZR": (
        "eotc-ot-15",
        "The English Church list groups ‘Ezra and Nehemia’ (SRC-029); this Brenton member is titled ‘Ezra and Nehemiah’ (SRC-038, SRC-142). "
        "The close title and grouping support a research-only candidate link, but do not establish agreement in numbering, contents, chapter divisions, "
        "or identity with a Geʽez witness or current Ethiopian Orthodox edition. This reader remains outside canon-linked coverage.",
    ),
    "PRO": (
        "eotc-ot-24",
        "The English Church list names ‘Proverbs’ (SRC-029), and the Brenton member is titled ‘Proverbs’ (SRC-038, SRC-142). "
        "The matching title supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "ECC": (
        "eotc-ot-27",
        "The English Church list names ‘Ecclesiastes’ (SRC-029), and the Brenton member is titled ‘Ecclesiastes’ (SRC-038, SRC-142). "
        "The matching title supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "SNG": (
        "eotc-ot-28",
        "The English Church list names ‘Song of Songs’ (SRC-029); this Brenton member is titled ‘The Song of Solomon’ (SRC-038, SRC-142). "
        "The related title supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "JER": (
        "eotc-ot-30",
        "The English Church list names ‘Jeremiah’ (SRC-029); this Brenton member is titled ‘Jeremias’ (SRC-038, SRC-142). "
        "The title form supports a research-only candidate link; it does not establish agreement in text, order, extent, or boundaries with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "EZK": (
        "eotc-ot-31",
        "The English Church list names ‘Ezekiel’ (SRC-029); this Brenton member is titled ‘Jezekiel’ (SRC-038, SRC-142). "
        "The title form supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "HOS": (
        "eotc-ot-33",
        "The English Church list names ‘Hosea’ (SRC-029); this Brenton member is titled ‘Osee’ (SRC-038, SRC-142). "
        "The title form supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "JOL": (
        "eotc-ot-36",
        "The English Church list names ‘Joel’ (SRC-029), and the Brenton member is titled ‘Joel’ (SRC-038, SRC-142). "
        "The matching title supports a separate research-reader link; the Brenton text is a Greek-basis English witness, not a translation from Geʽez, "
        "and is not established as an Ethiopian Orthodox edition. It remains outside canon-linked coverage.",
    ),
    "AMO": (
        "eotc-ot-34",
        "The English Church list names ‘Amos’ (SRC-029), and the Brenton member is titled ‘Amos’ (SRC-038, SRC-142). "
        "The matching title supports a separate research-reader link; the Brenton text is a Greek-basis English witness, not a translation from Geʽez, "
        "and is not established as an Ethiopian Orthodox edition. It remains outside canon-linked coverage.",
    ),
    "OBA": (
        "eotc-ot-37",
        "The English Church list names ‘Obadiah’ (SRC-029); this Brenton member is titled ‘Obdias’ (SRC-038, SRC-142). "
        "The title form supports a separate research-reader link; the Brenton text is a Greek-basis English witness, not a translation from Geʽez, "
        "and is not established as an Ethiopian Orthodox edition. It remains outside canon-linked coverage.",
    ),
    "JON": (
        "eotc-ot-38",
        "The English Church list names ‘Jonah’ (SRC-029); this Brenton member is titled ‘Jonas’ (SRC-038, SRC-142). "
        "The title form supports a separate research-reader link; the Brenton text is a Greek-basis English witness, not a translation from Geʽez, "
        "and is not established as an Ethiopian Orthodox edition. It remains outside canon-linked coverage.",
    ),
    "MIC": (
        "eotc-ot-35",
        "The English Church list names ‘Micah’ (SRC-029); this Brenton member is titled ‘Michæas’ (SRC-038, SRC-142). "
        "The title form supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "NAM": (
        "eotc-ot-39",
        "The English Church list names ‘Nahum’ (SRC-029); this Brenton member is titled ‘Naum’ (SRC-038, SRC-142). "
        "The title form supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "HAB": (
        "eotc-ot-40",
        "The English Church list names ‘Habakkuk’ (SRC-029); this Brenton member is titled ‘Ambacum’ (SRC-038, SRC-142). "
        "The title form supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "ZEP": (
        "eotc-ot-41",
        "The English Church list names ‘Zephaniah’ (SRC-029); this Brenton member is titled ‘Sophonias’ and has USFM code ZEP (SRC-038, SRC-142). "
        "It is distinct from Brenton’s ‘Zacharias’ member (code ZEC), which is the separate Zechariah title. This supports only a provisional title/code candidate, "
        "not text agreement with a Geʽez witness or current Ethiopian Orthodox edition. It remains outside canon-linked coverage.",
    ),
    "HAG": (
        "eotc-ot-42",
        "The English Church list names ‘Haggai’ (SRC-029); this Brenton member is titled ‘Aggæus’ (SRC-038, SRC-142). "
        "The title form supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "WIS": (
        "eotc-ot-26",
        "The Church list names ‘Metsihafe Tibeb (the books of wisdom)’ (SRC-029). This Brenton member is separately titled "
        "‘Wisdom Of Solomon’ and uses standard module code WIS (SRC-038, SRC-142, SRC-384). It is surfaced only as a possible "
        "single-work discovery link within the broader plural title. This does not establish that it is identical to the grouped "
        "Church-list entry, represents all works intended by that title, or matches a Geʽez witness in contents or chapter boundaries. "
        "This English Septuagint research reader remains outside canon-linked coverage.",
    ),
    "ZEC": (
        "eotc-ot-43",
        "The English Church list names ‘Zechariah’ (SRC-029); this Brenton member is titled ‘Zacharias’ and has USFM code ZEC (SRC-038, SRC-142). "
        "It is distinct from Brenton’s ‘Sophonias’ member (code ZEP), which is the separate Zephaniah title. This supports only a provisional title/code candidate, "
        "not text agreement with a Geʽez witness or current Ethiopian Orthodox edition. It remains outside canon-linked coverage.",
    ),
    "MAL": (
        "eotc-ot-44",
        "The English Church list names ‘Malachi’ (SRC-029); this Brenton member is titled ‘Malachias’ (SRC-038, SRC-142). "
        "The title form supports a research-only candidate link; it does not establish textual agreement with a Geʽez witness or current Ethiopian Orthodox edition. "
        "This English translation is from the Greek Septuagint and remains outside canon-linked coverage.",
    ),
    "DAG": (
        "eotc-ot-32",
        "The English Church list names ‘Daniel’ (SRC-029), and this Brenton member is titled ‘Daniel (Greek)’ (SRC-038, SRC-142). "
        "The title supports a separate research-reader link only; this Greek Daniel witness has distinct scope and additions that have not been compared with the Church-list Geʽez work. "
        "It is not a replacement or verified equivalent and remains outside canon-linked coverage.",
    ),
    "1CH": (
        "eotc-ot-11",
        "The English Church list names ‘I Chronicles’ (SRC-029), and the archived Brenton USFM member is titled ‘Chronicles I’ (SRC-038, SRC-142). "
        "The matching title supports a research-only candidate link. It does not establish that this English translation of the Greek Septuagint "
        "matches a Geʽez witness or an Ethiopian Orthodox printed edition, or that their contents and chapter boundaries agree. "
        "This reader remains outside canon-linked coverage.",
    ),
    "2CH": (
        "eotc-ot-12",
        "The English Church list names ‘II Chronicles’ (SRC-029), and the archived Brenton USFM member is titled ‘Chronicles II’ (SRC-038, SRC-142). "
        "The matching title supports a research-only candidate link. It does not establish that this English translation of the Greek Septuagint "
        "matches a Geʽez witness or an Ethiopian Orthodox printed edition, or that their contents and chapter boundaries agree. "
        "This reader remains outside canon-linked coverage.",
    ),
    "JDT": (
        "eotc-ot-18",
        "The English Church list names ‘Judith’ (SRC-029), and this Brenton USFM member is titled ‘Judith’. "
        "The shared title supports a research-only candidate link; it does not establish that Brenton's English "
        "translation of Greek Septuagint Judith matches a Geʽez witness or an Ethiopian Orthodox printed edition, "
        "or that their contents and chapter boundaries agree. This reader remains outside canon-linked coverage.",
    ),
    "ESG": (
        "eotc-ot-19",
        "The English Church list names ‘Esther’ (SRC-029), while this archived Brenton USFM member is explicitly "
        "titled ‘Esther (Greek)’. The shared title supports only a research-candidate link; it does not establish "
        "identity with a Geʽez witness or an Ethiopian Orthodox printed edition, or agreement in contents and chapter "
        "boundaries. Its chapter 1 lettered labels are preserved as source labels. This separate English Septuagint "
        "reader remains outside canon-linked coverage.",
    ),
    "1MA": (
        "eotc-ot-20",
        "The English Church list names ‘I Maccabees’ (SRC-029). The archived Brenton member code 1MA has its own "
        "USFM heading ‘Maccabees I’; eBible's public title index calls the separate English Septuagint book ‘I Maccabees’. "
        "This supports only a title-level research candidate, not identity with a Geʽez witness or an EOTC printed edition, "
        "nor agreement in contents or chapter boundaries. This reader remains outside canon-linked coverage.",
    ),
    "2MA": (
        "eotc-ot-21",
        "The English Church list groups ‘II and III Maccabees’ at entry 21 (SRC-029). This separate Brenton member "
        "is titled ‘Maccabees II’. It is a title-level candidate for the grouped entry only; it does not establish that "
        "the Ethiopian grouping maps one-to-one to this Greek Septuagint witness, or that contents and boundaries agree. "
        "This reader remains outside canon-linked coverage.",
    ),
    "3MA": (
        "eotc-ot-21",
        "The English Church list groups ‘II and III Maccabees’ at entry 21 (SRC-029). This separate Brenton member "
        "is titled ‘Maccabees III’. It is a title-level candidate for the grouped entry only; it does not establish that "
        "the Ethiopian grouping maps one-to-one to this Greek Septuagint witness, or that contents and boundaries agree. "
        "This reader remains outside canon-linked coverage.",
    ),
}
ANCILLARY_CODES = {"FRT", "INT", "XXB", "XXC", "BAK", "OTH", "XXA"}
ANCILLARY_TITLES = {
    "FRT": ("Abbreviations and signs used in the notes", "glossary"),
    "INT": ("1870 Introduction", "introduction"),
    "XXB": ("1844 Preface", "preface"),
    "XXC": ("Errata", "errata"),
    "BAK": ("Appendix", "appendix"),
    "OTH": ("The Books of the Apocrypha", "historical introduction"),
    "XXA": ("Table of chapter and verse order in Jeremiah", "reference table"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_heading(source: str, marker: str) -> str:
    match = re.search(rf"^\\{marker}\s+(.+?)\s*$", source, re.M)
    return match.group(1).strip() if match else ""


def build_records() -> tuple[list[dict], list[dict], dict]:
    package_bytes = PACKAGE_PATH.read_bytes()
    package_hash = sha256(package_bytes)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("archive_sha256") != package_hash:
        raise ValueError("Brenton USFM package checksum differs from its capture manifest.")
    with zipfile.ZipFile(PACKAGE_PATH) as archive:
        members: dict[str, tuple[str, bytes]] = {}
        for member_name in archive.namelist():
            if not member_name.endswith(".usfm"):
                continue
            raw = archive.read(member_name)
            match = re.search(rb"^\\id\s+([A-Z0-9]{3})\s+-\s+Brenton English Septuagint\s*$", raw, re.M)
            if match:
                members[match.group(1).decode("ascii")] = (member_name, raw)
            elif (member_name == "13-2KIeng-Brenton.usfm"
                  and re.search(rb"^\\id\s+2KI\s*$", raw, re.M)
                  and re.search(rb"^\\toc3\s+4 Kings\s*$", raw, re.M)):
                # This eBible Brenton package member omits its edition name
                # from \id; require the exact package path plus its printed
                # fourth-Kings contents heading before admitting it.
                members["2KI"] = (member_name, raw)

    missing = RESEARCH_CODES - members.keys()
    if missing:
        raise ValueError(f"Expected USFM members are absent from the package: {sorted(missing)}")
    if RESEARCH_CODES & ALREADY_REPRESENTED:
        raise ValueError("Research set overlaps an already bundled reader.")
    if ANCILLARY_CODES & (RESEARCH_CODES | ALREADY_REPRESENTED):
        raise ValueError("Brenton ancillary matter overlaps a book-reader selection.")
    if members.keys() != RESEARCH_CODES | ALREADY_REPRESENTED | ANCILLARY_CODES:
        raise ValueError(
            "The archived Brenton USFM inventory changed; reconcile book readers, separately represented books, "
            "and ancillary edition matter before updating the manifest."
        )

    readers: list[dict] = []
    corpora: list[dict] = []
    selected_members = manifest.setdefault("selected_members", {})
    notice = (
        "eBible.org identifies Brenton's 1851 English translation as public domain. "
        "This is a provider-reported status, not a jurisdiction-specific legal determination; "
        "other source layers and archive materials have separate rights."
    )
    for code in sorted(RESEARCH_CODES):
        member_name, raw = members[code]
        candidate = CANDIDATE_CANON_LINKS.get(code)
        source_ids = ["SRC-038", "SRC-142"] + (["SRC-029", "SRC-384"] if candidate else [])
        source = raw.decode("utf-8-sig")
        chapter_count = len(re.findall(r"^\\c\s+\d+\s*$", source, re.M))
        source_title = source_heading(source, "h") or source_heading(source, "toc1") or code
        mt_title = source_heading(source, "mt1")
        title = f"{source_title} — Brenton English Septuagint (1851)"
        slug = code.lower().replace("1", "first-").replace("2", "second-").replace("3", "third-").replace("4", "fourth-").strip("-")
        reader_id = f"brenton-lxx-{slug}-research"
        corpus_id = f"brenton-lxx-{slug}-research"
        previous_book = brenton.BOOKS.get(code)
        brenton.BOOKS[code] = (slug, 0, source_title, chapter_count)
        try:
            parsed = brenton.parse_usfm(raw, code, member_name, package_hash)
        finally:
            if previous_book is None:
                brenton.BOOKS.pop(code, None)
            else:
                brenton.BOOKS[code] = previous_book
        member_hash = sha256(raw)
        selected_members[member_name] = {"sha256": member_hash, "byte_length": len(raw)}
        chapters = parsed["chapters"]
        unit_count = parsed["unit_count"]
        notes = parsed["note_count"]
        continuations = parsed["continuation_segment_count"]
        marker_only_count = parsed.get("marker_only_unit_count", 0)
        lettered_label_count = sum(
            bool(re.fullmatch(r"\d+[a-z]", str(verse.get("number", ""))))
            for chapter in chapters for verse in chapter["verses"]
        )
        source_metadata_note = (
            "Source metadata exception: this member's `\\id` line contains only `2KI`, without the Brenton edition label. "
            "It is admitted only by the exact archived filename plus the `4 Kings`/`KINGS IV.` headings. The anomaly is preserved; "
            "it does not independently verify textual identity or accuracy. "
            if code == "2KI" else ""
        )
        record = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "reader_scope": "research_witness_not_mapped_to_eotc_canon",
            "title": title,
            "display_name": f"{source_title} (Brenton English LXX, 1851)",
            "text_origin": "published_translation",
            "translation_id": parsed["translation_id"],
            "language": "English",
            "language_tag": "en",
            "script_code": "Latn",
            "translator": "Sir Lancelot Charles Lee Brenton",
            "basis_language_tag": "grc",
            "translation_path": ["grc", "en"],
            "translation_basis_status": "established",
            "translation_basis_note": "eBible.org identifies Brenton's 1851 English translation as from the Greek Septuagint; the edition title specifies the Vatican Text. This records the edition-stated Greek-to-English basis, not an independently audited translator workflow, textual accuracy, or alignment to Geʽez.",
            "edition": "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851).",
            "edition_scope": (
                "Historical English translation of a Greek Septuagint text as represented by this eBible.org USFM member. "
                "This is a separate research witness; it is not a Geʽez transcription, an EOTC printed-edition claim, "
                "or a verified translation from Geʽez. Any title-based EOTC candidate recorded for it is provisional "
                "and does not make this reader canon-linked."
            ),
            "chapter_count": len(chapters),
            "unit_count": unit_count,
            "unit_label": "English verse labels observed in the archived USFM member",
            "verse_marker_count": unit_count,
            "section_label": "Chapter",
            "chapter_structure_note": (
                f"The local USFM member {member_name} contains {len(chapters)} ordered chapter markers, "
                f"{unit_count:,} source labels, including {lettered_label_count:,} lettered labels, "
                f"{notes:,} preserved notes/cross-references, and "
                f"{continuations:,} unnumbered continuation segments. Marker-only source labels without inline text: "
                f"{marker_only_count}. These are package observations, "
                "not proof of completeness against a print edition, Greek witness, or any community's canon."
            ),
            "transcription_note": "Reader wording is parsed from the archived USFM member and has not been independently collated against the printed 1851 edition or the Greek source.",
            "editorial_signs_note": "USFM translator-supplied-word markers are displayed in visible archival brackets ⟦…⟧. Source notes, cross-references, headings, paragraph markers, and continuation segments are retained as structured data.",
            "source_ids": source_ids,
            "source_pages": f"readers/source/brenton-septuagint/{member_name} (member of the locally archived package)",
            "source_package_sha256": package_hash,
            "source_member_sha256": member_hash,
            "rights_classification": "public_domain_claimed",
            "copyright_notice": notice,
            "commercial_use": "The provider identifies Brenton's 1851 translation as public domain; this is not a jurisdiction-specific rights determination.",
            "verification_status": (
                source_metadata_note
                + f"Automated parsing checked the local member checksum, {len(chapters)} sequential chapter markers, "
                f"{unit_count:,} source labels, {notes:,} notes/cross-references, and {continuations:,} continuation segments. "
                f"{marker_only_count:,} source label(s) have no inline text and remain explicitly marked as such. "
                "This confirms local package-to-reader structural fidelity only. Exact wording, accuracy against Greek or print, "
                "printed-edition completeness, and relationship to any EOTC text remain unreviewed. It is not canon-linked and is not counted as an EOTC canon reader or toward EOTC coverage."
            ),
            "chapters": chapters,
        }
        readers.append(record)
        corpora.append({
            "corpus_id": corpus_id,
            "title": title,
            "reader_id": reader_id,
            "unit_count": unit_count,
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "uncertain" if candidate else "not_mapped",
            "candidate_canon_id": candidate[0] if candidate else None,
            "canon_mapping_note": candidate[1] if candidate else "No EOTC canon crosswalk is assigned. Similar English titles in other catalogues do not establish work identity, Geʽez text identity, or the same chapter boundaries. This English Septuagint research reader is excluded from canon-linked coverage.",
            "language_description": "English (en), translated by Sir Lancelot Charles Lee Brenton from Greek (grc).",
            "script_description": "Latin script (Latn), as used by the English digital witness.",
            "unit_summary": f"{unit_count:,} English labels in {len(chapters)} ordered chapter divisions, with {notes:,} notes/cross-references, {marker_only_count:,} labels without inline text, and {continuations:,} continuation segments observed in the local USFM member.",
            "rights_classification": "public_domain_claimed",
            "rights_status": notice,
            "review_status": record["verification_status"],
            "source_ids": source_ids,
            "text_origin": "published_translation",
            "language_tag": "en",
            "script_code": "Latn",
            "basis_language_tag": "grc",
            "translation_path": ["grc", "en"],
            "translation_basis_status": "established",
            "translation_basis_note": "eBible.org identifies Brenton's 1851 English translation as from the Greek Septuagint; the edition title specifies the Vatican Text. This records the edition-stated Greek-to-English basis, not an independently audited translator workflow, textual accuracy, or alignment to Geʽez.",
            "translation_basis_source_ids": ["SRC-142"],
            "translation_id": parsed["translation_id"],
            "translator": "Sir Lancelot Charles Lee Brenton",
            "edition_statement": record["edition"],
        })

    # Keep selected-member hashes deterministic and the scope statement exact.
    manifest["selected_members"] = dict(sorted(selected_members.items()))
    ancillary_members = []
    for code in sorted(ANCILLARY_CODES):
        member_name, raw = members[code]
        title, category = ANCILLARY_TITLES[code]
        ancillary_members.append({
            "usfm_id": code,
            "path": member_name,
            "title": title,
            "category": category,
            "byte_length": len(raw),
            "sha256": sha256(raw),
            "handling": "Retained inside the checksummed source archive and inventoried as non-scripture edition matter; not treated as a biblical book or parsed into a reader.",
        })
    manifest["ancillary_members"] = ancillary_members
    manifest["member_inventory"] = {
        "total_usfm_members": len(members),
        "parsed_as_additional_book_readers": len(RESEARCH_CODES),
        "book_members_handled_by_separate_local_readers": len(ALREADY_REPRESENTED),
        "ancillary_nonbook_members": len(ANCILLARY_CODES),
    }
    manifest["scope"] = (
        "The capture manifest lists all selected members. Existing English companions and research texts are retained separately; "
        f"{len(RESEARCH_CODES)} additional book members are parsed as independent English research readers; "
        f"{len(CANDIDATE_CANON_LINKS)} have scoped, explicitly provisional title candidates, and none becomes an EOTC canon-linked reader. "
        f"{len(ALREADY_REPRESENTED)} book members are handled by separate local readers. "
        "Seven additional members are non-scripture edition matter (abbreviations, introductions, preface, errata, appendix, "
        "an Apocrypha introduction, and a Jeremiah chapter/verse reference table); they remain in the source ZIP and are inventoried, "
        "not misclassified as biblical books or parser failures."
    )
    manifest["limitations"] = (
        "The provider identifies Brenton's translation as 1851 and public domain. Checks establish local package identity and "
        "parser extraction structure only; they do not establish print-edition completeness, Greek translation accuracy, "
        "or identity with any Geʽez/EOTC witness. Provisional title candidates support discovery only; they do not assert exact scope or canon membership. "
        "Seven non-book ancillary members are retained and inventoried but not presented "
        "as scripture readers. Book members with separately represented readers are not imported a second time. "
        "No source text is silently repaired."
    )
    return readers, corpora, manifest


def main() -> None:
    readers, corpora, manifest = build_records()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reader_dir = ROOT / "readers"
    for reader in readers:
        code_slug = reader["reader_id"].removeprefix(READER_PREFIX).removesuffix("-research")
        path = reader_dir / f"{READER_PREFIX}{code_slug}{READER_SUFFIX}"
        path.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    other_corpora = [item for item in registry.get("research_corpora", []) if item.get("reader_id") not in {r["reader_id"] for r in readers}]
    registry["research_corpora"] = other_corpora + corpora
    canon_registry = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    registry["coverage_statement"] = build_coverage_statement(registry, canon_registry)
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Built {len(readers)} standalone Brenton research readers; no verified EOTC crosswalks assigned, "
        "and any title candidates remain explicitly provisional."
    )


if __name__ == "__main__":
    main()
