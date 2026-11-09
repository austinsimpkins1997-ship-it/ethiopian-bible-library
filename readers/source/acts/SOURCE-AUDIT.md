# Acts of the Apostles TEI source audit

## Source and scope

The retained source is Beta maṣāḥǝft Works file `LIT1019Actsof.xml` at commit `ec53d3f4c5de47e463fa56a8465cf1090316a999`, retrieved 2026-10-25. Its SHA-256 is `97d28f9b6ef3de974526d54572aaa7c509cd895563aca02fe45427d9e941611d` (360,137 bytes). The file-level TEI licence statement identifies CC BY-SA 4.0. Attribute Beta maṣāḥǝft and the named contributors in its header; identify extraction and whitespace normalization; share adaptations alike. The file-level license does not establish rights in the unidentified printed exemplar.

The TEI root defaults to `xml:lang="en"`; the enclosing edition declares `xml:lang="gez"`. The reader extracts the `Acts` division, explicitly labeled “Text of the EOTC printed Bible,” and does not include a separate `IntroductionActs` section. That introductory section contains incipits attributed in the TEI to a Vatican manuscript catalogue description; it remains intact in the retained source XML, outside the 28-chapter reader. This title-level EOTC link is provisional: the exact print exemplar, current edition identity, transcription accuracy, and physical-edition completeness remain unverified.

## Observed structure

The selected Acts division has 28 ordered chapter divisions and 1,208 TEI `<l>` elements: 1,007 with `n` labels, 201 without labels, and none empty. The build preserves all line elements in order, exact source labels, and source links. These are TEI structure counts, not verse-completeness claims.

Observed source-label irregularities, preserved unchanged:

- Chapter 12 repeats label `3`, then resumes at `8` (label `7` is absent).
- Chapter 14 repeats label `25`.
- Chapter 26 omits label `12` and repeats label `16`.

The retained TEI also contains unnumbered headings interspersed with numbered lines. The reader keeps them as line elements without treating them as numbered verses. No text or numbering has been reconstructed.

## Pinned sources

- [Beta maṣāḥǝft work record for LIT1019Actsof](https://betamasaheft.awhamburg.de/works/LIT1019Actsof/main)
- [TEI XML at pinned BetaMasaheft/Works commit](https://github.com/BetaMasaheft/Works/blob/ec53d3f4c5de47e463fa56a8465cf1090316a999/1001-2000/LIT1019Actsof.xml)
- [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
