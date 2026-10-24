# Contributing texts, translations, and evidence

The archive welcomes source-backed additions. A book appearing in a canon list or catalogue is not evidence that its text has been obtained, verified, translated, or cleared for redistribution.

By contributing original metadata to the files listed in `DATA-LICENSE.md`, contributors agree to offer that metadata under CC BY 4.0, provided they have the rights needed to do so. Code contributions are offered under the repository's MIT license. Scripture and other third-party material require their own source-specific rights; a metadata contribution is not permission to reproduce a text.

## Before adding a text

1. Identify the tradition and the named canon list. Preserve that list's grouping and wording; record uncertain crosswalks as uncertain.
2. Identify a specific witness and edition. Cite the source page and retain a local source capture when reuse permits.
3. Check the full source for chapter order, boundaries, numbering, supplied text, missing sections, and editorial apparatus. Preserve source numbering and explain any mapping.
4. Confirm the content license from the underlying rights holder or edition, not merely a container repository's license. Include exact attribution and restrictions. A conflict blocks redistribution.
5. For translations, name the translator, source witness, edition/date, and method. Record `translation_path` as ordered BCP 47 language tags from source through any relay languages to output; use `null` when the path is unknown. Never label a relay translation as direct.
6. Mark machine-generated output as a draft. It is not a verified translation until reviewed against the source by qualified language readers, with revision notes and approval recorded.
7. Add language/script metadata using BCP 47 language tags and ISO 15924 script codes when known. Keep original forms and community-preferred names. Record `direction` as `ltr`, `rtl`, or `unknown`; use `writing_mode` separately for an evidenced horizontal or vertical layout. Do not infer either from the script code.
8. Add a bundled text to the appropriate reader JSON and add its layer metadata to `translation-registry.json` and `examples/`. Add or correct its sources in `archive.json`, update `CONTENT-LICENSES.md`, and preserve any required notice with the text package. Update the canon coverage record only when evidence supports the exact mapping.

## Build and validation

Run the builders needed for the files you changed, then run `python build_standalone.py` from the `site` directory. This validates the archive's required metadata, source references and local source paths, reader structure and counts, selected layer-package checksums, language paths, and canon coverage before regenerating the offline `index.html` and `examples/portable-text-layers.json`. It is a project-specific integrity check, not a complete JSON Schema validator or scholarly review.

The GitHub Pages workflow runs the standalone build and fails if generated files are stale. Commit regenerated `archive.json`, `index.html`, and `examples/portable-text-layers.json` with the corresponding source changes. From the repository root, `python build_archive.py` also syncs the parent project's catalogue exports; those exports are not part of the Pages site repository.

## Review status vocabulary

- `candidate`: source lead only; text not admitted to the reader.
- `transcribed`: text copied from an identified source; completeness and correctness review pending.
- `source_checked`: source identity and structural coverage checked; not necessarily collated to manuscripts.
- `translated_draft`: translation exists but awaits qualified review.
- `translation_reviewed`: named reviewer(s) compared the translation with the specified source and recorded limits.
- `bundled`: the exact locally stored text is included in the offline build; this status alone does not claim critical-edition accuracy.

Every claim should point to evidence. Unknown values should remain explicit unknowns; do not fill gaps by guessing or silently substituting a more familiar canon or translation. Passing the build checks does not establish textual accuracy, completeness, translation equivalence, community approval, or legal permission beyond the cited terms.
