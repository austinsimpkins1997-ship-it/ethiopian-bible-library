"""Build a source-captured Geʽez Sirach reader with labels retained as observed."""
from __future__ import annotations

import copy
import hashlib
import json
from archive_manifest import write_text_atomically
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "sirach-tau-2026"
READER_PATH = ROOT / "readers" / "sirach-geez-dillmann-hacohen-tau.json"
LAYER_PATH = ROOT / "examples" / "sirach-geez-dillmann-hacohen-tau-layer.json"
READER_ID = "sirach-geez-dillmann-hacohen-tau"
CANON_ID = "eotc-ot-45"
SOURCE_ID = "SRC-318"
CORPUS_LEAD_NOTE = (
    "TAU's Sirach component has been captured and bundled separately as the 51-page reader "
    + READER_ID
    + "; this does not mean the other books listed on the 1894 volume page are bundled."
)
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
NOTICE = (
    "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any "
    "NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and "
    "this permission notice appear in all copies of the text. For other uses, please contact the copyright owner."
)


class IndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict] = []
        self.form: dict | None = None
        self.select: list[dict[str, str]] | None = None
        self.option: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag.lower() == "form":
            self.form = {"title": values.get("title", ""), "selects": []}
            self.forms.append(self.form)
        elif tag.lower() == "select" and self.form is not None:
            self.select = []
        elif tag.lower() == "option" and self.select is not None:
            self._finish_option()
            self.option = {"value": values.get("value", ""), "label": ""}

    def handle_data(self, data: str) -> None:
        if self.option is not None:
            self.option["label"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "option":
            self._finish_option()
        elif tag.lower() == "select" and self.select is not None:
            self._finish_option()
            if self.form is not None:
                self.form["selects"].append(self.select)
            self.select = None
        elif tag.lower() == "form":
            self._finish_option()
            self.form = None

    def _finish_option(self) -> None:
        if self.option is not None and self.select is not None:
            self.option["label"] = self.option["label"].strip()
            self.select.append(self.option)
        self.option = None


class SirachPageParser(HTMLParser):
    """Retain each number shown in TAU's small-font verse-label spans."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_paragraph = False
        self.marker_depth = 0
        self.marker_parts: list[str] = []
        self.current_marker: str | None = None
        self.body_parts: list[str] = []
        self.rows: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag == "p":
            self.in_paragraph = True
        elif tag == "br" and self.in_paragraph and self.current_marker is not None:
            self.body_parts.append(" ")
        elif tag == "span":
            style = values.get("style", "").lower().replace(" ", "")
            if self.marker_depth:
                self.marker_depth += 1
            elif self.in_paragraph and "font-size:70%" in style:
                self.marker_depth = 1
                self.marker_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "span" and self.marker_depth:
            self.marker_depth -= 1
            if self.marker_depth == 0:
                candidate = "".join(self.marker_parts).strip()
                if candidate.isdecimal():
                    self._finish_row()
                    self.current_marker = candidate
                    self.body_parts = []
                elif self.current_marker is not None:
                    self.body_parts.append(candidate)
                self.marker_parts = []
        elif tag == "p":
            self.in_paragraph = False

    def handle_data(self, data: str) -> None:
        if self.marker_depth:
            self.marker_parts.append(data)
        elif self.in_paragraph and self.current_marker is not None:
            self.body_parts.append(data)

    def close(self) -> None:
        self._finish_row()
        super().close()

    def _finish_row(self) -> None:
        if self.current_marker is not None:
            body = re.sub(r"\s+", " ", "".join(self.body_parts)).strip()
            if body:
                self.rows.append((self.current_marker, body))
        self.current_marker = None
        self.body_parts = []


def _checked_manifest() -> tuple[dict, dict[int, list[tuple[str, str]]]]:
    manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        raw = (CAPTURE / item["path"]).read_bytes()
        if (item.get("http_status") != 200 or len(raw) != item["size_bytes"]
                or hashlib.sha256(raw).hexdigest() != item["sha256"]):
            raise ValueError(f"Sirach capture failed HTTP/size/SHA validation: {item['path']}")
    index = IndexParser()
    index.feed((CAPTURE / "tau-ethiopic-index.html").read_text(encoding="utf-8"))
    forms = [form for form in index.forms if "ecclesiasticus" in form["title"].lower()]
    if len(forms) != 1 or not forms[0]["selects"]:
        raise ValueError("TAU index does not expose exactly one Ecclesiasticus/Sirach menu.")
    text_options = forms[0]["selects"][0]
    chapter_options = [
        option for option in text_options
        if option["label"].isdecimal()
        and re.fullmatch(r"Apocryphi/Sir \d+\.html", option["value"])
    ]
    expected = [f"Apocryphi/Sir {n}.html" for n in range(1, 52)]
    if [option["value"] for option in chapter_options] != expected:
        raise ValueError("TAU's captured Sirach text menu no longer lists exactly pages 1–51 in order.")
    if [option["label"] for option in chapter_options] != [str(n) for n in range(1, 52)]:
        raise ValueError("TAU's captured Sirach chapter labels differ from the 1–51 text-page targets.")
    info = (CAPTURE / "sirach-information.html").read_text(encoding="utf-8")
    apocrypha = (CAPTURE / "apocryphi-information.html").read_bytes().decode("utf-8", errors="replace")
    rights = (CAPTURE / "tau-general-information.html").read_bytes().decode("utf-8", errors="replace")
    if "transcribed by Ran HaCohen" not in info or "February, 2026" not in info:
        raise ValueError("Book-specific TAU page no longer supports Ran HaCohen attribution/date.")
    if "Wisdom of the Son of Sirach" not in apocrypha or "1894" not in apocrypha:
        raise ValueError("TAU apocrypha page no longer supports the Sirach title and Dillmann edition.")
    if "NONCOMMERCIAL" not in rights or "Ran HaCohen" not in rights:
        raise ValueError("TAU site-wide copyright terms or required attribution are missing from capture.")

    by_chapter: dict[int, list[tuple[str, str]]] = {}
    for chapter in range(1, 52):
        filename = f"sirach-chapter-{chapter}.html"
        html = (CAPTURE / filename).read_text(encoding="utf-8")
        if f"<title>Sirach {chapter}</title>" not in html:
            raise ValueError(f"Source page title does not identify Sirach chapter {chapter}.")
        parser = SirachPageParser()
        parser.feed(html)
        parser.close()
        if not parser.rows or any(not marker.isdecimal() or not body for marker, body in parser.rows):
            raise ValueError(f"Sirach chapter {chapter} has no labeled nonempty source units.")
        by_chapter[chapter] = parser.rows
    return manifest, by_chapter


def _label_gaps(by_chapter: dict[int, list[tuple[str, str]]]) -> list[dict]:
    gaps = []
    for chapter, rows in by_chapter.items():
        labels = [int(marker) for marker, _ in rows]
        if labels:
            missing = [str(n) for n in range(1, max(labels) + 1) if n not in labels]
            if missing:
                gaps.append({"chapter": chapter, "unobserved_source_markers": missing})
    return gaps


def _label_order_anomalies(by_chapter: dict[int, list[tuple[str, str]]]) -> list[dict]:
    anomalies = []
    for chapter, rows in by_chapter.items():
        labels = [int(marker) for marker, _ in rows]
        reversals = [
            {"source_order": index + 1, "previous_label": labels[index - 1], "label": label}
            for index, label in enumerate(labels[1:], start=1)
            if label < labels[index - 1]
        ]
        if reversals:
            anomalies.append({"chapter": chapter, "reversals": reversals})
    return anomalies


def build() -> tuple[dict, dict]:
    manifest, by_chapter = _checked_manifest()
    manifest_files = {item["path"]: item for item in manifest["files"]}
    label_gaps = _label_gaps(by_chapter)
    label_order_anomalies = _label_order_anomalies(by_chapter)
    total = sum(len(rows) for rows in by_chapter.values())
    chapters = []
    for chapter, rows in by_chapter.items():
        page_path = CAPTURE / f"sirach-chapter-{chapter}.html"
        page_meta = manifest_files[f"sirach-chapter-{chapter}.html"]
        chapters.append({
            "chapter": chapter,
            "source_marker": str(chapter),
            "source_sha256": hashlib.sha256(page_path.read_bytes()).hexdigest(),
            "source_page_title": f"Sirach {chapter}",
            "verses": [
                {"number": int(marker), "source_marker": marker, "text": body}
                for marker, body in rows
            ],
        })
    pages = ", ".join(f"sirach-chapter-{n}.html" for n in range(1, 52))
    gap_text = "; ".join(
        f"chapter {item['chapter']}: {', '.join(item['unobserved_source_markers'])}"
        for item in label_gaps
    ) or "none observed"
    reader = {
        "reader_id": READER_ID,
        "text_origin": "source_transcription",
        "canon_id": CANON_ID,
        "title": "Sirach (Ecclesiasticus) — Geʽez Dillmann / HaCohen transcription",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "script_code": "Ethi",
        "section_label": "Chapter",
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-098", "SRC-100", SOURCE_ID],
        "edition": "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Quintus, Berlin, 1894; TAU identifies this as Ecclesiasticus (Wisdom of the Son of Sirach). Ran HaCohen is credited by the book-specific TAU page with transcribing the text (February 2026).",
        "edition_scope": "The local reader transcribes all 51 text pages offered by TAU's captured Sirach menu (chapter labels 1–51). TAU identifies the printed edition as Dillmann 1894 and the work as Ecclesiasticus / Wisdom of the Son of Sirach. No comparison with the printed edition, its images, manuscripts, or another Geʽez text has been performed. The tentative title-family link to the Church list's ‘Book of Joshua the Son of Sirac’ is not proof of exact work identity, canon status, or current EOTC edition identity.",
        "transcription_note": "The parser extracts visible Ethiopic content after each small-font numeric source label. It normalizes HTML whitespace to single spaces, preserves every displayed label as source_marker, and retains source HTML for every page with response metadata and SHA-256. It does not translate, emend, supply omitted labels, or align this text to another witness.",
        "additional_notes": "This is a Geʽez source transcription, not an English translation. No English translation is included.",
        "editorial_signs_note": "Visible Ethiopic characters, punctuation, and parenthetical material are retained as parsed. Formatting, images, Latin/English text, footnote apparatus, and external BibleGateway content are excluded; raw HTML pages remain in the source capture for inspection.",
        "chapter_structure_note": f"The captured TAU index lists 51 text pages, numbered 1–51; all 51 page titles and their nonempty source units were checked. Observed source-label discontinuities are preserved as gaps and are not treated as proof of textual lacunae or supplied from another edition. Gaps observed: {gap_text}.",
        "rights_classification": "permission_limited",
        "copyright_notice": NOTICE,
        "commercial_use": "TAU permits noncommercial copying/distribution only when the stated Ran HaCohen copyright and permission notice accompanies every copy; other uses require contacting the copyright owner. No commercial permission or open-content license is asserted. Underlying edition rights were not independently assessed.",
        "license_id": None,
        "license_url": None,
        "chapter_count": len(chapters),
        "unit_count": total,
        "unit_label": "visible numeric label in TAU's Geʽez Sirach chapter HTML",
        "source_numbered_unit_count": total,
        "source_unnumbered_unit_count": 0,
        "source_label_gaps": label_gaps,
        "source_label_order_anomalies": label_order_anomalies,
        "verification_status": f"Automated local validation confirms all {len(manifest['files'])} retained source HTML files match response status, byte length, and SHA-256. The captured TAU index lists text pages 1–51; each corresponding page title was checked and {total} nonempty numbered units were extracted. Chapter-local label discontinuities are recorded without interpolation. These checks establish source capture and extraction structure only; no human Geʽez proofreading, print/image collation, manuscript collation, completeness audit beyond TAU's digital menu, independent canon crosswalk, or accuracy review was performed.",
        "source_pages": f"51 source HTML pages retained in readers/source/sirach-tau-2026: {pages}; the capture manifest also preserves the TAU index, book-specific information, collection description, and general copyright/permission notice.",
        "chapters": chapters,
    }
    reader_bytes = (json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    reader_sha = hashlib.sha256(reader_bytes).hexdigest()
    base_layer = json.loads((ROOT / "examples" / "zephaniah-geez-lofgren-hacohen-layer.json").read_text(encoding="utf-8"))
    layer = copy.deepcopy(base_layer)
    layer.update({
        "record_id": f"{BASE}/layer/{READER_ID}",
        "work_id": f"{BASE}/work/sirach-dillmann-1894",
        "labels": [
            {"value": "Sirach (Ecclesiasticus) — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"},
            {"value": "ጥበበ ፡ ሲራክ ።", "language_tag": "gez", "label_type": "original_form"},
        ],
        "tradition_assertions": [{
            "tradition_id": f"{BASE}/tradition/eotc",
            "canon_id": f"{BASE}/canon/{CANON_ID}",
            "mapping_state": "uncertain",
            "evidence_source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-098", "SRC-100", SOURCE_ID],
            "notes": "The Church-list label ‘Book of Joshua the Son of Sirac’ and TAU's Ecclesiasticus / Wisdom of the Son of Sirach title indicate a plausible Sirach title-family link. The exact work identity, Church-list crosswalk, canon status of this 1894 edition, and relation to the current EOTC printed text are not established.",
        }],
        "witness": {
            "witness_id": f"{BASE}/witness/sirach-dillmann-1894-hacohen-tau-2026",
            "witness_type": "digital_edition",
            "title": "Dillmann 1894 Ethiopic Ecclesiasticus; TAU text transcribed by Ran HaCohen (2026)",
            "date_statement": "Printed critical edition Berlin 1894; TAU Sirach text page dated February 2026",
            "repository_or_publisher": "Tel Aviv University website; transcription attributed to Ran HaCohen",
            "shelfmark_or_edition_id": "Ecclesiasticus / Wisdom of the Son of Sirach in Dillmann, Veteris Testamenti Aethiopici Tomus Quintus (1894)",
            "editorial_policy": "TAU identifies the printed critical edition and credits Ran HaCohen with transcribing its text. The archive preserves all 51 pages offered by the current captured index and their visible source labels. No print collation, witness inventory review, or human transcription review has been conducted.",
            "source_ids": ["SRC-034", "SRC-036", "SRC-098", "SRC-100", SOURCE_ID],
        },
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "language_name_as_recorded": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "basis_path": ["gez"],
        "agents": [
            {"role": "editor", "name": "August Dillmann", "authority_or_affiliation": "1894 critical-edition title-page attribution as reported by TAU", "source_ids": ["SRC-098"]},
            {"role": "transcriber", "name": "Ran HaCohen", "authority_or_affiliation": "Tel Aviv University website; credited transcriber", "source_ids": [SOURCE_ID]},
        ],
        "content_package": {"uri": f"../readers/{READER_ID}.json", "media_type": "application/json", "sha256": reader_sha, "format_version": "1"},
        "coverage": {
            "extent_state": "complete_for_declared_edition",
            "extent_basis": "source_inventory",
            "unit_count": total,
            "structure_description": f"All 51 chapter text pages offered by the captured TAU index were captured and parsed; {total} nonempty labeled units were observed. Source-label gaps are retained in the reader metadata ({gap_text}); these do not establish missing textual content. This describes the menu-defined digital scope only, not print or manuscript completeness.",
            "missing_or_lacunose_ranges": [],
            "supplements_and_editorial_signs": "No wording was supplied or aligned. Raw source pages are retained. The digital parser preserves displayed Geʽez wording and parenthetical matter while normalizing whitespace; source labels remain explicit. Images, translations, and critical apparatus are excluded.",
            "numbering_policy": "Preserve the 51 chapter page labels and each numeric label exactly as displayed. Keep within-chapter gaps and any repeats as source observations; do not infer, renumber, or align missing labels.",
        },
        "rights": {
            "status": "permission_limited",
            "statement": NOTICE,
            "license_id": None,
            "rights_holder": "Ran HaCohen (TAU site notice)",
            "attribution_required": True,
            "territory_or_term_limits": "TAU notice grants noncommercial use only with the copyright and permission notice attached; other uses require contacting the rights holder. This is not an open license. Underlying 1894 critical-edition rights have not been independently assessed.",
            "evidence_source_ids": ["SRC-036", "SRC-098", "SRC-100", SOURCE_ID],
        },
        "review_dimensions": [
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": f"The captured index contains exactly 51 text targets in order, and all 51 captured files have matching source page titles, HTTP status, byte lengths, and hashes. {total} nonempty numbered units were extracted; gaps are recorded.", "reviewer": None, "review_method": "automated_validation", "review_process": "Sirach TAU capture/parser and archive build", "reviewed_at": manifest_files["sirach-information.html"]["captured_at"][:10], "evidence_source_ids": [SOURCE_ID], "notes": "Menu-to-capture and extraction structure only; no print completeness or wording accuracy claim."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No collation against the 1894 printed edition, image pages, other manuscripts, or current EOTC text.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-098", SOURCE_ID], "notes": "TAU credits Ran HaCohen with transcription; this archive has not independently assessed it."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "TAU book-specific transcription attribution, collection bibliographic scope, and site-wide noncommercial notice were captured locally.", "reviewer": None, "review_method": "source_inspection", "review_process": "Retained TAU's book-specific page and required notice.", "reviewed_at": manifest_files["tau-general-information.html"]["captured_at"][:10], "evidence_source_ids": ["SRC-036", "SRC-098", "SRC-100", SOURCE_ID], "notes": "Noncommercial with notice only; no open or commercial grant is asserted."},
        ],
        "publication_state": "bundled",
        "community_access_note": None,
        "additional_notes": "The reader contains Geʽez source transcription only. No English translation is included; no machine translation or generated wording was added. Church-list mapping remains uncertain.",
    })
    return reader, layer


def write() -> tuple[dict, dict]:
    reader, layer = build()
    READER_PATH.write_bytes((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    LAYER_PATH.write_bytes((json.dumps(layer, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = archive["sources"]
    capture_manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    capture_files = {item["path"]: item for item in capture_manifest["files"]}
    source = {
        "source_id": SOURCE_ID,
        "source_name": "Tel Aviv University — Ethiopic Sirach text and transcription information (Dillmann 1894; HaCohen 2026)",
        "url": "https://www.tau.ac.il/~hacohen/Apocryphi/InformationSir.html",
        "inspection_and_limitations": "TAU's book-specific page (accessed and captured 2026-10-25) says Dillmann's text version was transcribed by Ran HaCohen and is dated February 2026. The captured main index calls the title Ecclesiasticus (Wisdom of the Son of Sirach) and lists 51 text targets; all 51 corresponding chapter pages were retained with response status, byte length, capture time, and SHA-256. This supports the declared digital page inventory and attribution only. The archive has not checked wording against print/images/manuscripts, audited verse completeness, established current EOTC edition identity, or proven an exact crosswalk to the Church list's Book of Joshua the Son of Sirac. TAU's noncommercial terms and notice are separately recorded in SRC-036 and SRC-100; no commercial or open license is asserted.",
        "archive_status": "51-page source transcription bundled with raw page captures and required notice; extraction structure checked; text accuracy, exact canon mapping, and print completeness unverified",
        "local_metadata_url": "readers/source/sirach-tau-2026/sirach-information.utf8.html",
        "local_capture_manifest_url": "readers/source/sirach-tau-2026/SOURCE-CAPTURE.json",
        "local_snapshot_path": "readers/source/sirach-tau-2026/sirach-information.html",
        "local_snapshot_sha256": capture_files["sirach-information.html"]["sha256"],
        "local_snapshot_status": "byte-exact original capture; declares windows-1252; not a scripture text layer",
        "local_snapshot_note": "Captured 2026-10-25T23:36:24Z from https://www.tau.ac.il/~hacohen/Apocryphi/InformationSir.html; raw bytes retained unchanged. Sanitized UTF-8 display derivative: readers/source/sirach-tau-2026/sirach-information.utf8.html (SHA-256 83564027bf41bbf4118455288017e46c20bdcb929bcfe4c3da7cac6e1cb18dd7); active scripts and embedded/network content removed or blocked."
    }
    sources[:] = [s for s in sources if s.get("source_id") != SOURCE_ID]
    sources.append(source)
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    language = next(x for x in registry["languages"] if x["language_tag"] == "gez")
    language["source_ids"] = list(dict.fromkeys(language.get("source_ids", []) + reader["source_ids"]))
    language["records"] = [r for r in language.get("records", []) if r.get("reader_id") != READER_ID]
    language["records"].append({
        "canon_id": CANON_ID,
        "reader_id": READER_ID,
        "layer_role": "source_text_transcription",
        "status": "bundled",
        "basis_language_tag": "gez",
        "basis_description": "TAU identifies Dillmann's 1894 Ethiopic Ecclesiasticus (Wisdom of the Son of Sirach); the book page credits Ran HaCohen with the February 2026 transcription. This is a provisional title-family link to the Church-list Book of Joshua the Son of Sirac, not a verified EOTC edition crosswalk.",
        "rights_status": "TAU notice permits noncommercial copying only with the Ran HaCohen copyright and permission notice. No open or commercial license is asserted; underlying edition rights are not independently assessed.",
        "rights_classification": "permission_limited",
        "source_ids": reader["source_ids"],
    })
    language["records"].sort(key=lambda r: r.get("reader_id") or "")
    for lead in registry.get("corpus_leads", []):
        if lead.get("corpus_id") == "taue-apocryphi-dillmann-1894":
            lead["source_ids"] = list(dict.fromkeys(lead.get("source_ids", []) + [SOURCE_ID]))
            notes = lead.get("notes", "").strip()
            while notes.endswith(CORPUS_LEAD_NOTE):
                notes = notes[: -len(CORPUS_LEAD_NOTE)].rstrip()
            lead["notes"] = f"{notes} {CORPUS_LEAD_NOTE}".strip()
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return reader, layer


if __name__ == "__main__":
    result, _layer = write()
    print(f"Built {result['reader_id']}: {result['chapter_count']} menu-listed chapters, {result['unit_count']} observed labeled units, {len(result['source_label_gaps'])} chapters with unobserved labels; link remains provisional.")
