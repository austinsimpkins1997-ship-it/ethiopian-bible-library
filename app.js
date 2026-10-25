const state = { archiveData: null, books: [], sources: [], related: [], readers: [], canonBooks: [], canonContextSourceIds: [], translationRegistry: null, query: '', filter: 'All', selected: null, chapter: 1, readerId: null };
const byId = (id) => document.getElementById(id);
const escapeHTML = (value = '') => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeURL = (value) => {
  if (typeof value !== 'string') return '#';
  if (value.startsWith('#')) return value;
  try {
    const base = new URL(window.location.href);
    const url = new URL(value, base);
    const localPath = !/^[a-z][a-z0-9+.-]*:/i.test(value) && !value.startsWith('//') && !value.split(/[?#]/)[0].split('/').includes('..');
    if (url.protocol === 'https:' && (url.origin === base.origin || /^[a-z][a-z0-9+.-]*:/i.test(value))) return url.href;
    if (base.protocol === 'file:' && url.protocol === 'file:' && localPath) return url.href;
    return '#';
  } catch { return '#'; }
};
const listedHost = (value) => {
  try {
    const url = new URL(safeURL(value), window.location.href);
    return ['https:', 'http:'].includes(url.protocol) && url.origin !== window.location.origin ? url.host : '';
  } catch { return ''; }
};
const hostHint = (value) => {
  const host = listedHost(value);
  return host ? ` <span class="source-host">(listed host: ${escapeHTML(host)})</span>` : '';
};
const sourceLinkHTML = (source, label = source.source_name) => {
  if (source.link_status === 'withheld') {
    return `<span class="source-link-withheld">${escapeHTML(label)}<small>${escapeHTML(source.link_warning || 'External link withheld pending review.')}</small></span>`;
  }
  return `<a href="${escapeHTML(safeURL(source.url))}"${source.url.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : ''}>${escapeHTML(label)}${hostHint(source.url)} ↗</a>`;
};

async function init() {
  try {
    const archiveNode = byId('archive-data');
    if (!archiveNode) throw new Error('Embedded archive data is missing. Regenerate index.html from archive.json.');
    const data = JSON.parse(archiveNode.textContent);
    state.archiveData = data;
    state.books = Array.isArray(data.catalogue) ? data.catalogue : [];
    state.sources = Array.isArray(data.sources) ? data.sources : [];
    state.related = Array.isArray(data.related_texts) ? data.related_texts : [];
    state.readers = Array.isArray(data.readers) ? data.readers : [];
    state.canonBooks = Array.isArray(data.canon_registry?.books) ? data.canon_registry.books : [];
    state.canonContextSourceIds = Array.isArray(data.canon_registry?.context_source_ids) ? data.canon_registry.context_source_ids : [];
    state.translationRegistry = data.translation_registry || null;
    byId('book-count').textContent = state.books.length;
    byId('all-count').textContent = state.books.length;
    byId('source-count').textContent = state.sources.length;
    const catalogueIds = new Set(state.books.map(book => book.catalogue_id));
    const mappedRows = new Set(state.canonBooks.flatMap(book => book.catalogue_ids || []).filter(id => catalogueIds.has(id)));
    const mappedCanonEntries = state.canonBooks.filter(book => (book.catalogue_ids || []).some(id => catalogueIds.has(id))).length;
    byId('catalogue-crosswalk-summary').textContent = `${mappedCanonEntries} of ${state.canonBooks.length} Church-list entries link to ${mappedRows.size} of ${state.books.length} catalogue rows for navigation. This does not verify that the mapped titles identify the same work.`;
    renderBooks(); renderSources(); renderRelated(); renderCanonCoverage(); renderLanguageCoverage(); renderReader();
  } catch (error) {
    byId('results-label').textContent = 'The catalogue could not be loaded.';
    byId('book-grid').innerHTML = `<div class="load-error"><strong>Archive unavailable</strong><p>${escapeHTML(error.message)}. Rebuild the embedded archive from archive.json.</p></div>`;
  }
}

function rightsClassificationLabel(value) {
  return ({
    public_domain_claimed: 'Public domain claimed (jurisdiction may vary)',
    open_license: 'Open license stated (see exact terms)',
    permission_limited: 'Reuse limited by stated terms',
    all_rights_reserved: 'All rights reserved',
    unknown: 'Rights unknown or not established',
    mixed: 'Mixed rights or jurisdictional terms'
  })[value] || 'Rights category not recorded';
}

function rightsNote(record) {
  return `Rights category: ${escapeHTML(rightsClassificationLabel(record.rights_classification))} · detailed source notice: ${escapeHTML(record.rights_status || 'not recorded')}`;
}

function renderLanguageCoverage() {
  const registry = state.translationRegistry;
  let integrityNote = byId('language-integrity-note');
  if (!integrityNote) {
    integrityNote = document.createElement('aside');
    integrityNote.id = 'language-integrity-note';
    integrityNote.className = 'archive-integrity-note';
    integrityNote.setAttribute('role', 'note');
    integrityNote.setAttribute('aria-label', 'Coverage and translation integrity');
    document.querySelector('#language-coverage-title')?.closest('.section-heading')?.after(integrityNote);
  }
  const languageLabel = tag => registry?.languages?.find(language => language.language_tag === tag)?.language_name || registry?.basis_languages?.find(language => language.language_tag === tag)?.language_name || tag;
  const languages = registry?.languages || [];
  const readerLanguages = languages.filter(language => (language.records || []).some(record => record.status === 'bundled'));
  const bundledLayers = readerLanguages.flatMap(language => language.records.filter(record => record.status === 'bundled'));
  const layerReader = record => state.readers.find(reader => reader.reader_id === record.reader_id);
  const researchLayerCount = bundledLayers.filter(record => {
    const reader = layerReader(record);
    return Boolean(reader?.research_corpus_id);
  }).length;
  const canonLinkedLayerCount = bundledLayers.filter(record => {
    const reader = layerReader(record);
    return Boolean(reader?.canon_id && !reader.research_corpus_id && reader.canon_id === record.canon_id);
  }).length;
  const pathLanguagePairs = bundledLayers.filter(record => ['translation', 'historical_companion_translation', 'draft_translation'].includes(record.layer_role) && record.translation_path?.length === 2 && record.translation_path[0] !== 'und').length;
  const corpusLeads = registry?.corpus_leads || [];
  const corpusLeadLanguages = new Set(corpusLeads.map(lead => lead.language_tag)).size;
  const bundledSourceCanonIds = new Set(bundledLayers.filter(record => ['source_text_transcription', 'source_text_edition'].includes(record.layer_role)).map(record => record.canon_id).filter(Boolean));
  const availableCanonEntries = state.canonBooks.filter(book => bundledSourceCanonIds.has(book.canon_id)
    && state.readers.some(reader => reader.canon_id === book.canon_id
      && (!book.reader_id || reader.reader_id === book.reader_id))).length;
  const researchReaderCount = state.readers.filter(reader => reader.research_corpus_id).length;
  const researchReaderLabel = researchReaderCount === 1 ? 'research reader' : 'research readers';
  byId('language-coverage-summary').textContent = `${readerLanguages.length} reader languages · ${canonLinkedLayerCount} canon-linked text layers · ${researchLayerCount} separate research text layers · ${researchReaderCount} related ${researchReaderLabel} · ${languages.length} language profiles · ${pathLanguagePairs} two-language translation paths recorded · ${corpusLeadLanguages} languages with unbundled corpus leads`;
  const locallyUnbundledEntries = state.canonBooks.length - availableCanonEntries;
  if (integrityNote) integrityNote.textContent = `Measured from records in this bundled snapshot: ${availableCanonEntries} of ${state.canonBooks.length} Church-listed entries have source-text readers; ${locallyUnbundledEntries} have no reader bundled here. These counts describe this package, not worldwide availability, completeness, accuracy, or review status. Absence from the package means “not bundled here.” Zero is reserved for a defined, completed survey that found none; unassessed scope and viewpoints remain “not surveyed” or “unknown,” never zero by default. Machine-generated wording may appear only as a labeled draft and is never counted or presented as verified scripture or translation.`;
  byId('language-coverage-statement').textContent = registry?.coverage_statement || 'Language coverage is not available.';
  byId('language-coverage-list').innerHTML = languages.map(language => {
    const records = language.records.filter(record => record.status === 'bundled');
    const items = records.map(record => {
      const role = record.layer_role === 'source_text_transcription' ? 'Source-text transcription' : record.layer_role === 'source_text_edition' ? 'Source-text edition (encoded transcription)' : record.layer_role === 'historical_companion_translation' ? 'Historical companion translation' : record.layer_role;
      const path = record.translation_path || [];
      const basis = record.basis_language_tag === language.language_tag ? 'Source text in this language' : path.length ? `Path: ${path.map(languageLabel).map(escapeHTML).join(' → ')}` : `Basis language: ${escapeHTML(record.basis_language_tag)}`;
      const reader = state.readers.find(item => item.reader_id === record.reader_id);
      const corpus = registry?.research_corpora?.find(item => item.reader_id === record.reader_id);
      const researchOnly = Boolean(reader?.research_corpus_id || corpus);
      const candidate = record.canon_id ? state.canonBooks.find(book => book.canon_id === record.canon_id) : null;
      const title = candidate?.display_name || record.canon_id || 'Unmapped text';
      const identity = researchOnly
        ? `Research candidate: ${escapeHTML(title)} · mapping ${escapeHTML(corpus?.canon_mapping_state || 'not established')}; not canon-linked coverage`
        : escapeHTML(title);
      const textLayer = record.translation_id ? reader?.parallel_translation || (researchOnly ? reader : null) : reader;
      const review = textLayer?.verification_status ? `<details class="language-review"><summary>Review status</summary><p>${escapeHTML(textLayer.verification_status)}</p></details>` : '';
      return `<li><strong>${identity}</strong><span>${escapeHTML(role)}</span><small>${basis}</small>${review}</li>`;
    }).join('');
    const scripts = language.script_code === 'Zzzz' ? 'not established' : language.script_codes?.length ? language.script_codes.join(', ') : language.script_code;
    const direction = language.direction === 'unknown' ? 'direction unknown' : language.direction;
    const description = language.script_profile_note ? `<p class="language-profile-note">${escapeHTML(language.script_profile_note)}</p>` : '';
    const languageSources = (language.source_ids || []).map(id => state.sources.find(source => source.source_id === id)).filter(Boolean);
    const sourceDetails = languageSources.length ? `<details class="language-evidence"><summary>Language and script evidence (${languageSources.length})</summary><ul>${languageSources.map(source => `<li>${sourceLinkHTML(source)}<small>${escapeHTML(source.inspection_and_limitations || '')}</small></li>`).join('')}</ul></details>` : '<p class="language-profile-note">No language or script sources are linked to this profile.</p>';
    const survey = language.availability_survey || { status: 'not_surveyed' };
    const surveySources = (survey.source_ids || []).map(id => state.sources.find(source => source.source_id === id)).filter(Boolean);
    const surveyEvidence = surveySources.length ? `<ul class="language-survey-sources">${surveySources.map(source => `<li>${sourceLinkHTML(source)}</li>`).join('')}</ul>` : '';
    const surveyNote = survey.status === 'completed'
      ? `<p class="language-profile-note"><strong>External availability survey:</strong> ${escapeHTML(survey.result === 'none_found' ? 'no records found' : `${survey.result_count} record(s) found`)} within the bounded scope “${escapeHTML(survey.scope)}” as of ${escapeHTML(survey.searched_at)}. This result does not extend beyond that scope.</p>${surveyEvidence}`
      : survey.status === 'in_progress'
        ? `<p class="language-profile-note"><strong>External availability survey:</strong> in progress within “${escapeHTML(survey.scope)}”; no result is recorded.</p>${surveyEvidence}`
        : '<p class="language-profile-note"><strong>External availability:</strong> not surveyed. This card lists only text bundled in this archive.</p>';
    const contents = items || '<li>No text for this language is bundled in this archive. This does not establish whether texts exist elsewhere; see separately recorded leads.</li>';
    const writingMode = language.writing_mode ? ` · writing mode ${escapeHTML(language.writing_mode)}` : '';
    return `<article class="language-card"><div class="language-card-heading"><h3>${escapeHTML(language.language_name)}</h3><span lang="en">${escapeHTML(language.language_tag)} · script${language.script_code === 'Zzzz' || language.script_codes?.length === 1 ? '' : 's'} ${escapeHTML(scripts)} · ${escapeHTML(direction)}${writingMode}</span></div>${surveyNote}<ul>${contents}</ul>${description}${sourceDetails}</article>`;
  }).join('');
  const leads = registry?.translation_leads || [];
  const sourceLinks = ids => ids.map(id => state.sources.find(source => source.source_id === id)).filter(Boolean).map(source => sourceLinkHTML(source)).join(' · ');
  const translationHtml = leads.length ? `<h3>Book translation leads · not bundled</h3>${leads.map(lead => `<article class="translation-lead"><strong>${escapeHTML(lead.edition)}</strong><p>${escapeHTML(lead.translator)} · ${lead.translation_path ? lead.translation_path.map(languageLabel).map(escapeHTML).join(' → ') : 'translation path unknown'} · ${escapeHTML(lead.review_status)}</p><p>${escapeHTML(lead.notes)}</p><small>${rightsNote(lead)} · ${sourceLinks(lead.source_ids || [])}</small></article>`).join('')}` : '';
  const editionLeads = registry?.edition_leads || [];
  const editionHtml = editionLeads.length ? `<h3>Book source-edition leads · not bundled</h3>${editionLeads.map(lead => {
    const candidate = state.canonBooks.find(book => book.canon_id === lead.candidate_canon_id);
    return `<article class="translation-lead edition-lead"><strong>${escapeHTML(lead.title)}</strong><p>${escapeHTML(lead.edition_statement)}</p><p>Candidate catalogue link: ${escapeHTML(candidate?.display_name || lead.candidate_canon_id)} · mapping ${escapeHTML(lead.mapping_state)} · ${escapeHTML(lead.language_name)} (${escapeHTML(lead.language_tag)}, ${escapeHTML(lead.script_code)})</p><p>${escapeHTML(lead.scope_description)}</p><p>${escapeHTML(lead.review_status)}</p><small>${rightsNote(lead)} · ${sourceLinks(lead.source_ids || [])}</small></article>`;
  }).join('')}` : '';
  const corpusHtml = corpusLeads.length ? `<h3>Multi-book language/corpus leads · not bundled</h3>${corpusLeads.map(lead => {
    const basis = lead.basis_language_tag === 'und' ? 'source language unknown' : `basis ${escapeHTML(languageLabel(lead.basis_language_tag))}`;
    return `<article class="translation-lead"><strong>${escapeHTML(lead.title)}</strong><p>${escapeHTML(lead.publisher)} · ${escapeHTML(lead.publication_year)} · ${escapeHTML(lead.language_name)} (${escapeHTML(lead.language_tag)}, script ${escapeHTML(lead.script_code)}${lead.script_status ? ` · ${escapeHTML(lead.script_status)} for this witness` : ''}) · ${lead.translation_path ? lead.translation_path.map(languageLabel).map(escapeHTML).join(' → ') : 'translation path unknown'} · ${basis}</p><p>${escapeHTML(lead.scope_description)}</p><p>${escapeHTML(lead.contributors)} ${escapeHTML(lead.review_status)}</p><p>${escapeHTML(lead.notes)}</p><small>${rightsNote(lead)} · ${sourceLinks(lead.source_ids || [])}</small></article>`;
  }).join('')}` : '';
  const researchCorpora = registry?.research_corpora || [];
  const researchHtml = researchCorpora.length ? `<h3>Related research readers · not counted as Church-list book coverage</h3>${researchCorpora.map(corpus => `<article class="translation-lead"><strong>${escapeHTML(corpus.title)}</strong><p>${escapeHTML(corpus.language_description)} · ${escapeHTML(corpus.script_description)} · ${escapeHTML(corpus.unit_summary)}</p><p>${escapeHTML(corpus.canon_mapping_note)}</p><p>${escapeHTML(corpus.review_status)}</p><small>${rightsNote(corpus)} · ${sourceLinks(corpus.source_ids || [])}</small><p><button class="reader-open-research" type="button" data-reader-id="${escapeHTML(corpus.reader_id)}">Open this research reader</button></p></article>`).join('')}` : '';
  byId('translation-leads').innerHTML = translationHtml + editionHtml + researchHtml + corpusHtml;
  document.querySelectorAll('.reader-open-research').forEach(button => button.addEventListener('click', () => {
    state.readerId = button.dataset.readerId;
    state.chapter = 1;
    renderReader();
    document.querySelector('#reader')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    byId('reader-book').focus({ preventScroll: true });
  }));
}

function renderCanonCoverage() {
  const archive = JSON.parse(byId('archive-data').textContent);
  const registry = archive.canon_registry;
  const translationRegistry = archive.translation_registry;
  // Report reader availability from reader records actually embedded in this build,
  // not from a display label that could become stale.
  const readerForCanon = book => state.readers.find(reader => reader.canon_id === book.canon_id
    && (!book.reader_id || reader.reader_id === book.reader_id));
  const available = state.canonBooks.filter(book => readerForCanon(book)).length;
  byId('canon-coverage-summary').textContent = `${available} of ${state.canonBooks.length} Church-listed entries have bundled reader text`;
  const notBundled = state.canonBooks.length - available;
  const candidateCanonIds = new Set([
    ...(translationRegistry.translation_leads || []),
    ...(translationRegistry.edition_leads || []),
    ...(translationRegistry.corpus_leads || []),
    ...(translationRegistry.research_corpora || [])
  ].map(record => record.candidate_canon_id).filter(Boolean));
  const candidateEntryCount = state.canonBooks.filter(book => !readerForCanon(book) && candidateCanonIds.has(book.canon_id)).length;
  const unlinkedCandidateCount = notBundled - candidateEntryCount;
  const coverageNote = document.querySelector('.canon-coverage-method');
  if (coverageNote) coverageNote.textContent = `Measured from the actual reader records in this bundled snapshot: ${available} of ${state.canonBooks.length} listed entries have a reader here; ${notBundled} have no reader bundled here. Of those unbundled entries, ${candidateEntryCount} have at least one title-linked candidate record and ${unlinkedCandidateCount} have no such candidate recorded in this registry snapshot. Candidate records are research or bibliographic leads; they do not establish that usable text is available, confirm an exact canon mapping, or prove accuracy, completeness, rights, or review. No candidate recorded here does not mean no source exists elsewhere. These observed package counts do not estimate worldwide availability. “Not bundled here” describes this package only. A zero is valid only after a defined, completed survey finds none; unassessed availability and viewpoints stay “not surveyed” or “unknown,” never zero by default. Entries with bundled text go to the reader. Grouped titles stay grouped as the Church list gives them; unresolved crosswalks are marked in the catalogue. Machine-generated wording may appear only as a labeled draft; it never contributes to coverage counts or appears as verified scripture or translation.`;
  const contextSources = (registry.context_source_ids || []).map(id => state.sources.find(source => source.source_id === id)).filter(Boolean);
  byId('canon-coverage-context').innerHTML = `<p>${escapeHTML(registry.scholarly_context || 'No comparative canon context has been recorded.')}</p>${contextSources.length ? `<p class="canon-context-sources">Context sources: ${contextSources.map(source => sourceLinkHTML(source)).join(' · ')}</p>` : ''}`;
  const sections = ['Old Testament', 'New Testament'];
  byId('canon-coverage-list').innerHTML = sections.map(section => {
    const books = state.canonBooks.filter(book => book.section === section);
    return `<div class="canon-coverage-group"><h3>${escapeHTML(section)} <span>${books.length}</span></h3><div class="canon-coverage-grid">${books.map(book => {
      const reader = readerForCanon(book);
      const hasReader = Boolean(reader);
      const status = hasReader
        ? (String(book.reader_status || '').startsWith('Bundled:') ? book.reader_status : `Reader bundled: ${reader.language_tag || 'language recorded in reader metadata'}`)
        : (String(book.reader_status || '').startsWith('Bundled:') ? 'Reader record unavailable; coverage needs repair' : book.reader_status);
      const sourceLabel = book.source_label && book.source_label !== book.display_name ? `<span class="canon-entry-source-label">Church list: ${escapeHTML(book.source_label)}</span>` : '';
      const mappingNote = book.mapping_note ? `<span class="canon-entry-mapping-note">${escapeHTML(book.mapping_note)}</span>` : '';
      return `<button class="canon-entry${hasReader ? ' canon-entry-ready' : ''}" type="button" data-canon-entry="${escapeHTML(book.canon_id)}"><span class="canon-entry-number">${book.section_number}</span><span class="canon-entry-title">${escapeHTML(book.display_name)}</span>${sourceLabel}<span class="canon-entry-status">${escapeHTML(status)}</span>${mappingNote}</button>`;
    }).join('')}</div></div>`;
  }).join('');
  document.querySelectorAll('[data-canon-entry]').forEach(button => button.addEventListener('click', () => {
    const entry = state.canonBooks.find(book => book.canon_id === button.dataset.canonEntry);
    if (!entry) return;
    const reader = readerForCanon(entry);
    if (reader) {
      state.readerId = reader.reader_id;
      location.hash = 'reader';
      renderReader();
      byId('reader').scrollIntoView({ behavior: 'smooth' });
      return;
    }
    if (entry.catalogue_ids?.[0]) selectBook(entry.catalogue_ids[0]);
    location.hash = 'catalogue';
    byId('catalogue').scrollIntoView({ behavior: 'smooth' });
  }));
  if (!registry || registry.book_count !== 81) throw new Error('The Church-list coverage index is incomplete.');
}

function filteredBooks() {
  const q = state.query.trim().toLocaleLowerCase();
  return state.books.filter(book => (state.filter === 'All' || book.tradition_group === state.filter)
    && (!q || [book.display_name, book.alternate_names_or_notes, book.tradition_group, book.identity_status].join(' ').toLocaleLowerCase().includes(q)));
}

function renderBooks() {
  const books = filteredBooks();
  byId('results-label').textContent = `Showing ${books.length} of ${state.books.length} records`;
  byId('reset-filters').hidden = !state.query && state.filter === 'All';
  byId('empty-state').hidden = books.length > 0;
  byId('book-grid').innerHTML = books.map(book => `
    <button class="book-card${state.selected === book.catalogue_id ? ' selected' : ''}" data-book="${escapeHTML(book.catalogue_id)}" aria-pressed="${state.selected === book.catalogue_id}">
      <span class="book-number">${escapeHTML(book.catalogue_id.replace('eotc-',''))}</span>
      <h3>${escapeHTML(book.display_name)}</h3>
      <span class="card-footer"><span class="mini-tag">${escapeHTML(book.tradition_group)}</span><span class="mini-tag"><i class="status-dot"></i>${escapeHTML(book.text_availability_status)}</span></span>
    </button>`).join('');
  document.querySelectorAll('[data-book]').forEach(button => button.addEventListener('click', () => selectBook(button.dataset.book)));
}

function selectBook(id) {
  state.selected = id;
  const book = state.books.find(item => item.catalogue_id === id);
  if (!book) return;
  renderBooks();
  const source = state.sources.find(item => item.source_id === book.source_id);
  const evidence = (book.evidence_source_ids || []).map(id => state.sources.find(item => item.source_id === id)).filter(Boolean);
  const reader = state.readers.find(item => state.canonBooks.some(entry => entry.reader_id === item.reader_id && (entry.catalogue_ids || []).includes(book.catalogue_id)));
  const relatedCanonIds = state.canonBooks.filter(entry => (entry.catalogue_ids || []).includes(book.catalogue_id)).map(entry => entry.canon_id);
  const researchReader = (state.translationRegistry?.research_corpora || []).find(corpus => relatedCanonIds.includes(corpus.candidate_canon_id));
  const editionLeads = (state.translationRegistry?.edition_leads || []).filter(lead => relatedCanonIds.includes(lead.candidate_canon_id));
  if (reader) state.readerId = reader.reader_id;
  const readerLink = reader
    ? `<a class="button button-gold detail-reader-link" href="#reader">Open the locally stored ${escapeHTML(reader.language)} reader ↓</a><p class="detail-warning">Reader edition: ${escapeHTML(reader.edition)}. Verification: ${escapeHTML(reader.verification_status)} The reader panel records its source and remaining limits.</p>`
    : researchReader
      ? `<p class="detail-warning">No canon-linked reader is bundled for this catalogue title. A related title-level research witness is available; its canon mapping, language metadata, accuracy, and edition relationship remain unresolved.</p><button class="reader-open-research" type="button" data-reader-id="${escapeHTML(researchReader.reader_id)}">Open related research witness</button>`
      : '<p class="detail-warning">No source-text reader is bundled for this title in this archive snapshot. This describes the local package only; any known source leads and their limits are listed above.</p>';
  const link = item => sourceLinkHTML(item);
  const editionLeadHtml = editionLeads.length ? `<section class="translation-leads edition-leads"><h3>Source edition leads · not bundled as reader text</h3>${editionLeads.map(lead => {
    const leadSources = (lead.source_ids || []).map(sourceId => state.sources.find(item => item.source_id === sourceId)).filter(Boolean);
    return `<article class="translation-lead edition-lead"><strong>${escapeHTML(lead.title)}</strong><p>${escapeHTML(lead.edition_statement)}</p><p>Mapping status: ${escapeHTML(lead.mapping_state)} · ${escapeHTML(lead.witness_type)}</p><p>${escapeHTML(lead.scope_description)}</p><p>${escapeHTML(lead.review_status)}</p><small>${rightsNote(lead)}</small><ul>${leadSources.map(item => `<li>${link(item)}<br><small>${escapeHTML(item.inspection_and_limitations || '')}</small></li>`).join('') || '<li>No source records linked.</li>'}</ul></article>`;
  }).join('')}</section>` : '';
  const chapterCount = /^\d+$/.test(String(book.chapter_count || '')) ? `${escapeHTML(book.chapter_count)} chapters` : escapeHTML(book.chapter_count || 'Not established');
  byId('detail-panel').innerHTML = `
    <div class="detail-top"><div><span class="detail-index">${escapeHTML(book.catalogue_id)} · ${escapeHTML(book.tradition_group)}</span><h3>${escapeHTML(book.display_name)}</h3></div><button class="detail-close" aria-label="Close details">×</button></div>
    <span class="detail-status">${escapeHTML(book.identity_status)}</span>
    <dl class="detail-meta"><dt>Alternate names &amp; notes</dt><dd>${escapeHTML(book.alternate_names_or_notes || 'Alternate names not yet researched.')}</dd><dt>Edition / translation</dt><dd>${escapeHTML(book.edition_or_translation || 'Not identified')}</dd><dt>Chapter count</dt><dd>${chapterCount}</dd><dt>Chapter order</dt><dd>${escapeHTML(book.chapter_order_status || 'Not researched')}</dd><dt>Text &amp; completeness</dt><dd>${escapeHTML(book.text_availability_status || 'Not researched')} · ${escapeHTML(book.completeness_status || 'Not assessed')}</dd><dt>Reuse rights</dt><dd>${escapeHTML(book.rights_status || 'Not assessed; no edition selected')}</dd><dt>Catalogue source</dt><dd>${source ? link(source) : 'Local record source missing.'}</dd><dt>Evidence leads</dt><dd>${evidence.length ? evidence.map(link).join(' · ') : 'No evidence lead recorded yet.'}</dd></dl>
     ${readerLink}${editionLeadHtml}`;
  byId('detail-panel').querySelector('.detail-close').addEventListener('click', () => { state.selected = null; renderBooks(); byId('detail-panel').innerHTML = '<div class="detail-empty"><span class="detail-star">✳</span><h3>Choose a title</h3><p>Open a catalogue record to see its alternate names, source, and current research status.</p></div>'; });
  byId('detail-panel').querySelectorAll('.reader-open-research').forEach(button => button.addEventListener('click', () => {
    state.readerId = button.dataset.readerId;
    state.chapter = 1;
    renderReader();
    document.querySelector('#reader')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    byId('reader-book').focus({ preventScroll: true });
  }));
}

function renderReader() {
  const bookSelect = byId('reader-book');
  const languageSelect = byId('reader-language');
  if (!state.readers.length) {
    byId('reader-text').innerHTML = '<p class="reader-empty">No reader text is bundled in this archive yet.</p>';
    return;
  }
  const reader = state.readers.find(item => item.reader_id === state.readerId) || state.readers[0];
  state.readerId = reader.reader_id;
  const canonReaders = state.readers.filter(item => item.canon_id);
  const researchReaders = state.readers.filter(item => item.research_corpus_id);
  const option = item => `<option value="${escapeHTML(item.reader_id)}"${item.reader_id === reader.reader_id ? ' selected' : ''}>${escapeHTML(item.display_name || item.title)}</option>`;
  bookSelect.innerHTML = [
    canonReaders.length ? `<optgroup label="Church-list readers">${canonReaders.map(option).join('')}</optgroup>` : '',
    researchReaders.length ? `<optgroup label="Related research texts · not canon coverage">${researchReaders.map(option).join('')}</optgroup>` : '',
  ].join('');
  const companion = reader.parallel_translation;
  const languageOptions = [`<option value="${escapeHTML(reader.language_tag)}">${escapeHTML(reader.language)}</option>`];
  if (companion) languageOptions.push(`<option value="${escapeHTML(companion.language_tag)}">${escapeHTML(companion.language)}</option>`, '<option value="parallel">Parallel witnesses</option>');
  const priorMode = languageSelect.value;
  languageSelect.innerHTML = languageOptions.join('');
  languageSelect.value = languageOptions.some(option => option.includes(`value="${priorMode}"`)) ? priorMode : reader.language_tag;
  const chapter = reader.chapters.find(item => item.chapter === state.chapter) || reader.chapters[0];
  state.chapter = chapter.chapter;
  const mode = languageSelect.value;
  const readerDownload = byId('reader-download');
  if (readerDownload) readerDownload.textContent = mode === 'parallel'
    ? 'Download both witnesses + evidence (JSON)'
    : `Download ${mode === companion?.language_tag ? companion.language : reader.language} text + evidence (JSON)`;
  if (byId('reader-export-status')) byId('reader-export-status').textContent = '';
  const englishChapter = companion?.chapters?.find(item => item.chapter === chapter.chapter);
  const languageProfile = tag => state.translationRegistry?.languages?.find(language => language.language_tag === tag);
  const direction = tag => {
    const value = languageProfile(tag)?.direction;
    return value === 'ltr' || value === 'rtl' ? value : 'auto';
  };
  const writingModeStyle = tag => {
    const mode = languageProfile(tag)?.writing_mode;
    return mode === 'vertical-rl' || mode === 'vertical-lr' ? ` style="writing-mode:${mode}"` : '';
  };
  const sourceTag = reader.language_tag || 'und';
  const englishTag = companion?.language_tag || 'en';
  const sourceUnits = Array.isArray(chapter.units) ? chapter.units : chapter.verses || [];
  const parallelRows = window.ReaderAlignment.buildParallelRows(sourceUnits, englishChapter?.verses || []);
  const sectionLabel = reader.section_label || 'Chapter';
  byId('reader-chapter').innerHTML = reader.chapters.map(item => `<option value="${item.chapter}"${item.chapter === chapter.chapter ? ' selected' : ''}>${escapeHTML(sectionLabel)} ${item.chapter}</option>`).join('');
  const unitLabel = reader.unit_label || 'Verse';
  const marker = item => item?.unit_order != null
    ? `${unitLabel} ${item.unit_order} · ${item.source_marker != null ? `source label ${item.source_marker}` : 'source label absent'}`
    : item?.source_marker ? `${item.number} · source ${item.source_marker}` : String(item?.number ?? '');
  const witness = (item, tag, cls, label) => `<div class="reader-witness ${cls}"><span class="reader-verse-number">${escapeHTML(label)}</span><span class="reader-witness-content" lang="${escapeHTML(tag)}" dir="${escapeHTML(direction(tag))}"${writingModeStyle(tag)}>${item ? item.text ? `${escapeHTML(item.text)}${(item.continuations || []).map(segment => `<span class="reader-continuation"><span class="reader-structure-marker">Unnumbered continuation (source ${escapeHTML(segment.source_marker || 'marker')})</span>${escapeHTML(segment.text)}</span>`).join('')}` : item.source_text_state === 'marker_only' ? '<span class="reader-gap">This source label has no inline verse text; its source note is retained below.</span>' : '<span class="reader-gap">No text is recorded for this source unit.</span>' : '<span class="reader-gap">No entry carrying this printed label in this witness.</span>'}</span></div>`;
  const sourceStructure = item => {
    const markers = item?.source_markers_before || [];
    return [
      markers.includes('d') ? '<span class="reader-structure-marker">Source descriptive-title / superscription marker</span>' : '',
      markers.includes('b') ? '<span class="reader-structure-marker">Source break marker</span>' : '',
    ].join('');
  };
  const englishVerse = item => `<article class="reader-verse ${(item.source_markers_before || []).includes('p') ? 'paragraph-start' : ''}">${sourceStructure(item)}${witness(item, englishTag, 'english-witness', String(item.number))}</article>`;
  const chapterHeading = Array.isArray(chapter.heading) && chapter.heading.length ? `<div class="reader-heading" lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${chapter.heading.map(item => `<p>${escapeHTML(item)}</p>`).join('')}</div>` : '';
  byId('reader-title').textContent = `${reader.display_name || reader.title.split(' — ')[0]} · ${sectionLabel} ${chapter.chapter}${mode === 'parallel' ? ' · Parallel witnesses' : ` · ${mode === englishTag && companion ? 'English' : reader.language}`}`;
  const sectionCount = reader.section_unit_plural ? `${reader.chapter_count} ${reader.section_unit_plural}` : `${reader.chapter_count} chapters`;
  const observedUnits = layer => Number.isInteger(layer?.unit_count) && layer.unit_count >= 0
    ? `${layer.unit_count.toLocaleString()} ${layer.unit_label || 'source units'} observed`
    : `unit count unknown for ${layer?.title || layer?.language || 'this text'}`;
  const activeCountLayers = mode === 'parallel' && companion ? [reader, companion]
    : companion && mode === englishTag ? [companion] : [reader];
  byId('reader-chapter-count').textContent = `${sectionCount} · ${activeCountLayers.map(observedUnits).join(' · ')}`;
  if (mode === 'parallel' && companion) {
    byId('reader-text').innerHTML = chapterHeading + parallelRows.map(row => `<article class="reader-parallel-row"><div><span class="reader-witness-label">${escapeHTML(reader.language.toUpperCase())}</span>${witness(row.source, sourceTag, 'geez-witness', row.source ? marker(row.source) : 'No source unit')}</div><div><span class="reader-witness-label">${escapeHTML(companion.title)}</span>${sourceStructure(row.english)}${witness(row.english, englishTag, 'english-witness', row.english ? String(row.english.number) : 'No matching English label')}</div></article>`).join('');
    byId('reader-alignment-note').textContent = 'Only unique matching printed labels are paired, for navigation. Duplicate, absent, or ambiguous labels stay unpaired and visible; matching labels do not establish textual equivalence or translation accuracy.';
  } else if (companion && mode === englishTag) {
    byId('reader-text').innerHTML = chapterHeading + (englishChapter?.verses || []).map(englishVerse).join('');
    byId('reader-alignment-note').textContent = companion.translation_basis;
  } else {
    byId('reader-text').innerHTML = chapterHeading + sourceUnits.map(item => `<article class="reader-verse">${witness(item, sourceTag, 'geez-witness', marker(item))}</article>`).join('');
    byId('reader-alignment-note').textContent = reader.unit_label ? `Source numbering note: ${reader.chapter_structure_note}` : '';
  }
  const sourceNotes = (chapter.notes || []).map(note => ({ ...note, witnessLabel: reader.language }));
  const translatedNotes = (englishChapter?.notes || []).map(note => ({ ...note, witnessLabel: companion?.language || 'Translation' }));
  const notes = mode === 'parallel' && companion ? [...sourceNotes, ...translatedNotes]
    : companion && mode === englishTag ? translatedNotes : sourceNotes;
  byId('reader-translation-notes').innerHTML = notes.length ? `<details><summary>Source notes and cross-references (${notes.length})</summary><ol>${notes.map(note => `<li><strong>${note.witnessLabel ? `${escapeHTML(note.witnessLabel)} · ` : ''}${escapeHTML(note.verse)}${note.marker ? ` ${escapeHTML(note.marker)}` : ''}</strong> ${note.text ? escapeHTML(note.text) : 'A source note marker is present without note text in the archived member.'}${note.source_reference ? ` <span class="reader-structure-marker">Source reference ${escapeHTML(note.source_reference)}</span>` : ''}</li>`).join('')}</ol></details>` : '';
  byId('reader-prev').disabled = chapter.chapter === 1;
  byId('reader-next').disabled = chapter.chapter === reader.chapter_count;
  const activeLayers = companion && mode !== sourceTag ? (mode === 'parallel' ? [reader, companion] : [companion]) : [reader];
  const verification = activeLayers.map(layer => `${layer.title || layer.language || reader.title}: ${layer.verification_status || 'Review status not recorded.'}`).map(escapeHTML).join(' ');
  const activeSourceIds = [...new Set(activeLayers.flatMap(layer => layer.source_ids || []))];
  const citations = activeSourceIds.map(id => state.sources.find(item => item.source_id === id)).filter(Boolean);
  byId('reader-source').innerHTML = `${verification} Sources: ${citations.map(item => sourceLinkHTML(item)).join(' · ')}`;
  byId('reader-permission').textContent = `Text rights: ${rightsClassificationLabel(reader.rights_classification)}. ${reader.copyright_notice}${companion ? ` English companion rights: ${rightsClassificationLabel(companion.rights_classification)}. ${companion.text_notice}` : ''}`;
  byId('reader-caveat-text').textContent = [reader.edition_scope, reader.chapter_structure_note, reader.transcription_note, reader.editorial_signs_note, ...(companion && mode !== sourceTag ? [companion.translation_basis, companion.verification_status] : [])].filter(Boolean).join(' ');
  renderReaderStudyView(reader, chapter);
}

function renderReaderStudyView(reader, chapter) {
  const lensSelect = byId('reader-lens');
  const panel = byId('reader-study-panel');
  const text = byId('reader-text');
  const lens = lensSelect?.value || 'text';
  text.hidden = !['text', 'integrated'].includes(lens);
  panel.hidden = lens === 'text';
  if (lens === 'text') { panel.innerHTML = ''; return; }

  const corpus = (state.translationRegistry?.research_corpora || []).find(item => item.corpus_id === reader.research_corpus_id);
  const canon = state.canonBooks.find(item => item.canon_id === reader.canon_id);
  const entry = state.books.find(item => canon?.catalogue_ids?.includes(item.catalogue_id));
  const registry = state.translationRegistry;
  const profiles = registry?.languages || [];
  const bookLeads = (registry?.translation_leads || []).filter(lead => lead.canon_id === reader.canon_id);
  const languageName = tag => profiles.find(item => item.language_tag === tag)?.language_name || registry?.basis_languages?.find(item => item.language_tag === tag)?.language_name || tag;
  const languageRows = profiles.map(profile => {
    const records = (profile.records || []).filter(record => record.canon_id === reader.canon_id || record.reader_id === reader.reader_id);
    const hasLead = bookLeads.some(lead => lead.language_tag === profile.language_tag);
    const content = records.length
      ? records.map(record => {
          const path = Array.isArray(record.translation_path) ? ` · Path: ${record.translation_path.map(languageName).map(escapeHTML).join(' → ')}` : '';
          return `<li><strong>${escapeHTML(record.status || 'Status not recorded')}</strong> — ${escapeHTML(record.layer_role || 'language layer')}${path}<br><span>${escapeHTML(record.basis_description || 'No basis description recorded.')}</span></li>`;
        }).join('')
      : hasLead
        ? '<li><strong>No text is bundled.</strong> A separate unbundled translation lead is listed below.</li>'
        : '<li><strong>No bundled layer identified for this title.</strong> This language profile is not a translation of the selected book.</li>';
    return `<section class="reader-language-card"><h4 lang="${escapeHTML(profile.language_tag)}">${escapeHTML(profile.language_name)} <small>${escapeHTML(profile.language_tag)} · ${escapeHTML(profile.script_code || 'script not recorded')}</small></h4><ul>${content}</ul></section>`;
  }).join('');

  const sourceLink = item => sourceLinkHTML(item);
  const sources = state.sources;
  const sourceCards = ids => (ids || []).map(id => sources.find(item => item.source_id === id)).filter(Boolean).map(item => `<li>${sourceLink(item)} <span>${escapeHTML(item.archive_status || '')}</span><br><small>${escapeHTML(item.inspection_and_limitations || '')}</small></li>`).join('');
  const bookLeadHtml = bookLeads.length ? `<h4>Unbundled translation leads for this book</h4>${bookLeads.map(lead => `<article class="translation-lead"><strong>${escapeHTML(lead.edition)}</strong><p>${escapeHTML(lead.translator)} · ${Array.isArray(lead.translation_path) ? lead.translation_path.map(languageName).map(escapeHTML).join(' → ') : 'translation path unknown'} · not bundled</p><p>${escapeHTML(lead.review_status)}</p><p>${escapeHTML(lead.notes)}</p><small>${rightsNote(lead)}</small><ul class="reader-source-list">${sourceCards(lead.source_ids) || '<li>No source records linked.</li>'}</ul></article>`).join('')}` : '';
  const available = `<p class="reader-lens-intro">Only text layers bundled for this title are selectable above. Registered language profiles describe archive coverage; unbundled leads are evidence pointers, not reader text.</p><p><strong>Available here:</strong> ${escapeHTML(reader.language)}${reader.parallel_translation ? `; ${escapeHTML(reader.parallel_translation.language)} companion by ${escapeHTML(reader.parallel_translation.translator || 'translator not recorded')}` : ''}.</p><p><strong>Reader status:</strong> ${escapeHTML(reader.verification_status)}</p><div class="reader-language-grid">${languageRows || '<p>No language profiles are registered.</p>'}</div>${bookLeadHtml}`;
  const context = `<p class="reader-lens-intro">Context follows the named witness and edition. It is not a claim to reconstruct every historical stage or community reading.</p><dl class="reader-context-list"><dt>Edition / witness</dt><dd>${escapeHTML(reader.edition || 'Not identified')}</dd><dt>Time &amp; scope</dt><dd>${escapeHTML(reader.edition_scope || 'Not established')}</dd><dt>Chapter ${escapeHTML(chapter.chapter)} structure</dt><dd>${escapeHTML(reader.chapter_structure_note || 'Not established')}</dd><dt>Transcription status</dt><dd>${escapeHTML(reader.transcription_note || reader.verification_status || 'Not recorded')}</dd><dt>Editorial signs</dt><dd>${escapeHTML(reader.editorial_signs_note || 'No editorial-sign note recorded.')}</dd><dt>Archived pages</dt><dd>${escapeHTML(reader.source_pages || 'No local page-capture path recorded.')}</dd></dl><h4>Evidence sources</h4><ul class="reader-source-list">${sourceCards(reader.source_ids) || '<li>No source records are linked to this reader.</li>'}</ul>`;
  const perspectives = `<p class="reader-lens-intro">Perspectives are presented as attributed records, not collapsed into one supposedly universal interpretation. Unsurveyed traditions and viewpoints are marked unknown; they are not synthesized. This archive preserves the Church's cited English list and selected scholarship about canon-list variation, not a reviewed global survey.</p><dl class="reader-context-list"><dt>Canon mapping</dt><dd>${escapeHTML(corpus?.canon_mapping_note || canon?.mapping_note || entry?.canon_view || 'No verified mapping note is recorded.')}</dd><dt>Catalogue identity</dt><dd>${escapeHTML(entry?.identity_status || (corpus ? 'Related research text; no canon-linked catalogue identity assigned.' : 'No linked catalogue identity record.'))}</dd><dt>Church-list status</dt><dd>${escapeHTML(canon?.reader_status || (corpus ? 'Not linked to or counted as a Church-list reader.' : 'No Church-list crosswalk recorded.'))}</dd><dt>Editorial review</dt><dd>${escapeHTML(entry?.reviewer_notes || corpus?.review_status || 'No additional reviewer notes recorded.')}</dd></dl><h4>Evidence and scope</h4><ul class="reader-source-list">${sourceCards([...new Set([...(entry?.evidence_source_ids || canon?.source_ids || []), ...(corpus?.source_ids || []), ...state.canonContextSourceIds])]) || '<li>No separate perspective sources recorded.</li>'}</ul>`;

  const blocks = lens === 'language' ? `<h4>Language &amp; translation path</h4>${available}`
    : lens === 'time' ? `<h4>Time &amp; edition context</h4>${context}`
    : lens === 'tradition' ? `<h4>Tradition &amp; interpretive perspectives</h4>${perspectives}`
    : `<h4>Integrated reading · ${escapeHTML(reader.title)} · ${escapeHTML(reader.section_label || 'Chapter')} ${escapeHTML(chapter.chapter)}</h4><div class="reader-integrated-grid"><section><h5>Language &amp; translation</h5>${available}</section><section><h5>Time &amp; edition</h5>${context}</section><section><h5>Tradition &amp; perspectives</h5>${perspectives}</section></div><p class="reader-integrity-note">The text above remains the selected witness. The panels below it add distinct evidence and viewpoints; they do not merge unlike translations, resolve disputed readings, or fill missing text.</p>`;
  panel.innerHTML = blocks;
}

byId('reader-book').addEventListener('change', event => { state.readerId = event.target.value; state.chapter = 1; renderReader(); });
byId('reader-chapter').addEventListener('change', event => { state.chapter = Number(event.target.value); renderReader(); });
byId('reader-prev').addEventListener('click', () => { state.chapter = Math.max(1, state.chapter - 1); renderReader(); });
byId('reader-next').addEventListener('click', () => { const reader = state.readers.find(item => item.reader_id === state.readerId); state.chapter = Math.min(reader?.chapter_count || 1, state.chapter + 1); renderReader(); });
byId('reader-language').addEventListener('change', renderReader);
byId('reader-lens').addEventListener('change', renderReader);

byId('reader-download')?.addEventListener('click', () => {
  const status = byId('reader-export-status');
  try {
    const selected = window.ReaderPackage.createReaderPackage(state.archiveData, state.readerId, byId('reader-language').value);
    const file = new Blob([`${JSON.stringify(selected, null, 2)}\n`], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(file);
    const link = document.createElement('a');
    link.href = url;
    link.download = window.ReaderPackage.filename(state.readerId, selected.text_layers.map(layer => layer.language_tag));
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    if (status) status.textContent = `Downloaded ${selected.text_layers.length} text layer${selected.text_layers.length === 1 ? '' : 's'} with ${selected.source_records.length} cited source record${selected.source_records.length === 1 ? '' : 's'}. Rights and review limits are included.`;
  } catch (error) {
    if (status) status.textContent = `Reader export failed: ${error.message}`;
  }
});

function renderSources() {
  byId('source-list').innerHTML = state.sources.map(source => `
    <article class="source-card"${source.source_id === 'SRC-000' ? ' id="catalogue-method"' : ` id="source-${escapeHTML(source.source_id.toLowerCase())}"`}><span class="source-kind">${escapeHTML(source.archive_status)}</span><h3>${escapeHTML(source.source_name)}</h3><p>${escapeHTML(source.inspection_and_limitations)}</p>${source.link_status === 'withheld' ? sourceLinkHTML(source, 'External source link withheld') : sourceLinkHTML(source, source.url.startsWith('https://') ? 'Open source' : 'Open archived item')}</article>`).join('');
}

function renderRelated() {
  const sourceById = new Map(state.sources.map(source => [source.source_id, source]));
  byId('related-list').innerHTML = state.related.map(record => {
    const links = record.source_ids.map(id => sourceById.get(id)).filter(Boolean);
    return `<article class="related-card"><span class="related-category">${escapeHTML(record.category)}</span><h3>${escapeHTML(record.title)}</h3>${record.also_known_as ? `<p><strong>Also known as:</strong> ${escapeHTML(record.also_known_as)}</p>` : ''}<p>${escapeHTML(record.description)}</p><p class="related-boundary">${escapeHTML(record.not_canonical_note)}</p><div class="related-links">${links.map(source => sourceLinkHTML(source)).join('')}</div></article>`;
  }).join('');
}

byId('search').addEventListener('input', event => { state.query = event.target.value; renderBooks(); });
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
  state.filter = button.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(item => { const active = item === button; item.classList.toggle('active', active); item.setAttribute('aria-pressed', String(active)); });
  renderBooks();
}));
byId('reset-filters').addEventListener('click', () => { state.query=''; state.filter='All'; byId('search').value=''; document.querySelectorAll('[data-filter]').forEach(item => { const active=item.dataset.filter==='All'; item.classList.toggle('active',active); item.setAttribute('aria-pressed',String(active)); }); renderBooks(); });
document.querySelectorAll('[data-view]').forEach(link => link.addEventListener('click', () => {
  document.querySelectorAll('.nav-link').forEach(item => item.classList.toggle('active', item.dataset.view === link.dataset.view));
}));

byId('archive-export')?.addEventListener('click', event => {
  if (!state.archiveData) return;
  event.preventDefault();
  const file = new Blob([`${JSON.stringify(state.archiveData, null, 2)}\n`], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(file);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'ethiopian-bible-library-archive.json';
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
});

if (window.isSecureContext && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {
      // The archive remains usable online if service-worker storage is unavailable.
    });
  }, { once: true });
}

init();
