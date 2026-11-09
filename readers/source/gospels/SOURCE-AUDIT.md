# Beta maṣāḥǝft Gospel TEI source audit

## Scope and pin

The archive retains the three source TEI files below from the BetaMasaheft/Works repository at commit `9029473659ab6efc4035ee52b9922192c99ba75e` (retrieved 2026-10-25). The build is offline and verifies each SHA-256 before extracting. It preserves chapter order, every TEI line element, source labels, unnumbered lines, empty text, and normalized line wording; it does not collate against the printed source.

| Work | File | SHA-256 | Chapters | TEI lines | Numbered | Unnumbered | Empty |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Matthew | `LIT2709Matthew.xml-original.xml` | `017bf4aefa51768328c9b045abe203ad73096895daa9fb9c9534935a52304f1d` | 28 | 1,187 | 1,072 | 115 | 0 |
| Luke | `LIT2713Luke.xml-original.xml` | `2dacd571061a9b57dc8ad50f8857f7ea07eb1319ce4a345fc53268659cf0ecc8` | 24 | 1,277 | 1,151 | 126 | 1 |
| John | `LIT2715John.xml-original.xml` | `576aa7e7b29c3d6864555924da0488757e4e9efe6980e2b46fceea3393f85f46` | 21 | 937 | 879 | 58 | 0 |

The TEI roots default to `xml:lang="en"`, while each enclosing edition declares `xml:lang="gez"`; the archive retains this metadata conflict and uses the edition language for the text. Each file states CC BY-SA 4.0. That file-level grant does not establish rights in an unidentified underlying printed exemplar. Attribute Beta maṣāḥǝft and the named contributors as specified by the source, identify the TEI-derived extraction and changes, and share adaptations under the same license.

## Preserved source irregularities

- Matthew chapter 7 labels run 1–28 and then contain a second line labeled 24. The duplicate/out-of-order label is kept as written.
- Luke chapter 21 begins with an empty TEI line labeled 21, then an unnumbered heading, then numbered labels 1–36. The empty line and following elements remain in source order. The reader explicitly marks the empty source element; no wording is supplied.
- John's extracted chapter sequence and line labels showed no duplicate or out-of-sequence labels in this structural audit. This is not a claim of textual correctness.

Work titles and the edition note “Text of the EOTC printed Bible” support only provisional title-level mappings to the corresponding entries. The exact print exemplars, current EOTC edition identity, completeness, transcription accuracy, and manuscript relationships are unverified. Structural counts are not verse-completeness claims.

## Pinned source links

- [Matthew TEI at pinned commit](https://github.com/BetaMasaheft/Works/blob/9029473659ab6efc4035ee52b9922192c99ba75e/2001-3000/LIT2709Matthew.xml)
- [Luke TEI at pinned commit](https://github.com/BetaMasaheft/Works/blob/9029473659ab6efc4035ee52b9922192c99ba75e/2001-3000/LIT2713Luke.xml)
- [John TEI at pinned commit](https://github.com/BetaMasaheft/Works/blob/9029473659ab6efc4035ee52b9922192c99ba75e/2001-3000/LIT2715John.xml)
