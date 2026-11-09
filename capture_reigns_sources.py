"""Capture TAU's Ethiopic Reigns I–II pages and the source/rights context."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "reigns-tau-dillmann"
BASE = "https://www.tau.ac.il/~hacohen"
BOOKS = (("I", "RegI", 31), ("II", "RegII", 24))


def _url_for(path: str) -> str:
    return f"{BASE}/{quote(path, safe='/')}"


def main() -> dict:
    CAPTURE.mkdir(parents=True, exist_ok=True)
    pages: list[tuple[str, str]] = [
        ("regum-information.html", f"{BASE}/Regum/Information.html"),
        ("tau-general-information.html", f"{BASE}/Information.html"),
        ("tau-ethiopic-index.html", f"{BASE}/Biblia.html"),
    ]
    for roman, file_prefix, chapter_count in BOOKS:
        for chapter in range(1, chapter_count + 1):
            pages.append((f"regum-{roman.lower()}-{chapter:02d}.html", _url_for(f"Regum/{file_prefix} {chapter}.html")))

    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    records = []
    for index, (name, url) in enumerate(pages):
        request = Request(url, headers={"User-Agent": "EthiopianBibleLibrary-source-archiver/1.0"})
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            modified = response.headers.get("Last-Modified")
        if status != 200 or "text/html" not in content_type.lower():
            raise RuntimeError(f"Unexpected source response for {url}: HTTP {status}, {content_type}")
        (CAPTURE / name).write_bytes(raw)
        records.append({
            "path": name,
            "url": url,
            "http_status": status,
            "content_type": content_type,
            "last_modified": modified,
            "captured_at": captured_at,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
        if index + 1 < len(pages):
            time.sleep(0.1)

    manifest = {
        "source": "Tel Aviv University, Ran HaCohen Ethiopic Bible site",
        "capture_scope": (
            "The 31 TAU menu-listed Regum I pages and 24 Regum II pages, plus the Reigns information page, "
            "site-wide terms page, and Ethiopic Bible index. Regum III–IV, critical apparatus PDFs, images, "
            "and other books are excluded. The page count is an observed capture scope, not proof of print-edition completeness."
        ),
        "captured_at": captured_at,
        "files": records,
    }
    (CAPTURE / "SOURCE-CAPTURE.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    notice = (
        "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any "
        "NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and this "
        "permission notice appear in all copies of the text. For other uses, please contact the copyright owner.\n\n"
        "TAU's site-wide information page says its Ethiopic texts are in the public domain or displayed with "
        "rights-holder permission; it explains that critical editions can have separate protection. This archive "
        "records the site's noncommercial permission as permission-limited, not as an open license or a claim of "
        "commercial permission. TAU's Reigns page says the transcription was OCR-converted and carefully proofread, "
        "and warns that new errors may remain."
    )
    (CAPTURE / "SOURCE-NOTICE.txt").write_text(notice + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    data = main()
    print(f"Captured {len(data['files'])} TAU Reigns text and context pages.")
