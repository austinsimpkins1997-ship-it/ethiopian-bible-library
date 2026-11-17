# Historical parallel witnesses — 2026-11-16

**Current status:** all 12 resumption candidates implemented locally; 23 historical
comparisons total (16 label-navigation, seven independently selected chapters).
Malachi extraction repaired from retained HTML. The dated sections below preserve
the earlier batch findings; the final closeout supersedes their pending-work status.

## What changed

Five existing Geʽez readers now include separately identified Brenton English
Septuagint companions. These are historical Greek-to-English witnesses, not
translations of the bundled Geʽez wording. No text was generated to fill gaps.

| Reader | Captured Geʽez labels | English labels | Chapter pairs |
|---|---:|---:|---:|
| Obadiah — Bachmann / THEOT | 21 | 21 | 1 |
| Jonah — Löfgren / Ghebre | 48 | 48 | 4 |
| Nahum — Löfgren / Ghebre | 48 | 47 | 3 |
| Zephaniah — Löfgren / HaCohen | 52 | 53 | 3 |
| Haggai — Löfgren / Ghebre | 37 | 38 | 2 |

This adds 13 historical chapter comparisons: 11 → 16 companion-enabled readers,
400 → 413 chapter pairs. The archive still has 759 reader packages and source-text
links for 19 of the 81 Church-list entries. The English editions already existed
as separate research readers; nesting a companion does not discover a new text,
verify a translation, or add Church-list book coverage.

## Evidence and preservation

`build_minor_prophet_companions.py` rebuilds each source transcription through
its existing captured-HTML parser and reparses the retained Brenton ZIP. It
checks package/member digests, reader identity, separately recorded rights,
Greek-to-English basis and the declared chapter sequences before writing the
five-book batch. Stored English text must match its owning builder's output;
only the two known standalone display annotations may be additional fields.

Brenton source package: `readers/source/brenton-septuagint/eng-Brenton_usfm.zip`.
SHA-256: `ce098084f168f8bb67081ab48061588f7074d4f68d88dec2ab3edbcc10607a7a`.
Provider and retained notice: SRC-038 and SRC-142; the package manifest records
each selected member and its digest. Geʽez source notices, attributions and
capture checks remain with the corresponding source reader and portable layer.

The Geʽez transcriptions retain their noncommercial permission and required
copyright notices. Brenton retains the provider's public-domain claim. The
English layer's status does not change the rights of the Geʽez layer or grant
commercial permission for the combined package.

Matching labels are navigation aids, not verified alignment. Nahum 1:15 is
source-only; Zephaniah 2:15 and Haggai 1:15 are English-only in these stored
chapter inventories. Every unit remains visible, including unmatched units.
These label differences are not evidence that either witness has missing
meaning, erroneous wording, or a missing equivalent passage elsewhere.

## Indexed implementation

- Builder and preflight: `build_minor_prophet_companions.py`.
- Release integration: `build_standalone.py`, called by `build_release.py`.
- Source readers: the five named Geʽez JSON packages under `readers/`.
- Portable companion records: `examples/obadiah-brenton-translation-layer.json`,
  `jonah-brenton-translation-layer.json`, `nahum-brenton-translation-layer.json`,
  `zephaniah-brenton-translation-layer.json`, `haggai-brenton-translation-layer.json`.
- Label inventory and source/member digests:
  `research/minor-prophet-parallel-review.json`.
- Reader association and independent English rights: `translation-registry.json`.
- New preservation and failure checks: `tests/test_minor_prophet_companions.py`.
- Display/export coverage: `tests/test_parallel_coverage.js`,
  `tests/test_reader_package.js`, `tests/browser_smoke.cjs`.
- Offline shell: v49. Existing source captures and source ZIPs are unchanged.

## Review status and next work

The offline release build, six new preflight tests, eight Node suites and real
Chrome reader checks passed. Browser checks covered the existing flow at
320/390/768/1440 pixels and all five new companions at 390/1440 pixels,
including unmatched labels and retained alignment limits. The initial browser
assertion used rendered innerText for collapsed evidence; it was corrected to
inspect retained textContent. No product wording was removed to pass that check.

The initial 420-test Python run had three outdated expectations after this
addition: Haggai's former no-companion statement and two old layer totals.
Those expectations were corrected while retaining the unchanged 19-entry
source-text coverage check. Full-suite revalidation passed: 420 tests run, 400 passed and 20
explicitly skipped. Skipped cases are not counted as passed.

Seven intake candidates remain for separate review: Habakkuk, Malachi, Sirach,
I/II Samuel and I/II Kings. Malachi and I Kings have divergent chapter totals;
Habakkuk has a recorded chapter-2 link-target anomaly. Do not infer mappings or
repair source wording silently. Neither print/Greek collation nor scholarly
Geʽez-to-English alignment has been performed. Nothing in this update certifies
an official or complete Ethiopian Orthodox Bible.

Changes are local on `codex/parallel-witness-resumption-2026-11-16`; publication
and live deployment are not claimed. Recovery baseline is commit
`b6ee7e618b2ae79b1b14ebadad10258c32cb885b`. Original inputs remain retained;
the builder and label inventory make the added comparisons reproducible.

The user-adopted ChronoRealm workflow package was read in full. Its nine listed
digests matched and its 16 portable-review tests passed. Those are tool/package
checks, not independent evidence that a Scripture transcription is accurate.

## Local verification closeout

Recorded at 2026-11-16T20:30:21-05:00 (local machine clock, not independently authenticated).

The final source comparison against the baseline commit found identical
Geʽez chapter content, unit totals, copyright notices and rights classifications
for all five readers. No retained source capture or ZIP changed. Eight Node
suites passed, including the expanded complete-witness export check. The
full Python suite passed with 20 explicit skips. Original failure logs and
the corrected-run logs remain in the ignored task checkpoint directory.
The broader witness-addition goal remains active; this closes only the
first five-book local implementation and validation batch.

## Continuation — seven independent comparisons

The seven remaining intake candidates have now been implemented locally. They
use independent source/English chapter controls, not inferred verse rows.

| Geʽez witness | Source pages | English chapters | Source / English labels |
|---|---:|---:|---:|
| Habakkuk — Löfgren / Ghebre | 3 | 3 | 56 / 56 |
| Malachi — Löfgren / Ghebre | 4 | 3 | 55 / 55 |
| Sirach — Dillmann / HaCohen | 51 | 51 | 1341 / 1368 |
| I Samuel — TAU Regum I | 31 | 31 | 805 / 792 |
| II Samuel — TAU Regum II | 24 | 24 | 691 / 697 |
| I Kings — TAU Regum III | 23 | 22 | 765 / 823 |
| II Kings — TAU Regum IV | 25 | 25 | 718 / 723 |

There are now 23 historical comparison-enabled readers: the 16 label-navigation
comparisons from the first batch and baseline, plus these seven independent
comparisons. The 413 label-navigation chapter comparisons are not increased by
pretending the independent chapters align. All 759 reader packages and the
19/81 source-text Church-list entry count remain unchanged. The four Samuel/
Kings source readers remain research-only; their work/title crosswalk does not
upgrade them into canon-linked source readers. The Brenton English editions
already existed; these are additional comparison locations, not new translations.

### Preserved differences

- Habakkuk page 2 retains its twenty links targeting Nahum. Its page title/menu
  identification and the conflicting external targets remain explicit. The
  English comparison does not silently repair or resolve them.
- Malachi retains four source pages alongside three English chapters.
- I Kings retains all 23 source-page positions, including 3a/3b and the captured
  menu order 21 before 20. English keeps its own 22 chapters.
- I Samuel's source page 31 retains a span linked to 2 Samuel 1:1, which also
  occurs in TAU Regum II page 1. Neither copy is moved, merged or deleted.
- Sirach preserves Geʽez label gaps, English prologue labels 1a–1g, its prologue
  heading, source notes and the unnumbered English continuation.

English starts at its own first chapter, explicitly independently of the source.
Changing a source page keeps the chosen English chapter. Every English chapter
remains selectable, including in English-only view and read-aloud controls.
Exports retain both complete witnesses with their separate rights and evidence.
No automatic chapter/verse crosswalk is offered for these seven comparisons.

### Additional indexed files

- `build_additional_witness_companions.py`: source/capture preflight, separate
  rights, pinned English member parsing and seven comparison associations.
- `research/additional-parallel-witness-review.json`: observed page/chapter and
  label counts, source IDs, member hashes, page order and comparison limits.
- Seven `examples/*-brenton-comparison-layer.json` records: nested English
  comparison occurrences; Sirach retains its existing English witness identity.
- Four `examples/samuel-*-geez-research-layer.json` /
  `examples/kings-*-geez-research-layer.json` records: portable source provenance
  carrying the existing scoped work/title review, not new accuracy claims.
- `reader-english.js` and `app.js`: independent chapter choice, readable English
  notes, evidence, narration context and distinct English-only/source views.
- `tests/test_additional_witness_companions.py`: preservation, divergent chapter
  inventories, prologue/continuation retention, anomaly and rejection checks.
- Existing browser, export, coverage and navigation suites include the additions.

The strict build first rejected missing scoped identity-review metadata for the
new Samuel/Kings portable records. The fix linked the existing cited work/title
review; the gate was retained. Browser testing then exposed an out-of-scope
source-link helper in the new English-only view. Its evidence renderer was
corrected and an explicit comparison-page exception check was added. Final
validation and release evidence are recorded below after completion.

### Malachi extraction repair discovered during visual review

The pre-existing Malachi parser closed a unit at `</a>`, but the retained source
puts only the verse number inside that link; the actual Geʽez follows in a sibling
span. Consequently the old reader stored digits as its 55 verse bodies. Nonempty
unit/count checks had not caught the omitted wording.

The repair closes units at the next verse label or paragraph end, retains the
source's introductory Geʽez heading, and keeps the unnumbered closing doxology
separate. A new regression verifies the post-link body boundary and compares
every Ethiopic character in each captured HTML body with the extracted heading,
verse bodies and continuation, in order. Each verse must contain Ethiopic letters,
rather than merely a nonempty number. This is source-to-extraction fidelity,
not an independent Geʽez translation, proofreading or printed-edition review.

Malachi's derived wording therefore changes intentionally; its original captures,
55 labels, rights notice and chapter/page order do not. Preservation checks must
compare this repair with the retained HTML, not restore the earlier extraction bug.

The integration also preserves Samuel/Kings' existing normalized work identifiers
and checks rights associations by both reader and translation ID. Sirach's two
packaging locations retain identical English chapters and rights under the same
translation identity.

## Final local closeout — 2026-11-16T21:14:55-05:00

All 12 intake candidates are implemented and verified locally. There are 23
historical comparison-enabled readers: 16 label-navigation comparisons and
seven independent chapter comparisons. All 759 packages and 19/81 source-text
Church-list entries remain unchanged in count. The archive contains no generated
replacement wording or inferred cross-witness alignment.

Validation: 428 Python tests run (408 passed, 20 explicitly skipped), eight
Node suites, and real Chrome checks. The full release pipeline passed again
and reproduced the identical archive SHA-256: `8b42b5741dc0a6a407ce3caf54a14dde2c9548134fc8e74bf7840f7c30ac2f67`.

All twelve source chapter payloads match their owning capture parsers. Eleven
also match the baseline chapter payloads exactly; Malachi intentionally replaces
the old number-only extraction with the retained HTML wording and heading.
No original source capture or ZIP changed. A bounded scan also found literal
`DDD` in I Samuel 23:3 and confirmed it in retained
`readers/source/reigns-tau-dillmann/regum-i-23.html`. It is preserved, not silently
emended; its origin is unknown.

The requirement-by-requirement evidence and remaining scholarly/source limits
are recorded in `research/parallel-witness-completion-review.json`. This is local
implementation and release preparation, not a GitHub push, deployment, official
canon certification, legal certification or translation-accuracy certification.

### Storage recovery during packaging

The C: export failed with `ENOSPC` while creating an uncompressed staging copy.
Automatic review blocked the proposed staging cleanup. No deletion ran; source
files, prior completed ZIPs and the partial staging copy were left intact.

The exporter now supports an explicit `--external-output-dir` for a fresh absolute
destination outside the input project. Default exports remain confined to `dist/`;
existing external destinations and overlapping paths are rejected. A conservative
free-space preflight runs before export writes. Three focused tests pass for the
default boundary, external-path protections and low-space failure before staging.
The 428-test main-suite result predates this packaging-only extension; it is not
represented as a combined 431-test full-suite run.

The fresh copy-only export is directed to D:, which had available capacity.
No automatic upload or deployment is performed. The low free space on C: remains
a machine-storage issue; this task does not delete other project or personal files.
