"""Build the Church-list coverage index without treating catalogue rows as canon units."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "canon-registry.json"
SOURCE_TRANSCRIPTION = ROOT / "research" / "eotc-english-canon-source-transcription.json"

OT = [
    ("Genesis", ["eotc-001"]), ("Exodus", ["eotc-002"]),
    ("Leviticus", ["eotc-003"]), ("Numbers", ["eotc-004"]),
    ("Deuteronomy", ["eotc-005"]), ("Joshua", ["eotc-006"]),
    ("Judges", ["eotc-007"]), ("Ruth", ["eotc-008"]),
    ("I and II Samuel", ["eotc-009", "eotc-010"]),
    ("I and II Kings", ["eotc-011", "eotc-012"]),
    ("I Chronicles", ["eotc-013"]), ("II Chronicles", ["eotc-014"]),
    ("Jubilees", ["eotc-015"]), ("Enoch", ["eotc-016"]),
    ("Ezra and Nehemia", ["eotc-017", "eotc-018"]),
    ("Ezra (2nd) and Ezra Sutuel", ["eotc-090", "eotc-019"]),
    ("Tobit", ["eotc-020"]), ("Judith", ["eotc-021"]),
    ("Esther", ["eotc-022"]),
    ("I Maccabees", ["eotc-023"]),
    ("II and III Maccabees", ["eotc-024", "eotc-025"]),
    ("Job", ["eotc-026"]), ("Psalms", ["eotc-027"]),
    ("Proverbs", ["eotc-029"]), ("Tegsats (Reproof)", ["eotc-030"]),
    ("Metsihafe Tibeb (books of wisdom)", ["eotc-031"]),
    ("Ecclesiastes", ["eotc-032"]), ("Song of Songs", ["eotc-028"]),
    ("Isaiah", ["eotc-033"]),
    ("Jeremiah", ["eotc-034", "eotc-035", "eotc-036", "eotc-037", "eotc-038"]),
    ("Ezekiel", ["eotc-039"]), ("Daniel", ["eotc-040"]),
    ("Hosea", ["eotc-041"]), ("Amos", ["eotc-042"]),
    ("Micah", ["eotc-043"]), ("Joel", ["eotc-044"]),
    ("Obadiah", ["eotc-045"]), ("Jonah", ["eotc-046"]),
    ("Nahum", ["eotc-047"]), ("Habakkuk", ["eotc-048"]),
    ("Zephaniah", ["eotc-049"]), ("Haggai", ["eotc-050"]),
    ("Zechariah", ["eotc-051"]), ("Malachi", ["eotc-052"]),
    ("Book of Joshua the Son of Sirac", ["eotc-053"]),
    ("Book of Josephas the Son of Bengorion", ["eotc-054"]),
]

NT_NAMES = [
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "I Corinthians",
    "II Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "I Thessalonians", "II Thessalonians", "I Timothy", "II Timothy", "Titus",
    "Philemon", "Hebrews", "I Peter", "II Peter", "I John", "II John",
    "III John", "James", "Jude", "Revelation", "Sirate Tsion (Book of Order)",
    "Tizaz (Book of Herald)", "Gitsew", "Abtilis", "I Book of Dominos",
    "II Book of Dominos", "Book of Clement", "Didascalia",
]
# Catalogue display order puts James before the Johannine and Petrine letters,
# while the Church's 81-entry list places James after III John. Keep this
# crosswalk explicit; arithmetic IDs silently attached six wrong titles.
NT_CATALOGUE_IDS = {
    20: "eotc-075",  # I Peter
    21: "eotc-076",  # II Peter
    22: "eotc-077",  # I John
    23: "eotc-078",  # II John
    24: "eotc-079",  # III John
    25: "eotc-074",  # James
}

NT_MAPPING_METADATA = {
    28: ("The Church list's transliterated title is indexed to the first Sinodos candidate. Asale's dissertation (2015, pp. 178–180) identifies four Sinodos books and names Ser'ata Seyon / Order of Zion among them. This supports title-level navigation, not the identity, boundaries, or edition of this catalogue text.", ["SRC-029", "SRC-073"]),
    29: ("The Church list's transliterated title is indexed to a Te'ezaz candidate. Asale's dissertation (2015, pp. 178–180) lists Te'ezaz among four Sinodos books. This supports title-level navigation, not the identity, boundaries, or edition of this catalogue text.", ["SRC-029", "SRC-073"]),
    30: ("The Church list's transliterated title is indexed to a Gessew candidate. Asale's dissertation (2015, pp. 178–180) lists Gessew among four Sinodos books. This supports title-level navigation, not the identity, boundaries, or edition of this catalogue text.", ["SRC-029", "SRC-073"]),
    31: ("The Church list's transliterated title is indexed to an Abtelis candidate. Asale's dissertation (2015, pp. 178–180) lists Abtelis among four Sinodos books. This supports title-level navigation, not the identity, boundaries, or edition of this catalogue text.", ["SRC-029", "SRC-073"]),
    32: ("The Church page lists two 'Book of Dominos' entries. Asale's dissertation (2015, pp. 178–180) describes a two-part Book of the Covenant in a broader-canon account; the equivalence of the translated labels and exact text boundaries are not established here.", ["SRC-029", "SRC-073"]),
    33: ("The Church page lists two 'Book of Dominos' entries. Asale's dissertation (2015, pp. 178–180) describes a two-part Book of the Covenant in a broader-canon account; the equivalence of the translated labels and exact text boundaries are not established here.", ["SRC-029", "SRC-073"]),
    34: ("Asale's dissertation (2015, pp. 178–180) describes three Epistles of Clement counted together as one book in one canon account. This is comparative context, not proof that this title identifies a particular Clement text or edition.", ["SRC-029", "SRC-073"]),
    35: ("Asale's dissertation (2015, pp. 178–180) includes Didascalia among the broader New Testament additions. This supports title-level navigation only; the exact text, edition, and boundaries of this catalogue row remain unverified.", ["SRC-029", "SRC-073"]),
}

READER_IDS = {
    1: "genesis-geez-dillmann-hacohen",
    2: "exodus-geez-dillmann-hacohen",
    3: "leviticus-geez-dillmann-hacohen",
    4: "numbers-geez-dillmann-hacohen",
    5: "deuteronomy-geez-dillmann-hacohen",
    6: "joshua-geez-dillmann-hacohen",
    7: "judges-geez-dillmann-hacohen",
    8: "ruth-geez-dillmann-hacohen",
    13: "jubilees-geez-hacohen",
    14: "enoch-geez-eotc",
    23: "psalms-geez-ludolf-hacohen",
}
READER_FILES = {
    1: "genesis-geez.json",
    2: "exodus-geez.json",
    3: "leviticus-geez.json",
    4: "numbers-geez.json",
    5: "deuteronomy-geez.json",
    6: "joshua-geez.json",
    7: "judges-geez.json",
    8: "ruth-geez.json",
    13: "jubilees-geez-hacohen.json",
    14: "enoch-geez-eotc.json",
    23: "psalms-geez-ludolf.json",
}
SOURCE_METADATA = {
    20: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    21: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    24: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    25: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    45: {
        "source_ids": ["SRC-029", "SRC-101"],
    },
    23: {
        "source_ids": ["SRC-029", "SRC-036", "SRC-058", "SRC-059", "SRC-067", "SRC-068", "SRC-069"],
        "mapping_note": (
            "The Church list names Psalms; this reader contains the TAU-hosted Geʽez transcription of Ludolf's Psalter in 151 Rahlfs-numbered pages. "
            "The reader preserves source label anomalies and has not been independently collated. This supports navigation, not an exact canon crosswalk or completeness claim."
        ),
    },
    14: {
        "source_ids": ["SRC-029", "SRC-040", "SRC-065", "SRC-066"],
        "mapping_note": (
            "The Church list names Enoch, and the pinned Beta maṣāḥǝft block EOTCed is labeled as text of the EOTC printed Bible. "
            "The exact printed exemplar and date are unspecified. The reader preserves the TEI block's 108 chapters and 1,058 labeled lines; "
            "chapter 21 starts at source marker 2. This verifies the stored block's structure, not manuscript or printed-page accuracy."
        ),
    }
}


def main() -> None:
    source_list = json.loads(SOURCE_TRANSCRIPTION.read_text(encoding="utf-8"))
    old_labels = source_list.get("old_testament", [])
    new_labels = source_list.get("new_testament", [])
    if source_list.get("source_id") != "SRC-029":
        raise ValueError("Canon-label transcription must cite the Church source SRC-029.")
    if [row.get("number") for row in old_labels] != list(range(1, 47)) or [row.get("number") for row in new_labels] != list(range(1, 36)):
        raise ValueError("Canon-label transcription must preserve ordered 46/35 numbering.")
    books = []
    for number, (name, catalogue_ids) in enumerate(OT, 1):
        source_label = old_labels[number - 1]["label"]
        reader_id = READER_IDS.get(number)
        bundled_reader = bool(reader_id and (ROOT / "readers" / READER_FILES[number]).is_file())
        source_metadata = SOURCE_METADATA.get(number, {})
        english_companion = False
        if bundled_reader:
            reader_data = json.loads((ROOT / "readers" / READER_FILES[number]).read_text(encoding="utf-8"))
            companion = reader_data.get("parallel_translation", {})
            english_companion = companion.get("language_tag") == "en" and companion.get("text_origin") == "published_translation"
        reader_status = (
            "Bundled: Geʽez EOTC printed-edition transcription" if number == 14 and bundled_reader else
            "Bundled: Geʽez Ludolf Psalter transcription" if number == 23 and bundled_reader else
            "Bundled: Geʽez + English Brenton companion" if number == 1 and bundled_reader else
            "Bundled: Geʽez source transcription + English Brenton research companion (wording unreviewed)" if number == 2 and english_companion else
            "Bundled: Geʽez source transcription" if bundled_reader else
            source_metadata.get("reader_status", "No reader bundled here; external availability not assessed")
        )
        mapping_note = (
            "The Church page presents ‘Ezra (2nd)’ and ‘Ezra Sutuel’ as one numbered entry. "
            "The title-level candidate rows preserve those names, but their identities and "
            "crosswalk to TAU's distinct Ethiopic Ezra I/II/III works remain unresolved."
            if number == 16 else
            "The Church page uses the plural phrase ‘books of wisdom.’ Wisdom of Solomon is "
            "a research candidate row only; its identity as the exact listed work is not established."
            if number == 26 else
            "The Church list's ‘I Maccabees’/‘II and III Maccabees’ labels are preserved. "
            "Mikre-Sellassie (1993) documents different Maccabean groupings in broader and narrower list traditions; those labels do not prove a one-to-one mapping to the catalogue's Meqabyan texts, whose identities remain unresolved."
            if number in (20, 21) else
            "Mikre-Sellassie (1993) describes Messale (Proverbs 1–24) and Tegsas (Proverbs 25–31) as separate titles in a historical canon account. The Church page lists Proverbs and Tegsats (Reproof); their exact boundaries and relationship to a specific edition remain unverified."
            if number in (24, 25) else
            "The Church page's 'Book of Joshua the Son of Sirac' is indexed to a Sirach/Ecclesiasticus title candidate. Mikre-Sellassie (1993) records a 'Wisdom of Jesus, Son of Sirach' in a different list; that comparison does not establish the exact work or edition crosswalk here."
            if number == 45 else
            source_metadata.get("mapping_note", "") if source_metadata else
            "This is a grouped title in the Church list; separate catalogue rows are discovery aids, not proof of exact textual boundaries."
            if len(catalogue_ids) > 1 else ""
        )
        books.append({
            "canon_id": f"eotc-ot-{number:02d}", "section": "Old Testament",
            "section_number": number, "display_name": name,
            "source_label": source_label,
            "catalogue_ids": catalogue_ids, "source_ids": source_metadata.get("source_ids", ["SRC-029"]),
            "reader_status": reader_status,
            "reader_id": reader_id if bundled_reader else None,
            "mapping_note": mapping_note,
        })
    for number, name in enumerate(NT_NAMES, 1):
        source_label = new_labels[number - 1]["label"]
        books.append({
            "canon_id": f"eotc-nt-{number:02d}", "section": "New Testament",
            "section_number": number, "display_name": name,
            "source_label": source_label,
            "catalogue_ids": [NT_CATALOGUE_IDS.get(number, f"eotc-{54 + number:03d}")],
            "source_ids": NT_MAPPING_METADATA.get(number, ("", ["SRC-029"]))[1],
            "reader_status": "No reader bundled here; external availability not assessed", "reader_id": None,
            "mapping_note": NT_MAPPING_METADATA.get(number, ("", []))[0],
        })
    if len(OT) != 46 or len(NT_NAMES) != 35 or len(books) != 81:
        raise ValueError("Church-list registry must contain 46 Old Testament and 35 New Testament entries.")
    registry = {
        "source_id": "SRC-029",
        "basis": "The Ethiopian Orthodox Tewahedo Church’s own English canon page lists 46 Old Testament and 35 New Testament entries and explicitly states a total of 81. Grouped names are kept as that source presents them; they are not silently split into separate canonical units.",
        "mapping_caution": "Links to this archive’s 90 research rows support navigation only. They do not independently establish a title’s canonical mapping, text identity, completeness, or translation.",
        "context_source_ids": ["SRC-072", "SRC-073", "SRC-101"],
        "scholarly_context": "The 81-count and wording above describe the Church's cited English page, not a claim that all historical or scholarly lists have identical contents or counting rules. Bruk Ayele Asale's 2016 peer-reviewed article says the composition of the traditional 81 remains obscure; his 2015 University of KwaZulu-Natal thesis discusses multiple lists and competing broader/narrower classifications, including unresolved manuscript connections among Proverbs and Tegsas and names for the broader New Testament books. G.A. Mikre-Sellassie's 1993 article compares historical list traditions that group Proverbs, Maccabees, Sirach, and other works differently. These are attributed scholarly analyses, not Church rulings or proof of this page's edition-level crosswalks. The archive does not infer alternate mappings or generate missing canon entries from them.",
        "book_count": len(books),
        "reader_count": sum(entry["reader_id"] is not None for entry in books),
        "books": books,
    }
    OUTPUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {OUTPUT.name}: {len(OT)} Old Testament entries + {len(NT_NAMES)} New Testament entries.")


if __name__ == "__main__":
    main()
