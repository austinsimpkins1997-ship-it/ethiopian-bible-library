# English/narration verification — 2026-11-15

Status: local implementation and release checks passed. Publication and live
deployment are separate states; a local pass does not establish a live update.

## Final local release checks

- Full offline source-backed release rebuild: passed, including retained source
  checks and signature verification. Windows used a temporary short Q: alias for
  GPG's socket path; it was removed afterward. This is an environment workaround,
  not a changed source or relaxed check.
- Python suite: **412 tests run, 392 passed, 20 skipped**, zero failures/errors
  on the final run. Existing skip boundaries remain; skipped tests did not pass.
- All eight Node suites and eight JavaScript syntax checks: passed.
- Responsive Chromium checks: passed at 320, 390, 768 and 1440 pixels, including
  automatic opening, offline reload, existing 11 companion books and all 13
  non-English language groups' source/reference and English-only views.
- Browser regressions passed for missing English chapters, independently chosen
  English chapter 16 with source chapter 1, reference network failure, no hidden
  source-language narration in English-only view, no autoplay, navigation/stop
  cancellation and labeled machine-preview fixture/export exclusion.
- Version-2 comparison JSON validates against the published JSON Schema.
- Desktop/mobile reference screenshots were visually inspected. A duplicate
  observation label was removed; real-browser counts remain checked per witness.

Real-model and full-player observations are retained in the development checks
below. Native translation output, pronunciation accuracy and physical-device
performance remain unverified.

## Observed development checks

- Generated index: 759 packages, 123 already English, 636 non-English with
  existing English references, zero unmatched. All 81 reference packages are
  actual archived English readers; no title-only guesses are used.
- Node checks passed for English-reference selection/export, preview control
  flow, narrator cancellation/Microsoft exclusion and existing audio/package
  behavior. Preview tests use a fixture, not evidence of language accuracy.
- Real local Chrome module-worker generation produced 162,600 PCM samples at
  24,000 Hz (6.775 seconds) using Heart, with nonzero RMS 0.0722983. This proves
  one tested model path generated audio, not general quality or pronunciation.
- Full-player testing caught a native SpeechSynthesisVoice type error for the
  application's neural voice choice. Neural requests now bypass that typed
  native field; a regression test exercises the exact boundary.
- Retest in the actual reader succeeded: Heart generated a 652,200-sample
  buffer at 24,000 Hz (27.175 seconds), playback started and Stop returned the
  player to its ready state. Four narrator options were present and none was
  a Microsoft voice. This was real model inference with muted output, not a
  mocked speech engine. The earlier WAV sample was also made available for
  listening; no independent listening-quality assessment is claimed.
- Chrome reported Arabic-to-English Translator availability as downloadable;
  native model creation/translation was not run. Fixture tests cover UI flow.
- Browser testing caught English-only reference text being reopened by the
  legacy study-lens renderer. The selected view is now reapplied after that
  renderer; the browser check retains the English-only visibility assertion.
- A source chapter without a matching reference number remains explicit,
  rather than silently loading a different English chapter.
- JSON Schema validation caught the export schema omitting the archive's
  existing reviewed_match mapping label. The schema now accepts that actual
  vocabulary without relabeling it or upgrading research readers to canon
  coverage. A schema-vocabulary regression and version-2 export validation pass.

## Boundaries

No scholar, Church custodian or language community has reviewed these new UI
comparisons. Existing text/edition uncertainties remain. A book-family match
does not prove chapter/verse equivalence. Model download and device resources
can limit playback. Physical iOS/Android devices and assistive technologies
have not been tested in this run. Native Translator execution and translation
quality are unverified unless a separately recorded result says otherwise.

Mocked translation/narration tests verify application behavior; they do not
certify model accuracy. No numeric quality or universal compatibility score
is claimed.
