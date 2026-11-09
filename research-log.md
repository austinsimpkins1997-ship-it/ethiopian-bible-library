# Research log and source triage

Review date: 2026-10-24. This is preliminary desk research. Search snippets and site marketing copy were not treated as evidence of complete scripture texts.

## Preliminary research snapshot before the local readers were added

The following six-point review records the earlier catalogue-only state. Its statements about no bundled chapter text and no scripture reproduction describe that earlier snapshot; the implementation updates below supersede them.

## Main findings

1. The Ethiopian Orthodox Tewahedo canon is conventionally described as 81 books, but the exact enumeration/grouping varies across tradition and reference lists. The brief's 88-title scope is represented here as a catalogue view that splits grouped units for discovery; it is not described as a universally recognized 88-book canon.
2. No single complete, verified English corpus of all Ethiopian Orthodox canonical works was found. A secondary availability review says nine books are not widely available in English and identifies Meqabyan translations as provenance-sensitive. This remains a book-by-book research claim, not proof that no unpublished or local translations exist.
3. Candidate public-domain English texts include R. H. Charles's translations of Enoch (1912) and Jubilees (1902), plus older translations of selected deuterocanonical works. None has been copied into this archive; each exact source file must be checked for identity, completeness, and rights.
4. The Ethiopian Orthodox Bible Project category contains a lead to an English Third Meqabyan edition translated from Amharic. It is commercial; the translation's full provenance and rights for digital reproduction remain unresolved.
5. Digital Ark and Ertale were among the requested leads. Digital Ark's page was not readable in the research browser, and Ertale returned 403. Their actual content could not be verified.
6. The user's Internet Archive link is recorded as a lead for the Testament of Solomon. It could not be opened in the research browser, so edition, access, identity, and rights remain unverified.
7. Pistis Sophia (Askew Codex, British Library Add MS 5114), the Testament of Solomon, Psalms of Solomon, and 11Q11 are maintained as related-text leads, not silently inserted into the Ethiopian canon catalogue.
8. The Ugaritic Baal Cycle is included in the related-text register as comparative literature. The Louvre catalogue identifies an incomplete tablet witness (AO 16643 / RS 3.361) from Ras Shamra as part of a Baal myth cycle; a scholarly overview describes the larger cycle as KTU 1.1–1.6. It is not part of the Ethiopian canon and is not a Dead Sea Scroll. No translation has been copied, and reuse rights for external reading leads remain unresolved.
9. The image shared during the site work matches Harold L. Ginsberg’s Baal Cycle translation in Pritchard’s *Ancient Near Eastern Texts Relating to the Old Testament*, 3rd ed. with supplement (1969), p. 137. It is registered as a user-provided bibliographic lead only; the scan and translation were not published on the site.

## Candidate status meanings

“External source only” means the source contains catalogue or contextual information, not that the archive has verified or licensed the scriptural text. “Rights unresolved” blocks copying or narration. The CSV intentionally has no chapter counts or text/completeness claims yet.

## Inspected links

All source URLs, inspection summaries, and limitations are in `sources.csv`. Candidate texts that were not inspected are not marked verified. The archive has not been deployed, and no scripture content has been reproduced here.


## Implementation update — 2026-10-24

The archive now bundles one reader: the Geʽez Genesis transcription digitized from August Dillmann's 1853–55 Octateuch edition by Ran HaCohen. The local build captures all 50 chapters and 1,526 source-linked verse markers. The builder checks chapter sequence, page identity, marker order, and nonempty text; each captured source page is fingerprinted. This is a source/structure verification, not independent manuscript collation or a claim that the transcription is error-free. The source itself warns that transcription errors may remain, omits its critical apparatus, and uses Septuagint-based verse numbering that can have gaps. The site labels the edition and this limitation, preserves the source numbering, and includes HaCohen's noncommercial reuse notice. It does not claim that this historical edition is the current official EOTC print edition.

Only Genesis is bundled as scripture text. The other catalogue entries remain catalogue records; no chapter text or completeness is claimed for them. Narration has not been added. This implementation is local and has not been published to GitHub.


## Translation implementation update — 2026-10-24

The Genesis reader now bundles two witnesses for immediate offline comparison: the Geʽez Dillmann/HaCohen transcription and Sir Lancelot Charles Lee Brenton’s 1851 English translation of the Greek Septuagint. Brenton is not translated from the Geʽez transcription; the UI labels it as an English companion and warns that matching chapter/verse labels do not certify equivalent wording. Its 50 chapter captures retain 1,532 labels (including the source label 50a) and 197 translator/editor notes. The Geʽez side retains its 1,526 source-linked markers. Data and notes are embedded locally; no translation API is called at runtime.

This provides a named English witness, not the requested new direct Geʽez-to-English translation. A genuinely direct English rendering remains unverified and should not be synthesized from the English Septuagint and passed off as one. The next translation stage needs a qualified Geʽez translator, source-text collation, a documented editorial method, and independent review. Brenton’s translation is identified by eBible.org as public domain; the Geʽez transcription keeps its separate noncommercial reuse notice. The reader has not been published to GitHub in this work.

## Full-canon coverage update — 2026-10-24

The Church’s English canon page states 81 canonized entries (46 Old Testament, 35 New Testament) and presents grouped book names. A local coverage registry now records all 81 source-list entries, while preserving the archive’s 89 split research rows separately. Genesis alone currently has bundled reading text. The registry is a sourced checklist, not a claim that the other texts are available or verified.

The public repository `cpradmin/ethiopian-bible` was inspected as a potential full Geʽez corpus and not used as scripture. Its README lists Kebra Nagast among its “unique to Ethiopia” set, claims 81 books without reconciling its contents to the Church list, and says its English comparison layer covers 3.3%. Its declared repo-level license and Beta maṣāḥǝft attribution do not verify each file or clear upstream text rights.

A separate source register entry records book-specific Geʽez leads for 1 Enoch and Jubilees via Beta maṣāḥǝft, as documented by Source Text. Direct inspection of the pinned upstream XML surfaced a rights conflict for Enoch: the outer file says CC BY-SA 4.0, while the notice embedded in that same file gives the underlying 1995 transcription a noncommercial/no-sale restriction. The conflict is unresolved; Enoch is not cleared for reuse. The pinned Jubilees XML explicitly makes HaCohen's transcription available under CC BY-SA 4.0, so it is a viable candidate pending text-boundary/parser validation and attribution. Neither text has been added to the reader yet.

A complete, verified direct Geʽez-to-English reader for all 81 entries has not been established. The immediate engineering goal is to add books only when the text witness, boundaries, translation provenance, and reuse terms can be stated; the coverage index displays the remaining gaps instead of filling them with unverified text.

## Open multilingual archive foundation — 2026-10-24

The site now carries a language/translation registry and JSON Schema for source and translation layers. Records include BCP 47 language tags, ISO 15924 script codes, text direction, layer role, source/target basis language, translator when applicable, rights status, source IDs, canon mapping, and a bounded review status. The reader UI derives its `lang` and `dir` attributes from this metadata, rather than assuming every future script is left-to-right. The embedded registry is bundled in the static page; it causes no network request.

The present registry contains two bundled Genesis layers: a Geʽez transcription and Brenton's English translation based on Greek. It records zero direct Geʽez-to-English translations and does not imply representation of every language. The reader remains one book out of 81 listed entries. The site is a static, offline-capable archive, not yet a collaborative global database service.

The software is now explicitly MIT-licensed. That license does not grant blanket rights to scripture, translation, images, or apparatus. `CONTENT-LICENSES.md` separates software licensing from per-text rights, and `CONTRIBUTING.md` specifies evidence and review gates for adding material. No machine-produced rendering is admitted as a verified translation without qualified source-language review.

Validation on this update rebuilt the two Genesis text layers, 81-entry registry, and embedded page; checked the canon, language-layer, source, translation, and reader cross-references; parsed the embedded archive; confirmed unique page IDs and JavaScript syntax; and confirmed that the language panel is local-data driven. A JSON Schema validator package is not installed in this environment, so validation used the standalone builder's structural checks and direct JSON parsing. The update has not been published to GitHub.


## Jubilees reader implementation — 2026-10-24

The pinned Beta maṣāḥǝft `LIT1697Jubilees.xml` TEI snapshot is stored at `site/readers/source/jubilees/LIT1697Jubilees.xml` (SHA-256 recorded in `site/readers/jubilees-geez-hacohen.json`). The TEI publication statement explicitly extends CC BY-SA 4.0 to Ran HaCohen's transcription. The snapshot contains multiple editions; only edition `xml:id=Ran` is used in this reader. The separately encoded EOTC edition is preserved in the source file but is not merged into the display text.

The reader builder finds exactly chapters 1–50 in the selected edition and extracts all 1,139 nonempty numbered line elements. Source `n` attributes repeat and skip values (chapter 26 begins with `n=26` and later repeats `n=26`), so the reader assigns a unique display order while showing each original source marker beside it. These are not represented as canonical verse numbers. Unnumbered incipit is not silently inserted into chapter 1. No English Jubilees translation was added; the reader offers only the Geʽez source transcription.

The reader navigation now includes Genesis and Jubilees, and the 81-entry coverage index marks those two entries with bundled text. Genesis's historical English companion is offered only for Genesis and remains explicitly identified as Brenton's Greek-based translation. The root exports and embedded static page are rebuilt from local files. Validation rebuilt all reader and registry outputs; structural checks accepted both books and the JavaScript syntax check passed. No publication to GitHub occurred.

## Historical English Jubilees translation lead — 2026-10-24

A primary bibliographic record identifies R. H. Charles's 1902 English Jubilees as translated from the editor's Ethiopic text (SRC-042). Wikimedia Commons identifies its scan as a 1902 London edition, translated from Ethiopic, and applies a Public Domain Mark based on the author's life-plus-70 term while flagging some country exceptions (SRC-043). This makes it a strong direct-language witness candidate, but not a blanket global-rights determination.

The candidate is now recorded separately from bundled texts in `translation-registry.json` and surfaced on the site as **not bundled**. Full text extraction, chapter and verse boundary comparison against the scan, OCR correction, note preservation, and territorial rights review remain outstanding. No English Jubilees text was copied or represented as verified in this update.


## 2026-10-24 — Charles Jubilees OCR intake audit

- Confirmed the Internet Archive record for Charles's 1902 London edition: it says translated from Ethiopic, reports 384 pages, and identifies Tesseract 5.0.0 OCR.
- Preserved the downloaded 953,770-byte OCR capture outside the published `site/` directory at `source-captures/jubilees-charles-1902/bookofjubileesor00char_djvu.txt`; SHA-256 `491e1726cdca207a4bc3a8b6877faed30cb43ba247246354567d43dfd84e35c5`.
- Spot inspection found page-running headers and translator commentary intermixed with scripture; 149 `CHAPTER` strings are not chapter count evidence.
- Decision: do not produce or publish a Charles English reader yet. Chapter/verse segmentation, OCR correction against all scan pages, apparatus separation, and jurisdiction-aware rights review are outstanding. The translation remains a lead, not verified text. See `site/readers/source/jubilees-english/SOURCE-AUDIT.md`.


## 2026-10-24 — Jubilees TEI edition boundary review

- Inspected the pinned `LIT1697Jubilees.xml` source and confirmed that it contains two distinct Geʽez editions: HaCohen's `Ran` transcription and an `EOTCed` edition labelled “standard printed EOTC Bible edition.” The license notice explicitly identifies the HaCohen transcription; the EOTC edition's separate reuse status is unresolved.
- To avoid silently republishing the second edition, moved the original snapshot outside the deployed `site/` tree (`source-captures/betamasaheft-jubilees-2025/LIT1697Jubilees-original.xml`, SHA-256 `d8c6eaa3857c35d8e467a6c150178fc02395fc569527bedfc7687c43cc68d87f`) and generated a Ran-only TEI build input (`site/readers/source/jubilees/LIT1697Jubilees-Ran.xml`, SHA-256 `95df4eadacbdec938e1a5196c1a9f86c5168b59755129d454a417f51eaa9fa9e`).
- Updated the offline builder, source record, reader provenance, README, and content-license notes. The original remains available locally for audit; only the explicitly licensed Ran edition is in the site build input.


## 2026-10-24 — Eritrean canon, language, and Tigrinya Bible research

- Added sources SRC-045–SRC-052: Eritrean Orthodox Diocese canon page; Four Corners catalog for the 2000 Tigrinya deuterocanonical Bible; Senai W. Andemariam's peer-reviewed translation-history article; UNICEF Eritrea language-policy review; Geʽez Experience's rights/quality notice and PDF; and Eritrean Constitution/Civil Code records at WIPO Lex.
- Added two Tigrinya multi-book corpus leads to `site/translation-registry.json`, explicitly not bundled. The 2000 edition's translation basis and contents are unknown; the volunteer PDF's publisher text warns that verses may be missing and restricts reuse to personal use absent permission.
- Recorded the 1957 / 1998 / 2000 publication-history distinction and the conflict with the catalog's “first Tigrinya Bible” wording. The Diocesan canon list's “Didascalia | Didache” entry is flagged as ambiguous rather than flattened into the EOTC list.
- Added the in-site note `site/research/eritrea.html`. No Tigrinya scripture was copied, and bundled reader coverage remains unchanged.

## Evidence and coverage integrity follow-up — 2026-10-25

The site now distinguishes inspected repository metadata from uninspected scripture payloads in the cpradmin/ethiopian-bible lead. README, translation policy, license, index, books metadata, and canon metadata were inspected; the advertised chapter files and text were not downloaded or audited. The repository claims 81 books and its canon metadata contains 81 objects, but this does not establish complete book texts or a crosswalk to the Church list. The README’s six category counts total 91 if disjoint; overlap remains unexplained. The repository-level CC BY-NC-SA notice does not settle rights in underlying TEI-derived text. No text was copied, no coverage was added, and unknown extent remains unknown rather than zero. SRC-039 is now explicitly marked as a preliminary record about the same repository; SRC-141 contains the later metadata inspection.

At the time this preliminary inspection was written, 11 of 81 Church-list entries had bundled source-text readers. Subsequent local additions supersede that count; the current snapshot has 17 of 81, and the other 64 are “not bundled here,” not evidence that no text exists elsewhere. Separate companion translations and research readers remain outside the canon-linked count. Generated or unreviewed wording remains ineligible as verified scripture.

## External source link review — 2026-10-25

The secondary PDF-download guide SRC-004 remains in the provenance record, but the UI now withholds outbound navigation to that page. A user-provided browser screenshot showed a security block when opening its linked PDF on img1.wsimg.com and categorized it as malware/phishing. This is recorded only as a browser-reported warning; the file was not downloaded or independently scanned, and the archive does not call it confirmed malware. All source-link render paths now use one shared withholding rule so catalogue, translation, language-evidence, reader, related-text, and source-list references do not bypass the restriction. The guide remains a secondary candidate source and no candidate PDF was imported.

## Jonah source transcription added — 2026-10-25

- Captured TAU's four Ethiopic Jonah text pages, its book information page, general rights notice, and index. Raw responses, HTTP status, last-modified metadata, byte lengths, capture timestamps, and SHA-256 digests are in `site/readers/source/jonah-tau-2018/SOURCE-CAPTURE.json`.
- TAU identifies Oscar Löfgren's 1930 critical edition, pp. 3–9; it credits Kefela Ghebre with preparing the text (posted with his permission) and Ran HaCohen with proofreading. TAU's site notice permits noncommercial copying/distribution only with the notice; no open or commercial license is claimed.
- `site/build_jonah_reader.py` checks every captured asset and retains the four source pages' labels exactly: 16, 11, 10, and 11 (48 total). Whitespace is normalized and the linked label is held separately from the text body. No verse alignment, printed-edition completeness, manuscript completeness, or current EOTC edition identity is claimed.
- Added a provisional title-level link to Church-list entry 38, the Geʽez language layer, source and rights records, and a reader package. The full build embeds this content without runtime fetching.
- The normalized graph schema's agent role vocabulary now includes `reviewer`, allowing the credited proofreader attribution to survive graph generation.

## Nahum source transcription added — 2026-10-25

- Captured TAU's three Ethiopic Nahum text pages, its book information page, site-wide rights notice, and Old Testament index. Raw responses, HTTP status, last-modified metadata, byte lengths, capture timestamps, and SHA-256 digests are retained in `site/readers/source/nahum-tau-2018/SOURCE-CAPTURE.json`.
- TAU identifies Oscar Löfgren's 1930 critical edition, pp. 13–20; it credits Kefela Ghebre with preparing the text (published on TAU with his permission) and Ran HaCohen with proofreading. The site-wide notice permits noncommercial copying/distribution only with the copyright and permission notice; no open or commercial license is claimed.
- `site/build_nahum_reader.py` validates the retained local assets and parses three text pages with sequential source-linked labels 1–15, 1–14, and 1–19 (48 total). No wording is translated or silently emended; no print/manuscript collation, completeness beyond the captured digital pages, or current EOTC edition identity is claimed.
- Added a provisional title-level crosswalk to Church-list entry 39, language and rights records, source citation, reader view, and package tests. Canon-linked reader availability rose to 14/81; 67 entries remain without a bundled reader in this local snapshot. This is not a worldwide availability census.


## Habakkuk source transcription added — 2026-10-25

- Captured TAU's three Geʽez text pages, book information page, general reuse notice, and index. `site/readers/source/habakkuk-tau-2018/SOURCE-CAPTURE.json` records capture metadata and SHA-256 digests.
- TAU's information page identifies Oscar Löfgren's 1930 edition, pp. 23–32; it credits Kefela Ghebre with preparing the web text and Ran HaCohen with proofreading (2018). TAU's general notice limits reuse to noncommercial copying/distribution with its required notice; this is not an open license or commercial grant.
- `site/build_habakkuk_reader.py` validates and parses the three captured pages, retaining 17, 20, and 19 labels (56 total) and each source link target. The second page is titled/indexed as Habakkuk 2, but its twenty links target Nahum 2. This anomaly is preserved and exposed; no correction is inferred.
- Added a provisional title-level crosswalk to Church-list entry 40. This is a source transcription, not an English translation; print/manuscript collation, completeness beyond captured pages, and exact current EOTC edition identity remain unverified. Canon-linked reader availability at that step was 15/81 in the local snapshot (66 without bundled reader text).


## Zephaniah source transcription added — 2026-10-25

- Captured TAU's three Geʽez text pages, book information page, site-wide reuse notice, and index. Capture metadata, byte lengths, HTTP status, and SHA-256 digests are retained in `site/readers/source/zephaniah-tau-2022/SOURCE-CAPTURE.json`.
- TAU identifies Oscar Löfgren's 1930 edition, pp. 36–43, and credits Ran HaCohen with preparing the text in March 2022. The site notice permits noncommercial reuse only with the required notices; this is not an open or commercial license.
- The local parser retains sequential displayed labels from the three title/menu-identified chapters: 18, 14, and 20 (52 total). It verifies capture-to-reader extraction and matching Zephaniah link targets, not collation against print, manuscripts, or a current EOTC edition. No English translation is included.
- Promoted the metadata lead into a source-backed but provisionally crosswalked reader for canon-list Zephaniah. Local coverage is now 16/81; 65 entries have no bundled reader in this snapshot. This does not imply that no external text exists.


## Haggai source transcription added — 2026-10-25

- Captured TAU's two Geʽez text pages, book information page, site-wide reuse notice, and Old Testament index. Capture metadata, byte lengths, HTTP status, and SHA-256 digests are retained in `site/readers/source/haggai-tau-2018/SOURCE-CAPTURE.json`.
- TAU identifies Oscar Löfgren's 1930 edition, pp. 47–53; it credits Kefela Ghebre with preparing the text (posted with his permission) and Ran HaCohen with proofreading. TAU dates this text version October 2018. The site notice allows noncommercial copying/distribution only with its copyright and permission notice.
- The local parser retains sequential displayed labels from the two title/menu-identified chapters: 14 and 23 (37 total). Link targets identify matching Haggai chapters. This verifies capture-to-reader structure only, not collation against print, manuscripts, or a current EOTC edition. No English translation is included.
- Replaced the metadata-only candidate with a source-backed but provisionally crosswalked reader for Haggai. Local availability is now 17/81; 64 entries have no reader bundled in this snapshot. This does not imply that no external edition exists.


## Joel source transcription added — 2026-10-25

- Captured TAU’s four Geʽez text pages, Joel information/attribution page, site-wide reuse terms, and Old Testament index. Raw HTML, status, byte sizes, capture time, and SHA-256 values are retained under `site/readers/source/joel-tau-2024/`.
- TAU identifies August Dillmann’s 1879 critical edition (pp. 449–458) and credits Ran HaCohen with preparing the online text (June 2024).
- The page parser retains 70 linked units: chapter extents 20, 26, 5, and 19. Linked labels 2:16 and 4:2–3 are absent and remain explicit gaps. The archive makes no conjectural repair or re-numbering.
- TAU’s site-wide permission is noncommercial and notice-bound; this is not an open license. The EOTC title mapping is provisional; text accuracy, completeness against print/manuscripts, and English translation remain unverified/not bundled.
- The local build now links Joel to its source transcription while explicitly preserving those limits.


## Brenton USFM ancillary inventory corrected — 2026-10-25

- Re-audited all USFM members in the retained eBible.org Brenton ZIP by their `\id`, headings, and raw bytes. The 57-member package consists of 38 additional biblical-book members parsed as research readers, 12 book members handled by separate local readers, and seven non-book ancillary members.
- The seven ancillary members are FRT (abbreviations/signs used in notes), INT (1870 introduction), XXB (1844 preface), XXC (errata), BAK (appendix), OTH (historical introduction to the Apocrypha), and XXA (Jeremiah chapter/verse table). Their byte lengths and SHA-256 values are now listed individually in the package capture manifest.
- Corrected earlier documentation that mistakenly called these seven “parser failures.” They are still retained within the checksummed source ZIP; none is a missing scripture book. The reader builder now asserts the exact 57-member classification and stops if the source package changes.


## Amos source transcription added — 2026-10-25

- Captured TAU’s nine menu-listed Geʽez text pages, Amos information/attribution page, site-wide reuse terms, and Ethiopic index. Raw HTML, HTTP status, content type, byte size, capture time, and SHA-256 are retained under `site/readers/source/amos-tau-2009/`.
- TAU identifies Pereira’s 1917 critical edition; it credits Kefela Ghebre with preparing the digital text and says it is posted with his permission, and credits Ran HaCohen with proofreading. TAU’s general notice grants noncommercial copying/distribution with required notices; no open or commercial license is claimed.
- The parser retains 146 source-linked labels across nine pages (15,16,15,13,27,14,17,14,15). Every linked page target uses `Amo`. The Church-list title mapping remains provisional; print/manuscript accuracy and completeness remain unverified.
- Added a canon-linked Geʽez reader without asserting exact current EOTC witness identity or inventing a translation from Geʽez. The reader also exposes Brenton’s existing 146-label English Septuagint text as a clearly separate Greek-based companion; matching labels are navigation only.


## 2026-10-25 — Ugaritic Baal Cycle source status

- Inspected the University of Göttingen EUPT corpus page and recorded it as SRC-194. It identifies KTU 1.1–1.6 as the Baʿlu Epic, describes its digital philological workflow, and currently schedules those editions for 2027–2029. The schedule is a project forecast, not an existing complete translation; reuse terms for future project materials are not established.
- Updated REL-001 and the Baal Cycle research guide. The six recommended books are English-language scholarship; their full text is not being reproduced or purportedly translated. No Ugaritic or new English Baal Cycle text was added.
- Rebuilt the offline site and verified the package manifest. This checks archive structure and integrity only, not scholarly accuracy.


## 2026-10-25 — Malachi source-text reader

- Captured four TAU Ethiopic Malachi text pages plus their attribution, general permission notice, and index; retained HTTP status, byte length, and SHA-256 for each asset. TAU identifies the 1930 Löfgren edition, credits Kefela Ghebre as preparer (with permission), and Ran HaCohen as proofreader.
- Built a Geʽez reader with 55 sequential source-linked labels and preserved the unnumbered closing doxology as a continuation after chapter 4:6. The three-chapter Brenton English reader is Greek-based and was kept separate; no verse alignment is inferred.
- Registered the edition as a provisional Malachi title-level crosswalk. No collation against print or manuscripts or current EOTC edition was performed. TAU notice permits noncommercial reuse only with required notices; this is not an open-content/commercial license.
- Rebuilt the offline package and validated source capture hashes, page/label structure, archive schema and local manifest. Current count: 20 of 81 Church-list entries have linked reader records; this does not certify completeness or accuracy.
