from __future__ import annotations

import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
OUTPUT = ROOT / "EthiopianBibleLibrary_GitHub_Upload.zip"


def included(path: Path) -> bool:
    relative = path.relative_to(SITE)
    return not any(part in {".git", "__pycache__"} for part in relative.parts) and path.suffix != ".pyc"


def main() -> None:
    files = sorted(path for path in SITE.rglob("*") if path.is_file() and included(path))
    if not files:
        raise SystemExit("Site package is empty.")
    required = {
        ".nojekyll",
        ".github/workflows/pages.yml",
        "index.html",
        "archive.json",
        "app.js",
        "readers/source/brenton-exodus/capture-manifest.json",
        "readers/source/brenton-exodus/CAPTURE-NOTICE.txt",
    }
    relative_names = {path.relative_to(SITE).as_posix() for path in files}
    missing = required - relative_names
    if missing:
        raise SystemExit(f"Site package is missing required files: {sorted(missing)}")

    fd, temp_name = tempfile.mkstemp(prefix="ethiopian-bible-upload-", suffix=".zip", dir=ROOT)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                archive.write(path, path.relative_to(SITE).as_posix())

        with zipfile.ZipFile(temp_path) as archive:
            bad = archive.testzip()
            if bad:
                raise SystemExit(f"ZIP CRC check failed: {bad}")
            names = set(archive.namelist())
            if required - names:
                raise SystemExit(f"ZIP omitted required files: {sorted(required - names)}")
            if any(name.startswith(".git/") or "/.git/" in name or "__pycache__" in name for name in names):
                raise SystemExit("ZIP must exclude Git internals and Python caches.")
            embedded = archive.read("index.html").decode("utf-8")
            match = re.search(r'<script id="archive-data" type="application/json">(.*?)</script>', embedded, re.S)
            if not match:
                raise SystemExit("Packaged index has no embedded archive data.")
            page_data = json.loads(match.group(1))
            archive_data = json.loads(archive.read("archive.json"))
            if page_data != archive_data:
                raise SystemExit("Packaged index data does not match packaged archive.json.")
            manifest = json.loads(archive.read("readers/source/brenton-exodus/capture-manifest.json"))
            if manifest.get("chapter_count") != 40:
                raise SystemExit("Packaged Exodus capture manifest is incomplete.")
            for row in manifest["chapters"]:
                capture_path = f"readers/source/brenton-exodus/{row['capture_file']}"
                if capture_path not in names:
                    raise SystemExit(f"Packaged capture is missing: {capture_path}")
        os.replace(temp_path, OUTPUT)
        print(f"Built {OUTPUT.name}: {len(files)} files, {OUTPUT.stat().st_size:,} bytes.")
        print("Validated ZIP CRCs, upload-root layout, embedded archive equality, and all 40 Exodus capture files.")
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    main()
