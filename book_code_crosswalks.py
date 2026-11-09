"""Cautious title-code candidates for aligning common Bible book codes to the 81-entry list.

These are discovery pointers only. They do not establish canon membership,
tradition affiliation, textual identity, chapter-scope equivalence, or completeness.
"""

PUBLISHER_BOOK_CODE_CANDIDATES = {
    "GEN": "eotc-ot-01", "EXO": "eotc-ot-02", "LEV": "eotc-ot-03", "NUM": "eotc-ot-04",
    "DEU": "eotc-ot-05", "JOS": "eotc-ot-06", "JDG": "eotc-ot-07", "RUT": "eotc-ot-08",
    "1SA": "eotc-ot-09", "2SA": "eotc-ot-09", "1KI": "eotc-ot-10", "2KI": "eotc-ot-10",
    "1CH": "eotc-ot-11", "2CH": "eotc-ot-12", "EZR": "eotc-ot-15", "NEH": "eotc-ot-15",
    "EST": "eotc-ot-19", "JOB": "eotc-ot-22", "PSA": "eotc-ot-23", "PRO": "eotc-ot-24",
    "ECC": "eotc-ot-27", "SNG": "eotc-ot-28", "ISA": "eotc-ot-29", "JER": "eotc-ot-30",
    "EZK": "eotc-ot-31", "DAN": "eotc-ot-32", "HOS": "eotc-ot-33", "AMO": "eotc-ot-34",
    "JOL": "eotc-ot-36", "MIC": "eotc-ot-35", "OBA": "eotc-ot-37", "JON": "eotc-ot-38", "NAM": "eotc-ot-39",
    "HAB": "eotc-ot-40", "ZEP": "eotc-ot-41", "HAG": "eotc-ot-42", "ZEC": "eotc-ot-43",
    "MAL": "eotc-ot-44", "MAT": "eotc-nt-01", "MRK": "eotc-nt-02", "LUK": "eotc-nt-03",
    "JHN": "eotc-nt-04", "ACT": "eotc-nt-05", "ROM": "eotc-nt-06", "1CO": "eotc-nt-07",
    "2CO": "eotc-nt-08", "GAL": "eotc-nt-09", "EPH": "eotc-nt-10", "PHP": "eotc-nt-11",
    "COL": "eotc-nt-12", "1TH": "eotc-nt-13", "2TH": "eotc-nt-14", "1TI": "eotc-nt-15",
    "2TI": "eotc-nt-16", "TIT": "eotc-nt-17", "PHM": "eotc-nt-18", "HEB": "eotc-nt-19",
    "JAS": "eotc-nt-25", "1PE": "eotc-nt-20", "2PE": "eotc-nt-21", "1JN": "eotc-nt-22",
    "2JN": "eotc-nt-23", "3JN": "eotc-nt-24", "JUD": "eotc-nt-26", "REV": "eotc-nt-27",
}

GROUPED_CANDIDATE_CODES = {"1SA", "2SA", "1KI", "2KI", "EZR", "NEH"}

# USFM/USX 3.2's official book-code table documents these tradition- and
# edition-specific distinctions. Keep code/title discovery separate from a
# claim that the source member has matching contents or extent.
CODE_SCOPE_NOTES = {
    "1SA": "USFM documents that 1 Samuel may be called 1 Kings/Kingdoms in Orthodox numbering.",
    "2SA": "USFM documents that 2 Samuel may be called 2 Kings/Kingdoms in Orthodox numbering.",
    "1KI": "USFM documents that 1 Kings may be called 3 Kings/Kingdoms in Orthodox numbering.",
    "2KI": "USFM documents that 2 Kings may be called 4 Kings/Kingdoms in Orthodox numbering.",
    "EZR": "USFM says EZR can denote Hebrew Ezra or Ezra-Nehemiah when treated as one book.",
    "NEH": "USFM says Nehemiah may be appended to Ezra in a single-book arrangement.",
    "EST": "USFM reserves EST for Hebrew Esther and identifies Greek Septuagint Esther separately as ESG.",
    "PSA": "USFM notes differing Psalm inventories, including 151 Psalms in Orthodox Bibles; PSA alone does not establish whether Psalm 151 is included or separate.",
    "PRO": "USFM notes 31 Proverbs in the standard inventory but 24 in the Ethiopian Bible; this code/title match does not establish extent or the relation to a separately listed Reproof.",
    "DAN": "USFM reserves DAN for Hebrew Daniel and identifies the longer Greek Septuagint Daniel separately as DAG.",
}


def candidate_note(code: str, canon_id: str) -> str:
    """Describe a provisional title match without turning it into canon coverage."""
    partial = (
        " This reader is one named component of a grouped catalogue entry, not the whole entry."
        if code in GROUPED_CANDIDATE_CODES else ""
    )
    scope_detail = CODE_SCOPE_NOTES.get(code)
    scope_note = (
        f" {scope_detail} This distinction is documented in the official USFM/USX 3.2 book identifier reference (SRC-396)."
        if scope_detail else ""
    )
    return (
        f"Provisional title-level candidate for {canon_id}, based only on publisher standard book code {code} "
        "and the archive's English navigation-name lookup. This does not establish EOTC, Eritrean, or other canon "
        f"affiliation, text identity, scope equivalence, or completeness.{partial}{scope_note} "
        "It remains a research reader and is "
        "excluded from canon-linked coverage pending independent crosswalk review."
    )
