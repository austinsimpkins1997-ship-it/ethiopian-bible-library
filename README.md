# Ethiopian Bible Library site

Static, mobile-first archive. It uses only local HTML, CSS, JavaScript, and archive data embedded in `index.html`. Browsing makes no network requests: no API, external data feed, analytics, account, CDN, or third-party font. Source links are provided for readers who choose to open them and require internet access. The related texts section keeps the Ugaritic Baal Cycle, 11Q11, Pistis Sophia, the Testament of Solomon, and Psalms of Solomon distinct from the canon catalogue.

## Run locally

Open `index.html` directly in a browser. The archive data is embedded, so the catalogue also works from a `file://` address without a local server. For optional local development, run:

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`. The server is optional; the archive is embedded in `index.html`, so it also works directly from a `file://` address.

## GitHub Pages

The `pages.yml` workflow deploys the contents of this folder when pushed to the `main` branch. For a dedicated repository, copy the contents of this folder to the repository root. In repository Settings → Pages, select **GitHub Actions** as the publishing source. GitHub Pages provides the public site URL after the first successful workflow run.

For a ready-to-upload archive and browser upload steps, see `UPLOAD_TO_GITHUB.md`.

## Important content boundary

The site stores its catalogue locally and cites itself only as the record custodian; self-citation is not independent evidence. It displays 89 searchable research rows, not 89 canonical books. The Ethiopian Orthodox Tewahedo Church’s English canon page states 81 books (46 Old Testament, 35 New Testament) and groups some titles. The row-to-canon mappings, Ethiopic witnesses, editions, translations, chapter boundaries, text availability, completeness, and reuse rights remain unverified unless a record explicitly says otherwise. Evidence links are leads and context, not a certification of each row. The archive makes no claim to omniscience; if knowledge is understood as a gift from God, the editorial response here is humility: name witnesses, distinguish evidence from interpretation, and keep unresolved claims open to correction. Build readers only after verifying text and boundaries; clear reuse rights before publication and add narration only after text, boundaries, and audio rights are verified.

### Source safety

An overview-PDF link was withdrawn after browser protection flagged its hosting URL as a phishing risk. The PDF was not opened, so this is not a claim that its contents are malicious. The Church’s own published canon list remains cited as the primary source for its stated 81-book count.

## Updating the archive

`archive.json` is the editable source of truth. After changing it, run `python build_standalone.py` to validate catalogue IDs and source references and embed the updated data into `index.html`. The generated site works offline. No data is fetched from external sites; outbound source links open only when a reader chooses them.

