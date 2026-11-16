# Readable Scripture and USFM word metadata — 2026-11-15

## What the screenshot showed

The reported passage is Revelation 1:11. Strings such as
`What|strong="G3739"` are USFM word-level study attributes, not the words
of the English translation. Strong's IDs identify lexicon entries; G labels
Greek entries and H labels Hebrew entries.

The retained source uses nested word spans inside character formatting:
`\wj “\+w What|strong="G3739"\+w* ...”\wj*`.
The shared parser handled ordinary word spans first, then removed generic
nested wrappers. That order left the nested spans' attributes in readable text.
The English comparison pane, narration and exports correctly consumed that
reader field, so they inherited the extraction error.

## Correction

- Handle both ordinary and opted-in nested word spans before generic formatting
  removal; retain their words and punctuation, excluding their study attributes.
- Carry the generic nested-format option through heading/structural notes.
  This also removes leftover nested formatting wrappers in those notes.
- Reject leftover word-attribute syntax and unsupported nested markers in
  generic extraction rather than silently publishing them as Scripture.
- Rebuild the derived reader packages, aggregate archive, graph hashes and
  package checksums from the unchanged, pinned local sources.
- Advance the service-worker shell to v48 so updated online visits refresh
  the reader assets. A page already holding old text needs a reload.

The exact tagged source remains in the original ZIP for study and audit.
This is a parsing/display correction, not a new translation, a correction of
the source's words, or a certification of the edition's textual accuracy.

## Evidence and checks

A recursive check of the baseline commit's current reader chapter fields found
2,117 strings containing named word attributes, across 11 English reader
packages. The same bounded check of the rebuilt 759-reader archive finds none.
These are text-field counts, not a claim about every possible USFM construct.

The source-based regression checks the exact Revelation 1:11 sentence:

> saying, “What you see, write in a book and send to the seven assemblies: to Ephesus, Smyrna, Pergamum, Thyatira, Sardis, Philadelphia, and to Laodicea.”

It separately retains the two verse-11 textual notes (including the Alpha and
Omega variant). All 81 WEBBE modules are checked for leaked attributes in
chapters and front matter; their 1,402 chapter divisions and 38,058 verse labels
remain unchanged. Read-aloud/export tests check the derived text, and a real
browser checks the English comparison pane for the reported passage.

Earlier inventory, checksum and structural tests did not test this nested
word-tag rendering failure. The screenshot exposed that missing check.
Regression tests now exercise that actual example and nearby nested/ordinary
word cases; broad language/translation accuracy remains outside these checks.

Final local verification: full offline release rebuild passed; 414 Python tests
ran (394 passed, 20 skipped); all eight Node suites passed; Chromium checks
passed at 320, 390, 768 and 1440 pixels, including the corrected Revelation
comparison pane. The cleaned passage was visually inspected. Existing source
hashes and text-unit counts remain checked; skipped tests are not reported as
passes. GitHub publication, hosted checks and live deployment are separate states.

References: [current USFM word marker](https://docs.usfm.bible/usfm/latest/char/features/w.html)
and [USFM 3 word-level attributes](https://ubsicap.github.io/usfm/attributes/index.html).
