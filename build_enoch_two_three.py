"""Register source-backed, rights-scoped records for 2 and 3 Enoch."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RECOVERY_PAGE = "research/enoch-2-3-recovery.html"
TWO_ENOCH_TEXT = "readers/source/enoch/secrets-of-enoch-morfill-1896_djvu.txt"
TWO_ENOCH_CAPTURE = "readers/source/enoch/secrets-of-enoch-morfill-1896_capture.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _recovery_page(two_sha256: str, two_size: int) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Source and rights notes for 2 Enoch and 3 Enoch, including a local OCR capture of Morfill's 1896 edition.">
  <title>2 Enoch and 3 Enoch · source recovery</title>
  <style>
    :root {{ color-scheme: light; --ink:#17372f; --muted:#53665f; --line:#d8d2c5; --paper:#fffdf8; --accent:#9a6d2e; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.65 system-ui,sans-serif; }}
    main {{ max-width:900px; margin:auto; padding:clamp(1.25rem,4vw,3rem); }} h1,h2 {{ font-family:Georgia,serif; line-height:1.2; }} h1 {{ font-size:clamp(2rem,5vw,3.25rem); }} h2 {{ margin-top:2rem; }}
    .lede,.note {{ color:var(--muted); }} .card {{ border:1px solid var(--line); background:white; padding:1rem 1.2rem; margin:1rem 0; }}
    .badge {{ display:inline-block; border:1px solid var(--line); padding:.15rem .5rem; color:var(--muted); font-size:.84rem; }} a {{ color:#07594a; }} code {{ overflow-wrap:anywhere; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:.8rem; margin:1rem 0; }} .actions a {{ border:1px solid var(--accent); padding:.65rem .9rem; text-decoration:none; }}
    footer {{ border-top:1px solid var(--line); margin-top:2rem; padding-top:1rem; color:var(--muted); }}
  </style>
</head>
<body><main>
  <p><a href="../index.html#related">← Ethiopian Bible Library</a></p>
  <h1>2 Enoch and 3 Enoch</h1>
  <p class="lede">These are separate ancient works associated with Enoch, not missing chapters of 1 Enoch. This page restores source access while distinguishing a historical OCR capture from a verified reader.</p>

  <section class="card" aria-labelledby="two-heading">
    <span class="badge">2 Enoch · Slavonic Enoch · Secrets of Enoch</span>
    <h2 id="two-heading">A local source transcription is available</h2>
    <p>The archive stores the Internet Archive OCR of <i>The Book of the Secrets of Enoch</i> (Oxford, Clarendon Press, 1896), translated from Church Slavonic by W. R. Morfill and edited by R. H. Charles. The file is the OCR of the whole scanned volume: it includes front matter and editorial material as well as the translated work.</p>
    <p><strong>This is not a verified chapter reader.</strong> OCR was captured byte-for-byte from the source item and has not been collated against the page images. OCR character errors, layout artifacts, and the edition's chapter/recension choices remain. The historical translation is not a direct translation from a newly checked Slavonic manuscript. Modern scholarship recognizes more than one recension and reports Coptic fragments; origins and textual history remain debated.</p>
    <div class="actions"><a href="../{TWO_ENOCH_TEXT}" download>Download the 1896 OCR text</a><a href="https://archive.org/details/cu31924014633568" target="_blank" rel="noopener noreferrer">Open the scanned source volume</a></div>
    <p class="note">Captured OCR: {two_size:,} bytes · SHA-256 <code>{two_sha256}</code>. The scan's front matter states that Cornell had no known U.S. copyright restrictions; this archive has not completed a territory-by-territory worldwide rights review.</p>
  </section>

  <section class="card" aria-labelledby="three-heading">
    <span class="badge">3 Enoch · Sefer Hekhalot · Hebrew Book of Enoch</span>
    <h2 id="three-heading">The 1928 edition is located; its translation is not bundled</h2>
    <p>The Internet Archive provides a digitized copy of Hugo Odeberg's <i>3 Enoch; or, The Hebrew Book of Enoch</i> (Cambridge University Press, 1928), with English translation and Hebrew text. Its catalog describes a translation with notes and a Hebrew text with critical notes, based on Odeberg's thesis; the edition identifies Bodleian MS Opp. 556 as its base manuscript.</p>
    <p>“3 Enoch” is a scholarly title; it does not appear as the work's title in the manuscripts. The work belongs to the Hebrew Hekhalot literature. The translation is under copyright in some jurisdictions, and the digitizing library says its reuse rights were not evaluated. For those reasons, this project links to the scan but does not copy or present its English text as freely reusable or universally cleared.</p>
    <div class="actions"><a href="https://archive.org/details/3enochorhebrewbo00unse" target="_blank" rel="noopener noreferrer">Read the digitized Odeberg edition</a><a href="https://www.posenlibrary.com/entry/3-enoch" target="_blank" rel="noopener noreferrer">Read the scholarly overview and licensed excerpt</a><a href="https://www.nli.org.il/en/books/NNL_ALEPH990019743350205171/NLI" target="_blank" rel="noopener noreferrer">View National Library of Israel catalog record</a></div>
  </section>

  <section>
    <h2>Canon and scope</h2>
    <p>The Ethiopian Orthodox Tewahedo Church's numbered list has an entry called “Enoch.” This archive's reviewed title match for that entry concerns <strong>1 Enoch</strong>. The list does not give separate numbered entries for 2 Enoch or 3 Enoch; this project makes no canon claim for either work. Their inclusion here is comparative textual research, not a claim that they belong to the Ethiopian Orthodox canon.</p>
    <p>“Recovered” here means the historical edition and its source trail are accessible. It does not mean lost originals have been found, every manuscript witness has been recovered, or all variants have been translated.</p>
  </section>

  <section>
    <h2>Sources and limits</h2>
    <ul>
      <li><a href="https://archive.org/details/cu31924014633568">Internet Archive / Cornell: Morfill–Charles, 1896 scan and OCR</a>.</li>
      <li><a href="https://ci.nii.ac.jp/ncid/BA65815852">CiNii Books catalog record</a>: translator, editor, date, and Slavonic source language.</li>
      <li><a href="https://www.marquette.edu/maqom/2enoch.html">Marquette University, “Slavonic Enoch”</a>: recensions and manuscript coverage; a research overview, not a new critical edition.</li>
      <li><a href="https://archive.org/details/3enochorhebrewbo00unse">Internet Archive / Princeton Theological Seminary Library: Odeberg, 1928 scan</a>; catalog metadata identifies the edition's language and manuscript basis, but reuse rights are not evaluated.</li>
      <li><a href="https://www.posenlibrary.com/entry/3-enoch">Posen Library: 3 Enoch</a>: scholarly overview; its translated excerpt is published with permission and is not reproduced here.</li>
    </ul>
  </section>
  <footer>Source status checked 2026-10-28. A citation or public scan link is not itself a reuse license. Chapter boundaries, completeness, variants, and transcription accuracy are not certified by this record.</footer>
</main></body></html>
'''


def apply(archive: dict) -> None:
    text_path = ROOT / TWO_ENOCH_TEXT
    capture_path = ROOT / TWO_ENOCH_CAPTURE
    if not text_path.is_file() or not capture_path.is_file():
        raise FileNotFoundError("The captured Morfill–Charles 1896 OCR and its capture record are required; build does not fetch external data.")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    digest = _sha256(text_path)
    if capture.get("sha256") != digest or capture.get("bytes") != text_path.stat().st_size:
        raise ValueError("2 Enoch source capture checksum or size does not match its local capture record.")

    sources = archive.setdefault("sources", [])
    sources[:] = [s for s in sources if s.get("source_id") not in {"SRC-449", "SRC-450", "SRC-451", "SRC-452"}]
    sources.extend([
        {
            "source_id": "SRC-449",
            "source_name": "Internet Archive / Cornell University Library — Morfill–Charles, The Book of the Secrets of Enoch (1896), OCR derivative",
            "url": "https://archive.org/details/cu31924014633568",
            "inspection_and_limitations": f"The source item and its DjVu-derived plain-text file were inspected and the exact OCR bytes were captured locally ({text_path.stat().st_size} bytes; SHA-256 {digest}). The captured OCR is the full scanned volume, not only the translated text. It has not been collated against scan pages, normalized, structurally verified, or reviewed for translation accuracy. Cornell scan front matter states that there are no known U.S. copyright restrictions; that notice does not settle every jurisdiction.",
            "archive_status": "Exact OCR derivative captured locally; uncollated source transcription, not a verified reader",
            "rights_classification": "public_domain_claimed",
            "rights_status": "The 1896 edition is treated as a historical public-domain source lead. The scanned volume states no known U.S. copyright restrictions. No global legal opinion is asserted; the archive has not reviewed every jurisdiction or any separate image/database terms.",
            "rights_basis": "Internet Archive item cu31924014633568, Cornell University Library scan; its front matter includes the statement ‘There are no known copyright restrictions in the United States on the use of the text.’ Translator W. R. Morfill (1834–1909) and editor R. H. Charles (1855–1931) are identified in the edition. This is evidence for a public-domain claim, not universal legal advice.",
            "local_snapshot_path": TWO_ENOCH_TEXT,
            "local_snapshot_sha256": digest,
            "local_snapshot_status": "Exact bytes of the Internet Archive OCR derivative; not scan images",
            "local_snapshot_note": "Full-volume OCR; contains editorial matter and uncorrected OCR artifacts.",
            "local_ocr_url": TWO_ENOCH_TEXT,
            "local_metadata_url": TWO_ENOCH_CAPTURE,
            "local_review_url": RECOVERY_PAGE,
        },
        {
            "source_id": "SRC-450",
            "source_name": "Internet Archive / Princeton Theological Seminary Library — Odeberg, 3 Enoch (1928) digitized edition",
            "url": "https://archive.org/details/3enochorhebrewbo00unse",
            "inspection_and_limitations": "The digitized item record identifies a 1928 Cambridge University Press edition in English and Hebrew, with translation and notes and a Hebrew text with critical notes. It identifies Bodleian MS Opp. 556 as the base manuscript. The record provides scan/text download options but says no reuse license; Princeton's Commons record marks image copyright not evaluated. The scan has not been collated here.",
            "archive_status": "External scan located; no text or images copied into this archive",
            "rights_classification": "unknown",
            "rights_status": "The digitizing library's rights state is not evaluated. Odeberg's English translation is not cleared here for worldwide redistribution. A free-to-read/download interface is not a reuse license.",
            "rights_basis": "Internet Archive catalog item 3enochorhebrewbo00unse; Princeton Theological Seminary Library Commons record https://commons.ptsem.edu/id/3enochorhebrewbo00unse states image copyright not evaluated and educational/research access. No permission to reproduce the translation was identified.",
            "local_review_url": RECOVERY_PAGE,
        },
        {
            "source_id": "SRC-451",
            "source_name": "Posen Library — 3 Enoch scholarly overview and excerpt",
            "url": "https://www.posenlibrary.com/entry/3-enoch",
            "inspection_and_limitations": "The page describes the Hebrew work in the Hekhalot corpus and notes that the designation ‘3 Enoch’ is not found in the manuscripts. Its English excerpt is credited to Philip S. Alexander and marked used with permission; it is not copied into this archive.",
            "archive_status": "Scholarly contextual source; excerpt not reproduced",
            "rights_classification": "permission_limited",
            "rights_status": "The published excerpt is used with permission on the source page. That permission does not extend to this archive; no excerpt is reproduced.",
            "rights_basis": "Source page's editorial and rights statements; consulted for context only.",
            "local_review_url": RECOVERY_PAGE,
        },
        {
            "source_id": "SRC-452",
            "source_name": "Marquette University — Slavonic Enoch manuscript and recension overview",
            "url": "https://www.marquette.edu/maqom/2enoch.html",
            "inspection_and_limitations": "The page summarizes manuscript coverage and the longer/shorter recension question for 2 Enoch, including that surviving manuscripts do not all preserve the same extent. It is a scholarly overview, not an edition or direct witness to the Morfill OCR wording.",
            "archive_status": "Contextual scholarly reference; metadata only",
            "rights_classification": "unknown",
            "rights_status": "No page-reuse license was established; no page text is copied.",
            "rights_basis": "No reuse terms were identified for this page; cited for contextual claims only.",
            "local_review_url": RECOVERY_PAGE,
        },
    ])

    related = archive.setdefault("related_texts", [])
    related[:] = [r for r in related if r.get("related_id") not in {"REL-008", "REL-009"}]
    related.extend([
        {
            "related_id": "REL-008",
            "title": "2 Enoch — The Book of the Secrets of Enoch",
            "also_known_as": "Slavonic Enoch; Second Enoch",
            "category": "Ancient Jewish pseudepigraphon preserved in Slavonic transmission",
            "not_canonical_note": "Not separately named in the Ethiopian Orthodox Tewahedo Church's numbered 81-book list. No canon mapping is asserted here; this is a comparative research record.",
            "description": "A distinct work from 1 Enoch. A historical English edition translated from Church Slavonic by W. R. Morfill and edited by R. H. Charles (Oxford, 1896) is preserved locally as exact Internet Archive OCR of the whole scanned volume. OCR is uncollated and is not presented as a verified reader. Manuscript transmission includes different recensions; Coptic fragments are also reported, and textual origins remain debated.",
            "source_ids": ["SRC-029", "SRC-449", "SRC-452"],
            "text_status": "Full-volume OCR source captured locally; not normalized, chapter-verified, or checked against scan pages",
            "rights_status": "1896 historical edition; source scan states no known U.S. copyright restrictions. This archive has not completed territory-specific rights review. OCR accuracy and textual completeness are not certified.",
            "rights_classification": "public_domain_claimed",
        },
        {
            "related_id": "REL-009",
            "title": "3 Enoch — Sefer Hekhalot",
            "also_known_as": "Hebrew Book of Enoch; Book of the Palaces",
            "category": "Jewish Hekhalot literature",
            "not_canonical_note": "Not separately named in the Ethiopian Orthodox Tewahedo Church's numbered 81-book list. No canon mapping is asserted here; this is a comparative research record.",
            "description": "A distinct Hebrew work in the Hekhalot corpus. ‘3 Enoch’ is a scholarly label, not a title found in the manuscripts. Hugo Odeberg's 1928 edition includes English translation, notes, and Hebrew text and is available as a digitized scan from Princeton/Internet Archive. That translation is not bundled because its worldwide reuse rights are not cleared.",
            "source_ids": ["SRC-029", "SRC-450", "SRC-451"],
            "text_status": "1928 digitized edition located; external source access only; no text bundled",
            "rights_status": "The digitizing library marks copyright not evaluated; the English translation is not cleared for worldwide redistribution. The linked scholarly excerpt is expressly permission-based and is not copied.",
            "rights_classification": "unknown",
        },
    ])

    (ROOT / RECOVERY_PAGE).write_text(
        _recovery_page(digest, text_path.stat().st_size), encoding="utf-8", newline="\n"
    )


def main() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    apply(archive)
    archive_path.write_text(json.dumps(archive, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Registered 2 and 3 Enoch source records; 2 Enoch OCR SHA-256: {_sha256(ROOT / TWO_ENOCH_TEXT)}")


if __name__ == "__main__":
    main()
