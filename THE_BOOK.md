# The Book

Updated 2026-11-20. This is a library feature, not a new scriptural edition.

## Governing declaration

Read across the library without collapsing scripture into commentary, a witness
into a canon list, a person into a representation, or a present interpretation
into historical evidence. The supplied reading map informs an optional method;
it does not determine what every passage must mean.

## What is connected

- `build_the_book.py` derives `the-book.json` from every bundled reader and its
  actual local JSON package. The regular standalone/release build refreshes it.
- The same index retains the 81 Church-list entries, including unavailable texts,
  and all catalogue rows. These are distinct inventories, not additive book totals.
- `the-book-section.html` is the canonical section fragment. Its integration is
  idempotent: reader first, optional map second, other research disclosures later.
- `the-book.js` connects the active reader and chapter to a local worksheet and
  searches every bundled reader by title, language, edition or identifier.
- The main reader's existing sourced English references and historical companions
  remain separate editions with their existing mapping limits. No new translation
  or verse alignment is inferred by the map.
- `the-book.css` provides responsive, keyboard-focus-visible controls using the
  site's warm palette. The new assets, map and conceptual source are in shell v51.

The scope is the public scripture already bundled plus existing catalogue and
canon metadata. Withheld scripture remains withheld; missing editions remain
missing. Existing Geʽez, English and other language wording is not reinterpreted
or rewritten by a generator.

## Four paths and their sources

A. Shared books: the 24-book Tanakh reckoning and 39-book Protestant Old Testament
grouping can be compared without asserting identical texts. Conventional
Protestant counting adds 27 New Testament books for 66. The Twelve illustrates
how counting can change independently of textual wording.

B. Catholic and Eastern Orthodox: the Catholic 46 + 27 count is attributed to
[Catechism §120](https://www.vatican.va/content/catechism/en/part_one/section_one/chapter_two/article_3/iv_the_canon_of_scripture.index.html).
Use a named Orthodox list or edition; the [OCA history page](https://www.oca.org/orthodoxy/the-orthodox-faith/doctrine-scripture/old-testament/history)
is a teaching source, not an exhaustive shared Orthodox edition.

C. Ethiopian Orthodox Tewahedo: keep the [Church's cited English list](https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en)
and its grouped 46 + 35 reckoning distinct from available witnesses. Enoch and
Jubilees are listed works; their listing does not grant this archive text rights.

D. Comparative audit: identify passage, witness, reading, numbering, differences
and gaps within any chosen scope. A selected scope never silently filters out or
certifies a tradition's texts.

The map links [Chabad's Torah FAQ](https://www.chabad.org/library/article_cdo/aid/6173470/jewish/Torah-FAQ.htm)
for the 24-book reckoning and the [Bible Society style guide](https://www.biblesociety.org.uk/content/news/press_area/bible_style_guide.pdf)
for the Protestant counting convention. These sources were consulted on
2026-11-20; their doctrinal accounts are attributed, not universalized. No new
canon crosswalk has been asserted.

## Relationship to the supplied architecture

The complete supplied text is preserved byte-for-byte at
`research/the-book-reading-map-source.txt`; its SHA-256 is recorded in the map.
It is an excerpt with missing sections and truncated headings, not a complete
master specification. Authorship was not established by the attachment.

The guide exposes ten groups covering I/IS/AM/AS IS, preservation without freezing,
TRG-01 recollection, MFB/DFB/PFB/TFB/EFB failure distinctions, Mind/Body/Soul,
GTI-01 grammar and time, mathematical integrity, Christian theological premises,
fallbacks, UTC-01 and the extension protocol. The symbolic local course and
SCG-07 are explained alongside the original source. None claims a general
ChronoRealm engine has been implemented in this static library.

WAS/IS/BECOMING/BECAME are available in separate temporal-standing and review-step
fields. BEING is the frame, TO_BE a projection annotation, and legacy AS maps to
IS. The owning ChronoTense catalogs were inspected; tests compare each duplicated
axis to its own catalog when that workspace source is available. Portable package
tests retain the four-value contract without importing a different application.

Time fields distinguish event, observation, recollection, record creation,
publication, discovery, interpretation and as-of. Dates can remain unknown and
are not authenticated clocks. Saving supplies only the note's local record time;
it does not turn a claim into BECAME.

Christian theological interpretation is identified as faith. The 3–6–9 and
3 × 2 + 1 = 7 associations are symbolic; ordinary arithmetic and the distinction
between analogy and proof remain intact. The guide neither certifies salvation
nor establishes physical time travel, resurrection or postmortem consciousness.

## Local persistence, privacy and recovery

Notes are written only on an explicit Save, under browser-local storage key
`ethiopian-bible-library-the-book-v1`. They are reader-authored records and are
not added to scripture, published to GitHub or transmitted to a note server.
Other users of the same browser profile may read them; storage is not encrypted.

Each saved revision has an ID, parent ID, timestamp, original witness/chapter,
source IDs, framework-source hash, scope, observations, interpretation, unknowns,
optional comparisons and the self-review checklist. Moving to another chapter
does not move an open note. Use Start a note for a new source context. Older
revisions remain; saving does not overwrite them. A local course closes only as
a reader-attested review, not as certification of a claim.

The store is bounded to 200 revisions and 1,500,000 serialized characters. The
latest 30 revisions are listed; the export includes all. A JSON export includes
the raw saved value for recovery and separately labels the current worksheet.
No import or automatic synchronization is implemented. Back up important notes
before clearing browser data. Corruption, quota/access errors and conflicting
tab writes report failure without claiming a save or replacing existing notes.
Where supported, Web Locks serializes saves across tabs before the stale-record
check. Without it the UI asks users to use one tab; the comparison alone cannot
guarantee exclusion of simultaneous writes. The explicit Clear control asks
before removing this key only.

If the map cannot load or does not match the reader collection, only its dependent
workspace is held. Scripture remains readable; Retry can load the local map.
Offline availability requires the new shell to install and the intended reader
to be cached; all scripture is not automatically downloaded.

## Verification and release boundary

Tests cover all-reader package linkage, source hashes, preserved canon gaps,
deterministic generation, separate temporal axes, idempotent insertion, note
revisions, source binding, classification, corrupted storage and failed writes.
Real-browser checks use the GitHub Pages subpath at 320/390/768/1440 pixels and
exercise saved notes, exports, offline reload and failure reporting.

`python build_release.py` rebuilds the archive and map; the checksum guard checks
Git-normalized text before hashing. Raw source captures and the supplied excerpt
are explicitly byte-preserved. Keep the strict CI stale-output check enabled.
Updating a local build does not publish it. Commit/push and a successful GitHub
Actions deployment are separate steps. Older `dist/` exports remain historical
and do not automatically contain this feature.
