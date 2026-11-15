# Local release verification — 2026-11-15

- Complete ordered source rebuild: passed. Current public snapshot: 759 readers,
  451 sources and 28 language profiles.
- Python: 399 tests run in 102.933 seconds; 379 passed, 20 intentionally skipped
  because the mixed-rights scripture/source XML is absent from the public tree.
- Post-test package integrity: passed; the tests left the 2,198-file public
  inventory unchanged before this verification record was added.
- Three JavaScript suites passed: reader export, offline cache, service worker.
  Syntax checks also passed for the app, export, cache and service-worker code.
- Real Chromium automation at a GitHub Pages-style subpath passed at 320, 390,
  768 and 1440 pixels. Checked English/parallel reading, chapter navigation,
  language view, search, JSON export and offline reload. No horizontal overflow
  or page errors were recorded in those checks.
- Separate mobile touch emulation confirmed Arabic Genesis uses `lang=arb` and
  `dir=rtl`, with no overflow at 390 pixels. The keyboard skip link is reachable.
- Authored HTML link audit: 28 pages, zero unresolved local file links. Captured
  historical HTML, external websites and semantic identifiers are outside this
  check's scope.
- Ruth source registration regression checks preserve rights enrichment while
  rejecting conflicting source fields. Restored captures retain their original
  pinned digests. The rebuild now keeps the source-reported verse-numbering
  method (SRC-035), rather than replacing it with a page-pagination claim.
- Remote main was rechecked and remains the original failing commit
  `253bfa4da3f41949803da5743d18f821712e2d39`.

See `release-verification.json` for structured results. Package-specific file
counts, sizes and SHA-256 are generated separately in `dist/release-checksums.json`.

These are local implementation and integrity checks. Hosted CI/deployment,
physical devices, Safari, Firefox and assistive technologies remain untested.
Checksums and structural tests do not establish scholarly accuracy, canon or
edition equivalence, completeness, or worldwide redistribution rights.
