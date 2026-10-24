const state = { books: [], sources: [], related: [], readers: [], canonBooks: [], translationRegistry: null, query: '', filter: 'All', selected: null, chapter: 1, readerId: null };
const byId = (id) => document.getElementById(id);
const escapeHTML = (value = '') => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeURL = (value) => {
  if (typeof value !== 'string') return '#';
  if (value.startsWith('#')) return value;
  try {
    const base = new URL(window.location.href);
    const url = new URL(value, base);
    const localPath = !/^[a-z][a-z0-9+.-]*:/i.test(value) && !value.startsWith('//') && !value.split(/[?#]/)[0].split('/').includes('..');
    if (['https:', 'http:'].includes(url.protocol) && (url.origin === base.origin || /^[a-z][a-z0-9+.-]*:/i.test(value))) return url.href;
    if (base.protocol === 'file:' && url.protocol === 'file:' && localPath) return url.href;
    return '#';
  } catch { return '#'; }
};

async function init() {
  try {
    const archiveNode = byId('archive-data');
    if (!archiveNode) throw new Error('Embedded archive data is missing. Regenerate index.html from archive.json.');
    const data = JSON.parse(archiveNode.textContent);
    state.books = Array.isArray(data.catalogue) ? data.catalogue : [];
    state.sources = Array.isArray(data.sources) ? data.sources : [];
    state.related = Array.isArray(data.related_texts) ? data.related_texts : [];
    state.readers = Array.isArray(data.readers) ? data.readers : [];
    state.canonBooks = Array.isArray(data.canon_registry?.books) ? data.canon_registry.books : [];
    state.translationRegistry = data.translation_registry || null;
    byId('book-count').textContent = state.books.length;
    byId('all-count').textContent = state.books.length;
    byId('source-count').textContent = state.sources.length;
    renderBooks(); renderSources(); renderRelated(); renderCanonCoverage(); renderLanguageCoverage(); renderReader();
  } catch (error) {
    byId('results-label').textContent = 'The catalogue could not be loaded.';
    byId('book-grid').innerHTML = `<div class="load-error"><strong>Archive unavailable</strong><p>${escapeHTML(error.message)}. Rebuild the embedded archive from archive.json.</p></div>`;
  }
}

function renderLanguageCoverage() {
  const registry = state.translationRegistry;
  const languageLabel = tag => registry?.languages?.find(language => language.language_tag === tag)?.language_name || registry?.basis_languages?.find(language => language.language_tag === tag)?.language_name || tag;
  const languages = registry?.languages || [];
  const readerLanguages = languages.filter(language => (language.records || []).some(record => record.status === 'bundled'));
  const bundledLayers = readerLanguages.flatMap(language => language.records.filter(record => record.status === 'bundled'));
  const directPaths = bundledLayers.filter(record => ['translation', 'historical_companion_translation', 'draft_translation'].includes(record.layer_role) && record.translation_path?.length === 2 && record.translation_path[0] !== 'und').length;
  const corpusLeads = registry?.corpus_leads || [];
  const corpusLeadLanguages = new Set(corpusLeads.map(lead => lead.language_tag)).size;
  byId('language-coverage-summary').textContent = `${readerLanguages.length} reader languages · ${bundledLayers.length} bundled text layers · ${languages.length} language profiles · ${directPaths} direct translation paths recorded · ${corpusLeadLanguages} languages with unbundled corpus leads`;
  byId('language-coverage-statement').textContent = registry?.coverage_statement || 'Language coverage is not available.';
  byId('language-coverage-list').innerHTML = languages.map(language => {
    const records = language.records.filter(record => record.status === 'bundled');
    const items = records.map(record => {
      const role = record.layer_role === 'source_text_transcription' ? 'Source-text transcription' : record.layer_role === 'source_text_edition' ? 'Source-text edition (encoded transcription)' : record.layer_role === 'historical_companion_translation' ? 'Historical companion translation' : record.layer_role;
      const path = record.translation_path || [];
      const basis = record.basis_language_tag === language.language_tag ? 'Source text in this language' : path.length ? `Path: ${path.map(languageLabel).map(escapeHTML).join(' → ')}` : `Basis language: ${escapeHTML(record.basis_language_tag)}`;
      return `<li><strong>${escapeHTML(record.canon_id)}</strong><span>${escapeHTML(role)}</span><small>${basis}</small></li>`;
    }).join('');
    const scripts = language.script_code === 'Zzzz' ? 'not established' : language.script_codes?.length ? language.script_codes.join(', ') : language.script_code;
    const direction = language.direction === 'unknown' ? 'direction unknown' : language.direction;
    const description = language.script_profile_note ? `<p class="language-profile-note">${escapeHTML(language.script_profile_note)}</p>` : '';
    const contents = items || '<li>No bundled reader text; see separately recorded corpus leads.</li>';
    const writingMode = language.writing_mode ? ` · writing mode ${escapeHTML(language.writing_mode)}` : '';
    return `<article class="language-card"><div class="language-card-heading"><h3>${escapeHTML(language.language_name)}</h3><span lang="en">${escapeHTML(language.language_tag)} · script${language.script_code === 'Zzzz' || language.script_codes?.length === 1 ? '' : 's'} ${escapeHTML(scripts)} · ${escapeHTML(direction)}${writingMode}</span></div><ul>${contents}</ul>${description}</article>`;
  }).join('');
  const leads = registry?.translation_leads || [];
  const sourceLinks = ids => ids.map(id => state.sources.find(source => source.source_id === id)).filter(Boolean).map(source => `<a href="${escapeHTML(safeURL(source.url))}" target="_blank" rel="noopener noreferrer">${escapeHTML(source.source_name)} ↗</a>`).join(' · ');
  const translationHtml = leads.length ? `<h3>Book translation leads · not bundled</h3>${leads.map(lead => `<article class="translation-lead"><strong>${escapeHTML(lead.edition)}</strong><p>${escapeHTML(lead.translator)} · ${lead.translation_path ? lead.translation_path.map(languageLabel).map(escapeHTML).join(' → ') : 'translation path unknown'} · ${escapeHTML(lead.review_status)}</p><p>${escapeHTML(lead.notes)}</p><small>Rights: ${escapeHTML(lead.rights_status)} · ${sourceLinks(lead.source_ids || [])}</small></article>`).join('')}` : '';
  const corpusHtml = corpusLeads.length ? `<h3>Multi-book language/corpus leads · not bundled</h3>${corpusLeads.map(lead => `<article class="translation-lead"><strong>${escapeHTML(lead.title)}</strong><p>${escapeHTML(lead.publisher)} · ${escapeHTML(lead.publication_year)} · ${escapeHTML(lead.language_name)} (${escapeHTML(lead.language_tag)}, script ${escapeHTML(lead.script_code)}${lead.script_status ? ` · ${escapeHTML(lead.script_status)} for this witness` : ''}) · ${lead.translation_path ? lead.translation_path.map(languageLabel).map(escapeHTML).join(' → ') : 'translation path unknown'} · basis ${escapeHTML(lead.basis_language_tag)}</p><p>${escapeHTML(lead.scope_description)}</p><p>${escapeHTML(lead.contributors)} ${escapeHTML(lead.review_status)}</p><p>${escapeHTML(lead.notes)}</p><small>Rights: ${escapeHTML(lead.rights_status)} · ${sourceLinks(lead.source_ids || [])}</small></article>`).join('')}` : '';
  byId('translation-leads').innerHTML = translationHtml + corpusHtml;
}

function renderCanonCoverage() {
  const registry = JSON.parse(byId('archive-data').textContent).canon_registry;
  const available = state.canonBooks.filter(book => String(book.reader_status || '').startsWith('Bundled:')).length;
  byId('canon-coverage-summary').textContent = `${available} of ${state.canonBooks.length} Church-listed entries have bundled reader text`;
  const sections = ['Old Testament', 'New Testament'];
  byId('canon-coverage-list').innerHTML = sections.map(section => {
    const books = state.canonBooks.filter(book => book.section === section);
    return `<div class="canon-coverage-group"><h3>${escapeHTML(section)} <span>${books.length}</span></h3><div class="canon-coverage-grid">${books.map(book => {
      const hasReader = String(book.reader_status || '').startsWith('Bundled:');
      const sourceLabel = book.source_label && book.source_label !== book.display_name ? `<span class="canon-entry-source-label">Church list: ${escapeHTML(book.source_label)}</span>` : '';
      const mappingNote = book.mapping_note ? `<span class="canon-entry-mapping-note">${escapeHTML(book.mapping_note)}</span>` : '';
      return `<button class="canon-entry${hasReader ? ' canon-entry-ready' : ''}" type="button" data-canon-entry="${escapeHTML(book.canon_id)}"><span class="canon-entry-number">${book.section_number}</span><span class="canon-entry-title">${escapeHTML(book.display_name)}</span>${sourceLabel}<span class="canon-entry-status">${escapeHTML(book.reader_status)}</span>${mappingNote}</button>`;
    }).join('')}</div></div>`;
  }).join('');
  document.querySelectorAll('[data-canon-entry]').forEach(button => button.addEventListener('click', () => {
    const entry = state.canonBooks.find(book => book.canon_id === button.dataset.canonEntry);
    if (!entry) return;
    if (String(entry.reader_status || '').startsWith('Bundled:')) {
      state.readerId = entry.reader_id || state.readers.find(reader => reader.canon_id === entry.canon_id)?.reader_id || null;
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
  if (reader) state.readerId = reader.reader_id;
  const link = item => `<a href="${escapeHTML(safeURL(item.url))}"${item.url.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : ''}>${escapeHTML(item.source_name)}</a>`;
  const chapterCount = /^\d+$/.test(String(book.chapter_count || '')) ? `${escapeHTML(book.chapter_count)} chapters` : escapeHTML(book.chapter_count || 'Not established');
  byId('detail-panel').innerHTML = `
    <div class="detail-top"><div><span class="detail-index">${escapeHTML(book.catalogue_id)} · ${escapeHTML(book.tradition_group)}</span><h3>${escapeHTML(book.display_name)}</h3></div><button class="detail-close" aria-label="Close details">×</button></div>
    <span class="detail-status">${escapeHTML(book.identity_status)}</span>
    <dl class="detail-meta"><dt>Alternate names &amp; notes</dt><dd>${escapeHTML(book.alternate_names_or_notes || 'Alternate names not yet researched.')}</dd><dt>Edition / translation</dt><dd>${escapeHTML(book.edition_or_translation || 'Not identified')}</dd><dt>Chapter count</dt><dd>${chapterCount}</dd><dt>Chapter order</dt><dd>${escapeHTML(book.chapter_order_status || 'Not researched')}</dd><dt>Text &amp; completeness</dt><dd>${escapeHTML(book.text_availability_status || 'Not researched')} · ${escapeHTML(book.completeness_status || 'Not assessed')}</dd><dt>Reuse rights</dt><dd>${escapeHTML(book.rights_status || 'Not assessed; no edition selected')}</dd><dt>Catalogue source</dt><dd>${source ? link(source) : 'Local record source missing.'}</dd><dt>Evidence leads</dt><dd>${evidence.length ? evidence.map(link).join(' · ') : 'No evidence lead recorded yet.'}</dd></dl>
    ${reader ? '<a class="button button-gold detail-reader-link" href="#reader">Open the locally stored Geʽez reader ↓</a><p class="detail-warning">A source-based reader is available for this title. It is a historical Dillmann edition transcription, not the current official EOTC printed edition. Its source and transcription limitations are stated beside the text.</p>' : '<p class="detail-warning">No verified reader text is bundled for this title. Any locally archived source package and its limits are listed above.</p>'}`;
  byId('detail-panel').querySelector('.detail-close').addEventListener('click', () => { state.selected = null; renderBooks(); byId('detail-panel').innerHTML = '<div class="detail-empty"><span class="detail-star">✳</span><h3>Choose a title</h3><p>Open a catalogue record to see its alternate names, source, and current research status.</p></div>'; });
}

function renderReader() {
  const bookSelect = byId('reader-book');
  const languageSelect = byId('reader-language');
  if (!state.readers.length) {
    byId('reader-text').innerHTML = '<p class="reader-empty">No source-verified text is bundled yet.</p>';
    return;
  }
  const reader = state.readers.find(item => item.reader_id === state.readerId) || state.readers[0];
  state.readerId = reader.reader_id;
  bookSelect.innerHTML = state.readers.map(item => `<option value="${escapeHTML(item.reader_id)}"${item.reader_id === reader.reader_id ? ' selected' : ''}>${escapeHTML(item.title)}</option>`).join('');
  const companion = reader.parallel_translation;
  const languageOptions = [`<option value="${escapeHTML(reader.language_tag)}">${escapeHTML(reader.language)}</option>`];
  if (companion) languageOptions.push(`<option value="${escapeHTML(companion.language_tag)}">${escapeHTML(companion.language)}</option>`, '<option value="parallel">Parallel witnesses</option>');
  const priorMode = languageSelect.value;
  languageSelect.innerHTML = languageOptions.join('');
  languageSelect.value = languageOptions.some(option => option.includes(`value="${priorMode}"`)) ? priorMode : reader.language_tag;
  const chapter = reader.chapters.find(item => item.chapter === state.chapter) || reader.chapters[0];
  state.chapter = chapter.chapter;
  const mode = languageSelect.value;
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
  const sourceByLabel = new Map(chapter.verses.map(item => [String(item.number), item]));
  const englishByLabel = new Map((englishChapter?.verses || []).map(item => [String(item.number), item]));
  const labels = [...new Set([...sourceByLabel.keys(), ...englishByLabel.keys()])].sort((a, b) => {
    const parse = value => { const m = value.match(/^(\d+)([a-z]?)$/); return [Number(m?.[1] || 0), m?.[2] || '']; };
    const aa = parse(a), bb = parse(b); return aa[0] - bb[0] || aa[1].localeCompare(bb[1]);
  });
  const sectionLabel = reader.section_label || 'Chapter';
  byId('reader-chapter').innerHTML = reader.chapters.map(item => `<option value="${item.chapter}"${item.chapter === chapter.chapter ? ' selected' : ''}>${escapeHTML(sectionLabel)} ${item.chapter}</option>`).join('');
  const unitLabel = reader.unit_label || 'Verse';
  const marker = item => item?.source_marker ? `${item.number} · source ${item.source_marker}` : String(item?.number ?? '');
  const witness = (item, tag, cls, label) => `<div class="reader-witness ${cls}"><span class="reader-verse-number">${escapeHTML(label)}</span><span class="reader-witness-content" lang="${escapeHTML(tag)}" dir="${escapeHTML(direction(tag))}"${writingModeStyle(tag)}>${item ? escapeHTML(item.text) : '<span class="reader-gap">No entry carrying this printed label in this witness.</span>'}</span></div>`;
  const chapterHeading = Array.isArray(chapter.heading) && chapter.heading.length ? `<div class="reader-heading" lang="${escapeHTML(sourceTag)}" dir="${escapeHTML(direction(sourceTag))}"${writingModeStyle(sourceTag)}>${chapter.heading.map(item => `<p>${escapeHTML(item)}</p>`).join('')}</div>` : '';
  byId('reader-title').textContent = `${reader.title.split(' — ')[0]} · ${sectionLabel} ${chapter.chapter}${mode === 'parallel' ? ' · Parallel witnesses' : ` · ${mode === englishTag && companion ? 'English' : reader.language}`}`;
  const sectionCount = reader.section_unit_plural ? `${reader.chapter_count} ${reader.section_unit_plural}` : `${reader.chapter_count} chapters`;
  byId('reader-chapter-count').textContent = `${sectionCount} · ${reader.language}${companion ? ` + ${companion.language} companion` : ''}`;
  if (mode === 'parallel' && companion) {
    byId('reader-text').innerHTML = chapterHeading + labels.map(label => `<article class="reader-parallel-row"><div><span class="reader-witness-label">${escapeHTML(reader.language.toUpperCase())}</span>${witness(sourceByLabel.get(label), sourceTag, 'geez-witness', marker(sourceByLabel.get(label)) || label)}</div><div><span class="reader-witness-label">${escapeHTML(companion.title)}</span>${witness(englishByLabel.get(label), englishTag, 'english-witness', String(englishByLabel.get(label)?.number ?? label))}</div></article>`).join('');
    byId('reader-alignment-note').textContent = 'Paired by chapter and printed marker for navigation. Matching labels do not certify word-for-word alignment; unmatched labels remain visible.';
  } else if (companion && mode === englishTag) {
    byId('reader-text').innerHTML = chapterHeading + (englishChapter?.verses || []).map(item => `<p class="reader-verse">${witness(item, englishTag, 'english-witness', String(item.number))}</p>`).join('');
    byId('reader-alignment-note').textContent = companion.translation_basis;
  } else {
    byId('reader-text').innerHTML = chapterHeading + chapter.verses.map(item => `<p class="reader-verse">${witness(item, sourceTag, 'geez-witness', marker(item))}</p>`).join('');
    byId('reader-alignment-note').textContent = reader.unit_label ? `Source numbering note: ${reader.chapter_structure_note}` : '';
  }
  const notes = companion && mode !== sourceTag ? (englishChapter?.notes || []) : [];
  byId('reader-translation-notes').innerHTML = notes.length ? `<details><summary>Translator’s notes (${notes.length})</summary><ol>${notes.map(note => `<li><strong>${escapeHTML(note.verse)}${note.marker ? ` ${escapeHTML(note.marker)}` : ''}</strong> ${escapeHTML(note.text)}</li>`).join('')}</ol></details>` : '';
  byId('reader-prev').disabled = chapter.chapter === 1;
  byId('reader-next').disabled = chapter.chapter === reader.chapter_count;
  const citations = reader.source_ids.map(id => state.sources.find(item => item.source_id === id)).filter(Boolean);
  byId('reader-source').innerHTML = `${escapeHTML(reader.verification_status)} Sources: ${citations.map(item => `<a href="${escapeHTML(safeURL(item.url))}" target="_blank" rel="noopener noreferrer">${escapeHTML(item.source_name)} ↗</a>`).join(' · ')}`;
  byId('reader-permission').textContent = `${reader.copyright_notice}${companion ? ` English companion: ${companion.text_notice}` : ''}`;
  byId('reader-caveat-text').textContent = [reader.edition_scope, reader.chapter_structure_note, reader.transcription_note, reader.editorial_signs_note].filter(Boolean).join(' ');
}

byId('reader-book').addEventListener('change', event => { state.readerId = event.target.value; state.chapter = 1; renderReader(); });
byId('reader-chapter').addEventListener('change', event => { state.chapter = Number(event.target.value); renderReader(); });
byId('reader-prev').addEventListener('click', () => { state.chapter = Math.max(1, state.chapter - 1); renderReader(); });
byId('reader-next').addEventListener('click', () => { const reader = state.readers.find(item => item.reader_id === state.readerId); state.chapter = Math.min(reader?.chapter_count || 1, state.chapter + 1); renderReader(); });
byId('reader-language').addEventListener('change', renderReader);

function renderSources() {
  byId('source-list').innerHTML = state.sources.map(source => `
    <article class="source-card"${source.source_id === 'SRC-000' ? ' id="catalogue-method"' : ` id="source-${escapeHTML(source.source_id.toLowerCase())}"`}><span class="source-kind">${escapeHTML(source.archive_status)}</span><h3>${escapeHTML(source.source_name)}</h3><p>${escapeHTML(source.inspection_and_limitations)}</p><a href="${escapeHTML(safeURL(source.url))}"${source.url.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : ''}>${source.url.startsWith('http') ? 'Open source ↗' : 'Open archived item ↓'}</a></article>`).join('');
}

function renderRelated() {
  const sourceById = new Map(state.sources.map(source => [source.source_id, source]));
  byId('related-list').innerHTML = state.related.map(record => {
    const links = record.source_ids.map(id => sourceById.get(id)).filter(Boolean);
    return `<article class="related-card"><span class="related-category">${escapeHTML(record.category)}</span><h3>${escapeHTML(record.title)}</h3>${record.also_known_as ? `<p><strong>Also known as:</strong> ${escapeHTML(record.also_known_as)}</p>` : ''}<p>${escapeHTML(record.description)}</p><p class="related-boundary">${escapeHTML(record.not_canonical_note)}</p><div class="related-links">${links.map(source => `<a href="${escapeHTML(safeURL(source.url))}" target="_blank" rel="noopener noreferrer">${escapeHTML(source.source_name)} ↗</a>`).join('')}</div></article>`;
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
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {
      // The archive remains usable online if service-worker storage is unavailable.
    });
  }, { once: true });
}

init();
