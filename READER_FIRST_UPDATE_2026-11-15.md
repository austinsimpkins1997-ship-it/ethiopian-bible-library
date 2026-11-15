# Reader-first layout and device read-aloud — 2026-11-15

## Purpose and verified scope

Austin requested a warmer, less cluttered website, with Scripture closer to the
top, the selected text open automatically, parallel reading selected where
available, and visible spoken-audio controls for the selected language.
The implementation is based on main revision `55482cd`; source editions,
retained captures, rights boundaries and Scripture wording are unchanged.

## What changed

- A compact welcome, warm paper colors, clay accents and a quiet book illustration
  lead directly to the reader. In the 1440-pixel local browser check, the reader
  section begins within 500 pixels of the top, before the catalogue.
- Read & listen, Browse books, Research and About links open their destination.
  Seven secondary sections start collapsed; source/catalogue cards are rendered
  when needed. Sources, edition differences, rights, downloads, offline preparation
  and study lenses remain accessible through labeled disclosures.
- Opening the page loads one selected same-site reader JSON package, rather than
  all 759 packages. A reader link opens its selected book; new paired selections
  start in parallel view. An explicit reading-view choice is retained per book
  during that page session.
- Play, Pause/Resume and Stop are visible. Text opens automatically; sound waits
  for Play. Resume restarts the current short passage. Chapter/book/view changes
  stop playback, invalidate late speech callbacks, and refresh the selected text.
- Speech uses the selected text's language and only an installed voice reporting
  `localService: true`. In parallel view English is the initial spoken side, with
  the other available text side selectable under Voice & speed. Single-language
  view follows that language. No missing translation is generated and no English
  voice is substituted for Geʽez or another unsupported language.
- Spoken content consists of stored verse/source-unit text and its unnumbered
  continuations, in order. Footnotes and study commentary are excluded. Short
  passages limit loss on pause; the page never needs microphone access.
- The offline shell includes the new stylesheet and audio module. Previously
  visited text remains available through the existing on-demand cache. Installed
  local-voice availability is a separate device requirement.

## How many books have parallel reading?

**11 books, covering 400 source/companion chapter pairs:**

| Book | Chapter pairs |
|---|---:|
| Genesis | 50 |
| Exodus | 40 |
| Leviticus | 27 |
| Numbers | 36 |
| Deuteronomy | 34 |
| Joshua | 24 |
| Judges | 21 |
| Ruth | 4 |
| Psalms | 151 |
| Amos | 9 |
| Joel | 4 |

`tests/test_parallel_coverage.js` checks every chapter pair, retains every source
unit and companion verse exactly once, preserves source order, and refuses
ambiguous label matches. All chapters have nonempty companion text. Ruth and
Amos have every printed label structurally paired; the other nine retain gaps
or unmatched labels visibly. These are technical display checks, not proof of
textual equivalence, complete translation alignment, collation or accuracy.
The English historical companions are distinct editions; they are not generated
translations from the displayed Geʽez. The other 748 reader packages do not
acquire parallel companions through this UI change.

Read-aloud controls are shared across available reader texts, conditional on a
matching device voice. **No recorded narration corpus is added.** No claim is
made that all languages or devices can speak these texts, or that pronunciation
has been reviewed by qualified language readers.

## Verification and repaired mismatches

- Real Chrome checks at 320, 390, 768 and 1440 pixels passed: automatic opening,
  default parallel display, visible audio controls, collapsed sections, English
  view, chapter navigation, study lens, JSON export, search and offline reload.
  No horizontal overflow or observed browser errors in those flows.
- A separate homepage check passed the reader placement and disclosure navigation
  checks. Desktop and narrow-phone screenshots were visually inspected.
- Browser speech-engine fixtures exercised no autoplay, selected English text,
  pause/resume, cancellation on navigation, ignored stale callbacks, unsupported
  Geʽez messaging, and first/last chapter controls for all 11 parallel books.
  These fixtures verify wiring, not audible pronunciation or device coverage.
- Audio unit checks passed local-only matching, language aliases, chunking,
  preserved continuations, notes exclusion, async voice discovery, error handling
  and a selected Amharic text/voice fixture.
- A muted native Chrome/Windows speech probe discovered three local `en-US`
  voices (Microsoft David, Mark and Zira). The selected English voice emitted
  both start and end events for one short Scripture sentence. This checks the
  native engine lifecycle; it is not a listening or pronunciation review.
- The hash-navigation check initially exposed an unrelated notes panel opening
  at `#reader`. Navigation now unfolds only named section disclosures.
- A main-view switch initially retained an automatic Geʽez speech selection when
  returning to parallel. Only explicit audio-language preferences now persist;
  the regression fixture verifies the English default otherwise.
- Early browser runs stalled without a bounded failure report. The test now has
  explicit default timeouts and bounded service-worker readiness diagnostics.
  The successful final run does not establish one definitive cause for those
  earlier stalls; no product failure was inferred from the stall alone.

The first full suite caught a removed structural-count disclaimer and a README
command list missing the two new CI checks. The disclaimer was restored inside
the reader's optional notes, and the instructions now match CI. Both affected
suites passed before the complete suite was repeated.

Final local checks on Windows, Python 3.14.7, Node 24.20.0 and installed Chrome:

| Check | Observed result |
|---|---|
| Ordered offline `build_release.py` | Passed; 759 reader packages, 451 source records, no source/reader-content changes in the final diff |
| Complete Python suite | 408 cases run in 132.149 seconds: 388 passed, 20 existing skips |
| Reader export, audio, parallel coverage, offline-cache and service-worker Node suites | All five passed |
| Responsive/offline/browser speech-fixture checks | Passed at all four widths and across all 11 parallel books |
| Native muted English speech event probe | Start and end observed; three matching local voices discovered |
| Source syntax and Git whitespace checks | Passed |

The skipped cases and untested pronunciation/device combinations are not passes.
Local logs, detailed coverage data and screenshots remain in ignored `tmp/`.
Earlier deployment evidence remains in `DEPLOYMENT_FIX_2026-11-15.md` and is not
overwritten. Publishing a branch or opening a pull request does not update the
live site; merge and a successful Pages deployment are separate action states.

## Resources, licenses and limitations

This work follows the shared AGENTS.md scope, evidence, repair and reassessment
workflow. Native HTML disclosures, the existing offline reader and Web Speech
were sufficient; no new AI service or paid API is required. The resource-list
Lucide play icon is retained with its official source and license under
`assets/lucide/`; native controls retain their text labels. No external fonts,
tracking or remote speech endpoint are added by this change.

- [MDN: speech synthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)
- [MDN: available voices](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/getVoices)
- [MDN: localService flag](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService)
- [MDN: utterance configuration](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisUtterance)
- [Lucide play icon](https://lucide.dev/icons/play) and [license](https://lucide.dev/license)

The browser exposes whether a voice is local; this is not an independent audit
of the operating system or its provider. The page avoids selecting network
voices. Browser support, voice installation, language quality and operating
system behavior vary. Local tests do not certify all devices or assistive
technologies. Scripture and translation rights remain item-specific and separate
from the software's license. No new text acquisition or scholarly research is
represented by this interface update.
