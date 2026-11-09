"""One-time capture of TAU's Geʽez Zephaniah text and provenance pages."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "zephaniah-tau-2022"
BASE = "https://www.tau.ac.il/~hacohen"
PAGES = {
    "zephaniah-chapter-1.html": f"{BASE}/Zephanja/Zep%201.html",
    "zephaniah-chapter-2.html": f"{BASE}/Zephanja/Zep%202.html",
    "zephaniah-chapter-3.html": f"{BASE}/Zephanja/Zep%203.html",
    "zephaniah-information.html": f"{BASE}/Zephanja/Information.html",
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
            "path": name,
            "url": url,
            "http_status": status,
            "content_type": content_type,
            "last_modified": modified,
            "captured_at": stamp,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    manifest = {
        "source": "Tel Aviv University, Ran HaCohen Ethiopic Bible site",
        "capture_scope": "Geʽez Zephaniah text pages 1–3, information and attribution page, site-wide reuse notice, and Ethiopic index menu. Facsimile images and Löfgren apparatus are not included.",
        "files": rows,
    }
    (CAPTURE / "SOURCE-CAPTURE.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
