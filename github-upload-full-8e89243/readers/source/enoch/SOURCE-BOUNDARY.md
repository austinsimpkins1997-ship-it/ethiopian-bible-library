# 1 Enoch TEI edition boundary

## Selected reader text

The reader is generated only from `LIT1340EnochE-EOTCed.xml`, the locally stored extract of the pinned Beta maṣāḥǝft TEI block `xml:id="EOTCed"`. The TEI labels this block “Text of the EOTC printed Bible.” It says edition 2 was digitized by partner projects from modern Vulgata printed editions and converted to XML by the Beta maṣāḥǝft team. The TEI does not identify the exact printed exemplar or its date.

The same TEI file contains another text block, `xml:id="ed1"`, which follows August Dillmann’s 1851 critical edition and carries a separate 1995 noncommercial/no-sale notice. That text is not present in the site extract or reader. The full upstream TEI is preserved locally outside this Pages site repository at `../../../../source-captures/betamasaheft-enoch-2026/LIT1340EnochE-original.xml` for audit.

## Provenance and rights

- Pinned upstream: [Beta maṣāḥǝft `LIT1340EnochE.xml`](https://raw.githubusercontent.com/BetaMasaheft/Works/ff9d4981eba2084c4914ca840ff323d85cbd2a1d/1001-2000/LIT1340EnochE.xml), commit `ff9d4981eba2084c4914ca840ff323d85cbd2a1d`.
- Full upstream SHA-256: `61dd5b372894e54c10f661740d0dd3fbfbfaeef4c99c55690eed4b4aae03f6d9`.
- Public, EOTCed-only extract SHA-256: `24158d4b631141f13c9f68f771b0a225993c5a0ece422d29d0c86c5bda71be40`.
- Edition-specific corroboration: [Source Text 1 Enoch record](https://biblesrc.org/text/enoch) identifies its Geʽez source as the EOTC printed edition and states CC BY-SA 4.0. This source displays 1,058 verses; the count agrees with the local TEI lines, but the texts were not compared line by line.
- The selected EOTCed text is published here under CC BY-SA 4.0 with attribution, ShareAlike, and change-notice requirements. The additional noncommercial/no-sale notice explicitly names the excluded Edition 1. No rights claim is made for other editions or for the unspecified physical print exemplar.

## Structural review

The selected block contains 108 direct chapter divisions numbered consecutively 1–108, with 1,058 nonempty `<l n>` entries. Each entry’s text and original `n` label is retained. The reader displays a separate order number for stable navigation; this display index is not a normalized canon verse number. Chapter 21 begins with source marker `2`; it remains `2`, without an invented marker `1`. Structural checks do not establish transcription accuracy against the physical print or manuscript witnesses. Completeness is asserted only for the captured EOTCed TEI block, not for every printed EOTC witness.
