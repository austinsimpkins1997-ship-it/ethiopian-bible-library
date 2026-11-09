"""Create a media-free, checksum-pinned capture of the eBible Amharic HTML pages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "amharic"
UPSTREAM = SOURCE_DIR / "amh_html.zip"
CAPTURE = SOURCE_DIR / "amh-html-pages.zip"
MANIFEST = SOURCE_DIR / "capture-manifest.json"
UPSTREAM_URL = "https://ebible.org/Scriptures/amh_html.zip"


def capture() -> dict:
    if not UPSTREAM.is_file():
        raise FileNotFoundError(f"Download the upstream package to {UPSTREAM} before capturing it.")
    if CAPTURE.exists() or MANIFEST.exists():
        raise FileExistsError("Refusing to overwrite the existing Amharic source capture.")

    upstream_bytes = UPSTREAM.read_bytes()
    upstream_sha256 = hashlib.sha256(upstream_bytes).hexdigest()
    with zipfile.ZipFile(UPSTREAM) as source:
        html_members = sorted(
            name for name in source.namelist()
            if name.lower().endswith((".htm", ".html"))
        )
        if len(html_members) != 290 or "index.htm" not in html_members or "copyright.htm" not in html_members:
            raise ValueError(f"Expected the observed 290 HTML pages including index and copyright; found {len(html_members)}.")
        pages = {name: source.read(name) for name in html_members}

    CAPTURE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(CAPTURE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name, body in pages.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            target.writestr(info, body, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    manifest = {
        "source_name": "eBible.org Amharic New Testament HTML source package",
        "upstream_url": UPSTREAM_URL,
        "captured_at": "2026-10-25",
        "upstream_package_sha256": upstream_sha256,
        "upstream_package_bytes": len(upstream_bytes),
        "filtered_capture_file": CAPTURE.name,
        "filtered_capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "filtered_capture_scope": "All 290 HTML members only; stylesheets, fonts, images, and other non-HTML assets excluded.",
        "members": [
            {"path": name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
            for name, body in pages.items()
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = capture()
    print(
        f"Captured {len(result['members'])} HTML pages; upstream SHA-256 "
        f"{result['upstream_package_sha256']}; filtered SHA-256 {result['filtered_capture_sha256']}."
    )
