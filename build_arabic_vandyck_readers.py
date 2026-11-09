"""Build structurally checked, separate Arabic Van Dyck research readers from archived USFM."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from copy import deepcopy
from pathlib import Path

from book_code_crosswalks import PUBLISHER_BOOK_CODE_CANDIDATES, candidate_note
from rights_metadata import reader_rights_status

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "readers/source/arabic-vandyck-2026/arb-vd_usfm_text_only.zip"
CAPTURE_MANIFEST = ROOT / "readers/source/arabic-vandyck-2026/capture-manifest.json"
EXPECTED_BUNDLE_SHA256 = "e0a2e9ceb7f621268974648c7150421694249cbc636cdff23aa4b36c69fbaf9b"
EXPECTED_UPSTREAM_PACKAGE_SHA256 = "8c3b212750ca37850c94d53ebdf8a5919fc5c5d4d0a986de17f900ba84ac6e80"
SOURCE_IDS = ["SRC-329", "SRC-330", "SRC-335", "SRC-340"]
STANDARD_ARABIC_PROFILE = {
    "language_tag": "arb",
    "language_name": "Standard Arabic",
    "script_code": "Arab",
    "script_codes": ["Arab"],
    "script_profile_note": "eBible.org labels the Van Dyck edition standard Arabic [arb]. Its linked display stylesheet explicitly sets right-to-left direction for that witness. This profile records the one named edition represented by the locally bundled 66-book USFM package; it is not an inventory of all Standard Arabic scripture editions or Arabic varieties and does not imply an Eritrean-specific or EOTC text.",
    "source_ids": ["SRC-077", "SRC-078", "SRC-329", "SRC-330", "SRC-335"],
    "direction": "rtl",
    "records": [],
    "availability_survey": {
        "status": "completed",
        "scope": "Inspected eBible.org's Arabic Van Dyck edition record, its linked display stylesheet, and the retained USFM package. The bounded result is one named Standard Arabic edition with 66 separate book members; it is not a census of Standard Arabic resources, a completeness review, or a survey of Arabic varieties.",
        "searched_at": "2026-10-25",
        "result": "records_found",
        "result_count": 1,
        "source_ids": ["SRC-329", "SRC-330", "SRC-335"],
        "notes": "The IANA registry identifies arb as Standard Arabic within the ar macrolanguage. eBible.org labels the Van Dyck edition [arb], dialect standard. Its package is stored as research text only; member counts do not establish accuracy, completeness, translation basis, or a canon crosswalk.",
    },
}

BOOKS = {
    "GEN": ("01-gen", "Genesis"), "EXO": ("02-exo", "Exodus"), "LEV": ("03-lev", "Leviticus"),
    "NUM": ("04-num", "Numbers"), "DEU": ("05-deu", "Deuteronomy"), "JOS": ("06-jos", "Joshua"),
    "JDG": ("07-jdg", "Judges"), "RUT": ("08-rut", "Ruth"), "1SA": ("09-1sa", "1 Samuel"),
    "2SA": ("10-2sa", "2 Samuel"), "1KI": ("11-1ki", "1 Kings"), "2KI": ("12-2ki", "2 Kings"),
    "1CH": ("13-1ch", "1 Chronicles"), "2CH": ("14-2ch", "2 Chronicles"), "EZR": ("15-ezr", "Ezra"),
    "NEH": ("16-neh", "Nehemiah"), "EST": ("17-est", "Esther"), "JOB": ("18-job", "Job"),
    "PSA": ("19-psa", "Psalms"), "PRO": ("20-pro", "Proverbs"), "ECC": ("21-ecc", "Ecclesiastes"),
    "SNG": ("22-sng", "Song of Songs"), "ISA": ("23-isa", "Isaiah"), "JER": ("24-jer", "Jeremiah"),
    "LAM": ("25-lam", "Lamentations"), "EZK": ("26-ezk", "Ezekiel"), "DAN": ("27-dan", "Daniel"),
    "HOS": ("28-hos", "Hosea"), "JOL": ("29-jol", "Joel"), "AMO": ("30-amo", "Amos"),
    "OBA": ("31-oba", "Obadiah"), "JON": ("32-jon", "Jonah"), "MIC": ("33-mic", "Micah"),
    "NAM": ("34-nam", "Nahum"), "HAB": ("35-hab", "Habakkuk"), "ZEP": ("36-zep", "Zephaniah"),
    "HAG": ("37-hag", "Haggai"), "ZEC": ("38-zec", "Zechariah"), "MAL": ("39-mal", "Malachi"),
    "MAT": ("40-mat", "Matthew"), "MRK": ("41-mrk", "Mark"), "LUK": ("42-luk", "Luke"),
    "JHN": ("43-jhn", "John"), "ACT": ("44-act", "Acts"), "ROM": ("45-rom", "Romans"),
    "1CO": ("46-1co", "1 Corinthians"), "2CO": ("47-2co", "2 Corinthians"), "GAL": ("48-gal", "Galatians"),
    "EPH": ("49-eph", "Ephesians"), "PHP": ("50-php", "Philippians"), "COL": ("51-col", "Colossians"),
    "1TH": ("52-1th", "1 Thessalonians"), "2TH": ("53-2th", "2 Thessalonians"), "1TI": ("54-1ti", "1 Timothy"),
    "2TI": ("55-2ti", "2 Timothy"), "TIT": ("56-tit", "Titus"), "PHM": ("57-phm", "Philemon"),
    "HEB": ("58-heb", "Hebrews"), "JAS": ("59-jas", "James"), "1PE": ("60-1pe", "1 Peter"),
    "2PE": ("61-2pe", "2 Peter"), "1JN": ("62-1jn", "1 John"), "2JN": ("63-2jn", "2 John"),
    "3JN": ("64-3jn", "3 John"), "JUD": ("65-jud", "Jude"), "REV": ("66-rev", "Revelation"),
}
ALLOWED_MARKERS = {"id", "h", "toc1", "toc2", "toc3", "mt1", "c", "cl", "s1", "p", "d", "qa", "qc", "nb", "v"}
HEADING_MARKERS = {"s1", "d", "qa", "qc"}

SOURCES = [
    {
        "source_id": "SRC-329",
        "source_name": "eBible.org — Arabic Van Dyck Bible edition record",
        "url": "https://ebible.org/bible/details.php?id=arb-vd",
        "inspection_and_limitations": "Inspected 2026-10-25. eBible.org identifies the Arabic Van Dyck Bible as standard Arabic [arb], names the Syrian Mission as translator and the American Bible Society as contributor, and labels the edition public domain. These are provider statements, not independent rights advice or a textual accuracy review. The country-filtered Eritrea listing is a separate discovery context and does not make this an Eritrean-specific translation.",
        "archive_status": "Edition metadata source for bundled standard-Arabic research witnesses; rights status is provider-claimed public domain, not independently adjudicated",
    },
    {
        "source_id": "SRC-330",
        "source_name": "eBible.org — Arabic Van Dyck USFM package captured locally",
        "url": "https://ebible.org/Scriptures/arb-vd_usfm.zip",
        "inspection_and_limitations": "Downloaded 2026-10-25 from the USFM link on the eBible.org Arabic Van Dyck edition page. The exact 1,744,912-byte upstream ZIP is retained outside the public site at ../source-captures/arabic-vandyck-2026/arb-vd_usfm_original.zip (SHA-256 recorded in capture-manifest.json). The deployed tree carries a deterministic USFM-only bundle of its 66 scripture members; stylesheet, HTML copyright page, public key, and signature assets are excluded. The checksums of all 66 members match the checksum list inside the upstream clear-signed file, but the PGP signature was not cryptographically verified. The builder checks the local text-bundle hash, member hashes, unique book IDs, known marker inventory, chapter sequence, and verse extraction. This is structural evidence only, not collation, translation accuracy, completeness, canon identity, or suitability for every Arabic-speaking community.",
        "archive_status": "Exact upstream package retained in local source-captures; text-only subset bundled publicly; member checksums match packaged list, PGP signature unverified; wording not independently collated",
    },
    {
        "source_id": "SRC-335",
        "source_name": "eBible.org — Arabic Van Dyck mobile HTML stylesheet (witness display direction)",
        "url": "https://ebible.org/arb-vd/amiri.css",
        "inspection_and_limitations": "Inspected 2026-10-25. The stylesheet linked from eBible.org's Arabic Van Dyck mobile HTML edition sets direction:rtl and text-align:right for html and body. This verifies the displayed direction of that witness; it is not a general claim about every Arabic-language resource or script use.",
        "archive_status": "Witness-specific layout metadata inspected to support right-to-left rendering; no scripture text copied",
    },
    {
        "source_id": "SRC-340",
        "source_name": "John A. Thompson — historical account of the Smith–Van Dyck Arabic Bible's source texts",
        "url": "https://translation.bible/wp-content/uploads/2024/05/thompson-1955-the-origin-and-nature-of-the-chief-printed-arabic-bibles-2.pdf",
        "inspection_and_limitations": "Inspected 2026-10-25. In Part III of 'The Origin and Nature of the Chief Printed Arabic Bibles' (The Bible Translator, 1955), Thompson reports that the Smith–Van Dyck version follows the Masoretic text in Hebrew and Aramaic for the Old Testament and the Greek Textus Receptus for the New Testament. He distinguishes these base texts from ancient versions, including Syriac, used for variant readings in reference-edition notes. This is a historical account of edition policy; it does not collate the later eBible.org digital witness, establish every book's exact textual decisions, or assess translation accuracy.",
        "archive_status": "Scholarly historical evidence about edition-level source-text policy; book-specific path for the bundled digital witness remains unverified",
    },
    {
        "source_id": "SRC-396",
        "source_name": "USFM/USX Documentation — standard book identifiers and tradition-specific notes",
        "url": "https://docs.usfm.bible/usfm/3.2/doc/books.html",
        "inspection_and_limitations": "Inspected 2026-10-26. The official USFM/USX 3.2 identifier table defines standard three-character codes and notes tradition- or edition-specific distinctions, including Hebrew versus Greek Esther (EST/ESG) and Daniel (DAN/DAG), different Psalm inventories, 24 Proverbs in the Ethiopian Bible, and alternative Orthodox numbering for Samuel/Kings. Used only to document code semantics and warn against inferring textual scope from a code. It does not identify the Arabic Van Dyck edition's underlying text, prove any EOTC or Eritrean canon mapping, or verify content.",
        "archive_status": "Official standard-code reference; supports identifier semantics and scope cautions only, not textual or canon equivalence",
    },
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_member(raw: bytes, expected_id: str, member_name: str) -> dict:
    text = raw.decode("utf-8-sig")
    chapters: list[dict] = []
    current = None
    pending_markers: list[str] = []
    pending_headings: list[str] = []
    pending_elements: list[dict] = []
    metadata = {}
    count = 0
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = re.match(r"^\\([A-Za-z0-9+*]+)\s*(.*)$", line)
        if not match:
            raise ValueError(f"{member_name}:{line_no}: unmarked nonempty line would be dropped")
        marker, value = match.group(1), match.group(2).strip()
        if marker not in ALLOWED_MARKERS:
            raise ValueError(f"{member_name}:{line_no}: unsupported marker \\{marker}")
        if marker == "id":
            if value.split()[0] != expected_id:
                raise ValueError(f"{member_name}: filename ID {expected_id} disagrees with \\id {value}")
        elif marker in {"h", "toc1", "toc2", "toc3", "mt1"}:
            metadata.setdefault(marker, []).append(value)
        elif marker == "cl":
            if current is None:
                metadata.setdefault(marker, []).append(value)
            else:
                current["source_chapter_label"].append(value)
        elif marker == "c":
            if not value.isdigit():
                raise ValueError(f"{member_name}:{line_no}: nonnumeric chapter label {value!r}")
            current = {"chapter": int(value), "verses": [], "heading": [], "source_chapter_label": [], "source_markers": []}
            chapters.append(current)
            pending_markers = []
            pending_headings = []
            pending_elements = []
        elif marker == "v":
            if current is None:
                raise ValueError(f"{member_name}:{line_no}: verse appears before chapter")
            verse_match = re.match(r"^(\d+[a-z]?)(?:-(\d+[a-z]?))?\s*(.*)$", value)
            if not verse_match:
                raise ValueError(f"{member_name}:{line_no}: unsupported verse label {value!r}")
            number, end, verse_text = verse_match.groups()
            if end:
                number = f"{number}-{end}"
            if not verse_text:
                raise ValueError(f"{member_name}:{line_no}: empty verse would be ambiguous")
            verse = {"number": number, "text": verse_text}
            if pending_markers:
                verse["source_markers_before"] = pending_markers
            if pending_headings:
                verse["source_headings_before"] = pending_headings
            if pending_elements:
                verse["source_elements_before"] = pending_elements
            current["verses"].append(verse)
            pending_markers, pending_headings, pending_elements = [], [], []
            count += 1
        elif marker in HEADING_MARKERS:
            if current is None:
                raise ValueError(f"{member_name}:{line_no}: heading appears before chapter")
            pending_markers.append(marker)
            pending_elements.append({"marker": marker, "text": value})
            if value:
                pending_headings.append(value)
        else:
            if current is None:
                raise ValueError(f"{member_name}:{line_no}: marker \\{marker} appears before chapter")
            pending_markers.append(marker)
            pending_elements.append({"marker": marker, "text": value})
            if marker == "cl":
                current["source_chapter_label"].append(value)
            else:
                current["source_markers"].append({"marker": marker, "text": value})
    if not chapters or not count:
        raise ValueError(f"{member_name}: no chapter/verse text parsed")
    if pending_markers or pending_headings:
        chapters[-1]["source_trailing_markers"] = pending_markers
        chapters[-1]["source_trailing_headings"] = pending_headings
        chapters[-1]["source_trailing_elements"] = pending_elements
    expected_chapters = list(range(1, len(chapters) + 1))
    if [item["chapter"] for item in chapters] != expected_chapters:
        raise ValueError(f"{member_name}: chapter order/numbering is not a simple 1..N sequence")
    return {"chapters": chapters, "chapter_count": len(chapters), "verse_count": count, "metadata": metadata}


def build() -> tuple[list[dict], list[dict]]:
    payload = PACKAGE.read_bytes()
    package_hash = sha256(payload)
    manifest = json.loads(CAPTURE_MANIFEST.read_text(encoding="utf-8"))
    if package_hash != EXPECTED_BUNDLE_SHA256 or manifest.get("public_bundle_sha256") != package_hash:
        raise ValueError(f"Van Dyck text-only bundle checksum mismatch: {package_hash}")
    if manifest.get("upstream_package_sha256") != EXPECTED_UPSTREAM_PACKAGE_SHA256:
        raise ValueError("Van Dyck upstream source-package checksum record changed")
    readers, corpora = [], []
    with zipfile.ZipFile(PACKAGE) as zf:
        members = sorted(zf.namelist())
        if len(members) != 66 or any(not name.lower().endswith(".usfm") for name in members):
            raise ValueError("Public Van Dyck bundle must contain only its 66 USFM scripture members")
        manifest_members = manifest.get("members", {})
        if set(members) != set(manifest_members):
            raise ValueError("Van Dyck bundle member inventory disagrees with capture manifest")
        parsed_by_id = {}
        member_names = {}
        for name in members:
            match = re.match(r"\d{2}-([A-Z0-9]{3})arb-vd\.usfm$", Path(name).name)
            if not match:
                raise ValueError(f"Unexpected USFM member filename: {name}")
            book_code = match.group(1)
            if book_code not in BOOKS or book_code in parsed_by_id:
                raise ValueError(f"Unknown or duplicate book code {book_code}")
            parsed_by_id[book_code] = parse_member(zf.read(name), book_code, name)
            member_names[book_code] = name
        if set(parsed_by_id) != set(BOOKS):
            raise ValueError(f"Expected the 66 distinct book IDs listed in the Van Dyck package; found {len(parsed_by_id)}")
        for code, (slug, name) in BOOKS.items():
            parsed = parsed_by_id[code]
            reader_id = f"arb-vd-{slug.split('-',1)[1]}-research"
            corpus_id = f"arb-vd-{slug.split('-',1)[1]}-2020"
            member = zf.read(member_names[code])
            member_hash = sha256(member)
            if member_hash != manifest_members[member_names[code]].get("sha256") or member_hash != manifest_members[member_names[code]].get("upstream_manifest_sha256"):
                raise ValueError(f"{member_names[code]} checksum disagrees with source capture manifest")
            reader = {
                "reader_id": reader_id,
                "research_corpus_id": corpus_id,
                "reader_scope": "research_witness_uncertain_catalogue_mapping",
                "title": f"{name} — Arabic Van Dyck (standard Arabic; eBible.org package)",
                "display_name": f"Research reader — {name} (Arabic Van Dyck, standard Arabic)",
                "text_origin": "published_translation",
                "translation_id": "arabic-van-dyck-standard",
                "language": "Standard Arabic",
                "language_tag": "arb",
                "script_code": "Arab",
                "language_assignment_status": "eBible.org identifies this Van Dyck edition as Standard Arabic [arb] (SRC-329); the linked stylesheet sets right-to-left direction for this witness (SRC-335). These are edition-level metadata observations, not independent linguistic validation and not claims about other Arabic varieties or communities.",
                "translator": "Syrian Mission (attribution on eBible.org edition record)",
                "translation_basis_status": "unknown",
                "translation_basis_note": "The provider's edition record does not establish the source-language basis or a complete translation path. No basis language is inferred here.",
                "edition": "Arabic Van Dyck Bible; eBible.org USFM package, edition page dated 2020-08-03 (provider metadata)",
                "edition_statement": "Arabic Van Dyck Bible, standard Arabic [arb], USFM edition offered by eBible.org.",
                "edition_scope": "One separate book from a 66-book standard-Arabic package. This is a research witness, not an Eritrean-specific language edition or a Geʽez/EOTC text. Provisional title-code candidates are recorded separately where publisher standard book codes align with Church-list titles; these do not establish an EOTC crosswalk, identity, order, scope equivalence, or completeness.",
                "chapter_count": parsed["chapter_count"],
                "unit_count": parsed["verse_count"],
                "unit_label": "numbered USFM verse labels observed in the archived source member",
                "verse_marker_count": parsed["verse_count"],
                "section_label": "Chapter",
                "chapter_structure_note": f"The archived member has {parsed['chapter_count']} ordered chapter markers and {parsed['verse_count']} nonempty numbered verse labels. Chapter labels and recognized headings/paragraph markers are retained in reader structure. These counts describe the package, not completeness against another edition or canon.",
                "transcription_note": "Text was extracted from the locally retained UTF-8 USFM member. No independent collation against a print copy, source-language text, or another Arabic edition was performed.",
                "editorial_signs_note": "The parser preserves section headings, descriptive titles, paragraph markers, chapter labels, and observed verse labels as separate structural data; it rejects unrecognized markers or unmarked nonempty lines rather than silently dropping them.",
                "source_ids": SOURCE_IDS,
                "source_pages": f"readers/source/arabic-vandyck-2026/arb-vd_usfm_text_only.zip#{member_names[code]} (curated bundle member; original package hash is in the capture manifest)",
                "source_package_sha256": package_hash,
                "upstream_package_sha256": EXPECTED_UPSTREAM_PACKAGE_SHA256,
                "source_member_sha256": member_hash,
                "rights_classification": "public_domain_claimed",
                "copyright_notice": "eBible.org labels the translation text public domain. The provider's claim is recorded, not independently verified as a worldwide legal determination. The original support files have separate, unassessed terms and are excluded from the deployed bundle.",
                "commercial_use": "The provider labels the translation text public domain. This is not an independent rights determination; no rights claim is made for excluded support files.",
                "verification_status": "The text-only bundle hash and all 66 member hashes are checked against a local capture manifest; those member hashes also match the list inside the upstream clear-signed package file, but its PGP signature is not cryptographically verified. Expected inventory, recognized USFM markers, chapter sequence, and nonempty verse extraction are checked locally. Wording, translation accuracy, edition completeness, translation basis, and canon mapping are not independently verified.",
                "chapters": parsed["chapters"],
            }
            reader["rights_status"] = reader_rights_status(reader)
            readers.append(reader)
            candidate_canon_id = PUBLISHER_BOOK_CODE_CANDIDATES.get(code)
            mapping_state = "uncertain" if candidate_canon_id else "not_mapped"
            mapping_note = (
                candidate_note(code, candidate_canon_id)
                + " Crosswalk inputs: the publisher's standard book-code documentation (SRC-196), the official USFM/USX identifier reference (SRC-396), and the Church's cited English list (SRC-029); this provisional comparison is authored by the archive, not asserted by eBible.org."
                if candidate_canon_id else
                "No separate Church-list candidate is assigned to this publisher book code. This standard-Arabic research witness is not an Eritrean-specific or Geʽez/EOTC text; absence of a candidate is not a claim that no related text exists."
            )
            corpora.append({
                "corpus_id": corpus_id,
                "title": reader["title"],
                "reader_id": reader_id,
                "unit_count": parsed["verse_count"],
                "reader_status": "bundled_research_reader",
                "canon_mapping_state": mapping_state,
                "candidate_canon_id": candidate_canon_id,
                "canon_mapping_note": mapping_note,
                "language_description": "Standard Arabic [arb] as identified on eBible.org; this is not a distinct Eritrean Arabic witness.",
                "script_description": "Arabic script (ISO 15924 Arab).",
                "language_tag": "arb",
                "script_code": "Arab",
                "unit_summary": f"{parsed['chapter_count']} source chapters and {parsed['verse_count']} observed numbered verse labels in this package member.",
                "rights_classification": "public_domain_claimed",
                "rights_status": "eBible.org labels the translation text public domain. Recorded as a provider claim, not independently adjudicated; original CSS and support-file terms were not identified and those assets are excluded from the public bundle.",
                "review_status": "Package/member structural checks passed; no independent textual collation or translation review.",
                "source_ids": sorted(set(SOURCE_IDS) | ({"SRC-029", "SRC-196", "SRC-396"} if candidate_canon_id else set()), key=lambda value: int(value.split("-")[1])),
                "text_origin": "published_translation",
                "translation_id": "arabic-van-dyck-standard",
                "translator": "Syrian Mission (attribution on eBible.org edition record)",
                "translation_basis_status": "unknown",
                "translation_basis_note": "The provider's record does not document a source-text path for this digital reader. Thompson's historical account describes Smith–Van Dyck edition policy: Masoretic Hebrew and Aramaic for the Old Testament, and Greek Textus Receptus for the New Testament; Syriac and other versions are discussed for variant readings in reference notes. That edition-level account has not been collated against this digital witness or resolved for this specific book, so its book-specific path remains unknown.",
                "edition_statement": reader["edition_statement"],
            })
            path = ROOT / "readers" / f"{reader_id}.json"
            path.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return readers, corpora


def apply(archive: dict) -> None:
    _, corpora = build()
    sources = {item["source_id"]: item for item in archive.get("sources", [])}
    sources.update({item["source_id"]: item for item in SOURCES})
    archive["sources"] = list(sources.values())
    registry = archive.setdefault("translation_registry", {})
    existing = [item for item in registry.get("research_corpora", []) if not item.get("corpus_id", "").startswith("arb-vd-")]
    registry["research_corpora"] = sorted(existing + corpora, key=lambda item: item["corpus_id"])
    arabic_context = next((item for item in registry.get("languages", []) if item.get("language_tag") == "ar"), None)
    if arabic_context is None:
        raise ValueError("The existing Arabic country-context language profile is required")
    arabic_context["language_name"] = "Arabic"
    arabic_context["source_ids"] = sorted(set(arabic_context.get("source_ids", [])) - set(SOURCE_IDS), key=lambda value: int(value.split("-")[1]))
    arabic_context["script_profile_note"] = (
        "This [ar] profile carries a bounded eBible.org resource survey filtered by Eritrea. It uses the Arabic macrolanguage "
        "tag and does not represent one distinct Eritrean Arabic variety. The 66-book Van Dyck research package is separately "
        "recorded under Standard Arabic [arb]; it does not establish use by any Eritrean community. Reported local varieties "
        "remain separate secondary discovery leads."
    )
    profiles = registry.setdefault("languages", [])
    standard_arabic = next((item for item in profiles if item.get("language_tag") == "arb"), None)
    if standard_arabic is None:
        standard_arabic = deepcopy(STANDARD_ARABIC_PROFILE)
        ar_index = next(i for i, item in enumerate(profiles) if item.get("language_tag") == "ar")
        profiles.insert(ar_index + 1, standard_arabic)
    else:
        records = standard_arabic.get("records", [])
        standard_arabic.update(deepcopy(STANDARD_ARABIC_PROFILE))
        standard_arabic["records"] = records
