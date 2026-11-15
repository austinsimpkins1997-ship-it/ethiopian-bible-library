# Deployment repair — 2026-11-15

## Observed failure

GitHub Actions [run 43759850338](https://github.com/austinsimpkins1997-ship-it/ethiopian-bible-library/actions/runs/43759850338), commit `71fa47d864350bd367d63e5c0e26f4d20fd99c56`, passed the ordered rebuild, checksum verification, Python tests, JavaScript suites and Chromium checks. The final committed-output check found only `archive-manifest.json` changed; deployment was skipped.

## Cause and change

`build_manifest()` sorted native `Path` objects. Windows compares paths without case sensitivity; Linux uses case-sensitive ordering. The committed 2,201-entry manifest matched Windows ordering and differed from Linux ordering. Rebuilding the same inventory therefore changed the serialized manifest.

The generator now sorts each relative `as_posix()` spelling explicitly. This defines one order on both platforms without normalizing or changing retained source bytes. The stale-output failure, checksum verification, source-signature checks, and deployment prerequisites remain enforced.

Added mixed-case/Unicode and directory-enumeration regression tests. The mixed-case test failed against the original code on Windows and passed after the fix.

## Verification and limits

Local verification recorded at `2026-11-15T16:15:03-05:00` (America/New_York):

- Complete ordered rebuild: passed; 2,203 package files verified.
- Python suite: 406 tests in 140.013 seconds, 386 passed and 20 intentionally skipped because withheld mixed-rights source text is absent from the public package.
- Three JavaScript suites and app/cache/service-worker syntax checks: passed.
- Fresh headless Chrome checks at 320, 390, 768 and 1440 pixels: passed. English and parallel reading, chapter navigation, language view, search, JSON export and offline reload were checked; no overflow or page errors were recorded.
- Compared with the baseline manifest: 2,199 existing records unchanged, no removals, two changed file records (generator and README), and two additions (this repair record and the regression tests). Source captures and reader text are unchanged.
- The workflow file is unchanged, including its strict stale-output failure.

Hosted Linux CI is pending at commit preparation. Its result belongs to the associated pull request/check run; local Windows results do not establish hosted success. The prior commit's successful Linux browser run is separate historical evidence.

An initial full-suite attempt exposed an unresolved drive alias in the new enumeration test fixture. The fixture now resolves its root as the production generator does; the complete suite above was rerun after that correction.

A local validation attempt with a long project-local temporary path exposed GnuPG's socket-path limit. The recovery uses a temporary short drive alias pointing to the same app-owned `tmp` directory, removed after the command. This is an environment workaround, not a change to signature validation or its trust assumptions.

## Recovery

The pre-repair baseline is commit `71fa47d864350bd367d63e5c0e26f4d20fd99c56`. Keep previous exports in `dist/`; stage repaired exports into a new directory. If this repair must be reversed, review a normal revert and regenerate its manifest; do not disable validation to force publication.
