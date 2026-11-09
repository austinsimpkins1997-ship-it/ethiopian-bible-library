# Publish the existing site

This folder is the root of the existing `austinsimpkins1997-ship-it/ethiopian-bible-library` repository. Its `main` branch deploys through `.github/workflows/pages.yml`; do not create another repository or upload a ZIP as the site.

## Recommended: push from Git

Use a GitHub account with write access to the repository. From this folder:

```powershell
git status --short --branch
python build_standalone.py
python verify_archive_manifest.py
python -m unittest discover -s tests -v
node tests/test_reader_package.js
git push origin main
```

The Pages workflow rebuilds source-backed readers, runs the checks, and deploys when a commit reaches `main`. Confirm the workflow succeeds in the repository's **Actions** tab and check **Settings → Pages** for the deployment URL. Never force-push to replace the repository history.

## Browser uploads

GitHub's web uploader is suited to small changes. It accepts at most 100 files per upload and 25 MB per file. This archive update changes hundreds of paths; committing batches separately can leave the published site in an incomplete state and trigger failing builds. Use a normal Git push for the complete repository snapshot instead.

## Content and checksums

`archive-manifest.json` records SHA-256 hashes and byte lengths for the package. Rebuild with `python build_standalone.py`, then run `python verify_archive_manifest.py` to confirm the complete package matches the manifest. Scripture and translation content retain their individual source, rights, and review limits; the software license does not grant blanket text reuse rights.
