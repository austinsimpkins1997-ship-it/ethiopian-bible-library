"""Record publisher-reported English editions as unbundled, rights-unknown leads."""

from __future__ import annotations

import json
from pathlib import Path

from archive_manifest import write_text_atomically


ROOT = Path(__file__).resolve().parent
SOURCE_ID = "SRC-448"
SOURCE_URL = (
    "https://ethiopianorthodoxbible.wordpress.com/2025/11/05/"
    "important-announcement-new-edition-of-some-eotc-books-in-english-"
    "plus-missing-verses-in-ethiopic-clement-translated-into-english/"
)
REVIEW_PATH = "research/eotc-english-edition-leads.html"

SINODOS_LEADS = [
    {
        "translation_id": "sirate-tsion-en-mikhail-sinodos-2025",
        "canon_id": "eotc-nt-28",
        "title": "Sirate Tsion / Səratä Ṣiyon — reported English Sinodos edition",
        "base": "Horner's 1904 English edition, as reported for the collective Sinodos edition",
        "work": "the Order of Zion section called Səratä Ṣiyon in Horner's 1904 edition",
        "canon_title": "Sirate Tsion (Book of Order)",
    },
    {
        "translation_id": "tizaz-en-mikhail-sinodos-2025",
        "canon_id": "eotc-nt-29",
        "title": "Tizaz / Təʻezaz — reported English Sinodos edition",
        "base": "Horner's 1904 English edition, as reported for the collective Sinodos edition",
        "work": "the Təʻezaz section in Horner's 1904 edition",
        "canon_title": "Tizaz (Book of Herald)",
    },
    {
        "translation_id": "abtilis-en-mikhail-sinodos-2025",
        "canon_id": "eotc-nt-31",
        "title": "Abtilis / ʿAbṭəlis — reported English Sinodos edition",
        "base": "Horner's 1904 English edition, as reported for the collective Sinodos edition",
        "work": "the ʿAbṭəlis section in Horner's 1904 edition",
        "canon_title": "Abtilis",
    },
]


def _sinodos_lead(item: dict) -> dict:
    return {
        "translation_id": item["translation_id"],
        "canon_id": item["canon_id"],
        "title": item["title"],
        "mapping_state": "asserted_by_source",
        "scope_description": (
            "The Ethiopian Orthodox Bible Project's 2025-11-05 announcement describes a released English "
            f"edition of Ethiopic Sinodos and identifies {item['work']}. The announcement says the editor "
            "uses Horner's 1904 English edition as a basis and compares versions; it does not establish a "
            "direct Ge'ez-to-English path for this section. Its placement under the corresponding Church-list "
            f"title is source-asserted only ({item['canon_title']}); the exact published section, boundaries, "
            "edition identity, completeness, wording, and relation to a current Church edition have not been "
            "independently checked. The linked sales listing and book text were not inspected. No text is bundled."
        ),
        "language_tag": "en",
        "translator": (
            "Michael Mikhail (named by the project; his specific translator/editor role for this section is not established)"
        ),
        "edition": (
            "English Ethiopic Sinodos edition; the project reported its release on 2025-11-05. Exact title-page, "
            "publisher, ISBN, and publication record have not been independently verified."
        ),
        "translation_path": None,
        "source_ids": ["SRC-029", SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "Reuse rights for the book text are unknown. The project announcement links to a commercial listing "
            "but grants no text-reuse license. No translation text or listing content is reproduced here."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "Publisher/project report only. The reported Horner basis and named Sinodos components are recorded; "
            "the book, full bibliography, exact wording, section boundaries, completeness, translation accuracy, "
            "and community review have not been examined. This metadata lead is not a reader and does not count "
            "as canon-linked coverage."
        ),
        "notes": (
            f"Reported basis: {item['base']}. The project says its editorial work compares versions and clarifies "
            "terms. Do not describe this as a verified direct Ge'ez translation or as an inspected, complete text."
        ),
    }


def _clement_lead() -> dict:
    return {
        "translation_id": "ethiopic-clement-6-83-86-en-mikhail-2025-lead",
        "canon_id": "eotc-nt-34",
        "title": "Ethiopic Clement 6:83–86 — reported partial English rendering",
        "mapping_state": "uncertain",
        "scope_description": (
            "A 2025-11-05 Ethiopian Orthodox Bible Project announcement reports an English rendering of four "
            "verses (6:83–86) from a manuscript it describes as Amharic, supplemented by S. Grébaut's French "
            "translation. The announcement says verse 83 is rendered solely from French because the surviving "
            "Ethiopic is unintelligible. This is a publisher-reported, partial rendering, not a complete Clement "
            "reader; the exact source manuscript, French passage, edition, wording, and relation to the Church-list "
            "Book of Clement have not been independently verified. No text is bundled."
        ),
        "language_tag": "en",
        "translator": "Michael Mikhail (as attributed by the Ethiopian Orthodox Bible Project)",
        "edition": (
            "Partial English rendering of Ethiopic Clement 6:83–86 reported in the project's 2025-11-05 notice; "
            "exact publication metadata not independently inspected."
        ),
        "translation_path": None,
        "source_ids": ["SRC-029", SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "Reuse rights for this modern English rendering are unknown. The project notice links to a commercial "
            "listing but grants no license to reproduce the text. No wording is copied."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "Publisher/project report only. Four-verse scope and mixed Ethiopic/French basis are reported, not "
            "independently checked. The mapping to the Church-list Book of Clement remains uncertain. This partial "
            "lead is not reader text and does not increase coverage."
        ),
        "notes": (
            "No direct Ge'ez-to-English path is claimed: the report mentions an Amharic manuscript, surviving "
            "Ethiopic fragments, and French supplementation. The text is partial and its input relationships "
            "remain to be checked against the named witnesses."
        ),
    }


def _render_review() -> str:
    rows = "\n".join(
        f"<li><strong>{item['canon_title']}</strong>: the announcement describes a section in the released "
        "English Sinodos edition and reports Horner 1904 as a basis. Exact wording, book boundaries, and the "
        "edition's relationship to the Church-list entry remain unverified.</li>"
        for item in SINODOS_LEADS
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light"><title>English edition leads for EOTC works</title>
<style>
:root {{ color-scheme: light; --ink:#123e39; --muted:#53645f; --line:#e3ddd1; --paper:#fbfaf7; --accent:#b27d32; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.65 system-ui,sans-serif; }}
main {{ width:min(900px,calc(100% - 32px)); margin:0 auto; padding:36px 0 64px; }}
h1,h2 {{ font-family:Georgia,serif; font-weight:500; line-height:1.2; }} h1 {{ font-size:clamp(2rem,5vw,3.2rem); }}
.note {{ border-left:4px solid var(--accent); background:#f3efe5; padding:14px 18px; }}
a {{ color:#075c53; }} .muted {{ color:var(--muted); }}
</style></head><body><main>
<p class="muted">Ethiopian Bible Library · metadata-only source review</p>
<h1>Reported English editions and partial translation</h1>
<p class="note"><strong>Status:</strong> This page records a publisher/project announcement, not inspected books. No third-party translation wording or images are included. The listed text rights remain unknown, and none of these leads counts as bundled reader coverage.</p>
<h2>Sinodos sections</h2><p>The Ethiopian Orthodox Bible Project's announcement dated 2025-11-05 says it released an English edition of the Ethiopic Books of the Synod (Sinodos). It reports that the edition uses Horner's <em>The Statutes of the Apostles</em> (1904), which the post associates with these sections, and compares versions:</p>
<ul>{rows}</ul>
<p>The post also names Schodde's 1885 English translation of the Ethiopic Gessew as a basis for the Canons section. That is consistent with the separately documented Schodde witness, but does not prove that this newly reported edition is the same as any other publisher's modernized Gitzew edition. No direct Ge'ez-to-English path is assigned to the Sinodos sections in these records.</p>
<h2>Partial Clement rendering</h2><p>The same announcement reports an English rendering of Clement 6:83-86. It says the manuscript it calls Amharic has damaged or lost wording, that Ethiopic fragments and a French translation were consulted, and that verse 83 was translated solely from French because the surviving Ethiopic is unintelligible. This report does not establish a full Book of Clement translation, source alignment, or its exact relationship to the Church-list title.</p>
<h2>Source, publication, and rights limits</h2><p>The announcement is the primary source for what the Ethiopian Orthodox Bible Project claims about its own edition. It links to sales listings, but the linked listings and books were not independently inspected. The page carries a copyright notice and offers no reuse license for its text or the books. These records therefore remain metadata-only with unknown content-reuse rights.</p>
<p><a href="{SOURCE_URL}">Open the 2025-11-05 announcement</a> · <a href="../index.html#catalogue">Return to catalogue</a></p>
</main></body></html>
"""


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive.get("sources", [])}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": "Ethiopian Orthodox Bible Project — 2025 report on English Sinodos/Dominos editions and Clement 6:83–86",
        "url": SOURCE_URL,
        "local_review_url": REVIEW_PATH,
        "inspection_and_limitations": (
            "Inspected 2026-10-27. The Ethiopian Orthodox Bible Project's 2025-11-05 post names Michael "
            "Mikhail and reports release of English editions of Sinodos and Dominos. It says the Sinodos "
            "edition uses Horner 1904, containing Səratä Ṣiyon, ʿAbṭəlis, and Təʻezaz, and "
            "Schodde's 1885 translation from Ethiopic for Gessew. It reports a partial English rendering of "
            "Clement 6:83–86 using a manuscript it calls Amharic, Ethiopic fragments, and Grébaut's French "
            "translation; the post says verse 83 relies solely on French. These are source-reported claims, "
            "not independent verification of publication details, the witnesses, wording, completeness, "
            "translation accuracy, or exact Church-list mapping. The post footer states Copyright © "
            "2012–2026 Ethiopian Orthodox Bible Project Committee, All Rights Reserved. No article text, "
            "images, or book text are copied."
        ),
        "archive_status": (
            "Metadata-only publisher report; sales listings and translation texts not independently inspected"
        ),
        "rights_classification": "all_rights_reserved",
        "rights_status": (
            "The announcement page displays an All Rights Reserved notice. This records the page's stated "
            "terms, not the rights in the books it discusses. No page text, images, or book text are copied."
        ),
        "rights_basis": (
            "The linked announcement footer states Copyright © 2012–2026 and All Rights Reserved; no "
            "reuse license for the page or the described modern translations is provided there."
        ),
    }
    archive["sources"] = sorted(
        sources.values(), key=lambda item: int(item["source_id"].split("-")[1])
    )
    write_text_atomically(
        archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n"
    )

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["translation_id"]: item for item in registry.get("translation_leads", [])}
    for item in SINODOS_LEADS:
        leads[item["translation_id"]] = _sinodos_lead(item)
    clement = _clement_lead()
    leads[clement["translation_id"]] = clement
    registry["translation_leads"] = sorted(leads.values(), key=lambda item: item["translation_id"])
    write_text_atomically(
        registry_path, json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    )

    (ROOT / REVIEW_PATH).write_text(_render_review(), encoding="utf-8")
    print("Recorded three source-asserted Sinodos leads and one partial Clement translation lead; no text bundled.")


if __name__ == "__main__":
    build()
