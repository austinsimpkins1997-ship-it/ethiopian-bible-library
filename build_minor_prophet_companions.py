"""Rebuild five retained Geʽez texts with separate, Greek-basis English witnesses.

All copying is offline. Matching labels support navigation, never equivalence.
Chapter-divergent and source-anomalous candidates are deliberately not admitted.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import zipfile

import build_brenton_octateuch as brenton
from build_brenton_research_readers import build_records, CANDIDATE_CANON_LINKS

ROOT = Path(__file__).resolve().parent
AS_OF = "2026-11-16"
PAIRS = (
    ("OBA", "obadiah", "obadiah-geez-bachmann-theot", 1),
    ("JON", "jonah", "jonah-geez-lofgren-ghebre-tau", 4),
    ("NAM", "nahum", "nahum-geez-lofgren-ghebre-tau", 3),
    ("ZEP", "zephaniah", "zephaniah-geez-lofgren-hacohen-tau", 3),
    ("HAG", "haggai", "haggai-geez-lofgren-ghebre-tau", 2),
)
BOUNDARY = (
    "Separate historical English translation from Greek, not translated from this Geʽez witness. "
    "Shared printed labels are navigation aids only; textual equivalence, verse alignment, "
    "current EOTC edition identity and print completeness remain unverified. "
    "Unmatched units must remain visible; neither witness is renumbered or corrected to fit the other."
)


def serialize(record: dict) -> bytes:
    return (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def prepare_pair(source: dict, english: dict, companion: dict, *, code: str) -> dict:
    """Validate the admitted pair before copying; preserve every original unit."""
    spec = next((row for row in PAIRS if row[0] == code), None)
    if spec is None:
        raise ValueError("Candidate is outside the reviewed five-book batch.")
    _, _, reader_id, expected = spec
    if source.get("reader_id") != reader_id or english.get("reader_id") != f"brenton-lxx-{code.lower()}-research":
        raise ValueError("Witness identity differs from the declared pair.")
    if (source.get("rights_classification") != "permission_limited"
            or not source.get("copyright_notice")
            or english.get("rights_classification") != "public_domain_claimed"
            or not english.get("copyright_notice")):
        raise ValueError("Required separate rights classifications/notices are missing.")
    if english.get("translation_path") != ["grc", "en"]:
        raise ValueError("English witness must retain its Greek-to-English basis.")
    expected_sequence = list(range(1, expected + 1))
    for witness in (source, english, companion):
        if (witness.get("chapter_count") != expected
                or [c.get("chapter") for c in witness.get("chapters", [])] != expected_sequence):
            raise ValueError("Chapter sequence differs; hold this pair for explicit mapping review.")
    if companion.get("chapters") != english.get("chapters"):
        raise ValueError("Stored English reader differs from the freshly parsed retained member.")
    if (companion.get("source_member_sha256") != english.get("source_member_sha256")
            or companion.get("source_package_sha256") != english.get("source_package_sha256")):
        raise ValueError("English source digests disagree.")
    result = copy.deepcopy(source)
    companion = copy.deepcopy(companion)
    companion["translation_basis"] = BOUNDARY
    companion["verification_status"] += " " + BOUNDARY
    result["parallel_translation"] = companion
    result["source_ids"] = sorted(set(result["source_ids"]) | set(companion["source_ids"]))
    if "additional_notes" in result:
        result["additional_notes"] = "The primary text remains the captured Geʽez transcription. " + BOUNDARY
    return result


def build() -> list[dict]:
    # This independently reparses the pinned archive and checks its full digest.
    english_readers = {r["reader_id"]: r for r in build_records()[0]}
    manifest = json.loads(brenton.MANIFEST.read_text(encoding="utf-8"))
    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    en_registry = next(lang for lang in registry["languages"] if lang["language_tag"] == "en")
    pending = []
    reports = []
    with zipfile.ZipFile(brenton.PACKAGE) as package:
        for code, slug, reader_id, expected in PAIRS:
            module = importlib.import_module(f"build_{slug}_reader")
            source, source_layer = module.build()  # checks retained capture hashes and labels
            english = english_readers[f"brenton-lxx-{code.lower()}-research"]
            stored = json.loads((ROOT / "readers" / f"{english['reader_id']}.json").read_text(encoding="utf-8"))
            # The standalone build adds bounded language/rights display notes.
            # Compare all owning-builder fields, without rejecting those two annotations.
            if ({key: stored.get(key) for key in english} != english
                    or set(stored) - set(english) - {"language_assignment_status", "rights_status"}):
                raise ValueError(f"Rebuild stale English source reader before pairing: {english['reader_id']}")
            member = next(name for name in manifest["selected_members"] if f"-{code}eng-Brenton.usfm" in name)
            raw = package.read(member)
            pin = manifest["selected_members"][member]
            if hashlib.sha256(raw).hexdigest() != pin["sha256"] or len(raw) != pin["byte_length"]:
                raise ValueError(f"Retained member differs from capture manifest: {member}")
            previous = brenton.BOOKS.get(code)
            brenton.BOOKS[code] = (code.lower(), 0, slug.title(), expected)
            try:
                companion = brenton.parse_usfm(raw, code, member, manifest["archive_sha256"])
            finally:
                if previous is None:
                    brenton.BOOKS.pop(code, None)
                else:
                    brenton.BOOKS[code] = previous
            reader = prepare_pair(source, english, companion, code=code)
            digest = hashlib.sha256(serialize(reader)).hexdigest()
            source_layer["content_package"]["sha256"] = digest
            source_layer["additional_notes"] = (
                "This record describes only the captured Geʽez layer. The shared JSON package also "
                "contains a separately identified English companion. " + BOUNDARY
            )
            canon_id, candidate_note = CANDIDATE_CANON_LINKS[code]
            layer = brenton.make_layer(slug, slug.title(), canon_id, reader["parallel_translation"], module.READER_PATH.name)
            layer["content_package"]["sha256"] = digest
            assertion = layer["tradition_assertions"][0]
            assertion.update(mapping_state="uncertain", evidence_source_ids=["SRC-029", "SRC-038", "SRC-142"], notes=candidate_note)
            for review in layer["review_dimensions"]:
                if review.get("reviewed_at") is not None:
                    review["reviewed_at"] = AS_OF
            layer["additional_notes"] = BOUNDARY + " " + candidate_note
            registry_record = {
                "canon_id": canon_id, "reader_id": reader_id,
                "translation_id": companion["translation_id"],
                "layer_role": "historical_companion_translation", "status": "bundled",
                "translator": companion["translator"], "basis_language_tag": "grc",
                "basis_description": BOUNDARY, "rights_status": "public_domain_per_cited_source",
                "source_ids": ["SRC-038", "SRC-142"], "translation_path": ["grc", "en"],
                "rights_classification": "public_domain_claimed",
            }
            matches = [item for item in en_registry["records"] if item.get("translation_id") == companion["translation_id"]]
            if len(matches) > 1 or any(item.get("reader_id") != reader_id for item in matches):
                raise ValueError(f"Translation registry collision: {companion['translation_id']}")
            en_registry["records"] = [item for item in en_registry["records"] if item.get("translation_id") != companion["translation_id"]] + [registry_record]
            rows = []
            for first, second in zip(source["chapters"], companion["chapters"], strict=True):
                a = [str(v.get("source_marker", v.get("number", ""))) for v in first["verses"]]
                b = [str(v["number"]) for v in second["verses"]]
                rows.append({"chapter": first["chapter"], "source_labels": a, "english_labels": b,
                             "source_only_labels": [x for x in a if x not in b],
                             "english_only_labels": [x for x in b if x not in a]})
            reports.append({"reader_id": reader_id, "english_reader_id": english["reader_id"],
                            "source_member": member, "source_member_sha256": pin["sha256"],
                            "source_units": source["unit_count"], "english_units": companion["unit_count"],
                            "chapters": rows, "alignment_status": "unverified_navigation_only"})
            pending.extend([(module.READER_PATH, reader), (module.LAYER_PATH, source_layer),
                            (ROOT / "examples" / f"{slug}-brenton-translation-layer.json", layer)])
    # Finish all preflights before writing any of this batch's outputs.
    for path, record in pending + [(registry_path, registry)]:
        path.write_bytes(serialize(record))
    report = {"as_of": AS_OF, "scope": BOUNDARY, "pairs": reports}
    (ROOT / "research" / "minor-prophet-parallel-review.json").write_bytes(serialize(report))
    print(f"Built {len(reports)} separate historical companions; alignment remains unverified.")
    return reports


if __name__ == "__main__":
    build()
