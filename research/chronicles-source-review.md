# Chronicles source review

## What is bundled

Two Geʽez TEI research readers are bundled from Beta maṣāḥǝft Works at pinned commit `ec53d3f4c5de47e463fa56a8465cf1090316a999`:

- **1 Chronicles** (`LIT3499Chroni`): 29 ordered chapter divisions and 950 TEI line elements.
- **2 Chronicles** (`LIT3500Chroni`): 36 ordered chapter divisions and 854 TEI line elements.

The source file's `<edition>` division explicitly declares `xml:lang="gez"`; its document root separately declares English. The reader uses the edition-level declaration and preserves the metadata conflict. All line elements are retained in source order. The `n` labels remain source markers, not asserted verse numbers. In 1 Chronicles, markers 13 in chapter 1 and 28 in chapter 26 are absent; the archive records and preserves those gaps without filling them. The source TEI files remain bundled unchanged, with hashes and extraction notes in each adjacent `*-SOURCE-AUDIT.md`.

Separate English research readers from Brenton's 1851 Greek Septuagint translation are also bundled for both titles. The archived USFM headings read “Chronicles I” and “Chronicles II,” corresponding by title to the Church-list labels “I Chronicles” and “II Chronicles.” The archive now surfaces those as uncertain, title-based candidate links (SRC-029, SRC-038, SRC-142). They are not translations from Geʽez, do not establish EOTC edition identity or equivalent scope, and remain outside canon-linked coverage.

The broader Brenton title/code candidate method, including links for other English research witnesses and unresolved mapping cases, is documented in the [Brenton crosswalk review](brenton-title-crosswalk-review.md) and its cited source records.

## Limits

The TEI work titles match the two catalogue titles, so the records are offered as research candidates for Church-list entries `eotc-ot-11` and `eotc-ot-12`. The TEI does not identify the print edition or manuscript basis of this exact transcription, or say that it represents a current EOTC printed Bible. No independent proofreading or collation was performed. These readers are therefore discoverable from the catalogue, but excluded from the count of canon-linked readers.

Each file's own TEI availability statement specifies CC BY-SA 4.0. The Beta maṣāḥǝft site footer also displays CC BY-NC-SA 4.0. This package records both notices and does not claim that the discrepancy is resolved or that either statement independently establishes rights in an unidentified underlying print witness.

## Sources

- [Beta maṣāḥǝft 1 Chronicles work record](https://betamasaheft.awhamburg.de/works/LIT3499Chroni/main) · [pinned source XML](https://github.com/BetaMasaheft/Works/blob/ec53d3f4c5de47e463fa56a8465cf1090316a999/3001-4000/LIT3499Chroni.xml)
- [Beta maṣāḥǝft 2 Chronicles work record](https://betamasaheft.awhamburg.de/works/LIT3500Chroni/main) · [pinned source XML](https://github.com/BetaMasaheft/Works/blob/ec53d3f4c5de47e463fa56a8465cf1090316a999/3001-4000/LIT3500Chroni.xml)
- [CC BY-SA 4.0 license text](https://creativecommons.org/licenses/by-sa/4.0/)
- [Beta maṣāḥǝft site](https://betamasaheft.awhamburg.de/) (site footer displays a distinct noncommercial notice)
