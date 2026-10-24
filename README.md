# Ethiopian Bible Library site

Static, mobile-first catalogue site. It uses only HTML, CSS, JavaScript, and the adjacent `archive.json`; no user account or external service is required to browse. Fonts use system fallbacks, and the site makes no third-party font requests. The related texts section includes the Ugaritic Baal Cycle, 11Q11, Pistis Sophia, the Testament of Solomon, and Psalms of Solomon, clearly separated from the canon list.

## Run locally

Open a terminal in this directory and run a local static server, for example:

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`. A local server is needed because the browser fetches `archive.json`.

## GitHub Pages

The `pages.yml` workflow deploys the contents of this folder when pushed to the `main` branch. For a dedicated repository, copy the contents of this folder to the repository root. In repository Settings → Pages, select **GitHub Actions** as the publishing source. GitHub Pages provides the public site URL after the first successful workflow run.

For a ready-to-upload archive and browser upload steps, see `UPLOAD_TO_GITHUB.md`.

## Important content boundary

The site currently displays a preliminary catalogue and source register, not scripture text. Catalogue records are not equivalent to verified texts. Do not add text until its edition, translation, chapter sequence, completeness, provenance, and rights have been checked. Current canon counts and groupings vary; the 88 displayed records are a searchable display scheme based on a provisional 81-unit list.

