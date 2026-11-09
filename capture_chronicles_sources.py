"""Capture TAU's menu-listed Ethiopic Chronicles pages and source/rights context."""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "chronicles-tau-grebaut"
BASE = "https://www.tau.ac.il/~hacohen"
CONTEXT_PAGES = (
    ("chronicles-information.html", f"{BASE}/Paralipomen/Information.html"),
    ("tau-general-information.html", f"{BASE}/Information.html"),
    ("tau-ethiopic-index.html", f"{BASE}/Biblia.html"),
)
BOOKS = (("I", "MySubjectDMAAA1", 29), ("II", "MySubjectDMAAA2", 36))


def _fetch(url: str) -> tuple[bytes, dict]:
    request = Request(url, headers={"User-Agent": "EthiopianBibleLibrary-source-archiver/1.0"})
    for attempt in range(6):
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
                record = {
                    "url": url,
                    "http_status": response.status,
                    "content_type": content_type,
                    "last_modified": response.headers.get("Last-Modified"),
                    "size_bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            if record["http_status"] != 200 or "text/html" not in content_type.lower():
                raise RuntimeError(f"Unexpected source response for {url}: HTTP {record['http_status']}, {content_type}")
            return raw, record
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 5:
                raise RuntimeError(f"Unable to capture {url}: {exc}") from exc
            time.sleep(min(8, 0.5 * (2 ** attempt)))
        except URLError as exc:
            if attempt == 5:
                raise RuntimeError(f"Unable to capture {url}: {exc}") from exc
            time.sleep(min(8, 0.5 * (2 ** attempt)))
    raise RuntimeError(f"Unable to capture {url} after retries.")


def _menu(index_html: str, function_name: str) -> list[tuple[str, str]]:
    match = re.search(rf"function {function_name}\([^)]*\)(.*?)(?=\nfunction |\Z)", index_html, re.S)
    if not match:
        raise ValueError(f"TAU index is missing {function_name}.")
    return [
        (item.group(1), item.group(2))
        for item in re.finditer(r'new Option\("([^\"]+)","([^\"]+)"\)', match.group(1))
    ]


def main() -> dict:
    CAPTURE.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    records = []
    index_html = None
    for name, url in CONTEXT_PAGES:
        raw, record = _fetch(url)
        (CAPTURE / name).write_bytes(raw)
        record.update({"path": name, "captured_at": captured_at})
        records.append(record)
        if name == "tau-ethiopic-index.html":
            index_html = raw.decode("ascii")
        time.sleep(0.25)

    for roman, function_name, chapter_count in BOOKS:
        pages = _menu(index_html, function_name)
        expected = [str(value) for value in range(1, chapter_count + 1)]
        labels = [label for label, _ in pages]
        if labels != expected:
            raise ValueError(f"TAU Chronicles {roman} menu changed: expected {expected!r}, observed {labels!r}.")
        for position, (label, relative_path) in enumerate(pages, start=1):
            url = f"{BASE}/{quote(relative_path, safe='/')}"
            raw, record = _fetch(url)
            name = f"chronicles-{roman.lower()}-{int(label):02d}.html"
            (CAPTURE / name).write_bytes(raw)
            record.update({"path": name, "captured_at": captured_at, "menu_label": label, "menu_position": position})
            records.append(record)
            if position < len(pages):
                time.sleep(0.25)

    manifest = {
        "source": "Tel Aviv University, Ran HaCohen Ethiopic Bible site",
        "capture_scope": (
            "The 29 TAU menu-listed Paralipomena I pages and 36 Paralipomena II pages, plus the Chronicles information page, "
            "site-wide terms page, and Ethiopic Bible index. The two menu sequences and their page URLs are retained. "
            "The observed web scope does not prove completeness of the printed edition or agreement with a present-day EOTC edition."
        ),
        "captured_at": captured_at,
        "files": records,
    }
    (CAPTURE / "SOURCE-CAPTURE.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    notice = (
        "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any NONCOMMERCIAL "
        "purpose is granted without fee, provided that the copyright notice Ran HaCohen and this permission notice appear "
        "in all copies of the text. For other uses, please contact the copyright owner.\n\n"
        "TAU's Chronicles information page identifies the text as following Sylvain Grébaut's 1932 critical edition. "
        "This archive records TAU's site-wide notice-bound noncommercial permission, not an open license or commercial grant."
    )
    (CAPTURE / "SOURCE-NOTICE.txt").write_text(notice + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    data = main()
    print(f"Captured {len(data['files'])} TAU Chronicles text and context pages.")
