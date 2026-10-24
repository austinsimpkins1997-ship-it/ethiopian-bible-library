"""Build the bundled, attributed English Septuagint companion for Genesis."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from layer_metadata import sync_layer_checksum


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "brenton-genesis"
OUTPUT = ROOT / "readers" / "genesis-brenton.json"


def verse_sort_key(label: str) -> tuple[int, str]:
    match = re.fullmatch(r"(\d+)([a-z]?)", label)
    if not match:
        raise ValueError(f"Unexpected English verse label: {label!r}")
    return int(match.group(1)), match.group(2)


def parse_chapter(chapter: int) -> dict:
    path = SOURCE_DIR / f"Genesis_{chapter:02d}.txt"
    if not path.is_file():
        raise ValueError(f"Missing captured Brenton source page: {path.name}")
    raw = path.read_bytes()
    page = raw.decode("utf-8")
    if not re.search(rf"Brenton Septuagint Translation Genesis {chapter} ", page):
        raise ValueError(f"Unexpected source page identity in {path.name}")

    verses: dict[str, str] = {}
    notes: list[dict] = []
    for line in page.splitlines():
        match = re.match(r"L\d+:\s?(.*)$", line)
        if not match:
            continue
        body = match.group(1)
        markers = list(re.finditer(r"(?<!\S)(\d{1,3}[a-z]?)\u00a0", body))
        for index, marker in enumerate(markers):
            label = marker.group(1)
            end = markers[index + 1].start() if index + 1 < len(markers) else len(body)
            text = body[marker.end():end].strip()
            text = re.sub(r"【\d+†([^】]+)】", r"〔\1〕", text)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                raise ValueError(f"Empty English text at Genesis {chapter}:{label}")
            if label in verses:
                raise ValueError(f"Duplicate English verse marker Genesis {chapter}:{label}")
            verses[label] = text

        note = re.match(r"^(.*?)【\d+†(\d+):(\d+)】\s*(.*)$", body)
        if note:
            notes.append({
                "marker": note.group(1).strip(),
                "verse": note.group(3),
                "text": note.group(4).strip(),
            })

        labels = sorted(verses, key=verse_sort_key)
    if not labels or labels[0] != "1" or any(not verses[label] for label in labels):
        raise ValueError(f"Missing or empty Brenton Genesis {chapter} text")
    return {
        "chapter": chapter,
        "verses": [{"number": label, "text": verses[label]} for label in labels],
        "notes": notes,
        "source_url": f"https://ebible.org/eng-Brenton/GEN{chapter:02d}.htm",
        "source_capture_sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> None:
    chapters = [parse_chapter(chapter) for chapter in range(1, 51)]
    companion = {
        "translation_id": "genesis-english-brenton-lxx-1851",
        "title": "English companion — Brenton Septuagint (1851)",
        "language": "English",
        "language_tag": "en",
        "script_code": "Latn",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_language_tag": "grc",
        "translation_method": "Historical translation from Greek Septuagint; not directly from the bundled Geʽez transcription.",
        "edition": "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851).",
        "translation_basis": "Translated from Greek Septuagint, not directly from the bundled Geʽez transcription. It is supplied as an English companion witness, not a replacement, direct translation, or proof that every wording aligns with the Ethiopic text.",
        "text_notice": "The Brenton translation is public domain. This archive preserves its historical wording, spelling, verse labels (including lettered labels), and translator/editor notes. Its English is 19th-century and may not read like contemporary English.",
        "source_ids": ["SRC-037", "SRC-038"],
        "chapter_count": len(chapters),
        "verse_label_count": sum(len(chapter["verses"]) for chapter in chapters),
        "verification_status": "Bundled from the complete 50 chapter pages identified as Brenton's 1851 English Septuagint at eBible.org. Chapter identity, ordered labels, nonempty verse text, notes, and source captures are checked locally. This is not an independent collation against Brenton's printed 1851 edition or a Geʽez-to-English translation.",
        "chapters": chapters,
    }
    OUTPUT.write_text(json.dumps(companion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(ROOT / "examples" / "genesis-brenton-translation-layer.json", OUTPUT)
    print(f"Built {OUTPUT.name}: {len(chapters)} chapters, {companion['verse_label_count']} English verse labels, {sum(len(c['notes']) for c in chapters)} notes.")


if __name__ == "__main__":
    main()
