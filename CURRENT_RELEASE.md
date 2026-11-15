# Release preparation — 2026-11-15

This is the canonical public project root. Start with `index.html` through
`START_LOCAL.bat`, or serve this folder over localhost/HTTPS. A `file://` copy
cannot fetch the separate reader JSON packages.

## What this release includes

The reader-first layout and device read-aloud update are documented in
[READER_FIRST_UPDATE_2026-11-15.md](READER_FIRST_UPDATE_2026-11-15.md).
It adds automatic text opening, default parallel display where supported, a
warmer responsive layout and optional matching-language local speech synthesis.
It does not add recorded narration or new Scripture translations.

The rebuilt inventory has 759 reader packages (19 canon-linked and 740 separately
scoped research readers), 451 source records, 28 language profiles, 90 catalogue
rows and nine related-work records. Nineteen of the cited 81 Church-list entries
have canon-linked readers; this is not a complete Ethiopian Orthodox Bible.
Title candidates, historical translations and edition identity remain distinct.
Forty-two mixed-rights Beta scripture readers remain withheld.

The baseline is remote main commit `253bfa4da3f41949803da5743d18f821712e2d39`
from November 9. It was compared with the older local `MasterArchive/site`
snapshot (227 readers, 345 sources). The older snapshot's four absent readers
are within the existing rights-withheld boundary; their metadata is retained.
No new scholarly collation, current-edition certification or exhaustive online
survey is claimed. Source capture dates remain as recorded.

## Why GitHub failed and what changed

The failed validation run was
[42546402064](https://github.com/austinsimpkins1997-ship-it/ethiopian-bible-library/actions/runs/42546402064).
`build_brenton_ruth.py` compared whole source dictionaries. Rights review had
added three fields to SRC-095, so an otherwise identical source was rejected.
The builder now checks its incoming fields, preserves enrichment, and rejects
genuine conflicts. Regression tests cover both cases and repeated registration.

Other discovered release blockers were repaired:

- Restored newline-damaged captures against their existing pinned SHA-256.
  Two mixed-newline Oromo metadata captures were recovered from matching local
  originals. Source digests were not replaced to make altered captures pass.
- Disabled Git normalization for retained captures; generated text uses LF on
  Windows and Linux. Leviticus byte and normalization checks fail closed again.
- Fixed the GPG verification argument list, Windows MSYS paths, key-import error
  handling and temporary-path length. The retained Maale signature verifies;
  its legacy algorithms and key-identity limits remain documented.
- Added one ordered, offline `build_release.py` entry point and an explicit
  release date, avoiding calendar-driven rebuild drift.
- Reconciled the illustrative Genesis graph checksum with the rebuilt English
  package. Updated stale tests for current records and source-basis wording.
- Fixed long citation/card overflow and tablet navigation. Bumped the offline
  shell version and added real-browser reading/offline tests to CI.
- Excluded private preservation captures, old upload copies, generated ZIPs and
  caches from the public inventory. Old delivery copies remain locally; this
  branch removes them from Git tracking. This does not erase Git history.
- Fixed repeated rights notices and whitespace growth when later catalogue notes follow them; a second complete build leaves every public file unchanged.
- Replaced the obsolete packaging assumptions with manifest-verified source and
  website exports. The copy helper uses that manifest rather than copying an
  entire working directory recursively.

## Build, test and package

Requirements: Python 3.13+; Node 24; GnuPG. On Windows, Git for Windows supplies
the supported Bash/GPG route. Run `npm ci --ignore-scripts --no-audit --no-fund`
and `npx playwright install chromium` before the browser test. Linux CI installs
the browser's OS dependencies with `--with-deps`.

Run the matching rebuild/check commands in README.md. `run_tests.py` runs the
whole Python suite with cross-platform output bytes. `tests/browser_smoke.cjs`
serves the site at a GitHub Pages-style subpath and checks 320, 390, 768 and
1440-pixel viewports, English/parallel text, chapter navigation, language view,
search, reader export and offline reload. These are browser tests, not testing
of every physical phone, browser or assistive technology.

After verification, run `python -B build_upload_package.py`. It creates:

- `dist/EthiopianBibleLibrary_GitHub_Source.zip` — canonical source, tests,
  research and workflow; no Git metadata or private preservation directory.
- `dist/EthiopianBibleLibrary_Website.zip` and `dist/site/` — static public site
  and reader/evidence assets, with their own checksum manifest.
- `dist/release-checksums.json` — package SHA-256, byte lengths and file counts.

Exports require a fresh directory. Use `--output-dir dist/release-next` to retain
an older export. `--site-only` stages a fresh `dist/site` for Pages. The workflow
validates first, then deploys only that staged site. Checksums establish byte
integrity, not textual accuracy or rights clearance.

Local test results are recorded in [VERIFICATION_2026-11-15.md](VERIFICATION_2026-11-15.md) and `release-verification.json`.

## GitHub handoff

Review the prepared branch `codex/github-release-2026-11-15`. Use Git or GitHub
Desktop; the full archive exceeds GitHub's browser uploader per-file limit.
Keep the project at the repository root. Local packaging does not push, merge
or deploy. The hosted Actions run still needs to pass after publication.

## Next substantial steps, in order

1. Publish and observe a green hosted validation/deployment, then check the real
   Pages URL on iOS Safari, Android Chrome, Firefox and assistive technology.
2. Recruit Ethiopian/Eritrean Church and Geʽez-language reviewers. Collate a
   small, named edition/book against its source, document disagreements, and
   expand only after a review protocol is demonstrated.
3. Resolve source-specific reuse and cultural-access questions with custodians.
   Prioritize the withheld 42 records and high-value gaps; permission for one
   edition or layer is not permission for the whole tradition or website.
4. Expand the 13 Church-list entries with neither a local reader nor a research
   candidate, while preserving the distinction between historical witness,
   title match and current Church edition.
5. Reduce initial metadata payload for slow devices and move large versioned
   data to a measured release strategy. Keep offline exports, provenance and
   update integrity intact. Measure before claiming a speed improvement.
