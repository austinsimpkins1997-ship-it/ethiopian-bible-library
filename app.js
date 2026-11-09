const state = { archiveData: null, books: [], sources: [], related: [], readers: [], activeReaderData: null, readerLoadSequence: 0, lexicalLensData: null, lexicalLensPromise: null, lexicalLensError: null, canonBooks: [], canonContextSourceIds: [], translationRegistry: null, query: '', filter: 'All', selected: null, chapter: 1, readerId: null };
let refreshOfflineReaderStatus = () => {};
let offlineReaderStatusFor = null;
let bulkReaderSavePlan = null;
let bulkReaderSaveController = null;
function persistReaderSelection(readerId) {
  if (!readerId || location.protocol === 'file:') return;
  const url = new URL(location.href);
  url.searchParams.set('reader', readerId);
  history.replaceState(history.state, '', url);
}
const byId = (id) => document.getElementById(id);
const formatChapterLabel = (reader, item) => {
  const sectionLabel = reader.section_label || 'Chapter';
  return item.source_page_label ? `${sectionLabel} ${item.source_page_label}` : `${sectionLabel} ${item.chapter}`;
};
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
const sourceFileHint = (value) => {
  try {
    const pathname = new URL(value, window.location.href).pathname.toLowerCase();
    const extension = pathname.match(/\.([a-z0-9]+)$/)?.[1];
    const hints = {
      pdf: 'PDF file · may open or download',
      zip: 'ZIP file · downloads',
      xml: 'XML file · may display or download',
      json: 'JSON file · may display or download',
      txt: 'text file · may display or download',
    };
    return hints[extension] ? ` <span class="source-file-hint">(${hints[extension]})</span>` : '';
  } catch { return ''; }
};
const sourceLinkHTML = (source, label = source.source_name) => {
  if (source.link_status === 'withheld') {
    return `<span class="source-link-withheld">${escapeHTML(label)}<small>${escapeHTML(source.link_warning || 'External link withheld pending review.')}</small></span>`;
  }
  const external = /^https:\/\//i.test(source.url);
  const localCopy = source.local_copy_url
    ? `<a href="${escapeHTML(safeURL(source.local_copy_url))}">Open stored facsimile</a> · `
    : '';
  const localRightsCopy = source.local_rights_copy_url
    ? `<a href="${escapeHTML(safeURL(source.local_rights_copy_url))}">View archived rights notice</a> · `
    : '';
  const localOcr = source.local_ocr_url
    ? `<a href="${escapeHTML(safeURL(source.local_ocr_url))}">Open stored OCR (unreviewed)</a> · `
    : '';
  const localMetadata = source.local_metadata_url
    ? `<a href="${escapeHTML(safeURL(source.local_metadata_url))}">View archived source metadata</a> · `
    : '';
  const localSnapshot = source.local_snapshot_path
    ? `<a href="${escapeHTML(safeURL(source.local_snapshot_path))}" download>Download exact captured page bytes</a> · `
    : '';
  const captureManifest = source.local_capture_manifest_url
    ? `<a href="${escapeHTML(safeURL(source.local_capture_manifest_url))}">View capture manifest</a> · `
    : '';
  const snapshotNote = source.local_snapshot_note
    ? `<small>${escapeHTML(source.local_snapshot_note)}</small> · `
    : '';
  const localReview = source.local_review_url
    ? `<a href="${escapeHTML(safeURL(source.local_review_url))}">Read local source review</a> · `
    : '';
  const localFidelityAudit = source.local_fidelity_audit_url
    ? `<a href="${escapeHTML(safeURL(source.local_fidelity_audit_url))}">View verse text fidelity audit</a> · `
    : '';
  const localHeadingAudit = source.local_heading_audit_url
    ? `<a href="${escapeHTML(safeURL(source.local_heading_audit_url))}">View chapter-heading audit</a> · `
    : '';
  const localResearchView = source.local_research_view_url
    ? `<a href="${escapeHTML(safeURL(source.local_research_view_url))}">${escapeHTML(source.local_research_view_label || 'Open supplemental source research view')}</a> · `
    : '';
  const localPackage = source.local_source_package_url
    ? `<a href="${escapeHTML(safeURL(source.local_source_package_url))}" download>Download archived source package</a> · `
    : '';
  const fullViewExternal = source.full_view_url && /^https:\/\//i.test(source.full_view_url);
  const fullView = fullViewExternal
    ? `<a href="${escapeHTML(safeURL(source.full_view_url))}" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer">Open digitized item viewer (access may be restricted) ↗</a> · `
    : '';
  return `${localRightsCopy}${localCopy}${localOcr}${localMetadata}${localSnapshot}${captureManifest}${snapshotNote}${localReview}${localFidelityAudit}${localHeadingAudit}${localResearchView}${localPackage}${fullView}<a href="${escapeHTML(safeURL(source.url))}"${external ? ' target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer"' : ''}>${escapeHTML(label)}${sourceFileHint(source.url)}${hostHint(source.url)} ↗</a>`;
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
    void setupBulkReaderSave();
    const requestedReaderId = new URLSearchParams(location.search).get('reader');
    const requestedReaderIsValid = Boolean(requestedReaderId && state.readers.some(reader => reader.reader_id === requestedReaderId));
    if (requestedReaderIsValid) state.readerId = requestedReaderId;
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
    renderBooks(); renderSources(); renderRelated(); renderCanonCoverage(); renderLanguageCoverage(); renderReader({ loadText: false });
    if (requestedReaderIsValid && !navigator.onLine && navigator.serviceWorker?.controller) {
      await renderReader({ loadText: true });
    }
  } catch (error) {
    byId('results-label').textContent = 'The catalogue could not be loaded.';
    byId('book-grid').innerHTML = `<div class="load-error"><strong>Archive unavailable</strong><p>${escapeHTML(error.message)}. Rebuild the embedded archive from archive.json.</p></div>`;
  }
}

async function setupBulkReaderSave() {
  const button = byId('save-all-readers');
  const status = byId('save-all-readers-status');
  if (!button || !status) return;
  const cancelButton = byId('cancel-save-all-readers');
  button.addEventListener('click', saveAllReaderTexts);
  cancelButton?.addEventListener('click', () => bulkReaderSaveController?.abort());
  try {
    if (!window.OfflineReaderCache) throw new Error('Offline save support is not loaded.');
    const response = await fetch(new URL('archive-manifest.json', location.href), { credentials: 'same-origin' });
    if (!response.ok) throw new Error(`The file-size manifest could not be loaded (HTTP ${response.status}).`);
    const manifest = await response.json();
    bulkReaderSavePlan = window.OfflineReaderCache.createPlan(state.readers, manifest);
    button.textContent = `Save all ${bulkReaderSavePlan.count} reader texts offline (${window.OfflineReaderCache.formatMiB(bulkReaderSavePlan.totalBytes)})`;
    button.disabled = false;
    status.textContent = 'Optional: save the bundled reader files on this device for later offline reading. Browser storage can be cleared or evicted.';
  } catch (error) {
    button.textContent = 'Offline reader download unavailable';
    status.textContent = `${error.message} Open this site over HTTPS or through START_LOCAL.bat; file:// pages cannot save the reader collection.`;
  }
}

async function saveAllReaderTexts() {
  const button = byId('save-all-readers');
  const cancelButton = byId('cancel-save-all-readers');
  const progress = byId('save-all-readers-progress');
  const status = byId('save-all-readers-status');
  if (!bulkReaderSavePlan || !button || !status || bulkReaderSaveController) return;
  if (!navigator.onLine) {
    status.textContent = 'Reconnect to the internet before saving the reader collection.';
    return;
  }
  if (!window.isSecureContext || !('serviceWorker' in navigator) || !('caches' in window)) {
    status.textContent = 'This browser does not support secure offline storage for the reader collection.';
    return;
  }
  button.disabled = true;
  status.textContent = 'Checking which reader files are already saved…';
  try {
    await navigator.serviceWorker.ready;
    if (!navigator.serviceWorker.controller) {
      await new Promise((resolve, reject) => {
        const timeout = window.setTimeout(() => reject(new Error('The offline worker is not controlling this page yet. Reload once, then try again.')), 8000);
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          window.clearTimeout(timeout);
          resolve();
        }, { once: true });
      });
    }
    if (!navigator.serviceWorker.controller) throw new Error('The offline worker is not active. Reload once, then try again.');
    const baseUrl = new URL('./', location.href).href;
    const current = await window.OfflineReaderCache.inspect(bulkReaderSavePlan, { baseUrl, cacheStorage: caches });
    if (!current.remainingCount) {
      status.textContent = `All ${bulkReaderSavePlan.count} reader files are already saved in this browser cache. The browser may still clear them later.`;
      return;
    }
    let spaceNotice = '';
    try {
      const estimate = await navigator.storage?.estimate?.();
      if (Number.isFinite(estimate?.quota) && Number.isFinite(estimate?.usage)) {
        const available = Math.max(0, estimate.quota - estimate.usage);
        if (available < current.remainingBytes) {
          spaceNotice = ` The browser estimates ${(available / (1024 * 1024)).toFixed(1)} MiB available, less than the ${window.OfflineReaderCache.formatMiB(current.remainingBytes)} still needed.`;
        }
      }
    } catch { /* Storage estimates are optional and not supported everywhere. */ }
    const prompt = `Save ${current.remainingCount} remaining reader files (${window.OfflineReaderCache.formatMiB(current.remainingBytes)}) for offline use? ${current.cachedCount} are already cached.${spaceNotice} The browser may refuse, clear, or evict cached files; you can cancel, and already saved files remain usable.`;
    if (!window.confirm(prompt)) {
      status.textContent = 'Offline save cancelled before downloading. Existing cached readers are unchanged.';
      return;
    }
    bulkReaderSaveController = new AbortController();
    if (cancelButton) cancelButton.hidden = false;
    if (progress) {
      progress.hidden = false;
      progress.max = bulkReaderSavePlan.count;
      progress.value = current.cachedCount;
      progress.setAttribute('aria-valuetext', `${current.cachedCount} of ${bulkReaderSavePlan.count} reader files saved`);
    }
    status.textContent = `Saving reader files: ${current.cachedCount} of ${bulkReaderSavePlan.count} already cached.`;
    const result = await window.OfflineReaderCache.save(bulkReaderSavePlan, {
      baseUrl,
      cacheStorage: caches,
      signal: bulkReaderSaveController.signal,
      onProgress: update => {
        if (progress) {
          progress.value = update.completed;
          progress.setAttribute('aria-valuetext', `${update.completed} of ${update.total} reader files saved`);
        }
        if (update.completed === update.total || update.completed % 20 === 0) {
          status.textContent = `Saving reader files: ${update.completed} of ${update.total} (${window.OfflineReaderCache.formatMiB(update.completedBytes)} saved).`;
        }
      },
    });
    status.textContent = `Offline save complete: ${result.completed} of ${result.total} reader files confirmed in this browser cache (${window.OfflineReaderCache.formatMiB(result.completedBytes)}). The browser may later clear or evict cached files.`;
  } catch (error) {
    status.textContent = error.name === 'AbortError'
      ? 'Offline save cancelled. Files already saved remain available; you can resume later.'
      : `Offline save stopped: ${error.message} Files already saved remain available; you can resume later.`;
  } finally {
    bulkReaderSaveController = null;
    button.disabled = false;
    if (cancelButton) cancelButton.hidden = true;
    refreshOfflineReaderStatus();
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

function sourceRightsNote(source) {
  const category = source.rights_classification
    ? `Recorded category: ${rightsClassificationLabel(source.rights_classification)}. `
    : 'Structured rights category: not recorded. ';
  const notice = source.rights_status
    ? `Recorded terms: ${source.rights_status}`
    : 'No item-specific reuse terms are recorded in the structured rights fields. A citation is not a reuse license.';
  const basis = source.rights_basis
    ? `Rights evidence basis: ${source.rights_basis}`
    : 'Rights evidence basis: not recorded.';
  return `<details class="source-rights-note"><summary>Rights and reuse</summary><p>${escapeHTML(`${category}${notice} ${basis} Rights for any bundled reader text or media are documented separately.`)}</p></details>`;
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
  const canonLinkedLayerCount = bundledLayers.filter(record => {
    const reader = layerReader(record);
    return Boolean(reader?.canon_id && !reader.research_corpus_id && reader.canon_id === record.canon_id);
  }).length;
  const pathLanguagePairs = bundledLayers.filter(record => ['translation', 'historical_companion_translation', 'draft_translation'].includes(record.layer_role) && record.translation_path?.length === 2 && record.translation_path[0] !== 'und').length;
  const corpusLeads = registry?.corpus_leads || [];
  const corpusLeadLanguages = new Set(corpusLeads.map(lead => lead.language_tag)).size;
  const researchCorpora = registry?.research_corpora || [];
  const researchTranslationRecords = researchCorpora.filter(corpus => corpus.reader_status === 'bundled_research_reader' && corpus.text_origin === 'published_translation');
  const researchTranslationsWithKnownPath = researchTranslationRecords.filter(corpus => corpus.translation_basis_status === 'established').length;
  const researchTranslationsWithUnknownPath = researchTranslationRecords.filter(corpus => corpus.translation_basis_status === 'unknown').length;
  const researchLanguageCount = new Set(researchCorpora.map(corpus => corpus.language_tag).filter(Boolean)).size;
  const bundledSourceCanonIds = new Set(bundledLayers.filter(record => ['source_text_transcription', 'source_text_edition'].includes(record.layer_role)).map(record => record.canon_id).filter(Boolean));
  const availableCanonEntries = state.canonBooks.filter(book => bundledSourceCanonIds.has(book.canon_id)
    && state.readers.some(reader => reader.canon_id === book.canon_id
      && (!book.reader_id || reader.reader_id === book.reader_id))).length;
  const researchCandidateCanonIds = new Set(researchCorpora
    .filter(corpus => corpus.candidate_canon_id
      && state.readers.some(reader => reader.reader_id === corpus.reader_id && reader.research_corpus_id))
    .map(corpus => corpus.candidate_canon_id));
  const researchOnlyEntryCount = state.canonBooks.filter(book => !bundledSourceCanonIds.has(book.canon_id)
    && researchCandidateCanonIds.has(book.canon_id)).length;
  const researchReaderCount = state.readers.filter(reader => reader.research_corpus_id).length;
  const researchReaderLabel = researchReaderCount === 1 ? 'research reader' : 'research readers';
  byId('language-coverage-summary').textContent = `Registered source/translation layers: ${readerLanguages.length} of ${languages.length} language/script profiles · ${canonLinkedLayerCount} canon-linked text layers · ${researchReaderCount} separately scoped ${researchReaderLabel} across ${researchLanguageCount} profiles (not canon-linked) · ${pathLanguagePairs} two-language paths in registered layers · ${researchTranslationsWithKnownPath} of ${researchTranslationRecords.length} bundled research translations have an established path; ${researchTranslationsWithUnknownPath} have unknown basis · ${corpusLeadLanguages} languages with unbundled corpus leads`;
  const neitherReaderTypeEntryCount = state.canonBooks.length - availableCanonEntries - researchOnlyEntryCount;
  if (integrityNote) integrityNote.textContent = `Measured from records in this bundled snapshot: ${availableCanonEntries} of ${state.canonBooks.length} Church-listed entries have canon-linked source-text readers; ${researchOnlyEntryCount} additional entries have separately bundled research readers with unverified Church-list links; ${neitherReaderTypeEntryCount} have neither type of reader bundled here. These counts describe this package, not worldwide availability, completeness, accuracy, or review status. Absence from the package means “not bundled here.” Zero is reserved for a defined, completed survey that found none; unassessed scope and viewpoints remain “not surveyed” or “unknown,” never zero by default. Machine-generated wording may appear only as a labeled draft and is never counted or presented as verified scripture or translation.`;
  byId('language-coverage-statement').textContent = registry?.coverage_statement || 'Language coverage is not available.';
  byId('language-coverage-list').innerHTML = languages.map(language => {
    const records = language.records.filter(record => record.status === 'bundled');
    const languageResearchCorpora = researchCorpora.filter(corpus => corpus.language_tag === language.language_tag);
    const items = records.map(record => {
      const role = record.layer_role === 'source_text_transcription' ? 'Source-text transcription' : record.layer_role === 'source_text_edition' ? 'Source-text edition (encoded transcription)' : record.layer_role === 'historical_companion_translation' ? 'Historical companion translation' : record.layer_role;
      const path = record.translation_path || [];
      const basis = record.basis_language_tag === language.language_tag ? 'Source text in this language' : path.length ? `Path: ${path.map(languageLabel).map(escapeHTML).join(' → ')}` : `Basis language: ${escapeHTML(record.basis_language_tag)}`;
      const reader = state.readers.find(item => item.reader_id === record.reader_id);
      const corpus = registry?.research_corpora?.find(item => item.reader_id === record.reader_id);
      const researchOnly = Boolean(reader?.research_corpus_id || corpus);
      const mappedCanonId = record.canon_id || corpus?.candidate_canon_id;
      const candidate = mappedCanonId ? state.canonBooks.find(book => book.canon_id === mappedCanonId) : null;
      const title = candidate?.display_name || mappedCanonId || 'Unmapped text';
      const mappingLabel = corpus?.canon_mapping_state === 'reviewed_match'
        ? 'reviewed work/title match'
        : corpus?.canon_mapping_state === 'asserted_by_source'
          ? 'source explicitly identifies title'
          : corpus?.canon_mapping_state === 'uncertain'
            ? 'provisional title candidate'
            : 'not assigned';
      const identity = researchOnly
        ? `Research witness: ${escapeHTML(title)} · ${escapeHTML(mappingLabel)}; tradition and edition identity remain separate`
        : escapeHTML(title);
      const textLayer = record.translation_id ? reader?.parallel_translation || (researchOnly ? reader : null) : reader;
      const review = textLayer?.verification_status ? `<details class="language-review"><summary>Review status</summary><p>${escapeHTML(textLayer.verification_status)}</p></details>` : '';
      return `<li><strong>${identity}</strong><span>${escapeHTML(role)}</span><small>${basis}</small>${review}</li>`;
    }).join('');
    const scriptNames = { Arab: 'Arabic', Ethi: 'Ethiopic', Latn: 'Latin' };
    const recordedScriptCodes = Array.isArray(language.script_codes) ? language.script_codes : [language.script_code];
    const citedScripts = recordedScriptCodes
      .filter(code => code && code !== 'Zzzz')
      .map(code => `${scriptNames[code] || code} (${code})`);
    const scriptEvidence = citedScripts.length
      ? `scripts in cited evidence: ${citedScripts.join(', ')}`
      : 'script not established';
    const scriptDefault = language.script_code === 'Zzzz'
      ? 'language-level default not established'
      : `profile default: ${scriptNames[language.script_code] || language.script_code}`;
    const direction = language.direction === 'unknown' ? 'direction unknown' : language.direction;
    const description = language.script_profile_note ? `<p class="language-profile-note">${escapeHTML(language.script_profile_note)}</p>` : '';
    const researchItems = languageResearchCorpora.map(corpus => {
      const reader = state.readers.find(item => item.reader_id === corpus.reader_id);
      const title = reader?.source_title_label || corpus.title;
      return `<li><strong>${escapeHTML(title)}</strong><small>${escapeHTML(corpus.unit_summary || 'Source-defined research reader; extent and completeness are not independently established.')}</small><button class="reader-open-research" type="button" data-reader-id="${escapeHTML(corpus.reader_id)}">Open stored text</button></li>`;
    }).join('');
    const researchReaderList = researchItems
      ? `<details class="language-research-readers"><summary>${languageResearchCorpora.length} separately scoped research reader${languageResearchCorpora.length === 1 ? '' : 's'} · not canon-linked</summary><ul>${researchItems}</ul></details>`
      : '';
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
    const contents = items || (languageResearchCorpora.length
      ? '<li>No canon-linked source-text or translation layer is registered here. Separately scoped research readers are listed below.</li>'
      : '<li>No text for this language is bundled in this archive. This does not establish whether texts exist elsewhere; see separately recorded leads.</li>');
    const writingMode = language.writing_mode ? ` · writing mode ${escapeHTML(language.writing_mode)}` : '';
    return `<article class="language-card"><div class="language-card-heading"><h3>${escapeHTML(language.language_name)}</h3><span lang="en">${escapeHTML(language.language_tag)} · ${escapeHTML(scriptEvidence)} · ${escapeHTML(scriptDefault)} · ${escapeHTML(direction)}${writingMode}</span></div>${surveyNote}<ul>${contents}</ul>${researchReaderList}${description}${sourceDetails}</article>`;
  }).join('');
  const leads = registry?.translation_leads || [];
  const sourceLinks = ids => ids.map(id => state.sources.find(source => source.source_id === id)).filter(Boolean).map(source => sourceLinkHTML(source)).join(' · ');
  const translationHtml = leads.length ? `<h3>Book translation leads · not bundled</h3>${leads.map(lead => {
    const candidate = state.canonBooks.find(book => book.canon_id === lead.canon_id);
    const mappingDescription = lead.mapping_state === 'reviewed_match'
      ? `Reviewed work/title match: ${escapeHTML(candidate?.display_name || lead.canon_id)}; edition identity and text quality remain separate questions.`
      : lead.mapping_state === 'asserted_by_source'
        ? `A cited source asserts a title link to ${escapeHTML(candidate?.display_name || lead.canon_id)}; independent text review remains incomplete.`
        : lead.mapping_state === 'related_work'
          ? `Related work only; not a crosswalk to ${escapeHTML(candidate?.display_name || lead.canon_id)}.`
          : `Provisional catalogue candidate: ${escapeHTML(candidate?.display_name || lead.canon_id)}; the work relationship remains uncertain.`;
    const path = lead.translation_path
      ? lead.translation_path.map(languageLabel).map(escapeHTML).join(' → ')
      : 'translation path unknown';
    return `<article class="translation-lead"><strong>${escapeHTML(lead.title || lead.edition)}</strong><p>${escapeHTML(lead.edition)}</p><p>${mappingDescription} · mapping status: ${escapeHTML(lead.mapping_state)}</p><p>${escapeHTML(lead.translator)} · ${path}</p><p>${escapeHTML(lead.scope_description)}</p><p>${escapeHTML(lead.review_status)}</p><details><summary>Bibliographic notes</summary><p>${escapeHTML(lead.notes)}</p></details><small>${rightsNote(lead)} · ${sourceLinks(lead.source_ids || [])}</small></article>`;
  }).join('')}` : '';
  const editionLeads = registry?.edition_leads || [];
  const editionHtml = editionLeads.length ? `<h3>Book source-edition leads · not bundled</h3>${editionLeads.map(lead => {
    const candidate = state.canonBooks.find(book => book.canon_id === lead.candidate_canon_id);
    const mappingDescription = lead.mapping_state === 'related_work'
      ? `Related Church-list entry (not a crosswalk): ${escapeHTML(candidate?.display_name || lead.candidate_canon_id)}`
      : lead.mapping_state === 'not_mapped'
        ? 'No Church-list crosswalk assigned'
        : `Candidate catalogue link: ${escapeHTML(candidate?.display_name || lead.candidate_canon_id)}`;
    return `<article class="translation-lead edition-lead"><strong>${escapeHTML(lead.title)}</strong><p>${escapeHTML(lead.edition_statement)}</p><p>${mappingDescription} · mapping ${escapeHTML(lead.mapping_state)} · ${escapeHTML(lead.language_name)} (${escapeHTML(lead.language_tag)}, ${escapeHTML(lead.script_code)})</p><p>${escapeHTML(lead.scope_description)}</p><p>${escapeHTML(lead.review_status)}</p><small>${rightsNote(lead)} · ${sourceLinks(lead.source_ids || [])}</small></article>`;
  }).join('')}` : '';
  const corpusHtml = corpusLeads.length ? `<h3>Multi-book language/corpus leads · not bundled</h3>${corpusLeads.map(lead => {
    const basis = lead.basis_language_tag === 'und' ? 'source language unknown' : `basis ${escapeHTML(languageLabel(lead.basis_language_tag))}`;
    return `<article class="translation-lead"><strong>${escapeHTML(lead.title)}</strong><p>${escapeHTML(lead.publisher)} · ${escapeHTML(lead.publication_year)} · ${escapeHTML(lead.language_name)} (${escapeHTML(lead.language_tag)}, script ${escapeHTML(lead.script_code)}${lead.script_status ? ` · ${escapeHTML(lead.script_status)} for this witness` : ''}) · ${lead.translation_path ? lead.translation_path.map(languageLabel).map(escapeHTML).join(' → ') : 'translation path unknown'} · ${basis}</p><p>${escapeHTML(lead.scope_description)}</p><p>${escapeHTML(lead.contributors)} ${escapeHTML(lead.review_status)}</p><p>${escapeHTML(lead.notes)}</p><small>${rightsNote(lead)} · ${sourceLinks(lead.source_ids || [])}</small></article>`;
  }).join('')}` : '';
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
  const archive = state.archiveData;
  const registry = archive.canon_registry;
  const translationRegistry = archive.translation_registry;
  // Report reader availability from reader records actually embedded in this build,
  // not from a display label that could become stale.
  const readerForCanon = book => state.readers.find(reader => reader.canon_id === book.canon_id
    && (!book.reader_id || reader.reader_id === book.reader_id));
  const available = state.canonBooks.filter(book => readerForCanon(book)).length;
  const linkedReaderRecords = [...new Map(
    state.canonBooks.map(readerForCanon).filter(Boolean).map(reader => [reader.reader_id, reader])
  ).values()];
  const linkedRightsCounts = linkedReaderRecords.reduce((counts, reader) => {
    const classification = reader.rights_classification || 'unknown';
    counts[classification] = (counts[classification] || 0) + 1;
    return counts;
  }, {});
  const linkedRightsSummary = [
    `open license ${linkedRightsCounts.open_license || 0}`,
    `permission limited ${linkedRightsCounts.permission_limited || 0}`,
    `public domain claimed ${linkedRightsCounts.public_domain_claimed || 0}`,
    `all rights reserved ${linkedRightsCounts.all_rights_reserved || 0}`,
    `mixed or unresolved ${linkedRightsCounts.mixed || 0}`,
    `unknown ${linkedRightsCounts.unknown || 0}`,
  ].join('; ');
  byId('canon-coverage-summary').textContent = `${available} of ${state.canonBooks.length} Church-listed entries have canon-linked reader text`;
  const notCanonLinked = state.canonBooks.length - available;
  const hasCandidateCanonLink = record => !['related_work', 'not_mapped'].includes(record.mapping_state || record.canon_mapping_state);
  const candidateCanonIds = new Set([
    ...(translationRegistry.translation_leads || []),
    ...(translationRegistry.edition_leads || []),
    ...(translationRegistry.corpus_leads || []),
    ...(translationRegistry.research_corpora || [])
  ].filter(record => hasCandidateCanonLink(record)).map(record => record.candidate_canon_id).filter(Boolean));
  const candidateEntryCount = state.canonBooks.filter(book => !readerForCanon(book) && candidateCanonIds.has(book.canon_id)).length;
  const researchReaderCanonIds = new Set((translationRegistry.research_corpora || [])
    .filter(corpus => hasCandidateCanonLink(corpus) && corpus.candidate_canon_id && candidateCanonIds.has(corpus.candidate_canon_id)
      && state.readers.some(reader => reader.reader_id === corpus.reader_id && reader.research_corpus_id))
    .map(corpus => corpus.candidate_canon_id));
  const bundledResearchEntryCount = state.canonBooks.filter(book => !readerForCanon(book) && researchReaderCanonIds.has(book.canon_id)).length;
  const unlinkedCandidateCount = notCanonLinked - candidateEntryCount;
  const coverageNote = document.querySelector('.canon-coverage-method');
  if (coverageNote) coverageNote.textContent = `Measured from the actual reader records in this bundled snapshot: ${available} of ${state.canonBooks.length} listed entries have a canon-linked reader. Rights classifications for those linked reader records: ${linkedRightsSummary}. The repository software license and metadata license apply only to their stated material; each scripture reader carries its own item-specific reuse notice. ${notCanonLinked} entries have no canon-linked reader here; ${bundledResearchEntryCount} of those have at least one separately bundled research reader surfaced from the catalogue. ${candidateEntryCount} unlinked entries have at least one title-linked candidate record and ${unlinkedCandidateCount} have no such candidate recorded in this registry snapshot. Candidate records are research or bibliographic leads; they do not establish that usable text is available, confirm an exact canon mapping, or prove accuracy, completeness, rights, or review. No candidate recorded here does not mean no source exists elsewhere. These observed package counts do not estimate worldwide availability. “Not canon-linked here” describes this package only. A zero is valid only after a defined, completed survey finds none; unassessed availability and viewpoints stay “not surveyed” or “unknown,” never zero by default. Entries with canon-linked bundled text go to the reader. Related research readers and supplemental source views can be opened from a book card or catalogue record; source views are not reader packages, and neither kind increases the canon-linked count. Grouped titles stay grouped as the Church list gives them; unresolved crosswalks are marked in the catalogue. Machine-generated wording may appear only as a labeled draft; it never contributes to coverage counts or appears as verified scripture or translation.`;
  const contextSources = (registry.context_source_ids || []).map(id => state.sources.find(source => source.source_id === id)).filter(Boolean);
  byId('canon-coverage-context').innerHTML = `<p>${escapeHTML(registry.scholarly_context || 'No comparative canon context has been recorded.')}</p>${contextSources.length ? `<p class="canon-context-sources">Context sources: ${contextSources.map(source => sourceLinkHTML(source)).join(' · ')}</p>` : ''}`;
  const sections = ['Old Testament', 'New Testament'];
  byId('canon-coverage-list').innerHTML = sections.map(section => {
    const books = state.canonBooks.filter(book => book.section === section);
    return `<div class="canon-coverage-group"><h3>${escapeHTML(section)} <span>${books.length}</span></h3><div class="canon-coverage-grid">${books.map(book => {
      const reader = readerForCanon(book);
      const hasReader = Boolean(reader);
      const researchReaders = (translationRegistry.research_corpora || [])
        .filter(corpus => hasCandidateCanonLink(corpus) && corpus.candidate_canon_id === book.canon_id)
        .map(corpus => ({
          corpus,
          reader: state.readers.find(item => item.reader_id === corpus.reader_id),
          language: (translationRegistry.languages || []).find(item => item.language_tag === corpus.language_tag)?.language_name
            || corpus.language_tag || 'language not recorded',
        }))
        .filter(item => item.reader?.research_corpus_id);
      const hasSourceAssertedResearchLink = researchReaders.some(({corpus}) => corpus.canon_mapping_state === 'asserted_by_source');
      const hasReviewedResearchTitleMatch = researchReaders.some(({corpus}) => corpus.canon_mapping_state === 'reviewed_match');
      const status = hasReader
        ? (String(book.reader_status || '').startsWith('Bundled:') ? book.reader_status : `Reader bundled: ${reader.language_tag || 'language recorded in reader metadata'}`)
        : researchReaders.length
          ? hasReviewedResearchTitleMatch
            ? 'A work/title match is archive-reviewed; the translation remains a separate research witness, not a verified EOTC edition'
            : hasSourceAssertedResearchLink
            ? 'A cited source asserts a work/title link; readers remain research-only'
            : 'Related research text available; canon link unverified — see its reader button'
          : (String(book.reader_status || '').startsWith('Bundled:') ? 'Reader record unavailable; coverage needs repair' : book.reader_status);
      const linkedLeads = [
        ...(translationRegistry.translation_leads || []),
        ...(translationRegistry.edition_leads || []),
        ...(translationRegistry.corpus_leads || []),
      ].filter(lead => (lead.candidate_canon_id || lead.canon_id) === book.canon_id);
      const sourceIdsForBook = new Set([
        ...(book.source_ids || []),
        ...linkedLeads.flatMap(lead => lead.source_ids || []),
      ]);
      const supplementalViews = state.sources
        .filter(source => sourceIdsForBook.has(source.source_id) && source.local_research_view_url)
        .map(source => `<a class="canon-entry-research" href="${escapeHTML(safeURL(source.local_research_view_url))}" aria-label="Open supplemental source research view for ${escapeHTML(book.display_name)}: ${escapeHTML(source.source_name)}. This is not a verified reader.">Open source research view · ${escapeHTML(source.source_name)} <small>(not a reader)</small></a><span class="canon-entry-view-note">${escapeHTML(source.archive_status || 'Supplemental research view; not counted as reader coverage.')}</span>`)
        .join('');
      const researchActions = researchReaders.map(({corpus, language}) => {
        const assertionLabel = corpus.canon_mapping_state === 'reviewed_match'
          ? ' Reviewed work/title match only. Tradition affiliation, exact edition, completeness, and translation accuracy remain unverified.'
          : corpus.canon_mapping_state === 'asserted_by_source'
            ? ' Source-asserted title link; edition identity, completeness, and accuracy remain unverified.'
            : ' This text is a research witness; its title mapping is not verified.';
        const assertionBadge = corpus.canon_mapping_state === 'reviewed_match'
          ? ' · reviewed title match'
          : corpus.canon_mapping_state === 'asserted_by_source'
            ? ' · source-asserted link'
            : '';
        return `<button class="canon-entry-research" type="button" data-canon-research-reader="${escapeHTML(corpus.reader_id)}" aria-label="Open related research reader: ${escapeHTML(corpus.title)}.${escapeHTML(assertionLabel)}">Open ${escapeHTML(language)} · ${escapeHTML(corpus.title)}${assertionBadge}</button>`;
      }).join('');
      const observedStructure = hasReader && Number.isInteger(reader.chapter_count) && Number.isInteger(reader.unit_count)
        ? `<span class="canon-entry-observed">Observed: ${reader.chapter_count} chapters · ${reader.unit_count.toLocaleString()} ${escapeHTML(reader.unit_label || 'source units')}</span>`
        : '';
      const sourceLabel = book.source_label && book.source_label !== book.display_name ? `<span class="canon-entry-source-label">Church list: ${escapeHTML(book.source_label)}</span>` : '';
      const mappingNote = book.mapping_note ? `<span class="canon-entry-mapping-note">${escapeHTML(book.mapping_note)}</span>` : '';
      const verificationDetails = hasReader && reader.verification_status
        ? `<details class="canon-entry-verification"><summary>Extent and checks</summary><p>${escapeHTML(reader.verification_status)}</p></details>`
        : '';
      return `<div class="canon-entry-card"><button class="canon-entry${hasReader ? ' canon-entry-ready' : ''}" type="button" data-canon-entry="${escapeHTML(book.canon_id)}"><span class="canon-entry-number">${book.section_number}</span><span class="canon-entry-title">${escapeHTML(book.display_name)}</span>${sourceLabel}<span class="canon-entry-status">${escapeHTML(status)}</span>${observedStructure}${mappingNote}</button>${verificationDetails}${researchActions}${supplementalViews}</div>`;
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
  document.querySelectorAll('[data-canon-research-reader]').forEach(button => button.addEventListener('click', () => {
    const reader = state.readers.find(item => item.reader_id === button.dataset.canonResearchReader && item.research_corpus_id);
    if (!reader) return;
    state.readerId = reader.reader_id;
    state.chapter = 1;
    location.hash = 'reader';
    renderReader();
    byId('reader').scrollIntoView({ behavior: 'smooth' });
  }));
  if (!registry || registry.book_count !== 81) throw new Error('The Church-list coverage index is incomplete.');
}

function filteredBooks() {
  const q = state.query.trim().toLocaleLowerCase();
  return state.books.filter(book => (state.filter === 'All' || book.tradition_group === state.filter)
    && (!q || [book.display_name, book.alternate_names_or_notes, book.tradition_group, book.identity_status].join(' ').toLocaleLowerCase().includes(q)));
}

function catalogueReaderContext(book) {
  const canonEntries = state.canonBooks.filter(entry => (entry.catalogue_ids || []).includes(book.catalogue_id));
  const reader = state.readers.find(item => canonEntries.some(entry => entry.reader_id === item.reader_id));
  const canonIds = canonEntries.map(entry => entry.canon_id);
  const corpora = state.translationRegistry?.research_corpora || [];
  const candidateReaderIds = new Set(corpora
    .filter(corpus => canonIds.includes(corpus.candidate_canon_id)
      && !['related_work', 'not_mapped'].includes(corpus.canon_mapping_state))
    .map(corpus => corpus.reader_id));
  const title = String(book.display_name || '').trim().toLocaleLowerCase();
  const matchesTitle = item => {
    if (String(item.normalized_title_en || '').trim().toLocaleLowerCase() === title) return true;
    return [item.display_name, item.title].some(value => {
      const candidate = String(value || '').trim().toLocaleLowerCase();
      return [' —', ' –', ' -', ' (', ' ·'].some(separator => candidate.startsWith(`${title}${separator}`));
    });
  };
  const researchReaders = state.readers.filter(item => item.research_corpus_id
    && item.reader_id !== reader?.reader_id
    && (candidateReaderIds.has(item.reader_id) || matchesTitle(item)));
  return { reader, researchReaders, corpora };
}

function renderBooks() {
  const books = filteredBooks();
  byId('results-label').textContent = `Showing ${books.length} of ${state.books.length} records`;
  byId('reset-filters').hidden = !state.query && state.filter === 'All';
  byId('empty-state').hidden = books.length > 0;
  byId('book-grid').innerHTML = books.map(book => {
    const { reader, researchReaders } = catalogueReaderContext(book);
    const status = !reader && researchReaders.length
      ? `Related research readers stored (${researchReaders.length}) · canon link unverified`
      : book.text_availability_status;
    return `
      <button class="book-card${state.selected === book.catalogue_id ? ' selected' : ''}" data-book="${escapeHTML(book.catalogue_id)}" aria-pressed="${state.selected === book.catalogue_id}">
        <span class="book-number">${escapeHTML(book.catalogue_id.replace('eotc-',''))}</span>
        <h3>${escapeHTML(book.display_name)}</h3>
        <span class="card-footer"><span class="mini-tag">${escapeHTML(book.tradition_group)}</span><span class="mini-tag"><i class="status-dot"></i>${escapeHTML(status)}</span></span>
      </button>`;
  }).join('');
  document.querySelectorAll('[data-book]').forEach(button => button.addEventListener('click', () => selectBook(button.dataset.book)));
}

function selectBook(id) {
  state.selected = id;
  const book = state.books.find(item => item.catalogue_id === id);
  if (!book) return;
  renderBooks();
  const source = state.sources.find(item => item.source_id === book.source_id);
  const evidence = (book.evidence_source_ids || []).map(id => state.sources.find(item => item.source_id === id)).filter(Boolean);
  const { reader, researchReaders: relatedResearchReaders, corpora: researchCorpora } = catalogueReaderContext(book);
  const relatedCanonEntries = state.canonBooks.filter(entry => (entry.catalogue_ids || []).includes(book.catalogue_id));
  const relatedCanonIds = relatedCanonEntries.map(entry => entry.canon_id);
  const researchCorpusFor = item => researchCorpora.find(corpus => corpus.reader_id === item.reader_id);
  const editionLeads = (state.translationRegistry?.edition_leads || []).filter(lead => relatedCanonIds.includes(lead.candidate_canon_id));
  if (reader) state.readerId = reader.reader_id;
  const readerLink = reader
    ? `<a class="button button-gold detail-reader-link" href="#reader">Open the locally stored ${escapeHTML(reader.language)} reader ↓</a><p class="detail-warning">Reader edition: ${escapeHTML(reader.edition)}. Verification: ${escapeHTML(reader.verification_status)} The reader panel records its source and remaining limits.</p>`
    : relatedResearchReaders.length
      ? '<p class="detail-warning">No canon-linked reader is bundled for this catalogue title. Other stored readers with a matching title or candidate catalogue link are listed below; these links do not verify work identity or canon mapping.</p>'
      : '<p class="detail-warning">No source-text reader is bundled for this title in this archive snapshot. This describes the local package only; any known source leads and their limits are listed above.</p>';
  const localResearchViews = (book.local_research_views || []).filter(view =>
    view && typeof view.title === 'string' && typeof view.path === 'string' && safeURL(view.path) !== '#'
  );
  const localResearchViewHtml = localResearchViews.length
    ? `<section class="translation-leads local-research-views"><h3>Local research views</h3>${localResearchViews.map(view => `<article class="translation-lead"><strong>${escapeHTML(view.title)}</strong><p>${escapeHTML(view.scope_note || 'Research material; review its scope and limits before treating it as a reader.')}</p><a class="button button-gold" href="${escapeHTML(safeURL(view.path))}">${escapeHTML(view.link_label || 'Open research view')}</a></article>`).join('')}</section>`
    : '';
  const relatedResearchHtml = relatedResearchReaders.length ? `<section class="translation-leads related-reader-leads"><h3>Other stored readers · related by title or candidate link</h3><p>These are separately sourced texts. A shared English title or catalogue candidate does not prove the same work, edition, canon, wording, or verse alignment.</p>${relatedResearchReaders.map(item => {
    const corpus = researchCorpusFor(item);
    const extent = corpus?.unit_summary || `${item.chapter_count || 'Unknown'} chapters · ${item.unit_count || 'Unknown'} source units`;
    const note = corpus?.canon_mapping_note || item.edition_scope || 'No additional mapping or review note is recorded.';
    return `<article class="translation-lead related-reader"><strong>${escapeHTML(item.display_name || item.title)}</strong><p>${escapeHTML(item.language || item.language_tag || 'Language not recorded')} · ${escapeHTML(extent)}</p><p>${escapeHTML(note)}</p><button class="reader-open-research" type="button" data-reader-id="${escapeHTML(item.reader_id)}">Open this reader</button></article>`;
  }).join('')}</section>` : '';
  const link = item => sourceLinkHTML(item);
  const editionLeadHtml = editionLeads.length ? `<section class="translation-leads edition-leads"><h3>Source edition leads · not bundled as reader text</h3>${editionLeads.map(lead => {
    const leadSources = (lead.source_ids || []).map(sourceId => state.sources.find(item => item.source_id === sourceId)).filter(Boolean);
    return `<article class="translation-lead edition-lead"><strong>${escapeHTML(lead.title)}</strong><p>${escapeHTML(lead.edition_statement)}</p><p>Mapping status: ${escapeHTML(lead.mapping_state)} · ${escapeHTML(lead.witness_type)}</p><p>${escapeHTML(lead.scope_description)}</p><p>${escapeHTML(lead.review_status)}</p><small>${rightsNote(lead)}</small><ul>${leadSources.map(item => `<li>${link(item)}<br><small>${escapeHTML(item.inspection_and_limitations || '')}</small></li>`).join('') || '<li>No source records linked.</li>'}</ul></article>`;
  }).join('')}</section>` : '';
  const chapterCount = /^\d+$/.test(String(book.chapter_count || '')) ? `${escapeHTML(book.chapter_count)} chapters` : escapeHTML(book.chapter_count || 'Not established');
  const catalogueMappingNote = book.canon_view || 'No Church-list mapping has been recorded for this catalogue row.';
  const canonMappingHtml = relatedCanonEntries.length
    ? relatedCanonEntries.map(entry => `${escapeHTML(entry.display_name)}: ${escapeHTML(entry.mapping_note || catalogueMappingNote)}`).join('<br>')
    : escapeHTML(catalogueMappingNote);
  byId('detail-panel').innerHTML = `
    <div class="detail-top"><div><span class="detail-index">${escapeHTML(book.catalogue_id)} · ${escapeHTML(book.tradition_group)}</span><h3>${escapeHTML(book.display_name)}</h3></div><button class="detail-close" aria-label="Close details">×</button></div>
    <span class="detail-status">${escapeHTML(book.identity_status)}</span>
    <dl class="detail-meta"><dt>Alternate names &amp; notes</dt><dd>${escapeHTML(book.alternate_names_or_notes || 'Alternate names not yet researched.')}</dd><dt>Church-list mapping</dt><dd>${canonMappingHtml}</dd><dt>Edition / translation</dt><dd>${escapeHTML(book.edition_or_translation || 'Not identified')}</dd><dt>Chapter count</dt><dd>${chapterCount}</dd><dt>Chapter order</dt><dd>${escapeHTML(book.chapter_order_status || 'Not researched')}</dd><dt>Text &amp; completeness</dt><dd>${escapeHTML(book.text_availability_status || 'Not researched')} · ${escapeHTML(book.completeness_status || 'Not assessed')}</dd><dt>Reuse rights</dt><dd>${escapeHTML(book.rights_status || 'Not assessed; no edition selected')}</dd><dt>Catalogue custodian</dt><dd>${source ? link(source) : 'Local record custodian missing.'}</dd><dt>Evidence leads</dt><dd>${evidence.length ? evidence.map(link).join(' · ') : 'No evidence lead recorded yet.'}</dd></dl>
      ${readerLink}${localResearchViewHtml}${relatedResearchHtml}${editionLeadHtml}`;
  byId('detail-panel').querySelector('.detail-reader-link')?.addEventListener('click', () => {
    state.chapter = 1;
    renderReader();
  });
  byId('detail-panel').querySelector('.detail-close').addEventListener('click', () => { state.selected = null; renderBooks(); byId('detail-panel').innerHTML = '<div class="detail-empty"><span class="detail-star">✳</span><h3>Choose a title</h3><p>Open a catalogue record to see its alternate names, source, and current research status.</p></div>'; });
  byId('detail-panel').querySelectorAll('.reader-open-research').forEach(button => button.addEventListener('click', () => {
    state.readerId = button.dataset.readerId;
    state.chapter = 1;
    renderReader();
    document.querySelector('#reader')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    byId('reader-book').focus({ preventScroll: true });
  }));
}

async function loadReaderData(readerMetadata) {
  if (state.activeReaderData?.reader_id === readerMetadata.reader_id) return state.activeReaderData;
  const requestSequence = ++state.readerLoadSequence;
  state.activeReaderData = null;
  byId('reader-title').textContent = `${readerMetadata.display_name || readerMetadata.title} · Loading bundled text…`;
  byId('reader-text').innerHTML = '<p class="reader-empty" role="status">Loading this text from the local archive package…</p>';
  byId('reader-translation-notes').innerHTML = '';
  byId('reader-study-panel').hidden = true;

  try {
    const path = readerMetadata.reader_data_url;
    if (typeof path !== 'string' || !/^readers\/[a-z0-9-]+\.json$/.test(path)) {
      throw new Error('This reader has no safe local package path recorded.');
    }
    const response = await fetch(path, { credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Local reader package could not be loaded (${response.status}).`);
    const reader = await response.json();
    if (reader.reader_id !== readerMetadata.reader_id || !Array.isArray(reader.chapters) || !reader.chapters.length) {
      throw new Error('The local package does not match the selected reader or has no chapter data.');
    }
    if (requestSequence !== state.readerLoadSequence || state.readerId !== readerMetadata.reader_id) return null;
    state.activeReaderData = reader;
    return reader;
  } catch (error) {
    if (requestSequence === state.readerLoadSequence && state.readerId === readerMetadata.reader_id) {
      byId('reader-title').textContent = `${readerMetadata.display_name || readerMetadata.title} · Text unavailable`;
      byId('reader-text').innerHTML = `<p class="reader-empty" role="alert">${escapeHTML(error.message)} Open this site while connected, or serve the downloaded project folder from a local web server. Reader texts are stored in the package; this browser cannot fetch local JSON files directly from a file:// page.</p>`;
    }
    return null;
  }
}

async function renderReader({ loadText = true } = {}) {
  const bookSelect = byId('reader-book');
  const languageSelect = byId('reader-language');
  if (!state.readers.length) {
    byId('reader-text').innerHTML = '<p class="reader-empty">No reader text is bundled in this archive yet.</p>';
    return;
  }
  const readerMetadata = state.readers.find(item => item.reader_id === state.readerId) || state.readers[0];
  state.readerId = readerMetadata.reader_id;
  if (loadText) persistReaderSelection(readerMetadata.reader_id);
  if (offlineReaderStatusFor !== readerMetadata.reader_id) {
    offlineReaderStatusFor = readerMetadata.reader_id;
    refreshOfflineReaderStatus();
  }
  const canonReaders = state.readers.filter(item => item.canon_id);
  const researchReaders = state.readers.filter(item => item.research_corpus_id);
  const option = item => `<option value="${escapeHTML(item.reader_id)}"${item.reader_id === readerMetadata.reader_id ? ' selected' : ''}>${escapeHTML(item.display_name || item.title)}</option>`;
  const searchQuery = (byId('reader-search')?.value || '').normalize('NFKC').trim().toLocaleLowerCase();
  const searchableText = item => [
    item.reader_id, item.research_corpus_id, item.display_name, item.title, item.language,
    item.language_tag, item.script_code, item.language_assignment_status, item.edition, item.edition_scope,
    item.parallel_translation?.title, item.parallel_translation?.language,
    item.parallel_translation?.language_tag, item.parallel_translation?.translator,
    item.parallel_translation?.edition, item.parallel_translation?.basis_language_tag,
  ].filter(Boolean).join(' ').normalize('NFKC').toLocaleLowerCase();
  const matchingReaders = state.readers.filter(item => !searchQuery || searchableText(item).includes(searchQuery));
  const currentReaderIsOutsideSearch = !matchingReaders.some(item => item.reader_id === readerMetadata.reader_id);
  const visibleReaders = currentReaderIsOutsideSearch ? [readerMetadata, ...matchingReaders] : matchingReaders;
  const visibleCanonReaders = visibleReaders.filter(item => item.canon_id && !(currentReaderIsOutsideSearch && item.reader_id === readerMetadata.reader_id));
  const visibleResearchReaders = visibleReaders.filter(item => item.research_corpus_id && !(currentReaderIsOutsideSearch && item.reader_id === readerMetadata.reader_id));
  const currentReaderOption = currentReaderIsOutsideSearch
     ? `<optgroup label="Current reader · kept open">${option(readerMetadata)}</optgroup>` : '';
  bookSelect.innerHTML = [
    currentReaderOption,
    visibleCanonReaders.length ? `<optgroup label="Church-list readers">${visibleCanonReaders.map(option).join('')}</optgroup>` : '',
    visibleResearchReaders.length ? `<optgroup label="Research texts · not canon coverage">${visibleResearchReaders.map(option).join('')}</optgroup>` : '',
  ].join('');
  const resultLanguages = new Set(matchingReaders.flatMap(item => [item.language_tag, item.parallel_translation?.language_tag].filter(Boolean)));
  const resultCount = matchingReaders.length;
  const resultWord = resultCount === 1 ? 'reader' : 'readers';
  const languageCount = resultLanguages.size;
  const status = byId('reader-search-status');
  if (status) {
    status.textContent = searchQuery
      ? resultCount
        ? `${resultCount} ${resultWord} found across ${languageCount} language${languageCount === 1 ? '' : 's'}.`
        : 'No matches; the current reader stays open.'
      : `${state.readers.length} readers · ${canonReaders.length} canon-linked, ${researchReaders.length} research-only.`;
  }
  const companionMetadata = readerMetadata.parallel_translation;
  const languageOptions = [`<option value="${escapeHTML(readerMetadata.language_tag)}">${escapeHTML(readerMetadata.language)}</option>`];
  if (companionMetadata) languageOptions.push(`<option value="${escapeHTML(companionMetadata.language_tag)}">${escapeHTML(companionMetadata.language)}</option>`, '<option value="parallel">Parallel witnesses</option>');
  const priorMode = languageSelect.value;
  languageSelect.innerHTML = languageOptions.join('');
  languageSelect.value = languageOptions.some(option => option.includes(`value="${priorMode}"`)) ? priorMode : readerMetadata.language_tag;
  const openButton = byId('reader-open');
  if (openButton) {
    const loaded = state.activeReaderData?.reader_id === readerMetadata.reader_id;
    openButton.disabled = loaded;
    openButton.textContent = loaded ? 'Text loaded' : 'Open selected text';
  }
  if (!loadText && state.activeReaderData?.reader_id !== readerMetadata.reader_id) {
    byId('reader-title').textContent = `${readerMetadata.display_name || readerMetadata.title} · Ready to open`;
    const sectionCount = readerMetadata.section_unit_plural
      ? `${readerMetadata.chapter_count} ${readerMetadata.section_unit_plural}`
      : `${readerMetadata.chapter_count} chapters`;
    byId('reader-chapter-count').textContent = `${sectionCount} · ${Number(readerMetadata.unit_count || 0).toLocaleString()} ${readerMetadata.unit_label || 'source units'} recorded`;
    byId('reader-text').innerHTML = '<p class="reader-empty">Choose <strong>Open selected text</strong> to load this bundled reader from the archive and save it for offline use.</p>';
    byId('reader-prev').disabled = true;
    byId('reader-next').disabled = true;
    byId('reader-translation-notes').innerHTML = '';
    byId('reader-study-panel').hidden = true;
    return;
  }
  if (openButton) {
    openButton.disabled = true;
    openButton.textContent = 'Loading text…';
  }
  const reader = await loadReaderData(readerMetadata);
  if (!reader) {
    if (openButton) {
      openButton.disabled = false;
      openButton.textContent = 'Retry loading text';
    }
    return;
  }
  if (openButton) openButton.textContent = 'Text loaded';
  const companion = reader.parallel_translation;
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
  byId('reader-chapter').innerHTML = reader.chapters.map(item => `<option value="${item.chapter}"${item.chapter === chapter.chapter ? ' selected' : ''}>${escapeHTML(formatChapterLabel(reader, item))}</option>`).join('');
  const unitLabel = reader.unit_label || 'Verse';
  const marker = item => item?.unit_order != null
    ? `${unitLabel} ${item.unit_order} · ${item.source_marker != null ? `source label ${item.source_marker}` : 'source label absent'}`
    : item?.source_marker ? `${item.number} · source ${item.source_marker}` : String(item?.number ?? '');
  const witness = (item, tag, cls, label) => `<div class="reader-witness ${cls}"><span class="reader-verse-number">${escapeHTML(label)}</span><span class="reader-witness-content" lang="${escapeHTML(tag)}" dir="${escapeHTML(direction(tag))}"${writingModeStyle(tag)}>${item ? item.text ? `${escapeHTML(item.text)}${(item.continuations || []).map(segment => `<span class="reader-continuation"><span class="reader-structure-marker">Unnumbered continuation (source ${escapeHTML(segment.source_marker || 'marker')})</span>${escapeHTML(segment.text)}</span>`).join('')}` : item.source_text_state === 'empty_source_element' ? '<span class="reader-gap">This source line element is empty in the retained TEI. See the archive note below; no wording has been supplied.</span>' : item.source_text_state === 'marker_only' ? '<span class="reader-gap">This source label has no inline verse text; its source note is retained below.</span>' : '<span class="reader-gap">No text is recorded for this source unit.</span>' : '<span class="reader-gap">No entry carrying this printed label in this witness.</span>'}</span></div>`;
  const sourceStructure = item => {
    const markers = item?.source_markers_before || [];
    const sourceHeadings = item?.source_headings_before || [];
    return [
      ...sourceHeadings.map(heading => `<span class="reader-structure-marker reader-source-heading" lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${escapeHTML(heading)}</span>`),
      ...(item?.source_elements_before || []).filter(element => element.marker === 'p' && element.text).map(element => `<p class="reader-heading" lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${escapeHTML(element.text)}</p>`),
      markers.includes('d') ? '<span class="reader-structure-marker">Source descriptive-title / superscription marker</span>' : '',
      markers.includes('b') ? '<span class="reader-structure-marker">Source break marker</span>' : '',
      ...[...new Set(markers.filter(marker => !['p', 'd', 'b'].includes(marker)))].map(marker => `<span class="reader-structure-marker">Source ${escapeHTML(marker)} marker</span>`),
    ].join('');
  };
  const trailingSourceStructure = (chapter.source_trailing_elements || []).map(element => element.text
    ? `<p class="reader-heading" lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${escapeHTML(element.text)}</p>`
    : `<span class="reader-structure-marker">Source ${escapeHTML(element.marker)} marker at chapter end</span>`).join('');
  const sourceTables = (chapter.source_tables || []).map((table, tableIndex) => {
    const rows = (table.rows || []).map((row, rowIndex) => `<tr aria-label="Source row ${rowIndex + 1}">${row.map(cell => `<td lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${cell.number ? `<span class="reader-source-table-verse">${escapeHTML(unitLabel)} ${escapeHTML(cell.number)}</span> ` : ''}${cell.text ? escapeHTML(cell.text) : '<span class="reader-gap">Empty source cell</span>'}</td>`).join('')}</tr>`).join('');
    return `<details class="reader-source-table" aria-label="Source table ${tableIndex + 1}"><summary>Source table layout (${(table.rows || []).length} rows; verse text is also shown above)</summary><div class="reader-source-table-scroll"><table><caption class="sr-only">Table ${tableIndex + 1}; cells remain in source order, and verse-labeled cells are also listed in reading order above.</caption><tbody>${rows}</tbody></table></div></details>`;
  }).join('');
  const frontMatter = chapter.chapter === 1 && Array.isArray(reader.front_matter) && reader.front_matter.length
    ? `<details class="reader-front-matter"><summary>Source front matter (${reader.front_matter.length} items)</summary><ul>${reader.front_matter.map(item => `<li><span class="reader-structure-marker">Source ${escapeHTML(item.marker || 'front-matter')} marker</span>${item.text ? `<p lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${escapeHTML(item.text)}</p>` : ''}${(item.notes || []).map(note => `<p class="reader-note"><span class="reader-structure-marker">Source ${escapeHTML(note.marker || 'note')} note</span> <span lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${escapeHTML(note.text || '')}</span></p>`).join('')}</li>`).join('')}</ul></details>`
    : '';
  const englishVerse = item => `<article class="reader-verse ${(item.source_markers_before || []).includes('p') ? 'paragraph-start' : ''}">${sourceStructure(item)}${witness(item, englishTag, 'english-witness', String(item.number))}</article>`;
  const chapterHeading = Array.isArray(chapter.heading) && chapter.heading.length ? `<div class="reader-heading" lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${chapter.heading.map(item => `<p>${escapeHTML(item)}</p>`).join('')}</div>` : '';
  const chapterLead = frontMatter + chapterHeading;
  byId('reader-title').textContent = `${reader.display_name || reader.title.split(' — ')[0]} · ${formatChapterLabel(reader, chapter)}${mode === 'parallel' ? ' · Parallel witnesses' : ` · ${mode === englishTag && companion ? 'English' : reader.language}`}`;
  const sectionCount = reader.section_unit_plural ? `${reader.chapter_count} ${reader.section_unit_plural}` : `${reader.chapter_count} chapters`;
  const observedUnits = layer => Number.isInteger(layer?.unit_count) && layer.unit_count >= 0
    ? `${layer.unit_count.toLocaleString()} ${layer.unit_label || 'source units'} observed`
    : `unit count unknown for ${layer?.title || layer?.language || 'this text'}`;
  const activeCountLayers = mode === 'parallel' && companion ? [reader, companion]
    : companion && mode === englishTag ? [companion] : [reader];
  byId('reader-chapter-count').textContent = `${sectionCount} · ${activeCountLayers.map(observedUnits).join(' · ')}`;
  if (mode === 'parallel' && companion) {
    byId('reader-text').innerHTML = chapterLead + parallelRows.map(row => `<article class="reader-parallel-row"><div><span class="reader-witness-label">${escapeHTML(reader.language.toUpperCase())}</span>${witness(row.source, sourceTag, 'geez-witness', row.source ? marker(row.source) : 'No source unit')}</div><div><span class="reader-witness-label">${escapeHTML(companion.title)}</span>${sourceStructure(row.english)}${witness(row.english, englishTag, 'english-witness', row.english ? String(row.english.number) : 'No matching English label')}</div></article>`).join('');
    byId('reader-alignment-note').textContent = 'Only unique matching printed labels are paired, for navigation. Duplicate, absent, or ambiguous labels stay unpaired and visible; matching labels do not establish textual equivalence or translation accuracy.';
  } else if (companion && mode === englishTag) {
    byId('reader-text').innerHTML = chapterLead + (englishChapter?.verses || []).map(englishVerse).join('');
    byId('reader-alignment-note').textContent = companion.translation_basis;
  } else {
    byId('reader-text').innerHTML = chapterLead + sourceUnits.map(item => `<article class="reader-verse ${(item.source_markers_before || []).includes('p') ? 'paragraph-start' : ''}">${sourceStructure(item)}${witness(item, sourceTag, 'geez-witness', marker(item))}</article>`).join('') + sourceTables + trailingSourceStructure;
    byId('reader-alignment-note').textContent = reader.unit_label ? `Source numbering note: ${reader.chapter_structure_note}` : '';
  }
  const sourceNotes = (chapter.notes || []).map(note => ({ ...note, witnessLabel: note.note_origin === 'archive' ? 'Archive' : reader.language }));
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
  const licenseLink = layer => layer?.license_url
    ? ` License: <a href="${escapeHTML(safeURL(layer.license_url))}" target="_blank" rel="noopener noreferrer">${escapeHTML(layer.license_id || 'view license terms')}</a>.`
    : '';
  byId('reader-permission').innerHTML = `Text rights: ${escapeHTML(rightsClassificationLabel(reader.rights_classification))}. ${escapeHTML(reader.rights_status || 'Rights status not recorded.')}${licenseLink(reader)}<details><summary>Item copyright and reuse notice</summary><p>${escapeHTML(reader.copyright_notice || 'No text-rights notice recorded.')}</p></details>${companion ? ` English companion rights: ${escapeHTML(rightsClassificationLabel(companion.rights_classification))}. ${escapeHTML(companion.text_notice || 'No companion rights notice recorded.')}${licenseLink(companion)}` : ''}`;
  byId('reader-caveat-text').textContent = [reader.edition_scope, reader.chapter_structure_note, reader.transcription_note, reader.editorial_signs_note, ...(chapter.source_label_observations || []), ...(companion && mode !== sourceTag ? [companion.translation_basis, companion.verification_status] : [])].filter(Boolean).join(' ');
  renderReaderStudyView(reader, chapter);
}

function renderGenesisLexicalLens(record) {
  const measurements = record.measurements || [];
  const byId = id => measurements.find(item => item.measurement_id === id);
  const firstPerson = byId('english-first-person-forms-in-attributed-divine-speech');
  const explicitNoun = byId('english-explicit-noun-god');
  const narratorNoun = byId('english-third-person-narrator-noun-god');
  const narratorPronoun = byId('english-third-person-pronoun-god-reference');
  const geezString = byId('geez-exact-string-lexical-occurrences');
  const geezGrammar = byId('geez-first-person-grammatical-forms');
  const secondPerson = byId('english-second-person-audience-reference-in-attributed-speech');
  if (!firstPerson || !explicitNoun || !narratorNoun || !narratorPronoun || !geezString || !geezGrammar || !secondPerson) return '<p class="reader-integrity-note">This lens record is incomplete; no counts are shown.</p>';
  const breakdown = (measurement, dimension) => (measurement.breakdowns || []).find(item => item.dimension === dimension)?.values || [];
  const tokenCounts = breakdown(firstPerson, 'token').map(item => `${item.value} × ${item.count}`).join(' · ');
  const nounVerses = breakdown(explicitNoun, 'verse').map(item => `v. ${item.value}: ${item.count}`).join(' · ');
  const narratorVerses = breakdown(narratorNoun, 'verse').map(item => `v. ${item.value}: ${item.count}`).join(' · ');
  const narratorPronounVerses = breakdown(narratorPronoun, 'verse').map(item => `v. ${item.value}: ${item.count}`).join(' · ');
  const speechNounCount = Number(explicitNoun.count) - Number(narratorNoun.count);
  const speechSpans = (firstPerson.excerpts || []).map(span => `<li><strong>Verse ${escapeHTML(span.unit_label)}:</strong> “${escapeHTML(span.text)}”</li>`).join('');
  const narratorPronounSpans = (narratorPronoun.excerpts || []).map(span => `<li><strong>Verse ${escapeHTML(span.unit_label)}:</strong> “${escapeHTML(span.text)}”</li>`).join('');
  const sourceIds = [...new Set(measurements.flatMap(item => item.evidence_source_ids || []))];
  const verseCount = record.scope?.witnesses?.find(item => item.witness_id === firstPerson.witness_id)?.stored_verse_count;
  const sourceLinks = sourceIds.map(id => state.sources.find(item => item.source_id === id)).filter(Boolean).map(item => sourceLinkHTML(item)).join(' · ');
  const limits = (record.interpretive_limits || []).map(item => `<li>${escapeHTML(item)}</li>`).join('');
  return `<section class="reader-lexical-lens"><h5>Genesis 1 · recorded lexical observations</h5><p class="reader-lens-intro">Scope: ${escapeHTML(verseCount ?? 'Unknown')} stored English verse texts, alongside a separate named Geʽez witness. These are distinct measurements, not equivalent totals or a theological conclusion.</p>
    <article class="reader-lexical-card"><h6>First-person forms in English spans editorially attributed to God</h6><p><strong>${Number(firstPerson.count).toLocaleString()} tokens</strong> · ${escapeHTML(tokenCounts || 'Token breakdown unavailable')}</p><p>${escapeHTML(firstPerson.operational_definition || '')}</p><details><summary>Inspect ${firstPerson.excerpts?.length || 0} attributed speech excerpts</summary><p>${escapeHTML(firstPerson.speaker_attribution?.statement || '')} Review: ${escapeHTML(firstPerson.speaker_attribution?.review_state || 'unknown')}.</p><ol>${speechSpans}</ol></details></article>
    <article class="reader-lexical-card"><h6>Third-person narrator reference · noun “God”</h6><p><strong>${Number(narratorNoun.count).toLocaleString()} occurrences</strong> · ${escapeHTML(narratorVerses)}</p><p>${escapeHTML(narratorNoun.operational_definition || '')}</p><p>Cross-check: ${Number(explicitNoun.count).toLocaleString()} whole-word occurrences across the chapter; ${speechNounCount.toLocaleString()} fall inside the selected speech excerpts. Attribution review: ${escapeHTML(narratorNoun.speaker_attribution?.review_state || 'unknown')}.</p></article>
    <article class="reader-lexical-card"><h6>Third-person narrator reference · pronoun “he” attributed to God</h6><p><strong>${Number(narratorPronoun.count).toLocaleString()} tokens</strong> · ${escapeHTML(narratorPronounVerses)}</p><p>${escapeHTML(narratorPronoun.operational_definition || '')}</p><details><summary>Inspect the ${narratorPronoun.excerpts?.length || 0} attributed phrases</summary><p>${escapeHTML(narratorPronoun.speaker_attribution?.statement || '')} Review: ${escapeHTML(narratorPronoun.speaker_attribution?.review_state || 'unknown')}.</p><ol>${narratorPronounSpans}</ol></details></article>
    <article class="reader-lexical-card"><h6>Exact Geʽez string occurrences</h6><p><strong>${Number(geezString.count).toLocaleString()} occurrences</strong> · <span lang="${escapeHTML(geezString.language_tag)}" dir="ltr">${escapeHTML(geezString.observed_value || '')}</span></p><p>${escapeHTML(geezString.feature || '')}</p><p>${escapeHTML(geezString.operational_definition || '')}</p></article>
    <article class="reader-lexical-card"><h6>Second-person audience references in the same English spans</h6><p><strong>${Number(secondPerson.count).toLocaleString()} tokens</strong></p><p>${escapeHTML(secondPerson.operational_definition || '')}</p></article>
    <article class="reader-lexical-card"><h6>Geʽez first-person grammatical forms</h6><p><strong>${escapeHTML(geezGrammar.state)}</strong> (not zero; no count reported)</p><p>${escapeHTML(geezGrammar.reason_for_state || geezGrammar.operational_definition || '')}</p></article>
    <details class="reader-lexical-limits"><summary>Translation, attribution, and interpretation limits</summary><ul>${limits}</ul></details>
    <p class="reader-lens-intro">Evidence: ${sourceLinks || 'No source links recorded.'} · <a href="research/genesis-1-divine-person-lens.md">Human-readable method note</a> · <a href="research/genesis-1-divine-person-lens.json" download>Download lens record</a> · <a href="schemas/textual-lens.schema.json" download>Download record schema</a>.</p></section>`;
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
    const records = (profile.records || []).filter(record => record.reader_id === reader.reader_id || Boolean(reader.canon_id && record.canon_id === reader.canon_id));
    const researchRecords = (registry?.research_corpora || []).filter(record => record.language_tag === profile.language_tag
      && (record.reader_id === reader.reader_id || Boolean(reader.canon_id && record.candidate_canon_id === reader.canon_id)));
    const researchRecord = researchRecords.find(record => record.reader_id === reader.reader_id);
    const researchCandidates = researchRecords.filter(record => record.reader_id !== reader.reader_id);
    const editionBasis = researchRecord?.translation_id
      ? (registry?.edition_basis_evidence || []).find(record => record.family_id === researchRecord.translation_id)
      : null;
    const hasLead = bookLeads.some(lead => lead.language_tag === profile.language_tag);
    const bookSpecific = Boolean(records.length || researchRecords.length || hasLead);
    let researchBasis = '';
    if (researchRecord?.text_origin === 'source_transcription') {
      researchBasis = `<strong>Text origin: source transcription.</strong> ${escapeHTML(researchRecord.language_description || 'No additional source-language note recorded.')}`;
    } else if (researchRecord?.text_origin === 'published_translation') {
      const basisStatus = researchRecord.translation_basis_status;
      const basisLabel = basisStatus === 'established'
        ? 'cited evidence identifies a path'
        : basisStatus === 'unknown' ? 'unknown in this archive' : 'not recorded';
      const basisPath = Array.isArray(researchRecord.translation_path)
        ? `Path: ${researchRecord.translation_path.map(languageName).map(escapeHTML).join(' → ')}. `
        : basisStatus === 'unknown' ? 'No source-language path is established here. '
          : basisStatus === 'established' ? 'The established path is missing from this record. ' : '';
      const basisEvidence = researchRecord.translation_basis_source_ids?.length
        ? ` Evidence: ${sourceLinks(researchRecord.translation_basis_source_ids)}.` : '';
      researchBasis = `<strong>Translation basis: ${basisLabel}.</strong> ${basisPath}${escapeHTML(researchRecord.translation_basis_note || 'No translation-basis note recorded.')}${basisEvidence}`;
    } else if (researchRecord) {
      researchBasis = `<strong>Text origin and translation basis are not recorded.</strong> ${escapeHTML(researchRecord.language_description || 'No language note recorded.')}`;
    }
    const content = records.length
      ? records.map(record => {
          const path = Array.isArray(record.translation_path) ? ` · Path: ${record.translation_path.map(languageName).map(escapeHTML).join(' → ')}` : '';
          return `<li><strong>${escapeHTML(record.status || 'Status not recorded')}</strong> — ${escapeHTML(record.layer_role || 'language layer')}${path}<br><span>${escapeHTML(record.basis_description || 'No basis description recorded.')}</span></li>`;
      }).join('')
      : researchRecord
        ? `<li><strong>${researchRecord.reader_id === reader.reader_id ? 'Bundled research reader' : `Related research candidate · title link ${escapeHTML(researchRecord.canon_mapping_state || 'not recorded')}; not confirmed as a canon-linked edition`}</strong> — ${escapeHTML(researchRecord.edition_statement || researchRecord.title)}<br><span>${researchBasis}</span>${editionBasis ? `<br><strong>Attributed edition-family basis report (not checked against this digital witness)</strong><ul>${editionBasis.claims.map(claim => `<li>${escapeHTML(claim.scope.replace(/_/g, ' '))}: ${escapeHTML(claim.statement)} Source-language tags: ${claim.source_language_tags.map(languageName).map(escapeHTML).join(', ')}.</li>`).join('')}</ul><span>${escapeHTML(editionBasis.limitations)} ${sourceLinks(editionBasis.source_ids || [])}</span>` : ''}${researchRecord.reader_id !== reader.reader_id ? `<br><button class="reader-open-research" type="button" data-reader-id="${escapeHTML(researchRecord.reader_id)}">Open research text</button>` : ''}</li>`
      : researchCandidates.length
        ? `<li><strong>${researchCandidates.length} separately bundled research candidate${researchCandidates.length === 1 ? '' : 's'} are listed below.</strong> Their title link does not establish equivalence to this canon entry.</li>`
        : hasLead
          ? '<li><strong>No text is bundled.</strong> A separate unbundled translation lead is listed below.</li>'
          : '<li><strong>No bundled layer identified for this title.</strong> This language profile is not a translation of the selected book.</li>';
    return { bookSpecific, html: `<section class="reader-language-card"><h4 lang="${escapeHTML(profile.language_tag)}">${escapeHTML(profile.language_name)} <small>${escapeHTML(profile.language_tag)} · ${escapeHTML(profile.script_code || 'script not recorded')}</small></h4><ul>${content}</ul></section>` };
  });

  const sourceLink = item => sourceLinkHTML(item);
  const sources = state.sources;
  const sourceCards = ids => (ids || []).map(id => sources.find(item => item.source_id === id)).filter(Boolean).map(item => `<li>${sourceLink(item)} <span>${escapeHTML(item.archive_status || '')}</span><br><small>${escapeHTML(item.inspection_and_limitations || '')}</small></li>`).join('');
  const relatedCandidates = (registry?.research_corpora || []).filter(record => reader.canon_id && record.candidate_canon_id === reader.canon_id && record.reader_id !== reader.reader_id);
  const researchCandidateHtml = relatedCandidates.length ? `<h4>Related research candidates · ${relatedCandidates.length}</h4><p>These stored texts have a catalogued title link to this entry. The link does not establish edition identity, canon equivalence, or textual completeness.</p>${relatedCandidates.map(record => {
    const candidateReader = state.readers.find(item => item.reader_id === record.reader_id);
    if (!candidateReader) return '';
    const mapping = record.canon_mapping_state || 'not recorded';
    const summary = record.unit_summary || record.edition_statement || 'Extent not recorded.';
    return `<article class="translation-lead"><strong>${escapeHTML(record.title || candidateReader.title)}</strong><p>${escapeHTML(record.language_tag || 'language not recorded')} · title mapping ${escapeHTML(mapping)} · research-only</p><p>${escapeHTML(summary)}</p><p>${escapeHTML(record.review_status || candidateReader.verification_status || 'Review status not recorded.')}</p><button class="reader-open-research" type="button" data-reader-id="${escapeHTML(record.reader_id)}">Open research text</button>${record.source_ids?.length ? `<ul class="reader-source-list">${sourceCards(record.source_ids)}</ul>` : ''}</article>`;
  }).join('')}` : '';
  const bookLeadHtml = bookLeads.length ? `<h4>Unbundled translation leads for this book</h4>${bookLeads.map(lead => `<article class="translation-lead"><strong>${escapeHTML(lead.edition)}</strong><p>${escapeHTML(lead.translator)} · ${Array.isArray(lead.translation_path) ? lead.translation_path.map(languageName).map(escapeHTML).join(' → ') : 'translation path unknown'} · not bundled</p><p>${escapeHTML(lead.review_status)}</p><p>${escapeHTML(lead.notes)}</p><small>${rightsNote(lead)}</small><ul class="reader-source-list">${sourceCards(lead.source_ids) || '<li>No source records linked.</li>'}</ul></article>`).join('')}` : '';
  const matchingLanguageRows = languageRows.filter(row => row.bookSpecific).map(row => row.html).join('');
  const otherLanguageRows = languageRows.filter(row => !row.bookSpecific).map(row => row.html).join('');
  const unrelatedProfileCount = languageRows.filter(row => !row.bookSpecific).length;
  const otherProfiles = unrelatedProfileCount
    ? `<details class="reader-other-languages"><summary>Other registered language profiles with no book-specific text or lead (${unrelatedProfileCount})</summary><p>These profiles are part of the archive-wide language inventory; none is evidence of a translation of this book.</p><div class="reader-language-grid">${otherLanguageRows}</div></details>`
    : '';
  const available = `<p class="reader-lens-intro">Only text layers bundled for this title are selectable above. Registered language profiles describe archive coverage; unbundled leads are evidence pointers, not reader text. Research candidates are labeled separately from canon-linked editions.</p><p><strong>Available here:</strong> ${escapeHTML(reader.language)}${reader.parallel_translation ? `; ${escapeHTML(reader.parallel_translation.language)} companion by ${escapeHTML(reader.parallel_translation.translator || 'translator not recorded')}` : ''}.</p><p><strong>Reader status:</strong> ${escapeHTML(reader.verification_status)}</p><div class="reader-language-grid">${matchingLanguageRows || '<p>No additional book-specific language records are registered.</p>'}</div>${otherProfiles}${researchCandidateHtml}${bookLeadHtml}`;
  const context = `<p class="reader-lens-intro">Context follows the named witness and edition. It is not a claim to reconstruct every historical stage or community reading.</p><dl class="reader-context-list"><dt>Language identification</dt><dd>${escapeHTML(reader.language_assignment_status || 'Language-assignment basis not recorded.')}</dd><dt>Edition / witness</dt><dd>${escapeHTML(reader.edition || 'Not identified')}</dd><dt>Time &amp; scope</dt><dd>${escapeHTML(reader.edition_scope || 'Not established')}</dd><dt>${escapeHTML(formatChapterLabel(reader, chapter))} structure</dt><dd>${escapeHTML(reader.chapter_structure_note || 'Not established')}</dd><dt>Transcription status</dt><dd>${escapeHTML(reader.transcription_note || reader.verification_status || 'Not recorded')}</dd><dt>Editorial signs</dt><dd>${escapeHTML(reader.editorial_signs_note || 'No editorial-sign note recorded.')}</dd><dt>Source capture / local location</dt><dd>${escapeHTML(reader.source_pages || reader.source_path || 'No source capture or local path recorded.')}</dd></dl><h4>Evidence sources</h4><ul class="reader-source-list">${sourceCards(reader.source_ids) || '<li>No source records are linked to this reader.</li>'}</ul>`;
  const perspectives = `<p class="reader-lens-intro">Perspectives are presented as attributed records, not collapsed into one supposedly universal interpretation. Unsurveyed traditions and viewpoints are marked unknown; they are not synthesized. This archive preserves the Church's cited English list and selected scholarship about canon-list variation, not a reviewed global survey.</p><dl class="reader-context-list"><dt>Canon mapping</dt><dd>${escapeHTML(corpus?.canon_mapping_note || canon?.mapping_note || entry?.canon_view || 'No verified mapping note is recorded.')}</dd><dt>Catalogue identity</dt><dd>${escapeHTML(entry?.identity_status || (corpus ? 'Related research text; no canon-linked catalogue identity assigned.' : 'No linked catalogue identity record.'))}</dd><dt>Church-list status</dt><dd>${escapeHTML(canon?.reader_status || (corpus ? 'Not linked to or counted as a Church-list reader.' : 'No Church-list crosswalk recorded.'))}</dd><dt>Editorial review</dt><dd>${escapeHTML(entry?.reviewer_notes || corpus?.review_status || 'No additional reviewer notes recorded.')}</dd></dl><h4>Evidence and scope</h4><ul class="reader-source-list">${sourceCards([...new Set([...(entry?.evidence_source_ids || canon?.source_ids || []), ...(corpus?.source_ids || []), ...state.canonContextSourceIds])]) || '<li>No separate perspective sources recorded.</li>'}</ul>`;

  const lexicalRecordMatches = reader.reader_id === 'genesis-geez-dillmann-hacohen' && chapter.chapter === 1;
  const lexicalObservation = lexicalRecordMatches
    ? state.lexicalLensData
      ? renderGenesisLexicalLens(state.lexicalLensData)
      : state.lexicalLensError
        ? '<p class="reader-integrity-note">The local Genesis 1 lens record could not be loaded. No counts are shown. Reconnect if needed, then retry.</p><button class="reader-step" id="reader-lens-retry" type="button">Retry loading lens</button>'
        : '<p class="reader-integrity-note" role="status">Loading the stored Genesis 1 lens record…</p>'
    : '<p class="reader-integrity-note">No source-scoped lexical lens is bundled here for this exact reader and chapter. This does not mean none exists elsewhere; no counts are implied.</p>';
  if (lexicalRecordMatches && !state.lexicalLensData && !state.lexicalLensPromise && !state.lexicalLensError) {
    const requestedReaderId = reader.reader_id;
    const requestedChapter = chapter.chapter;
    state.lexicalLensPromise = fetch('research/genesis-1-divine-person-lens.json', { credentials: 'same-origin' })
      .then(response => {
        if (!response.ok) throw new Error(`Lens record could not be loaded (${response.status}).`);
        return response.json();
      })
      .then(record => {
        if (record.record_id !== 'genesis-1-divine-person-lens' || record.scope?.reader_id !== requestedReaderId || record.scope?.chapter !== requestedChapter) {
          throw new Error('Lens record scope does not match the selected reader and chapter.');
        }
        state.lexicalLensData = record;
      })
      .catch(error => { state.lexicalLensError = error; })
      .finally(() => {
        state.lexicalLensPromise = null;
        const currentReader = state.activeReaderData;
        const currentChapter = currentReader?.chapters?.find(item => item.chapter === state.chapter);
        if (currentReader?.reader_id === requestedReaderId && currentChapter?.chapter === requestedChapter
            && ['lexical', 'integrated'].includes(byId('reader-lens')?.value)) {
          renderReaderStudyView(currentReader, currentChapter);
        }
      });
  }

  const blocks = lens === 'language' ? `<h4>Language &amp; translation path</h4>${available}`
    : lens === 'time' ? `<h4>Time &amp; edition context</h4>${context}`
    : lens === 'tradition' ? `<h4>Tradition &amp; interpretive perspectives</h4>${perspectives}`
    : lens === 'lexical' ? `<h4>Textual lexical lens</h4>${lexicalObservation}<p class="reader-integrity-note">Counts are scoped to the named witnesses and definitions; they do not establish translation equivalence.</p>`
    : `<h4>Integrated reading · ${escapeHTML(reader.title)} · ${escapeHTML(formatChapterLabel(reader, chapter))}</h4><div class="reader-integrated-grid"><section><h5>Language &amp; translation</h5>${available}</section><section><h5>Time &amp; edition</h5>${context}</section><section><h5>Tradition &amp; perspectives</h5>${perspectives}</section><section><h5>Textual lexical lens</h5>${lexicalObservation}</section></div><p class="reader-integrity-note">The text above remains the selected witness. The panels below it add distinct evidence and viewpoints; they do not merge unlike translations, resolve disputed readings, or fill missing text. Missing lexical or interpretive records are not filled in by inference.</p>`;
  panel.innerHTML = blocks;
  panel.querySelectorAll('.reader-open-research').forEach(button => button.addEventListener('click', () => {
    state.readerId = button.dataset.readerId;
    state.chapter = 1;
    renderReader();
    document.querySelector('#reader')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    byId('reader-book').focus({ preventScroll: true });
  }));
  byId('reader-lens-retry')?.addEventListener('click', () => {
    state.lexicalLensError = null;
    state.lexicalLensPromise = null;
    renderReaderStudyView(reader, chapter);
  });
}

byId('reader-book').addEventListener('change', event => { state.readerId = event.target.value; state.chapter = 1; renderReader(); });
byId('reader-search')?.addEventListener('input', () => renderReader({ loadText: Boolean(state.activeReaderData) }));
byId('reader-open')?.addEventListener('click', () => renderReader({ loadText: true }));
byId('reader-chapter').addEventListener('change', event => { state.chapter = Number(event.target.value); renderReader(); });
byId('reader-prev').addEventListener('click', () => { state.chapter = Math.max(1, state.chapter - 1); renderReader(); });
byId('reader-next').addEventListener('click', () => { const reader = state.readers.find(item => item.reader_id === state.readerId); state.chapter = Math.min(reader?.chapter_count || 1, state.chapter + 1); renderReader(); });
byId('reader-language').addEventListener('change', renderReader);
byId('reader-lens').addEventListener('change', renderReader);

byId('reader-download')?.addEventListener('click', () => {
  const status = byId('reader-export-status');
  try {
    if (!state.activeReaderData) throw new Error('Wait for the selected reader to finish loading.');
    const readerArchive = { ...state.archiveData, readers: [state.activeReaderData] };
    const selected = window.ReaderPackage.createReaderPackage(readerArchive, state.readerId, byId('reader-language').value);
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
    <article class="source-card"${source.source_id === 'SRC-000' ? ' id="catalogue-method"' : ` id="source-${escapeHTML(source.source_id.toLowerCase())}"`}><span class="source-kind">${escapeHTML(source.archive_status)}</span><h3>${escapeHTML(source.source_name)}</h3><p>${escapeHTML(source.inspection_and_limitations)}</p>${sourceRightsNote(source)}${source.link_status === 'withheld' ? sourceLinkHTML(source, 'External source link withheld') : sourceLinkHTML(source, source.url.startsWith('https://') ? 'Open source' : 'Open archived item')}</article>`).join('');
}

function renderRelated() {
  const sourceById = new Map(state.sources.map(source => [source.source_id, source]));
  byId('related-list').innerHTML = state.related.map(record => {
    const links = record.source_ids.map(id => sourceById.get(id)).filter(Boolean);
    return `<article class="related-card"><span class="related-category">${escapeHTML(record.category)}</span><h3>${escapeHTML(record.title)}</h3>${record.also_known_as ? `<p><strong>Also known as:</strong> ${escapeHTML(record.also_known_as)}</p>` : ''}<p>${escapeHTML(record.description)}</p><p class="related-boundary">${escapeHTML(record.not_canonical_note)}</p><p class="related-rights"><strong>Text reuse:</strong> ${escapeHTML(rightsClassificationLabel(record.rights_classification))}. ${escapeHTML(record.rights_status || 'Detailed rights status not recorded.')}</p><div class="related-links">${links.map(source => sourceLinkHTML(source)).join('')}</div></article>`;
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

if (window.isSecureContext && 'serviceWorker' in navigator) {
  const offlineStatus = byId('offline-status');
  const showOfflineStatus = (message, state) => {
    if (!offlineStatus) return;
    offlineStatus.textContent = message;
    offlineStatus.dataset.state = state;
  };
  let offlineCheckPending = false;
  let offlineCheckQueued = false;
  const checkOfflineReader = worker => {
    if (!worker) return;
    if (offlineCheckPending) {
      offlineCheckQueued = true;
      return;
    }
    if (!('MessageChannel' in window)) {
      showOfflineStatus('Automatic offline status is unavailable in this browser. You can download the selected reader as JSON below.', 'unknown');
      return;
    }
    offlineCheckPending = true;
    const channel = new MessageChannel();
    const timeout = window.setTimeout(() => {
      offlineCheckPending = false;
      channel.port1.close();
      showOfflineStatus('Could not confirm offline storage. If needed, use the selected reader’s JSON download below.', 'unknown');
      if (offlineCheckQueued) {
        offlineCheckQueued = false;
        requestOfflineStatus();
      }
    }, 5000);
    channel.port1.onmessage = event => {
      window.clearTimeout(timeout);
      offlineCheckPending = false;
      channel.port1.close();
      const available = event.data?.available;
      if (available === true) {
        showOfflineStatus(navigator.onLine
          ? 'This archive page and selected reader are saved on this device. Other bundled readers are saved when opened; use the optional bulk-save control below to prepare all reader files. Source links and unbundled material may need a connection.'
          : 'You are offline. This archive page and selected reader are saved on this device. Other bundled readers may not be saved; source links and unbundled material may need a connection.', 'available');
      } else if (available === false) {
        showOfflineStatus(navigator.onLine
          ? 'The selected reader is not yet confirmed for offline use. Keep it open while online so the browser can save its bundled file, use the optional bulk-save control below, or download the reader JSON.'
          : 'This selected reader is not saved on this device. Reconnect to open it, or use a reader JSON file downloaded earlier.', 'missing');
      } else {
        showOfflineStatus('Could not confirm offline storage. If needed, use the selected reader’s JSON download below.', 'unknown');
      }
      if (offlineCheckQueued) {
        offlineCheckQueued = false;
        requestOfflineStatus();
      }
    };
    const selected = state.readers.find(reader => reader.reader_id === state.readerId);
    worker.postMessage({ type: 'CHECK_OFFLINE_READER', readerUrl: selected?.reader_data_url || null }, [channel.port2]);
  };
  const requestOfflineStatus = () => {
    showOfflineStatus('Checking whether this archive page and selected text are saved for offline use…', 'checking');
    const worker = navigator.serviceWorker.controller;
    if (worker) {
      checkOfflineReader(worker);
      return;
    }
    navigator.serviceWorker.ready.then(registration => {
      checkOfflineReader(navigator.serviceWorker.controller || registration.active);
    }).catch(() => {
      showOfflineStatus('Automatic offline storage could not be confirmed. You can download the selected reader as JSON below.', 'unknown');
    });
  };
  refreshOfflineReaderStatus = requestOfflineStatus;
  window.addEventListener('online', requestOfflineStatus);
  window.addEventListener('offline', requestOfflineStatus);
  navigator.serviceWorker.addEventListener('controllerchange', requestOfflineStatus);
  navigator.serviceWorker.addEventListener('message', event => {
    if (event.data?.type === 'OFFLINE_READER_CACHE_UPDATED') requestOfflineStatus();
  });
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').then(registration => {
      return navigator.serviceWorker.ready.then(() => {
        requestOfflineStatus();
        return registration;
      });
    }).catch(() => {
      showOfflineStatus('Automatic offline storage is unavailable in this browser. You can download the selected reader as JSON below.', 'unknown');
    });
  }, { once: true });
} else {
  const offlineStatus = byId('offline-status');
  if (offlineStatus) {
    offlineStatus.textContent = 'Automatic offline storage is unavailable in this browsing mode. You can download the selected reader as JSON below.';
    offlineStatus.dataset.state = 'unknown';
  }
}

init();
