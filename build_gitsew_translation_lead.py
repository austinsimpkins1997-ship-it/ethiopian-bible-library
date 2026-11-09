"""Bundle the historical Gitsew/Gessew source editions without claiming a verified transcript."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from archive_manifest import write_text_atomically


ROOT = Path(__file__).resolve().parent
ARCHIVE_PATH = ROOT / "archive.json"
REGISTRY_PATH = ROOT / "translation-registry.json"
FELL_PDF = "readers/source/gitsew/Canones-Apostolorum-Aethiopice-Fell-1871.pdf"
SCHODDE_PDF = "readers/source/gitsew/The-Apostolic-Canons-Schodde-1885.pdf"
REVIEW_HTML = "research/gitsew-fell-schodde-translation.html"
SCHODDE_RAW_TEXT = "research/gitsew-schodde-1885-raw-extract.txt"
SCHODDE_RAW_TEXT_SHA256 = "b065bb15b1f1263833752a04562d04a621e26ab49ad98cf54b444ca65ed2e080"
SCHODDE_HEADING_AUDIT = "research/gitsew-schodde-heading-audit.json"
SCHODDE_PROOFREAD_PROGRESS = "research/gitsew-schodde-proofread-progress.json"
SCHODDE_PDF_SHA256 = "419f4f9f519414a4ad10c4533478488f741d26570fbf7220240cf998d766a79a"
SCHODDE_SOURCE_ID = "SRC-433"
SCHODDE_LEAD_ID = "gitsew-ethiopic-apostolic-canons-schodde-1885"
PUBLISHER_SOURCE_ID = "SRC-443"
PUBLISHER_LEAD_ID = "gitsew-modern-english-schoddederived-2026"
FELL_LATIN_CANON20_PATH = "research/gitsew-fell-latin-canon20.json"
FELL_OCR_AUDIT_PATH = "research/gitsew-fell-internet-archive-ocr-audit.json"
FELL_OCR_AUDIT = {
    "record_id": "gitsew-fell-internet-archive-ocr-audit",
    "source_id": "SRC-029",
    "source_path": FELL_PDF,
    "ocr_url": "https://archive.org/download/canonesapostolor00unse/canonesapostolor00unse_djvu.txt",
    "ocr_service": "Internet Archive DjVu text derivative for item canonesapostolor00unse",
    "checked_date": "2026-10-27",
    "downloaded_bytes": 80982,
    "downloaded_sha256": "4cde5ca66251e67dcf2be29135097f305c6050e1330ed31c5d07cdfe879f33c9",
    "observed_characters": 78933,
    "ethiopic_unicode_codepoints": 0,
    "canon_xx_sample": "The OCR labels an apparatus block 'Can. XX.' but renders its Ethiopic word content as unrelated Latin-looking glyph sequences and replacement characters.",
    "status": "rejected_as_geez_transcription",
    "decision": "Not bundled or used to transcribe or translate the Ethiopic passage. The Latin transcription continues to be checked visually against the PDF scan; the Geʽez wording remains uncollated.",
    "limitation": "The OCR output is a derivative of the same Internet Archive digitization, not an independent textual witness. Zero Ethiopic Unicode code points in the returned OCR are direct evidence that it is not a usable Unicode Geʽez transcription."
}
FELL_LATIN_CANON20 = {
    "record_id": "gitsew-fell-latin-canon20",
    "source_id": "SRC-029",
    "source_path": FELL_PDF,
    "source_sha256": "5bfc75a17cee6551153f36ba123b443dd17ce98c90aa40e9b7e8ac0115421beb",
    "source_location": {"pdf_page": 39, "printed_page": 37, "canon": "XX"},
    "same_edition_geez_locator": {
        "pdf_page": 30,
        "printed_page": 28,
        "section": "Lectiones variantes / critical apparatus",
        "evidence": "The printed apparatus explicitly labels a group of Ethiopic textual variants 'Can. XX.' This verifies the edition's Canon XX numbering and provides a locator for future Geʽez collation; it is not the full Ethiopic canon text."
    },
    "source_title_page_note": "The 1871 title page identifies the edition as including a Latin version (cum versione Latina).",
    "language_tag": "la",
    "transcription_method": "Manually transcribed by visual comparison with the bundled 1800-pixel rendered scan of PDF page 39. Original spelling and punctuation retained; line-end hyphenation removed.",
    "latin_text": "Can. XX. De eo, qui per munera ordinatus est. — Si quis episcopus aut presbyter aut diaconus dignitatem clericalem per munera adeptus fuerit: deponatur, atque deponatur etiam is, qui eum ordinaverit et in perpetuum ab administratione sacerdotii excludatur: nullamque cum eo habeant societatem, sicut Simonem Magum a me removi: ego Petrus.",
    "english_translation": {
        "language_tag": "en",
        "text": "Canon XX. On one ordained through payments. If any bishop, presbyter, or deacon has obtained clerical rank through payments, let him be deposed; and let the one who ordained him also be deposed and excluded forever from administering priestly office. Let them have no association with him, just as I removed Simon Magus from me: I, Peter.",
        "method": "New, close translation from Fell's printed Latin version, preserving the procedural clauses and first-person attribution. ‘Per munera’ literally means ‘through gifts’; ‘payments’ expresses its bribery context without silently reusing Percival's separate translation.",
        "review_status": "draft_translated_from_printed_latin_not_independently_reviewed"
    },
    "relationship_to_schodde": "This is Fell's Latin version within the same 1871 edition that contains the Ethiopic text used by Schodde. It independently supplies a same-edition Latin parallel for the complete rule, including 'ego Petrus'; it does not make those words visible in the damaged 1885 English scan or establish exact equivalence between the Latin and Ethiopic wording.",
    "rights_status": "The underlying 1871 text is public domain by age; scan-image rights metadata is recorded separately for the facsimile. The new English rendering is original archive editorial work.",
    "review_status": "scan_transcribed_and_translation_drafted_not_geez_collated"
}


def _write_json(path: Path, data: dict) -> None:
    write_text_atomically(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _roman(number: int) -> str:
    parts = ((50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
    result = []
    for value, numeral in parts:
        while number >= value:
            result.append(numeral)
            number -= value
    return "".join(result)


def _heading_audit() -> dict:
    page_spans = (
        (1, 7, 4, 63), (8, 13, 5, 64), (14, 20, 6, 65),
        (21, 26, 7, 66), (27, 31, 8, 67), (32, 37, 9, 68),
        (38, 46, 10, 69), (47, 51, 11, 70), (52, 54, 12, 71),
        (55, 57, 13, 72),
    )
    headings = []
    for first, last, pdf_page, printed_page in page_spans:
        headings.extend({
            "number": number,
            "printed_label": _roman(number),
            "pdf_page": pdf_page,
            "printed_page": printed_page,
        } for number in range(first, last + 1))
    return {
        "audit_id": "gitsew-schodde-1885-printed-heading-inventory",
        "source_id": SCHODDE_SOURCE_ID,
        "source_path": SCHODDE_PDF,
        "source_sha256": SCHODDE_PDF_SHA256,
        "observed_date": "2026-10-27",
        "method": "Visual inspection of rendered PDF facsimile pages; printed Roman-numeral headings transcribed as labels only.",
        "scope": {
            "pdf_pages": [4, 13],
            "printed_pages": [63, 72],
            "heading_count": 57,
            "first_heading": "I",
            "last_heading": "LVII",
        },
        "limitations": [
            "This inventory verifies only the visible printed heading labels and their scan/printed page locations.",
            "It does not proofread, transcribe, translate, or establish the accuracy or completeness of the article text.",
            "It does not establish that the 57 printed divisions match every Geʽez witness or current Church edition.",
            "The page-labeled PDF text-layer extraction remains unproofread research data and is not reader text.",
        ],
        "headings": headings,
    }


def _review_html() -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Gitsew / Gessew — source editions</title>
  <style>
    :root {{ color-scheme: light; --ink: #123e39; --muted: #53645f; --line: #e3ddd1; --paper: #fbfaf7; --accent: #b27d32; }}
    body {{ margin: 0; background: var(--paper); color: var(--ink); font: 16px/1.65 system-ui, sans-serif; }}
    main {{ width: min(900px, calc(100% - 32px)); margin: 0 auto; padding: 36px 0 64px; }}
    h1, h2 {{ font-family: Georgia, serif; font-weight: 500; line-height: 1.2; }}
    h1 {{ font-size: clamp(2rem, 5vw, 3.3rem); margin: 0 0 12px; }}
    h2 {{ font-size: 1.55rem; margin: 32px 0 8px; }}
    p, li {{ max-width: 78ch; }}
    .kicker {{ color: var(--accent); letter-spacing: .12em; text-transform: uppercase; font-size: .78rem; font-weight: 700; }}
    .notice {{ border-left: 4px solid var(--accent); background: #f3efe5; padding: 14px 18px; }}
    .source {{ border: 1px solid var(--line); background: white; padding: 18px; margin: 14px 0; }}
    a {{ color: #075c53; text-underline-offset: .18em; overflow-wrap: anywhere; }}
    .buttons {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }}
    .button {{ display: inline-block; border: 1px solid #8e795b; border-radius: 4px; padding: 10px 14px; text-decoration: none; font-weight: 650; }}
    .small {{ color: var(--muted); font-size: .92rem; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body><main>
  <p class="kicker">Ethiopian Bible Library · source review</p>
  <h1>Gitsew / Gessew</h1>
  <p>Two historical editions are bundled here for offline inspection: Winand Fell’s 1871 Ethiopic-and-Latin edition and George H. Schodde’s 1885 English translation of the Ethiopic text.</p>
  <div class="notice"><strong>Reader status:</strong> The page-labeled Schodde PDF text-layer extraction remains unproofread. A separate partial transcript covers the opening formula and Canons I–LVII, except that Canon XX is only a visible scan fragment. The scan cuts Canon XX off after “from me,” and the missing words are not supplied. This is not a complete reader and does not increase reader coverage.</div>

  <h2>Fell, 1871 — Ethiopic and Latin</h2>
  <div class="source">
    <p><em>Canones Apostolorum Aethiopice</em>, edited by Winand Fell, Leipzig: F. A. Brockhaus, 1871. Theological Commons describes the edition as Ethiopic and Latin; its digitized item record identifies 52 pages and states “No Known Copyright” for the images. Berkeley Lawcat describes the printed item as 47 pages. The difference between printed pagination and scan-page count remains noted rather than silently reconciled.</p>
    <div class="buttons"><a class="button" href="../readers/source/gitsew/Canones-Apostolorum-Aethiopice-Fell-1871.pdf">Open local Fell scan (PDF)</a></div>
    <p class="small">Catalog and scan record: <a href="https://commons.ptsem.edu/id/canonesapostolor00unse">Princeton Theological Seminary, Theological Commons</a> · <a href="https://archive.org/details/canonesapostolor00unse">Internet Archive item</a> · <a href="https://lawcat.berkeley.edu/record/333354">Berkeley Lawcat</a>.</p>
  </div>

  <h2>Schodde, 1885 — English translation</h2>
  <div class="source">
    <p>George H. Schodde, “The Apostolic Canons, Translated from the Ethiopic,” <em>Journal of the Society of Biblical Literature and Exegesis</em> 5, no. 1/2 (1885), 61–72. Schodde states that he translated Fell’s 1871 Ethiopic edition, which was published with a Latin version. The journal article prints headings through Canon LVII; that printed count is preserved as evidence and is not forced into the 56-canons count found in some descriptions.</p>
    <div class="buttons"><a class="button" href="../readers/source/gitsew/The-Apostolic-Canons-Schodde-1885.pdf">Open local Schodde article (PDF)</a></div>
    <div class="buttons"><a class="button" href="gitsew-schodde-1885-raw-extract.txt">Read raw text-layer extraction (unproofread)</a></div>
    <p class="small"><a href="gitsew-schodde-heading-audit.json">Open the visual inventory of all 57 printed headings</a>. <a href="gitsew-schodde-proofread-progress.json">Open the partial proofread transcript</a> for the opening formula, Canons I–LVII except Canon XX, and the scan-visible fragment of Canon XX. That working transcript is not a complete reader and is not counted toward coverage.</p>
    <p class="small">The extraction covers PDF pages 2–13 (printed pages 61–72); the later repository notice on PDF page 1 is excluded. Extraction errors, missing characters, and reading-order issues have not been corrected. Compare every passage with the facsimile before quoting or using it as a translation.</p>
    <p class="small">Article record and rights statement: <a href="https://www.jstor.org/stable/3268629">JSTOR stable record 3268629</a>. The local facsimile begins with a one-page repository notice; the article itself occupies printed pages 61–72 (PDF pages 2–13).</p>
  </div>

  <h2>Related Greek canonical parallel — not a completion of Schodde</h2>
  <div class="source">
    <p>The Ethiopic/Schodde Canon XX on printed page 65 concerns ordination obtained by bribery. A related Greek collection places a corresponding rule at Canon XXIX (Percival’s 1899 numbering): it concerns obtaining clerical rank by money and ends with the Simon Magus comparison, “as Simon Magus was by me, Peter.” The next rules also align in sequence: Schodde XXI concerns obtaining a church through rulers, corresponding to Percival XXX. This sequence supports identifying a parallel tradition, while showing that numbering differs.</p>
    <p><strong>Editorial boundary:</strong> this Greek-based parallel is not the missing portion of Schodde’s scan and does not establish the exact Ethiopic wording or the ending of Fell’s witness. Canon XX therefore remains a fragment ending “from me,” in the proofread transcription. The Greek/Percival wording is not inserted into it.</p>
    <p class="small">Parallel source: Henry R. Percival, translator, “The Apostolic Canons” (1899), Canon XXIX, hosted by <a href="https://apostoliki-diakonia.gr/en/the-apostolic-canons/">Apostoliki Diakonia</a>. The host identifies Percival as translator. Greek text, manuscript variants, and textual transmission were not independently collated here; treat this as a related English witness only.</p>
  </div>

  <h2>Fell’s Latin version — same printed edition</h2>
  <div class="source">
    <p>The title page says <em>cum versione Latina</em> (“with a Latin version”). On printed page 37 (PDF page 39), Fell’s Latin section contains a complete Canon XX parallel to the Geʽez-based Schodde passage.</p>
    <p><strong>Latin transcription:</strong></p>
    <blockquote><p><em>Can. XX. De eo, qui per munera ordinatus est. — Si quis episcopus aut presbyter aut diaconus dignitatem clericalem per munera adeptus fuerit: deponatur, atque deponatur etiam is, qui eum ordinaverit et in perpetuum ab administratione sacerdotii excludatur: nullamque cum eo habeant societatem, sicut Simonem Magum a me removi: ego Petrus.</em></p></blockquote>
    <p><strong>Close English rendering:</strong> “Canon XX. On one ordained through payments. If any bishop, presbyter, or deacon has obtained clerical rank through payments, let him be deposed; and let the one who ordained him also be deposed and excluded forever from administering priestly office. Let them have no association with him, just as I removed Simon Magus from me: I, Peter.”</p>
    <p><strong>Limit:</strong> this same-edition Latin parallel provides the complete rule in Latin, but it does not make the ending visible in the 1885 English scan or establish that the Latin and Ethiopic wording are exactly equivalent. Canon XX therefore remains a scan-fragment in the Schodde transcript. The Geʽez text has not yet been collated.</p>
    <p>The critical apparatus separately labels Ethiopic variants “Can. XX” on printed page 28 (PDF page 30). This confirms the corresponding canon number within Fell’s edition and supplies a locator for further comparison; the apparatus is not a complete Geʽez transcription.</p>
    <p>Internet Archive’s DjVu OCR derivative was checked as a possible text aid and rejected: the sampled Ethiopic material is misrecognized as Latin-like characters, and the file contains no Ethiopic Unicode code points. The OCR is neither bundled nor used to fill the gap. <a href="gitsew-fell-internet-archive-ocr-audit.json">View the OCR audit and checksum.</a></p>
    <p class="small"><a href="gitsew-fell-latin-canon20.json">Open transcription and translation record with provenance and method</a>.</p>
  </div>

  <h2>Publisher-described modern English text — edition not inspected</h2>
  <div class="source">
    <p>The Ethiopian Canon Project says its Gitzew / Apostolic Canons section contains 57 canons modernized from Schodde’s 1885 English translation, which Schodde identifies as translated from Geʽez. This is a publisher claim about its own work; it does not establish that the described edition has been published, that its structure matches a specific Geʽez witness, or that it is identical with a current Church edition.</p>
    <p class="small">No output text, complete edition record, accuracy review, or reuse license was inspected. No modernized wording is copied or bundled. The lead is metadata only and does not increase reader coverage.</p>
    <p class="small">Publisher article: <a href="https://www.ethiopiancanon.com/blog/the-article-that-started-this-project">The Article That Started This Project</a>. The site’s copyright notice is not a reuse license; this archive records text rights as unknown.</p>
  </div>

  <h2>Why this is linked to the Gitsew catalogue entry</h2>
  <p>Mikre-Sellassie and Cowley describe Gessew/Gitsew as a Sinodos section with a reported count of 56 or 57 canons and identify Fell’s 1871 edition as its printed witness. Schodde independently says his translation is based on Fell. This supports an attributed edition-family connection to the Church-list title Gitsew. It does not establish that this 19th-century printed text is identical to a current church edition, that all manuscript recensions share its order, or that a local transcription is complete.</p>
  <ul>
    <li><a href="https://translation.bible/wp-content/uploads/2024/06/mikre-sellassie-1993-the-bible-and-its-canon-in-the-ethiopian-orthodox-church.pdf">Mikre-Sellassie, “The Bible and its Canon in the Ethiopian Orthodox Church” (1993), pp. 119–120</a>.</li>
    <li><a href="https://www.islamic-awareness.org/bible/text/canon/ethiopican">R. W. Cowley, “The Biblical Canon of the Ethiopian Orthodox Church Today” (1974)</a>.</li>
    <li><a href="https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en">Ethiopian Orthodox Tewahedo Church English canon list</a>, which names Gitsew in the broader New Testament list.</li>
  </ul>

  <h2>Rights and verification</h2>
  <p>Both original works date from the 19th century. JSTOR says that, to its knowledge, the 1885 journal issue is in the public domain and may be used accordingly; Theological Commons marks the Fell item’s image rights “No Known Copyright.” These source-level statements are retained as public-domain claims, not as an open-license grant for unrelated editions or future translations.</p>
  <p>The scans’ bibliographic identity and article page range have been checked. All 57 printed headings in the relevant pages have been visually inventoried. The opening formula and Canons I–LVII have been transcribed against the page images, except for Canon XX, which is recorded only through the visible scan fragment. Printed page 65 ends after “from me,” and page 66 begins Canon XXI; the text layer supplies “I Peter” after that point, but those words are not visible in the scan and are not inserted. Canons XXXI, XXXVII, XLVI, LI, and LIV continue across page breaks. The article introduction and footnotes remain unproofread. <a href="https://biblicalstudies.org.uk/pdf/jbl/1885_061.pdf">A second online copy</a> was downloaded and proved byte-identical to this scan, so it is not an independent witness. No complete reader is available, and this partial transcript does not increase reader coverage. Ge’ez-English collation and reconciliation of 56/57 numbering remain open.</p>
  <p class="small">Local SHA-256 · Fell: <code>5bfc75a17cee6551153f36ba123b443dd17ce98c90aa40e9b7e8ac0115421beb</code> · Schodde: <code>419f4f9f519414a4ad10c4533478488f741d26570fbf7220240cf998d766a79a</code>.</p>
</main></body></html>
'''


def build() -> None:
    for relative in (FELL_PDF, SCHODDE_PDF):
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size < 100_000:
            raise ValueError(f"Required bundled source facsimile is missing or truncated: {relative}")
    raw_text_path = ROOT / SCHODDE_RAW_TEXT
    if not raw_text_path.is_file():
        raise ValueError(f"Missing page-labeled raw text extraction: {SCHODDE_RAW_TEXT}")
    raw_text_sha256 = hashlib.sha256(raw_text_path.read_bytes()).hexdigest()
    if raw_text_sha256 != SCHODDE_RAW_TEXT_SHA256:
        raise ValueError(f"Raw text extraction changed; review and update its provenance hash: {raw_text_sha256}")
    schodde_pdf_sha256 = hashlib.sha256((ROOT / SCHODDE_PDF).read_bytes()).hexdigest()
    if schodde_pdf_sha256 != SCHODDE_PDF_SHA256:
        raise ValueError(f"Schodde PDF changed; review the visual heading audit: {schodde_pdf_sha256}")
    progress_path = ROOT / SCHODDE_PROOFREAD_PROGRESS
    if not progress_path.is_file():
        raise ValueError(f"Missing partial proofread progress record: {SCHODDE_PROOFREAD_PROGRESS}")
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    fell_pdf_sha256 = hashlib.sha256((ROOT / FELL_PDF).read_bytes()).hexdigest()
    if fell_pdf_sha256 != FELL_LATIN_CANON20["source_sha256"]:
        raise ValueError(f"Fell PDF changed; review Latin Canon XX transcription provenance: {fell_pdf_sha256}")
    progress_numbers = [unit.get("number") for unit in progress.get("units", []) if "number" in unit]
    canon_20 = next((unit for unit in progress.get("units", []) if unit.get("number") == 20), {})
    complete_numbers = [unit.get("number") for unit in progress.get("units", []) if "number" in unit and unit.get("number") != 20]
    comparison_copy = progress.get("comparison_copy", {})
    if (
        progress.get("status") != "partial_working_transcription_not_reader"
        or progress.get("source_sha256") != schodde_pdf_sha256
        or progress.get("scope_completed", {}).get("canon_number_range_seen") != [1, 57]
        or progress.get("scope_completed", {}).get("fully_proofread_canon_ranges") != [[1, 19], [21, 57]]
        or progress.get("scope_completed", {}).get("incomplete_canons") != [20]
        or progress_numbers != list(range(1, 58))
        or complete_numbers != [*range(1, 20), *range(21, 58)]
        or canon_20.get("status") != "incomplete_scan_extent"
        or not canon_20.get("text", "").endswith("from me,")
        or "I Peter" in canon_20.get("text", "")
        or "not visible" not in canon_20.get("lacuna_note", "")
        or comparison_copy.get("sha256") != schodde_pdf_sha256
        or "not an independent witness" not in comparison_copy.get("result", "").lower()
    ):
        raise ValueError("Gitsew proofread progress must preserve the source-matched XX lacuna and the explicitly partial I–LVII transcription.")
    progress_sha256 = hashlib.sha256(progress_path.read_bytes()).hexdigest()
    _write_json(ROOT / SCHODDE_HEADING_AUDIT, _heading_audit())

    archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    existing_schodde = next(
        (item for item in archive["sources"] if item["source_id"] == SCHODDE_SOURCE_ID), None
    )
    if existing_schodde and existing_schodde.get("source_name") != (
        "JSTOR — George H. Schodde, ‘The Apostolic Canons, Translated from the Ethiopic’ (1885)"
    ):
        raise ValueError(f"Source ID collision: {SCHODDE_SOURCE_ID}")
    sources = {item["source_id"]: item for item in archive["sources"]}
    publisher_source_name = "The Ethiopian Canon Project — publisher statement on its modernized Gitzew text"
    existing_publisher_source = sources.get(PUBLISHER_SOURCE_ID)
    if existing_publisher_source and existing_publisher_source.get("source_name") != publisher_source_name:
        raise ValueError(f"Source ID collision: {PUBLISHER_SOURCE_ID}")
    sources[PUBLISHER_SOURCE_ID] = {
        "source_id": PUBLISHER_SOURCE_ID,
        "source_name": publisher_source_name,
        "url": "https://www.ethiopiancanon.com/blog/the-article-that-started-this-project",
        "local_review_url": REVIEW_HTML,
        "inspection_and_limitations": (
            "Inspected 2026-10-27. The Ethiopian Canon Project's own article describes a modern-English Gitzew / "
            "Apostolic Canons section as 57 canons modernized from George H. Schodde's 1885 English translation "
            "from Geʽez. This is a publisher statement about its own work, not independent evidence that its output "
            "has been published, that its count or structure matches a particular Geʽez witness, or that it is "
            "identical with a current Ethiopian Orthodox edition. The output text, editorial method, exact extent, "
            "translation accuracy, and reuse terms were not inspected. No text copied."
        ),
        "archive_status": "Publisher-described modernized English text; output edition and wording not inspected; metadata only",
        "rights_classification": "unknown",
        "rights_status": (
            "The page bears a 2026 copyright notice and does not grant reuse rights for the described book text. "
            "No license or permission for the modernized text was identified; its reuse status remains unknown. "
            "No text is copied or bundled."
        ),
        "rights_basis": (
            "The publisher article describes its own modernized text but does not provide a reuse license for it. "
            "The page's copyright notice is not a license. Unknown records an evidence gap, not permission or prohibition."
        ),
    }
    sources[SCHODDE_SOURCE_ID] = {
        "source_id": SCHODDE_SOURCE_ID,
        "source_name": "JSTOR — George H. Schodde, ‘The Apostolic Canons, Translated from the Ethiopic’ (1885)",
        "url": "https://www.jstor.org/stable/3268629",
        "local_review_url": REVIEW_HTML,
        "local_raw_extraction_path": SCHODDE_RAW_TEXT,
        "local_raw_extraction_sha256": raw_text_sha256,
        "local_raw_extraction_status": "unproofread PDF text-layer extraction; research aid only; not a transcription or reader",
        "local_heading_audit_url": SCHODDE_HEADING_AUDIT,
        "heading_audit_status": "57 printed headings visually inventoried; labels and page locations only; wording remains unproofread",
        "local_proofread_progress_url": SCHODDE_PROOFREAD_PROGRESS,
        "local_proofread_progress_sha256": progress_sha256,
        "proofread_progress_status": "Opening formula and Canons I–LVII transcribed against scan, except Canon XX which is only a visible fragment; partial working text, not a reader or counted toward coverage",
        "comparison_copy_url": comparison_copy["url"],
        "comparison_copy_sha256": comparison_copy["sha256"],
        "comparison_copy_result": comparison_copy["result"],
        "inspection_and_limitations": (
            "JSTOR identifies this as a free 12-page article in Journal of the Society of Biblical Literature and Exegesis "
            "5, no. 1/2 (1885), pp. 61–72. The article states that Schodde translated the Ethiopic Canons using Fell’s "
            "1871 edition, which includes a Latin version. The bundled 13-page PDF contains one repository notice followed "
            "by the 12 printed article pages. A visual audit inventories all 57 printed headings I–LVII on PDF pages 4–13 "
            "(printed pages 63–72); it verifies labels and locations only. The opening formula and Canons I–LVII except Canon XX "
            "were transcribed against the scan; Canon XX is visibly cut off after ‘from me,’ on printed page 65, and the "
            "text-layer reading ‘I Peter’ is not visible in this scan. Remaining wording has not been proofread. A "
            "page-labeled pypdf text-layer extraction is bundled as raw research "
            "data only; it is not a verified transcript or reader. A separate partial transcription of the opening formula "
            "and Canons I–LVII was visually proofread against the scan, except Canon XX which is recorded only as a visible "
            "fragment. The remaining unproofread material is the article introduction and footnotes. "
            "A second online PDF copy from biblicalstudies.org.uk was downloaded and had the same SHA-256 as the bundled scan; "
            "it is not an independent witness and does not resolve the visible Canon XX gap. "
            "The partial work is not a complete reader and does not increase reader coverage. JSTOR states that, to its knowledge, the journal issue "
            "is in the public domain and may be used accordingly. This does not establish accuracy or equivalence to every "
            "Ethiopic Sinodos manuscript or modern Church edition."
        ),
        "archive_status": "Historical English translation facsimile bundled for offline reference; no structured, proofread reader transcription",
        "rights_classification": "public_domain_claimed",
        "rights_status": (
            "JSTOR states that to its knowledge the 1885 journal issue is in the public domain and may be used accordingly. "
            "This archive records a public-domain claim for the historical article; it does not claim an open license for "
            "new editions, annotations, or other translations."
        ),
    }
    fell_source = sources["SRC-214"]
    fell_source["inspection_and_limitations"] = (
        "Theological Commons identifies Winand Fell’s Leipzig 1871 Canones Apostolorum Aethiopice as an Ethiopic/Latin "
        "edition, describes 52 pages, and labels image rights ‘No Known Copyright.’ Its linked Internet Archive scan is "
        "bundled locally (52 PDF pages; SHA-256 is recorded in the local review). The title page was visually checked; "
        "no full text transcription or collation was performed. Berkeley Lawcat describes the printed item as 47 pages; "
        "the difference from the scan-page count is recorded but not reconciled. Mikre-Sellassie and Cowley identify Fell’s "
        "edition with Gessew/Gitsew (reported as 56 or 57 canons), which supports an attributed edition-family relation, "
        "not identity with every manuscript or current Church edition. PTS image metadata is not a blanket license for "
        "other copies or derivative work."
    )
    fell_source["archive_status"] = "1871 Ethiopic/Latin edition facsimile bundled; bibliographic identity checked; text not transcribed or collated"
    fell_source["rights_classification"] = "public_domain_claimed"
    fell_source["rights_status"] = (
        "The 1871 printed work is recorded as a public-domain claim by age; Theological Commons labels its item images "
        "‘No Known Copyright.’ That statement concerns the cited scan record and does not license unrelated editions, "
        "modern translations, or newly supplied annotations."
    )
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))

    catalogue = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-084")
    catalogue["edition_or_translation"] = (
        "Winand Fell, Canones Apostolorum Aethiopice (1871; Ethiopic/Latin facsimile bundled); "
        "George H. Schodde, English translation based on Fell (1885; facsimile bundled)"
    )
    catalogue["chapter_count"] = "Schodde prints Canons I–LVII; a visual heading inventory is bundled; scholarship reports 56 or 57, depending on segmentation"
    catalogue["chapter_order_status"] = (
        "The 1885 English article preserves its printed numbering I–LVII; the local visual heading inventory verifies "
        "printed labels and page locations only. Scholarship also reports Gessew/Gitsew as "
        "56 or 57 canons. The archive retains these source counts without normalizing them."
    )
    catalogue["text_availability_status"] = (
        "Ethiopic/Latin 1871 edition and its 1885 historical English translation are bundled as local PDF facsimiles. "
        "A page-labeled, raw PDF text-layer extraction of Schodde pp. 61–72 is also bundled for search and remains unproofread. "
        "A separate working transcript covers the opening formula and Canons I–LVII, except for the scan-visible "
        "fragment of Canon XX (printed pp. 63–72); it is partial, "
        "not a complete reader, and does not increase reader coverage."
    )
    catalogue["completeness_status"] = (
        "The Schodde article covers printed Canons I–LVII on journal pages 61–72. This verifies the extent of that "
        "article only; it does not establish completeness of current Ge’ez witnesses, manuscript recensions, or a modern "
        "EOTC edition."
    )
    catalogue["rights_status"] = (
        "The bundled 1871 and 1885 historical facsimiles are treated as public-domain claimed by age; PTS says ‘No Known "
        "Copyright’ for the Fell item images, and JSTOR says that to its knowledge the 1885 issue is public domain. "
        "Neither is an open-license grant for modern editions or new translations."
    )
    catalogue["verification_date"] = "2026-10-27"
    catalogue["source_id"] = SCHODDE_SOURCE_ID
    catalogue["evidence_source_ids"] = ["SRC-029", "SRC-101", "SRC-210", "SRC-211", "SRC-214", "SRC-284", SCHODDE_SOURCE_ID]
    catalogue["reviewer_notes"] = (
        "A local visual audit inventories Schodde's 57 printed headings I–LVII and their page locations. A separate partial "
        "transcript of the opening formula and Canons I–LVII is checked against the scan, with Canon XX explicitly "
        "incomplete; the article introduction and footnotes remain unreviewed. Mikre-Sellassie (1993) reports Gessew as a 56-canon Sinodos division and cites Fell 1871 for its printed text; "
        "Cowley (1974) reports 56/57 and says Schodde translated the Ethiopic form using Fell. Schodde’s article itself "
        "uses headings through LVII. Together these sources support an attributed historical edition-family link to the "
        "Church-list Gitsew title, not identity with a current local edition. Source scans are available offline, but "
        "a raw PDF text-layer extraction is available separately for research. Structured transcription, text collation, "
        "and manuscript completeness remain unverified."
    )

    canon_book = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-30")
    canon_book["source_ids"] = sorted(set(canon_book.get("source_ids", [])) | set(catalogue["evidence_source_ids"]), key=lambda x: int(x.split("-")[1]))
    canon_book["reader_status"] = "Historical Ge’ez/Latin and English facsimiles plus a raw English text-layer extraction are bundled; partial proofread material covers Canons I–LVII except Canon XX, with Canon XX visibly incomplete; no complete reader is bundled"
    canon_book["mapping_note"] = catalogue["reviewer_notes"]
    _write_json(ROOT / "canon-registry.json", archive["canon_registry"])

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    translation_leads = {
        item["translation_id"]: item for item in registry.get("translation_leads", [])
    }
    translation_leads[PUBLISHER_LEAD_ID] = {
        "translation_id": PUBLISHER_LEAD_ID,
        "canon_id": "eotc-nt-30",
        "title": "Gitzew / Gitsew (Apostolic Canons) — publisher-described modernized English text",
        "mapping_state": "asserted_by_source",
        "scope_description": (
            "The publisher describes its Gitzew section as 57 canons modernized from Schodde's 1885 English "
            "translation, which Schodde identifies as translated from Geʽez. This reports an English-language "
            "transmission path through Schodde, not a new direct Geʽez translation. The publisher's output text, "
            "edition/publication state, detailed boundaries, accuracy, alignment to a Geʽez witness, and identity "
            "with a current Church edition have not been independently inspected."
        ),
        "language_tag": "en",
        "translator": "No individual translator identified in the cited article; publisher describes its editorial work collectively",
        "edition": "Publisher-described modernized text in a 2026 article; exact edition and publication status unverified",
        "translation_path": ["gez", "en"],
        "source_ids": ["SRC-029", SCHODDE_SOURCE_ID, PUBLISHER_SOURCE_ID],
        "text_bundled": False,
        "rights_status": (
            "Reuse rights for this modernized text are unknown. The publisher article carries a copyright notice but "
            "does not state a license for the text; do not reproduce it based on this metadata."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "Publisher claim only. The described output text, edition record, exact count, completeness, translation "
            "accuracy, and community review have not been independently checked. It is not a reader and does not "
            "increase book coverage."
        ),
        "notes": (
            "The cited publisher article says the Gitzew text modernizes Schodde 1885; Schodde's own article says "
            "his translation is from the Ethiopic. The language path is recorded as a source-reported Geʽez-to-English "
            "lineage, with the intermediate Schodde edition stated explicitly. The publisher's reported 57 canons "
            "are retained alongside the scholarly 56/57 count variation in the local review. No modernized wording copied."
        ),
    }
    registry["translation_leads"] = sorted(translation_leads.values(), key=lambda item: item["translation_id"])
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[SCHODDE_LEAD_ID] = {
        "edition_id": SCHODDE_LEAD_ID,
        "candidate_canon_id": "eotc-nt-30",
        "mapping_state": "asserted_by_source",
        "title": "Gitsew / Gessew — Ethiopic Apostolic Canons, English translation by Schodde (1885)",
        "witness_type": "printed_edition",
        "language_tag": "en",
        "language_name": "English",
        "script_code": "Latn",
        "edition_statement": (
            "George H. Schodde, ‘The Apostolic Canons, Translated from the Ethiopic,’ Journal of the Society of Biblical "
            "Literature and Exegesis 5, no. 1/2 (1885), pp. 61–72. Schodde states he used Winand Fell’s 1871 Ethiopic "
            "edition with Latin version. Local PDF facsimile bundled."
        ),
        "scope_description": (
            "The article prints the historical translation through Canons I–LVII. Mikre-Sellassie and Cowley identify "
            "Fell’s 1871 edition as the Gessew/Gitsew printed witness and report 56/57 canon counts. This is an "
            "edition-family link attributed to scholarly sources; exact equivalence to a current Church edition and "
            "manuscript boundaries is not established. A raw PDF text-layer extraction is bundled separately for research. "
            "A partial proofread transcript covers the opening formula and Canons I–LVII, except for the scan-visible "
            "fragment of Canon XX (printed pp. 63–72). It is not a complete reader. No Ge’ez-English alignment is bundled."
        ),
        "source_ids": ["SRC-029", "SRC-101", "SRC-210", "SRC-214", SCHODDE_SOURCE_ID],
        "text_bundled": False,
        "raw_extraction": {
            "path": SCHODDE_RAW_TEXT,
            "sha256": raw_text_sha256,
            "source_sha256": "419f4f9f519414a4ad10c4533478488f741d26570fbf7220240cf998d766a79a",
            "method": "pypdf 6.10.0 PageObject.extract_text(); PDF pages 2–13; no OCR or transcription correction",
            "status": "unproofread; not reader text or a verified translation",
        },
        "rights_status": (
            "JSTOR says that to its knowledge the 1885 journal issue is in the public domain and may be used accordingly. "
            "The archive bundles a historical facsimile on that public-domain claim; no open license is asserted for "
            "modern editions, translations, or annotations."
        ),
        "rights_classification": "public_domain_claimed",
        "review_status": (
            "Article authorship, publication, source edition, and printed range were inspected. The 13-page local PDF "
            "contains one repository notice and journal pages 61–72. All 57 printed headings I–LVII were visually inventoried "
            "with page locations. The opening formula and Canons I–LVII were also transcribed against the "
            "facsimile; Canon XX is incomplete, and the article introduction and footnotes remain unproofread. This partial transcript is not a complete "
            "reader. A page-labeled pypdf text-layer extraction is bundled as raw research data only; "
            "it is not a verified transcript or reader. Fell scan page count differs from printed-item catalog pagination and "
            "is retained as an unresolved bibliographic detail."
        ),
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])

    report = ROOT / REVIEW_HTML
    write_text_atomically(report, _review_html())
    _write_json(ROOT / FELL_LATIN_CANON20_PATH, FELL_LATIN_CANON20)
    _write_json(ROOT / FELL_OCR_AUDIT_PATH, FELL_OCR_AUDIT)
    _write_json(ARCHIVE_PATH, archive)
    _write_json(REGISTRY_PATH, registry)

    print("Bundled the Fell/Schodde Gitsew source pair; local source assets are cached on first access; structured reader coverage unchanged.")


if __name__ == "__main__":
    build()

