"""Record the source-backed, rights-limited Isaiah edition lead."""

import json
from pathlib import Path
from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
ARCHIVE_PATH = ROOT / "archive.json"
REGISTRY_PATH = ROOT / "translation-registry.json"


def build():
    archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources["SRC-276"] = {
        "source_id": "SRC-276",
        "source_name": "Tel Aviv University — Isaiah image edition information page (Bachmann 1893)",
        "url": "https://www.tau.ac.il/~hacohen/Jesaia/Information.html",
        "inspection_and_limitations": (
            "TAU identifies Johannes Bachmann (ed.), Der Prophet Jesaia nach der aethiopischen Bibeluebersetzung, "
            "I. Teil: Der aethiopische Text (Berlin, 1893). The page describes an internet image version of the "
            "Ethiopic book following that critical edition, says Bachmann’s text was scanned and errata corrected, "
            "and says each chapter is directly accessible from the main menu. It says the planned second part, "
            "on the text’s relation to the Septuagint, apparently was never published. These are provider statements; "
            "the chapter-page sequence, complete extent, image/text completeness, wording accuracy, current EOTC "
            "edition relationship, and item-specific reuse rights have not been audited. Inspected 2026-10-25; "
            "no text or image copied."
        ),
        "archive_status": "Primary source-edition information page; discovery lead only, no text bundled",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))
    write_text_atomically(ARCHIVE_PATH, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    edition_id = "bachmann-ethiopic-isaiah-1893-tau"
    registry["edition_leads"] = [
        item for item in registry["edition_leads"] if item["edition_id"] != edition_id
    ]
    registry["edition_leads"].append({
        "edition_id": edition_id,
        "candidate_canon_id": "eotc-ot-29",
        "mapping_state": "uncertain",
        "title": "Prophet Isaiah — Bachmann Ethiopic edition (1893), TAU image version",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": "Johannes Bachmann (ed.), Der Prophet Jesaia nach der aethiopischen Bibeluebersetzung, I. Teil: Der aethiopische Text (Berlin, 1893); TAU describes its copy as an internet image version.",
        "scope_description": (
            "TAU identifies the Ethiopic book and Bachmann’s 1893 critical edition, reports that the text was scanned "
            "and errata corrected, and says chapter pages are accessible from its menu. The exact page sequence and "
            "chapter count have not been inventoried, so the page statement does not establish complete coverage. "
            "The separate second part on the relation to the Septuagint is reported as apparently unpublished. "
            "This is an edition-level discovery lead, not proof of identity with a current EOTC edition, completeness, "
            "or wording accuracy; no text is bundled."
        ),
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", "SRC-276"],
        "text_bundled": False,
        "rights_status": (
            "TAU’s general notice permits noncommercial use, copying, and distribution of digitized Ethiopic texts "
            "only with its required copyright and permission notices; other uses require contacting the copyright "
            "owner. This archive does not bundle the text. The notice is not an unrestricted or commercial grant."
        ),
        "rights_classification": "permission_limited",
        "review_status": (
            "TAU Isaiah information page and general reuse notice inspected 2026-10-25. Bibliographic identity, "
            "provider-described image version, scan/errata statements, chapter-access claim, unpublished-second-part "
            "qualification, and site-wide noncommercial notice recorded. No page inventory, text extraction, accuracy "
            "review, current-edition comparison, or completeness audit performed."
        ),
    })
    registry["edition_leads"].sort(key=lambda item: item["edition_id"])
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
