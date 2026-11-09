"""Capture TAU's NT menu and rights metadata, plus two image-only wrappers.

No scan images or scripture transcriptions are downloaded by this script.
"""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "tau-platt-nt-menu"
BASE = "https://www.tau.ac.il/~hacohen/"
PAGES = {
    "nt-menu.html": "NTBiblia.html",
    "nt-information.html": "NT/Information.html",
    "general-information.html": "Information.html",
    "pauline-information.html": "NT/InformationPa.html",
    "catholic-information.html": "NT/InformationEp.html",
}


class MenuTargets(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict] = []
        self.form: dict | None = None
        self.select: dict | None = None
        self.option: dict | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs)
        if tag.lower() == "form":
            self.form = {"title": attrs.get("title", ""), "span_classes": [], "selectors": []}
        elif self.form is not None and tag.lower() == "span":
            self.form["span_classes"].extend((attrs.get("class") or "").split())
        elif self.form is not None and tag.lower() == "select":
            self.select = {"name": attrs.get("name", ""), "options": []}
        elif self.select is not None and tag.lower() == "option":
            self._finish_option()
            self.option = {"value": attrs.get("value"), "label": ""}

    def handle_data(self, data: str) -> None:
        if self.option is not None:
            self.option["label"] += data

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "option":
            self._finish_option()
        elif tag == "select" and self.select is not None and self.form is not None:
            self._finish_option()
            self.form["selectors"].append(self.select)
            self.select = None
        elif tag == "form" and self.form is not None:
            self._finish_option()
            self.forms.append(self.form)
            self.form = None

    def _finish_option(self) -> None:
        if self.option is None or self.select is None:
            return
        self.option["label"] = " ".join(self.option["label"].split())
        self.select["options"].append(self.option)
        self.option = None


def fetch(url: str) -> tuple[bytes, dict]:
    request = Request(url, headers={"User-Agent": "EthiopianBibleLibrary-source-archiver/1.0"})
    with urlopen(request, timeout=30) as response:
        body = response.read()
        metadata = {
            "url": url,
            "http_status": response.status,
            "content_type": response.headers.get("Content-Type", ""),
            "last_modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
            "size_bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
    if metadata["http_status"] != 200 or "text/html" not in metadata["content_type"].lower():
        raise RuntimeError(f"Unexpected TAU response: {metadata}")
    return body, metadata


def main() -> None:
    CAPTURE.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    files: list[dict] = []
    raw_pages: dict[str, bytes] = {}
    for name, relative_url in PAGES.items():
        body, record = fetch(urljoin(BASE, relative_url))
        raw_pages[name] = body
        (CAPTURE / name).write_bytes(body)
        files.append({"path": name, "captured_at": captured_at, **record})

    parser = MenuTargets()
    parser.feed(raw_pages["nt-menu.html"].decode("utf-8-sig", "replace"))
    sample_targets: dict[str, str] = {}
    for form in parser.forms:
        if form["title"] not in {"Acts", "Romans"}:
            continue
        for selector in form["selectors"]:
            for option in selector["options"]:
                value = option.get("value") or ""
                if value.startswith("NT/NTp ") and value.endswith(".html"):
                    sample_targets[form["title"]] = value
                    break
            if form["title"] in sample_targets:
                break
    if set(sample_targets) != {"Acts", "Romans"}:
        raise RuntimeError(f"Could not resolve both sample wrappers from the live menu: {sample_targets}")

    for title, relative_url in sample_targets.items():
        url = urljoin(BASE, quote(relative_url, safe="/"))
        body, record = fetch(url)
        name = f"sample-{title.lower()}-chapter-1.html"
        (CAPTURE / name).write_bytes(body)
        files.append({"path": name, "captured_at": captured_at, "sample_only": True, **record})

    manifest = {
        "source": "Tel Aviv University, Ran HaCohen Ethiopic Bible site",
        "capture_scope": (
            "The NT navigation page; its book-level, general-rights, Pauline, and Catholic-Epistles information pages; "
            "and one menu-selected HTML wrapper each for Acts and Romans. The wrapper pages refer to remote scan images. "
            "No image, OCR, or scripture transcription is captured. The menu is not exhaustively traversed."
        ),
        "files": files,
    }
    (CAPTURE / "SOURCE-CAPTURE.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Captured {len(files)} TAU metadata/wrapper pages; no scan images or scripture text copied.")


if __name__ == "__main__":
    main()
