"""Record a source-scoped comparison of EOTC and PC(USA) canon counts."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
REVIEW_PATH = "research/canon-comparison-66-81.html"
UNKNOWN_RIGHTS = "unknown"
SOURCES = (
    {
        "source_id": "SRC-446",
        "source_name": "Presbyterian Church (U.S.A.) — What is the Bible?",
        "url": "https://centernet.pcusa.org/what-we-believe/bible/",
        "inspection_and_limitations": (
            "The PC(USA) page describes the Bible as 66 books, 39 Old Testament and 27 New Testament, and frames "
            "the description for Presbyterians and others in the Reformed tradition. It supports that denomination's "
            "published count; it is not a survey of every Protestant community and does not establish textual identity "
            "with another tradition."
        ),
        "archive_status": "Primary denomination statement for the PC(USA) Bible count; not a universal Protestant census",
        "rights_classification": UNKNOWN_RIGHTS,
        "rights_status": "Reuse terms for the wording of this information page have not been established here; citation is not a license.",
        "rights_basis": "No page-reuse license or permission was identified for this source record. Unknown records an evidence gap, not permission or prohibition.",
        "local_review_url": REVIEW_PATH,
    },
    {
        "source_id": "SRC-447",
        "source_name": "American Bible Society — Old Testament in Christian Bibles chart",
        "url": "https://www.americanbible.org/engage/bible-resources/articles/the-old-testament-in-christian-bibles-chart/",
        "inspection_and_limitations": (
            "The chart compares Orthodox, Catholic, and Protestant Old Testament lists and states that Christian "
            "traditions differ in which books they include. Its table includes Tobit, Judith, Sirach, and Baruch in "
            "Catholic/Orthodox columns; it does not specifically describe the Ethiopian Orthodox 81-book list. Its "
            "generic Orthodox column must not be treated as an EOTC catalogue."
        ),
        "archive_status": "Comparative church-Bible chart; not an Ethiopian Orthodox canon source",
        "rights_classification": UNKNOWN_RIGHTS,
        "rights_status": "Reuse terms for the wording of this information page have not been established here; citation is not a license.",
        "rights_basis": "No page-reuse license or permission was identified for this source record. Unknown records an evidence gap, not permission or prohibition.",
        "local_review_url": REVIEW_PATH,
    },
)


def _html() -> str:
    return '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Source-scoped note comparing an Ethiopian Orthodox canon statement with one Reformed denomination's 66-book count.">
  <title>Canon counts: source-scoped comparison · Ethiopian Bible Library</title>
  <style>
    body{margin:0;background:#fbfaf7;color:#183b35;font:16px/1.65 system-ui,sans-serif}
    main{max-width:850px;margin:0 auto;padding:2rem 1.25rem 4rem}
    h1,h2{font-family:Georgia,serif;font-weight:500;line-height:1.2}
    a{color:#075c53;overflow-wrap:anywhere}
    .note{border-left:4px solid #b68437;background:#f4f0e7;padding:1rem}
    li{margin:.5rem 0}
  </style>
</head>
<body><main>
  <p><a href="../index.html">← Back to the archive</a></p>
  <h1>Canon counts: 66 and 81 in source context</h1>
  <p>This note checks a common “66 books plus additional books” explanation against cited institutional sources. It documents what those sources state; it does not decide theology.</p>
  <h2>What the cited sources say</h2>
  <ul>
    <li>The Ethiopian Orthodox Tewahedo Church’s English canon page states 81 canonized books: 46 Old Testament and 35 New Testament. It explicitly says its canon differs in both Testaments from those of other churches. Its numbered list contains combined titles such as “I and II Samuel” and “Ezra and Nehemia.” The count and the list’s groupings should be represented as the Church gives them, with unresolved title crosswalks visible.</li>
    <li>That English list labels its Maccabees entries “I Maccabees” and “II and III Maccabees”; it does not use the name “Meqabyan.” This page alone does not settle how those titles crosswalk to Greek Maccabees or to other transliterations. Keep the cited wording and do not silently normalize the works.</li>
    <li>The Presbyterian Church (U.S.A.) describes a 66-book Bible, 39 Old Testament and 27 New Testament, in a statement framed for Presbyterians and others in the Reformed tradition. This is evidence for that denomination’s count, not a census of every Protestant body.</li>
    <li>The American Bible Society’s comparative chart places titles including Tobit, Judith, Sirach, and Baruch in Catholic/Orthodox columns. Those titles are therefore not all distinctive to the Ethiopian tradition; the chart’s generic Orthodox column is not an EOTC list.</li>
  </ul>
  <h2>What this comparison does not establish</h2>
  <p>The difference between the published totals is not, by itself, a verified list of 15 discrete added works: the sources use tradition-specific counts, titles, and groupings. A shared English book name does not prove identical source witnesses, textual form, chapter divisions, or translation. This archive does not claim that the traditions cannot contradict one another, nor does it claim that one canon simply adds books without differences. Those are theological or textual judgments requiring a defined question and evidence beyond counts.</p>
  <h2>Editorial guidance for public explanations</h2>
  <p>A concise explanation may say that the Ethiopian Orthodox Tewahedo Church lists an 81-book canon, compared with the 66-book count stated by the Presbyterian Church (U.S.A.). It should identify the traditions being compared and link the sources. Avoid saying “nothing is removed, rewritten, or replaced,” “the same foundation, with more chapters,” or that the 81-book canon merely adds material to an unchanged 66-book canon: the cited Church page says its canon differs from other churches in both Testaments, and a count alone cannot establish textual or theological equivalence. Also avoid saying the traditions necessarily contradict; that conclusion requires a defined comparison of specific texts and claims.</p>
  <p>The promotional copy supplied for review is not treated as evidence for canon contents. Its claims are checked against the linked institutional sources; its campaign link is not used as a canon authority.</p>
  <p class="note">The Church’s English page itself is the authority here for the Church’s stated 81-book count and list. The PC(USA) page is used only for its denomination’s stated 66-book count. Neither source authenticates a modern edition or every reader in this archive.</p>
  <h2>Primary sources</h2>
  <ul>
    <li><a href="https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en">Ethiopian Orthodox Tewahedo Church — English canon list (SRC-029)</a></li>
    <li><a href="https://centernet.pcusa.org/what-we-believe/bible/">Presbyterian Church (U.S.A.) — Bible (SRC-446)</a></li>
    <li><a href="https://www.americanbible.org/engage/bible-resources/articles/the-old-testament-in-christian-bibles-chart/">American Bible Society — comparative chart (SRC-447)</a></li>
  </ul>
</main></body></html>
'''


def apply(archive: dict) -> None:
    sources = archive.setdefault("sources", [])
    by_id = {item.get("source_id"): item for item in sources}
    for record in SOURCES:
        previous = by_id.get(record["source_id"])
        if previous and previous.get("url") != record["url"]:
            raise ValueError(f"{record['source_id']} is already assigned to another source.")
        if previous:
            sources[sources.index(previous)] = dict(record)
        else:
            sources.append(dict(record))
    sources.sort(key=lambda item: int(item["source_id"].split("-")[-1]))
    (ROOT / REVIEW_PATH).write_text(_html(), encoding="utf-8")


if __name__ == "__main__":
    import json
    from archive_manifest import write_text_atomically

    path = ROOT / "archive.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    apply(data)
    write_text_atomically(path, json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Added denomination-scoped canon-count sources and local review: {REVIEW_PATH}")
