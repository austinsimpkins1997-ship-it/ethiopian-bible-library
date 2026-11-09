"""Build TAU's locally captured Geʽez Joel transcription without repairing its labels."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "joel-tau-2024"
READER_PATH = ROOT / "readers" / "joel-geez-dillmann-hacohen-tau.json"
LAYER_PATH = ROOT / "examples" / "joel-geez-dillmann-layer.json"
SOURCE_ID = "SRC-192"
CANON_ID = "eotc-ot-36"
READER_ID = "joel-geez-dillmann-hacohen-tau"
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
CHAPTER_LABELS = {
    1: [str(i) for i in range(1, 21)],
    2: [str(i) for i in range(1, 16)] + [str(i) for i in range(17, 28)],
    3: [str(i) for i in range(1, 6)],
    4: ["1"] + [str(i) for i in range(4, 22)],
}


class JoelPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: tuple[int, str] | None = None
        self.parts: list[str] = []
        self.units: list[tuple[int, str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        match = re.search(r"search=Joel\+(\d+)%3A(\d+)", href)
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
        self.units.append((chapter, marker, body, "Joel"))
        self.current = None
        self.parts = []


def _load() -> tuple[dict, dict[int, list[tuple[str, str, str]]]]:
    manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        data = (CAPTURE / item["path"]).read_bytes()
        if (item.get("http_status") != 200 or len(data) != item["size_bytes"]
                or hashlib.sha256(data).hexdigest() != item["sha256"]):
            raise ValueError(f"Joel retained source failed HTTP/size/SHA check: {item['path']}")
    by_chapter = {}
    for chapter, expected in CHAPTER_LABELS.items():
        parser = JoelPageParser()
        parser.feed((CAPTURE / f"joel-chapter-{chapter}.html").read_bytes().decode("ascii"))
        parser.close()
        rows = [(number, body, target) for ch, number, body, target in parser.units if ch == chapter]
        observed = [number for number, _, _ in rows]
        if observed != expected or any(not body for _, body, _ in rows):
            raise ValueError(f"Joel chapter {chapter}: expected captured source label sequence {expected}; observed {observed}")
        if any(ch != chapter for ch, _, _, _ in parser.units):
            raise ValueError(f"Joel source page {chapter} contains a different chapter link target")
        if any(target != "Joel" for _, _, target in rows):
            raise ValueError(f"Unexpected linked book in Joel chapter {chapter}")
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
        "source_sha256": hashlib.sha256((CAPTURE / f"joel-chapter-{chapter}.html").read_bytes()).hexdigest(),
        "verses": [{"number": int(marker), "source_marker": marker, "source_link_target_book": target, "text": body}
                   for marker, body, target in rows],
    } for chapter, rows in by_chapter.items()]
    gaps = "Chapter 2 has no captured linked label 16; chapter 4 has no captured linked labels 2–3. The source pages and menu are preserved as observed; no missing text or numbering has been inferred."
    reader = {
        "reader_id": READER_ID,
        "text_origin": "source_transcription",
        "canon_id": CANON_ID,
        "title": "Joel — Geʽez Dillmann / HaCohen transcription",
        "language": "Geʽez (Classical Ethiopic)", "language_tag": "gez", "script_code": "Ethi",
        "section_label": "Chapter", "source_ids": ["SRC-029", "SRC-036", "SRC-149", SOURCE_ID],
        "edition": "August Dillmann (ed.), ‘Der äthiopische Text des Joel,’ in Adalbert Merx, Die Prophetie des Joel und ihre Ausleger (Halle, 1879), pp. 449–458; TAU text prepared by Ran HaCohen, dated June 2024 (image version October 2009).",
        "edition_scope": "TAU's Ethiopic index presents four text pages for Joel (1–4). This reader contains those four captured pages only. TAU identifies Dillmann's 1879 critical-edition text as the basis, but no comparison with the print edition, apparatus, facsimiles, manuscripts, or current EOTC edition has been made. The title crosswalk to EOTC list entry 36 is provisional.",
        "transcription_note": "Verse-like bodies are parsed from the four retained TAU HTML text pages. Whitespace is normalized to single spaces; every displayed linked number and its target are retained separately. Labels absent from the source pages are not supplied or renumbered.",
        "editorial_signs_note": "Visible Geʽez text and signs from TAU's HTML pages are retained after whitespace normalization. Facsimile images and Dillmann's apparatus are not bundled.",
        "chapter_structure_note": "The captured TAU menu lists text pages 1–4. Observed linked labels are chapter 1: 1–20; chapter 2: 1–15, 17–27; chapter 3: 1–5; chapter 4: 1, 4–21 (70 labels). Labels 2:16 and 4:2–3 are absent from the captured HTML. The archive does not infer whether this reflects source numbering, omissions, or another cause.",
        "rights_classification": "permission_limited", "copyright_notice": notice,
        "commercial_use": "TAU's site-wide notice grants noncommercial copying and distribution only when its copyright and permission notice accompany every copy; other uses require contacting the copyright owner. The permission is not an open license or commercial grant.",
        "license_id": None, "license_url": None,
        "chapter_count": len(chapters), "unit_count": total,
        "unit_label": "displayed linked number; target book retained per unit",
        "source_numbered_unit_count": total, "source_unnumbered_unit_count": 0,
        "verification_status": "Automated local validation confirms all seven retained HTML assets match their HTTP status, byte size, and SHA-256 manifest. The four text pages parse to 70 nonempty source-linked units with the exact observed label sequences and Joel link targets. This verifies capture-to-reader extraction only. Labels 2:16 and 4:2–3 are absent; their cause is unknown. No print, facsimile, apparatus, manuscript, completeness, accuracy, or current EOTC collation is claimed.",
        "source_pages": "Four local HTML text pages, chapters 1–4; information/attribution, site-wide terms, and TAU index menu are also retained.",
        "additional_notes": "No English translation from Geʽez is bundled. An optional English Septuagint companion is a separate Greek-based historical witness.",
        "chapters": chapters,
    }
    # Reuse the separately sourced Brenton reader as an explicitly Greek-based
    # English companion. The UI aligns printed labels for navigation only; this
    # does not make it a translation of the Geʽez witness.
    brenton_path = ROOT / "readers" / "brenton-lxx-jol-research.json"
    brenton = json.loads(brenton_path.read_text(encoding="utf-8"))
    reader["parallel_translation"] = {
        "translation_id": brenton["translation_id"],
        "text_origin": "published_translation",
        "title": "English companion — Brenton Septuagint (1851)",
        "language": brenton["language"], "language_tag": brenton["language_tag"], "script_code": brenton["script_code"],
        "translator": brenton["translator"], "basis_language_tag": brenton["basis_language_tag"],
        "translation_method": "Historical translation from the Greek Septuagint; not translated from the bundled Geʽez transcription.",
        "edition": brenton["edition"],
        "translation_basis": "A separate historical English witness translated from Greek. Matching chapter/verse labels are used for navigation only; they do not prove textual identity or alignment with the Geʽez text.",
        "rights_classification": brenton["rights_classification"],
        "text_notice": brenton["copyright_notice"], "source_ids": brenton["source_ids"],
        "chapter_count": brenton["chapter_count"], "unit_count": brenton["unit_count"], "verse_label_count": brenton.get("verse_label_count", brenton.get("verse_marker_count")),
        "unit_label": brenton["unit_label"], "verification_status": brenton["verification_status"],
        "chapters": brenton["chapters"],
    }
    reader["additional_notes"] = "An optional English companion is included: Brenton's 1851 translation of the Greek Septuagint, not a translation from Geʽez. It is a separate historical witness; parallel display matches labels for navigation only."
    reader_sha = hashlib.sha256((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8")).hexdigest()
    layer = copy.deepcopy(json.loads((ROOT / "examples" / "obadiah-geez-bachmann-theot-layer.json").read_text(encoding="utf-8")))
    layer.update({
        "record_id": f"{BASE}/layer/{READER_ID}", "work_id": f"{BASE}/work/joel-dillmann-1879-candidate",
        "labels": [{"value": "Joel — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"}],
        "tradition_assertions": [{"tradition_id": f"{BASE}/tradition/eotc", "canon_id": f"{BASE}/canon/{CANON_ID}", "mapping_state": "uncertain", "evidence_source_ids": ["SRC-029", "SRC-149", SOURCE_ID], "notes": "This title-level crosswalk to the EOTC Church-list entry is provisional; witness identity with a current EOTC edition is unestablished."}],
        "witness": {"witness_id": f"{BASE}/witness/joel-dillmann-1879-hacohen-2024", "witness_type": "digital_edition", "title": "Dillmann's 1879 Ethiopic Joel; TAU text prepared by Ran HaCohen (June 2024)", "date_statement": "Printed edition 1879, pp. 449–458; TAU text version June 2024", "repository_or_publisher": "Tel Aviv University website", "shelfmark_or_edition_id": "Ethiopic Joel in Merx, Die Prophetie des Joel und ihre Ausleger", "editorial_policy": "TAU identifies Dillmann's critical edition as the basis and HaCohen as preparer. Four chapter pages and source labels are captured; print collation, apparatus and manuscript review are not done.", "source_ids": ["SRC-149", SOURCE_ID]},
        "text_origin": "source_transcription", "language_tag": "gez", "language_name_as_recorded": "Geʽez (Classical Ethiopic)", "script_code": "Ethi", "basis_path": ["gez"],
        "agents": [{"role": "editor", "name": "August Dillmann", "authority_or_affiliation": None, "source_ids": ["SRC-149"]}, {"role": "transcriber", "name": "Ran HaCohen", "authority_or_affiliation": "Tel Aviv University website", "source_ids": ["SRC-149", SOURCE_ID]}],
        "content_package": {"uri": f"../readers/{READER_ID}.json", "media_type": "application/json", "sha256": reader_sha, "format_version": "1"},
        "coverage": {"extent_state": "unknown", "extent_basis": "source_inventory", "unit_count": total, "structure_description": "Four TAU pages/menu entries contain 70 parsed source labels with gaps at 2:16 and 4:2–3. Completeness against the print edition or manuscripts is unknown.", "missing_or_lacunose_ranges": ["2:16", "4:2–3"], "supplements_and_editorial_signs": "Visible Ethiopic body text retained; whitespace normalized. Source HTML retained. Facsimiles and apparatus excluded.", "numbering_policy": "Preserve captured page numbers and source labels exactly; do not fill gaps or infer cross-witness alignment."},
        "rights": {"status": "permission_limited", "statement": notice, "license_id": None, "rights_holder": "Ran HaCohen (TAU site notice)", "attribution_required": True, "territory_or_term_limits": "TAU notice grants noncommercial use only with copyright and permission notices; other uses require contacting rights holder. No open or commercial license is asserted.", "evidence_source_ids": ["SRC-036", "SRC-149", SOURCE_ID]},
        "review_dimensions": [
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "Four retained pages match capture manifest and reproduce 70 nonempty linked units with matching Joel chapter targets; labels 2:16 and 4:2–3 are absent.", "reviewer": None, "review_method": "automated_validation", "review_process": "Joel capture parser and archive build", "reviewed_at": files["joel-chapter-1.html"]["captured_at"][:10], "evidence_source_ids": [SOURCE_ID], "notes": gaps},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No collation against Dillmann's print, facsimiles, apparatus, manuscripts, or an EOTC edition.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-149", SOURCE_ID], "notes": "TAU credits HaCohen with preparing the text; this archive has not independently reviewed his transcription."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "TAU Joel attribution page and site-wide reuse notice retained locally.", "reviewer": None, "review_method": "source_inspection", "review_process": "Captured and retained the source's attribution and permission terms.", "reviewed_at": files["joel-information.html"]["captured_at"][:10], "evidence_source_ids": ["SRC-036", "SRC-149", SOURCE_ID], "notes": "Noncommercial-only permission with notices; not open content."},
        ],
        "publication_state": "bundled", "community_access_note": None,
        "additional_notes": "No English translation from Geʽez is bundled. The optional Brenton English text is a separate Greek-based witness; source-label gaps in the Geʽez transcription remain marked.",
    })
    return reader, layer


def write() -> tuple[dict, dict]:
    reader, layer = build()
    READER_PATH.write_bytes((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    LAYER_PATH.write_bytes((json.dumps(layer, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return reader, layer


if __name__ == "__main__":
    reader, layer = write()
    print(f"Built Joel reader: {reader['chapter_count']} chapters, {reader['unit_count']} captured labels; gaps preserved; layer {layer['record_id']}.")
