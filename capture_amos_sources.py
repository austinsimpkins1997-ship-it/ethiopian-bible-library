"""Capture TAU's Ethiopic Amos transcription and its attribution/terms pages."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "amos-tau-2009"
BASE = "https://www.tau.ac.il/~hacohen"
PAGES = {
    **{f"amos-chapter-{n}.html": f"{BASE}/Amos/Amos%20{n}.html" for n in range(1, 10)},
    "amos-information.html": f"{BASE}/Amos/Information.html",
    "tau-general-information.html": f"{BASE}/Information.html",
    "tau-ethiopic-index.html": f"{BASE}/Biblia.html",
}


def main() -> None:
    CAPTURE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    files = []
    for name, url in PAGES.items():
        request = Request(url, headers={"User-Agent": "EthiopianBibleLibrary-source-archiver/1.0"})
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            modified = response.headers.get("Last-Modified")
        if status != 200 or "text/html" not in content_type.lower():
            raise RuntimeError(f"Unexpected source response for {url}: HTTP {status}, {content_type}")
        (CAPTURE / name).write_bytes(raw)
        files.append({
            "path": name, "url": url, "http_status": status, "content_type": content_type,
            "last_modified": modified, "captured_at": stamp, "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    manifest = {
        "source": "Tel Aviv University, Ran HaCohen Ethiopic Bible site",
        "capture_scope": "Nine Ethiopic Amos text pages (menu chapters 1–9), source information/attribution, site-wide reuse notice, and Old Testament index. Images, Pereira's Portuguese translation, introduction, and critical apparatus are not copied.",
        "files": files,
    }
    (CAPTURE / "SOURCE-CAPTURE.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    notice = (
        "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and this permission notice appear in all copies of the text. For other uses, please contact the copyright owner.\n\n"
        "TAU's Amos information page credits Kefela Ghebre with preparing the text and says it is published there with his permission; Ran HaCohen proofread it. This archive relies on TAU's site-wide noncommercial copying/distribution notice for this digital text. No open-content or commercial license is asserted."
    )
    (CAPTURE / "SOURCE-NOTICE.txt").write_text(notice + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
