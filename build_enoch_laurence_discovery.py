"""Record Richard Laurence's historical English 1 Enoch lead without bundling text."""

from __future__ import annotations

from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ITEM_URL = "https://www.gutenberg.org/ebooks/77815"
HTML_URL = "https://www.gutenberg.org/cache/epub/77815/pg77815-images.html"
REVIEW_PATH = "research/enoch-laurence-1883-source.html"
TRANSLATION_ID = "enoch-en-laurence-1883-gutenberg-77815"
SOURCE_RECORDS = (
    {
        "source_id": "SRC-444",
        "source_name": "Project Gutenberg — The book of Enoch the Prophet, item metadata (#77815)",
        "url": ITEM_URL,
        "inspection_and_limitations": (
            "The Project Gutenberg item metadata identifies Richard Laurence (1760–1838) as translator, "
            "the title as translated from an Ethiopic manuscript in the Bodleian Library, and the original "
            "publication as London: Kegan Paul, Trench & Co., 1883. It reports the eBook as public domain "
            "in the United States. This bibliographic record does not establish manuscript identity, text "
            "accuracy, completeness, chapter structure, or worldwide reuse rights."
        ),
        "archive_status": "Bibliographic source for a historical English 1 Enoch lead; no text bundled",
        "rights_classification": "unknown",
        "rights_status": (
            "This is a bibliographic item page. The page's public-domain label applies to the eBook's "
            "U.S. distribution statement and does not establish reuse rights in the page itself or worldwide rights."
        ),
        "rights_basis": (
            "No separate license for reuse of the metadata page's expressive content was identified. "
            "The unknown classification records that gap; it does not establish permission or prohibition."
        ),
        "local_review_url": REVIEW_PATH,
    },
    {
        "source_id": "SRC-445",
        "source_name": "Project Gutenberg — The book of Enoch the Prophet, full HTML rendition (#77815)",
        "url": HTML_URL,
        "inspection_and_limitations": (
            "The HTML front matter identifies the 1883 English edition as translated from an Ethiopic "
            "manuscript in the Bodleian Library and names Richard Laurence. Its preliminary matter includes "
            "a statement reserving translation and reproduction rights; Project Gutenberg separately marks "
            "the eBook public domain in the United States and directs readers elsewhere to check local law. "
            "These source statements are preserved without adjudicating their present legal effect or "
            "worldwide scope. No text was captured or bundled."
        ),
        "archive_status": "Online edition and rights notices inspected; source text not captured or bundled",
        "rights_classification": "mixed",
        "rights_status": (
            "Project Gutenberg states a U.S.-scoped public-domain claim and requires users elsewhere to "
            "check local law; the digitized 1883 front matter says translation and reproduction rights are "
            "reserved. The scope and present legal effect of those notices have not been independently "
            "resolved. No worldwide reuse clearance is claimed."
        ),
        "rights_basis": (
            "Classification preserves the coexistence of the Project Gutenberg U.S. claim, the 1883 "
            "front-matter notice, and the territorial caveat. It is not a legal conclusion."
        ),
        "local_review_url": REVIEW_PATH,
    },
)


def _review_html() -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A source-backed bibliographic record for Richard Laurence's 1883 English 1 Enoch translation, with mapping and rights limits.">
  <title>Laurence 1883 · 1 Enoch source record</title>
  <style>
    body{{margin:0;background:#fbfaf7;color:#183b35;font:16px/1.65 system-ui,sans-serif}}
    main{{max-width:820px;margin:0 auto;padding:2rem 1.25rem 4rem}}
    h1,h2{{font-family:Georgia,serif;font-weight:500;line-height:1.2}}
    a{{color:#075c53;overflow-wrap:anywhere}}
    .notice{{border-left:4px solid #b68437;background:#f4f0e7;padding:1rem}}
    li{{margin:.5rem 0}}
  </style>
</head>
<body><main>
  <p><a href="../index.html">← Back to the archive</a></p>
  <h1>Richard Laurence’s 1883 English 1 Enoch</h1>
  <p>Bibliographic and rights evidence only. This page does not contain a reader or a transcription.</p>
  <h2>What the source establishes</h2>
  <ul>
    <li>Project Gutenberg identifies Richard Laurence (1760–1838) as translator.</li>
    <li>The printed title describes the work as translated from an Ethiopic manuscript in the Bodleian Library.</li>
    <li>The recorded original publication is London, Kegan Paul, Trench &amp; Co., 1883.</li>
    <li>The Gutenberg item marks its eBook public domain in the United States.</li>
  </ul>
  <h2>What remains unresolved</h2>
  <p>The title does not identify the exact manuscript shelfmark or recension in the records inspected. It does not establish a chapter map, completeness, wording accuracy, or identity with a current Ethiopian or Eritrean Orthodox edition. It is a title-level match to the Church-list entry “Enoch,” not proof that this translation represents that edition.</p>
  <p class="notice">The 1883 preliminary matter says translation and reproduction rights are reserved. Project Gutenberg separately states a U.S.-scoped public-domain claim and tells readers elsewhere to check local law. This archive records both notices and does not resolve their legal interaction or claim worldwide reuse rights. No text is bundled.</p>
  <h2>Primary sources</h2>
  <ul>
    <li><a href="{escape(ITEM_URL, quote=True)}">Project Gutenberg item metadata (#77815)</a></li>
    <li><a href="{escape(HTML_URL, quote=True)}">Project Gutenberg HTML edition and front matter</a></li>
    <li><a href="../archive.json">Local archive records</a> · SRC-444 and SRC-445</li>
  </ul>
  <p>The lead is kept separate from the other English 1 Enoch translation by R. H. Charles. Neither lead is counted as a bundled reader.</p>
</main></body></html>
'''


def apply(archive: dict) -> None:
    sources = archive.setdefault("sources", [])
    existing_sources = {item.get("source_id"): item for item in sources}
    for record in SOURCE_RECORDS:
        prior = existing_sources.get(record["source_id"])
        if prior and prior.get("url") != record["url"]:
            raise ValueError(f"{record['source_id']} is already assigned to another source.")
        if prior:
            sources[sources.index(prior)] = dict(record)
        else:
            sources.append(dict(record))
    sources.sort(key=lambda item: int(item["source_id"].split("-")[-1]))

    registry = archive.setdefault("translation_registry", {})
    leads = registry.setdefault("translation_leads", [])
    lead = {
        "translation_id": TRANSLATION_ID,
        "title": "1 Enoch — Richard Laurence English translation (1883; Gutenberg eBook #77815)",
        "canon_id": "eotc-ot-14",
        "language_tag": "en",
        "translator": "Richard Laurence (1760–1838)",
        "edition": "The Book of Enoch the Prophet; London: Kegan Paul, Trench & Co., 1883; Project Gutenberg eBook #77815",
        "translation_path": ["gez", "en"],
        "mapping_state": "reviewed_match",
        "source_ids": ["SRC-029", "SRC-444", "SRC-445"],
        "text_bundled": False,
        "rights_classification": "mixed",
        "rights_status": (
            "Project Gutenberg marks the eBook public domain in the United States and directs users elsewhere "
            "to check local law. The 1883 front matter says translation and reproduction rights are reserved. "
            "The notices' scope and present legal effect are unresolved; no worldwide reuse clearance is claimed."
        ),
        "scope_description": (
            "Historical English translation whose title identifies an Ethiopic manuscript in the Bodleian Library. "
            "The exact manuscript shelfmark and recension are not established by the cited item metadata. The "
            "correspondence to the Church-list title Enoch is a title-level work match only; identity with a current "
            "Ethiopian or Eritrean Orthodox edition, completeness, chapter structure, and text accuracy remain unverified."
        ),
        "review_status": (
            "The official Project Gutenberg item metadata and HTML front matter were inspected. No source text was "
            "captured, chapter map audited, or wording checked. This bibliographic lead is not a reader and does not "
            "increase bundled-reader coverage."
        ),
        "notes": (
            "Keep distinct from the later R. H. Charles translation lead. This is a separately attributed historical "
            "English rendering; it is not a synthesized translation and no textual equivalence is inferred."
        ),
    }
    existing_leads = {item.get("translation_id"): item for item in leads}
    prior = existing_leads.get(TRANSLATION_ID)
    if prior:
        leads[leads.index(prior)] = lead
    else:
        leads.append(lead)
    leads.sort(key=lambda item: item.get("translation_id", ""))
    (ROOT / REVIEW_PATH).write_text(_review_html(), encoding="utf-8")


if __name__ == "__main__":
    import json
    from archive_manifest import write_text_atomically

    path = ROOT / "archive.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    apply(data)
    write_text_atomically(path, json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Recorded Laurence 1883 1 Enoch bibliographic lead: {TRANSLATION_ID}; no text bundled.")
