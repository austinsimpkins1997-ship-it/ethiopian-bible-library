"""Derive the public coverage statement from the current registry records."""

from __future__ import annotations


TEXT_ROLES = {"source_text_transcription", "source_text_edition"}
TRANSLATION_ROLES = {"translation", "historical_companion_translation", "draft_translation"}


def validate_unit_count(value: object, label: str = "coverage.unit_count") -> None:
    """Allow null for an unknown count; reject booleans, negatives, and nonintegers."""
    if isinstance(value, bool) or (value is not None and (not isinstance(value, int) or value < 0)):
        raise ValueError(f"{label} must be a nonnegative integer or null when not established.")


def validate_unit_coverage(coverage: dict, label: str = "coverage") -> None:
    """Validate count type and require evidence before treating zero as absence."""
    count = coverage.get("unit_count")
    validate_unit_count(count, f"{label}.unit_count")
    if count is None or count != 0:
        return
    if coverage.get("extent_state") == "unknown":
        raise ValueError(f"{label} cannot report zero units while its extent is unknown.")
    if coverage.get("extent_basis") not in {"source_inventory", "independent_collation"}:
        raise ValueError(f"{label} needs a completed source inventory or independent collation to report zero units.")
    scope = coverage.get("structure_description")
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError(f"{label} must name the bounded scope surveyed before reporting zero units.")


def build_coverage_statement(registry: dict, canon_registry: dict | None = None) -> str:
    languages = registry.get("languages", [])
    bundled = [
        (language, record)
        for language in languages
        for record in language.get("records", [])
        if record.get("status") == "bundled"
    ]
    text_records = [record for _, record in bundled if record.get("layer_role") in TEXT_ROLES]
    translation_records = [record for _, record in bundled if record.get("layer_role") in TRANSLATION_ROLES]
    canon_ids = {record.get("canon_id") for record in text_records if record.get("canon_id")}
    canon_books = (canon_registry or {}).get("books", [])
    names = [book.get("display_name", book["canon_id"])
             for book in canon_books if book.get("canon_id") in canon_ids]
    listed_count = len(canon_books)
    covered_count = len({book.get("canon_id") for book in canon_books} & canon_ids)
    corpus_leads = len(registry.get("corpus_leads", []))
    research_readers = len(registry.get("research_corpora", []))
    translation_leads = len(registry.get("translation_leads", []))
    edition_leads = len(registry.get("edition_leads", []))

    if names:
        text_scope = f"canon-linked reader records for {', '.join(names)}"
    else:
        text_scope = f"{len(canon_ids)} canon-linked reader records"
    translation_scope = ""
    if translation_records:
        count = len(translation_records)
        noun = "layer" if count == 1 else "layers"
        quantity = "one" if count == 1 else str(count)
        translation_scope = f" plus {quantity} separately registered translation/companion {noun}"
    list_scope = (
        f" The coverage list contains {listed_count} entries; {covered_count} currently link to bundled source-text readers and {listed_count - covered_count} have no reader bundled in this archive. These are counts for this snapshot only, not a claim that no edition exists elsewhere."
        if listed_count else ""
    )
    lead_count = translation_leads + edition_leads + corpus_leads
    lead_noun = "lead" if lead_count == 1 else "leads"
    lead_scope = f" The registry also contains {lead_count} unbundled translation, source-edition, or corpus {lead_noun}."
    research_noun = "reader" if research_readers == 1 else "readers"
    research_pronoun = "it is" if research_readers == 1 else "they are"
    research_scope = (
        f" It also includes {research_readers} separately scoped related research {research_noun}; {research_pronoun} not linked to or counted as Church-list book coverage."
        if research_readers else ""
    )
    return (
        f"This archive snapshot bundles {text_scope}{translation_scope}."
        " This is an availability count from reader records in this build, not a certification of completeness or textual accuracy; see each reader's review status."
        f" It records {len(languages)} language/script profile(s); these are scoped records, not an exhaustive world-language inventory."
        f"{list_scope}{lead_scope}{research_scope} Unknown perspectives, text, boundaries, translation paths, and rights remain unresolved where the evidence does not establish them."
        " Absence from this package means not bundled here; a zero is reported only for a defined, completed survey that found none; unassessed scope remains not surveyed or unknown, never zero by default."
        " Machine-generated or unreviewed wording is not promoted to verified scripture, and missing texts or viewpoints are not synthesized."
    )
