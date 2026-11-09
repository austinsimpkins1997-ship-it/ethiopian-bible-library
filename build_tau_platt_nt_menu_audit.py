"""Build a bounded, offline audit of TAU's Platt 1830 NT navigation menu."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from archive_manifest import write_text_atomically
from capture_tau_platt_nt_menu import CAPTURE, MenuTargets

ROOT = Path(__file__).resolve().parent
CAPTURE_MANIFEST = CAPTURE / "SOURCE-CAPTURE.json"
REPORT_JSON = ROOT / "examples" / "tau-platt-nt-menu-audit.json"
REPORT_HTML = ROOT / "research" / "tau-platt-nt-menu-audit.html"
CORPUS_ID = "ethiopic-new-testament-platt-1830-tau"
NT_FORM_TITLES = {
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "Corinthians", "Galatians",
    "Ephesians", "Philippians", "Colossians", "Thessalonians", "Timothy", "Titus",
    "Philemon", "Hebrews", "Epistle of James", "Epistles of Peter", "Epistles of John",
    "Epistle of Jude", "Revelation",
}
EXPECTED_GREY = {"Matthew", "Mark", "Luke", "John", "Romans", "Ephesians", "Philippians", "Colossians"}
EXPECTED_GREEN = {
    "Thessalonians", "Timothy", "Titus", "Philemon", "Epistle of James", "Epistles of Peter",
    "Epistles of John", "Epistle of Jude",
}


class ImageReferences(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            source = dict(attrs).get("src")
            if source:
                self.sources.append(source)


class PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def page_text(data: bytes) -> str:
    parser = PlainText()
    parser.feed(data.decode("cp1252", "replace"))
    return " ".join(" ".join(parser.parts).split())


def load_capture() -> tuple[dict, dict[str, bytes]]:
    manifest = json.loads(CAPTURE_MANIFEST.read_text(encoding="utf-8"))
    bodies: dict[str, bytes] = {}
    for item in manifest["files"]:
        path = CAPTURE / item["path"]
        data = path.read_bytes()
        if (item.get("http_status") != 200 or len(data) != item["size_bytes"]
                or hashlib.sha256(data).hexdigest() != item["sha256"]):
            raise ValueError(f"TAU NT capture failed size/SHA validation: {item['path']}")
        bodies[item["path"]] = data
    return manifest, bodies


def build_report() -> dict:
    manifest, bodies = load_capture()
    general = page_text(bodies["general-information.html"])
    info = page_text(bodies["nt-information.html"])
    pauline = page_text(bodies["pauline-information.html"])
    catholic = page_text(bodies["catholic-information.html"])
    if "noncommercial purpose" not in general.lower() or "Ran HaCohen" not in general:
        raise ValueError("TAU's general noncommercial notice is missing from the captured page.")
    if "newer critical edition" not in info.lower() or "each book and chapter" not in info.lower():
        raise ValueError("TAU NT information page no longer states the menu and newer-edition limitation.")
    personal_only = "personal research only" in pauline.lower() and "without written consent" in pauline.lower()
    personal_only &= "personal research only" in catholic.lower() and "without written consent" in catholic.lower()
    if not personal_only:
        raise ValueError("The captured Pauline/Catholic transcription restriction changed or is missing.")

    menu = MenuTargets()
    menu.feed(bodies["nt-menu.html"].decode("utf-8-sig", "replace"))
    nt_forms = []
    other_forms = []
    for form in menu.forms:
        classes = set(form["span_classes"])
        style = "grey" if any("grey" in item.lower() for item in classes) else (
            "green" if any("green" in item.lower() for item in classes) else "standard"
        )
        selectors = form["selectors"]
        targets = [
            option["value"] for selector in selectors for option in selector["options"]
            if option.get("value")
        ]
        record = {
            "menu_title": form["title"],
            "observed_color_class": style,
            "select_control_count": len(selectors),
            "select_option_count": sum(len(selector["options"]) for selector in selectors),
            "selector_names": [selector["name"] for selector in selectors],
            "target_values_observed": targets,
        }
        (nt_forms if form["title"] in NT_FORM_TITLES else other_forms).append(record)

    if len(nt_forms) != 21 or len(other_forms) != 4:
        raise ValueError(f"Unexpected TAU menu form inventory: NT={len(nt_forms)}, other={len(other_forms)}")
    grey = {item["menu_title"] for item in nt_forms if item["observed_color_class"] == "grey"}
    green = {item["menu_title"] for item in nt_forms if item["observed_color_class"] == "green"}
    if grey != EXPECTED_GREY or green != EXPECTED_GREEN:
        raise ValueError(f"TAU menu color classes changed: grey={sorted(grey)}, green={sorted(green)}")

    samples = []
    for title in ("Acts", "Romans"):
        captured_name = f"sample-{title.lower()}-chapter-1.html"
        body = bodies[captured_name]
        parser = ImageReferences()
        parser.feed(body.decode("utf-8-sig", "replace"))
        title_match = re.search(r"<title>\s*([^<]+)", body.decode("utf-8-sig", "replace"), re.I)
        if not title_match or not parser.sources:
            raise ValueError(f"TAU {title} sample wrapper no longer points to an image page.")
        samples.append({
            "menu_title": title,
            "wrapper_page": captured_name,
            "wrapper_title": title_match.group(1).strip(),
            "image_reference_not_copied": parser.sources[0],
            "image_count_in_wrapper": len(parser.sources),
            "evidence_limit": "One sample wrapper only; the referenced image was not fetched or copied.",
        })

    return {
        "audit_date": max(item["captured_at"][:10] for item in manifest["files"]),
        "corpus_id": CORPUS_ID,
        "capture_manifest": "../readers/source/tau-platt-nt-menu/SOURCE-CAPTURE.json",
        "source_ids": ["SRC-036", "SRC-081", "SRC-086", "SRC-100", "SRC-162", "SRC-163"],
        "edition_basis": "TAU identifies its digitized Ethiopic New Testament as following Platt's 1830 edition.",
        "menu_form_count": len(nt_forms),
        "nt_menu_forms": nt_forms,
        "other_menu_forms": other_forms,
        "grey_form_titles": sorted(grey),
        "green_form_titles": sorted(green),
        "sample_wrappers": samples,
        "rights": {
            "site_digitization_notice": "Noncommercial copying/distribution only with Ran HaCohen's copyright and permission notices.",
            "green_transcriptions": "Pauline/Catholic information pages restrict the named Ted Erho transcriptions to personal research and prohibit storage in another repository without written consent.",
        },
        "limits": [
            "The 21 menu form labels are grouped labels, not an audited one-form-per-canon-entry crosswalk.",
            "Option totals are raw HTML controls, not verified chapter counts; some grouped controls are dynamic.",
            "Only the Acts and Romans first-page wrappers were sampled; each points to a remote image. No image or scripture text was copied.",
            "No claim of complete Platt edition coverage, current EOTC edition identity, text accuracy, or a Church-list crosswalk is made.",
        ],
    }


def render_html(report: dict) -> str:
    def esc(value: object) -> str:
        return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))

    rows = "\n".join(
        f"<tr><td>{esc(item['menu_title'])}</td><td>{esc(item['observed_color_class'])}</td>"
        f"<td>{item['select_control_count']}</td><td>{item['select_option_count']}</td></tr>"
        for item in report["nt_menu_forms"]
    )
    other = ", ".join(esc(item["menu_title"]) for item in report["other_menu_forms"])
    sample_rows = "\n".join(
        f"<li>{esc(item['menu_title'])}: captured wrapper title “{esc(item['wrapper_title'])}”; "
        f"it references {esc(item['image_reference_not_copied'])}, which was not copied.</li>"
        for item in report["sample_wrappers"]
    )
    limits = "\n".join(f"<li>{esc(item)}</li>" for item in report["limits"])
    return f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TAU Platt 1830 New Testament menu audit</title>
<style>body{{font:1rem/1.6 system-ui,sans-serif;max-width:70rem;margin:2rem auto;padding:0 1rem;color:#18352d}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd5d0;padding:.45rem;text-align:left}}th{{background:#eef4f0}}.note{{padding:1rem;background:#f5f2e8;border-left:4px solid #bb8c3d}}</style>
<main><h1>TAU Platt 1830 New Testament menu audit</h1>
<p>Local capture date: {esc(report['audit_date'])}. TAU identifies its digitized Ethiopic New Testament as following Platt’s 1830 edition and says book/chapter navigation is available from the menu. This page records observed menu metadata; it is not a reader or a canon crosswalk.</p>
<div class="note"><strong>Rights and boundaries.</strong> TAU's digitized-text notice permits noncommercial copying/distribution only with required notices. Its Pauline and Catholic Epistles pages separately restrict Ted Erho's transcriptions to personal research and prohibit repository storage without written consent. No transcription or scan image is bundled here.</div>
<h2>Observed New Testament form labels ({report['menu_form_count']})</h2>
<p>Grey labels are identified by TAU as books with newer critical editions that cannot be placed on its site. Green labels are separate transcription sections; their information pages carry the personal-research-only restriction. These colors are recorded as displayed; menu grouping is not mapped automatically to the EOTC list.</p>
<table><thead><tr><th>Menu form title</th><th>Displayed color class</th><th>Select controls</th><th>Raw option items</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Other forms on the menu page</h2><p>{other}</p>
<h2>Sampled wrappers</h2><ul>{sample_rows}</ul>
<p>The earlier menu sampling of Didascalia's introduction, sections I and XXI, and notes is documented separately in the <a href="didascalia-source-review.md">Didascalia source review</a>; it is not part of this NT form count.</p>
<h2>Limits</h2><ul>{limits}</ul>
<p>Captured source metadata: <a href="../readers/source/tau-platt-nt-menu/SOURCE-CAPTURE.json">SOURCE-CAPTURE.json</a>. Source records: {esc(', '.join(report['source_ids']))}.</p></main></html>'''


def apply(archive: dict) -> dict:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_HTML.write_text(render_html(report), encoding="utf-8")

    source_by_id = {item["source_id"]: item for item in archive.get("sources", [])}
    source = source_by_id.get("SRC-086")
    if source is None:
        raise ValueError("TAU NT menu source SRC-086 is missing.")
    source["inspection_and_limitations"] = (
        "Inspected and captured 2026-10-26. The menu contains 21 grouped New Testament form labels and four separate "
        "forms under LIBRI APOCRYPHI. Eight NT form labels are styled grey; TAU's information page says grey books "
        "have newer critical editions that cannot be placed on the site. Eight form labels are green; the separate "
        "Pauline/Catholic pages state that Ted Erho's transcriptions are for personal research only and cannot be "
        "stored in another repository without written consent. Raw option counts are preserved in the local audit, not "
        "treated as verified chapter counts. Sampled first-page wrappers for Acts and Romans each reference one remote "
        "scan image. The image files and all scripture text were excluded. See the local report for the exact form-level "
        "inventory and limits. This does not establish all NT page availability, a 27-entry crosswalk, complete Platt "
        "coverage, exact current EOTC edition identity, or text accuracy. Earlier Didascalia-specific inspection "
        "(2026-10-25) recorded the menu labels Cont., Intro., I–XXII, and Notae; four selected Didascalia wrappers "
        "(Intro., I, XXI, Notae) each contained one scan-image reference. This sample does not prove the full work's "
        "extent or a Church-list crosswalk; see research/didascalia-source-review.md."
    )
    source["archive_status"] = "NT menu/rights metadata captured; 21 grouped NT form labels inventoried; Acts/Romans wrappers sampled. Earlier Didascalia menu sample retained. No image or scripture text bundled."
    source["local_metadata_url"] = "readers/source/tau-platt-nt-menu/SOURCE-CAPTURE.json"
    source["local_review_url"] = "research/tau-platt-nt-menu-audit.html"

    info = source_by_id.get("SRC-081")
    if info is not None:
        info["inspection_and_limitations"] = (
            "Inspected and captured 2026-10-26. TAU identifies Platt's 1830 Ethiopic NT edition, says book/chapter "
            "navigation is provided from the menu, and warns that several books with newer critical editions cannot be "
            "placed on the site (the menu displays eight grey form labels). The separate local menu audit records 21 "
            "grouped NT form labels, not 27 verified book-to-page crosswalks. Two wrappers sampled for Acts and Romans "
            "reference scan images; no chapter inventory, page completeness, transcription, or text accuracy is "
            "established. See SRC-086 and the local source review."
        )
        info["local_metadata_url"] = "readers/source/tau-platt-nt-menu/nt-information.utf8.html"
        info["local_capture_manifest_url"] = "readers/source/tau-platt-nt-menu/SOURCE-CAPTURE.json"
        capture = next(item for item in json.loads(CAPTURE_MANIFEST.read_text(encoding="utf-8"))["files"] if item["path"] == "nt-information.html")
        info["local_snapshot_path"] = "readers/source/tau-platt-nt-menu/nt-information.html"
        info["local_snapshot_sha256"] = capture["sha256"]
        info["local_snapshot_status"] = "byte-exact original capture; declares windows-1252; not a scripture text layer"
        info["local_snapshot_note"] = f"Captured {capture["captured_at"]} from {capture["url"]}; raw bytes retained unchanged. Sanitized UTF-8 display derivative: readers/source/tau-platt-nt-menu/nt-information.utf8.html (SHA-256 4378f94f33510c3fca21e765e0e4447cc4085155e2756f3de292d732cd5e82cd); active scripts and embedded/network content removed or blocked."
        info["local_review_url"] = "research/tau-platt-nt-menu-audit.html"

    registry = archive.get("translation_registry", {})
    corpus = next((item for item in registry.get("corpus_leads", []) if item.get("corpus_id") == CORPUS_ID), None)
    if corpus is None:
        raise ValueError(f"TAU NT corpus lead {CORPUS_ID} is missing.")
    corpus["scope_description"] = (
        "TAU identifies a digitized Ethiopic NT following Thomas Pell Platt's 1830 edition. Its menu has 21 grouped "
        "NT form labels plus four additional forms under LIBRI APOCRYPHI. Eight NT labels are grey; TAU says this "
        "marks books with newer critical editions that cannot be placed on the site. Eight are green, and separate "
        "information pages restrict the Ted Erho Pauline/Catholic transcriptions to personal research and prohibit "
        "storage in another repository without written consent. Two sampled first-page wrappers (Acts and Romans) "
        "reference one remote scan image each; no image or scripture text is bundled. Raw option counts are not "
        "verified chapter counts, and grouped menu forms are not mapped to individual EOTC entries. This is bounded "
        "edition-navigation evidence, not evidence of complete/current EOTC text or a 27-book crosswalk. See "
        "research/tau-platt-nt-menu-audit.html and SRC-081, SRC-086, SRC-162, SRC-163."
    )
    corpus["review_status"] = (
        "Captured source pages pass local size/SHA checks. The 2026-10-26 audit inventory lists 21 grouped NT form "
        "labels, four separately classified page forms, eight grey labels, and eight green labels; two wrapper samples "
        "reference remote scan images. No image, OCR, or text was copied. Exact page extents, all chapter targets, "
        "completeness, text accuracy, and current EOTC edition mapping remain unverified. Ted Erho's green-form "
        "transcriptions are expressly personal-research-only and must not be stored here without written consent."
    )
    corpus["notes"] = (
        "TAU's general page describes digitized Ethiopic texts and conditional noncommercial reuse; the NT-specific "
        "page identifies Platt 1830 and says book/chapter navigation is provided. The local inventory captures 21 "
        "grouped NT form labels, not an individual title-to-page crosswalk. Grey means newer critical editions cannot "
        "be placed on the site per TAU's note; green sections are separately restricted by the Pauline/Catholic "
        "information pages to personal research and may not be stored in another repository without written consent. "
        "Sampled Acts and Romans wrappers contain image references only; images and texts are not bundled. Didascalia, "
        "Canones, Kebra Nagast, and Fetha Nagast appear separately under LIBRI APOCRYPHI; that heading is TAU's "
        "classification and is not a church canon mapping. The online scan is not a reader, nor proof of complete "
        "coverage or current EOTC edition identity. See research/tau-platt-nt-menu-audit.html."
    )
    registry_path = ROOT / "translation-registry.json"
    base_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    base_corpus = next(
        (item for item in base_registry.get("corpus_leads", []) if item.get("corpus_id") == CORPUS_ID), None
    )
    if base_corpus is None:
        raise ValueError(f"TAU NT corpus lead {CORPUS_ID} is missing from translation-registry.json.")
    for key in ("scope_description", "review_status", "notes"):
        base_corpus[key] = corpus[key]
    write_text_atomically(registry_path, json.dumps(base_registry, ensure_ascii=False, indent=2) + "\n")
    return report


if __name__ == "__main__":
    result = build_report()
    REPORT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_HTML.write_text(render_html(result), encoding="utf-8")
    print(f"Audited {result['menu_form_count']} grouped NT forms; grey={len(result['grey_form_titles'])}, green={len(result['green_form_titles'])}; text/images not bundled.")
