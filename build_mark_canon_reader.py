from __future__ import annotations
import json
from pathlib import Path
from archive_manifest import write_text_atomically
from build_mark_research_reader import build as extract_mark
from coverage_summary import build_coverage_statement
from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
READER_PATH = ROOT / "readers/mark-research-tei.json"
REGISTRY_PATH = ROOT / "translation-registry.json"
ARCHIVE_PATH = ROOT / "archive.json"
LAYER_PATH = ROOT / "examples/mark-research-tei-layer.json"
READER_ID = "mark-betamasaheft-tei-research"
CANON_ID = "eotc-nt-02"
SOURCE_IDS = ["SRC-029", "SRC-083", "SRC-084", "SRC-091", "SRC-092", "SRC-176"]


def main() -> None:
    raise RuntimeError("Publication blocked: Mark scripture text is withheld pending Beta maṣāḥǝft rights clarification.")
    # Reuse the pinned-source parser, then attach the record to the Church-list
    # title as a cautious candidate. This does not claim a current-edition match.
    extract_mark()
    reader = json.loads(READER_PATH.read_text(encoding="utf-8"))
    if reader.get("reader_id") != READER_ID or reader.get("source_snapshot_sha256") != "1c3682594d26bcedc425431913575a446d0cd508c78457abffae74bf7c2bfced":
        raise ValueError("Mark source identity or pinned checksum changed")
    reader.pop("research_corpus_id", None)
    reader.pop("reader_scope", None)
    reader["canon_id"] = CANON_ID
    reader["title"] = "Mark — Geʽez source transcription (Beta maṣāḥǝft TEI)"
    reader["display_name"] = "Mark · Geʽez · provisional title-level link; exact edition unverified"
    reader["edition_scope"] += " The edition-level note explicitly says ‘Text of the EOTC printed Bible’; this supports a provisional title-level link to Church-list Mark. The exact printed exemplar, current EOTC edition identity, completeness, and transcription accuracy remain unverified."
    reader["verification_status"] = "Pinned TEI extraction structurally checked: all 16 ordered chapters and 765 source line elements match the retained snapshot (678 numbered, 87 unnumbered). The edition note says ‘Text of the EOTC printed Bible’ and the Church list names Mark, supporting a provisional title-level link only. The root xml:lang=en conflict is preserved; the edition xml:lang=gez governs the text. No collation verifies wording, exact printed exemplar, completeness, or identity with a current EOTC edition."
    reader["additional_notes"] = "This reader is linked provisionally to Church-list Mark on matching work title and the TEI's EOTC printed Bible note. It is not a verified match to a specific current EOTC edition. No missing wording or viewpoints are generated."
    READER_PATH.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry["research_corpora"] = [c for c in registry.get("research_corpora", []) if c.get("reader_id") != READER_ID]
    lead = {
      "edition_id": "betamasaheft-mark-tei-edition-2025",
      "candidate_canon_id": CANON_ID,
      "mapping_state": "uncertain",
      "title": "Gospel of Mark (LIT2711Mark), Beta maṣāḥǝft TEI text",
      "witness_type": "digital_edition",
      "language_tag": "gez",
      "language_name": "Geʽez (Classical Ethiopic)",
      "script_code": "Ethi",
      "edition_statement": "Pinned Beta maṣāḥǝft LIT2711Mark TEI snapshot. The enclosing edition is explicitly tagged xml:lang=\"gez\" and its note reads ‘Text of the EOTC printed Bible’; the source says the text was digitized from modern Vulgata printed editions. The exact print exemplar is not identified.",
      "scope_description": "Provisional title-level link to Church-list Mark based on the work identity and source note. The bundled reader extracts the complete TEI edition scope inventoried here: 16 chapter divisions and 765 line elements (678 numbered, 87 unnumbered). This does not establish completeness against the unidentified print exemplar, transcription accuracy, or identity with a current EOTC edition. The TEI root xml:lang=\"en\" is retained as a document-default conflict; the enclosing edition xml:lang=\"gez\" governs the text.",
      "source_ids": SOURCE_IDS,
      "text_bundled": False,
      "bundled_reader_id": READER_ID,
      "rights_status": "The TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft and the file credits, indicate changes, and share adaptations under CC BY-SA 4.0. This item-level license is distinct from the website footer and does not establish rights in the unidentified print exemplar.",
      "rights_classification": "open_license",
      "license_id": "CC-BY-SA-4.0",
      "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
      "review_status": "Pinned TEI language, source note, file license, chapter sequence, and line extraction are structurally audited. Accuracy, exact print exemplar, physical-edition completeness, and current EOTC edition identity remain unknown. Mapping is a provisional title-level link, not a verified edition crosswalk."
    }
    registry["edition_leads"] = [e for e in registry.get("edition_leads", []) if e.get("edition_id") != lead["edition_id"]]
    registry["edition_leads"].append(lead)
    gez = next(l for l in registry["languages"] if l["language_tag"] == "gez")
    gez["records"] = [r for r in gez.get("records", []) if r.get("reader_id") != READER_ID]
    gez["records"].append({"canon_id": CANON_ID, "reader_id": READER_ID, "layer_role": "source_text_transcription", "status": "bundled", "basis_language_tag": "gez", "basis_description": "Beta maṣāḥǝft edition explicitly declares Geʽez; the root English default is preserved as a conflict. Title-level Church-list link is provisional.", "rights_status": "CC BY-SA 4.0 (file-level TEI license; print-exemplar rights not established)", "rights_classification": "open_license", "license_id": "CC-BY-SA-4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/", "source_ids": SOURCE_IDS})
    registry["research_corpora"].sort(key=lambda item: item["corpus_id"])
    registry["edition_leads"].sort(key=lambda item: item["edition_id"])
    canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    registry["coverage_statement"] = build_coverage_statement(registry, canon)
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    layer = json.loads(LAYER_PATH.read_text(encoding="utf-8"))
    layer["labels"][0]["value"] = "Mark — Geʽez source transcription; provisional Church-list title link"
    layer["tradition_assertions"][0]["mapping_state"] = "uncertain"
    layer["tradition_assertions"][0]["notes"] = "The Church list names Mark, and the pinned TEI identifies a Geʽez Gospel of Mark whose edition note says ‘Text of the EOTC printed Bible.’ The link is provisional and does not establish current-edition identity, completeness, or textual accuracy."
    LAYER_PATH.write_text(json.dumps(layer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(LAYER_PATH, READER_PATH)

    audit_path = ROOT / "readers/source/mark/SOURCE-AUDIT.md"
    audit = audit_path.read_text(encoding="utf-8")
    base_sentence = "The TEI says the text was digitized from modern Vulgata printed editions and converted to XML by the Beta maṣāḥǝft team."
    edition_note = " The edition note reads ‘Text of the EOTC printed Bible’; this is a source assertion, not independent confirmation of a current print exemplar or Church-list edition match."
    audit = audit.replace(edition_note, "")
    audit = audit.replace(base_sentence, base_sentence + edition_note, 1)
    audit = audit.replace("The research reader has no canon ID, is not claimed as a verified EOTC Mark edition, and does not raise the 81-entry canon reader count.", "The reader is linked provisionally to Church-list Mark based on the matching work title and the edition's own EOTC printed Bible note. This raises local reader availability by one, but does not verify a current EOTC edition match, print completeness, or textual accuracy.")
    audit_path.write_text(audit, encoding="utf-8")

    archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    source_updates = {
      "SRC-083": {
        "inspection_and_limitations": "Official LIT2711Mark work record identifies the Gospel of Mark as Geʽez and says it was digitized from modern Vulgata printed editions. The retained TEI root declares xml:lang=\"en\", but the enclosing text edition declares xml:lang=\"gez\" for all chapters and lines, as verified against the TEI inheritance rule and the local snapshot. Its edition note says ‘Text of the EOTC printed Bible.’ This supports a provisional title-level Church-list link, not identification of the exact print exemplar or current EOTC edition; textual accuracy and completeness remain unverified.",
        "archive_status": "Locally retained Geʽez source transcription; provisionally linked by title to Church-list Mark based on the TEI's EOTC printed Bible note. Exact current-edition identity, accuracy, and completeness remain unverified.",
      },
      "SRC-092": {
        "inspection_and_limitations": "Locally retained LIT2711Mark TEI snapshot and checksum-matched structural audit. A separate reader extracts every one of the 765 <l> elements (678 numbered, 87 unnumbered) and preserves original chapter labels and order. The enclosing edition declares xml:lang=\"gez\" for all extracted lines; the root's xml:lang=\"en\" default is preserved as a conflict. The edition note says ‘Text of the EOTC printed Bible,’ supporting a provisional title-level Church-list link. Inline markup is flattened and whitespace normalized in the display view; the unchanged TEI remains bundled. Accuracy, exact print exemplar, print completeness, and current EOTC edition identity remain unknown.",
        "archive_status": "Bundled Geʽez source transcription provisionally linked by title to Church-list Mark; structural extraction audited, while wording accuracy, print completeness, exact exemplar, and current-edition identity remain unverified.",
      },
    }
    for source in archive.get("sources", []):
      if source.get("source_id") in source_updates:
        source.update(source_updates[source["source_id"]])
    for row in archive.get("catalogue", []):
      if row.get("display_name", "").casefold() == "mark":
        row["text_availability_status"] = "A bundled Geʽez source transcription is linked provisionally by title and the TEI's EOTC printed Bible note; exact current-edition identity is unverified."
        row["reviewer_notes"] = "The Church list names Mark; the pinned Beta maṣāḥǝft TEI names the Gospel of Mark and says its Geʽez edition is text of the EOTC printed Bible. Structural extraction covers all 16 TEI chapters and 765 line elements. Textual accuracy, exact print exemplar, physical-edition completeness, and exact current-edition identity remain unknown."
        row["chapter_count"] = "16 observed TEI divisions; physical edition completeness unverified"
        row["chapter_order_status"] = "All 16 chapter divisions in the pinned TEI are ordered 1–16; this does not independently establish print completeness."
        row["completeness_status"] = "The TEI contains 765 line elements (678 numbered, 87 unnumbered); physical-edition completeness and transcription accuracy are unknown."
        row["rights_status"] = "The TEI file states CC BY-SA 4.0 for the file and adaptations; rights in the unidentified printed exemplar are not established."
        row["evidence_source_ids"] = list(dict.fromkeys(row.get("evidence_source_ids", []) + SOURCE_IDS))
    write_text_atomically(ARCHIVE_PATH, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    print("Promoted the Mark TEI reader to a provisional title-linked canon reader; exact edition and accuracy remain unverified.")

if __name__ == "__main__":
    main()
