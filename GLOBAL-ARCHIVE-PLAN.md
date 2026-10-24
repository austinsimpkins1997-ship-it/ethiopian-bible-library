# Global Scripture Archive: scope and data design

## Purpose

Build a durable, multilingual, openly documented *catalogue and reader platform* for scriptures and related textual traditions, beginning with the Ethiopian Orthodox Tewahedo collection already documented here. The software can be open source. Each text, translation, image, recording, and scholarly apparatus must carry its own rights and provenance; an open software license does not make every source text open.

This document is a design and work plan, not a claim that a worldwide corpus or database already exists. The current GitHub Pages site is a static prototype with a small, locally embedded dataset. It cannot accept contributions or function as a shared writeable database by itself.

## Scope and limits

- “All knowledge” is not a bounded or verifiable corpus. This project should archive identified works and evidence, not claim to contain all human knowledge.
- “Scripture” is tradition-specific. The archive must preserve each community’s own canon, ordering, titles, grouping, language, and edition. It must not flatten them into one universal canon or treat one tradition’s classification as another’s.
- No translation is perfectly equivalent in every context. Translation records must preserve the source edition, translation path (including relay languages), translator or tool, interpretive choices, uncertainty, and review history. Parallel wording is not proof of identical meaning.
- Unknown provenance, completeness, language, date, rights, or alignment stays marked unknown. No missing passages are silently supplied or machine-generated into a source text.
- Language coverage is a measured inventory, never “every language” by default. Use BCP 47 tags and the IANA registry; use script subtags only where justified. Script labels follow ISO 15924. Preserve local names and orthographies alongside identifiers.
- The archive is for research and access, not an official religious authority, substitute for a community edition, or arbiter of theological truth.

## Record model

The long-term store should separate entities that are often incorrectly collapsed into a single “book” row:

1. **Tradition and canon** — community/tradition, named canon list, source for that list, ordering, sections, and the exact title/grouping as printed. Crosswalks between lists are explicit, attributed assertions with a confidence/review state; they are not identity.
2. **Work** — an abstract work identity within a named scholarly/community framework. Do not merge works solely because titles look alike.
3. **Witness and edition** — manuscript, printed edition, or digital witness; shelfmark/edition statement, date, repository, source URL or local capture, checksum, and any known editorial policy.
4. **Text layer** — exact transcription, diplomatic transcription, normalized text, transliteration, translation, paraphrase, or commentary. Each layer has its own language/script, agent, basis, rights, and review status.
5. **Structure and alignment** — source-defined divisions and labels retained as given. Verse/chapter mappings between editions are separate, many-to-many assertions with a method and evidence. Never align by label alone and imply equivalence.
6. **Evidence and review** — sources support specific claims. Record who checked what, against which witness, when, and what remains unchecked. A review status applies to a scope (e.g. chapter sequence or OCR sample), not vaguely to an entire book.
7. **Rights and access** — rights holder/notice, license identifier and version, attribution, restrictions, territory or uncertainty, and permitted distribution format. Keep copyrighted/non-redistributable records discoverable as metadata while excluding their text from the downloadable corpus where lawful and appropriate.
8. **Community stewardship** — preferred names, contributor consent, culturally sensitive access rules, correction pathway, and contact/governance details when supplied by the relevant community. Public access is not presumed for restricted or sacred materials.

Suggested stable identifiers are opaque and permanent (for example `work:...`, `witness:...`, `layer:...`, `unit:...`). Human titles, language names, and canon labels remain editable metadata, not keys. Every release has a version and checksum manifest so mirrors can reproduce it.

## Translation and review policy

Translation is represented as a chain of language-tagged text layers, not a single source/target field. For example, a translation from Greek into English has path `grc → en`; an edition mediated through another language records every known step. Unknown basis is `null`, not guessed. Machine translation may help create a *draft* only; it must never be labeled an exact, verified, or authoritative translation without qualified human review. Reviewer names/roles, language competence, passages checked, changes, unresolved alternatives, and date are recorded. Where interpretation is disputed, preserve the alternatives and cite their advocates instead of manufacturing consensus.

Language identification follows IETF BCP 47 and its IANA Language Subtag Registry. Script codes use ISO 15924. The W3C Web Annotation model is a suitable interoperability reference for notes attached to text fragments; it does not supply scripture or validate interpretation. These standards identify and connect data; they do not establish textual truth or translation quality.

## Distribution architecture

Keep the current static site as a low-bandwidth, offline reader and catalogue. It can display reviewed, rights-cleared bundles and link to provenance. A genuinely global, collaborative corpus needs a separate service for submissions, moderation, authentication, version history, search/indexing, and storage; GitHub Pages alone cannot provide those functions. Design exports so the same release can be mirrored and read without that service. Publish small, independently versioned packages by tradition/language rather than requiring one enormous download. The site should continue to make zero runtime data requests for any locally bundled text.

Do not select a production database or promise “worldwide” hosting until volume, governance, moderation, preservation, and funding requirements are known. The initial deliverable is portable data and explicit admission rules; service selection is a later engineering decision.

## Phased work

### Phase 1 — trustworthy seed (current)

- Complete source-backed catalogue for the EOTC list and clearly separated related material.
- Admit texts only with identified edition/witness, source boundaries, provenance, license assessment, and stated review scope.
- Continue reviewing the currently bundled texts and their rights, source boundaries, and structural checks book by book. Add other works only after the admission checklist is met; do not infer text availability from a canon entry.
- Improve the reader’s way to show bundled vs. unbundled entries, editions, translation basis, and unresolved mappings.

### Phase 2 — portable multilingual corpus

- Build on the v1 text-layer schema and the 12 metadata records now included for the bundled layers: 11 Geʽez readers plus Brenton's Greek-to-English Genesis companion under `site/schemas/` and `site/examples/`. Expand to separate canon, work, witness, structure, alignment, citation, rights, and review-event records before calling the corpus model complete.
- Add import/export paths for established scripture formats after checking their current specifications and preserving source-specific detail.
- Invite qualified readers and source communities to review specific bounded tasks; publish corrections and dissent with attribution/consent.

### Phase 3 — federated public service

- Add moderated contribution and review workflows, language-aware search, accessible interface/localization, downloadable packages, mirrors, and archival backups.
- Measure coverage per tradition, language/script, edition, book, and review dimension. Show gaps publicly.
- Establish governance, consent, privacy, security, funding, service ownership, and response commitments before opening submissions at scale.

## Admission checklist

A text layer is not marked `verified` merely because a source was found. Before reader inclusion, record: (1) what tradition/work it claims to represent; (2) exact witness/edition; (3) source and local checksum; (4) language/script and text layer type; (5) observed structure and coverage, including lacunae/editorial supplements; (6) transcription/translation method and every known basis language; (7) citation and reuse rights for that layer; (8) checks performed and reviewer scope; and (9) known disagreements or unresolved questions. Reader UI must show these distinctions plainly.

## Current project status

The repository currently contains a static EOTC-focused prototype with 89 searchable catalogue rows, 70 source records, the Church-list coverage index (81 entries: 46 Old Testament and 35 New Testament), 11 locally stored Geʽez reader records (Genesis–Ruth, Psalms, Jubilees, and 1 Enoch), and a separate historical English Genesis companion derived from Greek. Eleven Church-list entries have bundled reader text; this is not a claim that all mapped editions are official, critically verified, or textually complete. The translation registry has 12 language profiles (Geʽez, English, and ten scoped Eritrean profiles, including Dahalik with script and scripture witness unestablished) and records both bundled and unbundled material. The draft v1 text-layer schema has 12 corresponding metadata records. The site can work as a locally stored static reader; it is not a writable global database. It does **not** contain all 81 texts, all world scriptures, translations into every language, or a global knowledge database. Phase 1 remains in progress: the current inventory and checks do not replace qualified textual review, full rights clearance for every future use, or community review.

## Standards and related infrastructure

- IETF [BCP 47](https://datatracker.ietf.org/doc/bcp47/) / [RFC 5646](https://datatracker.ietf.org/doc/rfc5646/) and the [IANA Language Subtag Registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry).
- ISO [ISO 15924:2022](https://www.iso.org/standard/81905.html) for script codes.
- W3C [Web Annotation Data Model](https://www.w3.org/TR/annotation-model/) for interoperable annotations on specific text segments.
- Existing open scripture projects and text collections may be evaluated as *sources or format references*, one dataset at a time. Their software license does not automatically license the underlying texts. No third-party corpus is adopted by this plan.

