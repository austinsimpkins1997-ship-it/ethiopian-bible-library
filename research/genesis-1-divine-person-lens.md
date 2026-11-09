# Genesis 1: a first- and third-person lexical lens

## Result

This pilot counts features in the archive's English companion to Genesis, chapter 1. It does **not** count every grammatical reference to God, and it does not describe Geʽez wording.

| Lens | Count | Operational definition |
|---|---:|---|
| First-person self-reference inside words attributed to God | 3 | Exact English tokens: **I** (1), **us** (1), **our** (1). “Us” and “our” occur in 1:26; “I” occurs in 1:29. |
| Third-person narrator reference: noun “God” outside the selected speech excerpts | 33 | Case-insensitive whole-word occurrences outside the exact manually delimited speech excerpts. This is a lexical proxy for narrative reference, not a count of third-person pronouns or verbs. |
| Third-person narrator reference: subject pronoun “he” manually attributed to God | 5 | Five exact tokens in selected clauses: 1:5, 1:10, twice in 1:27, and 1:31. The object “him” in 1:27 refers to the human and is excluded. |
| Exact Geʽez divine-name string `እግዚአብሔር` in the source reader | 33 | Exact string occurrences across the 31 stored Geʽez verse texts. This is a lexical count, not a count of Geʽez grammatical person. |
| Second-person audience reference inside attributed speech | 2 | **you** occurs twice in 1:29, addressed to humans; it is not counted as God referring to God. |

The [machine-readable lens record](genesis-1-divine-person-lens.json) preserves each English speech excerpt, the lexical count rules, per-verse noun counts, and both chapter fingerprints. Version 2 ties every measurement to a named witness, language tag, source IDs, and a measured/unassessed state; an unassessed value is `null`, never zero. The [JSON Schema](../schemas/textual-lens.schema.json) defines this reusable record shape. Its builder and tests check that excerpts are exact substrings of the stored English witness. The assignment of those excerpts to God's speech remains an editorial judgment, marked unreviewed.

The noun and pronoun lenses are separate: 33 explicit noun occurrences of “God” in narrator text, and five manually attributed subject-pronoun tokens (“he”) in the selected clauses. The latter is not an exhaustive count of all third-person forms or references. The first-person count is a pronoun count in manually segmented divine speech, not a count of first-person verbs. These measurements use different units and should not be compared as equivalent totals.

## Scope and method

- **Text:** `genesis-english-brenton-lxx-1851`, embedded as the `parallel_translation` of `genesis-geez-dillmann-hacohen` in `archive.json`.
- **Edition and path:** Sir Lancelot Charles Lee Brenton's 1851 English translation from the Greek Septuagint (`grc → en`). It is a historical companion witness, not a direct translation from the bundled Geʽez transcription. Sources: [SRC-037](https://ebible.org/eng-Brenton/GEN01.htm) and [SRC-038](https://ebible.org/eng-Brenton/copyright.htm).
- **Extent:** the 31 verse texts in chapter 1. Footnote-marker text is retained in the source but does not affect the counted tokens.
- **Geʽez lexical check:** the exact string `እግዚአብሔር` occurs 33 times in the bundled Geʽez Genesis chapter 1, with the same per-verse distribution listed below. Its chapter-text fingerprint is SHA-256 `ad8cd109ae6241fc6330ee4762deca3d4187c89f2719d3887a5d3c315646abd7`. This coincidence does not prove word-for-word or translation equivalence: the Brenton companion was translated from Greek, while the other reader is a historical Geʽez transcription.
- **Attributed speech spans:** Genesis 1:3, 1:6, 1:9, 1:11, 1:14–15, 1:20, 1:22, 1:24, 1:26, 1:28, and 1:29–30. The JSON sidecar stores exact excerpts, separated manually from narrator lead-ins and narrative continuations. The builder verifies each excerpt against its stored verse but cannot independently verify the speaker assignment.
- **First-person tokens counted:** exact case-insensitive English tokens `I`, `me`, `my`, `mine`, `we`, `us`, `our`, and `ours` within those attributed speech portions. Result: 3: `us` + `our` in 1:26, and `I` in 1:29.
- **Third-person narrator-reference proxy:** exact whole-word `God`, case-insensitive, in all 31 stored verse texts after subtracting occurrences inside the exact selected speech excerpts. Result: 33; 0 noun occurrences fall inside those excerpts. This deliberately excludes pronouns such as `he` and `his`, whose antecedent requires clause-level interpretation. The narration label follows the editorial speech segmentation and is not independently reviewed.
- **Third-person pronoun reference:** five exact whole-word subject tokens `he`, in the manually selected phrases “he called Night” (1:5), “he called Seas” (1:10), “he made him” and “he made them” (1:27), and “he had made” (1:31). These clauses are attributed to God as grammatical subject; `him` in 1:27 refers to the human and is excluded. This antecedent assignment is editorial and not independently reviewed. No claim is made that this exhausts every possible third-person reference.
- **Text fingerprint:** SHA-256 `375764e1358a1715cc5a07786ce82537539dde432a1de8289a431cb4952e8f77` over the UTF-8 concatenation `verse-number: verse-text\n` for verses 1–31 in order.

### Occurrences of “God” by verse

`1:1, 2:1, 3:1, 4:2, 5:1, 6:1, 7:2, 8:2, 9:1, 10:2, 11:1, 12:1, 14:1, 16:1, 17:1, 18:1, 20:1, 21:2, 22:1, 24:1, 25:2, 26:1, 27:2, 28:1, 29:1, 31:1` (33 total). Verses not listed contain zero occurrences under this exact-word rule.

## Limits

This is a reproducible, narrowly scoped lexical count, not a theological interpretation, a count across Genesis, a translation-quality judgment, or a universal-language result. Different English translations can make different lexical choices; Geʽez needs a separate, language-specific morphology and speech-attribution method. Matching verse labels do not establish translation equivalence. No machine-generated wording is presented as scripture.

The English “us/our” tokens are counted as grammatical first-person forms only. This note does not decide what their plural means theologically. The Geʽez count does not claim that first-person morphology is absent; it remains uncounted pending a validated Geʽez morphological and speaker-attribution method.

For that next step, the relevant scholarly reference includes Aaron Michael Butts's chapter “Gǝʕǝz (Classical Ethiopic)” in the second edition of [*The Semitic Languages*](https://www.routledge.com/The-Semitic-Languages/Huehnergard-Pat-El/p/book/9780415731959) (Routledge, 2019). The chapter is identified bibliographically here as a research lead; its grammatical analysis has not yet been integrated or used to classify this chapter's Geʽez verbs.

See the [Geʽez morphology resource review](geez-morphology-resource-review.md) for two discovered analysis resources, their documented coverage, reported evaluation, and reuse limits.
