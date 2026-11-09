"""Record Beta maṣāḥǝft's Abṭelisāt witness lead without copying its text."""

from __future__ import annotations

import json
from archive_manifest import write_text_atomically
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-285"
EDITION_ID = "betamasaheft-abtelisat-81-ca2677"
SOURCE_URL = "https://betamasaheft.awhamburg.de/works/LIT2677ACABt1/main"
WITNESS_URL = "https://betamasaheft.awhamburg.de/manuscripts/AGmasTefut1/main"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Beta maṣāḥǝft — Apostolic canons Abṭelisāt (81), CAe 2677",
        "url": SOURCE_URL,
        "inspection_and_limitations": (
            "Beta maṣāḥǝft catalogs Apostolic canons Abṭelisāt (81), CAe 2677, as an Ethiopic textual unit; "
            "its manuscript record for ʾAmbā Gǝšan Māryām, Maṣḥafa ṭefut lists a first recension of 81 at ff. "
            "174v–177r and a separate 56-canons unit at ff. 172v–174v. The catalogue distinguishes 81- and "
            "56-canon works, and its witness record also notes an 80-canon second recension. This is a title/work "
            "lead for the Church-list Abtilis entry, not proof of an exact Church-list crosswalk or of one stable "
            "text. Manuscript images and text were not inspected or copied. The Beta page presents both a file-level "
            "CC BY-SA 4.0 statement and a site-level CC BY-NC-SA 4.0 notice; their relationship and underlying "
            "witness rights remain unresolved. Inspected 2026-10-25."
        ),
        "archive_status": (
            "Catalogued Geʽez textual-unit and manuscript-witness lead; no text bundled; 81/80/56 recension and "
            "Church-list crosswalk distinctions retained; rights unresolved"
        ),
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))

    catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-085")
    catalogue.update({
        "alternate_names_or_notes": "Beta maṣāḥǝft records Apostolic canons Abṭelisāt (81), CAe 2677; manuscript witnesses also record an 80-canon second recension. The separate Apostolic canons (56), CAe 2670, are not the same catalogue record.",
        "identity_status": "Title/work-family lead only; exact Church-list mapping and recension are not verified",
        "edition_or_translation": "Beta maṣāḥǝft CAe 2677 record; manuscript witness AGmasTefut1 ff. 174v–177r is labeled first recension (81); no text bundled",
        "text_availability_status": "External catalogue and manuscript description available; text and images not captured in this archive",
        "completeness_status": "Not assessed; manuscript witnesses include variant canon counts",
        "rights_status": "Unresolved: Beta file-level CC BY-SA 4.0 and site-level CC BY-NC-SA 4.0 notices coexist; no text copied",
        "verification_date": "2026-10-25",
        "source_id": SOURCE_ID,
        "evidence_source_ids": ["SRC-029", "SRC-073", "SRC-210", "SRC-211", SOURCE_ID],
        "reviewer_notes": (
            "Beta maṣāḥǝft catalogs Abṭelisāt (81), CAe 2677, and documents recension variation in manuscript witnesses. "
            "Its AGmasTefut1 record distinguishes an 81-canon Abṭelisāt witness from a neighboring 56-canons unit; "
            "the latter is not silently equated with Abtilis. A separate witness has an 80-canon second recension. "
            "This supports discovery and title-family comparison only. Exact identity with the Church's Abtilis entry, "
            "text boundaries, completeness, and rights remain unresolved."
        ),
    })
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[EDITION_ID] = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": "eotc-nt-31",
        "mapping_state": "uncertain",
        "title": "Apostolic canons Abṭelisāt (81) — Beta maṣāḥǝft CAe 2677",
        "witness_type": "manuscript",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "Beta maṣāḥǝft catalogs CAe 2677 as Apostolic canons Abṭelisāt (81). Its AGmasTefut1 witness record "
            "labels ff. 174v–177r as the first 81-canon recension and separately lists Apostolic canons (56) at ff. 172v–174v."
        ),
        "scope_description": (
            "A scholarly work record and manuscript description make this a relevant Abtilis title-family lead, "
            "not an exact Church-list crosswalk. Beta records recension differences, including an 80-canon second "
            "recension. The separately cataloged 56-canons unit is explicitly distinguished. No witness text or "
            "image is bundled, and no completeness or translation claim is made."
        ),
        "source_ids": ["SRC-029", "SRC-073", "SRC-210", "SRC-211", SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "Unresolved. The Beta page shows a file-level CC BY-SA 4.0 statement and site-level CC BY-NC-SA 4.0 "
            "notice; their relationship and manuscript-text rights were not determined. No text copied."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "Work and manuscript catalogue metadata inspected; manuscript text and images not inspected or copied. "
            "The exact Church-list mapping, recension, boundaries, completeness, and reuse rights remain unverified."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = (
        "# Abtilis source review\n\n"
        f"[Beta maṣāḥǝft's work record]({SOURCE_URL}) catalogs Apostolic canons Abṭelisāt (81), CAe 2677. "
        f"Its [Maṣḥafa ṭefut manuscript record]({WITNESS_URL}) labels ff. 174v–177r as the first recension (81); "
        "the same manuscript separately lists Apostolic canons (56) on ff. 172v–174v. Other catalogue records show "
        "recension variation, including an 80-canon second recension. These are distinct catalogue units and counts; "
        "the archive does not collapse them into one text.\n\n"
        "The record is a discovery lead for the Church-list Abtilis title, not an exact canon crosswalk. No manuscript "
        "text or image was captured. Beta displays a file-level CC BY-SA 4.0 notice and a site-level CC BY-NC-SA 4.0 "
        "notice; their relationship and underlying manuscript rights remain unresolved. The lead is unbundled and "
        "does not increase reader coverage.\n"
    )
    (ROOT / "research" / "abtilis-source-review.md").write_text(report, encoding="utf-8")
    print("Recorded Abtilis as an unbundled, recension-aware Beta discovery lead.")


if __name__ == "__main__":
    build()
