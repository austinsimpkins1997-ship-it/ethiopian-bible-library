"""Capture TAU's 51 Ethiopic Sirach text pages and source/rights metadata."""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "sirach-tau-2026"
BASE = "https://www.tau.ac.il/~hacohen"
PAGES = {
    **{f"sirach-chapter-{n}.html": f"{BASE}/Apocryphi/Sir%20{n}.html" for n in range(1, 52)},
    "sirach-information.html": f"{BASE}/Apocryphi/InformationSir.html",
    "apocryphi-information.html": f"{BASE}/Apocryphi/Information.html",
    "tau-general-information.html": f"{BASE}/Information.html",
    "tau-ethiopic-index.html": f"{BASE}/Biblia.html",
}


def fetch(item: tuple[str, str]) -> dict:
    name, url = item
    request = Request(url, headers={"User-Agent": "EthiopianBibleLibrary-source-archiver/1.0"})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
        status = response.status
        content_type = response.headers.get("Content-Type", "")
        modified = response.headers.get("Last-Modified")
    if status != 200 or "text/html" not in content_type.lower():
        raise RuntimeError(f"Unexpected response for {url}: HTTP {status}, {content_type}")
    return {"path": name, "url": url, "raw": raw, "http_status": status,
            "content_type": content_type, "last_modified": modified}


def main() -> None:
    CAPTURE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch, pair) for pair in PAGES.items()]
        for future in as_completed(futures):
            item = future.result()
            results[item["path"]] = item
    files = []
    for name, _url in PAGES.items():
        item = results[name]
        raw = item.pop("raw")
        (CAPTURE / name).write_bytes(raw)
        files.append({
            "path": name, "url": item["url"], "http_status": item["http_status"],
            "content_type": item["content_type"], "last_modified": item["last_modified"],
            "captured_at": stamp, "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    manifest = {
        "source": "Tel Aviv University, Ran HaCohen Ethiopic Bible site",
        "capture_scope": "All 51 menu-listed Ethiopic Sirach text pages, the book-specific information page, the Dillmann 1894 apocrypha information page, the site-wide copyright/permission page, and the Ethiopic Bible index. Raw HTML is retained. No image edition, English/Latin translation, editorial apparatus, or external BibleGateway content is copied.",
        "files": files,
    }
    (CAPTURE / "SOURCE-CAPTURE.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    notice = (
        "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and this permission notice appear in all copies of the text. For other uses, please contact the copyright owner.\n\n"
        "The Sirach information page identifies Ran HaCohen as transcriber. TAU's general notice permits noncommercial copying/distribution with the required notice. This is not an open-content license or commercial permission; independent assessment of all underlying edition rights has not been performed."
    )
    (CAPTURE / "SOURCE-NOTICE.txt").write_text(notice + "\n", encoding="utf-8")
    print(f"Captured {len(files)} TAU HTML pages; source bytes retained with HTTP, size, timestamp, and SHA-256 metadata.")


if __name__ == "__main__":
    main()
