"""Reproducibly parse the locally captured TAU Ge'ez Obadiah text page."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "obadiah-tau-2010"
READER_PATH = ROOT / "readers" / "obadiah-geez-bachmann-theot.json"
LAYER_PATH = ROOT / "examples" / "obadiah-geez-bachmann-theot-layer.json"
SOURCE_ID = "SRC-186"
CANON_ID = "eotc-ot-37"
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"


class ObadiahTextParser(HTMLParser):
    """Keep text after each BibleGateway Obadiah 1:n label, in page order."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: str | None = None
        self.parts: list[str] = []
        self.units: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        match = re.search(r"search=Oba\+1%3A(\d+)", href)
        if match:
            self._finish()
            self.current = match.group(1)
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.parts.append(data)

    def close(self) -> None:
        self._finish()
        super().close()

    def _finish(self) -> None:
        if self.current is None:
            return
        text = re.sub(r"\s+", " ", "".join(self.parts)).strip()
        # The linked label itself is visible in the original HTML. Store it
        # once as source_marker, rather than duplicating it in the verse body.
        text = re.sub(rf"^{re.escape(self.current)}\s+", "", text, count=1)
        self.units.append((self.current, text))
        self.current = None
        self.parts = []


def build() -> tuple[dict, dict]:
    source_path = CAPTURE / "obadiah-text.html"
    capture_manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    for item in capture_manifest["files"]:
        captured_path = CAPTURE / item["path"]
        captured_bytes = captured_path.read_bytes()
        if (item.get("http_status") != 200 or len(captured_bytes) != item["size_bytes"]
                or hashlib.sha256(captured_bytes).hexdigest() != item["sha256"]):
            raise ValueError(f"Captured Obadiah source asset failed its local checksum/response check: {item['path']}.")
    raw = source_path.read_bytes()
    capture_record = next(item for item in capture_manifest["files"] if item["path"] == source_path.name)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != capture_record["sha256"] or len(raw) != capture_record["size_bytes"]:
        raise ValueError("Captured Obadiah source page does not match its retained capture manifest.")

    parser = ObadiahTextParser()
    parser.feed(raw.decode("utf-8"))
    parser.close()
    expected = [str(index) for index in range(1, 22)]
    labels = [number for number, _ in parser.units]
    if labels != expected or any(not text for _, text in parser.units):
        raise ValueError(f"Obadiah source labels must be exactly 1–21 in order; observed {labels!r}.")
    chapters = [{
        "chapter": 1,
        "source_marker": "1",
        "verses": [
            {"number": int(number), "source_marker": number, "text": text}
            for number, text in parser.units
        ],
    }]
    rights_notice = (
        "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and this permission notice appear in all copies of the text. For other uses, please contact the copyright owner."
    )
    source_ids = ["SRC-029", "SRC-034", "SRC-036", "SRC-153", SOURCE_ID]
    reader = {
        "reader_id": "obadiah-geez-bachmann-theot",
        "text_origin": "source_transcription",
        "canon_id": CANON_ID,
        "title": "Obadiah — Geʽez Bachmann / THEOT transcription",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "script_code": "Ethi",
        "section_label": "Chapter",
        "source_ids": source_ids,
        "edition": "Johannes Bachmann (ed.), Dodekapropheton Aethiopum oder die zwölf kleinen Propheten der aethiopischen Bibelübersetzung, Heft I: Der Prophet Obadia, Halle a.S., 1892; text transcription by Samuel Aldridge, Jeremy Brown, Steve Delamarter, Garry Jost, and Shaun Short for the Textual History of the Ethiopic Old Testament (THEOT) Project, February 2013.",
        "edition_scope": "The local text derives from TAU's digital transcription of Bachmann's 1892 critical edition. The source information page describes it as the Ethiopic Book of Obadiah. This historical witness is not identified as the current official EOTC printed edition, and no manuscript or print-edition collation is claimed.",
        "transcription_note": "Verse bodies are parsed from the single captured TAU Text HTML page. HTML whitespace is normalized to single spaces; linked source verse labels are retained as separate source_marker strings. The original raw HTML page is stored alongside the reader and checked by SHA-256. No wording was translated or silently emended.",
        "editorial_signs_note": "Visible Geʽez punctuation and editorial signs in the text are retained in the extracted text. The source page offers image-page selectors 1 and + (page 5), but these facsimile pages and Bachmann's critical notes are not bundled. The raw Text HTML remains the extraction authority for this reader.",
        "chapter_structure_note": "The TAU index provides one Text option. The captured text page contains sequential linked labels Obadiah 1:1–1:21. One chapter with 21 source labels is established for the captured digital text page only; this does not independently establish completeness of the print edition or manuscript tradition.",
        "rights_classification": "permission_limited",
        "copyright_notice": rights_notice,
        "commercial_use": "Not granted by the cited notice. Noncommercial use only, with the copyright and permission notice accompanying every copy; contact the rights holder for other uses.",
        "license_id": None,
        "license_url": None,
        "chapter_count": 1,
        "unit_count": len(parser.units),
        "unit_label": "source-linked verse label",
        "source_numbered_unit_count": len(parser.units),
        "source_unnumbered_unit_count": 0,
        "verification_status": "Automated local audit confirms the retained TAU Text HTML checksum and all 21 nonempty sequential source-linked labels (1–21), parsed in order. This verifies local source-to-reader extraction and the captured page's chapter structure only. No collation against the 1892 print, critical notes, image facsimile, or manuscript was performed.",
        "source_pages": "One local HTML source page: readers/source/obadiah-tau-2010/obadiah-text.html. The source index lists one Text option and image pages 1 and + (page 5); those image pages are not included.",
        "source_sha256": digest,
        "chapters": chapters,
    }

    reader_serialized = (json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    reader_sha = hashlib.sha256(reader_serialized).hexdigest()
    record_id = f"{BASE}/layer/obadiah-geez-bachmann-theot"
    work_id = f"{BASE}/work/obadiah-eotc"
    witness_id = f"{BASE}/witness/obadiah-bachmann-1892-theot-2013"
    layer = {
        "schema_version": 2,
        "record_id": record_id,
        "work_id": work_id,
        "labels": [
            {"value": "Obadiah — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"},
            {"value": "ዘዓብድዩ ፡", "language_tag": "gez", "label_type": "original_form"},
        ],
        "tradition_assertions": [{
            "tradition_id": f"{BASE}/tradition/eotc",
            "canon_id": f"{BASE}/canon/{CANON_ID}",
            "mapping_state": "asserted_by_source",
            "evidence_source_ids": ["SRC-029", "SRC-153"],
            "notes": "The Church's cited English 81-entry list names Obadiah, and TAU identifies this as an Ethiopic Book of Obadiah. This is a title-level crosswalk only; it does not establish identity with a current EOTC printed edition or a particular manuscript recension.",
        }],
        "witness": {
            "witness_id": witness_id,
            "witness_type": "digital_edition",
            "title": "Bachmann 1892 Ethiopic Obadiah critical edition; THEOT Project text transcription (2013), displayed by TAU",
            "date_statement": "Printed critical edition 1892; THEOT transcription February 2013; TAU information page dated April 2010",
            "repository_or_publisher": "Tel Aviv University website; Textual History of the Ethiopic Old Testament (THEOT) Project",
            "shelfmark_or_edition_id": "Heft I: Der Prophet Obadia",
            "editorial_policy": "The source transcription follows Bachmann's critical edition. The source page links verse labels to external navigation references; local extraction retains verse labels and raw HTML. Critical apparatus and facsimile images are not included.",
            "source_ids": ["SRC-034", "SRC-036", "SRC-153", SOURCE_ID],
        },
        "layer_type": "source_text_transcription",
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "language_name_as_recorded": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "basis_path": ["gez"],
        "agents": [
            {"role": "editor", "name": "Johannes Bachmann", "authority_or_affiliation": None, "source_ids": ["SRC-153"]},
            *[{"role": "transcriber", "name": name, "authority_or_affiliation": "THEOT Project", "source_ids": ["SRC-153"]} for name in ("Samuel Aldridge", "Jeremy Brown", "Steve Delamarter", "Garry Jost", "Shaun Short")],
        ],
        "content_package": {"uri": "../readers/obadiah-geez-bachmann-theot.json", "media_type": "application/json", "sha256": reader_sha, "format_version": "1"},
        "coverage": {
            "extent_state": "complete_for_declared_edition",
            "extent_basis": "source_inventory",
            "unit_count": len(parser.units),
            "structure_description": "The captured TAU Text option is a single page with 21 sequential source-linked labels for chapter 1, verses 1–21. Complete for this locally captured digital Text page only; not a print-edition or manuscript completeness claim.",
            "missing_or_lacunose_ranges": [],
            "supplements_and_editorial_signs": "HTML whitespace is normalized; source markers are stored separately; visible Ethiopic punctuation and signs remain. Raw HTML is retained. No critical apparatus or facsimile pages are included.",
            "numbering_policy": "Preserve the exact source labels 1–21 as strings and integer navigation numbers. They are the source page's labels, not a reviewed alignment to other textual witnesses.",
        },
        "rights": {
            "status": "permission_limited",
            "statement": rights_notice,
            "license_id": None,
            "rights_holder": "Ran HaCohen",
            "attribution_required": True,
            "territory_or_term_limits": "Noncommercial purposes only under the source site's notice; other uses require contacting the rights holder. This is not an open license or blanket commercial grant.",
            "evidence_source_ids": ["SRC-036", SOURCE_ID],
        },
        "review_dimensions": [
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "Retained source page contains one chapter and 21 sequential linked verse labels; parser output is checked against each source label and raw-page checksum.", "reviewer": None, "review_method": "automated_validation", "review_process": "Obadiah capture parser and archive build", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID, "SRC-153"], "notes": "Source-to-reader extraction and structure only; no independent collation or print completeness claim."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No collation against Bachmann's 1892 printed edition, critical notes, image pages, or manuscript witnesses.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-153", SOURCE_ID], "notes": "The source identifies the edition and transcribers; this archive has not checked their wording against the print or manuscripts."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "TAU general and Obadiah source notices authorize noncommercial reuse with notices attached.", "reviewer": None, "review_method": "source_inspection", "review_process": "Inspected source notice and retained it in the local capture package.", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-036", SOURCE_ID], "notes": "Commercial reuse is not granted by the notice."},
        ],
        "publication_state": "bundled",
        "community_access_note": None,
        "additional_notes": "This record translates no wording. The English title is metadata; the bundled text layer is Geʽez.",
    }
    return reader, layer


def write() -> tuple[dict, dict]:
    reader, layer = build()
    READER_PATH.write_bytes((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    LAYER_PATH.write_bytes((json.dumps(layer, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return reader, layer


if __name__ == "__main__":
    reader, layer = write()
    print(f"Built Obadiah reader: {reader['chapter_count']} chapter, {reader['unit_count']} source labels; layer {layer['record_id']}.")
