# Start here: Ethiopian Bible Library

This folder is the complete repository root. The site, archive data, readers, source captures, schemas, tests, build scripts, and Pages workflow are directly inside it.

## Copy this package into your GitHub clone

Use GitHub Desktop with a local clone. The browser uploader cannot reliably handle this package's file count and large archive data.

1. In GitHub Desktop, open `austinsimpkins1997-ship-it/ethiopian-bible-library` and choose **Repository → Show in Explorer**.
2. Drag the repository root folder from Explorer onto `COPY_TO_GITHUB_REPO.bat` in this package. Or double-click the `.bat` and enter the clone folder path.
3. Review the displayed source and destination. Type `COPY` to proceed. The helper preserves `.git`, leaves destination-only files untouched, and verifies the copied files against the package checksums.
4. Review the resulting changes in GitHub Desktop. Commit and push when you are ready.

Copy the package contents to the clone root. Do not nest them inside a new folder in the repository. The helper does not commit or push.

## Verify

From this folder, run `python -B verify_archive_manifest.py`. The checksum manifest checks the listed package files; it does not certify canon completeness, translation accuracy, or rights. Read `README.md`, `CONTENT-LICENSES.md`, and `DATA-LICENSE.md` for the archive's scope and reuse notes.
