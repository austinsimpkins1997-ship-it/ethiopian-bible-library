"""Record the locally archived Ethiopic Octateuch source package and chapter menu."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "readers" / "source" / "Octateuch-Index.html"
MODULE = ROOT / "readers" / "source" / "crosswire" / "Geez.zip"
EXODUS_CAPTURE = ROOT / "readers" / "source" / "exodus" / "capture.json"
ADDITIONAL_CAPTURE = ROOT / "readers" / "source" / "octateuch-additional" / "capture.json"
MODULE_AUDIT = ROOT / "readers" / "source" / "crosswire" / "module-structure-audit.json"
OUTPUT = ROOT / "readers" / "source" / "Octateuch-scope.json"
ARCHIVE = ROOT / "archive.json"

BOOKS = [
    ("eotc-001", "Genesis", "Genesis", 50),
    ("eotc-002", "Exodus", "Exodus", 40),
    ("eotc-003", "Leviticus", "Leviticus", 27),
    ("eotc-004", "Numbers", "Numeri", 36),
    ("eotc-005", "Deuteronomy", "Deuteronomium", 34),
    ("eotc-006", "Joshua", "Josua", 24),
    ("eotc-007", "Judges", "Judices", 21),
    ("eotc-008", "Ruth", "Ruth", 4),
]

READER_SLUGS = {
    "Exodus": "exodus",
    "Leviticus": "leviticus",
    "Numbers": "numbers",
    "Deuteronomy": "deuteronomy",
    "Joshua": "joshua",
    "Judges": "judges",
    "Ruth": "ruth",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_chapter_menu() -> dict[str, list[int]]:
    if not INDEX.is_file() or not MODULE.is_file():
        raise ValueError("The local HaCohen menu and CrossWire module package are both required.")
    html = INDEX.read_bytes().decode("cp1255", errors="replace")
    menu: dict[str, list[int]] = {}
    for _, display_name, source_name, expected_count in BOOKS:
        chapters = sorted(
            int(number)
            for number in re.findall(
                rf"Octateuch/{re.escape(source_name)} (\d+)\.html", html
            )
        )
        if chapters != list(range(1, expected_count + 1)):
            raise ValueError(
                f"{display_name}: expected menu chapters 1–{expected_count}; found {chapters}."
            )
        menu[display_name] = chapters
    return menu


def module_metadata() -> dict[str, str]:
    with zipfile.ZipFile(MODULE) as package:
        conf = package.read("mods.d/geez.conf").decode("cp1252", errors="replace")
        expected_files = {
            "modules/texts/ztext/geez/ot.bzv",
            "modules/texts/ztext/geez/ot.bzz",
            "modules/texts/ztext/geez/ot.bzs",
            "mods.d/geez.conf",
        }
        missing = expected_files - set(package.namelist())
        if missing:
            raise ValueError(f"CrossWire package is missing expected files: {sorted(missing)}")
        required_phrases = ("Ran HaCohen", "NONCOMMERCIAL", "Copyrighted; Free non-commercial distribution")
        if any(phrase not in conf for phrase in required_phrases):
            raise ValueError("The CrossWire configuration no longer carries the expected attribution/rights text.")
        values = dict(re.findall(r"^([A-Za-z0-9_]+)=(.*)$", conf, re.MULTILINE))
        if values.get("Version") != "1.0.1" or values.get("SwordVersionDate") != "2012-07-10":
            raise ValueError("The archived package is not the inspected Geʽez module version.")
        return values


def source_record(source_id: str, name: str, url: str, details: str, status: str) -> dict:
    return {
        "source_id": source_id,
        "source_name": name,
        "url": url,
        "inspection_and_limitations": details,
        "archive_status": status,
    }


def main() -> None:
    menu = extract_chapter_menu()
    conf = module_metadata()
    menu_hash = sha256(INDEX)
    module_hash = sha256(MODULE)
    if not MODULE_AUDIT.is_file():
        raise ValueError("Run audit_crosswire_module.py before building the Octateuch inventory.")
    module_audit = json.loads(MODULE_AUDIT.read_text(encoding="utf-8"))
    if module_audit.get("module_sha256") != module_hash:
        raise ValueError("The CrossWire module structure audit is stale for the local source package.")
    module_audit_hash = sha256(MODULE_AUDIT)
    if not EXODUS_CAPTURE.is_file():
        raise ValueError("The local Exodus chapter-page capture is required.")
    exodus_capture_hash = sha256(EXODUS_CAPTURE)
    additional_capture_hash = sha256(ADDITIONAL_CAPTURE) if ADDITIONAL_CAPTURE.is_file() else None
    records = []
    def bundled_reader_path(display_name: str) -> Path | None:
        slug = READER_SLUGS.get(display_name)
        path = ROOT / "readers" / f"{slug}-geez.json" if slug else None
        return path if path and path.is_file() else None

    for catalogue_id, display_name, source_name, _ in BOOKS:
        chapters = menu[display_name]
        has_reader = bundled_reader_path(display_name) is not None
        records.append({
            "catalogue_id": catalogue_id,
            "display_name": display_name,
            "digitizer_menu_title": source_name,
            "chapter_count_in_digitizer_menu": len(chapters),
            "menu_chapters": chapters,
            "menu_basis": "Locally archived Octateuch-Index.html; chapter links are menu evidence only, not checked chapter text.",
            "reader_status": "Bundled source-linked Geʽez reader" if has_reader else "CrossWire structure audited; no web-reader text package bundled.",
            "source_ids": ["SRC-034", "SRC-035", "SRC-036", "SRC-058", "SRC-059", "SRC-060", "SRC-079", "SRC-080"] + (["SRC-061"] if display_name == "Exodus" and has_reader else (["SRC-064"] if display_name != "Exodus" and has_reader else [])),
        })

    manifest = {
        "manifest_version": 1,
        "title": "Locally archived Geʽez Octateuch source scope",
        "edition": "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Primus, sive Octateuchus Aethiopicus (Leipzig, 1853–1855), digitized/transcribed by Ran HaCohen.",
        "menu_source_url": "https://www.tau.ac.il/~hacohen/Octateuch/",
        "menu_local_path": "Octateuch-Index.html",
        "menu_sha256": menu_hash,
        "crosswire_module": {
            "module_name": "Geez",
            "module_version": conf["Version"],
            "module_release_date": conf["SwordVersionDate"],
            "source_module_url": "https://crosswire.org/sword/modules/ModInfo.jsp?modName=Geez",
            "module_local_path": "crosswire/Geez.zip",
            "module_sha256": module_hash,
            "structure_audit_path": "crosswire/module-structure-audit.json",
            "structure_audit_sha256": module_audit_hash,
            "structure_audit_scope": "Eleven zText blocks structurally decoded; ten book/chapter sequences match local readers. No verse text exported or collated.",
            "source_type": conf.get("SourceType"),
            "encoding": conf.get("Encoding"),
            "compression": conf.get("CompressType"),
            "module_description": "CrossWire describes this OT module as Dillmann's Ethiopic Octateuch plus Hiob Ludolf's Psalter, digitized by Ran HaCohen. The module's history states it is based on the July 2010 edition.",
        },
        "reuse": {
            "copyright": "© Ran HaCohen",
            "permission": "Copying and distribution are permitted for noncommercial purposes without fee when the copyright and permission notice accompany every copy. Other uses require contacting the copyright owner.",
            "commercial_use": "Not granted.",
            "notice_included_in_module_config": True,
        },
        "boundary": "The local audit checks ZIP integrity, zText block bounds and decompressed lengths, UTF-8 decoding, and OSIS book/chapter identifiers against local reader chapter counts. It exports no verse text and does not establish verse coverage or wording. The source-page HTML and SWORD package identify the same digitizer/corpus, not independent witnesses. Only books marked as bundled reader have source-linked reader packages.",
        "books": records,
    }
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    sources = archive.setdefault("sources", [])
    source_by_id = {source["source_id"]: source for source in sources}
    managed_sources = [
        source_record(
            "SRC-058",
            "CrossWire Bible Society — Geʽez Bible SWORD module (Geez 1.0.1)",
            "https://crosswire.org/sword/modules/ModInfo.jsp?modName=Geez",
            "CrossWire identifies this as the Geʽez Old Testament comprising Dillmann's Ethiopic Octateuch and Hiob Ludolf's Psalter, digitized by Ran HaCohen. Its module record grants noncommercial copying/distribution only when © Ran HaCohen and the permission notice accompany every copy; it does not grant commercial rights. The module configuration describes version 1.0.1, dated 2012-07-10, based on the July 2010 edition. A local structural audit decompresses its zText blocks and checks OSIS chapter identifiers against the HTML-derived reader counts; it exports no verse text and establishes no verse-level completeness or wording.",
            "Publisher metadata and noncommercial terms checked; module structure audited locally; no SWORD verse text added to the reader",
        ),
        source_record(
            "SRC-059",
            "Offline source package — CrossWire Geʽez SWORD module",
            "readers/source/crosswire/Geez.zip",
            f"Local copy of the CrossWire Geez 1.0.1 module package; SHA-256 {module_hash}. The included geez.conf carries the copyright and noncommercial permission notice. The local structure report at readers/source/crosswire/module-structure-audit.json (SHA-256 {module_audit_hash}) confirms block lengths, UTF-8 decoding, and chapter identifiers/counts for eight Octateuch books and Psalms 1–151. It exports no verse text and does not establish verse-level completeness, text equality, or manuscript accuracy.",
            "Offline source package and rights notice preserved; structural blocks audited; no module verse text admitted",
        ),
        source_record(
            "SRC-079",
            "CrossWire — SWORD zVerse source reference",
            "https://www.crosswire.org/sword/apiref/zverse_8cpp_source.html",
            "The official SWORD zVerse implementation is cited only to document the package's index/block structure and block lookup. This archive uses the reference to bound its local structural audit; it does not import or reproduce the SWORD implementation code.",
            "Official software-format reference; not a scripture witness or validation of text accuracy",
        ),
        source_record(
            "SRC-080",
            "Local CrossWire Geʽez module structure audit",
            "readers/source/crosswire/module-structure-audit.json",
            f"Deterministically generated by audit_crosswire_module.py from the locally archived Geez.zip package (SHA-256 {module_hash}); report SHA-256 {module_audit_hash}. It checks archive CRCs, block bounds and decompressed lengths, UTF-8 decoding, OSIS book/chapter identifiers, and chapter-count agreement with local reader records. No verse text is exported or collated.",
            "Local reproducible structure audit; confirms chapter metadata only, not verse coverage, wording, translation, or manuscript completeness",
        ),
        source_record(
            "SRC-060",
            "Local Octateuch chapter-menu inventory (generated from archived index)",
            "readers/source/Octateuch-scope.json",
            f"Deterministically generated by build_octateuch_inventory.py from locally archived Octateuch-Index.html (SHA-256 {menu_hash}) and the local CrossWire package. It records the index's chapter-menu sequence for the eight Octateuch books and explicitly does not verify chapter text, verse coverage, or manuscript completeness.",
            "Local derived scope manifest; chapter-menu evidence only",
        ),
        source_record(
            "SRC-061",
            "University of Tel Aviv — HaCohen Octateuch Exodus chapter pages (locally archived)",
            "readers/source/exodus/index.html",
            f"Local capture of the 40 chapter pages linked by the archived HaCohen Octateuch index; SHA-256 {exodus_capture_hash}. Pages retain the digitizer's Geʽez transcription and visible editorial marks. The capture is not a new translation, manuscript collation, or independent correction of the digitizer's text. Reuse is subject to the noncommercial permission and notice in SRC-036.",
            "All 40 source pages preserved offline; source transcription, not independently collated",
        ),
    ]
    if additional_capture_hash:
        managed_sources.append(source_record(
            "SRC-064",
            "University of Tel Aviv — HaCohen Octateuch chapters Leviticus–Ruth (locally archived)",
            "readers/source/octateuch-additional/index.html",
            f"Local capture of 146 chapter pages linked by the archived HaCohen Octateuch index; capture SHA-256 {additional_capture_hash}. The reader builder checks page status/title, source URL, and source-linked verse labels for each parsed chapter. The text remains HaCohen's transcription, not an independent correction, English translation, or manuscript collation. Reuse is subject to the noncommercial permission and notice in SRC-036.",
            "All 146 source pages preserved offline; source-linked verse labels checked; no independent collation",
        ))
    for record in managed_sources:
        existing = source_by_id.get(record["source_id"])
        if existing and existing != record:
            sources[sources.index(existing)] = record
        elif not existing:
            sources.append(record)

    for catalogue_id, display_name, _, _ in BOOKS[1:]:
        book = next((item for item in archive["catalogue"] if item.get("catalogue_id") == catalogue_id), None)
        if not book:
            raise ValueError(f"Missing catalogue row: {catalogue_id}")
        count = len(menu[display_name])
        book["edition_or_translation"] = "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Primus, sive Octateuchus Aethiopicus, Leipzig, 1853–1855; digitized/transcribed by Ran HaCohen; local CrossWire Geʽez module 1.0.1 identifies its source as the July 2010 digitization. Historical edition; not identified as the current official EOTC printed edition."
        reader_path = ROOT / "readers" / f"{READER_SLUGS[display_name]}-geez.json" if display_name in READER_SLUGS else None
        bundled_reader = json.loads(reader_path.read_text(encoding="utf-8")) if reader_path and reader_path.is_file() else None
        brenton = bundled_reader.get("parallel_translation") if bundled_reader else None
        brenton = brenton if brenton and brenton.get("translation_id") == "exodus-english-brenton-lxx-1851" else None
        if bundled_reader and bundled_reader.get("chapter_count") != count:
            raise ValueError(f"{display_name}: source reader missing or chapter count differs from local menu.")
        book["chapter_count"] = f"{count} chapters listed in the digitizer's local Octateuch menu"
        book["chapter_order_status"] = f"Locally archived index and source page capture list chapters 1–{count} in order; source-linked verse markers were checked in the bundled reader. The same-digitizer SWORD package has matching OSIS chapter IDs/counts; this is structural corroboration, not text collation or independent manuscript evidence." if bundled_reader else f"The locally archived HaCohen menu and same-digitizer SWORD package both list chapters 1–{count} in sequence. The SWORD audit checks chapter IDs only, not verse text or textual completeness."
        book["text_availability_status"] = ("Bundled: Geʽez source transcription + Brenton English research companion (wording unreviewed)" if brenton else "Bundled: source-linked Geʽez reader; no English translation") if bundled_reader else "Source package archived offline; web reader pending"
        book["completeness_status"] = (
            f"Geʽez: {count} source pages and {bundled_reader['verse_marker_count']} linked markers are bundled; transcription is not independently collated. English Brenton research layer: {brenton['chapter_count']} captured pages, {brenton['verse_label_count']} extracted labels, and {sum(len(chapter.get('notes', [])) for chapter in brenton['chapters'])} notes. Exact wording, completeness, translation accuracy, and Geʽez alignment are unreviewed."
            if brenton else
            (f"{count} source pages and {bundled_reader['verse_marker_count']} linked verse markers are bundled; the same-digitizer SWORD module confirms only the OSIS chapter sequence, not verse-level equality. The digitizer's transcription has not been independently collated, and no English translation is bundled." if bundled_reader else f"The local menu and SWORD structural audit list chapters 1–{count}. Module verse text and verse coverage remain unchecked; no web-reader chapter text is bundled.")
        )
        book["rights_status"] = "© Ran HaCohen. Noncommercial copying/distribution only when the copyright and permission notice accompany every copy; commercial reuse is not granted. See the CrossWire source record and the notice retained in the local module package." + (" The separate 1851 Brenton English translation is identified by eBible.org as public domain (SRC-038); that does not establish extraction fidelity." if brenton else "")
        book["reviewer_notes"] = (
            "The edition and Geʽez corpus scope are supported by the digitizer's local menu and CrossWire's module metadata. The Geʽez reader is parsed from locally archived HaCohen chapter HTML, retaining source verse labels and editorial signs; parsing does not independently validate it against print or manuscripts. A distinct Brenton English research layer is parsed from 40 browser-visible eBible.org captures; raw HTML and response bytes are absent, and exact wording, completeness, translation accuracy, and alignment with Geʽez remain unreviewed. It is not presented as verified scripture."
            if brenton else
            ("The edition and corpus scope are supported by the digitizer's local menu and CrossWire's module metadata. The reader is parsed from locally archived HaCohen chapter HTML, retaining source verse labels and editorial signs. The same-digitizer SWORD module's OSIS chapter IDs/counts structurally agree but do not establish verse-level text equality or completeness. No independent print/manuscript collation was done. The bundled text is Geʽez only, not an English translation." if bundled_reader else "The edition and corpus scope are supported by the digitizer's local menu and CrossWire's module metadata. The offline module was structurally decompressed and its chapter IDs checked, but its verse text was not exported to the reader or compared to the captured pages. No verse-level or manuscript collation was done.")
        )
        sources_for_book = book.setdefault("evidence_source_ids", [])
        source_ids = ("SRC-034", "SRC-035", "SRC-036", "SRC-058", "SRC-059", "SRC-060", "SRC-079", "SRC-080", "SRC-061") if display_name == "Exodus" else (("SRC-034", "SRC-035", "SRC-036", "SRC-058", "SRC-059", "SRC-060", "SRC-079", "SRC-080", "SRC-064") if bundled_reader else ("SRC-034", "SRC-035", "SRC-036", "SRC-058", "SRC-059", "SRC-060", "SRC-079", "SRC-080"))
        for source_id in source_ids:
            if source_id not in sources_for_book:
                sources_for_book.append(source_id)
        if brenton:
            for source_id in ("SRC-038", "SRC-074", "SRC-075", "SRC-076"):
                if source_id not in sources_for_book:
                    sources_for_book.append(source_id)

    genesis = next((item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-001"), None)
    if not genesis:
        raise ValueError("Missing catalogue row: eotc-001")
    genesis_evidence = genesis.setdefault("evidence_source_ids", [])
    for source_id in ("SRC-079", "SRC-080"):
        if source_id not in genesis_evidence:
            genesis_evidence.append(source_id)

    ARCHIVE.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Recorded {len(records)} Octateuch menu scopes, {len(managed_sources)} managed source records, and local module SHA-256 {module_hash}."
    )


if __name__ == "__main__":
    main()
