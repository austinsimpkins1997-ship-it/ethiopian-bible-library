"""Build an explicitly unreviewed English research reader from archived Brenton pages."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "brenton-exodus"
MANIFEST = SOURCE_DIR / "capture-manifest.json"
READER_PATH = ROOT / "readers" / "exodus-geez.json"
EXAMPLE_PATH = ROOT / "examples" / "exodus-brenton-translation-layer.json"
LABEL_RE = re.compile(r"(?<!\S)(\d{1,3}[a-z]?)\u00a0")
NOTE_RE = re.compile(r"^(.*?)【\d+†(\d+):(\d+)】\s*(.*)$")
EXODUS_COMPANION_NOTE = (
    "An English Brenton research companion is available in a separate layer; its page-extraction wording and alignment are not verified."
)


def ensure_note_once(existing: str, note: str) -> str:
    """Avoid accumulating the same generated note across standalone rebuilds."""
    base = existing.replace(note, "").strip()
    return f"{base} {note}".strip()


def verse_sort_key(label: str) -> tuple[int, str]:
    match = re.fullmatch(r"(\d+)([a-z]?)", label)
    if not match:
        raise ValueError(f"Unexpected Brenton Exodus label: {label!r}")
    return int(match.group(1)), match.group(2)


def parse_chapter(row: dict) -> dict:
    chapter = row["chapter"]
    path = SOURCE_DIR / row["capture_file"]
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != row["sha256"]:
        raise ValueError(f"Brenton Exodus capture checksum mismatch: {path.name}")
    page = raw.decode("utf-8")
    if (f"Brenton Septuagint Translation, Exodus {chapter}" not in page
            or row["source_url"] != f"https://ebible.org/eng-Brenton/EXO{chapter:02d}.htm"):
        raise ValueError(f"Unexpected source page identity: {path.name}")

    active = False
    verse_fragments: dict[str, list[str]] = {}
    notes: list[dict] = []
    for raw_line in page.splitlines():
        match = re.match(r"L\d+:\s?(.*)$", raw_line)
        if not match:
            continue
        body = match.group(1)
        if body.strip() == "EXODUS":
            active = False
            continue
        if body.strip() == str(chapter):
            active = True
            continue
        if not active or not body.strip() or body.strip() == "* * *" or "【" in body and not LABEL_RE.search(body):
            note = NOTE_RE.match(body)
            if note:
                notes.append({"verse": note.group(3), "marker": note.group(1).strip(), "text": note.group(4).strip()})
            continue
        markers = list(LABEL_RE.finditer(body))
        if not markers:
            continue
        note = NOTE_RE.match(body)
        if note:
            notes.append({"verse": note.group(3), "marker": note.group(1).strip(), "text": note.group(4).strip()})
        for index, marker in enumerate(markers):
            label = marker.group(1)
            end = markers[index + 1].start() if index + 1 < len(markers) else len(body)
            fragment = body[marker.end():end].strip()
            fragment = re.sub(r"【\d+†([^】]+)】", r"〔\1〕", fragment)
            fragment = re.sub(r"\s+", " ", fragment).strip()
            if not fragment:
                raise ValueError(f"Empty extracted text at Exodus {chapter}:{label}")
            verse_fragments.setdefault(label, []).append(fragment)

    labels = sorted(verse_fragments, key=verse_sort_key)
    if not labels or labels[0] != "1":
        raise ValueError(f"No ordered verse-label extraction for Brenton Exodus {chapter}")
    return {
        "chapter": chapter,
        "verses": [{"number": label, "text": " ".join(verse_fragments[label])} for label in labels],
        "notes": notes,
        "source_url": row["source_url"],
        "source_capture_sha256": digest,
    }


def build() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = manifest.get("chapters", [])
    if manifest.get("chapter_count") != 40 or [row.get("chapter") for row in rows] != list(range(1, 41)):
        raise ValueError("The archived Brenton Exodus manifest must contain chapters 1–40 in order.")
    chapters = [parse_chapter(row) for row in rows]
    companion = {
        "translation_id": "exodus-english-brenton-lxx-1851",
        "text_origin": "published_translation",
        "title": "English companion — Brenton Septuagint (1851), Exodus",
        "language": "English",
        "language_tag": "en",
        "script_code": "Latn",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_language_tag": "grc",
        "translation_method": "Historical English translation from the Greek Septuagint; it is not a translation from the bundled Geʽez transcription.",
        "edition": "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851).",
        "translation_basis": "Brenton's published English translation is based on the Greek Septuagint. Labels are retained for navigation, not as proof of alignment with the Geʽez witness.",
        "rights_classification": "public_domain_claimed",
        "text_notice": "The 1851 English translation is identified by eBible.org as public domain. This local text is parsed from browser-visible page extractions; raw HTML and response bytes were not retained, so exact wording has not been checked against those pages or the print edition. Read as an unreviewed research transcription, not verified scripture.",
        "source_ids": ["SRC-038", "SRC-074", "SRC-075", "SRC-076"],
        "chapter_count": len(chapters),
        "unit_count": sum(len(chapter["verses"]) for chapter in chapters),
        "unit_label": "Captured English verse labels",
        "verse_label_count": sum(len(chapter["verses"]) for chapter in chapters),
        "verification_status": "Research reader built from 40 checksum-matched browser-visible page extracts. Chapter headings, order, source URLs, nonempty labels and note capture are structurally checked. The wording has not been collated against the live pages or Brenton's printed edition; text completeness, translation accuracy, and alignment with Geʽez remain unknown. This layer is not labeled verified scripture.",
        "chapters": chapters,
    }

    reader = json.loads(READER_PATH.read_text(encoding="utf-8"))
    reader["parallel_translation"] = companion
    reader["chapter_structure_note"] = ensure_note_once(
        reader.get("chapter_structure_note", ""), EXODUS_COMPANION_NOTE
    )
    READER_PATH.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    base = json.loads((ROOT / "examples" / "genesis-brenton-translation-layer.json").read_text(encoding="utf-8"))
    example = copy.deepcopy(base)
    example["record_id"] = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/exodus-brenton-english-1851"
    example["work_id"] = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/exodus-lxx"
    example["labels"][0]["value"] = companion["title"]
    example["tradition_assertions"] = [{
        "tradition_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/tradition/eotc",
        "canon_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/canon/eotc-ot-02",
        "mapping_state": "related_work",
        "evidence_source_ids": ["SRC-029", "SRC-074", "SRC-075"],
        "notes": "The EOTC list includes Exodus. This Brenton English rendering is a Greek-Septuagint-based related witness, not a translation from or replacement for the distinct Geʽez transcription.",
    }]
    example["witness"]["witness_id"] = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/witness/brenton-lxx-exodus-1851"
    example["witness"]["title"] = "Brenton English Septuagint, Exodus (1851)"
    example["witness"]["repository_or_publisher"] = "Sir Lancelot Charles Lee Brenton; English page extracts from eBible.org"
    example["witness"]["source_ids"] = companion["source_ids"]
    example["agents"][0]["source_ids"] = ["SRC-038", "SRC-074"]
    example["rights"]["evidence_source_ids"] = ["SRC-038", "SRC-074"]
    example["content_package"]["uri"] = "../readers/exodus-geez.json"
    example["content_package"]["json_pointer"] = "/parallel_translation"
    example["coverage"] = {
        "extent_state": "unknown",
        "extent_basis": "source_inventory",
        "unit_count": companion["verse_label_count"],
        "structure_description": "40 ordered browser-visible chapter-page extracts and their nonempty numbered labels are stored. The count describes extracted units, not confirmed verse completeness.",
        "missing_or_lacunose_ranges": [],
        "supplements_and_editorial_signs": "Extracted translator notes are retained as a separate notes array; in-text note markers are preserved.",
        "numbering_policy": "Source labels and observed gaps are preserved. Labels do not prove verse alignment with the Geʽez layer.",
    }
    example["review_dimensions"] = [
        {"dimension": "identity", "state": "checked_with_limits", "scope": "Page headings identify Brenton English Septuagint, Exodus; no printed witness was inspected.", "reviewer": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": companion["source_ids"], "notes": "Edition identity follows the cited eBible record; exact print exemplar is not checked."},
        {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "All 40 capture manifest entries and extracted page headings are in chapter order.", "reviewer": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-075", "SRC-076"], "notes": "Confirms stored page inventory, not completeness of the source edition."},
        {"dimension": "unit_boundaries", "state": "checked_with_limits", "scope": "Nonempty numbered units parsed from the 40 extracts; source labels and gaps are retained.", "reviewer": "Archive build validation", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-075", "SRC-076"], "notes": "Extraction wording and exact boundary fidelity against original page responses have not been checked."},
        {"dimension": "completeness", "state": "unknown", "scope": "No completeness review against source pages or the printed edition.", "reviewer": None, "reviewed_at": None, "evidence_source_ids": ["SRC-074", "SRC-075", "SRC-076"], "notes": "A captured page inventory is not proof that every word or note was extracted."},
        {"dimension": "translation_accuracy", "state": "unknown", "scope": "No review against the Greek Septuagint or printed English edition.", "reviewer": None, "reviewed_at": None, "evidence_source_ids": ["SRC-038", "SRC-074"], "notes": "This is the identified published English translation, but this archive has not checked translation accuracy."},
        {"dimension": "alignment", "state": "not_checked", "scope": "No verse-by-verse alignment check against the Geʽez transcription.", "reviewer": None, "reviewed_at": None, "evidence_source_ids": ["SRC-034", "SRC-035", "SRC-061", "SRC-075"], "notes": "Shared labels are navigation aids only."},
        {"dimension": "rights", "state": "checked_with_limits", "scope": "English translation reuse notice only.", "reviewer": "Archive metadata review", "reviewed_at": "2026-10-24", "evidence_source_ids": ["SRC-038"], "notes": "Public-domain claim applies to Brenton English, not the separately permission-limited Geʽez transcription."},
    ]
    # Record what was actually checked. Structural automation is not a human
    # textual review and must never make the captured wording look verified.
    for review in example["review_dimensions"]:
        state = review["state"]
        if state == "unknown" or state == "not_checked":
            review["review_method"] = "unknown"
            review["reviewer"] = None
            review["review_process"] = None
            review["reviewed_at"] = None
        elif review["dimension"] in {"identity", "rights"}:
            review["review_method"] = "source_inspection"
            review["reviewer"] = None
            review["review_process"] = "Cited source metadata inspection"
        else:
            review["review_method"] = "automated_validation"
            review["reviewer"] = None
            review["review_process"] = "Archive structural validation"
    example["additional_notes"] = companion["verification_status"] + " Browser-visible extraction, not generated translation."
    EXAMPLE_PATH.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(EXAMPLE_PATH, READER_PATH)
    sync_layer_checksum(ROOT / "examples" / "exodus-geez-layer.json", READER_PATH)

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    english = next(language for language in registry["languages"] if language["language_tag"] == "en")
    english["records"] = [record for record in english["records"] if record.get("translation_id") != companion["translation_id"]]
    english["records"].append({
        "canon_id": "eotc-ot-02",
        "reader_id": reader["reader_id"],
        "translation_id": companion["translation_id"],
        "layer_role": "historical_companion_translation",
        "status": "bundled",
        "basis_language_tag": "grc",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_description": "Brenton's 1851 English Septuagint is based on Greek. The local Exodus layer is parsed from browser-visible captures and has not been collated against the source pages or print edition.",
        "rights_status": "public_domain_per_cited_source",
        "rights_classification": "public_domain_claimed",
        "translation_path": ["grc", "en"],
        "source_ids": companion["source_ids"],
    })
    english["records"].sort(key=lambda record: (record["canon_id"], record.get("translation_id", "")))
    english["source_ids"] = sorted(set(english["source_ids"] + ["SRC-075", "SRC-076"]))
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest["review_status"] = companion["verification_status"]
    manifest["extracted_label_count"] = companion["verse_label_count"]
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    notice = (
        "Brenton Septuagint Exodus capture notes\n\n"
        "Forty browser-visible text extracts were saved from eBible.org chapter pages. The captures contain the page's visible wording, labels, note markers, and extracted translator notes; raw HTML and original response bytes were not retained.\n\n"
        "The offline reader exposes this material as an unreviewed research transcription of a named published English translation. Its 40 page headings, ordering, local checksums, extracted labels, nonempty units, and captured notes are checked. Those checks do not establish exact wording against the live page or print edition, textual completeness, translation accuracy, or alignment with the Geʽez witness. It is not labeled verified scripture.\n\n"
        "Source corpus: https://ebible.org/eng-Brenton/\n"
        "Copyright notice: https://ebible.org/eng-Brenton/copyright.htm\n"
    )
    (SOURCE_DIR / "CAPTURE-NOTICE.txt").write_text(notice, encoding="utf-8")
    print(f"Built Brenton Exodus research companion: {len(chapters)} chapters, {companion['verse_label_count']} extracted labels, {sum(len(chapter['notes']) for chapter in chapters)} notes; wording remains unreviewed.")


if __name__ == "__main__":
    build()
