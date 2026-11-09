"""Record Ethiopic Josippon-related catalogue evidence without claiming a canon crosswalk."""

from __future__ import annotations

import json
from pathlib import Path

from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
CHURCH_SOURCE = "SRC-029"
BETA_SOURCE = "SRC-343"
BRITISH_LIBRARY_SOURCE = "SRC-344"
BRITISH_LIBRARY_OR822_SOURCE = "SRC-386"
OEBP_SOURCE = "SRC-422"
BETA_WORK_URL = "https://betamasaheft.awhamburg.de/works/LIT2598Yosipp/main"
BRITISH_LIBRARY_URL = "https://searcharchives.bl.uk/catalog/032-003440580"
BRITISH_LIBRARY_OR824_VIEWER_URL = "https://iiif.bl.uk/uv/#?manifest=https://bl.digirati.io/iiif/ark:/81055/vdc_100149969079.0x000001"
BRITISH_LIBRARY_OR822_URL = "https://searcharchives.bl.uk/catalog/032-003451655"
BRITISH_LIBRARY_OR822_VIEWER_URL = "https://iiif.bl.uk/uv/#?manifest=https://bl.digirati.io/iiif/ark:/81055/vdc_100149968554.0x000001"
BETA_EDITION_ID = "betamasaheft-josippon-cae2598"
BL_EDITION_ID = "bl-or824-joseph-ben-goryon"
BL_OR822_EDITION_ID = "bl-or822-joseph-ben-goryon"
OEBP_EDITION_ID = "oebp-zena-ayhud-2017-acquisition"
OEBP_URL = "https://ethiopianorthodoxbible.wordpress.com/2017/10/24/progress-we-have-acquired-the-book-of-josippon/"
MORWEN_SOURCE = "SRC-430"
SINGERMAN_SOURCE = "SRC-431"
CANON_PROJECT_SOURCE = "SRC-432"
MORWEN_URL = "https://openlibrary.org/works/OL42749782W/The_wonderful_and_most_deplorable_history_of_the_later_times_of_the_Jews"
SINGERMAN_URL = "https://singerman.judaicadhpenn.org/entry/0020/"
CANON_PROJECT_URL = "https://www.ethiopiancanon.com/blog/how-we-rebuilt-the-book-no-one-has-translated"
CANON_PROJECT_METHOD_URL = "https://www.ethiopiancanon.com/sources"
MORWEN_EDITION_ID = "morwen-josippon-epitome-1722"
CANON_PROJECT_EDITION_ID = "ethiopian-canon-josippon-reconstruction"
LEGACY_CANON_PROJECT_EDITION_ID = "ethiopian-canon-josippon-reconstruction-2026"


def _put_lead(registry: dict, lead: dict) -> None:
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[lead["edition_id"]] = lead
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    sources[BETA_SOURCE] = {
        "source_id": BETA_SOURCE,
        "source_name": "Beta maṣāḥǝft — Josippon / CAe 2598 work record",
        "url": BETA_WORK_URL,
        "inspection_and_limitations": (
            "The Beta maṣāḥǝft work record identifies CAe 2598 as Josippon and lists title forms including English "
            "Yosippon, Geʽez Zenā ʾAyhud (‘Story of Jews’), and Maṣḥafa Śǝrw. It records both Flavius Josephus and "
            "Joseph ben Gurion as attributions, explaining that the latter resulted from an error in one of the work's "
            "sources. The record lists witnesses including EMML 4773 and British Library Oriental 822 and 825, and cites "
            "Murad Kamil's 1938 edition. It does not identify this work record or any of those witnesses with the EOTC "
            "numbered title ‘Book of Josephas the Son of Bengorion’. No witness text was copied. The page displays both "
            "CC BY-SA and CC BY-NC-SA notices; no text is bundled and rights to any underlying witness remain unassessed. "
            "Inspected 2026-10-25."
        ),
        "archive_status": (
            "Work-catalogue metadata for a Josippon/Zenā ʾAyhud tradition; title-family candidate only; no text bundled"
        ),
    }
    sources[BRITISH_LIBRARY_SOURCE] = {
        "source_id": BRITISH_LIBRARY_SOURCE,
        "source_name": "British Library Archives and Manuscripts Catalogue — Or 824",
        "url": BRITISH_LIBRARY_URL,
        "full_view_url": BRITISH_LIBRARY_OR824_VIEWER_URL,
        "inspection_and_limitations": (
            "The British Library record titles the work ‘The History of the Jews, ascribed to Joseph ben Goryon’ and "
            "describes an Ethiopic/Geʽez manuscript, Or 824, with the work at ff. 3r–136v. It gives an 18th-century "
            "date range, identifies a parchment codex of 136 folios in two columns of 22 lines, and links to digitized "
            "content while stating that access restrictions apply. The catalogue does not identify the item as an EOTC "
            "canon witness, connect it to Beta maṣāḥǝft CAe 2598 or EAP704/2/3, or establish the Church-list title's "
            "textual boundaries or completeness. The British Library's image-use statement is separate from its CC BY "
            "catalogue-text notice; no images or manuscript wording are reproduced here. Inspected 2026-10-25."
        ),
        "archive_status": (
            "Digitized Geʽez manuscript catalogue metadata; related-name candidate only; no manuscript text or images bundled"
        ),
    }
    sources[BRITISH_LIBRARY_OR822_SOURCE] = {
        "source_id": BRITISH_LIBRARY_OR822_SOURCE,
        "source_name": "British Library Archives and Manuscripts Catalogue — Or 822",
        "url": BRITISH_LIBRARY_OR822_URL,
        "full_view_url": BRITISH_LIBRARY_OR822_VIEWER_URL,
        "inspection_and_limitations": (
            "The British Library record titles Or 822 ‘the History of the Jews, ascribed to Joseph ben Goryon’ and describes an Ethiopian Geʽez manuscript, "
            "ff. 2r–136v, with a colophon at f. 136r. It identifies Geʽez language and Ethiopic (ge'ez) script, dates the manuscript to the 17th century "
            "(1600–1699), and describes a 136-folio parchment codex written in two columns of 24 or 25 lines. A digitized-content viewer is linked, but the "
            "catalog says access restrictions apply. Its usage statement says the Library believes digitized Ethiopian manuscripts are not in copyright under "
            "Ethiopian law and asks users to respect their cultural heritage; this is not treated as a specific text/image reuse grant. The record does not "
            "identify Or 822 as the EOTC numbered ‘Book of Josephas the Son of Bengorion’, nor establish its relation to Or 824, Or 823, CAe 2598, or EAP704/2/3. "
            "No manuscript text or images were copied. Inspected 2026-10-26."
        ),
        "archive_status": (
            "Digitized Geʽez manuscript catalogue metadata; separate related-name candidate; no manuscript text or images bundled"
        ),
    }
    sources[OEBP_SOURCE] = {
        "source_id": OEBP_SOURCE,
        "source_name": "Ethiopian Orthodox Bible Project Committee — 2017 Josippon acquisition report",
        "url": OEBP_URL,
        "local_review_url": "research/josephas-source-review.md",
        "inspection_and_limitations": (
            "This project report says its group acquired a printed book it calls Josippon/Yosëf wäldä Koryonor, "
            "The Book of Josephas the Son of Ben Gorion, and Zëna Ayhud. It says the title page reads Zëna Ayhud in "
            "Amharic and the project identifies the volume as the right work from the greater EOTC canon. This is the "
            "project's own report and identification, not an EOTC-issued catalogue record, bibliographic edition record, "
            "or independent text collation. The post does not give a publisher, publication date, full edition statement, "
            "or reusable full text; no text or image is copied here. The page carries a 2017–2026 copyright notice. "
            "Inspected 2026-10-26."
        ),
        "rights_classification": "unknown",
        "rights_status": (
            "The page displays a 2017–2026 copyright notice. No license or permission for reuse of its text or images "
            "is identified here; only bibliographic discovery metadata is recorded."
        ),
        "archive_status": (
            "Project-reported physical-volume acquisition and title identification; attributed source assertion only; no text or images bundled"
        ),
    }
    sources[MORWEN_SOURCE] = {
        "source_id": MORWEN_SOURCE,
        "source_name": "Open Library — English edition catalogued under Josippon (1718/1722)",
        "url": MORWEN_URL,
        "inspection_and_limitations": (
            "The record describes The Wonderful and Most Deplorable History of the Later Times of the Jews, an English edition with a 1718 title page and a 1722 advertisement. Its edition note identifies Peter Morwen's English as a translation of Abraham ben David ibn Daud's abstract of book 3 of Sefer ha-kabalah, an abridgement associated with Josippon and historically attributed to Joseph ben Gorion/Josephus. This is a bibliographic record, not a checked copy or text; it is not a full English translation of the Ethiopic Church-list work. No text or images copied. Inspected 2026-10-26."
        ),
        "rights_classification": "unknown",
        "rights_status": "Only bibliographic metadata is recorded. No scanned text is bundled, and reuse terms for any digitized copy were not assessed.",
        "archive_status": "Bibliographic record for a related, abridged English text; not an Ethiopian Josippon reader",
    }
    sources[SINGERMAN_SOURCE] = {
        "source_id": SINGERMAN_SOURCE,
        "source_name": "University of Pennsylvania — Judaica Americana II, Singerman entry 0020",
        "url": SINGERMAN_URL,
        "inspection_and_limitations": (
            "This bibliography records the Boston English edition as 1718 [i.e. 1722?], 332 pages, and identifies Peter Morwen as the unnamed translator based on the Dictionary of National Biography. It independently documents the edition bibliographically, not its textual extent relative to the Ethiopic work. No text copied. Inspected 2026-10-26."
        ),
        "rights_classification": "unknown",
        "rights_status": "Only bibliographic facts are recorded; no text or images copied, and rights to any digitized copy were not assessed.",
        "archive_status": "Bibliographic corroboration for a related abridged English edition; no text bundled",
    }
    sources[CANON_PROJECT_SOURCE] = {
        "source_id": CANON_PROJECT_SOURCE,
        "source_name": "The Ethiopian Canon Project — Josippon reconstruction and source-method statements",
        "url": CANON_PROJECT_URL,
        "full_view_url": CANON_PROJECT_METHOD_URL,
        "local_review_url": "research/josephas-source-review.md",
        "inspection_and_limitations": (
            "The publisher describes an English print edition and calls its Josippon a documented reconstruction of about 116 chapters / 41,000 words, not a direct Geʽez translation. Its stated method uses Latin translations of Hebrew Sefer Yosippon, a chapter mapping attributed to Yonatan Binyam's 2017 dissertation, and E. A. Wallis Budge's translation for one Alexander section. These are publisher statements, not independently checked against the print copy, source-language text, dissertation chart, or full chapter inventory. The site carries a © 2026 notice; no reuse license for the full edition was found. No text copied. Inspected 2026-10-26."
        ),
        "rights_classification": "unknown",
        "rights_status": "The site carries a © 2026 notice and gives no reuse license for the full edition. Treat its reconstruction as not cleared for republication; no text copied.",
        "archive_status": "Publisher-described English reconstruction; direct Geʽez translation explicitly disclaimed; no text bundled",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))

    catalogue = next(item for item in archive["catalogue"] if item["catalogue_id"] == "eotc-054")
    catalogue.update({
        "display_name": "Book of Josephas the Son of Bengorion",
        "alternate_names_or_notes": (
            "The Church-list title is reproduced as published. Beta maṣāḥǝft separately records the Ethiopic Josippon / "
            "Zenā ʾAyhud work family; British Library Or 822 and Or 824 are separately catalogued manuscripts titled as a Jewish history ascribed to Joseph ben "
            "Goryon. These are related-name discovery leads, not verified identification with this numbered Church-list item."
        ),
        "identity_status": "Related Ethiopic historical-work records found; exact Church-list crosswalk remains unverified",
        "edition_or_translation": (
            "A 2017 Ethiopian Orthodox Bible Project report identifies a printed Zëna Ayhud/Josippon volume as the relevant greater-canon work. A separate publisher describes an English reconstruction as approximating the Ethiopian work, while explicitly disclaiming direct translation from Geʽez. "
            "Beta maṣāḥǝft CAe 2598 and British Library Or 822 and Or 824 are separate work/manuscript metadata leads. No edition or transcription is selected."
        ),
        "chapter_count": "Not established",
        "chapter_order_status": "Not assessed",
        "text_availability_status": (
            "British Library catalogue links digitized Or 824 content, with access restrictions. A publisher describes an English reconstruction, not a direct Geʽez translation; no text or images are bundled in this archive."
        ),
        "completeness_status": "Not assessed; neither candidate record establishes the Church-list text's extent",
        "rights_status": (
            "No text or images are bundled. The reconstruction site carries a copyright notice but gives no reuse license; Beta maṣāḥǝft shows differing license notices; British Library catalogue text and manuscript-image use have separate notices. Reuse rights for underlying witnesses remain unassessed."
        ),
        "verification_date": "2026-10-26",
        "reviewer_notes": (
            "The Church list names ‘Book of Josephas the Son of Bengorion’. Beta maṣāḥǝft CAe 2598 records Josippon and "
            "the Geʽez title Zenā ʾAyhud, and discusses Joseph ben Gurion as a mistaken attribution in one source. The "
            "British Library separately catalogs Or 822 and Or 824 as Geʽez histories of the Jews ascribed to Joseph ben Goryon, with different dates and folio extents. "
            "A 2017 Ethiopian Orthodox Bible Project report says a printed Zëna Ayhud/Josippon volume was acquired and identifies it as the greater-canon work; "
            "this is attributed project evidence, not an EOTC-issued edition record or text collation. The catalogues do not cross-identify Or 822, Or 823, "
            "Or 824, EAP704/2/3, CAe 2598 witnesses, and the Church-list title. A publisher whose site bears a © 2026 notice describes an English reconstruction but explicitly says it is not a direct Geʽez translation; its method and full text have not been independently reviewed. The 1718/1722 English text catalogued under Josippon is an abridged derivative, not a full Ethiopic reader. Treat these as separate evidence; do not infer a complete text, exact recension, or authorship by Josephus."
        ),
        "evidence_source_ids": [CHURCH_SOURCE, "SRC-033", "SRC-206", BETA_SOURCE, BRITISH_LIBRARY_SOURCE, BRITISH_LIBRARY_OR822_SOURCE, OEBP_SOURCE, MORWEN_SOURCE, SINGERMAN_SOURCE, CANON_PROJECT_SOURCE],
    })

    canon = archive["canon_registry"]
    book = next(item for item in canon["books"] if item["canon_id"] == "eotc-ot-46")
    book["source_ids"] = sorted(set(book.get("source_ids", [])) | {BETA_SOURCE, BRITISH_LIBRARY_SOURCE, BRITISH_LIBRARY_OR822_SOURCE, OEBP_SOURCE, MORWEN_SOURCE, SINGERMAN_SOURCE, CANON_PROJECT_SOURCE})
    book["reader_status"] = (
        "No reader bundled; related Geʽez catalogue records located; Church-list identity and reusable text unverified"
    )
    book["mapping_note"] = (
        "A 2017 Ethiopian Orthodox Bible Project report identifies its acquired printed Zëna Ayhud/Josippon volume as the greater-canon work; "
        "a separate publisher describes an English reconstruction on a site bearing a © 2026 notice, explicitly not a direct Geʽez translation. These are attributed claims, not independently verified editions or text collations. Beta maṣāḥǝft and British Library witnesses remain distinct. No text is bundled."
    )

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    beta_lead = {
        "edition_id": BETA_EDITION_ID,
        "candidate_canon_id": "eotc-ot-46",
        "mapping_state": "uncertain",
        "title": "Josippon / Zenā ʾAyhud — Beta maṣāḥǝft CAe 2598 work record",
        "witness_type": "unknown",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "Work-description record only, not a specific edition. Beta maṣāḥǝft CAe 2598 lists Josippon/Yosippon, "
            "Geʽez Zenā ʾAyhud and Maṣḥafa Śǝrw title forms, manuscript witnesses, and a 1938 edition bibliography."
        ),
        "scope_description": (
            "Discovery candidate for EOTC entry eotc-ot-46 based on the shared Joseph ben Goryon/Josephas name tradition "
            "and Geʽez Josippon title evidence. The Beta record discusses mistaken attributions and does not map CAe 2598 "
            "to the numbered Church-list title. Its witnesses and editions remain uncollated against that item. Metadata "
            "only; no text bundled."
        ),
        "source_ids": [CHURCH_SOURCE, BETA_SOURCE],
        "text_bundled": False,
        "rights_status": (
            "No text bundled. The catalogue page displays differing license notices; rights for the underlying manuscript witnesses are unassessed."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "Beta maṣāḥǝft work metadata and the Church-list title reviewed. No text or witness was collated; the exact "
            "EOTC crosswalk, edition, completeness, authorship, and reuse rights remain unresolved."
        ),
    }
    bl_lead = {
        "edition_id": BL_EDITION_ID,
        "candidate_canon_id": "eotc-ot-46",
        "mapping_state": "uncertain",
        "title": "The History of the Jews ascribed to Joseph ben Goryon — British Library Or 824",
        "witness_type": "manuscript",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "British Library Or 824 catalogue record describes an Ethiopic/Geʽez manuscript with ‘The History of the Jews, "
            "ascribed to Joseph ben Goryon’ at ff. 3r–136v; dated to the 18th century."
        ),
        "scope_description": (
            "Related-name candidate for Church-list entry eotc-ot-46 only. The British Library does not identify this "
            "manuscript as the EOTC ‘Book of Josephas the Son of Bengorion’, or connect it to Beta maṣāḥǝft CAe 2598 or "
            "EAP704/2/3. Boundaries, completeness, recension, and relationship to the Church-list work remain unverified. "
            "Metadata only; no manuscript text or images bundled."
        ),
        "source_ids": [CHURCH_SOURCE, BRITISH_LIBRARY_SOURCE],
        "text_bundled": False,
        "rights_status": (
            "The British Library links digitized content but states access restrictions apply. No manuscript images or text are copied; "
            "image redistribution rights are not established."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "Catalogue metadata reviewed; no codex, image, or text collation performed. The EOTC title mapping, exact extent, "
            "completeness, textual accuracy, and image/text reuse rights remain unresolved."
        ),
    }
    bl_or822_lead = {
        "edition_id": BL_OR822_EDITION_ID,
        "candidate_canon_id": "eotc-ot-46",
        "mapping_state": "uncertain",
        "title": "The History of the Jews ascribed to Joseph ben Goryon — British Library Or 822",
        "witness_type": "manuscript",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "British Library Or 822 catalogue record describes a 17th-century Ethiopian Geʽez manuscript, ff. 2r–136v, with a colophon at f. 136r. "
            "The catalog describes a 136-folio parchment codex in two columns of 24 or 25 lines."
        ),
        "scope_description": (
            "A separate related-name manuscript lead for Church-list entry eotc-ot-46. The British Library does not identify Or 822 as the numbered EOTC work "
            "or connect it to Or 823, Or 824, Beta maṣāḥǝft CAe 2598, or EAP704/2/3. Its differing folio span and date must not be silently merged with Or 824. "
            "Boundaries, completeness, recension, and relation to the Church-list text remain unverified. Metadata only; no text or images bundled."
        ),
        "source_ids": [CHURCH_SOURCE, BRITISH_LIBRARY_OR822_SOURCE],
        "text_bundled": False,
        "rights_status": (
            "The British Library links digitized content and says access restrictions apply. Its Ethiopian manuscript usage statement is not treated here as a specific reuse grant. "
            "No manuscript text or images are copied; reuse rights remain unestablished."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "British Library catalogue metadata reviewed; manuscript pages and text were not collated. The EOTC crosswalk, relation to other witnesses, completeness, "
            "transcription accuracy, and text/image reuse rights remain unresolved."
        ),
    }
    oebp_lead = {
        "edition_id": OEBP_EDITION_ID,
        "candidate_canon_id": "eotc-ot-46",
        "mapping_state": "asserted_by_source",
        "title": "Zëna Ayhud / Josippon — 2017 Ethiopian Orthodox Bible Project acquisition report",
        "witness_type": "printed_edition",
        "language_tag": "und",
        "language_name": "Undetermined",
        "script_code": "Zzzz",
        "edition_statement": (
            "The project report says it acquired a printed volume whose cover and title page read Zëna Ayhud in Amharic. "
            "The language and script of the book's body text are not identified; publisher, publication date, printing, "
            "and full bibliographic edition details are not supplied."
        ),
        "scope_description": (
            "The report identifies the acquired volume as Josippon / The Book of Josephas the Son of Ben Gorion and says it is the relevant work "
            "from the greater EOTC canon. This is an attributed project assertion. It is not a Church-issued edition record, independent verification "
            "of the title page, or collation with the Church-list entry. Metadata only; no text or images bundled."
        ),
        "source_ids": [CHURCH_SOURCE, OEBP_SOURCE],
        "text_bundled": False,
        "rights_status": (
            "No full text or image is bundled. The report's site displays a copyright notice but no reuse license for the acquired book; "
            "rights to any edition or translation remain unassessed."
        ),
        "rights_classification": "unknown",
        "review_status": (
            "The project's own acquisition and title-identification report was reviewed. No publication data, physical copy, title-page image, "
            "or text was independently checked. The exact edition, scope, completeness, textual identity, accuracy, and reuse rights remain unresolved."
        ),
    }
    morwen_lead = {
        "edition_id": MORWEN_EDITION_ID,
        "candidate_canon_id": "eotc-ot-46",
        "mapping_state": "related_work",
        "title": "The Wonderful and Most Deplorable History of the Later Times of the Jews — Morwen / Howell, 1718 [i.e. 1722?]",
        "witness_type": "printed_edition",
        "language_tag": "en",
        "language_name": "English",
        "script_code": "Latn",
        "edition_statement": (
            "Open Library and the University of Pennsylvania bibliography describe a Boston English edition titled The Wonderful and Most Deplorable History of the Later Times of the Jews, dated 1718 [i.e. 1722?], with Peter Morwen named as translator in the bibliographic notes."
        ),
        "scope_description": (
            "Related historical text only, not a translation of the Ethiopian Church-list Josippon. The catalog note identifies Morwen's version as Abraham ibn Daud's abridged account in book 3 of Sefer ha-kabalah, a text associated with Josippon but not equivalent to a complete Ethiopic witness. No text was inspected or copied; do not use it as a complete reader or crosswalk."
        ),
        "source_ids": [CHURCH_SOURCE, MORWEN_SOURCE, SINGERMAN_SOURCE],
        "text_bundled": False,
        "rights_status": "Only bibliographic metadata is recorded. No text is bundled and rights to a scan or digital transcription were not assessed.",
        "rights_classification": "unknown",
        "review_status": "Bibliographic descriptions compared; no copy was inspected. This is a related abridged text, not an Ethiopic witness or complete Josippon translation.",
    }
    reconstruction_lead = {
        "edition_id": CANON_PROJECT_EDITION_ID,
        "candidate_canon_id": "eotc-ot-46",
        "mapping_state": "asserted_by_source",
        "title": "Josippon — English reconstruction described by The Ethiopian Canon Project",
        "witness_type": "printed_edition",
        "language_tag": "en",
        "language_name": "English",
        "script_code": "Latn",
        "edition_statement": (
            "The publisher's methodology page (site notice © 2026) describes an English print edition with a 116-chapter, approximately 41,000-word Josippon reconstruction. The publisher explicitly says it is not a direct translation from Geʽez."
        ),
        "scope_description": (
            "The publisher presents this reconstruction as approximating the Ethiopian Josippon's scope and ordering. Its stated method uses Latin translations of Hebrew Sefer Yosippon plus a dissertation's comparative mapping, with one Alexander section from Budge's Geʽez-derived English. This is an attributed publisher claim, not an independently verified crosswalk; the publisher explicitly says it is not a direct Geʽez translation. Completeness and accuracy have not been reviewed. No text bundled."
        ),
        "source_ids": [CHURCH_SOURCE, CANON_PROJECT_SOURCE],
        "text_bundled": False,
        "rights_status": "The website carries a © 2026 notice and gives no reuse license for the full reconstruction. No text is copied or bundled; permission for republication is not established.",
        "rights_classification": "unknown",
        "review_status": "Publisher's public method and edition pages inspected; print copy, all 116 chapter boundaries, source collation, underlying comparative map, and textual accuracy not independently verified.",
    }
    registry["edition_leads"] = [
        lead for lead in registry.get("edition_leads", [])
        if lead.get("edition_id") != LEGACY_CANON_PROJECT_EDITION_ID
    ]
    _put_lead(registry, beta_lead)
    _put_lead(registry, bl_lead)
    _put_lead(registry, bl_or822_lead)
    _put_lead(registry, oebp_lead)
    _put_lead(registry, morwen_lead)
    _put_lead(registry, reconstruction_lead)
    write_text_atomically(registry_path, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    archive["translation_registry"] = registry

    canon_path = ROOT / "canon-registry.json"
    canon_path.write_text(json.dumps(canon, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    report = (
        "# Book of Josephas the Son of Bengorion — source review\n\n"
        f"The [EOTC English list]({sources[CHURCH_SOURCE]['url']}) gives this title as entry 46. "
        f"[Beta maṣāḥǝft CAe 2598]({BETA_WORK_URL}) catalogs the Ethiopic Josippon / Zenā ʾAyhud work family and records multiple attributions; "
        "it does not identify the record as the Church-list entry. "
        f"The [British Library Or 824 catalogue]({BRITISH_LIBRARY_URL}) describes a Geʽez history of the Jews ascribed to Joseph ben Goryon. "
        f"A separately catalogued [Or 822 witness]({BRITISH_LIBRARY_OR822_URL}) dates to the 17th century and covers ff. 2r–136v, with a colophon at f. 136r; "
        "the Or 824 catalogue dates to the 18th century and gives ff. 3r–136v. The different records and folio descriptions are retained separately.\n\n"
        f"The [Ethiopian Orthodox Bible Project Committee's 2017 report]({OEBP_URL}) says it acquired a printed Zëna Ayhud/Josippon volume and identifies it as the greater-canon work. This is the project's own assertion, not an EOTC-issued edition record or independent text collation; publication details and text reuse rights remain unknown. It adds an attributed discovery lead but no reader coverage.\n\n"
        f"A current external English edition is described by [The Ethiopian Canon Project]({CANON_PROJECT_URL}) and its [sources/methodology page]({CANON_PROJECT_METHOD_URL}). The publisher says its Josippon reconstruction approximates the Ethiopian text's scope and ordering, has 116 chapters, and is built primarily through Latin witnesses to Hebrew Sefer Yosippon with a dissertation's crosswalk; it explicitly says the result is not a direct Geʽez translation. These are publisher claims: no print copy, complete chapter structure, underlying source collation, translation accuracy, or reuse license for the full edition has been independently reviewed. The site bears a © 2026 notice, which does not itself date publication. It is recorded as an external, source-asserted edition lead only; no text is copied or bundled.\n\n"
        f"The tempting 1718/1722 English title [The Wonderful and Most Deplorable History of the Later Times of the Jews]({MORWEN_URL}) is not a complete English Ethiopian Josippon. Open Library's edition note and the [University of Pennsylvania's Judaica Americana bibliography]({SINGERMAN_URL}) identify it as Peter Morwen's rendering of Abraham ibn Daud's abridged Josippon account, in its book-3 / Sefer ha-kabalah context. It is recorded as a related text, not as a reader or crosswalk. No digitized text was inspected or copied.\n\n"
        "These are discovery leads, not a verified crosswalk. Or 822, Or 823, Or 824, Beta maṣāḥǝft's listed Josippon witnesses, and the separate EAP704/2/3 manuscript "
        "must not be merged. The British Library provides a digitized-content link but says access restrictions apply; its image-use statement is not a blanket license. "
        "Beta maṣāḥǝft's record displays differing license notices. No text or images are bundled, and no authorial attribution, chapter structure, "
        "complete extent, or exact Church-list identity is asserted. The added contemporary reconstruction remains attributed and unverified; neither it nor the historical abridgement is bundled or counted as canon-linked reader coverage.\n"
    )
    (ROOT / "research" / "josephas-source-review.md").write_text(report, encoding="utf-8")
    print("Recorded separate Josippon witnesses, an attributed English reconstruction, and an 18th-century abridged related text for Church-list entry 46; no new reader text bundled or canon-linked coverage added.")


if __name__ == "__main__":
    build()
