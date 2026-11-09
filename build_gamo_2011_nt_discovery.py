"""Record the separately catalogued 2011 Gamo New Testament without merging editions."""

from __future__ import annotations

from rights_metadata import same_source_identity


SOURCE = {
    "source_id": "SRC-397",
    "source_name": "eBible.org — Gamo New Testament (GMVWBT / gmvRNT), catalog and terms",
    "url": "https://ebible.org/find/details.php?id=gmvwbt",
    "inspection_and_limitations": (
        "The provider identifies Ooratha Caaqo Maxaafa Gamoththo / Gamo NT, language gmv, "
        "ID GMVWBT or gmvRNT, copyright © 2011 Wycliffe Bible Translators, Inc., and a New "
        "Testament scope. The same page first names a CC BY-NC-ND 3.0 license, then in a "
        "separate copyright block names CC BY-NC-ND 4.0 (dated 2014-04-25); this archive "
        "preserves the discrepancy and does not choose which version governs. The page does "
        "not state a source or relay language or name a script in its metadata; displayed "
        "sample verses visibly use Latin orthography, so its script assignment is provisional. It does not establish "
        "identity with the separate 2024 GMVETW/gmve Gamo Bible. No text is copied."
    ),
    "archive_status": (
        "Provider catalog inspected 2026-10-26; distinct 2011 New Testament lead recorded "
        "metadata-only. Translation path, controlling license version, detailed book/chapter "
        "extent, accuracy, and canon crosswalk remain unverified."
    ),
    "rights_classification": "mixed",
    "rights_status": (
        "The provider page states CC BY-NC-ND 3.0 in one block and CC BY-NC-ND 4.0 in another. "
        "The controlling notice is unresolved; do not treat either version as settled permission. "
        "No text is bundled."
    ),
}


CORPUS_LEAD = {
    "corpus_id": "gmv-gmvwbt-2011-nt",
    "title": "Ooratha Caaqo Maxaafa Gamoththo (GMVWBT / gmvRNT)",
    "language_tag": "gmv",
    "language_name": "Gamo (Gamotso)",
    "script_code": "Latn",
    "script_status": "provisional",
    "publisher": "Wycliffe Bible Translators, Inc. (as identified by eBible.org)",
    "publication_year": "2011 (copyright notice; provider page last updated 2014-04-25)",
    "scope_description": "Provider identifies this as the New Testament in Gamo. Book-level inventory and edition completeness were not checked.",
    "basis_language_tag": "und",
    "basis_description": "Source language and any relay-language path are not stated on the inspected provider page; und is used for the unknown basis language.",
    "translation_path": None,
    "contributors": "Wycliffe Bible Translators, Inc. is named for the translation; individual translators are not named on the inspected page.",
    "text_bundled": False,
    "rights_status": "The same provider page names CC BY-NC-ND 3.0 in its initial copyright information and CC BY-NC-ND 4.0 in a separate New Testament copyright block. The controlling version is unresolved. No text is redistributed by this archive; verify current permission terms with the rights holder before reuse.",
    "rights_classification": "mixed",
    "review_status": "Catalog metadata and the two on-page license-version statements recorded; text, scope beyond the provider's New Testament label, translation path, and accuracy not reviewed.",
    "source_ids": ["SRC-397"],
    "notes": "Keep distinct from the 2024 GMVETW/gmve Gamo full-Bible edition (SRC-168). The 2012 New Testament completion date in the agency history (SRC-375) does not by itself prove textual identity with this provider record.",
}


def apply(archive: dict) -> None:
    """Idempotently add the catalog source and metadata-only corpus lead."""
    sources = archive.setdefault("sources", [])
    by_id = {item.get("source_id"): item for item in sources}
    existing = by_id.get(SOURCE["source_id"])
    if existing is not None and not same_source_identity(existing, SOURCE):
        raise ValueError(f"Conflicting source record {SOURCE['source_id']}.")
    if existing is None:
        sources.append(dict(SOURCE))
        sources.sort(key=lambda item: item["source_id"])
    else:
        # Keep the provider's explicitly conflicting license notices more specific than
        # the generic unknown fallback used for other source records.
        existing.update({key: SOURCE[key] for key in ("rights_classification", "rights_status")})

    registry = archive.setdefault("translation_registry", {})
    leads = registry.setdefault("corpus_leads", [])
    existing_lead = next((item for item in leads if item.get("corpus_id") == CORPUS_LEAD["corpus_id"]), None)
    if existing_lead is not None and existing_lead != CORPUS_LEAD:
        raise ValueError(f"Conflicting corpus lead {CORPUS_LEAD['corpus_id']}.")
    if existing_lead is None:
        leads.append(dict(CORPUS_LEAD))
        leads.sort(key=lambda item: item["corpus_id"])
