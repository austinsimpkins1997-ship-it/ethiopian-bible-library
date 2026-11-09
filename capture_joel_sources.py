"""Capture TAU's Geʽez Joel text and provenance pages for offline audit."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "joel-tau-2024"
BASE = "https://www.tau.ac.il/~hacohen"
PAGES = {
    **{f"joel-chapter-{chapter}.html": f"{BASE}/Joel/Joel%20{chapter}.html" for chapter in range(1, 5)},
    "joel-information.html": f"{BASE}/Joel/Information.html",
    "tau-general-information.html": f"{BASE}/Information.html",
    "tau-ethiopic-index.html": f"{BASE}/Biblia.html",
}


def main() -> None:
    CAPTURE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    rows = []
    for name, url in PAGES.items():
        request = Request(url, headers={"User-Agent": "EthiopianBibleLibrary-source-archiver/1.0"})
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "")
            modified = response.headers.get("Last-Modified")
            status = response.status
        if status != 200 or "text/html" not in content_type.lower():
            raise RuntimeError(f"Unexpected source response for {url}: HTTP {status}, {content_type}")
        (CAPTURE / name).write_bytes(raw)
        rows.append({
            "path": name, "url": url, "http_status": status,
            "content_type": content_type, "last_modified": modified,
            "captured_at": stamp, "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    manifest = {
        "source": "Tel Aviv University, Ran HaCohen Ethiopic Bible site",
        "capture_scope": "Geʽez Joel text pages 1–4, information and attribution page, site-wide reuse notice, and Ethiopic index menu. Facsimile images and Dillmann's apparatus are not included.",
        "files": rows,
    }
    (CAPTURE / "SOURCE-CAPTURE.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    notice = (
        "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and this permission notice appear in all copies of the text. For other uses, please contact the copyright owner.\n\n"
        "TAU's Joel information page credits Ran HaCohen with preparing this online text and identifies Dillmann's 1879 Ethiopic text as its basis. This permission is not an open-content license and does not establish commercial rights."
    )
    (CAPTURE / "SOURCE-NOTICE.txt").write_text(notice + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
