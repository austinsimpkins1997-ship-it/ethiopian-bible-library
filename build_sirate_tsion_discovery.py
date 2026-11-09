"""Record the possible Sirate Tsion/Canons after Ascension relation as uncertain."""

from __future__ import annotations

import json
from archive_manifest import write_text_atomically
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-289"
COMMUNITY_LIST_SOURCE_ID = "SRC-442"
EDITION_ID = "betamasaheft-canons-after-ascension-cae2673"
WORK_URL = "https://betamasaheft.awhamburg.de/works/LIT2673CanonsAscension/main"
WITNESS_URL = "https://betamasaheft.awhamburg.de/manuscripts/BLorient794/main"
COMMUNITY_LIST_URL = "https://eotcmk.org/e/holy-scriptures/"


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Beta maṣāḥǝft — Apostolic Canons after Ascension (CAe 2673) in BL Oriental 794",
        "url": WITNESS_URL,
        "inspection_and_limitations": (
            "Beta maṣāḥǝft's manuscript record for British Library Oriental 794 describes a Geʽez Sinodos codex "
            "dated palaeographically to 1400–1450 and places Canons of the Apostles after the Ascension of our Lord, "
            "29 in number, at ff. 71v–77v; it identifies the unit as CAe 2673. Beta's corresponding work record is "
            f"{WORK_URL}. The manuscript description is encoded from catalogues, not from a new inspection of the "
            "codex or its images. Lexham and Cowley suggest that a text called Serʽatä Seyon in canon lists may relate "
            "to Canons after the Ascension, but they explicitly leave that identification uncertain. The Church-list "
            "entry is reported as 30 canons, while this witness says 29; the counts are not reconciled. No text or "
            "image copied. Inspected 2026-10-25."
        ),
        "archive_status": (
            "Primary catalogue metadata for a Geʽez witness; plausible but explicitly uncertain Sirate Tsion lead; "
            "29-vs-30 canon discrepancy preserved; no text bundled"
        ),
    }
    sources[COMMUNITY_LIST_SOURCE_ID] = {
        "source_id": COMMUNITY_LIST_SOURCE_ID,
        "source_name": "Mahibere Kidusan — Ethiopian Orthodox Tewahedo Church Sunday School Department, “Holy Scriptures”",
        "url": COMMUNITY_LIST_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-27. This Church Sunday School Department page lists 46 Old Testament and 35 New Testament entries, "
            "names “Sirate Tsion (the book of order)” as New Testament entry 28, and separately identifies broader church-order and "
            "theological literature. It cites A Short History, Faith and Order of the Ethiopian Orthodox Tewahido Church (Holy Synod, "
            "Addis Ababa, 1983) and The Ethiopian Orthodox Church (Aymero W. and Joachim M., 1970) in its source note. This corroborates "
            "the displayed Church-list title and its place in the 81-entry list; it is not a manuscript witness, a text edition, or evidence "
            "that the 29-canons CAe 2673 witness is identical to the entry. The 29/30 discrepancy and exact crosswalk remain unresolved. No "
            "text or images copied."
        ),
        "archive_status": (
            "Church Sunday School Department source corroborating the displayed 81-entry list and Sirate Tsion title/order; "
            "not a text witness or proof of the CAe 2673 crosswalk"
        ),
        "rights_classification": "unknown",
        "rights_status": "No page text is copied beyond short bibliographic/title references. Reuse terms were not assessed; citation is not a reuse license.",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))
    catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-082")
    catalogue.update({
        "alternate_names_or_notes": (
            "Serʽatä Seyon is a scholarly romanization of the canon-list form Sirate Tsion. Cowley/Lexham suggest "
            "a possible relation to Canons after the Ascension of our Lord (CAe 2673); exact identification remains uncertain."
        ),
        "identity_status": "Possible work-family relation only; exact Church-list crosswalk not verified",
        "edition_or_translation": (
            "Beta maṣāḥǝft CAe 2673 candidate: BL Oriental 794, ff. 71v–77v, catalogued as 29 Canons of the Apostles after the Ascension; "
            "palaeographic date 1400–1450. This witness count differs from the 30-canons list description."
        ),
        "chapter_count": "Not established; candidate manuscript record describes 29 canons, while scholarly canon lists report 30 for Serʽatä Seyon",
        "chapter_order_status": "Not assessed against the Church-list entry",
        "text_availability_status": "Manuscript catalogue record identified; no text or image captured here",
        "completeness_status": "Not assessed; canon-count discrepancy unresolved",
        "rights_status": "No text or image copied; rights and access terms for manuscript images not assessed",
        "verification_date": "2026-10-25",
        "source_id": SOURCE_ID,
        "evidence_source_ids": ["SRC-029", "SRC-073", "SRC-210", "SRC-211", SOURCE_ID, COMMUNITY_LIST_SOURCE_ID],
        "reviewer_notes": (
            "The possible identification is supported as a research hypothesis by Cowley/Lexham's comparison and a "
            "catalogued Geʽez witness of Canons after the Ascension (CAe 2673). The witness is not titled Serʽatä "
            "Seyon in the catalogue and contains 29 canons, against 30 reported for the Church-list title. Do not "
            "treat those differences as reconciled or as proof of a complete text crosswalk."
        ),
    })
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[EDITION_ID] = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": "eotc-nt-28",
        "mapping_state": "uncertain",
        "title": "Canons of the Apostles after the Ascension — Beta maṣāḥǝft CAe 2673 / BL Oriental 794",
        "witness_type": "manuscript",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "Beta maṣāḥǝft catalogues BL Oriental 794, ff. 71v–77v, as 29 Canons of the Apostles after the Ascension of our Lord (CAe 2673); "
            "the manuscript is palaeographically dated 1400–1450."
        ),
        "scope_description": (
            "Candidate relation to Church-list Sirate Tsion (Serʽatä Seyon) only: Cowley/Lexham suggest these may be related, "
            "but the identification is explicitly uncertain. The canon-list description gives 30, whereas this witness has 29; "
            "no text boundary or count reconciliation is established. Metadata lead only; no text is bundled."
        ),
        "source_ids": ["SRC-029", "SRC-073", "SRC-210", "SRC-211", SOURCE_ID],
        "text_bundled": False,
        "rights_status": "No text copied or bundled; rights and access terms for manuscript images were not assessed.",
        "rights_classification": "unknown",
        "review_status": (
            "Beta maṣāḥǝft catalogue metadata and secondary canon discussion reviewed. Codex, images, and text were not inspected. "
            "The 29-versus-30 canon discrepancy, exact Church-list mapping, completeness, and reuse rights remain unresolved."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = (
        "# Sirate Tsion source review\n\n"
        f"The [Mahibere Kidusan Church Sunday School Department page]({COMMUNITY_LIST_URL}) lists Sirate Tsion as New Testament entry 28 and states the list has 46 Old Testament and 35 New Testament entries. It cites Church publications from 1983 and 1970. This supports the title and placement in that displayed list, not the identity of any particular manuscript witness.\n\n"
        f"Beta maṣāḥǝft's [work record]({WORK_URL}) identifies the Geʽez unit as Canons of the Apostles after Ascension, CAe 2673. "
        f"Its [British Library Oriental 794 record]({WITNESS_URL}) places a 29-canon witness at folios 71v–77v in a manuscript dated palaeographically to 1400–1450.\n\n"
        "Cowley and the Lexham Bible Dictionary report Serʽatä Seyon (Sirate Tsion) as a 30-canon broader-canon title and suggest it may correspond to Canons after the Ascension. Lexham explicitly says the relation is unclear. The witness title is different and its count is 29, so the archive records a candidate only and preserves the discrepancy. No text or image is bundled.\n\n"
        "This catalogue record is encoded from manuscript catalogues; the archive did not inspect the codex, images, or wording. The candidate does not verify the Church-list crosswalk, textual boundaries, completeness, or reuse rights.\n"
    )
    (ROOT / "research" / "sirate-tsion-source-review.md").write_text(report, encoding="utf-8")
    print("Recorded a provisional Sirate Tsion witness lead; 29/30 canon counts remain unresolved.")


if __name__ == "__main__":
    build()
