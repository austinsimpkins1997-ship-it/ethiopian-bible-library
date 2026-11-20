"""Build an optional reading map for every bundled reader without editing scripture."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STANDINGS = ("WAS", "IS", "BECOMING", "BECAME")
REVIEW_STEPS = ("WAS", "IS", "BECOMING", "BECAME")


def integrate_html(html: str, root: Path = ROOT) -> str:
    """Keep the optional section reproducible without duplicating anchors."""
    section = (root / "the-book-section.html").read_text(encoding="utf-8").strip()
    marker = re.compile(r"<!-- THE BOOK SECTION START -->.*?<!-- THE BOOK SECTION END -->", re.S)
    if marker.search(html):
        html = marker.sub(lambda _: section, html)
    else:
        anchor = '    <div class="explore-intro">'
        if html.count(anchor) != 1:
            raise ValueError("Expected one reader-first insertion point for The Book")
        html = html.replace(anchor, section + "\n\n" + anchor)
    if 'href="the-book.css"' not in html:
        html = html.replace('</head>', '  <link rel="stylesheet" href="the-book.css">\n</head>')
    if 'src="the-book.js"' not in html:
        html = html.replace('  <script src="app.js" defer>', '  <script src="the-book.js" defer></script>\n  <script src="app.js" defer>')
    if 'data-view="the-book"' not in html:
        html = html.replace('      <a class="nav-link" href="#library"', '      <a class="nav-link" href="#the-book" data-view="the-book">The Book</a>\n      <a class="nav-link" href="#library"')
    if 'id="the-book-reader-link"' not in html:
        html = html.replace('<details class="reader-details" id="reader-notes">', '<p><a id="the-book-reader-link" href="#the-book">Explore this passage in The Book →</a></p>\n      <details class="reader-details" id="reader-notes">')
    return html


def build(archive: dict, packages: dict, root: Path = ROOT) -> dict:
    source = root / "research/the-book-reading-map-source.txt"
    readers = []
    for reader in archive["readers"]:
        reader_id = reader["reader_id"]
        if reader_id not in packages:
            raise ValueError(f"The Book has no package for {reader_id}")
        readers.append({
            "reader_id": reader_id,
            "title": reader.get("display_name") or reader["title"],
            "package_path": packages[reader_id],
            "language": reader.get("language", "Unknown"),
            "language_tag": reader.get("language_tag", "und"),
            "edition": reader.get("edition", "Unknown"),
            "source_ids": list(reader.get("source_ids", [])),
            "canon_id": reader.get("canon_id"),
            "candidate_canon_id": reader.get("candidate_canon_id"),
            "mapping_limit": "Existing title/work link only; no new canon membership, edition identity or textual alignment is inferred.",
        })
    readers.sort(key=lambda r: (r["title"], r["reader_id"]))
    if len({r["reader_id"] for r in readers}) != len(readers):
        raise ValueError("Duplicate reader in The Book")
    return {
        "schema_version": 1,
        "title": "The Book",
        "as_of": "2026-11-20",
        "purpose": "Read, compare and reflect while keeping witnesses, traditions, people and evidence distinct.",
        "source": {
            "path": "research/the-book-reading-map-source.txt",
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "description": "User-supplied Reading Map / 01 and CHRONOTENSE excerpts; creator attribution not established in the attachment.",
            "coverage": "Excerpts only. Numbering jumps, missing parts and incomplete sentences are retained; no missing content has been reconstructed.",
            "role": "Conceptual design source, not scripture, historical corroboration or church authority.",
        },
        "standings": list(STANDINGS),
        "review_steps": list(REVIEW_STEPS),
        "frame": "BEING",
        "projection_label": "TO_BE",
        "legacy_standing_map": {"AS": "IS"},
        "scope_paths": [
            {"id": "A", "title": "Shared books", "description": "Explore the Tanakh's 24-book reckoning alongside the 39-book Protestant Old Testament grouping; a conventional Protestant Bible adds 27 New Testament books for 66. Shared titles do not establish identical wording, order or editions.", "sources": ["sefaria", "protestant"]},
            {"id": "B", "title": "Catholic & Eastern Orthodox", "description": "The Catholic reckoning has 46 Old Testament and 27 New Testament books. Compare a specifically named Eastern Orthodox edition or list; do not impose one Orthodox count. Tobit and the Maccabees illustrate why inclusion, naming and grouping need checking.", "sources": ["catholic", "orthodox"]},
            {"id": "C", "title": "Ethiopian Orthodox Tewahedo", "description": "Use the Church's cited 81-entry English list, including Enoch and Jubilees, alongside its grouped names. A church list, Geʽez witness and English edition answer different questions. A listed work may lack distributable reader text.", "sources": ["eotc"]},
            {"id": "D", "title": "Comparative audit", "description": "Within any scope, select a passage and record witnesses, their exact readings, source numbering, differences and missing evidence. Torah, Prophets, Writings/Wisdom, Gospels, Epistles and apocalyptic literature are possible starting points, not identical categories in every tradition.", "sources": []},
        ],
        "canon_sources": [
            {"id": "sefaria", "title": "Chabad — Torah FAQ (24-book reckoning)", "url": "https://www.chabad.org/library/article_cdo/aid/6173470/jewish/Torah-FAQ.htm", "reviewed_on": "2026-11-20", "limit": "Jewish community teaching source; Sefaria's Tanakh contents additionally supports navigation, not identical editions."},
            {"id": "protestant", "title": "Bible Society — Bible style guide, Fast Facts", "url": "https://www.biblesociety.org.uk/content/news/press_area/bible_style_guide.pdf", "reviewed_on": "2026-11-20", "limit": "The 66-book convention does not describe every Protestant edition's treatment of the Apocrypha."},
            {"id": "catholic", "title": "Catechism of the Catholic Church §120", "url": "https://www.vatican.va/content/catechism/en/part_one/section_one/chapter_two/article_3/iv_the_canon_of_scripture.index.html", "reviewed_on": "2026-11-20", "limit": "Catholic list and reckoning; its own alternate Jeremiah/Lamentations grouping is noted by the source."},
            {"id": "orthodox", "title": "Orthodox Church in America — Old Testament history", "url": "https://www.oca.org/orthodoxy/the-orthodox-faith/doctrine-scripture/old-testament/history", "reviewed_on": "2026-11-20", "limit": "Named church teaching page, not an edition-complete universal Orthodox inventory."},
            {"id": "eotc", "title": "Ethiopian Orthodox Tewahedo Church — English canon list (SRC-029)", "url": "https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en", "reviewed_on": "2026-11-20", "limit": "Preserve the source's 46 + 35 reckoning and grouped entries; historical lists vary."},
        ],
        "principles": [
            {"id": "identity", "title": "Traveler, passage, proclamation", "text": "In the supplied conceptual framework, I names a traveler, IS a passage, AM a present proclamation and AS IS an integrity operation. These are symbolic roles, not new scripture, a grammar rule or an executable proof. The speaker in a passage, its author, translator and present reader need not be the same person. Unknown identities remain unresolved; distinct persons and witnesses stay distinct."},
            {"id": "preservation", "title": "Preserve without freezing", "text": "A record, memory, image or action does not exhaust a life. Reinterpreting a record changes the present account, not the original occurrence. Preserve the earlier version and identify the revision. Missing records do not by themselves prove nonexistence; absence of expected evidence can still count against a specific claim."},
            {"id": "recollection", "title": "TRG-01 · Timeless recollection", "text": "Recollection is optional and happens in the present; it does not replay an event, resurrect a body or establish consciousness outside time. Memory, documentation, publication, telemetry and unresolved existence have separate failure paths: MFB-01, DFB-02, PFB-03, TFB-04 and EFB-05. Leave unsupported history unknown rather than inventing it."},
            {"id": "dimensions", "title": "Mind, Body, Soul · optional lenses", "text": "Within an explicitly Christian reflection, consider thought and discernment; sensation and embodied conditions; faith, conscience, purpose and relation to God. The symbolic 3–6–9 mapping is not a physical law. Do not impose all dimensions on every entity, infer someone's private mind, or treat differing experiences as proof of multiple people."},
            {"id": "grammar", "title": "GTI-01 · Words and time", "text": "Keep quoted grammar, the speaker's viewpoint, temporal standing and the time of your interpretation separate. A past-tense sentence is not independently verified history. Event, observation, recollection, record creation, publication, discovery and interpretation dates may differ or be unknown."},
            {"id": "mathematics", "title": "Mathematics and symbolic completion", "text": "Ordinary arithmetic remains 1 + 1 = 2; 1 is not prime and 2 is the smallest prime. The valid expression 3 × 2 + 1 = 7 can accompany the source's six Mind/Body/Soul × traveler/passage positions and seventh AS IS integrity check. This is a local symbolic course, not a proof of theology or universal completion. Identity-aware integration may combine descriptions of the same established person; it must not merge distinct or uncertain people. A finite list does not exhaust infinity."},
            {"id": "theology", "title": "Christian reflection, identified as faith", "text": "GOD IS and the Creator–creation distinction are Christian theological premises here, not experimentally established conclusions. Exodus 3:14, John 1:1–3, Psalm 90:2, Hebrews 13:8, Revelation 1:8, Romans 12:2, 1 Corinthians 12 and 15, Galatians 5:1 and Genesis 2:2–3 are suggested passages. Traditions may interpret them differently. Recollection of a life does not establish biological return; resurrection and eternal life remain theological claims. No formal system certifies salvation."},
            {"id": "fallback", "title": "AS IS · preserve the reference", "text": "Fallback(IS) = IS is the source's conceptual preservation rule. Keep unknown, unavailable, disputed, conflicting and unsupported records visible; do not fabricate memory, force identity mergers or claim a failed computation returned successfully. Furthermore IS expresses an open continuation, not unlimited implemented capability."},
            {"id": "translation", "title": "UTC-01 · Translate without changing the kind of claim", "text": "For every cross-domain reading record source and target domains, original expression, intended meaning, preserved properties, lost information, new assumptions, evidence status and whether the relation is exact, partial or analogical. Analogy is not theorem; symbols do not turn theology into physics. This worksheet does not generate scripture translations."},
            {"id": "extension", "title": "A course that can be revised", "text": "Identify the proposed change; distinguish literal, mathematical, metaphorical, experiential, theological and operational meanings; integrate only an explicit interpretation; check non-collapse and authority; define boundaries; state fallback; preserve history; verify within scope; return to the current record. Power or repetition does not establish truth. A closed local course may reopen when evidence changes."},
        ],
        "completion_checks": [
            "Witness, edition and passage are identified without merging distinct sources.",
            "What the source says is separate from my interpretation and symbolic reading.",
            "Unknowns, conflicts and absent evidence remain explicit.",
            "Dates, temporal standing and current review step remain separate.",
            "Mind, Body and Soul lenses are optional and do not assert private experience.",
            "Any domain analogy states its assumptions, losses and limits.",
            "AS IS: I reviewed this local course; this does not certify truth, salvation or completeness.",
        ],
        "reader_count": len(readers), "readers": readers,
        "canon_entries": archive["canon_registry"]["books"],
        "catalogue_entries": [{k: row.get(k) for k in ("catalogue_id", "display_name", "identity_status", "text_availability_status", "source_id", "evidence_source_ids")} for row in archive["catalogue"]],
        "coverage_limit": "Every bundled reader can use the same optional worksheet. This does not supply missing books, certify interpretations, infer cross-tradition membership or align unrelated chapters.",
    }


def write(archive: dict, packages: dict, root: Path = ROOT) -> dict:
    record = build(archive, packages, root)
    (root / "the-book.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record
