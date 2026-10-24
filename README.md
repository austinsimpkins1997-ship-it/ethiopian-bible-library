# Ethiopian Bible Library — static site

Mobile-first and offline-capable. All catalogue, source, related-text, and reader data are embedded in `index.html`; the site makes no external data requests. On GitHub Pages or another HTTPS host, a service worker caches the app shell after a successful initial load and refreshes its saved copy during later online visits. Install it from the browser menu or share sheet where supported. A direct `file://` copy also works offline, but browsers do not allow service workers or install prompts for local files. Offline browser storage can be cleared or evicted by the device. Source links open only when a reader chooses them and need an internet connection.

The proposed multilingual and worldwide expansion is described in [GLOBAL-ARCHIVE-PLAN.md](GLOBAL-ARCHIVE-PLAN.md). This page is a static EOTC-focused prototype, not a global scripture database or a complete collection.

The portable record format is a draft v1 [text-layer JSON Schema](schemas/text-layer.schema.json), with examples for each of the eleven bundled readers and the separate Brenton English companion layer. The build combines these twelve records into a [single downloadable metadata manifest](examples/portable-text-layers.json). Each record checksums and points to its existing offline reader file; none duplicates the text. Exodus–Ruth and Psalms currently have no English translation, and their digitized Geʽez transcriptions have not been independently collated.

The reader software is MIT-licensed; project-curated descriptive metadata is CC BY 4.0 under the scope in `DATA-LICENSE.md`. These licenses do not relicense scripture or translation content; see `CONTENT-LICENSES.md`. The embedded `translation_registry` records language and script profiles, bundled layers, and unbundled leads separately. Geʽez and English have bundled text. Ten Eritrean language profiles are represented from cited language/script research; Dahalik is included with its default script and scripture witness left unestablished. Tigrinya, Tigre, Kunama, Blin, and Saho have unbundled scripture leads, with uncertain edition details and rights kept visible. The registry is not an exhaustive language census. Brenton English is identified as a Greek Septuagint companion rather than a direct translation from Geʽez. This is not global language coverage.

## Locally bundled reader

The web reader contains eight source-text books from the historical Ethiopic Octateuch edition edited by August Dillmann (1853–1855) and digitized/transcribed by Ran HaCohen: Genesis (50 chapters), Exodus (40), Leviticus (27), Numbers (36), Deuteronomy (34), Joshua (24), Judges (21), and Ruth (4). It also contains a 151-page Geʽez Psalter transcription from Ludolf's 1701 edition, digitized and retyped by Ran HaCohen at TAU. Psalter pages follow the online Rahlfs numbering; source marker irregularities are preserved. TAU warns transcription errors may remain, and this archive has not independently collated the text. The Genesis–Ruth source is not presented as the current official EOTC printed edition. The digitizer reports OCR followed by proofreading and warns that transcription errors may remain; the archive has not collated the text against manuscript witnesses. Verse numbering follows the Septuagint and is preserved as published. A separate Geʽez Jubilees transcription and the EOTC-labeled Geʽez 1 Enoch block are also bundled from pinned TEI records; their edition and rights boundaries are recorded separately. Brenton’s English Septuagint is bundled alongside Genesis only as a distinct historical English companion, not as a translation of this Geʽez witness.

Beside it is Brenton’s 1851 English translation of the Greek Septuagint: a public-domain English companion, **not a translation from the bundled Geʽez transcription**. The offline reader preserves 1,532 English labels, including lettered labels, and 197 translator/editor notes. It pairs passages by printed labels for navigation only and keeps unmatched labels visible; matching labels do not establish identical wording. The two witnesses have separate source and reuse notes.

The digitizer’s notice permits copying and distribution of the Ethiopic transcription for noncommercial purposes when the copyright and permission notices accompany every copy. Commercial rights are not granted. Brenton’s English translation is public domain.

The coverage index lists the 46 Old Testament and 35 New Testament entries on the EOTC English canon page. Eleven of those entries have bundled Geʽez web-reader text: Genesis through Ruth, Psalms, Jubilees, and 1 Enoch. Genesis also has a Greek-Septuagint-based English companion. The Psalter reader structurally audits 151 ordered TAU pages and 2,537 nonempty numbered units; duplicate, skipped, and nonnumeric labels are retained. That verifies page and extraction structure only, not textual accuracy, completeness against the 1701 print or manuscripts, or an exact Church-list crosswalk. The 1 Enoch reader uses only the pinned Beta maṣāḥǝft TEI block labeled EOTCed, identified there as the EOTC printed-Bible text. A local structural audit found chapters 1–108 and 1,058 labeled lines; chapter 21 starts with source marker 2, which is preserved. Source Text independently displays a 1,058-verse count, but no line-by-line collation was done. The exact physical print exemplar/date and transcription accuracy remain unverified. The separate restricted scholarly edition in the TEI is excluded, and the full upstream TEI snapshot is retained locally outside the Pages site while the public repository contains an EOTCed-only extract. A CrossWire SWORD Geʽez module is archived locally; its compressed text has not yet been decoded into reader chapters. A locally generated inventory records the eight Octateuch books. Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Joshua, Judges, and Ruth have source-linked chapter pages; verse markers were checked against links on local digitizer pages. This does not independently verify transcription accuracy, manuscript completeness, or an English translation. The 81-entry list is not a claim that all texts or translations are present; catalogue crosswalks remain separate and may need review.

## Run locally

Open `index.html` directly in a browser; no server or data fetch is needed. For optional local development, run `python -m http.server 8000` from this folder.

## Rebuild and verify the embedded site

From the project root, run:

```powershell
python site/build_jubilees_geez.py
python site/build_genesis_english.py
python site/build_genesis_geez.py
python site/build_exodus_geez.py
python site/build_octateuch_readers.py
python site/build_octateuch_inventory.py
python site/build_enoch_geez.py
python site/build_canon_registry.py
python site/build_eritrea_canon_evidence.py
python site/build_standalone.py
python build_archive.py
```

The Jubilees builder parses a pinned local, Ran-only TEI extract, preserving its selected edition and all source line markers. The full upstream snapshot is retained outside the published Pages site because it also contains a separate EOTC printed edition whose reuse terms are not individually clear. The 1 Enoch builder uses a public-repository extract containing only the EOTCed block; the full upstream TEI, including the excluded noncommercial edition 1, is retained outside the Pages site. It checks the 108 chapter divisions, labeled lines, and known chapter 21 marker gap. The Genesis and Exodus builders create source-linked Geʽez readers, and the Octateuch reader builder creates Leviticus through Ruth from the locally archived HaCohen chapter pages; these are historical digitizer transcriptions, not independently collated or English-translated texts. The inventory builder records the local CrossWire Geʽez module and verifies menu counts, while the canon builder creates the Ethiopian 81-entry coverage index. The module archive is source material, not reader text; its noncommercial terms and copyright notice are preserved. The Eritrea script preserves the numbered labels on an Eritrean Orthodox Diocese webpage as a separate source transcription, without claiming it is a final canon list or aligning it to the Ethiopian records. The standalone build validates project metadata, source links, reader/canon links, and eleven portable text-layer records (including package checksums) before embedding the archive. These eleven records describe ten reader files because Genesis also has a separate English companion layer. Metadata-only language records may have a null reader link; bundled records must resolve to a local reader. The GitHub Pages workflow reruns the build and blocks deployment when generated files are stale. These checks do not replace scholarly review. The final command updates the root JSON and CSV exports. All build inputs are stored locally; no command fetches remote data.

## Canon and completeness boundary

The Ethiopian Orthodox Tewahedo Church’s English canon page states 81 canonized books (46 Old Testament, 35 New Testament). This archive has 89 searchable research rows because titles may be split/indexed for research; 89 is not a canon count, and many mappings remain unverified. Genesis through Ruth, Jubilees, and the EOTCed 1 Enoch block have bundled Geʽez text. The other catalogue records do not imply a complete text is available. This is not an official Church publication. Read the edition and permission sources in the page’s Sources & method section before reusing the text.

## Eritrean comparison and language leads

The archive records Eritrean Orthodox and Tigrinya Bible sources separately from the Ethiopian canon and bundled readers. The 2000 Tigrinya Bible with deuterocanonical books is a multi-book corpus lead, not verified evidence of an 81-book translation; its contents, translation basis, and reuse rights remain unverified. A separate volunteer Tigrinya PDF is flagged as potentially incomplete and personal-use only. See the in-site research note at `research/eritrea.html` and source records SRC-045–SRC-054.

## Translation leads and adding a language layer

The registry separates language/script profiles, bundled language layers, book-level translation leads, and multi-book corpus leads. Corpus leads must match a registered language name and script; language profiles can exist before any scripture text is bundled. A lead is not reader text. For example, the 2000 Tigrinya edition is bibliographically identified but its book-level scope, translation basis, and reuse rights remain unresolved; a direct Ethiopic-to-English Jubilees translation by R. H. Charles (1902) is also identified, but its full text, structure, OCR, and territory-specific rights are not cleared for bundling.



Use `translation-registry.schema.json` and follow `CONTRIBUTING.md` and `CONTENT-LICENSES.md`. Translation records use an ordered BCP 47 path from source language through any relay languages to output, alongside edition, translator, rights, and review state. Unknown paths remain explicit as `null`. Texts are bundled only after source identity, boundaries, completeness, and reuse terms have been checked. Unknown or conflicting rights keep a text out of the reader.
