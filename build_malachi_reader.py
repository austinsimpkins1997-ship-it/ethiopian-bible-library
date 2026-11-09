"""Build a bounded Geʽez Malachi reader from the retained TAU text pages."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "malachi-tau-2018"
READER_PATH = ROOT / "readers" / "malachi-geez-lofgren-ghebre-tau.json"
LAYER_PATH = ROOT / "examples" / "malachi-geez-lofgren-ghebre-layer.json"
READER_ID = "malachi-geez-lofgren-ghebre-tau"
CANON_ID = "eotc-ot-44"
SOURCE_ID = "SRC-195"
LABEL_EXTENTS = {1: 14, 2: 17, 3: 18, 4: 6}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: tuple[int, str] | None = None
        self.parts: list[str] = []
        self.rows: list[tuple[int, str, str]] = []
        self.paragraph = False
        self.paragraph_parts: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "p":
            self.paragraph = True
            self.paragraph_parts = []
        if tag == "a":
            match = re.search(r"search=Mal\+(\d+)%3A(\d+)", dict(attrs).get("href") or "")
            if match:
                self._finish_unit()
                self.current = (int(match.group(1)), match.group(2))
                self.parts = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.parts.append(data)
        if self.paragraph:
            self.paragraph_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self._finish_unit()
        if tag == "p" and self.paragraph:
            value = re.sub(r"\s+", " ", "".join(self.paragraph_parts)).strip()
            if value:
                self.paragraphs.append(value)
            self.paragraph = False

    def close(self) -> None:
        self._finish_unit()
        super().close()

    def _finish_unit(self) -> None:
        if self.current is None:
            return
        chapter, marker = self.current
        body = re.sub(r"\s+", " ", "".join(self.parts)).strip()
        body = re.sub(rf"^{re.escape(marker)}\s+", "", body, count=1)
        self.rows.append((chapter, marker, body))
        self.current = None
        self.parts = []


def _capture() -> tuple[dict, dict[int, list[tuple[str, str]]], str]:
    manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        raw = (CAPTURE / item["path"]).read_bytes()
        if (item.get("http_status") != 200 or len(raw) != item["size_bytes"]
                or hashlib.sha256(raw).hexdigest() != item["sha256"]):
            raise ValueError(f"Malachi source capture failed status/size/SHA-256 check: {item['path']}")
    by_chapter: dict[int, list[tuple[str, str]]] = {}
    for chapter, expected_count in LABEL_EXTENTS.items():
        parser = PageParser()
        parser.feed((CAPTURE / f"malachi-chapter-{chapter}.html").read_bytes().decode("ascii"))
        parser.close()
        rows = [(marker, body) for ch, marker, body in parser.rows if ch == chapter]
        expected = [str(i) for i in range(1, expected_count + 1)]
        if ([marker for marker, _ in rows] != expected or any(not body for _, body in rows)
                or any(ch != chapter for ch, _, _ in parser.rows)):
            raise ValueError(f"Malachi page {chapter} did not yield the expected nonempty labels {expected}")
        if not rows:
            raise ValueError(f"Malachi page {chapter} has no parseable source-linked units")
        by_chapter[chapter] = rows
    last = PageParser()
    last.feed((CAPTURE / "malachi-chapter-4.html").read_bytes().decode("ascii"))
    last.close()
    # The source page places a doxological closing after verse 6 without verse labels.
    # Preserve it as an explicitly unnumbered continuation in the reader.
    unnumbered = [p for p in last.paragraphs if "ለይኩን" in p or "ለዓለም" in p or "አሜን" in p]
    closing = " ".join(unnumbered)
    if not closing:
        raise ValueError("Malachi chapter 4 unnumbered closing text was not captured")
    return manifest, by_chapter, closing


def build() -> tuple[dict, dict]:
    manifest, by_chapter, closing = _capture()
    file_map = {item["path"]: item for item in manifest["files"]}
    total = sum(map(len, by_chapter.values()))
    notice = ("© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any "
              "NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and "
              "this permission notice appear in all copies of the text. For other uses, please contact the copyright owner.")
    chapters = []
    for chapter, rows in by_chapter.items():
        verses = [{"number": int(number), "source_marker": number, "source_link_target_book": "Mal", "text": text}
                  for number, text in rows]
        if chapter == 4:
            verses[-1]["continuations"] = [{"source_marker": "unlabelled doxology after chapter 4, verse 6", "text": closing}]
        chapters.append({"chapter": chapter, "source_marker": str(chapter),
                         "source_sha256": hashlib.sha256((CAPTURE / f"malachi-chapter-{chapter}.html").read_bytes()).hexdigest(),
                         "verses": verses})
    reader = {
        "reader_id": READER_ID, "text_origin": "source_transcription", "canon_id": CANON_ID,
        "title": "Malachi — Geʽez Löfgren / Ghebre transcription",
        "language": "Geʽez (Classical Ethiopic)", "language_tag": "gez", "script_code": "Ethi",
        "section_label": "Chapter", "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-161", SOURCE_ID],
        "edition": "Oscar Löfgren (ed.), Jona, Nahum, Habakuk, Zephanja, Haggai, Sacharja und Maleachi äthiopisch, Uppsala, 1930, pp. 93–103. TAU text version prepared by Kefela Ghebre with permission and proofread by Ran HaCohen (October 2018).",
        "edition_scope": "Four text pages in TAU's Malachi menu, numbered 1–4, are captured. TAU identifies the print basis and credits the text preparer and proofreader. This is a digital transcription of a historical critical edition, not an identified current EOTC printed edition. The printed page span is bibliographic and is not used as proof of digital completeness.",
        "transcription_note": "Each source-linked verse label was parsed from the retained TAU HTML and kept as a separate source marker; whitespace was normalized. The original link target identifier Mal is preserved per unit. No Geʽez wording was translated, renumbered, or aligned to the Greek English companion. An unnumbered closing doxology on the fourth page is preserved as an unnumbered continuation after verse 6.",
        "editorial_signs_note": "Visible Geʽez text, punctuation, and editorial signs in source-linked verse bodies were retained after HTML entity decoding and whitespace normalization. Raw chapter pages are retained as extraction authority. Images and Löfgren's critical apparatus are not bundled.",
        "chapter_structure_note": "The four captured TAU pages contain sequential displayed labels 1–14, 1–17, 1–18, and 1–6 (55 total), each with a nonempty body and link target Mal. The last page also contains an unnumbered doxological closing, preserved separately. These are source-page observations, not proof of printed-edition or manuscript completeness. Brenton's separate Greek-based English Septuagint witness uses three chapters; it is not automatically aligned to this four-chapter Geʽez structure.",
        "rights_classification": "permission_limited", "copyright_notice": notice,
        "commercial_use": "TAU's site-wide notice permits noncommercial use, copying, and distribution with the required copyright and permission notices. TAU credits Kefela Ghebre with preparing the text, published with his kind permission, and Ran HaCohen with proofreading. No open-content or commercial license is claimed.",
        "chapter_count": 4, "unit_count": total, "source_numbered_unit_count": total, "source_unnumbered_unit_count": 1,
        "unit_label": "displayed linked number; TAU external book identifier retained per unit",
        "verification_status": "Automated checks confirm all seven captured HTML assets match their response status, byte length, and SHA-256 manifest. Four pages yield 55 nonempty sequential linked labels (14, 17, 18, 6); all links target Mal. The separately displayed unnumbered doxology is retained after chapter 4:6. This verifies the local capture-to-reader structure only. No collation against Löfgren's print edition, images, apparatus, or manuscripts was performed; exact EOTC witness identity and verse-level relationship to the Greek Brenton text remain unverified.",
        "source_pages": "Four local chapter HTML pages, TAU information/attribution page, site-wide permission notice, and TAU Old Testament index; see readers/source/malachi-tau-2018/.",
        "additional_notes": "Brenton's English Septuagint Malachi is available as a separate research reader (three chapters). It derives from Greek, not this Geʽez text. Chapter and verse labels are not used to assert a parallel translation or textual identity.",
        "chapters": chapters,
    }
    reader_sha = hashlib.sha256((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8")).hexdigest()
    layer = copy.deepcopy(json.loads((ROOT / "examples" / "zephaniah-geez-lofgren-hacohen-layer.json").read_text(encoding="utf-8")))
    layer.update({
        "record_id": f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/{READER_ID}",
        "work_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/malachi-eotc-candidate",
        "labels": [{"value": "Malachi — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"},
                   {"value": "ዘምልክያስ ፡ ነቢይ ።", "language_tag": "gez", "label_type": "original_form"}],
        "tradition_assertions": [{"tradition_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/tradition/eotc",
            "canon_id": f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/canon/{CANON_ID}",
            "mapping_state": "uncertain", "evidence_source_ids": ["SRC-029", "SRC-161", SOURCE_ID],
            "notes": "TAU and the cited Church English list both identify Malachi. This is a provisional title-level crosswalk only; identity with the current EOTC printed text and exact witness relationship remain unverified."}],
        "witness": {"witness_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/witness/malachi-lofgren-1930-ghebre-tau-2018",
            "witness_type": "digital_edition", "title": "Löfgren 1930 Ethiopic Malachi; TAU text prepared by Kefela Ghebre (2018)",
            "date_statement": "Printed edition 1930, pp. 93–103; TAU text version October 2018",
            "repository_or_publisher": "Tel Aviv University website; text attributed to Kefela Ghebre",
            "shelfmark_or_edition_id": "Malachi section of Löfgren's seven-prophet edition",
            "editorial_policy": "TAU identifies its page as the text version of the Löfgren edition, credits Kefela Ghebre as preparer (published with his permission), and Ran HaCohen as proofreader. Four chapter pages and the source notices are retained; print collation, images, and apparatus are excluded.",
            "source_ids": ["SRC-034", "SRC-036", "SRC-161", SOURCE_ID]},
        "text_origin": "source_transcription", "language_tag": "gez", "language_name_as_recorded": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi", "basis_path": ["gez"],
        "agents": [{"role": "editor", "name": "Oscar Löfgren", "authority_or_affiliation": None, "source_ids": ["SRC-161"]},
                    {"role": "transcriber", "name": "Kefela Ghebre", "authority_or_affiliation": "Credited by TAU; text published there with his permission", "source_ids": ["SRC-161", SOURCE_ID]},
                    {"role": "reviewer", "name": "Ran HaCohen", "authority_or_affiliation": "Credited by TAU as proofreader", "source_ids": ["SRC-161", SOURCE_ID]}],
        "content_package": {"uri": f"../readers/{READER_PATH.name}", "media_type": "application/json", "sha256": reader_sha, "format_version": "1"},
        "coverage": {"extent_state": "complete_for_declared_edition", "extent_basis": "source_inventory", "unit_count": total,
            "structure_description": "Four retained TAU text pages yield 55 sequential displayed labels with nonempty bodies (14, 17, 18, 6), plus an explicitly unnumbered doxological close on page 4. This establishes only the inventory of the captured TAU pages, not print or manuscript completeness.",
            "missing_or_lacunose_ranges": [],
            "supplements_and_editorial_signs": "Geʽez content and source punctuation are retained after whitespace normalization. Four source-page files preserve extraction context; the separate unnumbered closing remains attached to the reader as a continuation. Images and critical apparatus are excluded.",
            "numbering_policy": "Preserve chapter pages 1–4 and displayed labels exactly; keep the actual external target Mal per unit. No verse alignment with the three-chapter Greek-based Brenton companion is inferred."},
        "rights": {"status": "permission_limited", "statement": notice, "license_id": None,
            "rights_holder": "Ran HaCohen (TAU site notice); TAU credits Kefela Ghebre as text preparer",
            "attribution_required": True,
            "territory_or_term_limits": "Noncommercial use only with copyright and permission notice attached; other uses require contacting the rights holder. No open license or commercial permission is asserted.",
            "evidence_source_ids": ["SRC-036", "SRC-161", SOURCE_ID]},
        "review_dimensions": [
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "Four retained source pages yield 55 sequential labels in the observed page extents and all links target Mal; unnumbered closing doxology retained.", "reviewer": None, "review_method": "automated_validation", "review_process": "Malachi capture parser and archive build", "reviewed_at": file_map["malachi-chapter-1.html"]["captured_at"][:10], "evidence_source_ids": [SOURCE_ID], "notes": "This is capture-to-reader structural validation only."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No collation against Löfgren's print edition, cited manuscripts, image pages, or the current EOTC edition.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-161", SOURCE_ID], "notes": "TAU credits proofreading to Ran HaCohen; this archive has not independently repeated that review."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "TAU general notice and Malachi information/attribution page retained locally.", "reviewer": None, "review_method": "source_inspection", "review_process": "Recorded the source's permission and contributor statements.", "reviewed_at": file_map["malachi-information.html"]["captured_at"][:10], "evidence_source_ids": ["SRC-036", "SRC-161", SOURCE_ID], "notes": "Noncommercial use with notices; no commercial/open license."}],
        "publication_state": "bundled", "community_access_note": None,
        "additional_notes": "The text has a four-chapter structure in the TAU page set; the separate Brenton Greek-based reader has three chapters. No parallel mapping is asserted.",
    })
    return reader, layer


def write() -> tuple[dict, dict]:
    reader, layer = build()
    READER_PATH.write_bytes((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    LAYER_PATH.write_bytes((json.dumps(layer, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return reader, layer


if __name__ == "__main__":
    result, _ = write()
    print(f"Built Malachi reader: {result['chapter_count']} chapters, {result['unit_count']} source labels plus one unnumbered continuation.")
