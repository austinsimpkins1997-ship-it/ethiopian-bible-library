"""Structurally audit the locally archived CrossWire Ge'ez SWORD module.

This decodes zText book blocks only far enough to verify block lengths and
OSIS book/chapter identifiers against the locally bundled readers. It does
not export verse text or claim verse-level completeness or textual collation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib


ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "readers" / "source" / "crosswire" / "Geez.zip"
OUTPUT = ROOT / "readers" / "source" / "crosswire" / "module-structure-audit.json"
TEXT_ROOT = "modules/texts/ztext/geez/"
BLOCKS = [
    (0, None, []),
    (1, "Gen", ["genesis-geez.json", 50]),
    (2, "Exod", ["exodus-geez.json", 40]),
    (3, "Lev", ["leviticus-geez.json", 27]),
    (4, "Num", ["numbers-geez.json", 36]),
    (5, "Deut", ["deuteronomy-geez.json", 34]),
    (6, "Josh", ["joshua-geez.json", 24]),
    (7, "Judg", ["judges-geez.json", 21]),
    (8, "Ruth", ["ruth-geez.json", 4]),
    (9, "Ps", ["psalms-geez-ludolf.json", 150]),
    (10, "Ps", ["psalms-geez-ludolf.json", 151]),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_audit() -> dict:
    if not MODULE.is_file():
        raise ValueError("The archived CrossWire Geez.zip source package is missing.")

    with zipfile.ZipFile(MODULE) as package:
        if package.testzip() is not None:
            raise ValueError("A member in the CrossWire module ZIP failed its CRC check.")
        members = set(package.namelist())
        names = {
            "mods.d/geez.conf",
            f"{TEXT_ROOT}ot.bzs",
            f"{TEXT_ROOT}ot.bzz",
            f"{TEXT_ROOT}ot.bzv",
        }
        if not names <= members:
            raise ValueError(f"CrossWire module ZIP is missing members: {sorted(names - members)}")

        conf_bytes = package.read("mods.d/geez.conf")
        conf = conf_bytes.decode("cp1252", errors="replace")
        values = dict(re.findall(r"^([A-Za-z0-9_]+)=(.*)$", conf, re.MULTILINE))
        if (values.get("ModDrv") != "zText" or values.get("CompressType") != "ZIP"
                or values.get("BlockType") != "BOOK" or values.get("Encoding") != "UTF-8"
                or values.get("Lang") != "gez"):
            raise ValueError("The module configuration does not match the inspected zText ZIP/BOOK Geʽez profile.")
        if values.get("Version") != "1.0.1" or "NONCOMMERCIAL" not in conf:
            raise ValueError("The module identity or its retained noncommercial notice changed.")

        block_index = package.read(f"{TEXT_ROOT}ot.bzs")
        compressed_data = package.read(f"{TEXT_ROOT}ot.bzz")
        verse_index = package.read(f"{TEXT_ROOT}ot.bzv")
        if len(block_index) % 12:
            raise ValueError("The SWORD compressed-block index has a partial 12-byte record.")
        if len(verse_index) % 10:
            raise ValueError("The SWORD verse index has a partial 10-byte record.")

        block_count = len(block_index) // 12
        if block_count != len(BLOCKS):
            raise ValueError(f"Expected {len(BLOCKS)} inspected CrossWire data blocks; found {block_count}.")
        report_blocks = []
        for expected_number, osis_book, reader_spec in BLOCKS:
            offset, compressed_size, uncompressed_size = struct.unpack_from(
                "<III", block_index, expected_number * 12
            )
            end = offset + compressed_size
            if compressed_size <= 0 or end > len(compressed_data):
                raise ValueError(f"CrossWire block {expected_number} points outside ot.bzz.")
            raw = zlib.decompress(compressed_data[offset:end])
            if len(raw) != uncompressed_size:
                raise ValueError(
                    f"CrossWire block {expected_number} expands to {len(raw)} bytes; index says {uncompressed_size}."
                )
            decoded = raw.decode("utf-8")
            book_ids = re.findall(r'<div\s+osisID="([^"]+)"', decoded)
            chapter_ids = re.findall(r'<chapter\s+osisID="([^"]+)"', decoded)
            if osis_book is None:
                if book_ids or chapter_ids:
                    raise ValueError("CrossWire introduction block unexpectedly contains scripture book/chapter IDs.")
                report_blocks.append({
                    "block": expected_number,
                    "role": "module_import_metadata",
                    "uncompressed_bytes": len(raw),
                    "sha256": sha256(raw),
                })
                continue

            if osis_book == "Ps" and expected_number == 10:
                expected_ids = ["Ps.151"]
            else:
                expected_ids = [f"{osis_book}.{chapter}" for chapter in range(1, reader_spec[1] + 1)]
            expected_book_ids = [] if osis_book == "Ps" and expected_number == 10 else [osis_book]
            if book_ids != expected_book_ids or chapter_ids != expected_ids:
                raise ValueError(
                    f"CrossWire block {expected_number} OSIS identifiers do not match the expected {osis_book} chapter sequence."
                )

            reader_path = ROOT / "readers" / reader_spec[0]
            reader = json.loads(reader_path.read_text(encoding="utf-8"))
            reader_numbers = [chapter.get("chapter") for chapter in reader.get("chapters", [])]
            expected_reader_numbers = [int(chapter_id.rsplit(".", 1)[1]) for chapter_id in expected_ids]
            if (reader.get("chapter_count") != len(reader_numbers)
                    or reader_numbers != sorted(set(reader_numbers))
                    or not set(expected_reader_numbers) <= set(reader_numbers)):
                raise ValueError(f"{reader_path.name} does not include the expected ordered chapter sequence.")

            report_blocks.append({
                "block": expected_number,
                "role": "scripture_structure",
                "osis_book_id": osis_book,
                "chapter_count": len(chapter_ids),
                "chapter_id_first": chapter_ids[0],
                "chapter_id_last": chapter_ids[-1],
                "reader_path": f"readers/{reader_path.name}",
                "reader_total_chapter_count": len(reader_numbers),
                "reader_chapters_checked": expected_reader_numbers,
                "chapter_count_matches_reader": True,
                "uncompressed_bytes": len(raw),
                "sha256": sha256(raw),
            })

    return {
        "audit_version": 1,
        "audit_kind": "SWORD zText structural audit; no verse text exported",
        "module_path": "readers/source/crosswire/Geez.zip",
        "module_sha256": sha256(MODULE.read_bytes()),
        "module_version": values["Version"],
        "module_release_date": values["SwordVersionDate"],
        "encoding": values["Encoding"],
        "language_tag": values["Lang"],
        "compression": values["CompressType"],
        "block_type": values["BlockType"],
        "retained_rights_notice": "© Ran HaCohen; noncommercial copying/distribution only when notice accompanies every copy; other uses require contacting rights holder.",
        "internal_files": {
            "ot.bzs": {"bytes": len(block_index), "records": len(block_index) // 12, "sha256": sha256(block_index)},
            "ot.bzz": {"bytes": len(compressed_data), "sha256": sha256(compressed_data)},
            "ot.bzv": {"bytes": len(verse_index), "records": len(verse_index) // 10, "sha256": sha256(verse_index)},
        },
        "blocks": report_blocks,
        "interpretation_boundary": (
            "This deterministic audit checks ZIP CRCs, zText block bounds and decompressed lengths, UTF-8 decoding, OSIS book/chapter identifiers, and chapter-count agreement with local reader records. "
            "The SWORD module identifies the same digitizer and corpus as the locally captured HaCohen pages; it is another encoding of the cited corpus, not an independent textual witness. "
            "No verse text was exported, and this does not verify verse coverage, wording, translation, manuscript accuracy, or completeness."
        ),
    }


def main() -> None:
    audit = build_audit()
    OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checked = sum(block.get("chapter_count_matches_reader", False) for block in audit["blocks"])
    print(f"Audited {len(audit['blocks'])} SWORD blocks; {checked} reader-linked blocks match chapter totals. No verse text exported.")


if __name__ == "__main__":
    main()
