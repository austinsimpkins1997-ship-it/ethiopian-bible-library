"""Keep source-backed Chronicles edition leads in the archive inputs."""

import hashlib
import json
import re
from pathlib import Path
from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
ARCHIVE_PATH = ROOT / "archive.json"
REGISTRY_PATH = ROOT / "translation-registry.json"
CAPTURE_DIR = ROOT / "readers" / "source" / "chronicles-tau-grebaut"
CAPTURE_SOURCE_ID = "SRC-338"


def _verify_capture() -> tuple[dict, list[dict], str]:
    manifest = json.loads((CAPTURE_DIR / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    files = {item["path"]: item for item in manifest.get("files", [])}
    for name, item in files.items():
        raw = (CAPTURE_DIR / name).read_bytes()
        if (item.get("http_status") != 200 or len(raw) != item.get("size_bytes")
                or hashlib.sha256(raw).hexdigest() != item.get("sha256")):
            raise ValueError(f"Chronicles source capture failed its HTTP/size/SHA check: {name}")
    pages = [item for item in files.values() if item.get("menu_label") is not None]
    counts = {
        "I": sum(item["path"].startswith("chronicles-i-") for item in pages),
        "II": sum(item["path"].startswith("chronicles-ii-") for item in pages),
    }
    if counts != {"I": 29, "II": 36}:
        raise ValueError(f"Unexpected TAU Chronicles menu capture counts: {counts!r}")
    image_refs = []
    for item in pages:
        html = (CAPTURE_DIR / item["path"]).read_text(encoding="ascii")
        matches = re.findall(r"<img[^>]+src=['\"]([^'\"]+)['\"]", html, flags=re.I)
        if len(matches) != 1 or not matches[0].lower().endswith(".png"):
            raise ValueError(f"Expected one scanned-page PNG reference in {item['path']}; found {matches!r}")
        image_refs.append(matches[0])
    image_summary = (
        f"The {len(pages)} menu page wrappers each reference one PNG scan ({len(set(image_refs))} distinct image paths); "
        "the image files themselves are not included in this capture. These wrappers contain no OCR/transcribed verse layer."
    )
    context = "; ".join(
        f"{name} {item['size_bytes']} bytes SHA-256 {item['sha256']}"
        for name, item in files.items() if item.get("menu_label") is None
    )
    return manifest, pages, image_summary + f" Context files: {context}."


def build():
    archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    manifest, pages, image_summary = _verify_capture()
    if "Paralipomena capture audit 2026-10-26" not in sources["SRC-034"]["inspection_and_limitations"]:
        sources["SRC-034"]["inspection_and_limitations"] += (
            " Paralipomena capture audit 2026-10-26: the two index functions now resolve to separate 29- and 36-item "
            "numbered menus, credited to Grébaut. Locally retained page-wrapper HTML confirms each menu target displays "
            "a PNG scan; no page images or OCR text are bundled. This verifies the observed menu entries and wrapper targets, "
            "not completeness of the printed edition or exact identity with a current EOTC edition. See SRC-338."
        )
    notice = (CAPTURE_DIR / "SOURCE-NOTICE.txt").read_text(encoding="utf-8")
    sources[CAPTURE_SOURCE_ID] = {
        "source_id": CAPTURE_SOURCE_ID,
        "source_name": "Tel Aviv University — Grébaut Ethiopic Chronicles menu and image-page wrappers, locally retained",
        "url": "https://www.tau.ac.il/~hacohen/Paralipomen/Information.html",
        "inspection_and_limitations": (
            f"Captured {len(pages)} menu-listed HTML wrappers: 29 for Paralipomena I and 36 for II. Each file has an "
            "HTTP status, capture time, byte count, URL, and SHA-256 in its manifest. The source information page identifies "
            "Sylvain Grébaut's 1932 Ethiopic edition. " + image_summary + " The package contains neither the PNG scans nor "
            "a text transcription, so this source record does not add a reader or establish full page/edition completeness. "
            "TAU's site-wide notice is noncommercial and requires copyright and permission notices; it is not an open or "
            "commercial license. " + notice.strip()
        ),
        "archive_status": "Verified Chronicles menu and image-page wrappers only; PNG scans and scripture text are not bundled",
    }
    sources["SRC-275"] = {
        "source_id": "SRC-275",
        "source_name": "National Institute of Informatics (Japan) — CiNii Books record for Grébaut, Les Paralipomènes, livres I et II",
        "url": "https://ci.nii.ac.jp/ncid/BA73445318",
        "inspection_and_limitations": (
            "CiNii identifies Sylvain Grébaut, Les Paralipomènes, livres I et II : version éthiopienne, "
            "edited and translated from Bibliothèque nationale manuscript 94 and Abbadie collection "
            "manuscript 35; Patrologia Orientalis 23, fascicle 4; Paris: Firmin-Didot, 1932; 251 pages. "
            "The record specifies Ethiopic and French on each page, Ethiopic as the original language, "
            "and lists two Japanese university-library holdings. It is bibliographic metadata, not "
            "inspection of the book or digital text. It does not establish full text availability, "
            "chapter boundaries, completeness, translation alignment, current EOTC edition identity, "
            "or reuse rights. Inspected 2026-10-25; no text or images copied."
        ),
        "archive_status": "National bibliographic record for a historical Ethiopic edition; discovery lead only, text and rights unverified",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))
    write_text_atomically(ARCHIVE_PATH, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry["edition_leads"]}
    for part, canon_id in (("I", "eotc-ot-11"), ("II", "eotc-ot-12")):
        edition_id = f"grebaut-ethiopic-chronicles-{part.lower()}-1932"
        leads[edition_id] = {
            "edition_id": edition_id,
            "candidate_canon_id": canon_id,
            "mapping_state": "uncertain",
            "title": f"Chronicles {part} — Grébaut, Les Paralipomènes, livres I et II (1932)",
            "witness_type": "printed_edition",
            "language_tag": "gez",
            "language_name": "Geʽez (Classical Ethiopic)",
            "script_code": "Ethi",
            "edition_statement": (
                "Sylvain Grébaut, Les Paralipomènes, livres I et II : version éthiopienne, "
                "Patrologia Orientalis 23, fascicle 4 (Paris: Firmin-Didot, 1932), 251 pages. "
                "CiNii describes Ethiopic and French on each page and identifies Bibliothèque nationale "
                "manuscript 94 and Abbadie collection manuscript 35 as the manuscript basis."
            ),
            "scope_description": (
                f"The edition title explicitly names Books I and II of Chronicles; this record tracks the {part} "
                "title separately because the cited Church list has separate I and II Chronicles entries. "
                "The association is a bibliographic candidate, not proof that this historical edition matches "
                "the Church’s present text or numbering. The cited catalog record describes a bilingual volume "
                "but does not establish whether the French material is a continuous translation aligned to the "
                "Ethiopic text. TAU's separately captured menu contains 29 page pointers for Book I and 36 for Book II; "
                "each page wrapper points to a PNG scan, but no scans or text are bundled. These are observed menu entries, "
                "not proof of complete book/page coverage. Text accuracy, current-edition relationship, and physical completeness "
                "remain unverified."
            ),
            "source_ids": ["SRC-034", "SRC-275", "SRC-029", "SRC-338", "SRC-036"],
            "text_bundled": False,
            "rights_status": "TAU's site-wide notice permits noncommercial copying/distribution of its digitized Ethiopic texts when copyright and permission notices accompany every copy; it is not an open or commercial grant. This package retains only HTML wrappers, not the PNG scans or text. Rights in the underlying 1932 print edition beyond the stated TAU permission remain unresolved.",
            "rights_classification": "mixed",
            "review_status": (
                "TAU’s 2026-10-26 retained index audit resolves the two menus to 29 and 36 numbered page pointers. "
                "All 65 retained page wrappers checksum correctly and each references one PNG scan; no scan payload or "
                "transcribed text is bundled. TAU’s information page identifies Grébaut’s 1932 edition; CiNii records its "
                "stated manuscript basis. This verifies menu/page-wrapper structure only, not print completeness, textual "
                "accuracy, continuous French alignment, or current EOTC edition identity. TAU's reuse notice is limited to "
                "noncommercial use with notices; underlying-edition rights are not independently resolved."
            ),
        }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
