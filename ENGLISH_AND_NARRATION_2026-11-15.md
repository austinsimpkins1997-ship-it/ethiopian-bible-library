# English references and natural narration — 2026-11-15

## Scope and reader behavior

This extends merged reader-first baseline 5933f6465d5bc30843a7112040b6c087fd202f8b.
The generated index accounts for all 759 current public reader packages:

| Current package state | Count |
|---|---:|
| Already English | 123 |
| Non-English with a sourced English reference | 636 |
| Non-English without a reference | 0 |
| Existing WEB British English reference books | 81 |

These counts cover the **currently bundled packages**, not all books in every
Church list or every absent/withheld source. No source Scripture was downloaded,
rewritten, machine-translated into the archive, or newly canon-linked.

The English reference is the existing World English Bible (British) edition,
resolved from retained publisher book codes or an explicit historical work-family
table. It helps readers consult English alongside another witness. It does not
translate the exact Geʽez/other-language wording, certify equivalent contents,
or establish verse/chapter alignment. Full original rights and evidence remain.

Existing 11 Brenton companions and their 400 chapter pairs retain their own
separate parallel view. Other non-English packages open original + English
reference by default. Source and reference chapters have independent selectors;
matching chapter numbers are navigation aids only. If a number has no reference
chapter (for example, historical Joel chapter 4 versus the reference's three
chapters), the reader reports it instead of substituting chapter 1.

English reference exports use reader-package schema version 2, preserving both
editions, evidence and their separate canon/research mappings. Existing exports
remain version 1. English-only reference view does not display the original
text column, but the original package and metadata remain accessible.

## Optional machine study preview

The user selected sourced English first, with labeled machine previews where
supported. A separate, explicit button uses Chrome's on-device Translator API
only when present and when the recorded text terms permit derivative work.
Unsupported languages/browsers show an unavailable explanation. Geʽez support
is not claimed. No secret API key, translation proxy or server upload is used.

A preview is labeled **unreviewed machine-generated study text** and may be
wrong. It preserves source-unit order, is limited to 250 units/60,000 characters
per selected chapter, and is discarded on context change/reload. It is not
saved into the archive, offered as reviewed Scripture or included in exports.
Limited/unknown rights and non-derivative licenses do not enable generation.
An English reference is a separate sourced edition; a preview is a generated
attempt at the selected wording. The UI keeps that distinction visible.

## Voices

Four on-device Kokoro English narrators replace the default speech choices:
Heart (default), Bella, Emma and George. Microsoft/SAPI voices are excluded.
The default rate is 0.95. Visitors choose Play; opening a chapter never starts
sound. The first preparation downloads about 93 MB of weights plus supporting
files. Text is processed locally; third-party CDNs serve code/model resources.
Other languages need a matching non-Microsoft local device voice.

These are synthetic voices, not licensed human recordings or a guarantee of
pronunciation/translation quality. Devices with insufficient resources may
need to keep reading the written text. The model does not enter public ZIPs.
See [resource versions and licenses](assets/narrator/README.md).

## Requested resources and implementation choices

- [Public APIs](https://github.com/public-apis/public-apis) was reviewed for
  discovery. Existing source-backed English avoids a runtime Bible API,
  paid credentials, text uploads and unverified edition substitutions.
- [Lucide](https://lucide.dev/icons/languages) provides the decorative languages
  icon, with its ISC license and source attribution retained locally.
- [Adabraka UI](https://github.com/Augani/adabraka-ui) targets Rust/GPUI desktop
  applications. This static browser site instead uses native labeled controls
  and responsive CSS, without an incompatible framework dependency.
- [Chrome Translator documentation](https://developer.chrome.com/docs/ai/translator-api)
  defines capability detection, explicit model creation, progress and cleanup.
- [Kokoro JS documentation](https://github.com/hexgrad/kokoro/tree/main/kokoro.js)
  and the [voice descriptions](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
  informed the synthetic narrator integration.

## Verification

Coverage and schema checks, cancellation/voice filtering tests, and responsive
browser tests distinguish mocked control-flow checks from actual model execution.
Results and remaining limits are recorded in
[ENGLISH_NARRATION_VERIFICATION_2026-11-15.md](ENGLISH_NARRATION_VERIFICATION_2026-11-15.md).
