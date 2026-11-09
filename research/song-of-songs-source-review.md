# Song of Songs source review

## Basis for the reader link

Beta maṣāḥǝft work `LIT2362Songof` includes an `EOTCed` text division. That division declares Geʽez and has the note “Text of the EOTC printed Bible.” The TEI revision history records “added text from EOTC Bible edition” on 2025-06-05. Those are explicit provider statements supporting a source-asserted link to the Church-list Song of Songs entry.

The same work record says the text in the record was digitized from modern Vulgata printed editions and converted to XML. The precise printed exemplar, the history and scope of each edition division, and the relationship between that general statement and the EOTC-specific notes are not identified. Accordingly, the reader counts as a linked source-text record, while exact current-edition identity, completeness, and textual accuracy remain unverified.

## Structural audit

The pinned TEI contains eight ordered EOTCed chapter divisions and 131 nonempty line elements. Markers are sequential within chapters 1–7. Chapter 8 contains 17 line elements but repeats source marker `14` before continuing with `15` and `16`; the archive preserves both occurrences and does not correct the source. These `l` elements are presented as source line elements, not independently established verse numbers. The full TEI is retained unchanged beside the reader JSON; extraction normalizes whitespace and flattens inline markup.

## Rights notes

The pinned TEI file explicitly states CC BY-SA 4.0. The site's footer separately displays CC BY-NC-SA 4.0; the relationship between these notices remains unresolved. The archive records the file-level notice and does not treat it as proof of rights in the unidentified print exemplar.

## Sources

- [Beta maṣāḥǝft Song of Songs work record](https://betamasaheft.awhamburg.de/works/LIT2362Songof/main)
- [Pinned TEI source at Works commit `ec53d3f4c5de47e463fa56a8465cf1090316a999`](https://github.com/BetaMasaheft/Works/blob/ec53d3f4c5de47e463fa56a8465cf1090316a999/2001-3000/LIT2362Songof.xml)
- [CC BY-SA 4.0 license text](https://creativecommons.org/licenses/by-sa/4.0/)
