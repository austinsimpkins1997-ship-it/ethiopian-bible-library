"""Build the captured Geʽez Amos source transcription from TAU's nine text pages."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "amos-tau-2009"
READER_PATH = ROOT / "readers" / "amos-geez-pereira-ghebre-tau.json"
LAYER_PATH = ROOT / "examples" / "amos-geez-pereira-layer.json"
SOURCE_ID = "SRC-193"
CANON_ID = "eotc-ot-34"
READER_ID = "amos-geez-pereira-ghebre-tau"
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
CHAPTER_LABELS = {
    1: 15, 2: 16, 3: 15, 4: 13, 5: 27, 6: 14, 7: 17, 8: 14, 9: 15,
}


class AmosPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: tuple[int, str] | None = None
        self.parts: list[str] = []
        self.units: list[tuple[int, str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        match = re.search(r"search=Amo\+(\d+)%3A(\d+)", href)
        if match:
            self._finish()
            self.current = (int(match.group(1)), match.group(2))
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
        chapter, marker = self.current
        body = re.sub(r"\s+", " ", "".join(self.parts)).strip()
        body = re.sub(rf"^{re.escape(marker)}\s+", "", body, count=1)
        self.units.append((chapter, marker, body, "Amo"))
        self.current = None
        self.parts = []


def _load() -> tuple[dict, dict[int, list[tuple[str, str, str]]]]:
    manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        data = (CAPTURE / item["path"]).read_bytes()
        if (item.get("http_status") != 200 or len(data) != item["size_bytes"]
                or hashlib.sha256(data).hexdigest() != item["sha256"]):
            raise ValueError(f"Amos retained source failed HTTP/size/SHA check: {item['path']}")
    by_chapter: dict[int, list[tuple[str, str, str]]] = {}
    for chapter, count in CHAPTER_LABELS.items():
        parser = AmosPageParser()
        parser.feed((CAPTURE / f"amos-chapter-{chapter}.html").read_bytes().decode("ascii"))
        parser.close()
        rows = [(number, body, target) for ch, number, body, target in parser.units if ch == chapter]
        expected = [str(n) for n in range(1, count + 1)]
        observed = [number for number, _, _ in rows]
        if observed != expected or any(not body for _, body, _ in rows):
            raise ValueError(f"Amos chapter {chapter}: expected labels {expected}; observed {observed}")
        if any(ch != chapter for ch, _, _, _ in parser.units):
            raise ValueError(f"Amos chapter page {chapter} includes a different chapter target")
        if any(target != "Amo" for _, _, target in rows):
            raise ValueError(f"Amos chapter {chapter} has an unexpected BibleGateway book identifier")
        by_chapter[chapter] = rows
    return manifest, by_chapter


def build() -> tuple[dict, dict]:
    manifest, by_chapter = _load()
    files = {item["path"]: item for item in manifest["files"]}
    notice = (
        "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and this permission notice appear in all copies of the text. For other uses, please contact the copyright owner."
    )
    total = sum(len(rows) for rows in by_chapter.values())
    chapters = [{
        "chapter": chapter,
        "source_marker": str(chapter),
        "source_sha256": hashlib.sha256((CAPTURE / f"amos-chapter-{chapter}.html").read_bytes()).hexdigest(),
        "verses": [{"number": int(marker), "source_marker": marker, "source_link_target_book": target, "text": body}
                   for marker, body, target in rows],
    } for chapter, rows in by_chapter.items()]
    reader = {
        "reader_id": READER_ID, "text_origin": "source_transcription", "canon_id": CANON_ID,
        "title": "Amos — Geʽez Pereira / Ghebre transcription",
        "language": "Geʽez (Classical Ethiopic)", "language_tag": "gez", "script_code": "Ethi",
        "section_label": "Chapter", "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-151", SOURCE_ID],
        "edition": "F. M. Esteves Pereira (ed.), O livro do profeta Amós e a sua versão etiópica (Coimbra, 1917); text prepared by Kefela Ghebre and published at TAU with his permission, proofread by Ran HaCohen (November 2009).",
        "edition_scope": "TAU identifies its Ethiopic Amos text as following Pereira's 1917 critical edition. This reader contains the nine text pages numbered as chapters 1–9 in TAU's menu. It excludes the separate introduction, critical apparatus, images, and Portuguese translation. The Church-list title crosswalk is provisional; identity with a current EOTC edition is not established.",
        "transcription_note": "Verse bodies are parsed from nine captured TAU HTML text pages. Whitespace is normalized to single spaces. Each displayed linked number is retained as a separate source_marker, and each page's external BibleGateway book identifier is preserved per unit as Amo. No text is translated, renumbered, or aligned to another witness.",
        "editorial_signs_note": "Visible Geʽez letters, punctuation, and editorial signs in the linked text bodies are retained after HTML entity decoding and whitespace normalization. Pereira's separate Portuguese translation and critical apparatus are not bundled; raw page HTML is retained as extraction authority.",
        "chapter_structure_note": "The TAU menu lists text pages 1–9. They contain sequential displayed labels with extents 15, 16, 15, 13, 27, 14, 17, 14, and 15 (146 total). All 146 external links use the source identifier Amo. This is a page-label inventory, not print-edition or manuscript completeness evidence.",
        "rights_classification": "permission_limited", "copyright_notice": notice,
        "commercial_use": "TAU's site-wide notice permits noncommercial use, copying, and distribution of digitized Ethiopic texts when the Ran HaCohen copyright and permission notices accompany every copy. The Amos page credits Kefela Ghebre with preparing the text and says it is published at TAU with his permission; Ran HaCohen proofread it. No open-content or commercial license is asserted.",
        "license_id": None, "license_url": None,
        "chapter_count": len(chapters), "unit_count": total,
        "unit_label": "displayed linked number; TAU external book identifier retained per unit",
        "source_numbered_unit_count": total, "source_unnumbered_unit_count": 0,
        "verification_status": "Automated validation confirms all twelve captured HTML assets match the retained HTTP/size/SHA-256 manifest. Nine chapter pages yield 146 nonempty sequential source labels (1–15, 1–16, 1–15, 1–13, 1–27, 1–14, 1–17, 1–14, 1–15); every captured linked target uses the TAU identifier Amo. This checks local capture-to-reader structure only. No collation against Pereira's print edition, images, introduction, apparatus, manuscripts, or a current EOTC edition has been performed.",
        "source_pages": "Nine local HTML text pages, chapters 1–9; source information, general terms, and TAU index menu are also retained.",
        "additional_notes": "An optional English companion is included: Brenton's 1851 translation of the Greek Septuagint, not a translation from Geʽez. It is a separate historical witness; matching labels are for navigation only. TAU's separate introduction and critical apparatus are not included.",
        "chapters": chapters,
    }
    brenton = json.loads((ROOT / "readers" / "brenton-lxx-amo-research.json").read_text(encoding="utf-8"))
    reader["parallel_translation"] = {
        "translation_id": brenton["translation_id"],
        "text_origin": "published_translation",
        "title": "English companion — Brenton Septuagint (1851)",
        "language": brenton["language"], "language_tag": brenton["language_tag"], "script_code": brenton["script_code"],
        "translator": brenton["translator"], "basis_language_tag": brenton["basis_language_tag"],
        "translation_method": "Historical translation from the Greek Septuagint; not translated from the bundled Geʽez transcription.",
        "edition": brenton["edition"],
        "translation_basis": "A separate historical English witness translated from Greek. Matching chapter and verse labels are displayed for navigation only; they do not establish textual identity or alignment with the Geʽez witness.",
        "rights_classification": brenton["rights_classification"],
        "text_notice": brenton["copyright_notice"], "source_ids": brenton["source_ids"],
        "chapter_count": brenton["chapter_count"], "unit_count": brenton["unit_count"],
        "unit_label": brenton["unit_label"], "verse_label_count": brenton.get("verse_label_count", brenton.get("verse_marker_count")),
        "verification_status": brenton["verification_status"],
        "chapters": brenton["chapters"],
    }
    reader_sha = hashlib.sha256((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8")).hexdigest()
    layer = copy.deepcopy(json.loads((ROOT / "examples" / "obadiah-geez-bachmann-theot-layer.json").read_text(encoding="utf-8")))
    layer.update({
        "record_id": f"{BASE}/layer/{READER_ID}", "work_id": f"{BASE}/work/amos-pereira-1917-candidate",
        "labels": [{"value": "Amos — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"}],
        "tradition_assertions": [{"tradition_id": f"{BASE}/tradition/eotc", "canon_id": f"{BASE}/canon/{CANON_ID}", "mapping_state": "uncertain", "evidence_source_ids": ["SRC-029", "SRC-151", SOURCE_ID], "notes": "The English Church list and TAU use Amos; this is a provisional title-level crosswalk only. Identity of Pereira's witness with a current EOTC text is unverified."}],
        "witness": {"witness_id": f"{BASE}/witness/amos-pereira-1917-ghebre-tau-2009", "witness_type": "digital_edition", "title": "Pereira's 1917 Ethiopic Amos; TAU text prepared by Kefela Ghebre and proofread by Ran HaCohen", "date_statement": "Printed edition 1917; TAU text version November 2009", "repository_or_publisher": "Tel Aviv University website; text credited to Kefela Ghebre", "shelfmark_or_edition_id": "O livro do profeta Amós e a sua versão etiópica", "editorial_policy": "TAU credits Ghebre with preparing the text and says he permitted its publication; HaCohen proofread it. Nine text pages are captured; print collation, images, introduction, and apparatus are not included.", "source_ids": ["SRC-151", SOURCE_ID]},
        "text_origin": "source_transcription", "language_tag": "gez", "language_name_as_recorded": "Geʽez (Classical Ethiopic)", "script_code": "Ethi", "basis_path": ["gez"],
        "agents": [{"role": "editor", "name": "F. M. Esteves Pereira", "authority_or_affiliation": None, "source_ids": ["SRC-151"]}, {"role": "transcriber", "name": "Kefela Ghebre", "authority_or_affiliation": "Credited by Tel Aviv University; text published there with his permission", "source_ids": ["SRC-151", SOURCE_ID]}, {"role": "reviewer", "name": "Ran HaCohen", "authority_or_affiliation": "Credited by Tel Aviv University as proofreader", "source_ids": ["SRC-151", SOURCE_ID]}],
        "content_package": {"uri": f"../readers/{READER_ID}.json", "media_type": "application/json", "sha256": reader_sha, "format_version": "1"},
        "coverage": {"extent_state": "complete_for_declared_edition", "extent_basis": "source_inventory", "unit_count": total, "structure_description": "Nine menu-listed TAU text pages contain 146 nonempty sequential displayed labels. This covers the captured pages only; it does not establish completeness against Pereira's print edition or manuscripts.", "missing_or_lacunose_ranges": [], "supplements_and_editorial_signs": "HTML entities decoded and whitespace normalized; source HTML retained. External target identifier Amo is recorded separately per source unit. Introduction, critical apparatus, images, and Portuguese translation are excluded.", "numbering_policy": "Preserve TAU page numbers 1–9 and each displayed source label; retain linked source target identifier Amo. Do not infer cross-witness numbering or alignment."},
        "rights": {"status": "permission_limited", "statement": notice, "license_id": None, "rights_holder": "Ran HaCohen (TAU site notice); TAU credits Kefela Ghebre with preparing the text and permission for posting it", "attribution_required": True, "territory_or_term_limits": "TAU's site-wide notice grants noncommercial use only with required copyright and permission notices; other uses require contacting the rights holder. No open or commercial license is asserted.", "evidence_source_ids": ["SRC-036", "SRC-151", SOURCE_ID]},
        "review_dimensions": [
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "Nine captured page checksums and sequential displayed labels 1–146 verified; all link targets use Amo.", "reviewer": None, "review_method": "automated_validation", "review_process": "Amos capture parser and archive build", "reviewed_at": files["amos-chapter-1.html"]["captured_at"][:10], "evidence_source_ids": [SOURCE_ID], "notes": "Capture-to-reader structure only; not print or manuscript completeness."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No comparison with Pereira's 1917 printed edition, images, introduction, apparatus, manuscripts, or current EOTC text.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-151", SOURCE_ID], "notes": "TAU credits Ghebre with preparation and HaCohen with proofreading; this archive has not independently repeated that review."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "TAU Amos attribution page and site-wide noncommercial reuse notice captured locally.", "reviewer": None, "review_method": "source_inspection", "review_process": "Retained attribution, notice and permission terms with source HTML.", "reviewed_at": files["amos-information.html"]["captured_at"][:10], "evidence_source_ids": ["SRC-036", "SRC-151", SOURCE_ID], "notes": "Noncommercial copying/distribution with required notices only; not open or commercial."},
        ],
        "publication_state": "bundled", "community_access_note": None,
        "additional_notes": "No English translation is bundled. Canon mapping is a provisional title-level link; witness identity and textual accuracy remain unreviewed.",
    })
    return reader, layer


def write() -> tuple[dict, dict]:
    reader, layer = build()
    READER_PATH.write_bytes((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    LAYER_PATH.write_bytes((json.dumps(layer, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return reader, layer


if __name__ == "__main__":
    reader, layer = write()
    print(f"Built Amos reader: {reader['chapter_count']} chapters, {reader['unit_count']} captured source labels; layer {layer['record_id']}.")
