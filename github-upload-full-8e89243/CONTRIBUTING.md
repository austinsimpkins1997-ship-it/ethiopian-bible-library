# Contributing texts, translations, and evidence

The archive welcomes source-backed additions. A book appearing in a canon list or catalogue is not evidence that its text has been obtained, verified, translated, or cleared for redistribution.

By contributing original metadata to the files listed in `DATA-LICENSE.md`, contributors agree to offer that metadata under CC BY 4.0, provided they have the rights needed to do so. Code contributions are offered under the repository's MIT license. Scripture and other third-party material require their own source-specific rights; a metadata contribution is not permission to reproduce a text.

## Before adding a text

1. Identify the tradition and the named canon list. Preserve that list's grouping and wording; record uncertain crosswalks as uncertain.
2. Identify a specific witness and edition. Cite the source page and retain a local source capture when reuse permits.
   If a specific book-level source edition has been identified but is not available as a checked local reader, add a metadata-only `edition_leads` record to `translation-registry.json`. Use `candidate_canon_id` with an explicit `mapping_state`; do not turn a bibliographic title, repository scan, or candidate crosswalk into bundled coverage. Keep source editions separate from translation leads and multi-book corpus leads.
3. Check the full source for chapter order, boundaries, numbering, supplied text, missing sections, and editorial apparatus. Preserve source numbering and explain any mapping.
4. Confirm the content license from the underlying rights holder or edition, not merely a container repository's license. Include exact attribution and restrictions. A conflict blocks redistribution.
   Every bundled layer and unbundled lead must carry a controlled `rights_classification`: `public_domain_claimed`, `open_license`, `permission_limited`, `all_rights_reserved`, `unknown`, or `mixed`. Keep the source-specific legal notice separately in `rights_status`; the category is only a navigation aid, not a legal conclusion. A bundled text layer must carry source-linked rights evidence and a redistributable status (`public_domain_claimed`, `open_license`, or `permission_limited` under the recorded conditions); unknown or mixed rights stay metadata-only. An `open_license` claim must name the license. This build check validates the recorded evidence links, not the legal conclusion itself.
5. For translations, name the translator, source witness, edition/date, and method when the evidence supports them. Attribute a named agent only when the source ties that person or organization to a role in this specific text layer; cite the evidence. An empty `agents` list is valid when file-level credits cannot be mapped to the selected layer. Record `translation_path` as ordered BCP 47 language tags from source through any relay languages to output; use `null` when the path is unknown. Never label a relay translation as direct.
6. Record `review_method` separately from `reviewer`: automated validation is not a person, and automated checks cannot use the `reviewed` state. A fully reviewed status requires a named human reviewer and date. Mark machine-generated output as a draft. It is not a verified translation until reviewed against the source by qualified language readers, with revision notes and approval recorded.
   Report the observed count and its scope; never rewrite a source count to match an expected count. Set each language profile's `availability_survey.status` explicitly. Use `none_found` and a zero result count only for a completed, bounded, dated search with cited source IDs. Keep unassessed availability `not_surveyed`, and unresolved perspectives, boundaries, and wording marked unknown; never promote machine output to verified scripture.
   In portable text-layer records, a `coverage.unit_count` of `0` therefore requires a non-unknown extent, a `source_inventory` or `independent_collation` basis, and a nonempty `structure_description` naming the bounded scope surveyed. Use `null` when the count or surveyed scope is not established.
7. Add language/script metadata using BCP 47 language tags and ISO 15924 script codes when known. Keep original forms and community-preferred names. Record `direction` as `ltr`, `rtl`, or `unknown`; use `writing_mode` separately for an evidenced horizontal or vertical layout. Do not infer either from the script code.
8. Add a bundled text to the appropriate reader JSON and give the reader record a controlled `rights_classification` that matches its bundled registry layer; do the same for each parallel translation. Keep exact source notices with the text. Add the layer metadata to `translation-registry.json` and `examples/`, update source citations and `CONTENT-LICENSES.md`, and update the canon coverage record only when evidence supports the exact mapping. The build rejects rights-category mismatches between bundled reader data and its registry record.

## Build and validation

Run the builders needed for the files you changed, then run `python build_standalone.py` from the `site` directory. This validates the archive's required metadata, source references and local source paths, reader structure and counts, portable layer records' required nested witness, coverage, rights, and review fields, local package checksums and explicit nested JSON Pointer selectors, language paths, language-layer-to-reader canon crosswalks, metadata-only source-edition lead identities/rights/candidate mappings, canon coverage, and the local offline-shell cache list before regenerating the offline `index.html`, `examples/portable-text-layers.json`, and `archive-manifest.json`. The translation registry JSON Schema is version 2. The builder is a project-specific integrity check, not a complete JSON Schema validator, full browser/offline runtime test, or scholarly review. Run `python -m unittest discover -s tests -v` for coverage-state regression cases, then `python verify_archive_manifest.py` to independently check the package-file inventory, lengths, and SHA-256 values against the generated manifest.

The GitHub Pages workflow runs the standalone build and fails if generated files are stale. Commit regenerated `archive.json`, `index.html`, `examples/portable-text-layers.json`, and `archive-manifest.json` with the corresponding source changes. From the repository root, `python build_archive.py` also syncs the parent project's catalogue exports; those exports are not part of the Pages site repository.

## Review status vocabulary

- `candidate`: source lead only; text not admitted to the reader.
- `transcribed`: text copied from an identified source; completeness and correctness review pending.
- `source_checked`: source identity and structural coverage checked; not necessarily collated to manuscripts.
- `translated_draft`: translation exists but awaits qualified review.
- `translation_reviewed`: named reviewer(s) compared the translation with the specified source and recorded limits.
- `bundled`: the exact locally stored text is included in the offline build; this status alone does not claim critical-edition accuracy.

Every claim should point to evidence. Unknown values should remain explicit unknowns; do not fill gaps by guessing or silently substituting a more familiar canon or translation. Passing the build checks does not establish textual accuracy, completeness, translation equivalence, community approval, or legal permission beyond the cited terms.

## Propose a source or text layer

Use the [source, translation, or evidence proposal form](https://github.com/austinsimpkins1997-ship-it/ethiopian-bible-library/issues/new?template=source-or-translation-proposal.md) to submit a candidate or correction. It asks for edition identity, measured scope, language/script evidence, rights, and review limits. “Unknown” is acceptable and should remain explicit. Keep submissions metadata-only when rights or extent are unresolved; do not attach full text or scans to an issue.
