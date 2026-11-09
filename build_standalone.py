"""Embed lightweight archive metadata; keep complete reader text in local packages."""

from __future__ import annotations

import json
import hashlib
import re
from html.parser import HTMLParser
from copy import deepcopy
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse
from archive_manifest import enable_atomic_path_writes, verify_manifest, write_manifest, write_text_atomically
from metadata_helpers import ensure_appended_note_once
from coverage_summary import TEXT_ROLES, build_coverage_statement, validate_unit_count, validate_unit_coverage
from availability_survey import validate_availability_survey
from build_english_availability_survey import apply as apply_english_availability_survey
from build_eritrean_arabic_survey import apply as apply_eritrean_arabic_survey
from rights_metadata import reader_rights_status, validate_rights_classification
from review_metadata import validate_review_record
from reader_validation import validate_observed_unit_count
from language_code_audit import validate_iana_special_script_audit, validate_language_subtag_audit
from package_pointer import resolve_json_pointer
from book_coverage import write_book_coverage
from build_brenton_exodus import parse_chapter as parse_brenton_exodus_chapter
from build_brenton_octateuch import validate as validate_brenton_octateuch_companions
from audit_crosswire_module import build_audit as build_crosswire_module_audit
from build_normalized_graph import write_graph as write_normalized_graph
from build_review_coverage import write_review_coverage
from build_rights_coverage import write_reports as write_rights_coverage
from build_gamo_research_readers import build as build_gamo_research_readers
from build_gamo_text_layers import build as build_gamo_text_layers
from build_obadiah_reader import write as build_obadiah_reader
from build_jonah_reader import write as build_jonah_reader
from build_nahum_reader import write as build_nahum_reader
from build_habakkuk_reader import write as build_habakkuk_reader
from build_zephaniah_reader import write as build_zephaniah_reader
from build_haggai_reader import write as build_haggai_reader
from build_joel_reader import write as build_joel_reader
from build_amos_reader import write as build_amos_reader
from build_malachi_reader import write as build_malachi_reader
from build_sirach_reader import write as build_sirach_reader
from build_gamo_title_normalization import build as build_gamo_title_normalization
from build_amharic_research_readers import build as build_amharic_research_readers
from build_maale_research_readers import build as build_maale_research_readers
from build_gaz_research_readers import build as build_gaz_research_readers
from build_som_research_readers import build as build_som_research_readers
from build_lin_research_readers import build as build_lin_research_readers
from build_oyda_research_readers import build as build_oyda_research_readers
from build_yemsa_research_readers import build as build_yemsa_research_readers
from build_dawro_research_readers import build as build_dawro_research_readers
from build_baiso_research_readers import build as build_baiso_research_readers
from build_alaba_kabeena_research_readers import build as build_alaba_kabeena_research_readers


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "archive.json"
HTML_PATH = ROOT / "index.html"
INVENTORY_PATH = ROOT / "package-inventory.json"
README_PATH = ROOT / "README.md"
PLAN_PATH = ROOT / "GLOBAL-ARCHIVE-PLAN.md"
# Full per-reader notes remain in archive.json and each reader package. Keep the
# navigation shell lean by loading these long-form fields only with that reader.
DEFERRED_EMBEDDED_READER_FIELDS = (
    "front_matter",
    "rights_status",
    "copyright_notice",
    "commercial_use",
    "chapter_structure_note",
    "transcription_note",
    "editorial_signs_note",
    "source_page_hashes",
    "translation_basis_note",
    "source_book_metadata",
    "title_normalization",
    "source_pages",
    "source_path",
    "source_snapshot_sha256",
    "source_package_sha256",
    "language_assignment_status",
)
LANGUAGE_ASSIGNMENT_NOTES = {
    "en": "The cited edition/source identifies this witness as an English translation. The archive records English (en) and Latin script (Latn) as edition metadata; this does not evaluate translation accuracy or represent English varieties.",
    "gez": "The cited edition/source identifies this witness as Geʽez/Ethiopic. The archive records Geʽez (gez) and Ethiopic script (Ethi) from that edition context; this is not an independent language-specialist or recension review.",
}
SCRIPT_DISPLAY_NAMES = {
    "Arab": "Arabic script",
    "Ethi": "Ethiopic script",
    "Latn": "Latin script",
}
INVENTORY_START = "<!-- GENERATED PACKAGE INVENTORY: START -->"
INVENTORY_END = "<!-- GENERATED PACKAGE INVENTORY: END -->"
IANA_LINGALA_NOTE = (
    "The complete official 2026-09-17 registry snapshot is retained locally; its Lingala language record confirms "
    "Subtag `ln`, Description `Lingala`, and Suppress-Script `Latn`. This validates identifiers only, not script choice for all communities."
)
IANA_YEMSA_NOTE = (
    "The retained official 2026-09-17 IANA registry snapshot includes language subtag `jnj`, Description `Yemsa`. "
    "This validates the identifier only; the eBible.org edition page supplies the witness-specific language and Ethiopic-script claim."
)
IANA_BAISO_NOTE = (
    "The retained official 2026-09-17 IANA registry snapshot includes language subtag `bsw`, Description `Baiso`. "
    "This validates the language identifier only; separate eBible.org edition pages identify the script used in each bundled witness."
)
IANA_ALABA_NOTE = (
    "The retained official 2026-09-17 IANA registry snapshot includes language subtag `alw`, Description `Alaba-K’abeena`. "
    "This validates the language identifier only; the retained USFM package provides evidence for the script used in this edition."
)
EMBED_RE = re.compile(
    r'(<script id="archive-data" type="application/json">).*?(</script>)',
    re.DOTALL,
)


def build_package_inventory(archive: dict, portable_layer_records: list[dict]) -> dict:
    for source in archive.get("sources", []):
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not re.fullmatch(r"SRC-[0-9]{3}", source_id):
            raise ValueError(f"Source has an invalid source_id: {source_id!r}")
        for field in (
            "source_name", "url", "inspection_and_limitations", "archive_status", "rights_status",
        ):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f"{source_id} needs non-empty source provenance field {field}.")
        validate_rights_classification(source, f"Source {source_id}")
    canon_books = archive.get("canon_registry", {}).get("books", [])
    canon_ids = {book.get("canon_id") for book in canon_books}
    reader_records = archive.get("readers", [])
    canon_linked = sum(record.get("canon_id") in canon_ids for record in reader_records)
    canon_linked_reader_records = [record for record in reader_records if record.get("canon_id") in canon_ids]
    canon_linked_rights = dict(sorted(Counter(
        record.get("rights_classification", "unknown") for record in canon_linked_reader_records
    ).items()))
    reader_rights = dict(sorted(Counter(
        record.get("rights_classification", "unknown") for record in reader_records
    ).items()))
    source_rights = dict(sorted(Counter(
        record.get("rights_classification", "unknown") for record in archive.get("sources", [])
    ).items()))
    translation_registry = archive.get("translation_registry", {})
    reviewed_research_title_matches = sum(
        corpus.get("canon_mapping_state") == "reviewed_match"
        for corpus in translation_registry.get("research_corpora", [])
    )
    linked_canon_ids = {
        record.get("canon_id")
        for language in translation_registry.get("languages", [])
        for record in language.get("records", [])
        if record.get("status") == "bundled"
        and record.get("layer_role") in TEXT_ROLES
        and record.get("canon_id") in canon_ids
    }
    research_candidate_ids = {
        record.get("candidate_canon_id")
        for record in translation_registry.get("research_corpora", [])
        if record.get("candidate_canon_id") in canon_ids
        and record.get("reader_status") == "bundled_research_reader"
    }
    research_corpora = [
        record for record in translation_registry.get("research_corpora", [])
        if record.get("reader_status") == "bundled_research_reader"
        and record.get("candidate_canon_id") in canon_ids
    ]
    reviewed_title_entry_ids = {
        record["candidate_canon_id"] for record in research_corpora
        if record.get("canon_mapping_state") == "reviewed_match"
    } - linked_canon_ids
    source_asserted_entry_ids = {
        record["candidate_canon_id"] for record in research_corpora
        if record.get("canon_mapping_state") == "asserted_by_source"
    } - linked_canon_ids - reviewed_title_entry_ids
    provisional_entry_ids = research_candidate_ids - linked_canon_ids - reviewed_title_entry_ids - source_asserted_entry_ids
    archive_reader_ids = {record.get("reader_id") for record in reader_records}
    bundled_layer_records = [
        record
        for language in translation_registry.get("languages", [])
        for record in language.get("records", [])
        if record.get("status") == "bundled"
    ]
    missing_layer_readers = sorted(
        record.get("reader_id") or "<missing reader_id>"
        for record in bundled_layer_records
        if not record.get("reader_id") or record.get("reader_id") not in archive_reader_ids
    )
    bundled_research_corpora = [
        record for record in translation_registry.get("research_corpora", [])
        if record.get("reader_status") == "bundled_research_reader"
    ]
    standard_nt_canon_ids = {
        book.get("canon_id")
        for book in canon_books
        if book.get("section") == "New Testament"
    }
    standard_nt_canon_ids = set(sorted(standard_nt_canon_ids)[:27])
    standard_nt_research_corpora = [
        record for record in bundled_research_corpora
        if record.get("candidate_canon_id") in standard_nt_canon_ids
    ]
    standard_nt_research_state_counts = dict(sorted(Counter(
        record.get("canon_mapping_state", "unrecorded")
        for record in standard_nt_research_corpora
    ).items()))
    reader_by_id = {record.get("reader_id"): record for record in reader_records}
    standard_ot_code_pattern = re.compile(
        r"(?:::|[/#])\d+-(" + "|".join(sorted(STANDARD_OT_USFM_CROSSWALK, key=len, reverse=True)) + r")"
    )
    standard_ot_research_corpora = []
    standard_ot_module_codes = set()
    for corpus in bundled_research_corpora:
        reader = reader_by_id.get(corpus.get("reader_id"), {})
        match = standard_ot_code_pattern.search(str(reader.get("source_pages", "")))
        if match is None:
            continue
        code = match.group(1)
        candidate_canon_id = f"eotc-ot-{STANDARD_OT_USFM_CROSSWALK[code]:02d}"
        if corpus.get("candidate_canon_id") != candidate_canon_id:
            continue
        expected_state = "reviewed_match" if code in {"JOB", "1CH", "2CH"} else "uncertain"
        if (reader.get("canon_id") is not None
                or not {"SRC-029", "SRC-384"}.issubset(set(corpus.get("source_ids", [])))
                or corpus.get("canon_mapping_state") != expected_state
                or (code in {"JOB", "1CH", "2CH"} and "SRC-396" not in corpus.get("source_ids", []))):
            raise ValueError(f"Standard OT module candidate {corpus.get('corpus_id')} is not separately scoped and cited.")
        standard_ot_research_corpora.append(corpus)
        standard_ot_module_codes.add(code)
    standard_ot_research_state_counts = dict(sorted(Counter(
        record.get("canon_mapping_state", "unrecorded")
        for record in standard_ot_research_corpora
    ).items()))
    missing_research_readers = sorted(
        record.get("corpus_id", "<missing corpus_id>")
        for record in bundled_research_corpora
        if not record.get("reader_id") or record.get("reader_id") not in archive_reader_ids
    )
    if missing_layer_readers or missing_research_readers:
        raise ValueError(
            "Bundled language/corpus records point to absent archive readers: "
            f"layers={missing_layer_readers}; research={missing_research_readers}."
        )
    profiles_with_layers = {
        language.get("language_tag")
        for language in translation_registry.get("languages", [])
        if any(record.get("status") == "bundled" for record in language.get("records", []))
    }
    profiles_with_research = {
        record.get("language_tag") for record in bundled_research_corpora
    }
    language_profiles_by_tag = {
        language.get("language_tag"): language
        for language in translation_registry.get("languages", [])
    }
    research_language_script_labels = sorted({
        f"{language_profiles_by_tag[record['language_tag']]['language_name']} "
        f"({SCRIPT_DISPLAY_NAMES.get(record['script_code'], record['script_code'])})"
        for record in bundled_research_corpora
        if record.get("language_tag") in language_profiles_by_tag and record.get("script_code")
    })
    if None in profiles_with_layers or None in profiles_with_research:
        raise ValueError("Every bundled language layer and research corpus must identify its language profile.")
    if len(linked_canon_ids) != canon_linked:
        raise ValueError("Reader records and language registry disagree on canon-linked entry counts.")
    mapping_states_by_canon: dict[str, set[str]] = {}
    for layer in portable_layer_records:
        if layer.get("layer_type") not in TEXT_ROLES:
            continue
        for assertion in layer.get("tradition_assertions", []):
            if assertion.get("tradition_id", "").endswith("/tradition/eotc"):
                canon_id = assertion.get("canon_id", "").rsplit("/", 1)[-1]
                if canon_id in linked_canon_ids:
                    mapping_states_by_canon.setdefault(canon_id, set()).add(
                        assertion.get("mapping_state", "unrecorded")
                    )
    mapping_state_counts = Counter()
    for canon_id in linked_canon_ids:
        states = mapping_states_by_canon.get(canon_id, set())
        state = next(iter(states)) if len(states) == 1 else "mixed" if states else "unrecorded"
        mapping_state_counts[state] += 1
    leads = sum(
        len(translation_registry.get(key, []))
        for key in ("translation_leads", "edition_leads", "corpus_leads")
    )
    return {
        "schema_version": 1,
        "scope": "Counts describe this built package snapshot; they do not establish completeness or accuracy.",
        "catalogue_row_count": len(archive.get("catalogue", [])),
        "source_record_count": len(archive.get("sources", [])),
        "source_rights_class_counts": source_rights,
        "research_reviewed_title_match_count": reviewed_research_title_matches,
        "related_work_record_count": len(archive.get("related_texts", [])),
        "standard_nt_research": {
            "entry_count": len(standard_nt_canon_ids),
            "candidate_reader_record_count": len(standard_nt_research_corpora),
            "mapping_state_counts": standard_nt_research_state_counts,
            "language_tag_count": len({record.get("language_tag") for record in standard_nt_research_corpora}),
            "scope_note": "Bundled standard-New-Testament research modules linked by work/title candidates; not canon-linked coverage, edition equivalence, accuracy, or completeness.",
        },
        "standard_ot_research": {
            "entry_count": len({record.get("candidate_canon_id") for record in standard_ot_research_corpora}),
            "candidate_reader_record_count": len(standard_ot_research_corpora),
            "module_code_count": len(standard_ot_module_codes),
            "mapping_state_counts": standard_ot_research_state_counts,
            "language_tag_count": len({record.get("language_tag") for record in standard_ot_research_corpora}),
            "source_ids": ["SRC-029", "SRC-384", "SRC-396"],
            "scope_note": "Standard Old Testament USFM module links are research-only: Job and Chronicles modules have reviewed work/title matches based on the Church list and official USFM identifiers; the remaining links are uncertain title candidates. Reviewed title matches do not establish EOTC/Eritrean affiliation, edition identity, textual boundaries, completeness, or accuracy.",
        },
        "church_list": {
            "entry_count": len(canon_books),
            "old_testament_entry_count": sum(book.get("section") == "Old Testament" for book in canon_books),
            "new_testament_entry_count": sum(book.get("section") == "New Testament" for book in canon_books),
            "canon_linked_reader_entry_count": len(linked_canon_ids),
            "research_candidate_entry_count": len(research_candidate_ids - linked_canon_ids),
            "research_reviewed_title_match_entry_count": len(reviewed_title_entry_ids),
            "research_source_asserted_title_entry_count": len(source_asserted_entry_ids),
            "research_provisional_title_candidate_entry_count": len(provisional_entry_ids),
            "entries_with_neither_local_reader_count": len(canon_ids - linked_canon_ids - research_candidate_ids),
            "reader_mapping_state_counts": {
                state: mapping_state_counts[state]
                for state in ("reviewed_match", "asserted_by_source", "uncertain", "related_work", "not_mapped", "mixed", "unrecorded")
            },
            "mapping_scope_note": "Mapping state is evidence classification, not a completeness or accuracy score. A reviewed match here means a scoped work/title comparison against cited records, not scholarly peer review, edition identity, text collation, completeness, or accuracy.",
        },
        "reader_records": {
            "total": len(reader_records),
            "canon_linked": canon_linked,
            "research_only": len(reader_records) - canon_linked,
            "rights_class_counts": reader_rights,
            "canon_linked_rights_class_counts": canon_linked_rights,
            "scope_note": "Canon links are archive mappings, not certifications of edition identity, completeness, or textual accuracy.",
        },
        "language_script_profile_count": len(translation_registry.get("languages", [])),
        "language_profile_content_counts": {
            "with_registered_bundled_layers": len(profiles_with_layers),
            "with_bundled_research_readers": len(profiles_with_research),
            "with_any_bundled_text": len(profiles_with_layers | profiles_with_research),
            "bundled_research_language_script_pair_count": len(research_language_script_labels),
            "bundled_research_language_script_labels": research_language_script_labels,
            "scope_note": "A profile is a language/script metadata record; the total profile count is not a count of languages with bundled text.",
        },
        "research_translation_provenance": {
            "text_origin_counts": dict(sorted(Counter(
                record.get("text_origin", "unrecorded") for record in bundled_research_corpora
            ).items())),
            "published_translation_basis_counts": dict(sorted(Counter(
                record.get("translation_basis_status", "unrecorded")
                for record in bundled_research_corpora
                if record.get("text_origin") == "published_translation"
            ).items())),
            "scope_note": "These are corpus metadata states. An established basis path means cited evidence identifies a source-language path; it does not certify translator workflow, wording accuracy, completeness, or community review. Unknown means the path is not established in this archive, not that no translation exists.",
        },
        "portable_text_layer_count": len(portable_layer_records),
        "rights_withheld_text_record_count": len(archive.get("rights_withheld_texts", [])),
        "unbundled_lead_count": leads,
    }


def render_package_inventory(inventory: dict) -> str:
    canon = inventory["church_list"]
    readers = inventory["reader_records"]
    translation_provenance = inventory["research_translation_provenance"]
    rows = [
        ("Catalogue rows", inventory["catalogue_row_count"], "Catalogue records; not all represent distinct canon entries."),
        ("Source records", inventory["source_record_count"], "Evidence and provenance records."),
        ("Source rights: unknown", inventory["source_rights_class_counts"].get("unknown", 0), "Source-level reuse permission is not established; a citation is not a license."),
        ("Source rights: public domain claimed", inventory["source_rights_class_counts"].get("public_domain_claimed", 0), "Provider or record claim; not a worldwide legal conclusion."),
        ("Source rights: permission limited", inventory["source_rights_class_counts"].get("permission_limited", 0), "Recorded restrictions apply; consult the item-specific terms."),
        ("Source rights: all rights reserved", inventory["source_rights_class_counts"].get("all_rights_reserved", 0), "Source-record notice; does not replace reader-level rights records."),
        ("Source rights: open license", inventory["source_rights_class_counts"].get("open_license", 0), "Recorded source-level open license; confirm its item and content scope."),
        ("Source rights: mixed", inventory["source_rights_class_counts"].get("mixed", 0), "Conflicting or mixed notices; follow the linked review and item-specific terms."),
        ("Related-work records", inventory["related_work_record_count"], "Separate from Church-list entries."),
        ("Church-list entries", canon["entry_count"], f"{canon['old_testament_entry_count']} Old Testament; {canon['new_testament_entry_count']} New Testament."),
        ("Church-list entries without canon-linked reader", canon["entry_count"] - canon["canon_linked_reader_entry_count"], "Local absence only; external availability not implied."),
        ("Of these: with unlinked research reader", canon["research_candidate_entry_count"], "These readers remain separate from canon-linked coverage; mapping status is broken out below."),
        ("Of these: research reader with reviewed work/title match", canon["research_reviewed_title_match_entry_count"], "Work/title mapping only; tradition affiliation, exact edition, completeness, and accuracy remain separate."),
        ("Of these: research reader with source-asserted title link", canon["research_source_asserted_title_entry_count"], "A cited source makes the link; the archive has not independently reviewed it."),
        ("Of these: research reader with provisional title candidate", canon["research_provisional_title_candidate_entry_count"], "The title mapping remains unverified."),
        ("Of these: with neither local reader type", canon["entries_with_neither_local_reader_count"], "External availability is not inferred."),
        ("Canon-linked reader records", readers["canon_linked"], readers["scope_note"]),
        ("Canon-linked reader rights: open license", readers["canon_linked_rights_class_counts"].get("open_license", 0), "Reader's recorded open license applies; check its conditions."),
        ("Canon-linked reader rights: permission limited", readers["canon_linked_rights_class_counts"].get("permission_limited", 0), "Notice-bound terms; not an open license. Follow each reader's notice."),
        ("Canon-linked reader rights: public domain claimed", readers["canon_linked_rights_class_counts"].get("public_domain_claimed", 0), "Provider claim; not a worldwide legal conclusion."),
        ("Canon-linked entries with reviewed work/title match", canon["reader_mapping_state_counts"]["reviewed_match"], canon["mapping_scope_note"]),
        ("Canon-linked entries with source-asserted mapping", canon["reader_mapping_state_counts"]["asserted_by_source"], canon["mapping_scope_note"]),
        ("Canon-linked entries with uncertain mapping", canon["reader_mapping_state_counts"]["uncertain"], canon["mapping_scope_note"]),
        ("Research-only reader records", readers["research_only"], "Not counted as Church-list book coverage."),
        ("Research reader records with reviewed work/title mapping", inventory["research_reviewed_title_match_count"], "Title crosswalk only; edition/tradition identity, completeness, and textual accuracy remain separate questions."),
        ("Reader records total", readers["total"], "Withheld texts are excluded."),
        ("Standard New Testament research candidates", inventory["standard_nt_research"]["candidate_reader_record_count"], inventory["standard_nt_research"]["scope_note"]),
        ("Standard Old Testament research candidates", inventory["standard_ot_research"]["candidate_reader_record_count"], inventory["standard_ot_research"]["scope_note"]),
        ("Reader rights classification: open license", readers["rights_class_counts"].get("open_license", 0), "Recorded license applies; check its conditions."),
        ("Reader rights classification: permission limited", readers["rights_class_counts"].get("permission_limited", 0), "Notice-bound terms; not an open license."),
        ("Reader rights classification: public domain claimed", readers["rights_class_counts"].get("public_domain_claimed", 0), "Provider claim; not a worldwide legal conclusion."),
        ("Language/script profiles", inventory["language_script_profile_count"], "Scoped metadata profiles; not all profiles have bundled text."),
        ("Profiles with registered bundled source/translation layers", inventory["language_profile_content_counts"]["with_registered_bundled_layers"], "Currently Geʽez source text and English historical companions; not comprehensive language coverage."),
        ("Profiles with bundled research readers", inventory["language_profile_content_counts"]["with_bundled_research_readers"], f"Research-only readers represent {inventory['language_profile_content_counts']['bundled_research_language_script_pair_count']} language/script pairs: " + ", ".join(inventory["language_profile_content_counts"]["bundled_research_language_script_labels"]) + "; not counted as canon-linked coverage."),
        ("Research readers marked as published translations", translation_provenance["text_origin_counts"].get("published_translation", 0), "Corpus text-origin label; not a completeness or translation-quality claim."),
        ("Research readers marked as source transcriptions", inventory["research_translation_provenance"]["text_origin_counts"].get("source_transcription", 0), "Text-origin classification from each research-corpus record; it does not establish textual accuracy or completeness."),
        ("Published translation basis: evidence identifies a path", translation_provenance["published_translation_basis_counts"].get("established", 0), "Cited evidence identifies the source-language path; this does not verify translator workflow, wording accuracy, completeness, or community review."),
        ("Published translation basis: unknown in archive", translation_provenance["published_translation_basis_counts"].get("unknown", 0), "Available evidence does not establish the path; this does not mean the text is untranslated."),
        ("Portable text layers", inventory["portable_text_layer_count"], "Selected layers; not complete canon or language coverage."),
        ("Rights-withheld text records", inventory["rights_withheld_text_record_count"], "Metadata only; text is not bundled."),
        ("Unbundled discovery leads", inventory["unbundled_lead_count"], "Translation, source-edition, or corpus leads."),
    ]
    lines = [INVENTORY_START, "| Snapshot measure | Count | Scope |", "|---|---:|---|"]
    lines.extend(f"| {name} | {count} | {scope} |" for name, count, scope in rows)
    lines.extend([
        "",
        f"The {readers['research_only']} separately scoped research readers remain outside canon-linked coverage.",
        f"All {inventory['language_script_profile_count']} registered language profiles now have bounded provider-page survey records.",
        f"This snapshot documents all {readers['total']} current reader records ({readers['canon_linked']} canon-linked and {readers['research_only']} research-only).",
        "",
        "[Download this inventory as JSON](package-inventory.json).",
        "",
        inventory["scope"],
        INVENTORY_END,
    ])
    return "\n".join(lines)


def write_package_inventory(archive: dict, portable_layer_records: list[dict]) -> dict:
    inventory = build_package_inventory(archive, portable_layer_records)
    write_text_atomically(INVENTORY_PATH, json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
    snapshot_date = date.today().isoformat()
    readme = README_PATH.read_text(encoding="utf-8")
    readme, date_replacements = re.subn(
        r"## Current package status \(\d{4}-\d{2}-\d{2}\)",
        f"## Current package status ({snapshot_date})",
        readme,
        count=1,
    )
    if date_replacements != 1:
        raise ValueError("README.md must contain exactly one dated current package status heading.")
    pattern = re.compile(re.escape(INVENTORY_START) + r".*?" + re.escape(INVENTORY_END), re.DOTALL)
    readme, replacements = pattern.subn(render_package_inventory(inventory), readme)
    if replacements != 1:
        raise ValueError("README.md must contain exactly one generated package inventory block.")
    write_text_atomically(README_PATH, readme)

    plan = PLAN_PATH.read_text(encoding="utf-8")
    readers = inventory["reader_records"]
    nt_research = inventory["standard_nt_research"]
    nt_states = nt_research["mapping_state_counts"]
    nt_research_summary = (
        f"Across the {nt_research['entry_count']} standard New Testament work titles, "
        f"{nt_research['candidate_reader_record_count']} bundled research-reader records are indexed as work/title candidates "
        f"({nt_states.get('reviewed_match', 0)} reviewed title matches, "
        f"{nt_states.get('uncertain', 0)} provisional candidates, "
        f"{nt_research['language_tag_count']} language tags)."
    )
    ot_research = inventory["standard_ot_research"]
    ot_states = ot_research["mapping_state_counts"]
    ot_research_summary = (
        f"For standard Old Testament USFM modules, {ot_research['candidate_reader_record_count']} bundled research-reader records "
        f"are indexed ({ot_states.get('reviewed_match', 0)} reviewed work/title matches, "
        f"{ot_states.get('uncertain', 0)} uncertain title candidates) across {ot_research['entry_count']} Church-list entries, "
        f"{ot_research['module_code_count']} module codes, and {ot_research['language_tag_count']} language tags."
    )
    snapshot = (
        f"Current package snapshot ({snapshot_date}): the local standalone build has {readers['total']} reader records "
        f"({readers['canon_linked']} canon-linked and {readers['research_only']} research-only), "
        f"{inventory['catalogue_row_count']} catalogue entries, {inventory['source_record_count']} source records. "
        f"It links {inventory['church_list']['canon_linked_reader_entry_count']} of the Church list’s "
        f"{inventory['church_list']['entry_count']} entries to canon-linked readers; "
        f"{inventory['church_list']['research_candidate_entry_count']} further entries have bundled research candidates and "
        f"{inventory['church_list']['entries_with_neither_local_reader_count']} have neither reader type locally. "
        f"{nt_research_summary} {ot_research_summary} The archive-authored title candidates do not identify a text as an EOTC/Eritrean edition or verify translation ancestry, boundaries, completeness, or accuracy. "
        "These are package counts, not estimates of worldwide availability."
    )
    plan, snapshot_replacements = re.subn(
        r"Current package snapshot \(\d{4}-\d{2}-\d{2}\):[^\n]*",
        snapshot,
        plan,
        count=1,
    )
    current_inventory = (
        f"Current package inventory: {inventory['catalogue_row_count']} catalogue rows, "
        f"{inventory['source_record_count']} source records, and {readers['total']} readers "
        f"({readers['canon_linked']} canon-linked; {readers['research_only']} research-only)."
    )
    plan, inventory_replacements = re.subn(
        r"Current package inventory: [^\n.]*\.",
        current_inventory,
        plan,
        count=1,
    )
    if snapshot_replacements != 1 or inventory_replacements != 1:
        raise ValueError("GLOBAL-ARCHIVE-PLAN.md must have exactly one current snapshot and inventory line.")
    write_text_atomically(PLAN_PATH, plan)
    return inventory


def validate_offline_shell() -> int:
    """Validate the install shell and the assets cached when opened."""
    service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
    def listed_paths(name: str) -> list[str]:
        match = re.search(rf"const {name}\s*=\s*\[(.*?)\];", service_worker, re.DOTALL)
        if not match:
            raise ValueError(f"Service worker has no recognizable {name} path list.")
        return re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))

    precache_paths = listed_paths("PRECACHE_PATHS")
    paths = precache_paths
    if len(paths) != len(set(paths)):
        raise ValueError("Offline precache path list contains duplicate entries.")
    required_precache = {
        "index.html", "offline.html", "styles.css", "app.js", "offline-reader-cache.js", "reader-package.js",
        "reader-alignment.js", "manifest.webmanifest", "archive-manifest.json",
        "schemas/source-record.schema.json",
        "schemas/reader-package.schema.json", "schemas/text-layer.schema.json",
        "schemas/book-coverage.schema.json",
        "examples/review-coverage.json", "research/tegsats-source-review.md",
        "research/source-encoding-audit.md",
        "research/source-encoding-audit.html",
        "research/source-encoding-audit.json",
        "readers/source/amos-tau-2009/SOURCE-CAPTURE.json",
        "readers/source/amos-tau-2009/amos-information.html",
        "readers/source/amos-tau-2009/amos-information.utf8.html",
        "readers/source/obadiah-tau-2010/SOURCE-CAPTURE.json",
        "readers/source/obadiah-tau-2010/obadiah-information.html",
        "readers/source/obadiah-tau-2010/obadiah-information.utf8.html",
        "readers/source/sirach-tau-2026/SOURCE-CAPTURE.json",
        "readers/source/sirach-tau-2026/apocryphi-information.html",
        "readers/source/sirach-tau-2026/apocryphi-information.utf8.html",
        "readers/source/sirach-tau-2026/sirach-information.html",
        "readers/source/sirach-tau-2026/sirach-information.utf8.html",
        "readers/source/tau-platt-nt-menu/SOURCE-CAPTURE.json",
        "readers/source/tau-platt-nt-menu/nt-information.html",
        "readers/source/tau-platt-nt-menu/nt-information.utf8.html",

        "research/genesis-1-divine-person-lens.html",
        "research/rights-coverage.html", "examples/rights-coverage.json",
        "readers/source/alaba-kabeena/alw-copyright.html",
        "readers/source/tegsats-bl-add-ms-16186/capture-manifest.json",
        "readers/source/tegsats-bl-add-ms-16186/iiif-manifest.json",
        "assets/icon-192.png", "assets/icon-512.png",
        "assets/apple-touch-icon.png",
    }
    missing = required_precache - set(precache_paths)
    if missing:
        raise ValueError(f"Offline install shell omits required files: {', '.join(sorted(missing))}.")
    large_files = {
        "examples/portable-text-layers.json",
        "translation-registry.json",
        "book-coverage.json",
        "examples/archive-graph-registered-layers.json",
        "research/didascalia-harden1920-chapter-heading-audit.json",
        "research/didascalia-harden1920-ocr-reader.html",
        "research/josephas-source-review.md",
        "research/gitsew-source-review.md",
        "research/gitsew-fell-schodde-translation.html",
        "research/gitsew-schodde-1885-raw-extract.txt",
        "research/enoch-charles-1917-source.html",
        "readers/source/enoch/charles-1917-gutenberg-77935.txt",
        "readers/source/enoch/secrets-of-enoch-morfill-1896_djvu.txt",
        "readers/source/enoch/secrets-of-enoch-morfill-1896_capture.json",
        "readers/source/gitsew/Canones-Apostolorum-Aethiopice-Fell-1871.pdf",
        "readers/source/gitsew/The-Apostolic-Canons-Schodde-1885.pdf",
        "schemas/didascalia-heading-audit.schema.json",
        "research/eritrea-eotc-label-comparison.html",
        "research/tigrinya-open-text-index-audit.md",
        "research/tigrinya-eritrean-church-edition.md",
        "research/eritrea-eotc-label-comparison.json",
        "schemas/eritrea-canon-label-comparison.schema.json",
        "readers/source/bilin-mark-1890/Bilin-1890-Mark.pdf",
        "readers/source/didascalia-platt1834/internet-archive-djvu.xml",
        "readers/source/world-english-bible-british/capture-manifest.json",
        "readers/source/world-english-bible-british/eng-webbe_usfm.zip",
    }
    mistakenly_precached = large_files & set(precache_paths)
    if mistakenly_precached:
        raise ValueError(f"Large research files must not inflate first-install storage: {', '.join(sorted(mistakenly_precached))}.")
    for relative_path in paths:
        local_path = Path(relative_path)
        if local_path.is_absolute() or ".." in local_path.parts or not (ROOT / local_path).is_file():
            raise ValueError(f"Offline cache path is not a present, local file: {relative_path}.")
    if "if (relativePath)" not in service_worker or "await cache.put(request, response.clone())" not in service_worker:
        raise ValueError("Service worker must cache successful same-origin archive files on first access.")
    if "event.data?.type !== 'CHECK_OFFLINE_READER'" not in service_worker or "reader_available" not in service_worker:
        raise ValueError("Service worker must report whether the selected local reader package is cached.")
    if "new URL(request.url).origin !== SITE_BASE.origin" not in service_worker:
        raise ValueError("Service worker must limit intercepted requests to the site's own origin.")
    if "request.mode === 'navigate'" not in service_worker or "OFFLINE_URL" not in service_worker or "matchAcrossCaches(INDEX_URL)" not in service_worker:
        raise ValueError("Service worker navigation handler must provide cached index and offline-page fallbacks.")
    if "smallShellFiles = PRECACHE_FILES.filter(url => url !== INDEX_URL)" not in service_worker:
        raise ValueError("The large index must be cached separately so storage failure does not block service-worker installation.")
    if "await cache.addAll(smallShellFiles)" not in service_worker or "await cache.put(INDEX_URL, response.clone())" not in service_worker:
        raise ValueError("Service worker must pre-cache the small shell and cache the lightweight app page.")
    if not re.search(r"isBundledReaderPackage\s*=\s*/\^readers", service_worker):
        raise ValueError("Service worker must cache reader JSON packages on demand.")
    app_script = (ROOT / "app.js").read_text(encoding="utf-8")
    html = HTML_PATH.read_text(encoding="utf-8")
    class LocalAssetParser(HTMLParser):
        """Collect page URLs without treating cited external links as dependencies."""

        def __init__(self):
            super().__init__()
            self.ids = set()
            self.references = []

        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if values.get("id"):
                self.ids.add(values["id"])
            rel = set(values.get("rel", "").lower().split())
            for attribute in ("src", "href", "poster", "data"):
                value = values.get(attribute)
                if value:
                    self.references.append((tag, attribute, value, rel))

    asset_parser = LocalAssetParser()
    asset_parser.feed(html)
    site_root = ROOT.resolve()
    for tag, attribute, value, rel in asset_parser.references:
        parsed = urlparse(value)
        if parsed.scheme or parsed.netloc:
            if tag != "a" and attribute in {"src", "href", "poster", "data"}:
                raise ValueError(
                    f"The offline page must not depend on an external {tag} asset: {value}"
                )
            continue  # External anchors are citations, not page dependencies.
        if not parsed.path:
            if parsed.fragment and parsed.fragment not in asset_parser.ids:
                raise ValueError(f"The page links to a missing in-page section: #{parsed.fragment}.")
            continue
        local_asset = (ROOT / unquote(parsed.path.lstrip("/"))).resolve()
        if not local_asset.is_relative_to(site_root) or not local_asset.is_file():
            raise ValueError(f"The page refers to a missing or out-of-site local asset: {value}")
    stylesheet = (ROOT / "styles.css").read_text(encoding="utf-8")
    external_css_assets = re.findall(
        r"(?:url\(\s*|@import\s+)[\"']?(https?://[^\s\"')]+)", stylesheet, re.IGNORECASE
    )
    if external_css_assets:
        raise ValueError(f"The offline stylesheet depends on external assets: {sorted(set(external_css_assets))}.")
    if not re.search(r"fetch\(path,\s*\{\s*credentials:\s*'same-origin'\s*\}\)", app_script):
        raise ValueError("Application code must load selected reader text from its same-site package.")
    if "readerMetadata.reader_data_url" not in app_script or "state.activeReaderData = reader;" not in app_script:
        raise ValueError("Application code must validate and retain only the selected local reader package.")
    if "renderReader({ loadText: false })" not in app_script or 'id="reader-open"' not in html:
        raise ValueError("The initial page must defer reader text loading until a person opens a text.")
    if re.search(r"\bXMLHttpRequest\b|\bWebSocket\b", app_script):
        raise ValueError("Application code must not use unrestricted data channels.")
    if 'id="offline-status"' not in html or "CHECK_OFFLINE_READER" not in app_script:
        raise ValueError("The reader must show device-specific offline-cache status.")
    if not re.search(r'<a\s+id="archive-export"\s+href="archive\.json"\s+download\b', html):
        raise ValueError("The archive export must retain its local JSON fallback link.")
    if not re.search(r'<a\s+href="archive-manifest\.json"\s+download\b', html):
        raise ValueError("The archive checksum manifest must be downloadable from the page.")
    if 'href="research/review-coverage.html"' not in html:
        raise ValueError("The homepage must link to the generated review coverage report.")
    if 'href="examples/review-coverage.json"' not in html:
        raise ValueError("The homepage must link to the machine-readable review summary.")
    if 'href="research/rights-coverage.html"' not in html:
        raise ValueError("The homepage must link to the generated rights coverage report.")
    if 'href="examples/rights-coverage.json"' not in html:
        raise ValueError("The homepage must link to the machine-readable rights coverage summary.")
    if 'href="research/gamo-maale-provenance.html"' not in html:
        raise ValueError("The homepage must link to the Gamo and Maale translation-provenance audit.")
    if not re.search(r'<button[^>]+id="reader-download"', html) or "window.ReaderPackage.createReaderPackage" not in app_script:
        raise ValueError("The reader must offer its locally generated, provenance-bearing JSON export.")
    package_schema = json.loads((ROOT / "schemas" / "reader-package.schema.json").read_text(encoding="utf-8"))
    if package_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or package_schema.get("$id") != "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/schemas/reader-package.schema.json":
        raise ValueError("Reader package schema must use the published JSON Schema 2020-12 identifier.")
    if not re.search(r'<a\s+id="archive-export"\s+href="archive\.json"\s+download\b', html):
        raise ValueError("The complete archive JSON must remain downloadable as a separate, on-demand package.")
    return len(paths)


def require_unique(items: list[dict], field: str, label: str) -> set[str]:
    values = [item.get(field) for item in items]
    if any(not value for value in values):
        raise ValueError(f"Every {label} needs a {field}.")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {field} in {label}.")
    return set(values)


def validate_source_urls(sources: list[dict]) -> None:
    site_root = ROOT.resolve()
    for source in sources:
        value = source.get("url")
        if not isinstance(value, str) or not value:
            raise ValueError(f"{source.get('source_id')} needs a source URL.")
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"}:
            if parsed.scheme != "https":
                raise ValueError(f"{source['source_id']} uses an insecure external URL; source links must use HTTPS: {value}")
            if not parsed.netloc:
                raise ValueError(f"{source['source_id']} has an incomplete external URL: {value}")
            continue
        if parsed.scheme or parsed.netloc:
            raise ValueError(f"{source['source_id']} uses an unsupported URL scheme: {value}")
        if not parsed.path:
            if parsed.fragment:
                continue  # In-page references may target IDs generated by app.js.
            raise ValueError(f"{source['source_id']} has an empty relative URL.")
        local_path = (ROOT / unquote(parsed.path)).resolve()
        if not local_path.is_relative_to(site_root) or not local_path.is_file():
            raise ValueError(f"{source['source_id']} points to a missing or out-of-site file: {value}")


def validate_source_record_metadata(sources: list[dict]) -> None:
    """Require source entries to explain their inspection limits and archive role."""
    required_fields = (
        "source_id", "source_name", "url", "inspection_and_limitations", "archive_status",
        "rights_classification", "rights_status", "rights_basis",
    )
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Source record {index + 1} must be an object.")
        source_label = source.get("source_id", f"Source record {index + 1}")
        for field in required_fields:
            value = source.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{source_label} needs a nonempty {field} field.")
        validate_rights_classification(source, f"Source {source_label}")
        for field, local_url in source.items():
            if not (field.startswith("local_") and field.endswith("_url")):
                continue
            if not isinstance(local_url, str) or not local_url.strip():
                raise ValueError(f"{source_label} {field} must be a nonempty relative path.")
            parsed = urlparse(local_url)
            relative = Path(unquote(parsed.path))
            if (parsed.scheme or parsed.netloc or relative.is_absolute() or ".." in relative.parts
                    or not (ROOT / relative).is_file()):
                raise ValueError(f"{source_label} {field} must point to a present in-package file: {local_url}")
        full_view_url = source.get("full_view_url")
        if full_view_url is not None:
            parsed = urlparse(full_view_url) if isinstance(full_view_url, str) else None
            if (parsed is None or parsed.scheme != "https" or not parsed.netloc
                    or parsed.username or parsed.password):
                raise ValueError(f"{source_label} full_view_url must be a safe absolute HTTPS URL.")


def validate_local_source_snapshots(sources: list[dict]) -> None:
    """Verify retained source bytes and any capture-manifest linkage."""
    site_root = ROOT.resolve()
    required = ("local_snapshot_path", "local_snapshot_sha256", "local_snapshot_status", "local_snapshot_note")

    def local_file(source_id: str, field: str, value: object) -> tuple[Path, str]:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{source_id} {field} must be a nonempty package-relative path.")
        parsed = urlparse(value)
        relative = Path(unquote(parsed.path))
        if (parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
                or relative.is_absolute() or ".." in relative.parts):
            raise ValueError(f"{source_id} {field} must be a safe package-relative path: {value}")
        target = (site_root / relative).resolve()
        if not target.is_relative_to(site_root) or not target.is_file():
            raise ValueError(f"{source_id} {field} points to a missing or out-of-package file: {value}")
        return target, relative.as_posix()

    for source in sources:
        source_id = source.get("source_id", "unknown source")
        present = [field for field in required if field in source]
        if present and len(present) != len(required):
            missing = sorted(set(required) - set(present))
            raise ValueError(f"{source_id} has incomplete source snapshot provenance; missing {', '.join(missing)}.")
        if not present:
            if "local_capture_manifest_url" in source:
                raise ValueError(f"{source_id} has a capture manifest but no local source snapshot.")
            continue

        snapshot, snapshot_relative = local_file(source_id, "local_snapshot_path", source["local_snapshot_path"])
        expected_hash = source.get("local_snapshot_sha256")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_hash):
            raise ValueError(f"{source_id} local_snapshot_sha256 must be a lowercase SHA-256 digest.")
        actual_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"{source_id} local snapshot hash mismatch: {snapshot_relative}")
        for field in ("local_snapshot_status", "local_snapshot_note"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f"{source_id} needs a nonempty {field}.")

        manifest_value = source.get("local_capture_manifest_url")
        if manifest_value is None:
            continue  # Some local source renditions have no separate HTTP capture manifest.
        manifest_path, manifest_relative = local_file(source_id, "local_capture_manifest_url", manifest_value)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"{source_id} capture manifest is unreadable: {manifest_relative}: {error}") from error
        entries = manifest.get("files") if isinstance(manifest, dict) else None
        if not isinstance(entries, list):
            raise ValueError(f"{source_id} capture manifest has no files list: {manifest_relative}")
        manifest_root = manifest_path.parent.resolve()
        matches = []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                continue
            entry_path = Path(entry["path"])
            if entry_path.is_absolute() or ".." in entry_path.parts:
                raise ValueError(f"{source_id} capture manifest contains an unsafe path: {entry.get('path')}")
            resolved_entry = (manifest_root / entry_path).resolve()
            if resolved_entry == snapshot:
                matches.append(entry)
        if len(matches) != 1:
            raise ValueError(f"{source_id} capture manifest does not identify exactly one retained snapshot: {snapshot_relative}")
        entry = matches[0]
        if entry.get("sha256") != expected_hash or entry.get("size_bytes") != snapshot.stat().st_size:
            raise ValueError(f"{source_id} capture manifest does not authenticate retained bytes: {snapshot_relative}")

def mark_unassessed_source_rights(sources: list[dict]) -> None:
    """Record missing source-level reuse assessments and their evidence limits."""
    for source in sources:
        if not isinstance(source, dict):
            continue  # The record validator will report the malformed entry.
        classification = source.get("rights_classification")
        if not isinstance(classification, str) or not classification.strip():
            source["rights_classification"] = "unknown"
            classification = "unknown"
        if not isinstance(source.get("rights_status"), str) or not source["rights_status"].strip():
            if classification == "unknown":
                source["rights_status"] = (
                    "Source-level reuse terms have not been classified for this record; reuse permission is unknown. "
                    "A citation is not a license. Consult the linked source's current item-level terms. "
                    "Rights for any bundled reader text or media are documented separately."
                )
            else:
                source["rights_status"] = (
                    f"A source-level category is recorded as {classification}, but specific reuse terms are not "
                    "documented in this field. Consult the linked source's current item-level terms; a citation is "
                    "not a license. Rights for any bundled reader text or media are documented separately."
                )
        if not isinstance(source.get("rights_basis"), str) or not source["rights_basis"].strip():
            if classification == "unknown":
                source["rights_basis"] = (
                    "No source-specific license, reuse permission, or public-domain claim has been established in this "
                    "record. The unknown category records that evidence gap; it does not establish permission or prohibition."
                )
            else:
                source["rights_basis"] = (
                    "No separate rights-basis citation was present in the incoming record. See rights_status for the "
                    "preserved source notice, claim, conflict, or limitations. This archive has not independently "
                    "verified the claim or established worldwide legal status."
                )


SOURCE_RIGHTS_SCOPE_NOTES = {
    "SRC-429": {
        "rights_status": (
            "The linked archive site's reuse notice states that texts and images it identifies as property of the "
            "Igreja Lusitana are protected and may not be used, copied, reproduced, modified, sold, or otherwise "
            "reused, commercially or noncommercially, without the archive's express authorization. This establishes "
            "a restriction for materials covered by that notice, but the record does not establish ownership of this "
            "specific authority-page text. Rights in the linked page therefore remain unknown; no image or extended "
            "text from it is bundled."
        ),
        "rights_basis": (
            "The site's published notice was inspected at https://arquivo.igreja-lusitana.org/index.php/"
            "informationobject/browse?collection=9104&topLod=0 on 2026-10-27. It limits reuse of material owned by "
            "the Igreja Lusitana absent express authorization. Because ownership of this particular archival "
            "authority description is not established, this notice is recorded as a restriction, not as a definitive "
            "rights classification for that page."
        ),
    },
    "SRC-151": {
        "rights_status": (
            "TAU's captured Amos information page says the Ethiopic text version was prepared by Kefela Ghebre, "
            "published with his permission, and proofread by Ran HaCohen. TAU's separately captured site-wide notice "
            "permits noncommercial copying/distribution of digitized Ethiopic texts with required notices; other uses "
            "require contacting the rights holder. These statements concern the text, not reuse rights in this "
            "information page. The Amos reader records the text terms separately."
        ),
        "rights_basis": (
            "The retained Amos page documents transcriber attribution and permission to publish the text; SRC-036 "
            "documents TAU's notice for noncommercial text copying with notices. Neither establishes a license for "
            "reproducing this information webpage. Unknown is scoped to the webpage resource."
        ),
    },
    "SRC-318": {
        "rights_status": (
            "The retained Sirach information page identifies Dillmann's text version as transcribed by Ran HaCohen "
            "and bears © Ran HaCohen, February 2026. TAU's separately recorded site-wide notice permits "
            "noncommercial copying/distribution of digitized Ethiopic texts with required copyright and permission "
            "notices. That is a limited text-use notice, not an open license, and does not establish reuse rights in "
            "this information page. The bundled Sirach reader records text terms separately."
        ),
        "rights_basis": (
            "The captured page states attribution and a copyright claim for the transcription; SRC-036 records "
            "TAU's noncommercial text-use conditions. Neither provides page-specific reproduction terms. Unknown is "
            "scoped to the information webpage, not the reader text."
        ),
    },
}

TAU_PERMISSION_LIMITED_TEXT_SOURCE_IDS = (
    "SRC-061", "SRC-064", "SRC-069", "SRC-186", "SRC-187", "SRC-188", "SRC-189",
    "SRC-190", "SRC-191", "SRC-192", "SRC-193", "SRC-195", "SRC-336", "SRC-337",
)
TAU_PERMISSION_LIMITED_TEXT_RIGHTS = {
    "rights_classification": "permission_limited",
    "rights_status": (
        "This source record includes locally retained TAU digitized Ethiopic scripture text. TAU's captured notice "
        "permits use, copying, and distribution for noncommercial purposes only when the Ran HaCohen copyright and "
        "permission notices accompany every copy; other uses require contacting the copyright owner. This is "
        "permission-limited, not an open or commercial license. Consult the linked reader's item-specific notice."
    ),
    "rights_basis": (
        "The source inspection and retained local capture identify the scripture-text page(s); TAU's site-wide notice "
        "is separately recorded in SRC-036 and/or SRC-100. It expressly limits reuse to noncommercial copying and "
        "distribution with required notices. This record does not independently establish underlying print-edition "
        "rights or a worldwide legal conclusion."
    ),
}

CROSSWIRE_GEEZ_PERMISSION_LIMITED_TEXT_RIGHTS = {
    "rights_classification": "permission_limited",
    "rights_status": (
        "The locally bundled CrossWire Geez 1.0.1 module contains digitized Ethiopic scripture text and an embedded "
        "mods.d/geez.conf notice. The module identifies the text as copyrighted by Ran HaCohen and permits use, "
        "copying, and distribution for noncommercial purposes only when the copyright and permission notices "
        "accompany every copy; other uses require contacting the copyright owner. Its DistributionLicense field "
        "also says copyrighted; free non-commercial distribution. This is permission-limited, not an open or "
        "commercial license. It does not establish separate rights in software or ancillary package materials, "
        "or the text's accuracy or completeness."
    ),
    "rights_basis": (
        "The bundled readers/source/crosswire/Geez.zip is identified by SHA-256 in the local module audit at "
        "readers/source/crosswire/module-structure-audit.json. Its retained geez.conf contains the copyright, "
        "permission, and DistributionLicense fields quoted in rights_status. The permission applies to the "
        "digitized Ethiopic text as stated by the module; this archive does not independently establish a broader "
        "license or worldwide legal conclusion."
    ),
}


def apply_source_rights_scope_notes(sources: list[dict]) -> None:
    """Keep known text-level notice evidence distinct from the rights in its source page."""
    for source in sources:
        if not isinstance(source, dict):
            continue
        update = SOURCE_RIGHTS_SCOPE_NOTES.get(source.get("source_id"))
        if update:
            source.update(update)
        if source.get("source_id") in TAU_PERMISSION_LIMITED_TEXT_SOURCE_IDS:
            source.update(TAU_PERMISSION_LIMITED_TEXT_RIGHTS)
        if source.get("source_id") == "SRC-059":
            source.update(CROSSWIRE_GEEZ_PERMISSION_LIMITED_TEXT_RIGHTS)


def validate_source_link_safety(sources: list[dict]) -> None:
    """Keep withheld sources visible as evidence, never as navigable links."""
    for source in sources:
        if source.get("link_status") == "withheld" and not source.get("link_warning"):
            raise ValueError(f"{source.get('source_id')} has a withheld link but no user-facing warning.")

    reported_file_host = "img1.wsimg.com"
    reported_file_path = "/downloads/orthodox_tewahedo_bible.pdf"
    for source in sources:
        for field in ("url", "full_view_url"):
            parsed = urlparse(str(source.get(field, "")))
            if (parsed.hostname and parsed.hostname.lower() == reported_file_host
                    and unquote(parsed.path).lower() == reported_file_path
                    and source.get("link_status") != "withheld"):
                raise ValueError(
                    f"{source.get('source_id')} exposes the browser-blocked PDF as a navigable {field}; "
                    "keep this exact reported target withheld pending independent review."
                )

    # The reported security-blocked PDF remains useful as provenance, but the
    # archive must not send readers to it or to the page that offered it.
    reported_pdf = next((item for item in sources if item.get("source_id") == "SRC-004"), None)
    if not reported_pdf or reported_pdf.get("link_status") != "withheld":
        raise ValueError("SRC-004 must remain a retained, withheld source record pending independent review.")
    if "wsimg.com" in str(reported_pdf.get("url", "")).lower():
        raise ValueError("SRC-004 must retain the bibliographic source page, not the browser-blocked PDF host.")
    if "browser screenshot supplied with this project" not in str(reported_pdf.get("link_warning", "")):
        raise ValueError("SRC-004 must preserve that its security warning is reported evidence, not an independent scan.")

    app_script = (ROOT / "app.js").read_text(encoding="utf-8")
    withheld_branch = app_script.find("if (source.link_status === 'withheld')")
    non_link_return = app_script.find("return `<span class=\"source-link-withheld\">")
    local_copy_anchor = app_script.find("<a href=\"${escapeHTML(safeURL(source.local_copy_url))}\">")
    local_ocr_anchor = app_script.find("<a href=\"${escapeHTML(safeURL(source.local_ocr_url))}\">Open stored OCR (unreviewed)</a>")
    local_fidelity_audit_anchor = app_script.find("<a href=\"${escapeHTML(safeURL(source.local_fidelity_audit_url))}\">View verse text fidelity audit</a>")
    local_package_anchor = app_script.find("<a href=\"${escapeHTML(safeURL(source.local_source_package_url))}\" download>Download archived source package</a>")
    full_view_anchor = app_script.find("<a href=\"${escapeHTML(safeURL(source.full_view_url))}\" target=\"_blank\"")
    anchor_return = app_script.find("<a href=\"${escapeHTML(safeURL(source.url))}\"")
    if (min(withheld_branch, non_link_return, local_copy_anchor, local_ocr_anchor, local_fidelity_audit_anchor,
            local_package_anchor, full_view_anchor, anchor_return) < 0
            or not withheld_branch < non_link_return < local_copy_anchor < local_ocr_anchor < local_fidelity_audit_anchor
            < local_package_anchor < full_view_anchor < anchor_return):
        raise ValueError("The source renderer must show withheld sources as non-clickable text before building external anchors.")


def validate_brenton_exodus_capture() -> None:
    """Check local capture inventory integrity, not scripture accuracy."""
    capture_dir = ROOT / "readers" / "source" / "brenton-exodus"
    manifest_path = capture_dir / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chapters = manifest.get("chapters", [])
    expected = list(range(1, 41))
    if manifest.get("chapter_count") != len(expected) or [row.get("chapter") for row in chapters] != expected:
        raise ValueError("Brenton Exodus capture manifest must list all 40 expected chapter pages in order.")
    extracted_chapters = []
    for row in chapters:
        number = row["chapter"]
        filename = f"Exodus_{number:02d}.txt"
        if row.get("capture_file") != filename or row.get("source_url") != f"https://ebible.org/eng-Brenton/EXO{number:02d}.htm":
            raise ValueError(f"Brenton Exodus capture metadata mismatch for chapter {number}.")
        path = (capture_dir / filename).resolve()
        if not path.is_relative_to(capture_dir.resolve()) or not path.is_file():
            raise ValueError(f"Brenton Exodus capture file is missing or outside its directory: {filename}.")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != row.get("sha256"):
            raise ValueError(f"Brenton Exodus capture checksum mismatch: {filename}.")
        text = content.decode("utf-8")
        if (f"Brenton Septuagint Translation, Exodus {number}" not in text
                or f"https://ebible.org/eng-Brenton/EXO{number:02d}.htm" not in text
                or "raw HTML not retained" not in text):
            raise ValueError(f"Brenton Exodus capture header/limitation mismatch: {filename}.")
        extracted_chapters.append(parse_brenton_exodus_chapter(row))
    reader = json.loads((ROOT / "readers" / "exodus-geez.json").read_text(encoding="utf-8"))
    companion = reader.get("parallel_translation", {})
    if companion.get("translation_id") != "exodus-english-brenton-lxx-1851":
        raise ValueError("The Exodus reader must preserve the separately identified Brenton English companion.")
    if companion.get("chapters") != extracted_chapters:
        raise ValueError("The bundled Exodus companion does not exactly reproduce the captured-page extraction.")
    extracted_label_count = sum(len(chapter["verses"]) for chapter in extracted_chapters)
    if (manifest.get("extracted_label_count") != extracted_label_count
            or companion.get("verse_label_count") != extracted_label_count
            or companion.get("verification_status", "").find("not labeled verified scripture") < 0):
        raise ValueError("Brenton Exodus extraction count or unreviewed status is missing or stale.")
    notice = (capture_dir / "CAPTURE-NOTICE.txt").read_text(encoding="utf-8")
    if "not labeled verified scripture" not in notice:
        raise ValueError("Brenton Exodus capture notice must preserve the unreviewed research-only status.")


def validate_crosswire_module_audit() -> None:
    """Require the stored structural report to match the local SWORD package."""
    audit_path = ROOT / "readers" / "source" / "crosswire" / "module-structure-audit.json"
    if not audit_path.is_file():
        raise ValueError("Run audit_crosswire_module.py; the local module structure report is missing.")
    stored = json.loads(audit_path.read_text(encoding="utf-8"))
    if stored != build_crosswire_module_audit():
        raise ValueError("The stored CrossWire module structure report is stale or does not match its source package.")


def validate_mark_tei_audit() -> None:
    """Validate retained structural metadata after withholding the Mark text payload."""
    audit_path = ROOT / "readers" / "source" / "mark" / "structure-audit.json"
    if not audit_path.is_file():
        raise ValueError("The metadata-only Mark structure report is missing.")
    stored = json.loads(audit_path.read_text(encoding="utf-8"))
    expected = {
        "source_sha256": "1c3682594d26bcedc425431913575a446d0cd508c78457abffae74bf7c2bfced",
        "chapter_count": 16,
        "line_element_count": 765,
        "numbered_line_element_count": 678,
        "unnumbered_line_element_count": 87,
    }
    if any(stored.get(field) != value for field, value in expected.items()):
        raise ValueError("The retained Mark structural metadata does not match its recorded snapshot measurements.")
    if (ROOT / "readers" / "source" / "mark" / "LIT2711Mark-original.xml").exists():
        raise ValueError("The rights-withheld Mark source TEI must not be present in the public package.")

def require_object_fields(value: object, required: set[str], label: str) -> dict:
    """Require a JSON object and its schema-required keys without external dependencies."""
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object.")
    missing = required - set(value)
    if missing:
        raise ValueError(f"{label} is missing required fields: {sorted(missing)}")
    return value


def validate_closed_schema_objects(value: object, node: dict, root_schema: dict, label: str) -> None:
    """Enforce closed objects and array constraints, including siblings of $ref."""
    if "$ref" in node:
        if not node["$ref"].startswith("#/"):
            raise ValueError(f"{label} uses an unsupported external schema reference.")
        target = root_schema
        for part in node["$ref"][2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        validate_closed_schema_objects(value, target, root_schema, label)
        node = {key: constraint for key, constraint in node.items() if key != "$ref"}
    if "oneOf" in node:
        def matches_type(candidate: dict) -> bool:
            allowed = candidate.get("type")
            if allowed is None:
                return True
            if not isinstance(allowed, list):
                allowed = [allowed]
            return any(
                (kind == "null" and value is None)
                or (kind == "object" and isinstance(value, dict))
                or (kind == "array" and isinstance(value, list))
                or (kind == "string" and isinstance(value, str))
                or (kind == "integer" and isinstance(value, int) and not isinstance(value, bool))
                or (kind == "boolean" and isinstance(value, bool))
                for kind in allowed
            )
        branches = [candidate for candidate in node["oneOf"] if matches_type(candidate)]
        if len(branches) != 1:
            raise ValueError(f"{label} must match exactly one schema branch; matched {len(branches)}.")
        validate_closed_schema_objects(value, branches[0], root_schema, label)
        return
    if isinstance(value, dict):
        properties = node.get("properties", {})
        missing = set(node.get("required", [])) - set(value)
        if missing:
            raise ValueError(f"{label} is missing required schema properties: {sorted(missing)}.")
        if node.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise ValueError(f"{label} has unexpected schema properties: {sorted(extra)}.")
        for key, child in value.items():
            if key in properties:
                validate_closed_schema_objects(child, properties[key], root_schema, f"{label}.{key}")
    elif isinstance(value, list):
        if len(value) < node.get("minItems", 0):
            raise ValueError(f"{label} has fewer than {node['minItems']} required items.")
        if node.get("uniqueItems"):
            fingerprints = [json.dumps(child, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for child in value]
            if len(fingerprints) != len(set(fingerprints)):
                raise ValueError(f"{label} must not contain duplicate items.")
        if "items" in node:
            for index, child in enumerate(value):
                validate_closed_schema_objects(child, node["items"], root_schema, f"{label}[{index}]")


def validate_schema_constraints(value: object, node: dict, root_schema: dict, label: str) -> None:
    """Check the portable graph schema's scalar constraints without third-party dependencies."""
    if "$ref" in node:
        target = root_schema
        for part in node["$ref"][2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        validate_schema_constraints(value, target, root_schema, label)
    expected = node.get("type")
    allowed = expected if isinstance(expected, list) else ([expected] if expected else [])
    if allowed:
        type_matches = {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "null": value is None,
        }
        if not any(type_matches.get(kind, False) for kind in allowed):
            raise ValueError(f"{label} must have JSON Schema type {expected}.")
    if "const" in node and value != node["const"]:
        raise ValueError(f"{label} must equal its schema constant.")
    if "enum" in node and value not in node["enum"]:
        raise ValueError(f"{label} has a value outside its schema enum.")
    if isinstance(value, str):
        if len(value) < node.get("minLength", 0):
            raise ValueError(f"{label} is shorter than its schema minimum.")
        if "pattern" in node and re.search(node["pattern"], value) is None:
            raise ValueError(f"{label} does not match its schema pattern.")
        if node.get("format") == "uri":
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"{label} must be an absolute URI.")
        elif node.get("format") == "date":
            from datetime import date
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{label} must be an ISO date.") from exc
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value < node.get("minimum", float("-inf")):
        raise ValueError(f"{label} is below its schema minimum.")
    if isinstance(value, list):
        if len(value) < node.get("minItems", 0):
            raise ValueError(f"{label} has fewer items than its schema minimum.")
        if node.get("uniqueItems"):
            fingerprints = [json.dumps(child, ensure_ascii=False, sort_keys=True) for child in value]
            if len(fingerprints) != len(set(fingerprints)):
                raise ValueError(f"{label} violates uniqueItems.")
        if "items" in node:
            for index, child in enumerate(value):
                validate_schema_constraints(child, node["items"], root_schema, f"{label}[{index}]")
    if isinstance(value, dict):
        props = node.get("properties", {})
        required = set(node.get("required", []))
        if required - set(value):
            raise ValueError(f"{label} is missing schema-required fields: {sorted(required - set(value))}.")
        if node.get("additionalProperties") is False and set(value) - set(props):
            raise ValueError(f"{label} has fields not allowed by its closed schema.")
        for key, child in value.items():
            if key in props:
                validate_schema_constraints(child, props[key], root_schema, f"{label}.{key}")


def validate_catalogue_research_views(catalogue: list[dict]) -> None:
    """Validate local research-view links and ensure the site can cache each linked page."""
    schema = json.loads(
        (ROOT / "schemas" / "catalogue-research-view.schema.json").read_text(encoding="utf-8")
    )
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Catalogue research-view schema must declare JSON Schema 2020-12.")
    worker = (ROOT / "sw.js").read_text(encoding="utf-8")
    for record in catalogue:
        views = record.get("local_research_views", [])
        if not isinstance(views, list):
            raise ValueError(f"{record.get('catalogue_id', 'Catalogue record')} local_research_views must be an array.")
        paths = set()
        for index, view in enumerate(views):
            label = f"{record.get('catalogue_id', 'Catalogue record')}.local_research_views[{index}]"
            validate_closed_schema_objects(view, schema, schema, label)
            validate_schema_constraints(view, schema, schema, label)
            relative = Path(view["path"])
            if (relative.is_absolute() or ".." in relative.parts or relative.as_posix() != view["path"]
                    or not relative.as_posix().startswith("research/")):
                raise ValueError(f"{label} must point to a safe package-local research path.")
            target = (ROOT / relative).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                raise ValueError(f"{label} points to a missing or out-of-package file: {view['path']}.")
            if view["path"] in paths:
                raise ValueError(f"{label} duplicates a research-view path on its catalogue record.")
            paths.add(view["path"])
            if "if (relativePath)" not in worker:
                raise ValueError(f"{label} requires same-origin on-demand caching for offline access.")


def normalize_catalogue_custodians(catalogue: list[dict], source_ids: set[str]) -> None:
    """Use the archive as catalogue custodian and retain all prior sources as evidence."""
    custodian_id = "SRC-000"
    if custodian_id not in source_ids:
        raise ValueError("The archive's self-held catalogue source SRC-000 is missing.")
    for record in catalogue:
        prior_source_id = record.get("source_id")
        if prior_source_id not in source_ids:
            raise ValueError(f"{record.get('display_name', 'Catalogue record')} has no valid prior catalogue source.")
        evidence_ids = record.get("evidence_source_ids", [])
        if not isinstance(evidence_ids, list) or any(source_id not in source_ids for source_id in evidence_ids):
            raise ValueError(f"{record.get('display_name', 'Catalogue record')} has invalid evidence source IDs.")
        if prior_source_id != custodian_id:
            evidence_ids = [*evidence_ids, prior_source_id]
        record["source_id"] = custodian_id
        record["evidence_source_ids"] = sorted(set(evidence_ids), key=lambda value: int(value.split("-")[-1]))
def validate_research_corpus_language_script(
    corpus: dict,
    reader: dict,
    languages_by_tag: dict,
    audited_language_tags: set,
    audited_script_codes: set,
) -> None:
    """Require evidenced identifiers while preserving unknown language/script as und/Zzzz."""
    corpus_id = corpus.get("corpus_id")
    language_tag = corpus.get("language_tag")
    script_code = corpus.get("script_code")
    language_tag_pattern = r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$"
    script_code_pattern = r"^[A-Z][a-z]{3}$"
    if (not re.fullmatch(language_tag_pattern, str(language_tag or ""))
            or language_tag not in audited_language_tags):
        raise ValueError(f"Research corpus {corpus_id} needs a language tag in the cited audit.")
    if (not re.fullmatch(script_code_pattern, str(script_code or ""))
            or script_code not in audited_script_codes):
        raise ValueError(f"Research corpus {corpus_id} needs a script code in the cited audit.")
    if language_tag != "und":
        language = languages_by_tag.get(language_tag)
        if not language:
            raise ValueError(f"Research corpus {corpus_id} must use a registered language profile or und.")
        language_scripts = set(language.get("script_codes", [])) or {language.get("script_code")}
        if script_code != "Zzzz" and script_code not in language_scripts:
            raise ValueError(f"Research corpus {corpus_id} uses a script absent from its language profile.")
    if reader.get("language_tag") != language_tag or reader.get("script_code") != script_code:
        raise ValueError(f"Research corpus {corpus_id} language/script metadata disagrees with its reader.")


def validate_global_layer_example(source_ids: set[str]) -> list[dict]:
    schema_path = ROOT / "schemas" / "text-layer.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    identifier_audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
    audited_language_tags = set(identifier_audit.get("language_subtags", {}).get("codes", []))
    script_audit = identifier_audit.get("script_codes", {})
    audited_script_codes = set(script_audit.get("iso_15924_codes", [])) | set(script_audit.get("iana_special_codes", []))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Global text-layer schema must declare JSON Schema 2020-12.")
    properties = schema.get("properties", {})
    language_pattern = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
    valid_layer_types = set(properties["layer_type"].get("enum", []))
    valid_text_origins = set(properties["text_origin"].get("enum", []))
    valid_publication_states = set(properties["publication_state"].get("enum", []))
    example_paths = sorted((ROOT / "examples").glob("*-layer.json"))
    if not example_paths:
        raise ValueError("At least one global text-layer example is required.")
    records: list[dict] = []
    for example_path in example_paths:
        record = json.loads(example_path.read_text(encoding="utf-8"))
        validate_closed_schema_objects(record, schema, schema, example_path.name)
        missing = set(schema.get("required", [])) - set(record)
        if missing:
            raise ValueError(f"{example_path.name} is missing required fields: {sorted(missing)}")
        witness = require_object_fields(
            record.get("witness"), {"witness_id", "witness_type", "title", "source_ids"},
            f"{example_path.name} witness",
        )
        if witness.get("witness_type") not in {"manuscript", "printed_edition", "digital_edition", "transcription", "composite", "unknown"}:
            raise ValueError(f"{example_path.name} has an invalid witness type.")
        if (not isinstance(witness.get("title"), str) or not witness["title"].strip()
                or not isinstance(witness.get("source_ids"), list) or not witness["source_ids"]
                or any(not isinstance(source_id, str) or not source_id for source_id in witness["source_ids"])):
            raise ValueError(f"{example_path.name} witness needs a title and one or more source IDs.")
        assertions = record.get("tradition_assertions")
        if not isinstance(assertions, list):
            raise ValueError(f"{example_path.name} tradition_assertions must be a list.")
        for index, assertion in enumerate(assertions):
            assertion = require_object_fields(
                assertion, {"tradition_id", "canon_id", "mapping_state", "evidence_source_ids"},
                f"{example_path.name} tradition assertion {index + 1}",
            )
            if assertion.get("mapping_state") not in {"asserted_by_source", "reviewed_match", "related_work", "uncertain", "not_mapped"}:
                raise ValueError(f"{example_path.name} tradition assertion {index + 1} has an invalid mapping state.")
            evidence_ids = assertion.get("evidence_source_ids")
            if (not isinstance(evidence_ids, list) or not evidence_ids
                    or any(not isinstance(source_id, str) or not source_id for source_id in evidence_ids)):
                raise ValueError(f"{example_path.name} tradition assertion {index + 1} needs cited source IDs.")
            if assertion.get("mapping_state") == "reviewed_match":
                identity_reviews = [
                    item for item in record.get("review_dimensions", [])
                    if item.get("dimension") == "identity"
                    and item.get("state") in {"checked_with_limits", "reviewed"}
                    and item.get("review_method") in {"source_inspection", "human_review", "scholarly_review", "community_review", "combined_source_and_automated_validation"}
                    and item.get("evidence_source_ids")
                    and item.get("scope")
                ]
                if not identity_reviews:
                    raise ValueError(
                        f"{example_path.name} reviewed_match needs a scoped identity review with cited evidence."
                    )
        package = require_object_fields(
            record.get("content_package"), {"uri", "media_type", "sha256"},
            f"{example_path.name} content_package",
        )
        if (not isinstance(package.get("uri"), str) or not package["uri"].strip()
                or not isinstance(package.get("media_type"), str)
                or not re.fullmatch(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$", package["media_type"])):
            raise ValueError(f"{example_path.name} content_package needs a local URI and valid media type.")
        coverage = require_object_fields(
            record.get("coverage"), {"extent_state", "extent_basis", "unit_count"},
            f"{example_path.name} coverage",
        )
        if coverage.get("extent_state") not in {"complete_for_declared_edition", "partial", "unknown"}:
            raise ValueError(f"{example_path.name} has an invalid coverage extent_state.")
        if coverage.get("extent_basis") not in {"edition_contents_statement", "source_inventory", "independent_collation", "unknown"}:
            raise ValueError(f"{example_path.name} has an invalid coverage extent_basis.")
        validate_unit_count(coverage.get("unit_count"), f"{example_path.name} coverage.unit_count")
        validate_unit_coverage(coverage, f"{example_path.name} coverage")
        lacunae = coverage.get("missing_or_lacunose_ranges", [])
        if not isinstance(lacunae, list) or any(not isinstance(value, str) for value in lacunae):
            raise ValueError(f"{example_path.name} coverage.missing_or_lacunose_ranges must be a list of strings.")
        rights = require_object_fields(
            record.get("rights"), {"status", "statement"}, f"{example_path.name} rights",
        )
        if rights.get("status") not in {"public_domain_claimed", "open_license", "permission_limited", "all_rights_reserved", "unknown", "mixed"}:
            raise ValueError(f"{example_path.name} has an invalid rights status.")
        if (not isinstance(rights.get("statement"), str) or not rights["statement"].strip()
                or not isinstance(rights.get("attribution_required", False), bool)):
            raise ValueError(f"{example_path.name} rights needs a statement and a boolean attribution_required value.")
        if rights.get("status") == "open_license" and (
                not isinstance(rights.get("license_id"), str) or not rights["license_id"].strip()):
            raise ValueError(f"{example_path.name} needs a nonempty license identifier for its open-license claim.")
        review_dimensions = record.get("review_dimensions")
        if not isinstance(review_dimensions, list):
            raise ValueError(f"{example_path.name} review_dimensions must be a list.")
        valid_dimensions = {"identity", "transcription_accuracy", "translation_accuracy", "chapter_or_section_sequence", "unit_boundaries", "completeness", "alignment", "rights", "language_identification", "community_review", "other"}
        valid_review_states = {"not_checked", "in_progress", "checked_with_limits", "reviewed", "disputed", "unknown"}
        for index, review in enumerate(review_dimensions):
            review = require_object_fields(
                review, {"dimension", "state", "scope", "evidence_source_ids"},
                f"{example_path.name} review dimension {index + 1}",
            )
            if review.get("dimension") not in valid_dimensions or review.get("state") not in valid_review_states:
                raise ValueError(f"{example_path.name} review dimension {index + 1} has an invalid dimension or state.")
            validate_review_record(review, f"{example_path.name} review dimension {index + 1}")
            if not isinstance(review.get("scope"), str) or not review["scope"].strip():
                raise ValueError(f"{example_path.name} review dimension {index + 1} needs a nonempty scope.")
            evidence_ids = review.get("evidence_source_ids")
            if not isinstance(evidence_ids, list) or any(not isinstance(source_id, str) or not source_id for source_id in evidence_ids):
                raise ValueError(f"{example_path.name} review dimension {index + 1} evidence_source_ids must be a list of source IDs.")
        labels = record.get("labels", [])
        if not isinstance(labels, list):
            raise ValueError(f"{example_path.name} labels must be a list.")
        for index, label in enumerate(labels):
            label = require_object_fields(
                label, {"value", "language_tag", "label_type"},
                f"{example_path.name} label {index + 1}",
            )
            if (not isinstance(label.get("value"), str) or not label["value"].strip()
                    or not language_pattern.fullmatch(str(label.get("language_tag", "")))
                    or label.get("label_type") not in {"preferred", "alternate", "transliterated", "original_form", "community_name"}):
                raise ValueError(f"{example_path.name} label {index + 1} needs text, a language tag, and a valid label type.")
        if record.get("schema_version") != properties.get("schema_version", {}).get("const"):
            raise ValueError(f"{example_path.name} version does not match its schema.")
        agent_roles = {"author", "translator", "editor", "transcriber", "digitizer", "reviewer", "publisher", "community_steward", "software"}
        agents = record.get("agents")
        if not isinstance(agents, list):
            raise ValueError(f"{example_path.name} agents must be a list; use an empty list when no layer-specific attribution is supported.")
        for agent in agents:
            agent_sources = agent.get("source_ids") if isinstance(agent, dict) else None
            if (not isinstance(agent, dict) or not isinstance(agent.get("role"), str)
                    or agent.get("role") not in agent_roles
                    or not isinstance(agent.get("name"), str) or not agent["name"].strip()
                    or not isinstance(agent_sources, list) or not agent_sources
                    or any(not isinstance(source_id, str) for source_id in agent_sources)
                    or set(agent_sources) - source_ids):
                raise ValueError(f"{example_path.name} has an agent attribution without a name, valid role, or cited source; do not infer contributor identities.")
        if (record.get("layer_type") not in valid_layer_types
                or record.get("text_origin") not in valid_text_origins
                or record.get("publication_state") not in valid_publication_states):
            raise ValueError(f"{example_path.name} has an invalid layer type, text origin, or publication state.")
        if (record.get("publication_state") == "bundled"
                and record.get("text_origin") in {"machine_generated_draft", "unknown"}):
            raise ValueError(f"{example_path.name} cannot bundle generated draft wording or text with unknown origin.")
        if (record.get("layer_type") in {"source_text_transcription", "diplomatic_transcription"}
                and record.get("text_origin") != "source_transcription"):
            raise ValueError(f"{example_path.name} transcription layer must identify its origin as a source transcription.")
        if (record.get("layer_type") == "translation"
                and record.get("text_origin") not in {"published_translation", "machine_generated_draft"}):
            raise ValueError(f"{example_path.name} translation layer needs a published-translation or generated-draft origin.")
        identifiers = [record.get("record_id"), record.get("work_id"), record.get("witness", {}).get("witness_id")]
        for assertion in record.get("tradition_assertions", []):
            identifiers.extend((assertion.get("tradition_id"), assertion.get("canon_id")))
        for identifier in identifiers:
            parsed = urlparse(str(identifier or ""))
            if parsed.scheme not in {"https", "urn"} or (parsed.scheme == "https" and not parsed.netloc):
                raise ValueError(f"{example_path.name} has an identifier that is not a persistent HTTPS IRI or URN.")
        if (not language_pattern.fullmatch(str(record.get("language_tag", "")))
                or not re.fullmatch(r"^[A-Z][a-z]{3}$", str(record.get("script_code", "")))):
            raise ValueError(f"{example_path.name} needs a BCP 47 language tag and ISO 15924 script code.")
        path = record.get("basis_path")
        if path is not None and (
                not isinstance(path, list) or not path
                or any(not language_pattern.fullmatch(str(tag)) for tag in path)):
            raise ValueError(f"{example_path.name} needs a language-tagged basis path or explicit null.")
        if (record["layer_type"] == "translation" and path is not None
                and (len(path) < 2 or path[-1] != record["language_tag"])):
            raise ValueError(f"{example_path.name} translation path must end at its output language.")
        basis_path_status = record.get("basis_path_status")
        if (record["layer_type"] == "translation" and path is None
                and basis_path_status != "unknown"):
            raise ValueError(f"{example_path.name} translation with a null basis path must explicitly mark basis_path_status as unknown.")
        if (record["layer_type"] == "translation" and path is not None
                and basis_path_status == "unknown"):
            raise ValueError(f"{example_path.name} cannot mark a populated translation basis path as unknown.")
        if (record["layer_type"] in {"source_text_transcription", "diplomatic_transcription"}
                and path is not None and path != [record["language_tag"]]):
            raise ValueError(f"{example_path.name} transcription basis path must identify its text language.")
        if (record["layer_type"] == "translation" and path is None
                and not any(
                    item.get("dimension") == "translation_accuracy" and item.get("state") == "unknown"
                    for item in record.get("review_dimensions", [])
                )):
            raise ValueError(f"{example_path.name} translation with unknown basis must include an explicit unknown translation_accuracy review.")
        if (record["layer_type"] in {"source_text_transcription", "diplomatic_transcription"}
                and path is None and record.get("publication_state") == "bundled"
                and record.get("language_tag") != "und"):
            raise ValueError(f"{example_path.name} cannot publish a transcription without an identified text language.")
        referenced_sources: set[str] = set()

        def gather_sources(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"source_ids", "evidence_source_ids"} and isinstance(child, list):
                        referenced_sources.update(child)
                    else:
                        gather_sources(child)
            elif isinstance(value, list):
                for child in value:
                    gather_sources(child)

        gather_sources(record)
        if not referenced_sources or referenced_sources - source_ids:
            raise ValueError(f"{example_path.name} has missing source records: {sorted(referenced_sources - source_ids)}")
        rights_evidence = set(rights.get("evidence_source_ids", []))
        if record.get("publication_state") == "bundled":
            if rights.get("status") not in {"public_domain_claimed", "open_license", "permission_limited"}:
                raise ValueError(f"{example_path.name} cannot bundle text with unresolved or mixed rights.")
            if not rights_evidence or rights_evidence - source_ids:
                raise ValueError(f"{example_path.name} needs valid rights evidence before bundling.")
        relative_path = unquote(str(package.get("uri", "")))
        package_path = (example_path.parent / relative_path).resolve()
        if not package_path.is_relative_to(ROOT.resolve()) or not package_path.is_file():
            raise ValueError(f"{example_path.name} must reference an existing local package inside the site.")
        digest = hashlib.sha256(package_path.read_bytes()).hexdigest()
        if package.get("sha256", "").lower() != digest:
            raise ValueError(f"{example_path.name} package SHA-256 does not match its local reader.")
        package_document = json.loads(package_path.read_text(encoding="utf-8"))
        selector = package.get("json_pointer", "")
        packaged_reader = resolve_json_pointer(package_document, selector, f"{example_path.name} content package")
        if not isinstance(packaged_reader, dict):
            raise ValueError(f"{example_path.name} content package selector must resolve to a JSON object.")
        if packaged_reader.get("text_origin") != record["text_origin"]:
            raise ValueError(f"{example_path.name} text origin disagrees with its packaged reader.")
        packaged_unit_count = sum(
            len(chapter.get("verses", chapter.get("units", [])))
            for chapter in packaged_reader.get("chapters", [])
        )
        if (record.get("language_tag") != packaged_reader.get("language_tag")
                or record.get("script_code") != packaged_reader.get("script_code")
                or record.get("text_origin") != packaged_reader.get("text_origin")
                or record.get("language_tag") not in audited_language_tags
                or record.get("script_code") not in audited_script_codes
                or record.get("coverage", {}).get("unit_count") != packaged_unit_count):
            raise ValueError(f"{example_path.name} language, script, origin, or unit count disagrees with its content package.")
        records.append(record)
    manifest = {
        "manifest_version": 1,
        "schema_uri": "../schemas/text-layer.schema.json",
        "coverage_statement": f"This manifest includes portable metadata for {len(records)} selected text layers across the bundled readers. It does not represent complete canon or language coverage.",
        "records": records,
    }
    return manifest["records"]


def validate_archive_graph_example(source_ids: set[str], translation_registry: dict, filename: str = "archive-graph-genesis.json", source_registry: dict | None = None) -> None:
    """Validate the normalized graph sample's shape, references, and local package hashes."""
    schema = json.loads((ROOT / "schemas" / "archive-graph.schema.json").read_text(encoding="utf-8"))
    example_path = ROOT / "examples" / filename
    graph = json.loads(example_path.read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or schema.get("$id") != "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/schemas/archive-graph.schema.json":
        raise ValueError("Normalized archive graph schema must identify JSON Schema 2020-12 and its published schema URI.")
    validate_closed_schema_objects(graph, schema, schema, example_path.name)
    validate_schema_constraints(graph, schema, schema, example_path.name)
    if graph.get("scope_state") == "complete_for_declared_scope" and not graph.get("scope_note"):
        raise ValueError("A complete archive graph requires a declared, bounded scope note.")

    records_by_kind = {
        kind: {record["id"]: record for record in graph.get(kind, [])}
        for kind in ("traditions", "canons", "works", "witnesses", "layers", "structures", "alignments", "citations", "rights", "review_events")
    }
    entity_ids = []
    for kind, records in records_by_kind.items():
        if not records:
            continue
        original = graph.get(kind, [])
        if len(records) != len(original):
            raise ValueError(f"{example_path.name} contains duplicate IDs in {kind}.")
        entity_ids.extend(records)
    entry_ids = []
    for canon in graph.get("canons", []):
        for entry in canon.get("entries", []):
            entry_ids.append(entry["id"])
    all_ids = entity_ids + entry_ids
    if len(all_ids) != len(set(all_ids)):
        raise ValueError(f"{example_path.name} reuses an ID across record types.")

    known_sources = source_ids
    def collect_source_references(value: object) -> set[str]:
        found: set[str] = set()
        if isinstance(value, dict):
            for field in ("source_ids", "evidence_source_ids"):
                refs = value.get(field, [])
                if isinstance(refs, list):
                    found.update(item for item in refs if isinstance(item, str))
            if isinstance(value.get("source_id"), str):
                found.add(value["source_id"])
            for child in value.values():
                found.update(collect_source_references(child))
        elif isinstance(value, list):
            for child in value:
                found.update(collect_source_references(child))
        return found
    missing_sources = collect_source_references(graph) - known_sources
    if missing_sources:
        raise ValueError(f"{example_path.name} references missing evidence sources: {sorted(missing_sources)}.")
    for record in graph.get("citations", []):
        if record["source_id"] not in known_sources:
            raise ValueError(f"{example_path.name} citation references missing source {record['source_id']}.")
        if source_registry is not None and filename == "archive-graph-registered-layers.json":
            source = source_registry[record["source_id"]]
            if record.get("locator") != source.get("url") or record["supports_claim"] != (source.get("inspection_and_limitations") or source.get("source_name", "Source record linked by archive metadata.")):
                raise ValueError(f"{example_path.name} citation does not reproduce the linked archive source record.")
    for record in graph.get("canons", []):
        if record["tradition_id"] not in records_by_kind["traditions"]:
            raise ValueError(f"{example_path.name} canon references a missing tradition.")
        ordinals = [entry["ordinal"] for entry in record.get("entries", [])]
        if len(ordinals) != len(set(ordinals)):
            raise ValueError(f"{example_path.name} repeats a canon entry ordinal.")
        for entry in record.get("entries", []):
            for assertion in entry.get("work_assertions", []):
                if assertion["work_id"] not in records_by_kind["works"]:
                    raise ValueError(f"{example_path.name} canon assertion references a missing work.")
    for record in graph.get("works", []):
        if set(record.get("related_work_ids", [])) - set(records_by_kind["works"]):
            raise ValueError(f"{example_path.name} work references a missing related work.")
    for record in graph.get("witnesses", []):
        if record["work_id"] not in records_by_kind["works"]:
            raise ValueError(f"{example_path.name} witness references a missing work.")

    language_tags = {item.get("language_tag") for item in translation_registry.get("languages", [])}
    language_tags.update(item.get("language_tag") for item in translation_registry.get("basis_languages", []))
    language_audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
    valid_languages = set(language_audit.get("language_subtags", {}).get("codes", []))
    valid_scripts = set(language_audit.get("script_codes", {}).get("iso_15924_codes", [])) | set(language_audit.get("script_codes", {}).get("iana_special_codes", []))
    layer_ids = set(records_by_kind["layers"])
    structure_ids = set(records_by_kind["structures"])
    rights_ids = set(records_by_kind["rights"])
    review_ids = set(records_by_kind["review_events"])
    referenced_review_ids = set()
    for layer in graph.get("layers", []):
        if layer["witness_id"] not in records_by_kind["witnesses"]:
            raise ValueError(f"{example_path.name} layer references a missing witness.")
        if layer["rights_id"] not in rights_ids or layer["structure_id"] not in structure_ids:
            raise ValueError(f"{example_path.name} layer references missing rights or structure records.")
        if set(layer.get("review_event_ids", [])) - review_ids:
            raise ValueError(f"{example_path.name} layer references a missing review event.")
        referenced_review_ids.update(layer.get("review_event_ids", []))
        if layer["language_tag"] not in valid_languages or layer["language_tag"] not in language_tags:
            raise ValueError(f"{example_path.name} layer language is not in the audited registry.")
        if layer["script_code"] not in valid_scripts:
            raise ValueError(f"{example_path.name} layer script is not in the audited ISO 15924 set.")
        if layer["layer_type"] == "translation":
            if layer["text_origin"] not in {"published_translation", "machine_generated_draft"}:
                raise ValueError(f"{example_path.name} translation has an incompatible text origin.")
            if layer["basis_path"] and layer["basis_path"][-1] != layer["language_tag"]:
                raise ValueError(f"{example_path.name} translation path must end in its output language.")
            if layer["basis_path"] is None and not any(
                event["id"] in layer.get("review_event_ids", [])
                and event["dimension"] == "translation_accuracy"
                and event["state"] == "unknown"
                for event in graph.get("review_events", [])
            ):
                raise ValueError(f"{example_path.name} translation with unknown basis must preserve an explicit unknown-basis review.")
        elif layer["layer_type"] in {"source_text_transcription", "diplomatic_transcription"}:
            if layer["text_origin"] != "source_transcription" or layer["basis_path"] != [layer["language_tag"]]:
                raise ValueError(f"{example_path.name} transcription must identify its source language and origin.")
        if layer.get("publication_state") == "bundled" and layer.get("text_origin") in {"machine_generated_draft", "unknown"}:
            raise ValueError(f"{example_path.name} cannot publish a generated draft or unknown-origin layer as bundled text.")
        if (layer.get("publication_state") == "bundled"
                and layer.get("community_access", {}).get("state") == "restricted"):
            raise ValueError(f"{example_path.name} cannot bundle a community-restricted layer.")
        package = layer["content_package"]
        package_path = (ROOT / unquote(package["uri"])).resolve()
        if not package_path.is_relative_to(ROOT.resolve()) or not package_path.is_file():
            raise ValueError(f"{example_path.name} points to a missing or unsafe local content package.")
        if hashlib.sha256(package_path.read_bytes()).hexdigest() != package["sha256"].lower():
            raise ValueError(f"{example_path.name} content package checksum is stale.")
        package_data = json.loads(package_path.read_text(encoding="utf-8"))
        if package.get("json_pointer"):
            package_data = resolve_json_pointer(package_data, package["json_pointer"], f"{example_path.name} content package")
        if (package_data.get("language_tag") != layer["language_tag"]
                or package_data.get("script_code") != layer["script_code"]
                or package_data.get("text_origin") != layer["text_origin"]):
            raise ValueError(f"{example_path.name} layer language, script, or origin disagrees with its packaged reader.")

    for kind, records in graph.items():
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            cited = set(record.get("source_ids", [])) | set(record.get("evidence_source_ids", []))
            if record.get("source_id"):
                cited.add(record["source_id"])
            if cited - known_sources:
                raise ValueError(f"{example_path.name} record cites missing sources: {sorted(cited - known_sources)}.")

    for record in graph.get("structures", []):
        layer = records_by_kind["layers"].get(record["layer_id"])
        if not layer or layer["structure_id"] != record["id"]:
            raise ValueError(f"{example_path.name} structure/layer references are not reciprocal.")
        if record.get("extent_state") == "complete_for_declared_edition" and record.get("extent_basis") == "unknown":
            raise ValueError(f"{example_path.name} cannot call unknown-scope coverage complete.")
    for record in graph.get("rights", []):
        layer = records_by_kind["layers"].get(record["layer_id"])
        if not layer or layer["rights_id"] != record["id"]:
            raise ValueError(f"{example_path.name} rights/layer references are not reciprocal.")
        if record.get("distribution_decision") == "include_text" and record.get("status") in {"unknown", "all_rights_reserved", "mixed"}:
            raise ValueError(f"{example_path.name} includes text despite unresolved or prohibitive rights.")
    for record in graph.get("review_events", []):
        if record["layer_id"] not in layer_ids:
            raise ValueError(f"{example_path.name} review event references a missing layer.")
        if record["state"] == "reviewed" and (not record.get("reviewer") or not record.get("reviewed_at") or record["method"] not in {"human_review", "scholarly_review", "community_review"}):
            raise ValueError(f"{example_path.name} cannot claim reviewed without a named human reviewer and date.")
        if record["method"] == "automated_validation" and record.get("reviewer") is not None:
            raise ValueError(f"{example_path.name} must not put a tool or automated process in the reviewer field.")
    if referenced_review_ids != review_ids:
        raise ValueError(f"{example_path.name} contains orphaned or unlinked review events.")

    for record in graph.get("alignments", []):
        if record["source_layer_id"] not in layer_ids or record["target_layer_id"] not in layer_ids:
            raise ValueError(f"{example_path.name} alignment references a missing text layer.")
    if graph.get("scope_state") == "illustrative_subset" and not graph.get("scope_note", "").strip():
        raise ValueError(f"{example_path.name} illustrative subset needs an explicit scope note.")



def apply_reviewed_title_crosswalks(archive: dict | None = None) -> None:
    """Apply source-reviewed work/title states after source builders regenerate layers."""
    if archive is None:
        canon_registry = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    else:
        canon_registry = archive.get("canon_registry", {})
    applied: set[str] = set()
    for book in canon_registry.get("books", []):
        if book.get("mapping_state") != "reviewed_match" or not book.get("reader_id"):
            continue
        canon_id = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/canon/{book['canon_id']}"
        matched_paths = []
        for example_path in sorted((ROOT / "examples").glob("*-layer.json")):
            record = json.loads(example_path.read_text(encoding="utf-8"))
            if record.get("layer_type") != "source_text_transcription":
                continue
            package_uri = record.get("content_package", {}).get("uri")
            if not isinstance(package_uri, str):
                continue
            package_path = (example_path.parent / package_uri).resolve()
            if not package_path.is_file():
                continue
            try:
                reader = json.loads(package_path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if reader.get("reader_id") != book["reader_id"]:
                continue
            assertion = next((item for item in record.get("tradition_assertions", []) if item.get("canon_id") == canon_id), None)
            if assertion is None:
                continue
            assertion["mapping_state"] = "reviewed_match"
            assertion["evidence_source_ids"] = list(book.get("source_ids", []))
            assertion["notes"] = book.get("mapping_note", "")
            if not assertion["evidence_source_ids"] or "crosswalk" not in assertion["notes"].lower() or not assertion["notes"].startswith("Reviewed "):
                raise ValueError(f"Canon registry reviewed mapping for {book['canon_id']} lacks scoped evidence notes.")
            reviews = record.setdefault("review_dimensions", [])
            identity = next((item for item in reviews if item.get("dimension") == "identity"), None)
            prior_notes = identity.get("notes") if identity else None
            if identity is None:
                identity = {"dimension": "identity"}
                reviews.insert(0, identity)
            identity.update({
                "state": "checked_with_limits",
                "scope": f"{book['mapping_note']} Exact edition identity, textual accuracy, and completeness remain distinct questions.",
                "reviewer": None,
                "review_method": "source_inspection",
                "review_process": "Comparative inspection of the cited Church-list and source-work records.",
                "reviewed_at": "2026-10-25",
                "evidence_source_ids": sorted(set(book["source_ids"]) | set(identity.get("evidence_source_ids", []))),
                "notes": prior_notes if book["mapping_note"] in (prior_notes or "") else " ".join(value for value in [prior_notes, book["mapping_note"]] if value),
            })
            write_text_atomically(example_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
            matched_paths.append(example_path)
        if len(matched_paths) != 1:
            raise ValueError(f"Expected one source-text layer for reviewed canon entry {book['canon_id']}; found {len(matched_paths)}.")
        applied.add(book["canon_id"])
    expected = {book["canon_id"] for book in canon_registry.get("books", []) if book.get("mapping_state") == "reviewed_match" and book.get("reader_id")}
    if applied != expected:
        raise ValueError(f"Reviewed title crosswalk application mismatch: missing {sorted(expected - applied)}")


REVIEWED_NT_PACKAGE_CROSSWALKS = (
    {
        "reader_prefix": "som-1979-2008-",
        "language_tag": "so",
        "module_path_regex": r"::\d+-{code}som\.usfm$",
        "edition": "SOMSIM / som",
        "edition_source_id": "SRC-390",
        "package_source_id": "SRC-391",
        "source_ids": {"SRC-390", "SRC-391"},
    },
    {
        "reader_prefix": "lin-2020-",
        "language_tag": "ln",
        "module_path_regex": r"::\d+-{code}lin\.usfm$",
        "edition": "LINBIB / lin",
        "edition_source_id": "SRC-393",
        "package_source_id": "SRC-394",
        "source_ids": {"SRC-393", "SRC-394"},
    },
    {
        "reader_prefix": "maale-",
        "language_tag": "mdy",
        "module_path_regex": r"::\d+-{code}mdyeth\.usfm$",
        "edition": "MDYTWF / mdyeth",
        "edition_source_id": "SRC-363",
        "package_source_id": "SRC-364",
        "source_ids": {"SRC-363", "SRC-364"},
    },
    {
        "reader_prefix": "arb-vd-",
        "language_tag": "arb",
        "module_path_regex": r"#\d+-{code}arb-vd\.usfm \(curated bundle member; original package hash is in the capture manifest\)$",
        "edition": "Arabic Van Dyck / arb-vd",
        "edition_source_id": "SRC-329",
        "package_source_id": "SRC-330",
        "source_ids": {"SRC-329", "SRC-330"},
    },
    {
        "reader_prefix": "dawro-latin-",
        "language_tag": "dwr",
        "module_path_regex": r"::\d+-{code}dwrl\.usfm$",
        "edition": "DWRLTW / dwrl",
        "edition_source_id": "SRC-404",
        "package_source_id": "SRC-405",
        "source_ids": {"SRC-404", "SRC-405"},
    },
    {
        "reader_prefix": "oyda-",
        "language_tag": "oyd",
        "module_path_regex": r"::\d+-{code}oyde\.usfm$",
        "edition": "OYDETW / oyde",
        "edition_source_id": "SRC-400",
        "package_source_id": "SRC-401",
        "source_ids": {"SRC-400", "SRC-401"},
    },
    {
        "reader_prefix": "yemsa-",
        "language_tag": "jnj",
        "module_path_regex": r"::\d+-{code}jnje\.usfm$",
        "edition": "JNJETW / jnje",
        "edition_source_id": "SRC-407",
        "package_source_id": "SRC-408",
        "source_ids": {"SRC-407", "SRC-408"},
    },
    {
        "reader_prefix": "baiso-ethiopic-",
        "language_tag": "bsw",
        "module_path_regex": r"::\d+-{code}bswe\.usfm$",
        "edition": "BSWE",
        "edition_source_id": "SRC-412",
        "package_source_id": "SRC-413",
        "source_ids": {"SRC-412", "SRC-413"},
    },
)


def apply_standard_nt_research_crosswalks(archive: dict) -> int:
    """Index standard NT book modules by title while keeping readers research-only."""
    codes = [
        "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL",
        "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "1PE", "2PE", "1JN", "2JN", "3JN", "JAS", "JUD", "REV",
    ]
    church_source_ids = {"SRC-029", "SRC-384", "SRC-396"}
    readers_by_id = {reader.get("reader_id"): reader for reader in archive.get("readers", [])}
    corpora = archive.get("translation_registry", {}).get("research_corpora", [])
    corpora_by_reader = {corpus.get("reader_id"): corpus for corpus in corpora}
    canon_books = {book["canon_id"]: book for book in archive.get("canon_registry", {}).get("books", [])}
    sources_by_id = {source.get("source_id") for source in archive.get("sources", [])}
    if not church_source_ids.issubset(sources_by_id):
        raise ValueError("Standard NT crosswalk source records are missing")

    indexed = 0
    for number, code in enumerate(codes, 1):
        canon_id = f"eotc-nt-{number:02d}"
        book = canon_books.get(canon_id)
        if book is None:
            raise ValueError(f"Church-list entry {canon_id} is missing")
        suffix = f"-{code.lower()}-research"
        reader_ids = {
            reader_id for reader_id, reader in readers_by_id.items()
            if reader_id.endswith(suffix) and reader.get("research_corpus_id")
        }
        if not reader_ids:
            raise ValueError(f"No bundled research readers found for standard NT module {code}")
        if not reader_ids.issubset(corpora_by_reader):
            raise ValueError(f"Research corpus records missing for {code}: {sorted(reader_ids - corpora_by_reader.keys())}")

        evidence_ids = set(church_source_ids)
        for reader_id in sorted(reader_ids):
            reader = readers_by_id[reader_id]
            corpus = corpora_by_reader[reader_id]
            if not reader.get("source_pages") or code.lower() not in reader["source_pages"].lower():
                raise ValueError(f"Source member code {code} is not visible in {reader_id}'s stored source location")
            state = corpus.get("canon_mapping_state")
            prior_note = corpus.get("canon_mapping_note", "")
            # These source packages expose the conventional standard NT codes
            # in retained publisher USFM member paths. Review only those exact
            # module/title matches; no translation or canon link is promoted.
            reviewed_package = next((package for package in REVIEWED_NT_PACKAGE_CROSSWALKS
                                     if reader_id.startswith(package["reader_prefix"])
                                     and reader.get("language_tag") == package["language_tag"]
                                     and package["source_ids"].issubset(set(reader.get("source_ids", [])))
                                     and re.search(
                                         package["module_path_regex"].format(code=re.escape(code)),
                                         reader.get("source_pages", ""), re.I,
                                     )), None)
            if reviewed_package:
                expected_id = f"{reviewed_package['reader_prefix']}{code.lower()}-research"
                if reader_id != expected_id:
                    raise ValueError(f"Unexpected reader identity for reviewed module {code}: {reader_id}")
                if state not in {"not_mapped", "uncertain", "reviewed_match"}:
                    raise ValueError(f"Unexpected package title mapping state for {reader_id}: {state!r}")
                corpus["canon_mapping_state"] = "reviewed_match"
                corpus["candidate_canon_id"] = canon_id
                corpus["canon_mapping_note"] = (
                    f"Reviewed work/title candidate: publisher module {code} in edition {reviewed_package['edition']} is preserved as "
                    f"{reader.get('source_pages')} ({reviewed_package['package_source_id']}); its edition page identifies the named work "
                    f"({reviewed_package['edition_source_id']}); the official USFM table defines code {code} (SRC-396), "
                    f"and the Church's English list names the corresponding work at {canon_id} (SRC-029). This is a "
                    "title-level crosswalk only. It does not establish Orthodox edition identity or affiliation, textual "
                    "equivalence, completeness, translation ancestry, or accuracy. Reader-level provenance, rights, "
                    "and extraction limits remain in the cited records."
                )
                state = "reviewed_match"
                prior_note = corpus["canon_mapping_note"]
            if state == "not_mapped":
                corpus["canon_mapping_state"] = "uncertain"
                corpus["candidate_canon_id"] = canon_id
                corpus["canon_mapping_note"] = (
                    f"The full provider package is not crosswalked to an Ethiopian or Eritrean Orthodox canon. This specific bundled {code} member is "
                    f"linked provisionally to Church-list entry {canon_id} by the standard USFM member code {code}. This work/title candidate does not "
                    "establish EOTC or Eritrean affiliation, edition identity, translation ancestry, completeness, or accuracy. Reader-specific source, "
                    "translation-basis, rights, and review limits remain in this record and its cited edition sources."
                )
            elif state == "uncertain":
                if corpus.get("candidate_canon_id") != canon_id:
                    raise ValueError(f"Conflicting candidate link for {reader_id}: {corpus.get('candidate_canon_id')!r}")
                addition = (
                    f" This standard {code} book/title candidate does not establish EOTC or Eritrean affiliation, exact edition identity, "
                    "translation ancestry, completeness, or accuracy."
                )
                if addition.strip() not in prior_note:
                    corpus["canon_mapping_note"] = prior_note.rstrip() + addition
            elif state == "reviewed_match":
                if corpus.get("candidate_canon_id") != canon_id:
                    raise ValueError(f"Conflicting reviewed link for {reader_id}: {corpus.get('candidate_canon_id')!r}")
            else:
                raise ValueError(f"Unexpected standard NT mapping state for {reader_id}: {state!r}")
            corpus["source_ids"] = sorted(set(corpus.get("source_ids", [])) | church_source_ids,
                                          key=lambda value: int(value.rsplit("-", 1)[1]))
            evidence_ids.update(corpus["source_ids"])

        languages = {readers_by_id[reader_id].get("language_tag") for reader_id in reader_ids}
        summary = (
            f"{len(reader_ids)} separately scoped research readers across {len(languages)} language tags; these are standard-module work/title "
            "candidates, not verified Ethiopian or Eritrean Orthodox editions and not canon-linked coverage."
        )
        status_note = f" Bundled research views: {summary}"
        current_status = book.get("reader_status", "")
        if status_note.strip() not in current_status:
            book["reader_status"] = (current_status.rstrip() + status_note).strip()
        # Keep the canon record's citations scoped to its label/title mapping.
        # Corpus and edition provenance stays on each corpus/reader and is
        # indexed separately on the catalogue row below.
        book_source_ids = set(book.get("source_ids", []))
        # A registry generated by an earlier build may already contain the
        # research corpus citations. Remove those corpus-only citations here;
        # the Church label and USFM reference are the evidence for this mapping.
        book_source_ids.difference_update(evidence_ids - church_source_ids)
        book_source_ids.update(church_source_ids)
        book["source_ids"] = sorted(book_source_ids,
                                    key=lambda value: int(value.rsplit("-", 1)[1]))
        prior_mapping = book.get("mapping_note", "")
        mapping_marker = f"Standard module {code} has source-backed research readers."
        if mapping_marker not in prior_mapping:
            addition = (
                f" {mapping_marker} Their title-level candidate links are separate from identification "
                "of the Church-list edition, its textual ancestry, or its complete contents."
            )
            book["mapping_note"] = prior_mapping.rstrip() + addition

        for catalogue_id in book.get("catalogue_ids", []):
            catalogue = next((item for item in archive.get("catalogue", []) if item.get("catalogue_id") == catalogue_id), None)
            if catalogue is None:
                raise ValueError(f"Catalogue row {catalogue_id} for {canon_id} is missing")
            current_availability = catalogue.get("text_availability_status", "")
            availability = f"{summary} Per-reader units, rights, and verification are recorded individually."
            if availability not in current_availability:
                catalogue["text_availability_status"] = (current_availability.rstrip() + " " + availability).strip()
            catalogue["evidence_source_ids"] = sorted(set(catalogue.get("evidence_source_ids", [])) | evidence_ids,
                                                       key=lambda value: int(value.rsplit("-", 1)[1]))
            reviewer_note = f"Research-reader inventory for standard module {code}: {summary}"
            if reviewer_note not in catalogue.get("reviewer_notes", ""):
                catalogue["reviewer_notes"] = " ".join(filter(None, [catalogue.get("reviewer_notes", "").rstrip(), reviewer_note])).strip()
            catalogue["verification_date"] = "2026-10-26"
        indexed += len(reader_ids)
    return indexed


# These are title-level discovery links only. Codes with no one-to-one match
# in the Church's list stay unmapped: e.g. 1ES/2ES, 4MA, BAR/BEL/LAM/LJE,
# MAN, PS2, SUS, and WIS. Grouped or differently scoped titles such as
# Tegsats and Metsihafe Tibeb are not inferred from a superficially similar
# standard code.
STANDARD_OT_USFM_CROSSWALK = {
    "GEN": 1, "EXO": 2, "LEV": 3, "NUM": 4, "DEU": 5, "JOS": 6, "JDG": 7, "RUT": 8,
    "1SA": 9, "2SA": 9, "1KI": 10, "2KI": 10, "1CH": 11, "2CH": 12,
    "EZR": 15, "NEH": 15, "TOB": 17, "JDT": 18, "EST": 19, "ESG": 19,
    "1MA": 20, "2MA": 21, "3MA": 21, "JOB": 22, "PSA": 23, "PRO": 24,
    "ECC": 27, "SNG": 28, "ISA": 29, "JER": 30, "EZK": 31, "DAN": 32,
    "DAG": 32, "HOS": 33, "AMO": 34, "MIC": 35, "JOL": 36, "OBA": 37,
    "JON": 38, "NAM": 39, "HAB": 40, "ZEP": 41, "HAG": 42, "ZEC": 43,
    "MAL": 44, "SIR": 45,
}


def apply_standard_ot_research_crosswalks(archive: dict) -> int:
    """Expose standard-OT USFM modules as scoped research title candidates."""
    church_source_ids = {"SRC-029", "SRC-384"}
    sources_by_id = {item.get("source_id") for item in archive.get("sources", [])}
    if not church_source_ids.issubset(sources_by_id):
        raise ValueError("Standard OT title-crosswalk sources are missing")
    if "SRC-396" not in sources_by_id:
        raise ValueError("Official USFM/USX identifier reference SRC-396 is missing")
    for source in archive.get("sources", []):
        if source.get("source_id") in {"SRC-029", "SRC-396"}:
            source["local_review_url"] = "research/chronicles-title-crosswalk-review.md"
    books = {
        item.get("canon_id"): item
        for item in archive.get("canon_registry", {}).get("books", [])
    }
    readers = {item.get("reader_id"): item for item in archive.get("readers", [])}
    corpora = archive.get("translation_registry", {}).get("research_corpora", [])
    code_pattern = re.compile(
        r"(?:::|[/#])\d+-(" + "|".join(sorted(STANDARD_OT_USFM_CROSSWALK, key=len, reverse=True)) + r")"
    )
    indexed = 0
    affected_canon_ids = set()
    for corpus in corpora:
        reader = readers.get(corpus.get("reader_id"))
        if reader is None:
            continue
        match = code_pattern.search(str(reader.get("source_pages", "")))
        if match is None:
            continue
        code = match.group(1)
        canon_id = f"eotc-ot-{STANDARD_OT_USFM_CROSSWALK[code]:02d}"
        book = books.get(canon_id)
        if book is None:
            raise ValueError(f"Church-list entry {canon_id} for USFM module {code} is missing")
        corpus_id = corpus.get("corpus_id")
        if (reader.get("research_corpus_id") != corpus_id or reader.get("canon_id") is not None
                or corpus.get("reader_status") != "bundled_research_reader"):
            raise ValueError(f"Standard OT module {code} is not a separate bundled research reader: {corpus_id}")
        if not str(corpus.get("title", "")).strip():
            raise ValueError(f"Standard OT research corpus {corpus_id} has no displayed title")

        state = corpus.get("canon_mapping_state")
        candidate_id = corpus.get("candidate_canon_id")
        if code == "JOB":
            if state not in {"not_mapped", "uncertain", "reviewed_match"}:
                raise ValueError(f"Unexpected Job title mapping state for {corpus_id}: {state!r}")
            if candidate_id not in {None, canon_id}:
                raise ValueError(f"Conflicting Job title candidate for {corpus_id}: {candidate_id!r}")
            corpus["canon_mapping_state"] = "reviewed_match"
            corpus["candidate_canon_id"] = canon_id
            corpus["canon_mapping_note"] = (
                "Reviewed work/title match only: the Church-list source names Job at eotc-ot-22 (SRC-029); "
                "this retained standard USFM member uses the JOB identifier (SRC-384), which the official "
                "USFM/USX 3.2 book table defines as Job (SRC-396). This supports discovery by shared work/title "
                "only. It does not establish Ethiopian or Eritrean Orthodox affiliation, Geʽez or Church-edition "
                "identity, textual or chapter-boundary equivalence, translation ancestry, completeness, or accuracy. "
                "The reader remains research-only and is excluded from canon-linked coverage."
            )
            corpus["source_ids"] = sorted(
                set(corpus.get("source_ids", [])) | {"SRC-396"},
                key=lambda value: int(value.rsplit("-", 1)[1]),
            )
        elif code in {"1CH", "2CH"}:
            expected_id = "eotc-ot-11" if code == "1CH" else "eotc-ot-12"
            if canon_id != expected_id:
                raise ValueError(f"Chronicles code {code} resolves to unexpected Church-list entry {canon_id}")
            if state not in {"not_mapped", "uncertain", "reviewed_match"}:
                raise ValueError(f"Unexpected Chronicles title mapping state for {corpus_id}: {state!r}")
            if candidate_id not in {None, canon_id}:
                raise ValueError(f"Conflicting Chronicles title candidate for {corpus_id}: {candidate_id!r}")
            church_title = "I Chronicles" if code == "1CH" else "II Chronicles"
            orthodox_alt = "1 Paralipomenon" if code == "1CH" else "2 Paralipomenon"
            corpus["canon_mapping_state"] = "reviewed_match"
            corpus["candidate_canon_id"] = canon_id
            corpus["canon_mapping_note"] = (
                f"Reviewed work/title match only: the Church's cited English list names {church_title} at {canon_id} "
                f"(SRC-029); this retained source member is identified by standard USFM code {code} (SRC-384), "
                f"which the official USFM/USX 3.2 table defines as {church_title} and gives {orthodox_alt} as an "
                "Orthodox alternative title (SRC-396). This supports discovery by shared work/title only. It does not "
                "establish Ethiopian or Eritrean Orthodox affiliation, a particular edition or recension, textual or "
                "chapter-boundary equivalence, translation ancestry, completeness, or accuracy. The reader remains "
                "research-only and is excluded from canon-linked coverage."
            )
            corpus["source_ids"] = sorted(
                set(corpus.get("source_ids", [])) | {"SRC-396"},
                key=lambda value: int(value.rsplit("-", 1)[1]),
            )
        elif state == "not_mapped":
            if candidate_id is not None:
                raise ValueError(f"Unmapped OT corpus {corpus_id} unexpectedly has candidate {candidate_id}")
            corpus["canon_mapping_state"] = "uncertain"
            corpus["candidate_canon_id"] = canon_id
            corpus["canon_mapping_note"] = (
                f"The Church-list source names this work at {canon_id} (SRC-029). The stored source location identifies "
                f"standard USFM member code {code} (SRC-384), so this archive links it as an uncertain work/title candidate "
                "for discovery. This does not establish EOTC or Eritrean affiliation, edition identity, textual scope or "
                "boundaries, translation ancestry, completeness, or accuracy. It remains a research text and is excluded "
                "from canon-linked reader coverage."
            )
        elif state in {"uncertain", "reviewed_match", "asserted_by_source"}:
            if candidate_id != canon_id:
                raise ValueError(f"Conflicting OT title candidate for {corpus_id}: {candidate_id!r} != {canon_id!r}")
            if state == "uncertain":
                corpus["canon_mapping_note"] = ensure_appended_note_once(
                    str(corpus.get("canon_mapping_note", "")),
                    f"The stored standard USFM module code {code} supports discovery by title only; it does not establish "
                    "EOTC or Eritrean affiliation, edition identity, textual scope, completeness, or accuracy.",
                )
        else:
            raise ValueError(f"Unexpected mapping state for standard OT module {code} in {corpus_id}: {state!r}")
        corpus["source_ids"] = sorted(
            set(corpus.get("source_ids", [])) | church_source_ids,
            key=lambda value: int(value.rsplit("-", 1)[1]),
        )
        affected_canon_ids.add(canon_id)
        indexed += 1

    for canon_id in sorted(affected_canon_ids):
        book = books[canon_id]
        candidates = [
            corpus for corpus in corpora
            if corpus.get("candidate_canon_id") == canon_id
            and corpus.get("canon_mapping_state") in {"uncertain", "reviewed_match", "asserted_by_source"}
            and corpus.get("reader_status") == "bundled_research_reader"
            and corpus.get("reader_id") in readers
        ]
        languages = {corpus.get("language_tag") for corpus in candidates if corpus.get("language_tag")}
        title = str(book.get("display_name") or book.get("source_label") or canon_id)
        summary = (
            f"{len(candidates)} separately scoped {title} title-candidate research readers across {len(languages)} language tags; "
            "these are discovery links, not verified Ethiopian or Eritrean Orthodox editions or canon-linked readers."
        )
        count_note_pattern = re.compile(
            rf"(?:No canon-linked reader\.\s*)?\d+ separately scoped {re.escape(title)} "
            r"title-candidate research readers across \d+ language tags;[^.]*\."
        )
        all_evidence = set(church_source_ids)
        for corpus in candidates:
            corpus["source_ids"] = sorted(
                set(corpus.get("source_ids", [])) | church_source_ids,
                key=lambda value: int(value.rsplit("-", 1)[1]),
            )
            all_evidence.update(corpus.get("source_ids", []))
        # Research-reader provenance remains attached to the individual corpus
        # and catalogue availability record; it does not substantiate the
        # Church-list title mapping itself.
        book_source_ids = set(book.get("source_ids", []))
        book_source_ids.difference_update(all_evidence - church_source_ids)
        book_source_ids.update(church_source_ids)
        book["source_ids"] = sorted(
            book_source_ids,
            key=lambda value: int(value.rsplit("-", 1)[1]),
        )
        # Keep this field scoped to the Church-list reader itself. The older
        # Job record used it for research availability, so refresh that legacy
        # note there; other candidate counts belong in book-coverage.json and
        # catalogue availability, not in canon-reader status.
        if canon_id == "eotc-ot-22":
            book["reader_status"] = ensure_appended_note_once(
                count_note_pattern.sub("", str(book.get("reader_status", ""))).strip(),
                "No canon-linked reader. " + summary,
            )
        marker = f"Standard USFM title-candidate research readers are catalogued for {title}."
        book["mapping_note"] = ensure_appended_note_once(str(book.get("mapping_note", "")), marker)
        for catalogue_id in book.get("catalogue_ids", []):
            catalogue = next(
                (item for item in archive.get("catalogue", []) if item.get("catalogue_id") == catalogue_id),
                None,
            )
            if catalogue is None:
                raise ValueError(f"Catalogue record {catalogue_id} for {canon_id} is missing")
            catalogue_status_pattern = re.compile(
                rf"\d+ separately scoped {re.escape(title)} title-candidate research readers "
                r"across \d+ language tags;[^.]*\."
                r"(?: (?:Individual translation basis, rights, and review limits remain attached to each reader|"
                r"Per-reader source, rights, and review limits remain attached individually)\.)*"
            )
            prior_catalogue_status = catalogue_status_pattern.sub(
                "", str(catalogue.get("text_availability_status", ""))
            )
            prior_catalogue_status = re.sub(
                r"\s*(?:Per-reader source, rights, and review limits remain attached individually|"
                r"Individual translation basis, rights, and review limits remain attached to each reader)\.",
                "", prior_catalogue_status,
            ).strip()
            catalogue["text_availability_status"] = ensure_appended_note_once(
                prior_catalogue_status,
                summary + " Per-reader source, rights, and review limits remain attached individually.",
            )
            catalogue["evidence_source_ids"] = sorted(
                set(catalogue.get("evidence_source_ids", [])) | all_evidence,
                key=lambda value: int(value.rsplit("-", 1)[1]),
            )
            reviewer_note = (
                f"{summary} Module-code links were made by this archive for discovery and do not claim that the publishers "
                "identify these texts as Ethiopian Orthodox or that they share complete textual boundaries."
            )
            reviewer_note_pattern = re.compile(
                rf"\d+ separately scoped {re.escape(title)} title-candidate research readers across \d+ language tags;"
                r"[^.]*\. These are archive-authored title candidates from source module codes, not claims by the publishers "
                r"that their editions are Ethiopian Orthodox or share a complete textual scope\."
            )
            catalogue["reviewer_notes"] = ensure_appended_note_once(
                reviewer_note_pattern.sub("", str(catalogue.get("reviewer_notes", ""))).strip(), reviewer_note,
            )
    return indexed

def main() -> None:
    # The package has many independent source builders. Write outputs atomically
    # so a Windows file-scanner or open preview cannot leave a JSON file truncated.
    enable_atomic_path_writes()
    # Rebuild Gamo records from the checksummed local capture before loading
    # the archive so its reader candidates, source notes, and navigation stay
    # synchronized without fetching external data.
    build_gamo_research_readers()
    build_obadiah_reader()
    build_jonah_reader()
    build_nahum_reader()
    build_habakkuk_reader()
    build_zephaniah_reader()
    build_haggai_reader()
    build_joel_reader()
    build_amos_reader()
    build_malachi_reader()
    build_sirach_reader()
    from build_arabic_vandyck_readers import build as build_arabic_vandyck_readers
    build_arabic_vandyck_readers()
    # Mixed-rights Beta maṣāḥǝft Works texts are withheld from this public
    # distribution. Their source captures and reader JSON are absent here;
    # do not recreate them during a standalone build.
    from build_chronicles_discovery import build as build_chronicles_discovery
    build_chronicles_discovery()
    # Chronicles and Song of Songs mixed-rights text builders are likewise
    # intentionally not run. Their metadata-only discovery records remain.
    from build_isaiah_discovery import build as build_isaiah_discovery
    build_isaiah_discovery()
    from build_ecclesiastes_discovery import build as build_ecclesiastes_discovery
    build_ecclesiastes_discovery()
    from build_proverbs_discovery import build as build_proverbs_discovery
    build_proverbs_discovery()
    from build_job_discovery import build as build_job_discovery
    build_job_discovery()
    from build_gitsew_discovery import build as build_gitsew_discovery
    build_gitsew_discovery()
    from build_teezaz_discovery import build as build_teezaz_discovery
    build_teezaz_discovery()
    from build_abtilis_discovery import build as build_abtilis_discovery
    build_abtilis_discovery()
    from build_dominos_discovery import build as build_dominos_discovery
    build_dominos_discovery()
    from build_sirate_tsion_discovery import build as build_sirate_tsion_discovery
    build_sirate_tsion_discovery()
    from build_eotc_english_edition_leads import build as build_eotc_english_edition_leads
    build_eotc_english_edition_leads()
    from build_canon_registry import main as build_canon_registry
    build_canon_registry()
    from build_gitsew_translation_lead import build as build_gitsew_translation_lead
    build_gitsew_translation_lead()
    from build_eritrea_canon_evidence import main as build_eritrea_canon_evidence
    build_eritrea_canon_evidence()
    from build_ezra_nehemia_discovery import build as build_ezra_nehemia_discovery
    build_ezra_nehemia_discovery()
    from build_tegsats_discovery import build as build_tegsats_discovery
    build_tegsats_discovery()
    # Preserve the EAP manuscript discovery/access notice in the local source
    # registry without treating it as an edition-level text or reuse license.
    from build_ezra_sutuel_discovery import build as build_ezra_sutuel_discovery
    build_ezra_sutuel_discovery()
    from build_metsihafe_tibeb_discovery import build as build_metsihafe_tibeb_discovery
    build_metsihafe_tibeb_discovery()
    from build_clement_english_lead import build as build_clement_english_lead
    build_clement_english_lead()
    from build_josippon_discovery import build as build_josippon_discovery
    build_josippon_discovery()
    from build_didascalia_discovery import build as build_didascalia_discovery
    build_didascalia_discovery()
    from build_didascalia_ocr_view import build as build_didascalia_ocr_view
    build_didascalia_ocr_view()
    archive = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    from build_betamasaheft_license_audit import (
        build as build_betamasaheft_license_audit,
        public_payload_paths,
        remove_public_payloads,
    )
    beta_payload_paths = public_payload_paths(archive)
    build_betamasaheft_license_audit(archive)
    remove_public_payloads(beta_payload_paths)
    if any(path.exists() for path in beta_payload_paths):
        raise ValueError("A rights-withheld Beta scripture text is still present in the public tree.")
    from build_webbe_research_readers import build as build_webbe_research_readers
    webbe_readers, webbe_corpora, webbe_sources, webbe_capture_manifest = build_webbe_research_readers(
        archive.get("sources", [])
    )
    # Preserve the authoritative USFM identifier table used to distinguish
    # standard book codes from Brenton's historical Septuagint headings.
    usfm_reference = {
        "source_id": "SRC-384",
        "source_name": "YouVersion Platform — USFM Reference: standard book identifiers",
        "url": "https://developers.youversion.com/usfm-reference",
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The reference defines standard three-character USFM book identifiers and gives English names and alternatives. "
            "It explicitly distinguishes 1SA/2SA (1/2 Samuel; also called 1/2 Kings or Kingdoms in Orthodox Bibles) from 1KI/2KI (1/2 Kings; also called 3/4 Kings or Kingdoms), "
            "and identifies SNG as Song of Songs/Song of Solomon and DAG as the longer Greek Septuagint Daniel. "
            "This supports standard code interpretation and discovery links only; it does not establish Ethiopian Orthodox canon mappings, a specific edition's content, or text alignment."
        ),
        "archive_status": "Official format reference for standard USFM identifiers and selected alternative book names; not canon or text-alignment evidence",
    }
    archive["sources"] = sorted(
        [source for source in archive.get("sources", []) if source.get("source_id") != "SRC-384"]
        + webbe_sources + [usfm_reference],
        key=lambda source: int(source["source_id"].rsplit("-", 1)[1]),
    )
    from build_brenton_research_readers import main as build_brenton_research_readers
    build_brenton_research_readers()
    amharic_readers, amharic_corpora, amharic_sources = build_amharic_research_readers()
    from build_reigns_readers import build as build_reigns_research_readers
    reigns_readers, reigns_corpora, reigns_sources = build_reigns_research_readers()
    from build_kings_research_readers import build as build_kings_research_readers
    kings_readers, kings_corpora, kings_sources = build_kings_research_readers()
    maale_readers, maale_corpora, maale_sources, maale_source_manifest = build_maale_research_readers()
    gaz_readers, gaz_corpora, gaz_sources, gaz_source_manifest = build_gaz_research_readers()
    som_readers, som_corpora, som_sources, som_source_manifest = build_som_research_readers()
    lin_readers, lin_corpora, lin_sources, lin_source_manifest = build_lin_research_readers()
    oyda_readers, oyda_corpora, oyda_sources, oyda_source_manifest = build_oyda_research_readers()
    yemsa_readers, yemsa_corpora, yemsa_sources, yemsa_source_manifest = build_yemsa_research_readers()
    dawro_readers, dawro_corpora, dawro_sources, dawro_source_manifest = build_dawro_research_readers()
    baiso_readers, baiso_corpora, baiso_sources, baiso_source_manifests = build_baiso_research_readers()
    alaba_readers, alaba_corpora, alaba_sources, alaba_source_manifest = build_alaba_kabeena_research_readers()
    for reader in amharic_readers:
        (ROOT / "readers" / f"{reader['reader_id']}.json").write_text(
            json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    for reader in reigns_readers:
        (ROOT / "readers" / f"{reader['reader_id']}.json").write_text(
            json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    for reader in kings_readers:
        (ROOT / "readers" / f"{reader['reader_id']}.json").write_text(
            json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    gamo_titles = build_gamo_title_normalization()
    (ROOT / "research" / "gamo-title-normalization.json").write_bytes(
        (json.dumps(gamo_titles, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    # Title normalization mutates reader metadata, so create portable layer
    # checksums only after the final Gamo reader files have been written.
    build_gamo_text_layers()
    # Source-backed reader JSON files are merged offline; companion-only files are nested by their builder.
    reader_files = sorted((ROOT / "readers").glob("*-geez.json")) + [
        ROOT / "readers" / "jubilees-geez-hacohen.json",
        ROOT / "readers" / "enoch-geez-eotc.json",
        ROOT / "readers" / "psalms-geez-ludolf.json",
        ROOT / "readers" / "mark-research-tei.json",
        ROOT / "readers" / "matthew-betamasaheft-tei.json",
        ROOT / "readers" / "luke-betamasaheft-tei.json",
        ROOT / "readers" / "john-betamasaheft-tei.json",
        ROOT / "readers" / "acts-betamasaheft-tei.json",
        ROOT / "readers" / "esther-betamasaheft-tei.json",
        ROOT / "readers" / "judith-betamasaheft-tei.json",
        ROOT / "readers" / "revelation-betamasaheft-tei.json",
        ROOT / "readers" / "hosea-betamasaheft-tei.json",
        ROOT / "readers" / "micah-betamasaheft-tei.json",
        ROOT / "readers" / "zechariah-betamasaheft-tei.json",
        ROOT / "readers" / "james-betamasaheft-tei.json",
        ROOT / "readers" / "hebrews-betamasaheft-tei.json",
        ROOT / "readers" / "first-peter-betamasaheft-tei.json",
        ROOT / "readers" / "second-peter-betamasaheft-tei.json",
        ROOT / "readers" / "first-john-betamasaheft-tei.json",
        ROOT / "readers" / "first-corinthians-betamasaheft-tei.json",
        ROOT / "readers" / "second-corinthians-betamasaheft-tei.json",
        ROOT / "readers" / "galatians-betamasaheft-tei.json",
        ROOT / "readers" / "ephesians-betamasaheft-tei.json",
        ROOT / "readers" / "philippians-betamasaheft-tei.json",
        ROOT / "readers" / "colossians-betamasaheft-tei.json",
        ROOT / "readers" / "first-thessalonians-betamasaheft-tei.json",
        ROOT / "readers" / "second-thessalonians-betamasaheft-tei.json",
        ROOT / "readers" / "first-timothy-betamasaheft-tei.json",
        ROOT / "readers" / "second-timothy-betamasaheft-tei.json",
        ROOT / "readers" / "titus-betamasaheft-tei.json",
        ROOT / "readers" / "ii-john-betamasaheft-tei-research.json",
        ROOT / "readers" / "iii-john-betamasaheft-tei-research.json",
        ROOT / "readers" / "jude-betamasaheft-tei-research.json",
        ROOT / "readers" / "romans-betamasaheft-tei.json",
        ROOT / "readers" / "job-brenton-lxx-1851.json",
        ROOT / "readers" / "tobit-brenton-lxx-1851.json",
        ROOT / "readers" / "tobit-geez-betamasaheft-eotced.json",
        ROOT / "readers" / "sirach-brenton-lxx-1851.json",
        ROOT / "readers" / "sirach-geez-dillmann-hacohen-tau.json",
        ROOT / "readers" / "wisdom-solomon-betamasaheft-tei-research.json",
        ROOT / "readers" / "obadiah-geez-bachmann-theot.json",
        ROOT / "readers" / "jonah-geez-lofgren-ghebre-tau.json",
        ROOT / "readers" / "nahum-geez-lofgren-ghebre-tau.json",
        ROOT / "readers" / "habakkuk-geez-lofgren-ghebre-tau.json",
        ROOT / "readers" / "zephaniah-geez-lofgren-hacohen-tau.json",
        ROOT / "readers" / "haggai-geez-lofgren-ghebre-tau.json",
        ROOT / "readers" / "joel-geez-dillmann-hacohen-tau.json",
        ROOT / "readers" / "amos-geez-pereira-ghebre-tau.json",
        ROOT / "readers" / "malachi-geez-lofgren-ghebre-tau.json",
        ROOT / "readers" / "philemon-betamasaheft-tei-research.json",
        ROOT / "readers" / "isaiah-betamasaheft-tei-research.json",
        ROOT / "readers" / "daniel-betamasaheft-tei.json",
        ROOT / "readers" / "first-chronicles-betamasaheft-tei-research.json",
        ROOT / "readers" / "second-chronicles-betamasaheft-tei-research.json",
        ROOT / "readers" / "song-of-songs-geez-betamasaheft-eotced.json",
        ROOT / "readers" / "ecclesiastes-geez-betamasaheft-eotced.json",
        ROOT / "readers" / "samuel-i-geez-research.json",
        ROOT / "readers" / "samuel-ii-geez-research.json",
        ROOT / "readers" / "kings-i-geez-research.json",
        ROOT / "readers" / "kings-ii-geez-research.json",
    ] + sorted((ROOT / "readers").glob("brenton-lxx-*-research.json")) + sorted(
        (ROOT / "readers").glob("gamo-*-research.json")
    ) + sorted(
        (ROOT / "readers").glob("amh2003-*-research.json")
    ) + sorted(
        (ROOT / "readers").glob("arb-vd-*-research.json")
    ) + sorted(
        (ROOT / "readers").glob("maale-*-research.json")
    ) + sorted((ROOT / "readers").glob("gaz-*-research.json")) + sorted(
        (ROOT / "readers").glob("som-1979-2008-*-research.json")
    ) + sorted(
        (ROOT / "readers").glob("lin-2020-*-research.json")
    ) + sorted(
        (ROOT / "readers").glob("oyda-*-research.json")
    ) + sorted(
        (ROOT / "readers").glob("yemsa-*-research.json")
    ) + sorted((ROOT / "readers").glob("dawro-latin-*-research.json")) + sorted(
        (ROOT / "readers").glob("baiso-*-research.json")
    ) + sorted((ROOT / "readers").glob("alaba-kabeena-*-research.json")) + sorted(
        (ROOT / "readers").glob("webbe-2020-*-research.json")
    )
    current_readers = [json.loads(path.read_text(encoding="utf-8")) for path in reader_files if path.exists()]
    current_readers.sort(key=lambda reader: (
        0 if reader.get("canon_id") else 1,
        reader.get("canon_id") or reader.get("research_corpus_id", ""),
    ))
    current_ids = {reader.get("reader_id") for reader in current_readers}
    archive["readers"] = [reader for reader in archive.get("readers", []) if reader.get("reader_id") not in current_ids] + current_readers
    reader_package_paths = {}
    for path in (ROOT / "readers").glob("*.json"):
        package_record = json.loads(path.read_text(encoding="utf-8"))
        package_reader_id = package_record.get("reader_id")
        if package_reader_id:
            if package_reader_id in reader_package_paths:
                raise ValueError(f"Reader {package_reader_id} has more than one local JSON package.")
            reader_package_paths[package_reader_id] = path
    reader_package_digests = {}
    for reader in archive["readers"]:
        note = LANGUAGE_ASSIGNMENT_NOTES.get(reader.get("language_tag"))
        if note:
            if not reader.get("language_assignment_status"):
                reader["language_assignment_status"] = note
            reader_id = str(reader.get("reader_id", ""))
            if not re.fullmatch(r"[a-z0-9-]+", reader_id):
                raise ValueError(f"Unsafe reader ID for language metadata update: {reader_id!r}.")
            reader_path = reader_package_paths.get(reader_id)
            if reader_path is None:
                raise ValueError(f"Reader {reader_id} has no local JSON package for language metadata update.")
            package_record = json.loads(reader_path.read_text(encoding="utf-8"))
            if not package_record.get("language_assignment_status"):
                package_record["language_assignment_status"] = reader["language_assignment_status"]
                write_text_atomically(reader_path, json.dumps(package_record, ensure_ascii=False, indent=2) + "\n")
            reader_digest = hashlib.sha256(reader_path.read_bytes()).hexdigest()
            reader_package_digests[reader_path.resolve()] = reader_digest
    # Traverse each example once. Previously this JSON walk and its filesystem
    # path resolutions ran once per language-assigned reader, multiplying work
    # across the reader and example collections.
    for example_path in (ROOT / "examples").glob("*.json"):
        try:
            example = json.loads(example_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        package_changed = False
        uri_digest_cache = {}

        def refresh_package_hashes(value):
            nonlocal package_changed
            if isinstance(value, dict):
                package = value.get("content_package")
                if isinstance(package, dict) and package.get("uri"):
                    package_uri = unquote(str(package["uri"]))
                    if package_uri not in uri_digest_cache:
                        package_paths = (
                            (ROOT / package_uri).resolve(),
                            (example_path.parent / package_uri).resolve(),
                        )
                        uri_digest_cache[package_uri] = next(
                            (reader_package_digests[path] for path in package_paths if path in reader_package_digests),
                            None,
                        )
                    reader_digest = uri_digest_cache[package_uri]
                    if reader_digest and package.get("sha256") != reader_digest:
                        package["sha256"] = reader_digest
                        package_changed = True
                for child in value.values():
                    refresh_package_hashes(child)
            elif isinstance(value, list):
                for child in value:
                    refresh_package_hashes(child)

        refresh_package_hashes(example)
        if package_changed:
            write_text_atomically(example_path, json.dumps(example, ensure_ascii=False, indent=2) + "\n")
    canon_path = ROOT / "canon-registry.json"
    if canon_path.exists():
        registry = json.loads(canon_path.read_text(encoding="utf-8"))
        archive["canon_registry"] = registry
    language_registry_path = ROOT / "translation-registry.json"
    if language_registry_path.exists():
        archive["translation_registry"] = json.loads(language_registry_path.read_text(encoding="utf-8"))
    from build_enoch_charles_source_capture import apply as apply_enoch_charles_source_capture
    apply_enoch_charles_source_capture(archive)
    from build_enoch_laurence_discovery import apply as apply_enoch_laurence_discovery
    apply_enoch_laurence_discovery(archive)
    from build_enoch_two_three import apply as apply_enoch_two_three
    apply_enoch_two_three(archive)
    from build_canon_comparison_review import apply as apply_canon_comparison_review
    apply_canon_comparison_review(archive)
    webbe_corpus_ids = {corpus["corpus_id"] for corpus in webbe_corpora}
    archive["translation_registry"]["research_corpora"] = [
        corpus for corpus in archive["translation_registry"].get("research_corpora", [])
        if corpus.get("corpus_id") not in webbe_corpus_ids
    ] + webbe_corpora
    apply_english_availability_survey(archive)
    apply_eritrean_arabic_survey(archive)
    from build_arabic_vandyck_readers import apply as apply_arabic_vandyck_readers
    apply_arabic_vandyck_readers(archive)
    from build_tigrinya_discovery import apply as apply_tigrinya_discovery
    apply_tigrinya_discovery(archive)
    from build_tigrinya_ebible_index_check import apply as apply_tigrinya_ebible_index_check
    apply_tigrinya_ebible_index_check(archive)
    from build_gamo_2011_nt_discovery import apply as apply_gamo_2011_nt_discovery
    apply_gamo_2011_nt_discovery(archive)
    from build_tau_platt_nt_menu_audit import apply as apply_tau_platt_nt_menu_audit
    apply_tau_platt_nt_menu_audit(archive)
    from build_bilen_mark_facsimile import apply as apply_bilen_mark_facsimile
    apply_bilen_mark_facsimile(archive)
    from build_maale_strategy_example import apply as apply_maale_strategy_example
    apply_maale_strategy_example(archive)
    translation_registry = archive["translation_registry"]
    process_evidence = [
        item for item in translation_registry.get("translation_process_evidence", [])
        if item.get("record_id") not in {"twftw-gamo-project-history-2022", "twftw-maale-translator-bio"}
    ]
    process_evidence.extend([
        {
            "record_id": "twftw-gamo-project-history-2022",
            "language_tag": "gmv",
            "record_type": "project_history",
            "claim_summary": "The Word for the World reports that the Gamo New Testament was completed in January 2012 and a full Bible was dedicated in August 2022, with local Gamo translators and checkers participating.",
            "participants": [
                {"agent_type": "organization", "name": "The Word for the World", "claimed_role": "project agency"},
                {"agent_type": "community_team", "name": "Gamo local translators and checkers (individuals not named in the article)", "claimed_role": "translation and checking team"},
            ],
            "edition_link_status": "not_established",
            "edition_ids": [],
            "translation_path_status": "not_stated",
            "milestones": [
                {"event": "Gamo New Testament completion", "date": "2012-01", "date_precision": "month", "source_claim": "The article states that the New Testament was completed in January 2012."},
                {"event": "Gamo full-Bible dedication", "date": "2022-08", "date_precision": "month", "source_claim": "The article says the full Bible dedication took place in August 2022."},
            ],
            "source_ids": ["SRC-168", "SRC-375"],
            "limitations": "The article does not name individual translators, state a source or relay language, identify an edition ID, or establish textual identity with the captured 2024 GMVETW/gmve edition.",
        },
        {
            "record_id": "twftw-maale-translator-bio",
            "language_tag": "mdy",
            "record_type": "individual_contribution",
            "claim_summary": "The Word for the World biography says Tamene Lale Gego translated a complete Bible into his mother tongue, Maale.",
            "participants": [
                {"agent_type": "person", "name": "Tamene Lale Gego", "claimed_role": "translator (as stated in the agency biography)"},
            ],
            "edition_link_status": "not_established",
            "edition_ids": [],
            "translation_path_status": "not_stated",
            "milestones": [],
            "source_ids": ["SRC-363", "SRC-374"],
            "limitations": "The biography does not date this work or identify the 2008 MDYTWF/mdyeth edition; the edition-level translator field remains as listed by the publisher. No source or relay language is stated.",
        },
    ])
    translation_registry["translation_process_evidence"] = sorted(process_evidence, key=lambda item: item["record_id"])
    existing_amharic_corpora = [
        item for item in translation_registry.get("research_corpora", [])
        if not item.get("corpus_id", "").startswith("amh2003-")
    ]
    translation_registry["research_corpora"] = sorted(
        [
            item for item in existing_amharic_corpora
            if item.get("corpus_id") not in {
                corpus["corpus_id"] for corpus in reigns_corpora + kings_corpora
            }
        ] + amharic_corpora + reigns_corpora + kings_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "mdy"] + maale_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "gaz"] + gaz_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "so"] + som_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "ln"] + lin_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "oyd"] + oyda_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "jnj"] + yemsa_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "dwr"] + dawro_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "bsw"] + baiso_corpora,
        key=lambda item: item["corpus_id"],
    )
    translation_registry["research_corpora"] = sorted(
        [item for item in translation_registry["research_corpora"]
         if item.get("language_tag") != "alw"] + alaba_corpora,
        key=lambda item: item["corpus_id"],
    )
    if not any(language.get("language_tag") == "ln" for language in translation_registry.get("languages", [])):
        translation_registry.setdefault("languages", []).append({
            "language_tag": "ln",
            "language_name": "Lingala (Lingála)",
            "script_code": "Latn",
            "script_codes": ["Latn"],
            "script_profile_note": (
                "IANA identifies ln as Lingala and records Latn as its Suppress-Script value. This edition's digital files use Latin script; "
                "the registry does not establish every community's language variety or writing practice."
            ),
            "direction": "ltr",
            "records": [],
            "source_ids": ["SRC-077", "SRC-078", "SRC-393", "SRC-394", "SRC-395"],
            "availability_survey": {
                "status": "completed",
                "scope": "Inspected one official eBible.org Lingala edition record and its source package, copyright notice, and language/script authorities. This bounded acquisition check is not a Lingala scripture census or provider-complete survey.",
                "searched_at": "2026-10-26",
                "result": "records_found",
                "result_count": 1,
                "source_ids": ["SRC-393", "SRC-394", "SRC-395", "SRC-077", "SRC-078"],
                "notes": "One CC BY-SA 4.0 edition (LINBIB / lin) is bundled as 66 unmapped research readers. The publisher's conventional 66 USFM modules do not establish Ethiopian/Eritrean Orthodox canon equivalence, printed completeness, community review, or translation accuracy.",
            },
        })
    oyda_profile = next((language for language in translation_registry.get("languages", [])
                         if language.get("language_tag") == "oyd"), None)
    if oyda_profile is None:
        oyda_profile = {
            "language_tag": "oyd",
            "language_name": "Oyda",
            "script_code": "Ethi",
            "script_codes": ["Ethi"],
            "script_profile_note": (
                "IANA's retained 2026-09-17 registry identifies `oyd` as Oyda. The specific eBible.org OYDETW / oyde edition page identifies "
                "Ethiopic script. This is witness-level evidence, not a claim that all Oyda communities or materials use only this script."
            ),
            "direction": "ltr",
            "records": [],
            "source_ids": ["SRC-077", "SRC-078", *[source["source_id"] for source in oyda_sources]],
            "availability_survey": {},
        }
        translation_registry.setdefault("languages", []).append(oyda_profile)
    oyda_profile["source_ids"] = sorted(
        set(oyda_profile.get("source_ids", [])) | {"SRC-077", "SRC-078"} | {source["source_id"] for source in oyda_sources},
        key=lambda value: int(value.split("-")[1]),
    )
    oyda_profile["script_code"] = "Ethi"
    oyda_profile["script_codes"] = sorted(set(oyda_profile.get("script_codes", [])) | {"Ethi"})
    oyda_profile["script_profile_note"] = (
        "IANA's retained 2026-09-17 registry identifies `oyd` as Oyda. The specific eBible.org OYDETW / oyde edition page identifies "
        "Ethiopic script. This is witness-level evidence, not a claim that all Oyda communities or materials use only this script."
    )
    oyda_profile["availability_survey"] = {
        "status": "completed",
        "scope": "Inspected one official eBible.org Oyda edition page, its linked USFM distribution and license notice, and the matching language/script identifiers. This is a single-provider acquisition record, not a language-wide census, complete text review, translation-basis review, or EOTC/Eritrean canon survey.",
        "searched_at": "2026-10-26",
        "result": "records_found",
        "result_count": 1,
        "source_ids": ["SRC-077", "SRC-078", *[source["source_id"] for source in oyda_sources]],
        "notes": "One eBible.org edition (OYDETW / oyde) is bundled as 27 CC BY-SA 4.0 research readers. The publisher's conventional New Testament modules are not mapped to the EOTC or Eritrean Orthodox canon and are not counted as canon-linked coverage. Translation basis, accuracy, community review, and print completeness remain unknown. Other providers have not been surveyed.",
    }
    yemsa_profile = next((language for language in translation_registry.get("languages", [])
                          if language.get("language_tag") == "jnj"), None)
    if yemsa_profile is None:
        yemsa_profile = {
            "language_tag": "jnj",
            "language_name": "Yemsa",
            "script_code": "Ethi",
            "script_codes": ["Ethi"],
            "script_profile_note": (
                "IANA's retained 2026-09-17 registry identifies `jnj` as Yemsa. The specific eBible.org JNJETW / jnje edition page identifies "
                "Ethiopic script. This is witness-level evidence, not a claim that all Yemsa communities or materials use only this script."
            ),
            "direction": "ltr",
            "records": [],
            "source_ids": ["SRC-077", "SRC-078", *[source["source_id"] for source in yemsa_sources]],
            "availability_survey": {},
        }
        translation_registry.setdefault("languages", []).append(yemsa_profile)
    yemsa_profile["source_ids"] = sorted(
        set(yemsa_profile.get("source_ids", [])) | {"SRC-077", "SRC-078"} | {source["source_id"] for source in yemsa_sources},
        key=lambda value: int(value.split("-")[1]),
    )
    yemsa_profile["script_code"] = "Ethi"
    yemsa_profile["script_codes"] = sorted(set(yemsa_profile.get("script_codes", [])) | {"Ethi"})
    yemsa_profile["script_profile_note"] = (
        "IANA's retained 2026-09-17 registry identifies `jnj` as Yemsa. The specific eBible.org JNJETW / jnje edition page identifies "
        "Ethiopic script. This is witness-level evidence, not a claim that all Yemsa communities or materials use only this script."
    )
    yemsa_profile["availability_survey"] = {
        "status": "completed",
        "scope": "Inspected one official eBible.org Yemsa edition page, its linked USFM distribution and license terms, and the matching IANA language identifier and ISO script code. This is a single-provider acquisition record, not a language-wide scripture census, full text review, translation-basis review, or EOTC/Eritrean Orthodox canon survey.",
        "searched_at": "2026-10-26",
        "result": "records_found",
        "result_count": 1,
        "source_ids": ["SRC-077", "SRC-078", *[source["source_id"] for source in yemsa_sources]],
        "notes": "One eBible.org edition (JNJETW / jnje) is bundled as 27 CC BY-SA 4.0 research readers. The publisher's conventional New Testament modules are not mapped to the EOTC or Eritrean Orthodox canon and are not counted as canon-linked coverage. Translation basis, accuracy, local community review, and print completeness remain unknown. Other providers have not been surveyed.",
    }
    dawro_profile = next((language for language in translation_registry.get("languages", [])
                          if language.get("language_tag") == "dwr"), None)
    if dawro_profile is None:
        raise ValueError("The established Dawro language profile must exist before adding edition readers.")
    dawro_profile["source_ids"] = sorted(
        set(dawro_profile.get("source_ids", [])) | {"SRC-077", "SRC-403", "SRC-404", "SRC-405", "SRC-406"},
        key=lambda value: int(value.split("-")[1]),
    )
    dawro_profile["script_code"] = "Zzzz"
    dawro_profile["script_codes"] = sorted(set(dawro_profile.get("script_codes", [])) | {"Ethi", "Latn"})
    dawro_profile["script_profile_note"] = (
        "The retained eBible.org index shows three Dawro resource identifiers (DWRENT, DWRNT, DWRLTW/dwrl), a bounded provider-index observation, "
        "not three translations or an exhaustive language survey. The DWRLTW / dwrl edition page identifies Latin script; the separate DWRENT record identifies "
        "Ethiopic script. The DWRLTW / dwrl text is separately licensed CC BY-SA 4.0 and bundled as 66 unmapped research readers. Zzzz remains the legacy single-script "
        "value because this language profile covers more than one observed script; this does not describe every Dawro community or witness."
    )
    dawro_profile["availability_survey"] = {
        "status": "completed",
        "scope": (
            "Counted three distinct Dawro identifiers shown in the captured Ethiopia portion of eBible.org's Bible index (DWRENT, DWRNT, and DWRLTW/dwrl); "
            "then inspected the DWRLTW / dwrl edition and rights page and its linked 2024 Latin-script USFM package. The count is provider-index labels, not distinct "
            "translation projects, text units, all Dawro resources, or a complete language/canon survey."
        ),
        "searched_at": "2026-10-26",
        "result": "records_found",
        "result_count": 3,
        "source_ids": ["SRC-403", "SRC-404", "SRC-405", "SRC-406"],
        "notes": (
            "The DWRLTW / dwrl Latin-script edition is bundled as 66 CC BY-SA 4.0 research readers; it is not mapped to an EOTC or Eritrean Orthodox canon. "
            "The index's DWRENT and DWRNT entries remain distinct leads: the current captures do not establish their text scope or map the older mixed-license page's "
            "separate notices to each file. No source/relay language, accuracy, community review, or printed completeness is inferred."
        ),
    }
    dawro_lead = next((item for item in translation_registry.get("corpus_leads", [])
                       if item.get("corpus_id") == "ethiopia-dawro-ebible-resources"), None)
    if dawro_lead:
        dawro_lead["scope_description"] = (
            "The 2026-10-26 eBible.org index capture shows three Dawro labels: DWRENT, DWRNT, and DWRLTW/dwrl (SRC-403). "
            "This aggregate lead concerns the index and the separately captured earlier mixed-license notice, not a unified edition. "
            "The DWRLTW/dwrl Latin-script edition has its own current title/license evidence and is bundled separately as 66 unmapped research readers (SRC-404–SRC-406). "
            "The two other identifiers are not silently mapped to that package or to the separate CC BY-NC-ND 3.0 and CC BY-SA 4.0 statements. "
            "Their exact contents, licensing, completeness, accuracy, and Church-list correspondence remain unresolved."
        )
        dawro_lead["text_bundled"] = False
        dawro_lead["source_ids"] = sorted(
            set(dawro_lead.get("source_ids", [])) | {"SRC-403"},
            key=lambda value: int(value.split("-")[1]),
        )
        dawro_lead["review_status"] = (
            "Aggregate discovery record for three index identifiers. DWRLTW/dwrl has a separately verified, locally bundled research corpus; "
            "the other two labels remain unresolved. This record itself does not represent a bundled text or prove distinct translation projects."
        )
        dawro_lead["notes"] = (
            "The earlier page with separate 2011 Holy Bible and New Testament rights blocks did not map either notice to its catalogue codes. "
            "Keep those unresolved products distinct from the 2024 DWRLTW/dwrl edition and its source-stated CC BY-SA 4.0 license."
        )
    baiso_profile = next((language for language in translation_registry.get("languages", [])
                          if language.get("language_tag") == "bsw"), None)
    if baiso_profile is None:
        baiso_profile = {
            "language_tag": "bsw",
            "language_name": "Baiso (Bayso)",
            "script_code": "Zzzz",
            "script_codes": ["Ethi", "Latn"],
            "script_profile_note": "IANA identifies bsw as Baiso. The two inspected eBible.org editions use Ethiopic and Latin scripts respectively; this describes these digital witnesses, not every Baiso writing practice.",
            "direction": "ltr",
            "records": [],
            "source_ids": ["SRC-077", "SRC-078", *[source["source_id"] for source in baiso_sources]],
            "availability_survey": {},
        }
        translation_registry.setdefault("languages", []).append(baiso_profile)
    baiso_profile["script_code"] = "Zzzz"
    baiso_profile["script_codes"] = sorted(set(baiso_profile.get("script_codes", [])) | {"Ethi", "Latn"})
    baiso_profile["source_ids"] = sorted(
        set(baiso_profile.get("source_ids", [])) | {"SRC-077", "SRC-078"} | {source["source_id"] for source in baiso_sources},
        key=lambda value: int(value.split("-")[1]),
    )
    baiso_profile["script_profile_note"] = (
        "IANA identifies bsw as Baiso. The eBible.org BSWETW / bswe edition and its retained USFM use Ethiopic script; "
        "the separate BSWLTW / bswl edition and its USFM use Latin script. These are observations about these two digital editions, "
        "not a claim about all Baiso communities, speakers, or writing practices."
    )
    baiso_profile["availability_survey"] = {
        "status": "completed",
        "scope": "Inspected two eBible.org Baiso edition pages, rights notices, and linked USFM packages, plus IANA language and ISO script identifiers. This is a two-edition, single-provider capture, not a language-wide or provider-complete survey and not an Orthodox-canon review.",
        "searched_at": "2026-10-26",
        "result": "records_found",
        "result_count": 2,
        "source_ids": ["SRC-077", "SRC-078", *[source["source_id"] for source in baiso_sources]],
        "notes": "The Ethiopic-script BSWETW / bswe package contains 27 conventional NT USFM modules; it is not crosswalked to an EOTC or Eritrean Orthodox canon. The separate Latin-script BSWLTW / bswl package contains 16 modules and omits 11 conventional NT book codes, which are listed explicitly and are not filled from the Ethiopic edition. Both providers state CC BY-SA 4.0 for translation text; original packages, notices, and hashes are retained. Translation basis, accuracy, community review, and print completeness remain unverified.",
    }
    alaba_profile = next((language for language in translation_registry.get("languages", [])
                          if language.get("language_tag") == "alw"), None)
    if alaba_profile is None:
        alaba_profile = {
            "language_tag": "alw",
            "language_name": "Alaba-K’abeena",
            "script_code": "Ethi",
            "script_codes": ["Ethi"],
            "script_profile_note": "IANA identifies alw as Alaba-K’abeena. The specific eBible.org ALWWTW / alw edition's retained USFM uses Ethiopic script; this is an edition-level observation, not a census of all Alaba-K’abeena writing practice.",
            "direction": "ltr",
            "records": [],
            "source_ids": ["SRC-077", "SRC-078", *[source["source_id"] for source in alaba_sources]],
            "availability_survey": {},
        }
        translation_registry.setdefault("languages", []).append(alaba_profile)
    alaba_profile["script_code"] = "Ethi"
    alaba_profile["script_codes"] = sorted(set(alaba_profile.get("script_codes", [])) | {"Ethi"})
    alaba_profile["source_ids"] = sorted(
        set(alaba_profile.get("source_ids", [])) | {"SRC-077", "SRC-078"} | {source["source_id"] for source in alaba_sources},
        key=lambda value: int(value.split("-")[1]),
    )
    alaba_profile["script_profile_note"] = (
        "IANA identifies alw as Alaba-K’abeena. The eBible.org ALWWTW / alw edition's retained USFM uses Ethiopic script; "
        "this describes the inspected digital witness, not every Alaba-K’abeena community or writing practice."
    )
    alaba_profile["availability_survey"] = {
        "status": "completed",
        "scope": "Inspected one official eBible.org Alaba-K’abeena edition, its copyright notice and linked USFM package, plus IANA language and ISO script identifiers. This bounded one-provider record is not a language-wide or provider-complete survey, complete text review, or Orthodox-canon survey.",
        "searched_at": "2026-10-26",
        "result": "records_found",
        "result_count": 1,
        "source_ids": ["SRC-077", "SRC-078", *[source["source_id"] for source in alaba_sources if source["source_id"] in {"SRC-414", "SRC-415"}]],
        "notes": "One eBible.org ALWWTW / alw New Testament is bundled as 27 CC BY-SA 4.0 research readers. Its conventional NT modules are not mapped to an EOTC or Eritrean Orthodox canon. The source pages do not name an individual translator or source/relay language. Package-to-reader extraction is checked; translation accuracy, local review, and print completeness are unknown. Other providers have not been surveyed. A separate Digital Bible Society ARC metadata record for an ALWWFTW / alw New Testament dated 2015 is recorded as an unbundled historical edition lead; its relationship to the 2025 edition is not established, and it is outside this one-provider survey.",
    }
    alaba_historical_lead = {
        "corpus_id": "alw-2015-halaba-new-testament-metadata",
        "title": "The Halaba New Testament (ALWWFTW, 2015) — metadata record",
        "language_tag": "alw",
        "language_name": "Alaba-K’abeena",
        "script_code": "Ethi",
        "publisher": "The Word for the World Ethiopia (as listed in ARC metadata)",
        "publication_year": "2015 (as listed in ARC metadata)",
        "scope_description": (
            "Digital Bible Society ARC metadata identifies a New Testament record called The Halaba New Testament, code ALWWFTW, published in 2015. "
            "No text is bundled. The relationship between this metadata record and eBible.org’s separate 2025 ALWWTW / alw New Testament is not established."
        ),
        "basis_language_tag": "und",
        "basis_description": "The cited ARC record does not identify a source or relay language; no translation path is inferred.",
        "translation_path": None,
        "contributors": "ARC identifies The Word for the World Ethiopia as agency; it does not name individual translators.",
        "text_bundled": False,
        "rights_status": (
            "ARC displays the metadata value RESERVED for the 2015 record. The underlying text and applicable terms were not inspected; "
            "the metadata is not a reuse license. No text or media from this record are bundled."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "The retained ARC metadata page was checked for title, code, date, language, script, agency, and license field. "
            "The underlying 2015 edition, exact text, translation path, translator identities, and relationship to the 2025 eBible witness were not independently verified."
        ),
        "source_ids": ["SRC-436"],
        "notes": (
            "Recorded as a distinct discovery record to preserve the 2015 catalog claim. Shared output language, language code, and publisher do not establish that it is an earlier edition, revision, or textual ancestor of ALWWTW / alw (2025). "
            "No EOTC or Eritrean Orthodox canon mapping is assigned."
        ),
    }
    translation_registry["corpus_leads"] = [
        lead for lead in translation_registry.get("corpus_leads", [])
        if lead.get("corpus_id") != alaba_historical_lead["corpus_id"]
    ] + [alaba_historical_lead]
    language_audit_path = ROOT / "language-script-code-audit.json"
    language_audit = json.loads(language_audit_path.read_text(encoding="utf-8"))
    language_codes = language_audit.setdefault("language_subtags", {}).setdefault("codes", [])
    language_codes[:] = sorted(set(language_codes) | {"oyd", "jnj", "bsw", "alw"})
    latest_check = language_audit.setdefault("latest_authority_check", {})
    latest_check["iana_language_or_extlang_codes_checked"] = len(language_codes)
    latest_check["evidence_source_ids"] = sorted(
        set(latest_check.get("evidence_source_ids", [])) | {"SRC-077"}
    )
    write_text_atomically(language_audit_path, json.dumps(language_audit, ensure_ascii=False, indent=2) + "\n")
    for language in translation_registry.get("languages", []):
        if language.get("language_tag") == "am":
            language["source_ids"] = sorted(
                set(language.get("source_ids", [])) | {"SRC-196", "SRC-197", "SRC-198"},
                key=lambda value: int(value.split("-")[1]),
            )
            language["script_profile_note"] = (
                "The profile identifies the Amharic language (am) and Ethiopic script (Ethi) for the inspected witnesses. "
                "It includes the permission-limited eBible.org AMH2003 New Testament research readers, but does not "
                "represent all Amharic orthographies, editions, translation paths, or church-canon mappings."
            )
            survey = language.get("availability_survey", {})
            survey["notes"] = (
                "The result_count of five applies only to the inspected Bible.com Amharic versions page, not all providers. "
                "A separate eBible.org AMH2003 New Testament is now bundled as 27 permission-limited, source-backed "
                "research readers; it is not included in that Bible.com count and does not assert an EOTC canon crosswalk. "
                "The eBible source requires its full copyright statement in non-commercial works and written permission "
                "for commercial use. Other providers and editions have not been surveyed."
            )
        if language.get("language_tag") == "gez":
            language["source_ids"] = sorted(
                set(language.get("source_ids", []))
                | {source["source_id"] for source in reigns_sources + kings_sources},
                key=lambda value: int(value.split("-")[1]),
            )
        if language.get("language_tag") == "mdy":
            language["source_ids"] = sorted(
                set(language.get("source_ids", [])) | {source["source_id"] for source in maale_sources},
                key=lambda value: int(value.split("-")[1]),
            )
            language["script_codes"] = sorted(set(language.get("script_codes", [])) | {"Ethi"})
            language["script_profile_note"] = (
                "The inspected eBible.org MDYTWF / mdyeth edition record identifies Maale (Male), language tag mdy, and Ethiopic script. "
                "This is evidence for the specific 2008 Maale edition, not a claim that all Maale orthographies use only this script. "
                "The retained USFM package supplies 66 conventional book modules; that inventory is not an EOTC or Eritrean Orthodox canon crosswalk. An agency biography names Tamene Lale Gego as translating a complete Maale Bible, but does not identify the MDYTWF / mdyeth edition or its 2008 team (SRC-374)."
            )
            survey = language.get("availability_survey", {})
            survey["notes"] = (
                "The result_count of two describes the two Maale/Male catalogue labels originally counted on the eBible.org Scripture index; it is not a "
                "count of every edition or digital format. The separately inspected MDYTWF / mdyeth publisher record and retained USFM package are now "
                "bundled as 66 research readers. The package's conventional 39 OT / 27 NT module count does not establish EOTC/Eritrean canon equivalence, "
                "print completeness, or translation accuracy. Its source-stated CC BY-SA 4.0 license covers the text under attribution, change-indication, "
                "and ShareAlike terms; image assets are excluded because the provider states separate restrictions. A dated CC BY-ND 4.0 notice on an older third-party mirror is preserved as a version discrepancy (SRC-372); the distinct MDYBSE product record marked RESERVED (SRC-373) is not mapped to this package. No license-history or retroactive legal conclusion is asserted."
            )
            survey["source_ids"] = sorted(
                set(survey.get("source_ids", [])) | {source["source_id"] for source in maale_sources},
                key=lambda value: int(value.split("-")[1]),
            )
        if language.get("language_tag") == "gaz":
            language["source_ids"] = sorted(
                set(language.get("source_ids", [])) | {source["source_id"] for source in gaz_sources},
                key=lambda value: int(value.split("-")[1]),
            )
            language["script_profile_note"] = (
                "IANA identifies gaz as Oromo, West Central. The New Oromo Contemporary Version edition record names Afaan Oromoo (West Central), "
                "publisher code gaz, and Latin-script digital materials. Latn is recorded for this edition only, not all Oromo varieties or witnesses. "
                "The retained USFM has 66 conventional book modules and is not an EOTC or Eritrean Orthodox canon crosswalk."
            )
            survey = language.get("availability_survey", {})
            survey["scope"] = (
                "A bounded, non-exhaustive comparison: the earlier survey counted three version entries visible on Bible.com's public gaz page and "
                "inspected the MacQul version page; this update also identified one distinct eBible.org New Oromo Contemporary Version edition and "
                "inspected its license and USFM package. Four is the count of listed provider/version leads (not four proven unique translations), "
                "not a census of Oromo varieties or editions, a complete canon inventory, an EOTC/Eritrean crosswalk, or a wording review."
            )
            survey["result_count"] = 4
            survey["source_ids"] = sorted(
                set(survey.get("source_ids", [])) | {source["source_id"] for source in gaz_sources},
                key=lambda value: int(value.split("-")[1]),
            )
            survey["notes"] = (
                "Four provider/version leads were located in the bounded pages (three Bible.com entries plus one eBible.org edition page); they are "
                "not asserted to be four distinct translations. The eBible edition is CC BY-SA 4.0 with Biblica attribution, derivative-mark removal, "
                "change notice, and ShareAlike conditions. Its 66 conventional USFM modules are research readers, not EOTC/Eritrean canon coverage. "
                "Earlier MacQul reuse restrictions remain unchanged."
            )
        if language.get("language_tag") == "so":
            language["source_ids"] = sorted(
                set(language.get("source_ids", [])) | {source["source_id"] for source in som_sources},
                key=lambda value: int(value.split("-")[1]),
            )
            language["script_codes"] = sorted(set(language.get("script_codes", [])) | {"Latn"})
            language["script_profile_note"] = (
                "The Somali BCP 47 profile (`so`) includes the eBible.org SOMSIM / som Adan Jim'ale edition, whose source language code is som and "
                "whose retained text is observed in Latin script. This is evidence for this digital witness, not every Somali variety or writing practice. "
                "The 66 conventional modules are research readers and have no Ethiopian/Eritrean Orthodox canon crosswalk."
            )
        if language.get("language_tag") == "ln":
            language["source_ids"] = sorted(
                set(language.get("source_ids", [])) | {"SRC-077", "SRC-078"} | {s["source_id"] for s in lin_sources},
                key=lambda value: int(value.split("-")[1]),
            )
            language["script_codes"] = sorted(set(language.get("script_codes", [])) | {"Latn"})
            language["script_profile_note"] = (
                "IANA identifies `ln` as Lingala and lists Latn as its Suppress-Script value. The inspected eBible.org LINBIB / lin edition uses Latin script. "
                "This is evidence about this digital witness, not every Lingala community or language variety. Its 66 source modules are research readers, "
                "not an Ethiopian/Eritrean Orthodox canon crosswalk."
            )
            survey = language.get("availability_survey", {})
            survey["source_ids"] = sorted(
                set(survey.get("source_ids", [])) | {s["source_id"] for s in lin_sources} | {"SRC-077", "SRC-078"},
                key=lambda value: int(value.split("-")[1]),
            )
            survey["notes"] = (
                "The result_count of one refers only to the inspected eBible.org edition record and package, not all Lingala scripture providers. "
                "The bundled CC BY-SA 4.0 text requires attribution, change indication, ShareAlike, and removal of the registered mark from derivatives; "
                "images are excluded under separate terms. This edition is not counted as Ethiopian/Eritrean canon coverage."
            )
    archive["sources"] = sorted(
        [item for item in archive.get("sources", []) if item.get("source_id") not in {"SRC-197", "SRC-198"}]
        + amharic_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            s["source_id"] for s in reigns_sources + kings_sources
        }] + reigns_sources + kings_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in maale_sources
        }] + maale_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in gaz_sources
        }] + gaz_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in som_sources
        }] + som_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in lin_sources
        }] + lin_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in oyda_sources
        }] + oyda_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in yemsa_sources
        }] + yemsa_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in dawro_sources
        }] + dawro_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in baiso_sources
        }] + baiso_sources,
        key=lambda item: item.get("source_id", ""),
    )
    archive["sources"] = sorted(
        [item for item in archive["sources"] if item.get("source_id") not in {
            source["source_id"] for source in alaba_sources
        }] + alaba_sources,
        key=lambda item: item.get("source_id", ""),
    )
    iana_record = next((item for item in archive["sources"] if item.get("source_id") == "SRC-077"), None)
    if iana_record:
        iana_record["local_metadata_url"] = "readers/source/authority/language-subtag-registry.txt"
        iana_record["inspection_and_limitations"] = ensure_appended_note_once(
            iana_record["inspection_and_limitations"], IANA_LINGALA_NOTE
        )
        iana_record["inspection_and_limitations"] = ensure_appended_note_once(
            iana_record["inspection_and_limitations"], IANA_YEMSA_NOTE
        )
        iana_record["inspection_and_limitations"] = ensure_appended_note_once(
            iana_record["inspection_and_limitations"], IANA_BAISO_NOTE
        )
        iana_record["inspection_and_limitations"] = ensure_appended_note_once(
            iana_record["inspection_and_limitations"], IANA_ALABA_NOTE
        )
    build_betamasaheft_license_audit(archive)
    translation_registry = archive["translation_registry"]
    source_ids = require_unique(archive["sources"], "source_id", "source record")
    apply_reviewed_title_crosswalks(archive)
    standard_nt_research_reader_count = apply_standard_nt_research_crosswalks(archive)
    standard_ot_research_reader_count = apply_standard_ot_research_crosswalks(archive)
    rights_status_updates = {}
    rights_status_completed_count = 0
    for reader in archive["readers"]:
        reader_id = str(reader.get("reader_id", ""))
        if not re.fullmatch(r"[a-z0-9-]+", reader_id):
            raise ValueError(f"Unsafe reader ID for rights metadata update: {reader_id!r}.")
        reader_path = reader_package_paths.get(reader_id)
        if reader_path is None:
            raise ValueError(f"Reader {reader_id} has no local JSON package for rights metadata update.")
        package_record = json.loads(reader_path.read_text(encoding="utf-8"))
        archive_status = reader.get("rights_status")
        package_status = package_record.get("rights_status")
        if archive_status and package_status and archive_status != package_status:
            raise ValueError(f"Reader {reader_id} archive and package rights notices disagree.")
        expected_status = archive_status or package_status or reader_rights_status(reader)
        if not archive_status or not package_status:
            rights_status_completed_count += 1
        reader["rights_status"] = expected_status
        package_changed = package_record.get("rights_status") != expected_status
        if package_changed:
            package_record["rights_status"] = expected_status
            write_text_atomically(reader_path, json.dumps(package_record, ensure_ascii=False, indent=2) + "\n")
        if package_changed:
            rights_status_updates[reader_path.resolve()] = hashlib.sha256(reader_path.read_bytes()).hexdigest()
    if rights_status_updates:
        for example_path in (ROOT / "examples").glob("*.json"):
            try:
                example = json.loads(example_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            changed = False
            def refresh_rights_package_hashes(value):
                nonlocal changed
                if isinstance(value, dict):
                    package = value.get("content_package")
                    if isinstance(package, dict) and package.get("uri"):
                        uri = unquote(str(package["uri"]))
                        targets = {(ROOT / uri).resolve(), (example_path.parent / uri).resolve()}
                        for target, digest in rights_status_updates.items():
                            if target in targets and package.get("sha256") != digest:
                                package["sha256"] = digest
                                changed = True
                    for child in value.values():
                        refresh_rights_package_hashes(child)
                elif isinstance(value, list):
                    for child in value:
                        refresh_rights_package_hashes(child)
            refresh_rights_package_hashes(example)
            if changed:
                write_text_atomically(example_path, json.dumps(example, ensure_ascii=False, indent=2) + "\n")

    portable_layer_records = validate_global_layer_example(source_ids)
    translation_registry["coverage_statement"] = build_coverage_statement(
        translation_registry, archive["canon_registry"], portable_layer_records
    )
    language_registry_path.write_text(
        json.dumps(translation_registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    canon_path.write_text(
        json.dumps(archive["canon_registry"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    language_registry_path.write_text(
        json.dumps(translation_registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    reader_names = ", ".join(reader.get("title", reader.get("reader_id", "unnamed reader")) for reader in current_readers)
    canon_reader_count = sum(bool(reader.get("canon_id")) for reader in current_readers)
    research_reader_count = sum(bool(reader.get("research_corpus_id")) for reader in current_readers)
    research_reader_noun = "reader" if research_reader_count == 1 else "readers"
    archive["reader_policy"] = (
        f"This embedded archive bundles {canon_reader_count} canon-linked reader records and "
        f"{research_reader_count} separately scoped research {research_reader_noun}: {reader_names}. "
        "Language and edition scope, source limits, and rights are recorded per reader. Companion translations are "
        "distinct witnesses and are not presumed to translate the accompanying source text. Source snapshots, notices, "
        "and boundaries are stored locally. No runtime fetch or generated scripture is used."
    )
    catalogue = archive.get("catalogue", [])
    sources = archive.get("sources", [])
    normalize_catalogue_custodians(
        catalogue, {source.get("source_id") for source in sources if isinstance(source, dict)}
    )
    mark_unassessed_source_rights(sources)
    apply_source_rights_scope_notes(sources)
    source_registry = {source["source_id"]: source for source in sources}
    related = archive.get("related_texts", [])
    readers = archive.get("readers", [])
    canon_registry = archive.get("canon_registry", {})
    translation_registry = archive.get("translation_registry", {})
    translation_schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
    if translation_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Translation registry schema must declare JSON Schema 2020-12.")
    validate_closed_schema_objects(translation_registry, translation_schema, translation_schema, "translation-registry.json")
    if not all(isinstance(items, list) for items in (catalogue, sources, related, readers)):
        raise ValueError("catalogue, sources, related_texts, and readers must be arrays.")

    require_unique(catalogue, "catalogue_id", "catalogue record")
    validate_catalogue_research_views(catalogue)
    source_ids = require_unique(sources, "source_id", "source record")
    validate_source_record_metadata(sources)
    validate_local_source_snapshots(sources)
    validate_source_urls(sources)
    validate_source_link_safety(sources)
    validate_brenton_exodus_capture()
    validate_brenton_octateuch_companions()
    validate_crosswire_module_audit()
    validate_mark_tei_audit()
    related_schema_path = ROOT / "schemas" / "related-text.schema.json"
    related_schema = json.loads(related_schema_path.read_text(encoding="utf-8"))
    if related_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Related-text schema must declare JSON Schema 2020-12.")
    for index, record in enumerate(related):
        validate_closed_schema_objects(record, related_schema, related_schema, f"related_texts[{index}]")
        validate_schema_constraints(record, related_schema, related_schema, f"related_texts[{index}]")
        validate_rights_classification(record, f"Related text {record.get('related_id', index)}")
        missing_sources = set(record.get("source_ids", [])) - source_ids
        if missing_sources:
            raise ValueError(f"{record.get('related_id')} refers to missing sources: {sorted(missing_sources)}")
    require_unique(related, "related_id", "related-text record")
    require_unique(readers, "reader_id", "reader record")
    validate_archive_graph_example(source_ids, translation_registry, "archive-graph-genesis.json", source_registry)
    normalized_graph_path = write_normalized_graph(ROOT, archive, portable_layer_records)
    normalized_graph = json.loads(normalized_graph_path.read_text(encoding="utf-8"))
    write_review_coverage(ROOT, normalized_graph)
    offline_shell_files = validate_offline_shell()
    validate_archive_graph_example(source_ids, translation_registry, normalized_graph_path.name, source_registry)

    canon_books = canon_registry.get("books", [])
    if canon_registry.get("book_count") != 81 or len(canon_books) != 81:
        raise ValueError("The canon coverage registry must contain the Church-listed 81 entries.")
    if sum(book.get("section") == "Old Testament" for book in canon_books) != 46 or sum(book.get("section") == "New Testament" for book in canon_books) != 35:
        raise ValueError("The canon coverage registry must preserve the stated 46/35 section counts.")
    canon_ids = require_unique(canon_books, "canon_id", "canon registry entry")
    readers_by_id = {reader["reader_id"]: reader for reader in readers}
    catalogue_ids = {item["catalogue_id"] for item in catalogue}
    if any(not book.get("catalogue_ids") for book in canon_books):
        raise ValueError("Every Church-list entry needs a catalogue navigation record, even when its identity crosswalk remains unresolved.")
    if any(set(book.get("catalogue_ids", [])) - catalogue_ids for book in canon_books):
        raise ValueError("A canon registry entry refers to an unknown catalogue row.")
    mapped_catalogue_ids = {catalogue_id for book in canon_books for catalogue_id in book.get("catalogue_ids", [])}
    if catalogue_ids - mapped_catalogue_ids:
        raise ValueError(f"Catalogue rows are missing from the canon navigation crosswalk: {sorted(catalogue_ids - mapped_catalogue_ids)}")
    canon_by_id = {book["canon_id"]: book for book in canon_books}
    catalogue_by_id = {item["catalogue_id"]: item for item in catalogue}
    for entry in canon_books:
        for catalogue_id in entry.get("catalogue_ids", []):
            if not (entry.get("mapping_note") or catalogue_by_id[catalogue_id].get("canon_view")):
                raise ValueError(f"Canon entry {entry['canon_id']} and catalogue row {catalogue_id} need an explicit mapping note or caveat.")
    # The Church list orders James after III John, but this catalogue places
    # James first. Guard these evidence-reviewed title links against regressions.
    expected_nt_catalogue = {
        "eotc-nt-20": ("eotc-075", "1 Peter"),
        "eotc-nt-21": ("eotc-076", "2 Peter"),
        "eotc-nt-22": ("eotc-077", "1 John"),
        "eotc-nt-23": ("eotc-078", "2 John"),
        "eotc-nt-24": ("eotc-079", "3 John"),
        "eotc-nt-25": ("eotc-074", "James"),
    }
    for canon_id, (catalogue_id, display_name) in expected_nt_catalogue.items():
        entry = canon_by_id[canon_id]
        if entry.get("catalogue_ids") != [catalogue_id] or catalogue_by_id[catalogue_id].get("display_name") != display_name:
            raise ValueError(f"Incorrect catalogue crosswalk for {entry.get('source_label')!r}.")
    ezra_group = canon_by_id["eotc-ot-16"]
    if ezra_group.get("catalogue_ids") != ["eotc-090", "eotc-019"]:
        raise ValueError("Church-list entry 16 must keep both Ezra title-level discovery rows.")
    ezra_mapping_note = ezra_group.get("mapping_note", "").lower()
    if not all(token in ezra_mapping_note for token in ("provisional", "unverified", "no reader coverage")):
        raise ValueError("Ezra entry 16 must label the crosswalk provisional, its textual evidence unverified, and no reader coverage claimed.")
    wisdom_entry = canon_by_id["eotc-ot-26"]
    if catalogue_by_id["eotc-031"].get("display_name") != wisdom_entry.get("source_label"):
        raise ValueError("The wisdom catalogue row must preserve the Church list's source label.")
    if "not established" not in wisdom_entry.get("mapping_note", "").lower():
        raise ValueError("The wisdom entry must retain its unresolved work-identity warning.")
    for canon_id in ("eotc-ot-20", "eotc-ot-21", "eotc-ot-24", "eotc-ot-25", "eotc-ot-45"):
        if "SRC-101" not in canon_by_id[canon_id].get("source_ids", []):
            raise ValueError(f"{canon_id} must cite the scholarly historical-list comparison.")
        if not canon_by_id[canon_id].get("mapping_note"):
            raise ValueError(f"{canon_id} needs an explicit, attributed mapping limitation.")
    for number in range(28, 36):
        canon_id = f"eotc-nt-{number:02d}"
        if "SRC-073" not in canon_by_id[canon_id].get("source_ids", []):
            raise ValueError(f"{canon_id} must cite the dissertation used for its title crosswalk context.")
        if not canon_by_id[canon_id].get("mapping_note"):
            raise ValueError(f"{canon_id} needs an explicit title/identity limitation.")
    if any(set(book.get("source_ids", [])) - source_ids for book in canon_books):
        raise ValueError("A canon registry entry refers to an unknown source.")
    for book in canon_books:
        has_bundled_reader = str(book.get("reader_status", "")).startswith("Bundled:")
        reader_id = book.get("reader_id")
        if has_bundled_reader and reader_id not in readers_by_id:
            raise ValueError(f"Bundled canon entry {book['canon_id']} has no matching reader record.")
        if reader_id and reader_id not in readers_by_id:
            raise ValueError(f"Canon entry {book['canon_id']} refers to an unknown reader.")
        if reader_id and readers_by_id[reader_id].get("canon_id") != book["canon_id"]:
            raise ValueError(f"Reader {reader_id} is not explicitly linked back to canon entry {book['canon_id']}.")
        if not has_bundled_reader and reader_id:
            raise ValueError(f"Canon entry {book['canon_id']} links a reader while marked as unbundled.")
    for reader in readers:
        canon_id = reader.get("canon_id")
        if canon_id and canon_id not in canon_ids:
            raise ValueError(f"Reader {reader['reader_id']} refers to an unknown canon entry.")
    registry_sources = set(canon_registry.get("source_id", [])) if isinstance(canon_registry.get("source_id"), list) else {canon_registry.get("source_id")}
    registry_sources.update(canon_registry.get("context_source_ids", []))
    if not registry_sources.issubset(source_ids):
        raise ValueError("The canon registry refers to an unknown source.")
    # This is a count of reader records present in the embedded build, not the
    # number of catalogue labels that claim text is bundled.
    canon_registry["reader_count"] = sum(
        1 for book in canon_books
        if any(reader.get("canon_id") == book["canon_id"] and
               (not book.get("reader_id") or reader.get("reader_id") == book["reader_id"])
               for reader in readers)
    )
    # This registry is written earlier for downstream generation; refresh it
    # after the final withheld-reader count is computed.
    canon_path.write_text(
        json.dumps(canon_registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    language_records = translation_registry.get("languages", [])
    if (translation_registry.get("schema_version") != 3
            or not isinstance(language_records, list)
            or not isinstance(translation_registry.get("translation_leads"), list)
            or not isinstance(translation_registry.get("corpus_leads"), list)
            or not isinstance(translation_registry.get("edition_leads"), list)
            or not isinstance(translation_registry.get("translation_process_evidence"), list)
            or not translation_registry.get("coverage_statement")):
        raise ValueError("The version 3 translation registry needs language, translation, corpus, and source-edition lists plus an explicit coverage statement.")
    evidence_records = translation_registry["translation_process_evidence"]
    evidence_ids = [record.get("record_id") for record in evidence_records]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("Translation-process evidence record IDs must be unique.")
    registered_language_tags = {
        record.get("language_tag") for record in language_records
    } | {
        record.get("language_tag") for record in translation_registry.get("basis_languages", [])
    }
    known_edition_ids = {
        record.get("edition_id") for record in translation_registry.get("edition_leads", [])
    }
    for record in evidence_records:
        if record.get("language_tag") not in registered_language_tags:
            raise ValueError(f"Translation-process evidence {record.get('record_id')} refers to an unregistered language.")
        if set(record.get("source_ids", [])) - source_ids:
            raise ValueError(f"Translation-process evidence {record.get('record_id')} refers to an unknown source.")
        edition_ids = set(record.get("edition_ids", []))
        if (record.get("edition_link_status") == "identified") != bool(edition_ids):
            raise ValueError(f"Translation-process evidence {record.get('record_id')} has inconsistent edition-link status and IDs.")
        if edition_ids - known_edition_ids:
            raise ValueError(f"Translation-process evidence {record.get('record_id')} refers to an unknown source edition.")
        path = record.get("translation_path")
        if record.get("translation_path_status") == "established":
            if not path or path[-1] != record.get("language_tag") or set(path) - registered_language_tags:
                raise ValueError(f"Translation-process evidence {record.get('record_id')} has an invalid registered translation path.")
        elif path is not None:
            raise ValueError(f"Translation-process evidence {record.get('record_id')} states an unestablished path as fact.")
    identifier_audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
    language_audit = identifier_audit.get("language_subtags", {})
    script_audit = identifier_audit.get("script_codes", {})
    audited_language_tags = validate_language_subtag_audit(
        identifier_audit, translation_registry, ROOT, source_registry[language_audit.get("source_id")]
    )
    validate_iana_special_script_audit(
        identifier_audit, ROOT, source_registry[script_audit.get("iana_special_source_id")]
    )
    audited_script_codes = set(script_audit.get("iso_15924_codes", [])) | set(script_audit.get("iana_special_codes", []))
    iana_special_script_codes = set(script_audit.get("iana_special_codes", []))
    if (language_audit.get("source_id") not in source_ids
            or script_audit.get("iso_15924_source_id") not in source_ids
            or script_audit.get("iana_special_source_id") not in source_ids
            or not audited_language_tags or not audited_script_codes):
        raise ValueError("Language and script identifier audits must cite valid authority sources and contain codes.")
    expected_coverage = build_coverage_statement(translation_registry, canon_registry, portable_layer_records)
    if translation_registry["coverage_statement"] != expected_coverage:
        raise ValueError("The translation coverage statement is stale; regenerate it from current registry records.")
    language_tags = require_unique(language_records, "language_tag", "language registry entry")
    basis_language_tags = require_unique(translation_registry.get("basis_languages", []), "language_tag", "basis language entry")
    known_language_tags = language_tags | basis_language_tags | {"und"}
    if not known_language_tags.issubset(audited_language_tags):
        raise ValueError(f"Language registry contains subtags absent from its cited IANA audit: {sorted(known_language_tags - audited_language_tags)}")
    for basis in translation_registry.get("basis_languages", []):
        if set(basis.get("source_ids", [])) - source_ids:
            raise ValueError(f"Basis language {basis['language_tag']} refers to an unknown evidence source.")
    edition_basis_evidence = translation_registry.get("edition_basis_evidence", [])
    require_unique(edition_basis_evidence, "family_id", "edition-family basis evidence")
    known_translation_families = {
        record.get("translation_id") for record in translation_registry.get("research_corpora", [])
        if record.get("translation_id")
    }
    for evidence in edition_basis_evidence:
        label = f"Edition-family basis evidence {evidence.get('family_id')}"
        if evidence.get("family_id") not in known_translation_families:
            raise ValueError(f"{label} refers to an unregistered translation family.")
        if evidence.get("output_language_tag") not in known_language_tags:
            raise ValueError(f"{label} uses an unregistered output language.")
        if set(evidence.get("source_ids", [])) - source_ids:
            raise ValueError(f"{label} refers to an unknown evidence source.")
        for claim in evidence.get("claims", []):
            if set(claim.get("source_language_tags", [])) - known_language_tags:
                raise ValueError(f"{label} contains an unregistered source-language tag.")
    for language in language_records:
        scripts = set(language.get("script_codes", [])) | {language.get("script_code")}
        if not scripts.issubset(audited_script_codes):
            raise ValueError(f"Language {language['language_tag']} uses script codes absent from its cited ISO/IANA audit: {sorted(scripts - audited_script_codes)}")
    language_tag_pattern = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
    script_code_pattern = re.compile(r"^[A-Z][a-z]{3}$")
    translation_leads = translation_registry.get("translation_leads", [])
    require_unique(translation_leads, "translation_id", "translation lead")
    for lead in translation_leads:
        validate_rights_classification(lead, f"Translation lead {lead.get('canon_id')}")
        if lead.get("canon_id") not in canon_ids or lead.get("language_tag") not in language_tags:
            raise ValueError("A translation lead refers to an unknown canon item or language.")
        path = lead.get("translation_path")
        if path is not None and (not isinstance(path, list) or len(path) < 2 or path[-1] != lead.get("language_tag") or any(tag not in known_language_tags for tag in path)):
            raise ValueError("A translation lead's ordered path must use known language tags and end in its output language.")
        if set(lead.get("source_ids", [])) - source_ids:
            raise ValueError("A translation lead has an unknown source record.")
        if lead.get("text_bundled") is not False or not lead.get("review_status") or not lead.get("rights_status"):
            raise ValueError("Unbundled translation leads must state their review and rights boundaries.")
    corpus_leads = translation_registry.get("corpus_leads", [])
    require_unique(corpus_leads, "corpus_id", "corpus translation lead")
    languages_by_tag = {language["language_tag"]: language for language in language_records}
    for lead in corpus_leads:
        validate_rights_classification(lead, f"Corpus lead {lead.get('corpus_id')}")
        if not language_tag_pattern.fullmatch(str(lead.get("language_tag", ""))) or not lead.get("language_name") or not lead.get("scope_description"):
            raise ValueError("A corpus lead needs valid language and explicit scope metadata.")
        language = languages_by_tag.get(lead["language_tag"])
        if not language or lead.get("language_name") != language.get("language_name"):
            raise ValueError(f"Corpus lead {lead.get('corpus_id')} must match a registered language name.")
        if not language_tag_pattern.fullmatch(str(lead.get("basis_language_tag", ""))) or not lead.get("basis_description"):
            raise ValueError("A corpus lead needs an explicit basis-language tag and description; use 'und' if unknown.")
        path = lead.get("translation_path")
        if path is not None and (not isinstance(path, list) or len(path) < 2 or path[0] != lead.get("basis_language_tag") or path[-1] != lead.get("language_tag") or any(tag not in known_language_tags for tag in path)):
            raise ValueError(f"Corpus lead {lead.get('corpus_id')} has an invalid source-to-output language path.")
        lead_script = str(lead.get("script_code", ""))
        language_scripts = set(language.get("script_codes", [])) or {language.get("script_code")}
        if not script_code_pattern.fullmatch(lead_script):
            raise ValueError("A corpus lead needs an ISO 15924 script code.")
        if lead_script != "Zzzz" and lead_script not in language_scripts:
            raise ValueError(f"Corpus lead {lead.get('corpus_id')} uses a script absent from its language profile.")
        if lead.get("script_status", "identified") not in {"identified", "unidentified", "provisional"}:
            raise ValueError(f"Corpus lead {lead.get('corpus_id')} has an invalid script review state.")
        if set(lead.get("source_ids", [])) - source_ids:
            raise ValueError("A corpus lead refers to an unknown source record.")
        if lead.get("text_bundled") is not False or not lead.get("rights_status") or not lead.get("review_status"):
            raise ValueError("Unbundled corpus leads must state review and rights boundaries.")
    edition_leads = translation_registry.get("edition_leads", [])
    require_unique(edition_leads, "edition_id", "source-edition lead")
    languages_by_tag = {language["language_tag"]: language for language in language_records}
    valid_mapping_states = {"asserted_by_source", "reviewed_match", "related_work", "uncertain", "not_mapped"}
    for lead in edition_leads:
        label = f"Source-edition lead {lead.get('edition_id')}"
        validate_rights_classification(lead, label)
        if lead.get("mapping_state") not in valid_mapping_states:
            raise ValueError(f"{label} has an invalid or missing mapping state.")
        candidate_canon_id = lead.get("candidate_canon_id")
        if lead.get("mapping_state") == "not_mapped":
            if candidate_canon_id is not None:
                raise ValueError(f"{label} marked not_mapped must not assign a Church-list candidate.")
        elif candidate_canon_id not in canon_ids:
            raise ValueError(f"{label} needs a valid candidate Church-list entry unless mapping_state is not_mapped.")
        if lead.get("witness_type") not in {"manuscript", "printed_edition", "critical_edition", "digital_edition", "digital_service", "transcription", "composite", "unknown"}:
            raise ValueError(f"{label} has an invalid or missing witness type.")
        lead_language_tag = lead.get("language_tag")
        language_tags = lead.get("language_tags", [])
        if lead_language_tag == "mul":
            if (lead.get("language_name") != "Multiple languages"
                    or not isinstance(language_tags, list)
                    or len(language_tags) < 2
                    or len(language_tags) != len(set(language_tags))
                    or any(tag not in languages_by_tag for tag in language_tags)):
                raise ValueError(f"{label} must list at least two registered component languages for mul.")
            language_profiles = [languages_by_tag[tag] for tag in language_tags]
            language_scripts = set.intersection(*[
                set(item.get("script_codes", [])) or {item.get("script_code")}
                for item in language_profiles
            ])
        elif lead_language_tag == "und":
            if lead.get("language_name") != "Undetermined" or lead.get("script_code") != "Zzzz" or language_tags:
                raise ValueError(f"{label} with undetermined language must use language_name Undetermined and script Zzzz.")
            language_scripts = {"Zzzz"}
        else:
            language = languages_by_tag.get(lead_language_tag)
            if not language or lead.get("language_name") != language.get("language_name"):
                raise ValueError(f"{label} must match a registered language profile.")
            if language_tags:
                raise ValueError(f"{label} may list component language_tags only when language_tag is mul.")
            language_scripts = set(language.get("script_codes", [])) or {language.get("script_code")}
        lead_script = lead.get("script_code")
        if not script_code_pattern.fullmatch(str(lead_script or "")) or lead_script not in language_scripts:
            if not (lead_language_tag == "mul" and lead_script == "Zzzz" and lead_script in iana_special_script_codes):
                raise ValueError(f"{label} must use a script code supported by its registered language profile(s).")
        if lead_language_tag not in audited_language_tags or lead_script not in audited_script_codes:
            raise ValueError(f"{label} uses a language or script identifier absent from the cited standards audits.")
        if any(tag not in audited_language_tags for tag in language_tags):
            raise ValueError(f"{label} has a component language tag absent from the cited IANA audit.")
        if set(lead.get("source_ids", [])) - source_ids:
            raise ValueError(f"{label} refers to an unknown source record.")
        if lead.get("text_bundled") is not False:
            raise ValueError(f"{label} is a discovery record and cannot itself assert bundled reader text.")
        if any(not isinstance(lead.get(field), str) or not lead[field].strip() for field in ("title", "edition_statement", "scope_description", "rights_status", "review_status")):
            raise ValueError(f"{label} needs title, edition, scope, rights, and review-limit statements.")
        if lead.get("rights_classification") == "open_license" and not (lead.get("license_id") and lead.get("license_url")):
            raise ValueError(f"{label} must identify the exact open license and URL.")
    valid_directions = {"ltr", "rtl", "unknown"}
    valid_writing_modes = {"horizontal-tb", "vertical-rl", "vertical-lr", "unknown"}
    valid_roles = {"source_text_transcription", "source_text_edition", "translation", "historical_companion_translation", "transliteration", "paraphrase", "draft_translation"}
    valid_statuses = {"candidate", "transcribed", "source_checked", "translated_draft", "translation_reviewed", "bundled"}
    readers_by_id = {reader["reader_id"]: reader for reader in readers}
    reader_ids = {item["reader_id"] for item in readers}
    for lead in edition_leads:
        reader_id = lead.get("bundled_reader_id")
        if reader_id is None:
            continue
        reader = readers_by_id.get(reader_id)
        if reader is None:
            raise ValueError(f"Source-edition lead {lead['edition_id']} points to missing bundled reader {reader_id}.")
        if not (set(lead.get("source_ids", [])) & set(reader.get("source_ids", []))):
            raise ValueError(f"Source-edition lead {lead['edition_id']} and bundled reader {reader_id} have no shared source evidence.")
        if (lead.get("language_tag"), lead.get("script_code")) != (reader.get("language_tag"), reader.get("script_code")):
            raise ValueError(f"Source-edition lead {lead['edition_id']} and bundled reader {reader_id} disagree on language or script.")
    research_by_reader = {item.get("reader_id"): item for item in translation_registry.get("research_corpora", [])}
    for language in language_records:
        if not language_tag_pattern.fullmatch(str(language.get("language_tag", ""))) or not language.get("language_name") or not script_code_pattern.fullmatch(str(language.get("script_code", ""))) or language.get("direction") not in valid_directions:
            raise ValueError(f"Language {language.get('language_tag')} needs name, script, and direction metadata.")
        if language.get("writing_mode") is not None and language.get("writing_mode") not in valid_writing_modes:
            raise ValueError(f"Language {language.get('language_tag')} has an invalid writing_mode.")
        script_codes = language.get("script_codes", [language.get("script_code")])
        if not isinstance(script_codes, list) or not script_codes or len(script_codes) != len(set(script_codes)) or any(not script_code_pattern.fullmatch(str(code)) for code in script_codes):
            raise ValueError(f"Language {language.get('language_tag')} has invalid or duplicate script codes.")
        if set(language.get("source_ids", [])) - source_ids:
            raise ValueError(f"Language {language.get('language_tag')} points to an unknown script evidence source.")
        validate_availability_survey(
            language.get("availability_survey"),
            f"Language {language['language_tag']} availability_survey",
            source_ids,
        )
        for layer in language.get("records", []):
            validate_rights_classification(layer, f"Language layer {language['language_tag']}/{layer.get('canon_id')}")
            if layer.get("canon_id") not in canon_ids:
                raise ValueError(f"Language layer in {language['language_tag']} points to an unknown canon item.")
            reader_id = layer.get("reader_id")
            if reader_id is not None and reader_id not in reader_ids:
                raise ValueError(f"Language layer in {language['language_tag']} points to an unknown reader.")
            if layer.get("status") == "bundled" and reader_id is None:
                raise ValueError(f"Bundled language layer in {language['language_tag']} needs a reader.")
            if layer.get("translation_id") and reader_id is None:
                raise ValueError(f"Translation layer in {language['language_tag']} needs a reader record.")
            translation_roles = {"translation", "historical_companion_translation", "draft_translation"}
            if layer.get("layer_role") in translation_roles:
                missing_translation_fields = [
                    field for field in ("translation_id", "translator", "translation_path")
                    if not layer.get(field)
                ]
                if missing_translation_fields:
                    raise ValueError(
                        f"Translation layer in {language['language_tag']} is missing required metadata: "
                        f"{', '.join(missing_translation_fields)}."
                    )
            if layer.get("status") == "bundled" and layer.get("layer_role") == "draft_translation":
                raise ValueError(
                    f"Draft translation in {language['language_tag']} cannot be counted as bundled text."
                )
            if layer.get("status") == "bundled" and layer.get("layer_role") in translation_roles and not layer.get("translation_id"):
                raise ValueError(
                    f"Bundled translation in {language['language_tag']} must point to a distinct published translation layer."
                )
            if layer.get("translation_id") and layer.get("layer_role") not in translation_roles:
                raise ValueError(
                    f"Translation ID in {language['language_tag']} is attached to a non-translation layer."
                )
            if layer.get("basis_language_tag") not in known_language_tags:
                raise ValueError(f"Language layer in {language['language_tag']} has an unregistered basis language.")
            if set(layer.get("source_ids", [])) - source_ids:
                raise ValueError(f"Language layer in {language['language_tag']} points to an unknown source.")
            if not layer.get("basis_description") or not layer.get("rights_status") or not layer.get("status"):
                raise ValueError(f"Language layer in {language['language_tag']} needs basis, rights, and status metadata.")
            if not language_tag_pattern.fullmatch(str(layer.get("basis_language_tag", ""))) or layer.get("layer_role") not in valid_roles or layer.get("status") not in valid_statuses:
                raise ValueError(f"Language layer in {language['language_tag']} has an invalid language tag, role, or status.")
            path = layer.get("translation_path")
            if layer.get("layer_role") in translation_roles and (not isinstance(path, list) or len(path) < 2 or path[0] != layer.get("basis_language_tag") or path[-1] != language["language_tag"] or any(tag not in known_language_tags for tag in path)):
                raise ValueError(f"Translation layer in {language['language_tag']} needs an ordered source-to-output language path.")
            if path is not None and (not isinstance(path, list) or len(path) < 2 or path[0] != layer.get("basis_language_tag") or path[-1] != language["language_tag"] or any(tag not in known_language_tags for tag in path)):
                raise ValueError(f"Language path in {language['language_tag']} must start at its basis and end at its output language.")
            if layer.get("status") == "bundled" and layer.get("reader_id") not in reader_ids:
                raise ValueError(f"Bundled language layer in {language['language_tag']} has no reader.")
            if reader_id is not None:
                reader = readers_by_id[reader_id]
                reader_canon_id = reader.get("canon_id")
                research = research_by_reader.get(reader_id)
                if reader_canon_id is None and research:
                    reader_canon_id = research.get("candidate_canon_id")
                if reader_canon_id != layer.get("canon_id"):
                    raise ValueError(
                        f"Language layer in {language['language_tag']} points to reader {reader_id} "
                        f"for canon candidate {reader_canon_id!r}, not its declared entry {layer.get('canon_id')!r}."
                    )
                text_record = reader.get("parallel_translation") if layer.get("translation_id") else reader
                if layer.get("translation_id") and text_record is None and reader.get("translation_id") == layer["translation_id"]:
                    text_record = reader
                if layer.get("translation_id") and text_record.get("translation_id") != layer["translation_id"]:
                    raise ValueError(f"Language layer in {language['language_tag']} names a translation missing from its reader.")
                if layer.get("status") == "bundled" and text_record.get("language_tag") != language["language_tag"]:
                    raise ValueError(f"Bundled language tag in the registry disagrees with its reader data.")

    for record in related:
        missing = set(record.get("source_ids", [])) - source_ids
        if missing:
            raise ValueError(f"{record.get('title')} refers to missing sources: {sorted(missing)}")

    research_corpora = translation_registry.get("research_corpora", [])
    require_unique(research_corpora, "corpus_id", "separately scoped research corpus")
    for corpus in research_corpora:
        validate_rights_classification(corpus, f"Research corpus {corpus.get('corpus_id')}")
        reader = readers_by_id.get(corpus.get("reader_id"))
        if not reader or reader.get("research_corpus_id") != corpus.get("corpus_id"):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must point to its matching reader record.")
        validate_research_corpus_language_script(
            corpus, reader, languages_by_tag, audited_language_tags, audited_script_codes
        )
        if reader.get("canon_id") is not None or corpus.get("canon_mapping_state") not in {"asserted_by_source", "reviewed_match", "uncertain", "not_mapped"}:
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must stay outside canon-linked reader coverage.")
        candidate_canon_id = corpus.get("candidate_canon_id")
        mapping_state = corpus.get("canon_mapping_state")
        if mapping_state in {"asserted_by_source", "reviewed_match", "uncertain"} and candidate_canon_id not in canon_ids:
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} needs a valid candidate for its source assertion or reviewed/provisional mapping.")
        if mapping_state == "not_mapped" and candidate_canon_id is not None:
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must not carry a canon candidate when mapping is not assigned.")
        if not corpus.get("language_description") or not corpus.get("unit_summary") or not corpus.get("review_status"):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must describe language, observed units, and review limits.")
        if corpus.get("rights_classification") == "open_license" and not (corpus.get("license_id") and corpus.get("license_url")):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must identify its exact open license and URL.")
        if set(corpus.get("source_ids", [])) - source_ids:
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} refers to an unknown source.")
        if reader.get("unit_count") != corpus.get("unit_count"):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} unit count disagrees with its reader.")
        if corpus.get("text_origin") and corpus.get("text_origin") != reader.get("text_origin"):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} text origin disagrees with its reader.")
        if corpus.get("text_origin") == "published_translation":
            basis_status = corpus.get("translation_basis_status")
            required_translation_fields = ["language_tag", "script_code", "translation_id", "translator", "edition_statement", "translation_basis_status", "translation_basis_note"]
            if basis_status == "unknown":
                if (corpus.get("basis_language_tag") is not None or corpus.get("translation_path") is not None
                        or corpus.get("translation_basis_source_ids") is not None):
                    raise ValueError(f"Research translation {corpus.get('corpus_id')} must not invent a path when its basis is unknown.")
            elif basis_status == "established":
                required_translation_fields.extend(("basis_language_tag", "translation_path", "translation_basis_source_ids"))
            else:
                raise ValueError(f"Research translation {corpus.get('corpus_id')} has unsupported translation_basis_status {basis_status!r}.")
            if any(not corpus.get(field) for field in required_translation_fields):
                raise ValueError(f"Research translation {corpus.get('corpus_id')} needs complete language and translation-basis metadata.")
            compare_fields = ["language_tag", "script_code", "translation_id", "translator", "translation_basis_status"]
            if basis_status == "established":
                compare_fields.extend(("basis_language_tag", "translation_path"))
            if any(corpus.get(field) != reader.get(field) for field in compare_fields):
                raise ValueError(f"Research translation {corpus.get('corpus_id')} language or translator metadata disagrees with its reader.")
            if basis_status == "established":
                path = corpus["translation_path"]
                if (corpus["basis_language_tag"] not in known_language_tags or corpus["language_tag"] not in known_language_tags
                        or path[0] != corpus["basis_language_tag"] or path[-1] != corpus["language_tag"]
                        or any(tag not in known_language_tags for tag in path)):
                    raise ValueError(f"Research translation {corpus.get('corpus_id')} has an unregistered or inconsistent translation path.")
                basis_sources = corpus["translation_basis_source_ids"]
                if (not isinstance(basis_sources, list) or not basis_sources or len(set(basis_sources)) != len(basis_sources)
                        or set(basis_sources) - set(corpus.get("source_ids", []))
                        or set(basis_sources) - source_ids):
                    raise ValueError(f"Research translation {corpus.get('corpus_id')} has missing, duplicate, or unlinked basis evidence sources.")

    for reader in readers:
        required_reader_fields = (
            "title", "language", "language_tag", "edition", "edition_scope",
            "copyright_notice", "commercial_use", "rights_classification", "rights_status", "verification_status",
            "chapter_structure_note", "source_ids", "unit_count", "unit_label",
        )
        missing_fields = [field for field in required_reader_fields if not reader.get(field)]
        if missing_fields:
            raise ValueError(
                f"{reader.get('reader_id', 'Reader')} is missing provenance, rights, or review metadata: "
                f"{', '.join(missing_fields)}. Record unknowns explicitly."
            )
        if not reader["source_ids"]:
            raise ValueError(f"{reader['reader_id']} must cite at least one source record.")
        validate_rights_classification(reader, f"Reader {reader['reader_id']}")
        if reader.get("research_corpus_id"):
            rights_records = [
                record for record in research_corpora
                if record.get("reader_id") == reader["reader_id"]
                and record.get("corpus_id") == reader["research_corpus_id"]
            ]
        else:
            rights_records = [
                layer for language in language_records for layer in language.get("records", [])
                if layer.get("reader_id") == reader["reader_id"]
                and not layer.get("translation_id") and layer.get("status") == "bundled"
            ]
        if len(rights_records) != 1 or reader["rights_classification"] != rights_records[0].get("rights_classification"):
            raise ValueError(f"Reader {reader['reader_id']} rights classification must match exactly one bundled registry layer or research record.")
        if reader.get("language_tag") not in audited_language_tags or reader.get("script_code") not in audited_script_codes:
            raise ValueError(f"{reader['reader_id']} uses language or script codes absent from the cited identifier audit.")
        if reader.get("canon_id") is None and not reader.get("research_corpus_id"):
            raise ValueError(f"{reader['reader_id']} must be linked to a canon entry or a separately scoped research corpus.")
        allowed_research_translation = bool(reader.get("research_corpus_id")) and reader.get("text_origin") == "published_translation"
        if reader.get("text_origin") != "source_transcription" and not allowed_research_translation:
            raise ValueError(
                f"{reader['reader_id']} must identify a source transcription, or a separately scoped published research translation; "
                "machine-generated wording is not admissible as a scripture witness."
            )
        if allowed_research_translation:
            basis_status = reader.get("translation_basis_status")
            required_fields = ["translation_id", "translator", "translation_basis_status", "translation_basis_note"]
            if basis_status == "unknown":
                if reader.get("basis_language_tag") is not None or reader.get("translation_path") is not None:
                    raise ValueError(f"Published research translation {reader['reader_id']} must not invent an unknown translation path.")
            elif basis_status == "established":
                required_fields.extend(("basis_language_tag", "translation_path"))
            else:
                raise ValueError(f"Published research translation {reader['reader_id']} has unsupported translation_basis_status {basis_status!r}.")
            for field in required_fields:
                if not reader.get(field):
                    raise ValueError(f"Published research translation {reader['reader_id']} is missing {field}.")
            if basis_status == "established":
                path = reader["translation_path"]
                if (reader["basis_language_tag"] not in known_language_tags or path[0] != reader["basis_language_tag"]
                        or path[-1] != reader["language_tag"] or any(tag not in known_language_tags for tag in path)):
                    raise ValueError(f"Published research translation {reader['reader_id']} has an invalid translation path.")
        missing = set(reader.get("source_ids", [])) - source_ids
        if missing:
            raise ValueError(f"{reader.get('title')} refers to missing sources: {sorted(missing)}")
        chapters = reader.get("chapters", [])
        if not chapters or [item.get("chapter") for item in chapters] != list(range(1, len(chapters) + 1)):
            raise ValueError(f"{reader.get('title')} chapter sequence must be complete and ordered from 1.")
        if reader.get("chapter_count") != len(chapters):
            raise ValueError(f"{reader.get('title')} chapter count does not match its chapters.")
        validate_observed_unit_count(reader, "unit_count", reader.get("title", reader.get("reader_id", "Reader")))
        if reader.get("verse_marker_count", reader["unit_count"]) != reader["unit_count"]:
            raise ValueError(f"{reader.get('title')} legacy verse_marker_count disagrees with its generic unit_count.")
        for chapter in chapters:
            verses = chapter.get("units", chapter.get("verses", []))
            numbers = [verse.get("number", verse.get("unit_order")) for verse in verses]
            if not verses or any(not (isinstance(number, int) or isinstance(number, str) and number.strip()) for number in numbers):
                raise ValueError(f"{reader.get('title')} chapter {chapter.get('chapter')} has invalid source-unit order markers.")
            # Source editions may print duplicate, skipped, or nonnumeric labels.
            # The stored sequence is source order; do not normalize it by label.
            for verse in verses:
                if verse.get("text", "").strip():
                    continue
                source_note_is_present = any(
                    note.get("verse") == verse.get("number") and (note.get("text") or note.get("source_reference"))
                    for note in chapter.get("notes", [])
                )
                explicitly_empty_source_element = (
                    verse.get("source_text_state") == "empty_source_element"
                    and verse.get("source_marker") is not None
                    and source_note_is_present
                )
                explicitly_label_only_textpart = (
                    verse.get("source_text_state") == "marker_only"
                    and verse.get("source_element_type") == "textpart_label_only"
                    and verse.get("source_marker") is not None
                    and source_note_is_present
                )
                if not (reader.get("research_corpus_id")
                        and verse.get("source_text_state") == "marker_only"
                        and source_note_is_present) and not explicitly_empty_source_element and not explicitly_label_only_textpart:
                    raise ValueError(f"{reader.get('title')} chapter {chapter.get('chapter')} has an empty unit without an explicit source marker and note.")
        companion = reader.get("parallel_translation")
        if companion:
            required_companion_fields = (
                "title", "language", "language_tag", "edition", "translator",
                "basis_language_tag", "translation_basis", "translation_method",
                "text_notice", "rights_classification", "verification_status", "source_ids", "unit_count", "unit_label", "verse_label_count",
            )
            missing_fields = [field for field in required_companion_fields if not companion.get(field)]
            if missing_fields:
                raise ValueError(
                    f"{companion.get('translation_id', 'Companion translation')} is missing basis, "
                    f"rights, or review metadata: {', '.join(missing_fields)}. Record unknowns explicitly."
                )
            if not companion["source_ids"]:
                raise ValueError(f"{companion['translation_id']} must cite at least one source record.")
            validate_rights_classification(companion, f"Translation {companion['translation_id']}")
            companion_rights = [
                layer for language in language_records for layer in language.get("records", [])
                if layer.get("translation_id") == companion["translation_id"]
                and layer.get("status") == "bundled"
            ]
            if len(companion_rights) != 1 or companion["rights_classification"] != companion_rights[0].get("rights_classification"):
                raise ValueError(f"Translation {companion['translation_id']} rights classification must match exactly one bundled registry layer.")
            if companion.get("language_tag") not in audited_language_tags or companion.get("basis_language_tag") not in audited_language_tags or companion.get("script_code") not in audited_script_codes:
                raise ValueError(f"{companion['translation_id']} uses language or script codes absent from the cited identifier audit.")
            if companion.get("text_origin") != "published_translation":
                raise ValueError(
                    f"{companion['translation_id']} must identify a published translation as its text origin; "
                    "machine-generated wording is not admissible as a scripture witness."
                )
            missing_companion_sources = set(companion.get("source_ids", [])) - source_ids
            if missing_companion_sources:
                raise ValueError(f"{companion.get('title')} refers to missing sources: {sorted(missing_companion_sources)}")
            english_chapters = companion.get("chapters", [])
            validate_observed_unit_count(companion, "unit_count", companion.get("title", companion.get("translation_id", "Companion")))
            if companion.get("verse_label_count", companion["unit_count"]) != companion["unit_count"]:
                raise ValueError(f"{companion.get('title')} verse_label_count disagrees with its generic unit_count.")
            if len(english_chapters) != companion.get("chapter_count") or [c.get("chapter") for c in english_chapters] != list(range(1, len(english_chapters) + 1)):
                raise ValueError(f"{companion.get('title')} chapter sequence/count is incomplete.")
            def english_sort_key(label):
                match = re.fullmatch(r"(\d+)([a-z]?)", str(label))
                if not match:
                    raise ValueError(f"Invalid English verse label: {label!r}")
                return int(match.group(1)), match.group(2)
            for chapter in english_chapters:
                verses = chapter.get("verses", [])
                labels = [str(verse.get("number", "")) for verse in verses]
                if not labels or labels != sorted(set(labels), key=english_sort_key) or any(not verse.get("text", "").strip() for verse in verses):
                    raise ValueError(f"{companion.get('title')} chapter {chapter.get('chapter')} has invalid labels or missing text.")

    for record in catalogue:
        if record.get("source_id") not in source_ids:
            raise ValueError(f"{record.get('display_name')} has no valid catalogue source.")
        missing = set(record.get("evidence_source_ids", [])) - source_ids
        if missing:
            raise ValueError(f"{record.get('display_name')} refers to missing evidence sources: {sorted(missing)}")
        for field in ("identity_status", "edition_or_translation", "chapter_count", "chapter_order_status",
                      "text_availability_status", "completeness_status", "rights_status", "reviewer_notes"):
            if not record.get(field):
                raise ValueError(f"{record.get('display_name')} is missing {field}; use an explicit unknown status.")

    html = HTML_PATH.read_text(encoding="utf-8")
    if len(EMBED_RE.findall(html)) != 1:
        raise ValueError('Expected exactly one <script id="archive-data"> placeholder.')

    # Keep the repository's full archive.json and per-reader JSON packages as
    # the source of record, but put only reader metadata in the initial page.
    # This makes the catalogue quick to open on mobile; the selected bundled
    # text is loaded from this same local package when its reader is opened.
    reader_files_by_id = {}
    for path in (ROOT / "readers").glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        reader_id = record.get("reader_id")
        if reader_id:
            if reader_id in reader_files_by_id:
                raise ValueError(f"Reader {reader_id} has more than one root-level JSON package.")
            reader_files_by_id[reader_id] = (path, record)

    embedded_archive = deepcopy(archive)
    for reader in embedded_archive.get("readers", []):
        reader_id = reader.get("reader_id")
        package = reader_files_by_id.get(reader_id)
        if not package:
            raise ValueError(f"Reader {reader_id} has no local JSON package.")
        package_path, package_record = package
        if package_record != reader:
            raise ValueError(f"Reader package for {reader_id} differs from archive.json.")
        if not re.fullmatch(r"[a-z0-9-]+", str(reader_id or "")):
            raise ValueError(f"Reader ID is unsafe for a local package reference: {reader_id!r}.")
        reader["reader_data_url"] = package_path.relative_to(ROOT).as_posix()
        reader.pop("chapters", None)
        for field in DEFERRED_EMBEDDED_READER_FIELDS:
            reader.pop(field, None)
        companion = reader.get("parallel_translation")
        if companion:
            companion.pop("chapters", None)

    archive_reader_ids = {reader.get("reader_id") for reader in archive.get("readers", [])}
    missing_reader_packages = archive_reader_ids - set(reader_files_by_id)
    if missing_reader_packages:
        raise ValueError(f"The local reader package index is missing archive readers: {sorted(missing_reader_packages)}")

    payload = json.dumps(embedded_archive, ensure_ascii=False, separators=(",", ":"))
    # Prevent data from closing its containing script element.
    payload = payload.replace("<", "\\u003c")
    (ROOT / "examples" / "portable-text-layers.json").write_text(
        json.dumps({
            "manifest_version": 1,
            "schema_uri": "../schemas/text-layer.schema.json",
            "coverage_statement": (
                f"This manifest includes portable metadata for {len(portable_layer_records)} selected text layers across the bundled readers. "
                "It does not represent complete canon or language coverage."
            ),
            "records": portable_layer_records,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    book_coverage = write_book_coverage(
        archive,
        {reader_id: package[0].relative_to(ROOT).as_posix() for reader_id, package in reader_files_by_id.items()},
    )
    book_coverage_schema = json.loads((ROOT / "schemas" / "book-coverage.schema.json").read_text(encoding="utf-8"))
    if book_coverage_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Book-coverage schema must declare JSON Schema 2020-12.")
    validate_closed_schema_objects(
        book_coverage, book_coverage_schema, book_coverage_schema, "book-coverage.json"
    )
    validate_schema_constraints(
        book_coverage, book_coverage_schema, book_coverage_schema, "book-coverage.json"
    )
    write_package_inventory(archive, portable_layer_records)
    write_rights_coverage(ROOT, archive)
    from build_scripture_index_txt import write as write_scripture_index_txt
    write_scripture_index_txt(archive)
    # The full archive exceeds GitHub's browser-upload per-file limit when
    # pretty-printed. Compact JSON preserves the same data while keeping the
    # generated file suitable for ordinary GitHub repositories.
    write_text_atomically(
        DATA_PATH,
        json.dumps(archive, ensure_ascii=False, separators=(",", ":")) + "\n",
    )
    from build_genesis_divine_person_lens import write as build_genesis_divine_person_lens
    build_genesis_divine_person_lens()
    HTML_PATH.write_text(EMBED_RE.sub(lambda match: match.group(1) + payload + match.group(2), html), encoding="utf-8")
    write_manifest(ROOT)
    manifest_file_count = verify_manifest(ROOT)
    print(
        f"Embedded {len(catalogue)} catalogue rows, {len(sources)} sources, "
        f"{len(related)} related records, {len(readers)} local reader packages indexed, "
        f"and {len(language_records)} language profiles into index.html; "
        f"indexed {standard_nt_research_reader_count} standard-New-Testament research readers as work/title candidates; "
        f"indexed {standard_ot_research_reader_count} standard-Old-Testament research readers (JOB and Chronicles codes reviewed as work/title matches; remaining candidates uncertain); "
        f"completed missing reader rights-status fields on {rights_status_completed_count} records; "
        f"wrote and verified checksums for {manifest_file_count} package files; "
        f"validated {offline_shell_files} local offline-cache paths (small shell pre-cached; large sources on demand)."
    )


if __name__ == "__main__":
    main()
