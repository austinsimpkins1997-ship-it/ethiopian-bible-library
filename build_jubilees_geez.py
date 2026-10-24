"""Build the locally bundled Geʽez Jubilees reader from the pinned TEI source."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers" / "source" / "jubilees" / "LIT1697Jubilees-Ran.xml"
OUTPUT = ROOT / "readers" / "jubilees-geez-hacohen.json"
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI, "xml": XML}


def main() -> None:
    raw = SOURCE.read_bytes()
    root = ET.fromstring(raw)
    edition = root.find('.//tei:div[@type="edition"][@xml:id="Ran"]', NS)
    if edition is None or edition.get(f"{{{XML}}}lang") != "gez":
        raise ValueError("Pinned TEI source is missing the expected Ran Geʽez edition.")
    divisions = [item for item in edition.findall("tei:div", NS)
                 if item.get("type") == "textpart" and item.get("subtype") == "chapter"]
    numbered = [item for item in divisions if item.get("n")]
    if len(numbered) != 50 or [item.get("n") for item in numbered] != [str(i) for i in range(1, 51)]:
        raise ValueError("Expected exactly source chapters 1–50 in sequence.")
    chapters = []
    for index, division in enumerate(numbered, 1):
        lines = division.findall(".//tei:l", NS)
        if not lines:
            raise ValueError(f"Chapter {index} has no numbered source lines.")
        records = []
        for position, line in enumerate(lines, 1):
            label = line.get("n")
            text = "".join(line.itertext()).strip()
            if not label or not text:
                raise ValueError(f"Chapter {index} has a line with no source marker or text.")
            # Keep the original TEI n value while assigning unique display order. Some source
            # divisions repeat n values (for example Jubilees 26 starts at n=26, then repeats 26).
            records.append({"number": position, "source_marker": label, "text": text})
        chapters.append({"chapter": index, "verses": records})

    OUTPUT.write_text(json.dumps({
        "reader_id": "jubilees-geez-hacohen",
        "canon_id": "eotc-ot-13",
        "title": "Jubilees — Geʽez reader",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "script_code": "Ethi",
        "unit_label": "Entry order (source line marker shown)",
        "source_ids": ["SRC-029", "SRC-040", "SRC-041"],
        "edition": "Ran HaCohen transcription, OCTATEUCHUS © Digitalizat; edition 1 in the Beta maṣāḥǝft TEI record LIT1697Jubilees.",
        "edition_scope": "This is the Ran HaCohen transcription in the TEI edition identified xml:id=Ran. The public build input is a rights-conscious extract containing only this explicitly licensed edition; a separate standard EOTC printed edition in the original TEI snapshot is withheld pending rights review. The 50 numbered divisions are the source's chapters, and n attributes on l elements are retained as source line markers, not reinterpreted as biblical verse numbering.",
        "chapter_structure_note": "Preserves the source edition's chapters 1–50 and every TEI line's original n attribute. Display order is used for unique navigation because source labels repeat (for example chapter 26 begins with n=26 and later repeats n=26) and skip values; both display order and the original source marker are shown. The TEI incipit is unnumbered and excluded from numbered chapters; consult the stored source XML for its full diplomatic structure and parallel EOTC edition.",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "parent_source_sha256": "d8c6eaa3857c35d8e467a6c150178fc02395fc569527bedfc7687c43cc68d87f",
        "source_path": "readers/source/jubilees/LIT1697Jubilees-Ran.xml",
        "chapter_count": len(chapters),
        "verse_marker_count": sum(len(chapter["verses"]) for chapter in chapters),
        "verification_status": "Parsed offline from the pinned TEI snapshot’s Ran-only extract. The full pinned source snapshot is retained outside the published site for audit (SHA-256 d8c6eaa3857c35d8e467a6c150178fc02395fc569527bedfc7687c43cc68d87f). The selected edition contains exactly chapters 1–50; chapter order, nonempty line text, and preservation of every source n marker are checked. Source markers repeat and skip in places, so navigation uses display order and shows the original marker alongside. No independent manuscript collation or line-by-line scholarly verification was performed.",
        "copyright_notice": "CC BY-SA 4.0. Source TEI explicitly states that this Ran HaCohen transcription is under the same license. Attribute Ran HaCohen and the Beta maṣāḥǝft record; adaptations must use the same license and indicate changes.",
        "commercial_use": "Permitted under CC BY-SA 4.0 with attribution and ShareAlike terms.",
        "chapters": chapters,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(ROOT / "examples" / "jubilees-geez-layer.json", OUTPUT)
    print(f"Built {OUTPUT.name}: 50 chapters, {sum(len(c['verses']) for c in chapters)} source lines.")


if __name__ == "__main__":
    main()
