"""Record Digital Bible Society's Tigrinya edition leads without copying restricted text."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

SOURCES = [
    {
        "source_id": "SRC-331",
        "source_name": "Digital Bible Society — Tigrinya Common Language Bible profile",
        "url": "https://et.bible.cloud/en/bibles/TIRTBI/",
        "inspection_and_limitations": "Inspected 2026-10-25. Digital Bible Society's profile identifies Tigrinya, Ethiopic (Geʽez) alphabet, and a Tigrinya Common Language Bible. It lists a 1998 Genesis portion attributed to the Bible Society of Eritrea, a historic Tigrinya New Testament scan, and a Bible Society of Ethiopia-hosted Tigrinya resource. These are separate discovery rows; the page does not establish they are the same edition, the full extent of any item, reuse permission, or an Ethiopian Orthodox Church canon crosswalk.",
        "archive_status": "Provider catalogue and edition discovery page inspected; no text copied; edition identities and rights for listed resources remain unverified",
    },
    {
        "source_id": "SRC-332",
        "source_name": "Digital Bible Society — Tigrinya Common Language Bible PDF (TIRTBI)",
        "url": "https://bibles.dbs.org/TIRTBI/pdf/TIRTBI.pdf",
        "inspection_and_limitations": "Inspected 2026-10-25. The 133-page PDF identifies the Tigrinya Common Language Bible, year 1991, Bible Society of Ethiopia, and copyright © Bible Society of Ethiopia. Its generated metadata calls the translation a full Bible, but the visible table of contents in the PDF lists the standard 27 New Testament books only and no Old Testament titles. This is a scope discrepancy between edition-level metadata and the supplied PDF's visible contents; the archive records the PDF as an observed New Testament contents lead, not a verified complete Bible. No chapter-by-chapter boundary, wording, or completeness audit was performed. The PDF includes a Tigrinya statement describing Digital Bible Society's noncommercial distribution; no permission for this archive to reproduce the text was identified.",
        "archive_status": "PDF metadata and contents page inspected for scope and rights discovery; text not copied; apparent NT-only file scope conflicts with full-Bible metadata claim",
    },
    {
        "source_id": "SRC-333",
        "source_name": "Bible Society — Tigrinya Bible, Traditional Translation (ISBN 9783438081964)",
        "url": "https://www.biblesociety.org.uk/products/9783438081964/",
        "inspection_and_limitations": "Inspected 2026-10-25. The Bible Society product catalogue calls this a full-text Bible in Tigrinya, names the Bible Society of Eritrea as author/publisher, and gives ISBN 9783438081964. This is product metadata, not an inspection of the book's contents; it does not establish the canon, exact edition date, completeness, EOTC or Eritrean Orthodox crosswalk, or permission to reproduce the text.",
        "archive_status": "Product metadata inspected; no text copied; canon scope, content, and archive reuse rights remain unverified",
    },
    {
        "source_id": "SRC-334",
        "source_name": "Bible for the Nations — Tigrinya Bible product record (1998 Revised Bible)",
        "url": "https://www.bible-for-the-nations.com/en/Bible-in-Tigrinya/179151000",
        "inspection_and_limitations": "Inspected 2026-10-25. The distributor describes a whole Tigrinya Bible (Old and New Testaments), names the Revised Bible in Tigrigna and Bible Society of Eritrea, gives 1998, and lists a 1,140-page second edition. This retail record corroborates bibliographic identity and the seller's whole-Bible description only; the printed contents, canon scope, completeness, accuracy, and permission for digital reproduction were not inspected or established.",
        "archive_status": "Retail bibliographic record inspected; no text copied; contents, canon mapping, and digital reuse rights remain unverified",
    },
    {
        "source_id": "SRC-349",
        "source_name": "EriWengel — 2011 retyped Tigrigna Bible PDF",
        "url": "https://www.eriwengel.org/app/download/5789736450/Tigrigna_Bible.pdf",
        "inspection_and_limitations": "Inspected 2026-10-26. The 1,185-page PDF identifies itself as The Bible in Tigrigna, Old and New Testaments (2011), says it was retyped and reviewed by Christ for Eritrea International Ministry in South Carolina and Eritrean Philadelphia Church in Amsterdam, warns it may contain spelling errors or missing verses, and states ‘©copyright 2011’ and ‘Available publicly without restriction.’ That phrase is not a specific reuse license and conflicts with the separate Geʽez Experience rights page (SRC-049), which says the Bible Society of Eritrea owns the Tigrinya text, permits personal use, and asks users to obtain a license for other uses. This is a distinct digital witness lead; its printed exemplar, complete contents, translation basis, accuracy, and archive redistribution permission remain unverified. No text was copied.",
        "archive_status": "Distinct Tigrinya digital-witness lead; warning and rights ambiguity recorded; no text bundled pending edition, completeness, and reuse review",
    },
    {
        "source_id": "SRC-350",
        "source_name": "LEO-BW / SWB — Evangelia Sacra, Debtera Matheos (catalogue record)",
        "url": "https://www.leo-bw.de/en-GB/detail/-/Detail/details/DOKUMENT/bsz_swb/1177986159/Evangelia%20Sacra%20Domini%20Nostri%20et%20Salvatoris%20Jesu%20Christi%20sub%20auspiciis%20Caroli%20Guilielmi%20Isenberg%20%20in%20linguam%20Tigricam%20ve",
        "inspection_and_limitations": "Inspected 2026-10-26. The Baden-Württemberg state history portal's linked SWB catalogue record attributes the translation to Matteos, identifies Johann Ludwig Krapf as editor, gives 440 pages, and notes ‘In Ethiopian script, Tigrinya’; its subtitle is The Four Gospels of our Lord and Saviour Jesus Christ and it cites Darlow-Moule 9297. This is a bibliographic description, not inspection of the volume or its text. It does not establish detailed contents, textual completeness, translation basis, canon affiliation, or digital reproduction rights.",
        "archive_status": "Institutional union-catalogue metadata inspected; no scan or text copied; scope, contents, canon mapping, and reuse rights remain unaudited",
    },
    {
        "source_id": "SRC-351",
        "source_name": "St. Chrischona Theological Seminary Library — 1866 Evangelia Sacra catalogue item",
        "url": "https://bib.tsc.education/book.php?id=97195&rid=b90d9b773cee65e8a65d16b6166b710df192a2aa",
        "inspection_and_limitations": "Inspected 2026-10-26. The seminary library's item record dates Evangelia Sacra Domini Nostri Et Salvatoris Jesu Christi: In Linguam Tigricam to 1866, names Isenberg and Krapf, and identifies British and Foreign Bible Society and Spittler in its imprint fields. Its language field says Tigre, while LEO-BW's linked SWB record specifies Tigrinya; preserve the catalogue terminology and flag this historical naming discrepancy rather than silently normalizing it. A note appears to refer to the four Gospels and Acts, which differs from LEO-BW's Four Gospels subtitle and needs examination of the volume. The catalogue says the copy is an in-library-use item. No scan, contents, or rights statement for digitization/reuse was reviewed.",
        "archive_status": "Institutional holding and imprint metadata inspected; scan unavailable from this record; historical language label and scope discrepancy retained for review",
    },
    {
        "source_id": "SRC-352",
        "source_name": "University Library of Tübingen OpenDigi — 1866/67 catalogue entry citing Evangelia Sacra",
        "url": "https://opendigi.ub.uni-tuebingen.de/opendigi/LXV48_qt-G_NACHTR7_Ex1",
        "inspection_and_limitations": "Inspected 2026-10-26. This digitized page is a historical printed-library-catalogue supplement for 1866/67. Its OCR lists Evangelia sacra, translated into ‘linguam tigricam’ by Debtera Matheos and edited by J. L. Krapf, Basel 1866. The page explicitly identifies itself as a catalogue and has no OCR for the listed Gospel volume; it is not a digitized copy of the Tigrinya Gospels. The page's public-domain statement applies to this digitized catalogue object and is not evidence of a license for another book or scan.",
        "archive_status": "Digitized historical catalogue consulted as bibliographic corroboration only; no Gospel text or scan located in this item",
    },
    {
        "source_id": "SRC-353",
        "source_name": "Google Books — unverified digital-volume lead linked for the 1866 Tigrinya Gospels",
        "url": "https://books.google.com/books?id=_J5_Ze9BGN0C",
        "inspection_and_limitations": "The Tigrinya Scripture bibliography's 1866 entry links to this Google Books volume ID. Google Books page retrieval failed in the research interface and the Google Books metadata API returned HTTP 429 on 2026-10-26. The volume's title page, language, contents, digital-view status, source institution, and rights statement could not be inspected. The association with the 1866 Tigrinya edition is therefore an unverified locator lead based on the bibliography link, not a verified identification or permission to reuse. No text or scan was downloaded.",
        "archive_status": "Unverified digital-volume lead; identity, viewability, content, and rights unresolved; no text copied",
    },
    {
        "source_id": "SRC-354",
        "source_name": "Ethiopian Gospel Music — Tigrinya Bible texts bibliography (secondary discovery guide)",
        "url": "https://ethiopiangospelmusic.net/src/bible-tigrinya/",
        "inspection_and_limitations": "Inspected 2026-10-26. This specialist bibliography lists a 1909 Tigrinya New Testament titled Ḥaddiš kidan / Il Nuovo Testamento nella lingua tigrigna, published in Asmara for the British and Foreign Bible Society, and reports a Cambridge University Library holding. It relays translator/team and translation-basis details under a catalogue citation numbered 9299, but the underlying catalogue entry and Cambridge copy were not inspected. The page is a secondary discovery source, not a digital text, official rights statement, or proof of exact contents and reuse permission.",
        "archive_status": "Secondary bibliographic lead inspected; underlying catalogue entry and cited physical holding not verified; no text copied",
    },
    {
        "source_id": "SRC-355",
        "source_name": "GitHub — ethiopian-bibles repository, TIG24 XML rights and language metadata conflict",
        "url": "https://github.com/wuletawwonte/ethiopian-bibles",
        "inspection_and_limitations": "Inspected 2026-10-26. The repository README describes its translations as public domain and labels original/AmharicTigrinya2024Bible.xml as Language ‘Amharic’, Version ‘Amharic Tigrinya 2024’, License ‘Public Domain’. Its repository-level LICENSE is MIT and grants rights in the ‘Software’; it does not establish rights in scripture data. A limited HTTP range read of the XML header identifies the translation as ‘Amharic (Tigrigna: Contemporary Tigrinya Bible 2024)’, embeds a Bible.com link to version TIG24, and states ‘Copyright © 2024, by City Bible Foundation … Used with permission … All rights reserved worldwide.’ This materially contradicts the repository table’s Public Domain claim and links the file to the separately sampled TIG24 edition (SRC-088–SRC-089). Language metadata remains internally inconsistent: the table says Amharic, while the named Tigrinya edition and embedded TIG24 link identify a Tigrinya witness. The XML body and complete book/chapter inventory were not reviewed; no scripture text was copied. Treat the scripture as permission-limited and do not redistribute it without rights-holder authorization.",
        "archive_status": "XML header links the file to TIG24 and discloses all-rights-reserved text terms; repository Public Domain claim conflicts; no text copied pending rights-holder authorization",
        "rights_classification": "permission_limited",
        "rights_status": "The XML header identifies City Bible Foundation as copyright holder and states ‘Used with permission’ and ‘All rights reserved worldwide.’ That permission statement concerns the upstream distribution and does not grant reuse rights to this archive. The repository-level MIT license covers the ‘Software’ and is not a scripture-text license. Do not redistribute this text without authorization from the rights holder.",
    },
    {
        "source_id": "SRC-369",
        "source_name": "BibleFactory — Contemporary Tigrinya Bible 2024 product record (BBTI7000)",
        "url": "https://biblefactory.org/en/tigrinya-bible-softcover.html",
        "inspection_and_limitations": "Inspected 2026-10-26. BibleFactory identifies item BBTI7000 as the Tigrinya Contemporary Bible 2024, describes it as a complete Bible with Old and New Testaments, and lists a 720-page print product. The product record establishes the seller's bibliographic and scope claims only; its contents and full book list were not inspected. It does not establish an Eritrean/Ethiopian Orthodox canon crosswalk, exact textual completeness, or digital reproduction rights. See the separately inspected 7-page New Testament sample and its explicit 2024 all-rights-reserved colophon (SRC-370). No text copied.",
        "archive_status": "Product metadata inspected; seller describes Old and New Testaments; exact book list and canon mapping unverified; text not copied; no archive reuse permission established",
    },
    {
        "source_id": "SRC-370",
        "source_name": "BibleFactory / City Bible Foundation — Contemporary Tigrinya Bible 2024 New Testament sample PDF",
        "url": "https://biblefactory.org/media/wysiwyg/inkijkexemplaar/nt/Tigrinya_inkijk-exemplaar.pdf",
        "inspection_and_limitations": "Inspected 2026-10-26. The 7-page sample identifies the Contemporary Tigrinya Bible 2024 and labels the sample New Testament; its index lists the standard 27 New Testament titles. The colophon credits City Bible Foundation Netherlands, says the work is used by permission, and states ‘All rights reserved worldwide.’ This is evidence for the sampled edition's attribution, observed sample scope, and stated restriction—not permission for this archive to copy the text, a full contents inventory, or evidence of an Orthodox canon mapping. No scripture text copied.",
        "rights_classification": "all_rights_reserved",
        "rights_status": "The PDF colophon states © 2024 City Bible Foundation, used by permission, all rights reserved worldwide. That notice does not grant this archive permission to reproduce or redistribute the sample or full text; no scripture text is copied.",
        "archive_status": "7-page New Testament sample and colophon inspected; no text copied; explicit all-rights-reserved notice; no redistribution permission for this archive",
    },
    {
        "source_id": "SRC-371",
        "source_name": "Tigrigna Bible App — indexed description of a digital Tigrinya Bible service",
        "url": "https://tigrignabible.app/",
        "inspection_and_limitations": "Search-indexed site description inspected 2026-10-26; direct page retrieval returned a small HTML shell without the app's book list. The indexed description claims reading from scans and text, audio, search, and all 66 standard Bible books. This is a website-level claim, not a witnessed book-by-book inventory, edition identification, text review, rights grant, or Orthodox canon statement. It is not assumed to be the City Bible Foundation Contemporary Tigrinya Bible 2024 in SRC-369–SRC-370. No app text, audio, scan, or code copied.",
        "rights_classification": "unknown",
        "rights_status": "No copyright or reuse notice could be inspected because the live page returned only an HTML shell; the indexed service description is not a rights grant. Terms for the service's text, scans, and audio remain unknown. No content is copied.",
        "archive_status": "Indexed site-level claim only; edition, book list, content, and reuse terms not independently inspected; no text copied",
    },
    {
        "source_id": "SRC-407",
        "source_name": "Apple App Store — Tigrinya Bible app by Nippt",
        "url": "https://apps.apple.com/us/app/tigrinya-bible/id543960379",
        "inspection_and_limitations": "Inspected 2026-10-26. Apple's listing names developer Nippt and describes the app as containing all 66 Old and New Testament books in Tigrinya, an English KJV comparison, and offline reading. This is the seller's app description, not an independent inventory of the included texts, edition identification, or a claim about the Ethiopian/Eritrean Orthodox 81-entry list. The listing's © 2026 Nippt notice identifies app copyright only; it does not establish the rights holder or license for the underlying scripture text in Tigrinya. No text was copied.",
        "rights_classification": "unknown",
        "rights_status": "The App Store's © 2026 Nippt notice applies to the application listing/app and does not establish rights in its underlying scripture text. No text license or redistribution permission for the Bible text was located; no content is copied.",
        "archive_status": "App Store product and 66-book/offline claims inspected; underlying text edition, contents, Orthodox canon mapping, and reuse rights remain unverified",
    },
    {
        "source_id": "SRC-434",
        "source_name": "Eritrean Evangelical Church of Houston — 2011 Tigrigna Bible PDF copy",
        "url": "https://www.eechouston.org/wp-content/uploads/2014/10/TigrignaBible.pdf",
        "inspection_and_limitations": "Inspected 2026-10-27. The 1,185-page PDF title page identifies The Bible in Tigrigna, Old and New Testaments, dated December 2011. Its first-page notice says it was retyped and reviewed by Christ for Eritrea International Ministry and Eritrean Philadelphia Church, warns spelling errors or missing verses may remain, states ©copyright 2011, and says ‘Available publicly without restriction.’ This hosted PDF shares those visible title/date/contributor/rights statements with the separately catalogued EriWengel copy (SRC-349), but the files were not checksum-compared and are not asserted to be byte-identical or the same revision. The full book list, chapter and verse boundaries, printed exemplar, translation basis, and completeness were not audited. No scripture text was copied.",
        "rights_classification": "unknown",
        "rights_status": "The PDF states ©copyright 2011 and ‘Available publicly without restriction,’ but does not name a license or clarify what reuse is permitted. Its notice identifies the text as Bible Society of Eritrea content; the associated Geʽez Experience rights page (SRC-049) says personal use is permitted and other uses require a license. These notices have not been reconciled. Do not redistribute or bundle the text without permission from the relevant rights holder.",
        "archive_status": "External PDF inspected for title, page count, first-page attribution, warning, and rights wording; no text or scan copied; version identity and reuse rights remain unresolved",
    },
    {
        "source_id": "SRC-437",
        "source_name": "eBible.org — public scripture text index (bounded Tigrinya search)",
        "url": "https://ebible.org/study/content/texts/index.html",
        "inspection_and_limitations": "Inspected 2026-10-27. The live eBible.org text index was searched for the exact strings ‘Tigrinya’, ‘Tigrigna’, ‘TIR’, and ‘Eritrea’; none appears in the index text returned during this inspection. The index is a bounded catalogue of texts distributed by eBible.org, not a census of scripture translations or a country-language survey. This no-match result does not establish that an open Tigrinya text is unavailable elsewhere. eBible.org's About page says its freely redistributable files use acceptable sharing licenses or public-domain status; this is not a blanket license for third-party texts. No content was copied.",
        "local_review_url": "research/tigrinya-open-text-index-audit.md",
        "rights_classification": "unknown",
        "rights_status": "No scripture text was copied. This source is a provider index, not a license for any listed work. Reuse rights for Tigrinya editions discussed in the archive remain edition-specific and unresolved unless a record states otherwise.",
        "archive_status": "Bounded provider-index search recorded; no Tigrinya or Eritrea index match was found; no global absence or rights conclusion is inferred",
    },
    {
        "source_id": "SRC-438",
        "source_name": "Four Corners of the World Library — 2000 Eritrean Tigrinya deuterocanonical Bible catalogue record",
        "url": "https://fourcornersoftheworld.ptrs.ru.nl/publication/168/public/",
        "inspection_and_limitations": "Inspected 2026-10-27. The catalogue identifies a Tigrinya paperback titled Metshaf Kidus Kaliay Quenona Beluy Kidan Zihaze (English title supplied by the catalogue: The Revised Bible with Deuterocanonical Books in Tigrinya), published in Asmara in 2000 by the Bible Society of Eritrea, ISBN 978-9966-40-984-3 / CLDC062. It associates the item with the Eritrean Orthodox Tewahdo Church and says Orthodox Tewahdo, Catholic, and Evangelical/Lutheran churches participated, while only the Orthodox Tewahdo and Catholic churches participated in translation of the deuterocanonical books. This is a library catalogue record, not inspection of the volume; it does not establish the book list, exact contents, translation basis, textual accuracy, completeness, EOTC 81-entry mapping, or rights. Its metadata gives 286 pages without maps and 291 with maps. No text was copied.",
        "local_review_url": "research/tigrinya-eritrean-church-edition.md",
        "rights_classification": "unknown",
        "rights_status": "The inspected catalogue record identifies the publisher but provides no text reuse license. The Bible text is not bundled; obtain permission or verify a valid license before reproduction.",
        "archive_status": "Library catalogue discovery record; Tigrinya, Eritrean publisher, stated church participation, title, year, and ISBN recorded; no contents or reuse rights verified",
    },
    {
        "source_id": "SRC-439",
        "source_name": "Bible in My Language — Tigrinya CLDC062 retail listing (ISBN 9789966409843)",
        "url": "https://www.bibleinmylanguage.com/the-revised-bible-with-deuterocanonical-books-in-tigringna-ubs-cldc062-2010/",
        "inspection_and_limitations": "Inspected 2026-10-27. The bookseller listing describes The Revised Bible with Deuterocanonical Books in Tigringna, code CLDC062, publisher Bible Society, language Tigrinya, ISBN 978-9966-40-984-3, and date 2010. The ISBN matches the Four Corners of the World Library's record for a Bible Society of Eritrea publication dated 2000 (SRC-438). This is an unresolved date/source discrepancy; the seller page is not an inspected title page and does not prove a reprint, edition, or revised issue. It does not provide contents or an Orthodox canon mapping. No text was copied; the product listing supplies no reuse license.",
        "rights_classification": "unknown",
        "rights_status": "The retail listing names the Bible Society as publisher but supplies no text reproduction license. No text was copied; permission remains unverified.",
        "archive_status": "Retail bibliographic lead for ISBN 9789966409843; its 2010 date conflicts with a library record for the same ISBN dated 2000; edition relationship unresolved",
    },
    {
        "source_id": "SRC-440",
        "source_name": "Bible in My Language — Tigrinya CLDC032 retail listing (ISBN 9789966273840)",
        "url": "https://www.bibleinmylanguage.com/the-revised-bible-with-deuterocanonical-books-in-tigringna-ubs-cldc032-2010/",
        "inspection_and_limitations": "Inspected 2026-10-27. The bookseller listing uses a title similar to the CLDC062 listing, assigns code CLDC032 and ISBN 978-9966-27-384-0, and describes a 2010, 1,400-page vinyl-bound Tigrinya product from Bible Society. The vendor page does not include a contents list or independent proof that this is the same publication, a new edition, or a complete Bible. It is kept as a distinct product-catalogue lead because the code and ISBN differ; no EOTC or Eritrean Orthodox book mapping, textual completeness, or rights are established. No text was copied.",
        "rights_classification": "unknown",
        "rights_status": "The retail listing names Bible Society as publisher but supplies no text reproduction license. No text was copied; permission remains unverified.",
        "archive_status": "Separate seller product metadata with a different code and ISBN; edition identity, contents, canon scope, and reuse rights unverified",
    },
]

EDITION_LEADS = [
    {
        "edition_id": "tigrinya-eritrea-revised-deuterocanon-2000",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "Metshaf Kidus Kaliay Quenona Beluy Kidan Zihaze (2000) — Eritrean Tigrinya deuterocanonical Bible catalogue record",
        "witness_type": "printed_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "Four Corners of the World Library catalogue identifies a 2000 Asmara edition published by the Bible Society of Eritrea, ISBN 978-9966-40-984-3 / CLDC062, with a title translated there as The Revised Bible with Deuterocanonical Books in Tigrinya. A bookseller lists the same ISBN/code as a 2010 product; the date discrepancy is unresolved.",
        "scope_description": "The library catalogue associates this edition with the Eritrean Orthodox Tewahdo Church and reports participation by Orthodox Tewahdo, Catholic, and Evangelical/Lutheran churches; it says only Orthodox Tewahdo and Catholic churches participated in translating the deuterocanonical books. The physical volume and its contents were not inspected. The catalogue gives 286 pages without maps and 291 with maps, while a separate seller listing for the ISBN supplies no page count and dates it 2010. The catalogue does not supply a complete book list, translation basis, textual accuracy, completeness, or an EOTC 81-entry crosswalk. This lead does not establish that the edition matches any other Tigrinya Bible record.",
        "source_ids": ["SRC-438", "SRC-439"],
        "text_bundled": False,
        "rights_status": "The catalogue names the Bible Society of Eritrea as publisher but provides no text reuse license. Do not reproduce or bundle the text without permission or a verified license.",
        "rights_classification": "unknown",
        "review_status": "The library catalogue and secondary retail metadata were inspected 2026-10-27. The 2000 vs 2010 publication date for the shared ISBN is unresolved. The printed book, contents, translation basis, completeness, textual accuracy, and rights were not inspected or verified.",
    },
    {
        "edition_id": "tigrinya-eritrea-cldc032-retail-2010",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "Tigrinya CLDC032 (ISBN 9789966273840) — 2010 retail product lead",
        "witness_type": "printed_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "A bookseller describes a 2010 Bible Society Tigrinya product, code CLDC032, ISBN 978-9966-27-384-0, and 1,400 pages under a title similar to the CLDC062 product.",
        "scope_description": "This is retailer-supplied metadata only. The physical product and its table of contents were not inspected. The page count and title do not establish a complete book list, deuterocanonical contents, translation identity, Orthodox canon mapping, or relationship to the separate CLDC062 ISBN/product. This is not bundled text.",
        "source_ids": ["SRC-440"],
        "text_bundled": False,
        "rights_status": "The seller listing supplies no text reuse license. The text is not bundled; permission remains unverified.",
        "rights_classification": "unknown",
        "review_status": "Secondary seller metadata inspected 2026-10-27. The physical book, contents, exact edition, translation basis, completeness, textual accuracy, and rights were not verified.",
    },
    {
        "edition_id": "tigrinya-eritrea-genesis-portion-dbs-1998",
        "candidate_canon_id": "eotc-ot-01",
        "mapping_state": "uncertain",
        "title": "Tigrigna (1998) Genesis Portion — Bible Society of Eritrea (DBS catalogue lead)",
        "witness_type": "digital_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "Digital Bible Society's Tigrinya Common Language Bible profile lists a 1998 Genesis Portion attributed to the Bible Society of Eritrea.",
        "scope_description": "Catalogue-only lead for a named Genesis portion. The text file was not obtained or inspected; extent, translation identity, chapter/verse boundaries, and relationship to the separate Tigrinya Common Language Bible PDF are unknown. The candidate is a navigation aid, not proof of a complete Genesis text or an Ethiopian Orthodox Church edition.",
        "source_ids": ["SRC-331"],
        "text_bundled": False,
        "rights_status": "Reuse terms for this specific 1998 Genesis portion are not stated on the inspected catalogue page. Do not redistribute or bundle until the rights holder's terms are established.",
        "rights_classification": "unknown",
        "review_status": "The provider's Tigrinya profile and its catalogued title/attribution were inspected 2026-10-25. Text, extent, translation basis, rights, and any EOTC crosswalk remain unverified.",
    },
    {
        "edition_id": "tigrinya-common-language-bible-dbs-pdf-tirtbi",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "Tigrinya Common Language Bible — Digital Bible Society PDF (TIRTBI; observed New Testament contents)",
        "witness_type": "digital_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "Digital Bible Society PDF titled Tigrinya Common Language Bible; PDF metadata gives 1991 and Bible Society of Ethiopia. The visible contents list the 27 standard New Testament titles.",
        "scope_description": "The generated PDF metadata describes a full Bible completed in 1991, while the 133-page PDF's contents list only the 27 New Testament books. The archive preserves this discrepancy and describes the observed file scope without resolving whether an Old Testament portion is omitted, hosted separately, or represented elsewhere. No EOTC crosswalk, chapter-boundary audit, or textual accuracy review is claimed.",
        "source_ids": ["SRC-331", "SRC-332"],
        "text_bundled": False,
        "rights_status": "The PDF states copyright © Bible Society of Ethiopia and describes Digital Bible Society's noncommercial distribution. No separate license or permission for this archive to reproduce the complete text was located.",
        "rights_classification": "permission_limited",
        "review_status": "Provider page and PDF title/metadata and visible contents were inspected 2026-10-25. PDF text was not extracted; only the contents and rights/scope metadata were reviewed. Completeness, chapter boundaries, translation basis, and wording remain unaudited.",
    },
    {
        "edition_id": "tigrinya-revised-bible-eritrea-1998",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "Revised Bible in Tigrigna (1998) — Bible Society of Eritrea (whole-Bible product records)",
        "witness_type": "printed_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "Two Bible-society/distributor product records identify a Tigrinya Bible published by the Bible Society of Eritrea; one calls it the Revised Bible in Tigrigna (1998) and lists a 1,140-page second edition. Bible Society records ISBN 9783438081964.",
        "scope_description": "Bibliographic lead for a print edition described by the sellers as a whole Bible or full-text Bible. Neither product record was used to inspect the contents, book list, textual extent, chapter divisions, or translation wording. The record does not infer an Ethiopian or Eritrean Orthodox canon, an 81-book mapping, or identity with the separate 1991 Tigrinya Common Language Bible.",
        "source_ids": ["SRC-333", "SRC-334"],
        "text_bundled": False,
        "rights_status": "The inspected product pages do not grant permission to reproduce or redistribute a digital text. Treat text rights as unknown and do not bundle text unless the rights holder provides terms.",
        "rights_classification": "unknown",
        "review_status": "Retail metadata was inspected 2026-10-25. No copy of the printed edition or digital text was inspected. Contents, canon scope, completeness, accuracy, and reuse rights remain unverified.",
    },
    {
        "edition_id": "tigrinya-bible-eriwengel-retyped-2011",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "The Bible in Tigrigna — EriWengel 2011 retyped PDF",
        "witness_type": "digital_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "Two publicly accessible PDF URLs (EriWengel, SRC-349; Eritrean Evangelical Church of Houston, SRC-434) serve 1,185-page files titled The Bible in Tigrigna, Old and New Testaments, dated 2011. Their front matter credits retyping and review to Christ for Eritrea International Ministry and Eritrean Philadelphia Church; byte identity and revision identity have not been checked.",
        "scope_description": "The PDF's cover identifies it as Old and New Testaments, but this archive has not inventoried its book list, chapter sequence, verse labels, or relation to a printed edition. Its own notice warns spelling errors or missing verses may remain. It is distinct from the 1991 Tigrinya Common Language Bible PDF and the 1998 Bible Society of Eritrea printed-edition lead; no canon mapping is asserted.",
        "source_ids": ["SRC-349", "SRC-434", "SRC-049"],
        "text_bundled": False,
        "rights_status": "The PDF states ©copyright 2011 and ‘Available publicly without restriction,’ but supplies no named open license or clear permission to redistribute the text. SRC-049 separately reports the Bible Society of Eritrea's text ownership, personal-use permission, and licensing requirement for other uses. These statements are not reconciled; rights remain unknown. Do not bundle without permission from the relevant rights holder.",
        "rights_classification": "unknown",
        "review_status": "The EriWengel and EEC Houston PDFs were inspected for their title, page count, date, contributor/error notice, and rights wording (2026-10-26 and 2026-10-27). Their visible metadata matches, but byte identity and revision identity were not checked. Full table of contents, chapter/verse boundaries, translation basis, text accuracy, printed exemplar, completeness, canon crosswalk, and reuse authorization remain unaudited.",
    },
    {
        "edition_id": "tigrinya-four-gospels-matteos-isenberg-1866",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "Evangelia Sacra — Tigrinya Four Gospels edition (Debtera Matteos; 1866 catalogue record)",
        "witness_type": "printed_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "LEO-BW/SWB identifies Debtera Matteos as translator, Johann Ludwig Krapf as editor, a 440-page volume, and Tigrinya in Ethiopic script (the title uses the historical form ‘Tigricam’). Its subtitle is The Four Gospels of our Lord and Saviour Jesus Christ. St. Chrischona Theological Seminary Library dates its catalogue item to 1866 and records British and Foreign Bible Society and Spittler in the imprint fields; its language field says ‘Tigre.’",
        "scope_description": "This is a metadata-only lead for a printed historical witness, not a transcribed reader. LEO-BW describes the work as the Four Gospels; a St. Chrischona catalogue note appears to mention the four Gospels and Acts, so Acts inclusion and actual book order require inspection of the volume. No chapter or verse boundaries, completeness, translation basis, relationship to modern Tigrinya editions, or Ethiopian/Eritrean Orthodox canon crosswalk is asserted.",
        "source_ids": ["SRC-350", "SRC-351", "SRC-352", "SRC-353"],
        "text_bundled": False,
        "rights_status": "The catalogue records describe a 1866 print edition but provide no digitization or text-reuse license. No scan was used and no text was copied. Rights for any digital surrogate and the applicable jurisdiction remain unreviewed; do not redistribute a scan until its holding institution's terms and applicable rights are checked.",
        "rights_classification": "unknown",
        "review_status": "Three institutional catalogue objects and one bibliography-linked Google Books locator inspected 2026-10-26. Publication year, attribution, page count, language/script identification, and conflicting catalogue scope notes are recorded. The Tübingen digital item is a catalogue page, not the Gospel volume. Google Books volume identity, viewability, and contents could not be checked; no verified Gospel scan or text was located. Physical-copy contents, chapter boundaries, accuracy, canon relation, and digital-surrogate rights remain unreviewed.",
    },
    {
        "edition_id": "tigrinya-new-testament-winqvist-bfbs-1909",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "Ḥaddiš kidan / Il Nuovo Testamento nella lingua tigrigna (1909) — bibliographic lead",
        "witness_type": "printed_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "A secondary Tigrinya-scripture bibliography describes a 1909 New Testament edition published in Asmara for the British and Foreign Bible Society and reports a Cambridge University Library holding. It attributes the translation to Karl Winqvist with named Tigrinya collaborators and says it was translated from Greek with reference to several other versions; these details are relayed under catalogue citation 9299 and have not yet been checked against that catalogue entry or a copy.",
        "scope_description": "The secondary bibliography identifies this as a New Testament, but the archive has not inspected the Cambridge holding or an edition copy. Its exact book list, sequence, chapter/verse divisions, textual basis, edition variants, completeness, and relationship to an EOTC or Eritrean Orthodox canon remain unverified. This is a discovery record only and is not counted as a bundled reader or a canon crosswalk.",
        "source_ids": ["SRC-354"],
        "text_bundled": False,
        "rights_status": "The secondary bibliography provides no text-reuse license, and the reported library holding does not establish permission to reproduce the book or its scan. Rights for any digitized surrogate remain unreviewed; do not bundle or redistribute until the holding institution and applicable rights terms are checked.",
        "rights_classification": "unknown",
        "review_status": "One secondary bibliographic page inspected 2026-10-26. Its edition title, date, place, stated publisher, reported holding, and translation-history claim are recorded as leads only. The primary catalogue entry, physical copy, scan, contents, boundaries, accuracy, canon relation, and reuse rights were not checked.",
    },
    {
        "edition_id": "tigrinya-contemporary-bible-city-bible-2024",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "Tigrinya Contemporary Bible 2024 — City Bible Foundation (product record and NT sample)",
        "witness_type": "digital_edition",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "BibleFactory item BBTI7000 identifies the Tigrinya Contemporary Bible 2024 as a 720-page product containing Old and New Testaments. A separate seven-page sample PDF is labeled as a New Testament sample and carries a City Bible Foundation 2024 all-rights-reserved colophon.",
        "scope_description": "The publisher/distributor product record describes an Old and New Testament edition, but its book list and pages were not inspected. The separate sample's index lists the standard 27 New Testament titles; that index is not a full collation or proof of the complete edition's extent. This translation is a language resource lead only: no Ethiopian or Eritrean Orthodox canon crosswalk, exact 81-entry mapping, completeness, or accuracy is asserted. No text is bundled.",
        "source_ids": ["SRC-369", "SRC-370"],
        "text_bundled": False,
        "rights_status": "The sample colophon says ©2024 City Bible Foundation, used by permission, all rights reserved worldwide. That notice does not grant this archive permission to copy or redistribute the text. Do not bundle the text without a direct reuse license from the rights holder.",
        "rights_classification": "all_rights_reserved",
        "review_status": "Product metadata and all seven pages of the New Testament sample were inspected 2026-10-26 for title, stated scope, sample contents, and rights notice. The complete product's contents, chapter boundaries, translation basis, contributor list, accuracy, completeness, community review, canon relationship, and archive reuse permission remain unverified.",
    },
    {
        "edition_id": "tigrinya-app-66-book-site-claim",
        "candidate_canon_id": None,
        "mapping_state": "not_mapped",
        "title": "Tigrinya Bible App — Apple listing and site-level 66-book claims",
        "witness_type": "digital_service",
        "language_tag": "ti",
        "language_name": "Tigrinya (ትግርኛ)",
        "script_code": "Ethi",
        "edition_statement": "The Apple App Store listing describes the Nippt Tigrinya Bible app as containing all 66 Old and New Testament books, English KJV comparison, and offline reading. The separate TigrignaBible.app site advertises scanned and text reading, audio, and search; direct retrieval exposes only its HTML shell.",
        "scope_description": "These are vendor/site claims, not an independent book inventory; direct retrieval of the website returns only an HTML shell. The underlying Bible edition, publisher, translation basis, exact contents, book boundaries, accuracy, and source-text rights remain unidentified. The claimed 66-book package is not equated with the Ethiopian/Eritrean Orthodox 81-entry list and is not identified with the separate City Bible Foundation 2024 product. No app content or text is bundled.",
        "source_ids": ["SRC-371", "SRC-407"],
        "text_bundled": False,
        "rights_status": "Apple's © 2026 Nippt notice covers the application, not necessarily the underlying Bible text. No text license or redistribution permission was located; rights for text, scans, and audio remain unknown. No content is copied.",
        "rights_classification": "unknown",
        "review_status": "Apple's product listing was inspected 2026-10-26 and direct website retrieval returned an HTML shell. The 66-book and offline claims are not independently verified; live book inventory, exact edition, text accuracy, completeness, translation basis, and underlying-text rights remain unknown.",
    },
]


def apply(archive: dict) -> None:
    sources = {item["source_id"]: item for item in archive.get("sources", [])}
    sources.update({item["source_id"]: item for item in SOURCES})
    archive["sources"] = list(sources.values())
    registry = archive.setdefault("translation_registry", {})
    managed_ids = {item["edition_id"] for item in EDITION_LEADS}
    leads = [item for item in registry.get("edition_leads", []) if item.get("edition_id") not in managed_ids]
    registry["edition_leads"] = sorted(leads + deepcopy(EDITION_LEADS), key=lambda item: item["edition_id"])
    profile = next((item for item in registry.get("languages", []) if item.get("language_tag") == "ti"), None)
    if profile is None:
        raise ValueError("Tigrinya language profile is required before recording its edition leads")
    profile["source_ids"] = sorted(set(profile.get("source_ids", [])) | {item["source_id"] for item in SOURCES}, key=lambda value: int(value.split("-")[1]))
    survey_source_ids = profile["availability_survey"].get("source_ids", [])
    profile["availability_survey"]["source_ids"] = sorted(
        set(survey_source_ids) | {"SRC-437", "SRC-438", "SRC-439", "SRC-440"}, key=lambda value: int(value.split("-")[1])
    )
    note = (
        " A separate Digital Bible Society Tigrinya profile lists a 1998 Genesis portion attributed to the Bible Society of Eritrea. "
        "Its separate 133-page Tigrinya Common Language Bible PDF identifies Bible Society of Ethiopia copyright and displays a contents list "
        "of the 27 standard New Testament books, although the generated PDF metadata describes a full Bible. These items are not assumed to be "
        "the same edition, and the PDF is not counted in the survey's two Bible.com edition result; no text is bundled because reuse permission "
        "and complete scope are not established. Separate Bible Society and distributor product records identify a 1998 revised "
        "Tigrigna whole-Bible print edition from the Bible Society of Eritrea; its book list, canon scope, text, and digital reuse "
        "rights have not been inspected, so it remains metadata-only and is not treated as an EOTC crosswalk. Two separately hosted 2011 Tigrigna PDFs have matching visible title, date, contributor, and rights wording, but were not byte-compared; their ‘available publicly without restriction’ wording does not resolve reuse rights because the PDFs are ©2011 and the associated text-owner page says other uses require a license. An 1866 catalogue-described Tigrinya four-Gospel print edition by Debtera Matteos is now listed as a separate historical witness. Its catalogue labels differ on whether Acts is included. A secondary bibliography links a Google Books volume as a possible digitized witness, but the link's identity and viewability could not be confirmed; no scan or reusable text has been verified. The same bibliography reports a separate 1909 Tigrinya New Testament at Cambridge, with translator and translation-basis details that await primary-catalogue collation. The digitized Tübingen page is a 19th-century catalogue, not the Gospel volume, and its rights label does not apply to that book. See SRC-331–SRC-334, SRC-349–SRC-354, SRC-434, and SRC-049."
    )
    survey_notes = profile["availability_survey"].get("notes", "")
    survey_notes = survey_notes.replace(note + note, note)
    if "A separate Digital Bible Society Tigrinya profile lists a 1998 Genesis portion" not in survey_notes:
        survey_notes += note
    old_github_note = (
        " A public GitHub scripture-data repository claims Public Domain for a file named AmharicTigrinya2024Bible.xml, but its table calls the file's language Amharic and the repository license file is an MIT software license; the scripture file contents and upstream rights were not established. Bible.com lists a separately named TIG24 2024 Tigrinya version whose sampled copyright page names City Bible Foundation and says all rights reserved. Their similar year/title fragments do not establish the files are the same translation. Keep this repository item unclassified pending inspection of its actual contents and rights chain (SRC-355, SRC-088–SRC-089)."
    )
    github_note = (
        " The GitHub repository's XML header for AmharicTigrinya2024Bible.xml was inspected by a limited byte-range read. It identifies ‘Amharic (Tigrigna: Contemporary Tigrinya Bible 2024)’, embeds a Bible.com TIG24 link, and states ©2024 City Bible Foundation, used with permission, all rights reserved worldwide. This links the file to the sampled TIG24 edition (SRC-088–SRC-089) and conflicts with the repository README's Public Domain label; the separate MIT license covers software, not the scripture text. The repository table and XML translation label conflict on language, and the full file's contents and book/chapter inventory have not been audited. No text is copied; rights classification is permission-limited pending authorization, with no EOTC or Eritrean Orthodox crosswalk asserted (SRC-355)."
    )
    survey_notes = survey_notes.replace(old_github_note, github_note)
    if "The GitHub repository's XML header for AmharicTigrinya2024Bible.xml was inspected by a limited byte-range read" not in survey_notes:
        survey_notes += github_note
    contemporary_note = (
        " A separate BibleFactory listing describes the Tigrinya Contemporary Bible 2024 (BBTI7000) as a 720-page Old and New Testament product. Its seven-page New Testament sample identifies City Bible Foundation and says ‘All rights reserved worldwide’; this does not grant redistribution permission. The book list and contents of the complete product were not inspected, and no Orthodox canon crosswalk is asserted. A Tigrinya Bible app's indexed website and Apple App Store listing separately claim text/scan/audio/search features and all 66 standard books, with the App Store also claiming offline reading. Direct website retrieval exposed only an HTML shell; the app's actual contents, translation identity, and underlying-text rights remain unverified. Apple’s © 2026 Nippt notice is for the application, not an established scripture-text license. This app lead is not conflated with BBTI7000 and adds no reader text or canon coverage. See SRC-369–SRC-371 and SRC-407."
    )
    if "A separate BibleFactory listing describes the Tigrinya Contemporary Bible 2024" not in survey_notes:
        survey_notes += contemporary_note
    ebible_note = (
        " A bounded inspection of eBible.org's public scripture text index on 2026-10-27 found no exact ‘Tigrinya’, ‘Tigrigna’, ‘TIR’, or ‘Eritrea’ match in the returned index text. This describes only that provider index at inspection time; it is not evidence that open Tigrinya scripture is unavailable elsewhere, nor a complete search of its related links. No text was copied. The separate About page describes eBible.org's own redistributable materials and does not grant rights in third-party translations (SRC-437)."
    )
    if "A bounded inspection of eBible.org's public scripture text index" not in survey_notes:
        survey_notes += ebible_note
    eritrean_edition_note = (
        " A Four Corners of the World Library catalogue describes a 2000 Tigrinya Bible Society of Eritrea edition with deuterocanonical books, associates it with the Eritrean Orthodox Tewahdo Church, and reports cross-church participation. A seller lists the same CLDC062 ISBN as a 2010 product, while the library record says 2000; no title page was seen to resolve the difference. The seller also lists a similar-titled CLDC032 product with a different ISBN and a claimed 1,400 pages; its contents and relation to CLDC062 are unverified. These remain distinct/unresolved bibliographic leads; no complete book list, translation basis, EOTC 81-entry mapping, or reuse rights is established (SRC-438–SRC-440)."
    )
    if "A Four Corners of the World Library catalogue describes a 2000 Tigrinya" not in survey_notes:
        survey_notes += eritrean_edition_note
    profile["availability_survey"]["notes"] = survey_notes
    audit_path = Path(__file__).resolve().parent / "research" / "tigrinya-open-text-index-audit.md"
    audit_path.write_text(
        "# Tigrinya open-text index check\n\n"
        "**Inspected:** 2026-10-27  \n"
        "**Index:** [eBible.org public text index](https://ebible.org/study/content/texts/index.html)\n\n"
        "The index was searched for the exact strings `Tigrinya`, `Tigrigna`, `TIR`, and `Eritrea`. None appeared in the index text returned during this inspection. The live index includes many language-grouped scripture entries and links to provider editions; it is not a census of scripture availability. This bounded no-match result does not establish that an open Tigrinya text is unavailable elsewhere or that no linked page uses a different language name or code.\n\n"
        "The [eBible.org About page](https://ebible.org/about.php) describes acceptable licenses for texts distributed as freely redistributable. That policy is not a blanket license for works hosted by other providers. Existing Tigrinya edition records retain their own copyright and permission notes. No scripture text was copied, no rights status was changed, and no reader or canon-coverage count was added.\n\n"
        "Archive source record: `SRC-437`. This record documents a provider-index check, not a completed survey of Tigrinya scripture sources.\n",
        encoding="utf-8",
    )
    edition_audit_path = Path(__file__).resolve().parent / "research" / "tigrinya-eritrean-church-edition.md"
    edition_audit_path.write_text(
        "# Eritrean Tigrinya deuterocanonical Bible catalogue record\n\n"
        "**Inspected:** 2026-10-27  \n"
        "**Catalogue:** [Four Corners of the World Library, publication 168](https://fourcornersoftheworld.ptrs.ru.nl/publication/168/public/)\n\n"
        "The catalogue gives the title *Metshaf Kidus Kaliay Quenona Beluy Kidan Zihaze*, supplies the English rendering ‘The Revised Bible with Deuterocanonical Books in Tigrinya,’ and identifies Bible Society of Eritrea, Asmara, 2000, ISBN 978-9966-40-984-3 / CLDC062. It associates the item with the Eritrean Orthodox Tewahdo Church and reports that Orthodox Tewahdo, Catholic, and Evangelical/Lutheran churches participated in the edition; for translating the deuterocanonical books, it says only Orthodox Tewahdo and Catholic participants took part. The record lists 286 pages without maps and 291 with maps.\n\n"
        "A bookseller page identifies a product with the same ISBN and CLDC062 code as a 2010 item. This conflicts with the library catalogue's 2000 date; no physical title page has been inspected to resolve the difference. Another seller page lists a similar-titled 2010 CLDC032 item with a different ISBN (978-9966-27-384-0) and claims 1,400 pages. That description is not verified against a physical volume and does not establish that CLDC032 and CLDC062 are the same edition or which books either contains.\n\n"
        "These are catalogue/seller statements, not direct inspection of printed volumes. No contents list or scripture text was obtained. The archive has not established the book-by-book contents, translation basis, accuracy, completeness, equivalence to another Tigrinya Bible, or a crosswalk to the Ethiopian Church's 81 listed entries. No reuse license was found; rights remain unknown and neither text is bundled.\n\n"
        "These records add bibliographic leads only. They do not increase reader or canon-coverage counts. Archive source records: `SRC-438`, `SRC-439`, and `SRC-440`.\n",
        encoding="utf-8",
    )
