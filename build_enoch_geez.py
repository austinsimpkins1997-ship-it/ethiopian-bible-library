"""Build a rights-scoped Geʽez 1 Enoch reader from the pinned EOTC TEI extract."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers" / "source" / "enoch" / "LIT1340EnochE-EOTCed.xml"
OUTPUT = ROOT / "readers" / "enoch-geez-eotc.json"
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI, "xml": XML}
PARENT_SHA256 = "61dd5b372894e54c10f661740d0dd3fbfbfaeef4c99c55690eed4b4aae03f6d9"


def main() -> None:
    raw = SOURCE.read_bytes()
    root = ET.fromstring(raw)
    editions = root.findall('.//tei:div[@type="edition"]', NS)
    if len(editions) != 1 or editions[0].get(f"{{{XML}}}id") != "EOTCed":
        raise ValueError("The local TEI build source must contain only the EOTCed edition.")
    edition = editions[0]
    if edition.get(f"{{{XML}}}lang") != "gez":
        raise ValueError("The selected EOTCed text is not marked as Geʽez.")

    divisions = edition.findall('./tei:div[@type="textpart"][@subtype="chapter"]', NS)
    if len(divisions) != 108 or [item.get("n") for item in divisions] != [str(i) for i in range(1, 109)]:
        raise ValueError("Expected the source's 108 chapter divisions in order.")

    chapters = []
    marker_anomalies = []
    for chapter_number, division in enumerate(divisions, 1):
        lines = division.findall(".//tei:l", NS)
        if not lines:
            raise ValueError(f"Chapter {chapter_number} has no source lines.")
        records = []
        for display_order, line in enumerate(lines, 1):
            marker = line.get("n")
            text = "".join(line.itertext()).strip()
            if not marker or not text:
                raise ValueError(f"Chapter {chapter_number} has a source line without a marker or text.")
            if list(line):
                raise ValueError(f"Chapter {chapter_number} has nested line markup; refuse lossy flattening.")
            records.append({"number": display_order, "source_marker": marker, "text": text})
        source_numbers = [record["source_marker"] for record in records]
        if source_numbers != [str(i) for i in range(int(source_numbers[0]), int(source_numbers[0]) + len(source_numbers))]:
            raise ValueError(f"Chapter {chapter_number} source markers are not increasing consecutive integers.")
        if source_numbers[0] != "1":
            marker_anomalies.append({"chapter": chapter_number, "first_source_marker": source_numbers[0]})
        chapters.append({"chapter": chapter_number, "verses": records})

    total_lines = sum(len(chapter["verses"]) for chapter in chapters)
    if total_lines != 1058:
        raise ValueError(f"Expected 1,058 labeled source lines; found {total_lines}.")
    if marker_anomalies != [{"chapter": 21, "first_source_marker": "2"}]:
        raise ValueError(f"Unexpected source-marker discontinuities: {marker_anomalies}")

    OUTPUT.write_text(json.dumps({
        "reader_id": "enoch-geez-eotc",
        "canon_id": "eotc-ot-14",
        "title": "1 Enoch — Geʽez EOTC printed-edition transcription",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "script_code": "Ethi",
        "unit_label": "Display order (source marker shown)",
        "source_ids": ["SRC-029", "SRC-040", "SRC-065", "SRC-066"],
        "edition": "The EOTC printed-Bible text block identified as xml:id=EOTCed in Beta maṣāḥǝft TEI record LIT1340EnochE.",
        "edition_scope": "This reader uses only the TEI block xml:id=EOTCed, which the source labels “Text of the EOTC printed Bible.” The TEI says this edition was digitized by partner projects from modern Vulgata printed editions and converted to XML by the Beta maṣāḥǝft team; it does not identify the exact printed exemplar or its date. The separate edition xml:id=ed1, following Dillmann’s 1851 critical edition and carrying an explicit noncommercial/no-sale restriction, is excluded from this extract and reader.",
        "chapter_structure_note": "Preserves the EOTCed block’s 108 chapter divisions in source order and each <l n> label. Display order is used for navigation; the source label is shown beside it. Chapter 21 begins with source marker 2, so the reader does not silently invent or normalize a marker 1. The source labels its text as an EOTC printed-Bible edition, but the exact physical printed witness is unspecified.",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "parent_source_sha256": PARENT_SHA256,
        "source_path": "readers/source/enoch/LIT1340EnochE-EOTCed.xml",
        "chapter_count": len(chapters),
        "verse_marker_count": total_lines,
        "verification_status": "Parsed offline from the locally stored EOTCed-only TEI extract. Structural checks confirm chapters 1–108 in order, 1,058 nonempty labeled lines, increasing source markers within each chapter, and the documented chapter 21 starting marker 2. The 1,058 count matches Source Text’s displayed count, but its hosted text was not compared line by line. No independent printed-page or manuscript collation was performed, and the exact print exemplar is not identified.",
        "copyright_notice": "CC BY-SA 4.0 as stated in the Beta maṣāḥǝft TEI file and the Source Text edition record. Attribute Beta maṣāḥǝft and identify this as an EOTCed-only extract; adaptations must be shared under the same license and changes indicated. The separate Edition 1 noncommercial/no-sale notice does not apply to this extract, which contains no Edition 1 text.",
        "commercial_use": "Permitted under CC BY-SA 4.0 with attribution and ShareAlike terms for the selected EOTCed text; this does not grant rights to other editions or source-site presentation.",
        "chapters": chapters,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(ROOT / "examples" / "enoch-geez-eotc-layer.json", OUTPUT)
    print(f"Built {OUTPUT.name}: {len(chapters)} chapters, {total_lines} labeled lines; Edition 1 excluded.")


if __name__ == "__main__":
    main()
