"""Build a distinct, sourced Ruth companion from local Brenton page captures."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import re
from pathlib import Path

from coverage_summary import build_coverage_statement
from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
CAPTURE_DIR = ROOT / "readers" / "source" / "brenton-ruth"
MANIFEST_PATH = CAPTURE_DIR / "capture-manifest.json"
READER_PATH = ROOT / "readers" / "ruth-geez.json"
EXAMPLE_PATH = ROOT / "examples" / "ruth-brenton-translation-layer.json"
LABEL_RE = re.compile(r"(?<!\S)(\d{1,3}[a-z]?)\u00a0")


def label_key(label: str) -> tuple[int, str]:
    match = re.fullmatch(r"(\d+)([a-z]?)", label)
    if not match:
        raise ValueError(f"Unexpected Brenton Ruth label: {label!r}")
    return int(match.group(1)), match.group(2)


def parse_chapter(row: dict) -> dict:
    chapter = row["chapter"]
    filename = f"Ruth_{chapter:02d}.txt"
    if row.get("capture_file") != filename or row.get("source_url") != f"https://ebible.org/eng-Brenton/RUT{chapter:02d}.htm":
        raise ValueError(f"Brenton Ruth chapter {chapter} capture metadata mismatch.")
    path = (CAPTURE_DIR / filename).resolve()
    if not path.is_relative_to(CAPTURE_DIR.resolve()) or not path.is_file():
        raise ValueError(f"Brenton Ruth capture is missing or outside its directory: {filename}.")
    raw = path.read_bytes()
    if len(raw) != row.get("capture_bytes") or hashlib.sha256(raw).hexdigest() != row.get("sha256"):
        raise ValueError(f"Brenton Ruth capture checksum/length mismatch: {filename}.")
    text = raw.decode("utf-8")
    if "Ruth" not in text or not re.search(rf"L2:.*?{chapter}.*", text):
        raise ValueError(f"Brenton Ruth capture page number mismatch: {filename}.")

    verses: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"L\d+:\s?(.*)$", line)
        if not match:
            continue
        body = match.group(1)
        markers = list(LABEL_RE.finditer(body))
        for index, marker in enumerate(markers):
            label = marker.group(1)
            end = markers[index + 1].start() if index + 1 < len(markers) else len(body)
            verse = re.sub(r"\s+", " ", body[marker.end():end]).strip()
            if not verse or label in verses:
                raise ValueError(f"Empty or duplicate Brenton Ruth {chapter}:{label}.")
            verses[label] = verse

    labels = sorted(verses, key=label_key)
    expected = [str(number) for number in range(1, len(labels) + 1)]
    if labels != expected:
        raise ValueError(f"Brenton Ruth {chapter} labels are not a contiguous 1-based sequence: {labels}.")
    return {
        "chapter": chapter,
        "verses": [{"number": label, "text": verses[label]} for label in labels],
        "source_url": row["source_url"],
        "source_capture_sha256": row["sha256"],
    }


def ensure_source(archive: dict, source: dict) -> None:
    sources = archive.setdefault("sources", [])
    existing = next((item for item in sources if item.get("source_id") == source["source_id"]), None)
    if existing is None:
        sources.append(source)
    elif existing != source:
        raise ValueError(f"Source ID collision for {source['source_id']}.")


def build() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = manifest.get("chapters", [])
    if (manifest.get("chapter_count") != 4 or [row.get("chapter") for row in rows] != [1, 2, 3, 4]
            or "not byte-for-byte" not in manifest.get("capture_method", "")
            or "do not prove" not in manifest.get("limitations", "")):
        raise ValueError("Brenton Ruth capture manifest must disclose all four pages and extraction limits.")
    chapters = [parse_chapter(row) for row in rows]
    label_count = sum(len(chapter["verses"]) for chapter in chapters)
    if [len(chapter["verses"]) for chapter in chapters] != [22, 23, 18, 22] or label_count != 85:
        raise ValueError("Brenton Ruth capture does not match the four source-page label inventories (22, 23, 18, 22).")

    reader = json.loads(READER_PATH.read_text(encoding="utf-8"))
    if reader.get("reader_id") != "ruth-geez-dillmann-hacohen" or reader.get("canon_id") != "eotc-ot-08":
        raise ValueError("Brenton Ruth companion must attach only to the existing Ruth Geʽez reader.")
    reader["parallel_translation"] = {
        "translation_id": "ruth-english-brenton-lxx-1851",
        "text_origin": "published_translation",
        "title": "English companion — Brenton Septuagint (1851)",
        "language": "English",
        "language_tag": "en",
        "script_code": "Latn",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_language_tag": "grc",
        "translation_method": "Historical English translation from the Greek Septuagint; it is not directly translated from or aligned to the bundled Geʽez transcription.",
        "edition": "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851).",
        "translation_basis": "eBible.org identifies this as Brenton's 1851 English translation from Greek. It is an independent English witness paired for study, not a modern rendering, direct translation from Geʽez, or proof of verse-level equivalence.",
        "rights_classification": "public_domain_claimed",
        "text_notice": "eBible.org identifies Brenton's 1851 translation as public domain. The archive's browser-visible text capture is separately documented; site page design and any other source layer are not included in that rights claim. Historical spellings and names such as Bethleem, Noemin, Booz, and Jessæ are retained.",
        "source_ids": ["SRC-038", "SRC-095", "SRC-096"],
        "chapter_count": len(chapters),
        "unit_count": label_count,
        "unit_label": "Captured English verse labels",
        "verse_label_count": label_count,
        "verification_status": "All four eBible.org Ruth chapter pages were captured as browser-visible text and locally checked for page number, ordered chapters, nonempty text, and contiguous verse labels (85 labels: 22, 23, 18, 22). The captures are not raw HTML or byte-for-byte server responses. The English wording has not been independently collated against Brenton's printed 1851 edition or the Greek Septuagint; translation accuracy, edition completeness, and alignment with Geʽez remain unverified. This is a historical companion research transcription, not a verified Geʽez translation.",
        "chapters": chapters,
    }
    READER_PATH.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Both layer records point to this shared offline reader package.
    sync_layer_checksum(ROOT / "examples" / "ruth-geez-layer.json", READER_PATH)

    example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    example["content_package"]["json_pointer"] = "/parallel_translation"
    example["coverage"]["unit_count"] = label_count
    example["coverage"]["structure_description"] = "Four browser-visible chapter-page captures; 85 contiguous English verse labels (22, 23, 18, 22). This inventory does not prove completeness of the printed edition."
    sync_layer_checksum(EXAMPLE_PATH, READER_PATH)

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    ensure_source(archive, {
        "source_id": "SRC-095",
        "source_name": "eBible.org — Brenton Septuagint English, Ruth chapter pages",
        "url": "https://ebible.org/eng-Brenton/RUT.htm",
        "inspection_and_limitations": "The index lists Ruth chapters 1–4; each linked eBible.org chapter page identifies the Brenton English Septuagint and displays numbered text. Local browser-visible extracts preserve the returned page text, page labels, and wording. This is not raw HTML or a byte-for-byte server response; exact collation against Brenton's print edition, completeness, Greek accuracy, and Geʽez alignment are not established.",
        "archive_status": "Four chapter pages inspected; historical English companion bundled with explicit textual-review limits",
    })
    ensure_source(archive, {
        "source_id": "SRC-096",
        "source_name": "Local Brenton Ruth browser-visible capture manifest",
        "url": "readers/source/brenton-ruth/capture-manifest.json",
        "inspection_and_limitations": "Records the four chapter URLs, byte lengths, SHA-256 digests, capture method, and explicit limitations. The stored captures are UTF-8 visible-text extracts, not raw HTTP bodies. The parser checks the 1–4 chapter sequence and 85 contiguous labels; those structural checks do not verify print-edition completeness, exact wording, Greek translation accuracy, or Geʽez alignment.",
        "archive_status": "Local checksummed research captures for a separately identified English companion",
    })
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    english = next(language for language in registry["languages"] if language["language_tag"] == "en")
    record = {
        "canon_id": "eotc-ot-08",
        "reader_id": reader["reader_id"],
        "translation_id": reader["parallel_translation"]["translation_id"],
        "layer_role": "historical_companion_translation",
        "status": "bundled",
        "basis_language_tag": "grc",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_description": "Brenton's 1851 English Septuagint is based on Greek, not the accompanying Geʽez transcription. This historic translation is not direct Geʽez-to-English evidence.",
        "rights_status": "public_domain_per_cited_source",
        "rights_classification": "public_domain_claimed",
        "translation_path": ["grc", "en"],
        "source_ids": ["SRC-038", "SRC-095", "SRC-096"],
    }
    if not any(item.get("translation_id") == record["translation_id"] for item in english["records"]):
        english["records"].append(record)
    english["records"].sort(key=lambda item: (item["canon_id"], item.get("translation_id", "")))
    english["source_ids"] = sorted(set(english.get("source_ids", [])) | {"SRC-095", "SRC-096"})
    canon_path = ROOT / "canon-registry.json"
    canon = json.loads(canon_path.read_text(encoding="utf-8"))
    ruth_entry = next(item for item in canon["books"] if item.get("canon_id") == "eotc-ot-08")
    ruth_entry["reader_status"] = "Bundled: Geʽez source transcription + historical English Brenton Septuagint companion (Greek basis; not aligned)"
    canon_path.write_text(json.dumps(canon, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry["coverage_statement"] = build_coverage_statement(registry, canon)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built Brenton Ruth companion: 4 chapters, {label_count} source labels; accuracy and full-edition completeness remain unverified.")


if __name__ == "__main__":
    build()
