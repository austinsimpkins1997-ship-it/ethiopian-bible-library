const state = { books: [], sources: [], related: [], query: '', filter: 'All', selected: null };
const byId = (id) => document.getElementById(id);
const escapeHTML = (value = '') => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeURL = (value) => { if (typeof value === 'string' && value.startsWith('#')) return value; try { const u = new URL(value); return ['https:','http:'].includes(u.protocol) ? u.href : '#'; } catch { return '#'; } };

async function init() {
  try {
    const archiveNode = byId('archive-data');
    if (!archiveNode) throw new Error('Embedded archive data is missing. Regenerate index.html from archive.json.');
    const data = JSON.parse(archiveNode.textContent);
    state.books = Array.isArray(data.catalogue) ? data.catalogue : [];
    state.sources = Array.isArray(data.sources) ? data.sources : [];
    state.related = Array.isArray(data.related_texts) ? data.related_texts : [];
    byId('book-count').textContent = state.books.length;
    byId('all-count').textContent = state.books.length;
    byId('source-count').textContent = state.sources.length;
    renderBooks(); renderSources(); renderRelated();
  } catch (error) {
    byId('results-label').textContent = 'The catalogue could not be loaded.';
    byId('book-grid').innerHTML = `<div class="load-error"><strong>Archive unavailable</strong><p>${escapeHTML(error.message)}. Rebuild the embedded archive from archive.json.</p></div>`;
  }
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
  const link = item => `<a href="${escapeHTML(safeURL(item.url))}"${item.url.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : ''}>${escapeHTML(item.source_name)}</a>`;
  const chapterCount = /^\d+$/.test(String(book.chapter_count || '')) ? `${escapeHTML(book.chapter_count)} chapters` : escapeHTML(book.chapter_count || 'Not established');
  byId('detail-panel').innerHTML = `
    <div class="detail-top"><div><span class="detail-index">${escapeHTML(book.catalogue_id)} · ${escapeHTML(book.tradition_group)}</span><h3>${escapeHTML(book.display_name)}</h3></div><button class="detail-close" aria-label="Close details">×</button></div>
    <span class="detail-status">${escapeHTML(book.identity_status)}</span>
    <dl class="detail-meta"><dt>Alternate names &amp; notes</dt><dd>${escapeHTML(book.alternate_names_or_notes || 'Alternate names not yet researched.')}</dd><dt>Edition / translation</dt><dd>${escapeHTML(book.edition_or_translation || 'Not identified')}</dd><dt>Chapter count</dt><dd>${chapterCount}</dd><dt>Chapter order</dt><dd>${escapeHTML(book.chapter_order_status || 'Not researched')}</dd><dt>Text &amp; completeness</dt><dd>${escapeHTML(book.text_availability_status || 'Not researched')} · ${escapeHTML(book.completeness_status || 'Not assessed')}</dd><dt>Reuse rights</dt><dd>${escapeHTML(book.rights_status || 'Not assessed; no edition selected')}</dd><dt>Catalogue source</dt><dd>${source ? link(source) : 'Local record source missing.'}</dd><dt>Evidence leads</dt><dd>${evidence.length ? evidence.map(link).join(' · ') : 'No evidence lead recorded yet.'}</dd></dl>
    <p class="detail-warning">This is a research catalogue record, not a verified reader. Evidence leads establish context only; row identity, mapping, edition, text availability, chapter structure, completeness, and reuse rights remain unresolved as shown above.</p>`;
  byId('detail-panel').querySelector('.detail-close').addEventListener('click', () => { state.selected = null; renderBooks(); byId('detail-panel').innerHTML = '<div class="detail-empty"><span class="detail-star">✳</span><h3>Choose a title</h3><p>Open a catalogue record to see its alternate names, source, and current research status.</p></div>'; });
}

function renderSources() {
  byId('source-list').innerHTML = state.sources.map(source => `
    <article class="source-card"${source.source_id === 'SRC-000' ? ' id="catalogue-method"' : ''}><span class="source-kind">${escapeHTML(source.archive_status)}</span><h3>${escapeHTML(source.source_name)}</h3><p>${escapeHTML(source.inspection_and_limitations)}</p><a href="${escapeHTML(safeURL(source.url))}"${source.url.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : ''}>${source.url.startsWith('http') ? 'Open source ↗' : 'View catalogue method ↗'}</a></article>`).join('');
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
init();
