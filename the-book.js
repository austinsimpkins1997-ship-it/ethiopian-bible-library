/* Optional, local reading records. Never edits or certifies scripture. */
(function (global) {
  'use strict';
  const KEY = 'ethiopian-bible-library-the-book-v1';
  const LIMIT = 200;
  const MAX_BYTES = 1500000;
  const TIME_FIELDS = ['event', 'observation', 'recollection', 'record_creation', 'publication', 'discovery', 'interpretation', 'as_of'];
  const TRANSLATION_FIELDS = ['source_domain', 'target_domain', 'original_expression', 'intended_meaning', 'preserved_properties', 'lost_information', 'new_assumptions', 'evidence_status'];
  const FIELDS = ['passage', 'perspective', 'observation', 'interpretation', 'unknowns', 'kind', 'evidence', 'standing', 'review', 'evidence-basis', 'mind', 'body', 'soul', 'comparison', 'identity', 'relation'];
  const KINDS = ['interpretation', 'source_observation', 'reconstruction', 'theological', 'symbolic', 'proposal'];
  const STATUSES = ['Unverified', 'Unknown', 'Unresolved', 'Disputed', 'Unsupported', 'Conflicting', 'Unavailable', 'Historically attested', 'Reconstructed', 'Validated'];
  const isPackage = value => typeof value === 'string' && /^readers\/[a-zA-Z0-9_-]+\.json$/.test(value);
  function validateModel(model, readers) {
    if (model?.schema_version !== 1 || !Array.isArray(model.readers) || !Array.isArray(model.scope_paths)
        || !Array.isArray(model.standings) || !Array.isArray(model.review_steps)
        || model.standings.join('|') !== 'WAS|IS|BECOMING|BECAME'
        || model.review_steps.join('|') !== 'WAS|IS|BECOMING|BECAME'
        || model.scope_paths.map(p => p.id).join('') !== 'ABCD'
        || !Array.isArray(model.principles) || !Array.isArray(model.canon_sources)
        || model.completion_checks?.length !== 7) throw new Error('The reading map has an unsupported structure.');
    const expected = new Set(readers.map(r => r.reader_id));
    const actual = new Set(model.readers.map(r => r.reader_id));
    if (expected.size !== actual.size || actual.size !== model.readers.length
        || model.reader_count !== actual.size || [...expected].some(id => !actual.has(id))
        || model.readers.some(r => !isPackage(r.package_path))) throw new Error('The reading map does not match this reader collection.');
    return model;
  }
  function validateRecord(record, model) {
    if (!record || typeof record !== 'object' || record.schema_version !== 1
        || typeof record.id !== 'string' || !record.id || record.id.length > 150
        || !Number.isInteger(record.revision) || record.revision < 1
        || !(record.parent_id === null || typeof record.parent_id === 'string')
        || typeof record.recorded_at !== 'string' || Number.isNaN(Date.parse(record.recorded_at))
        || !model.readers.some(r => r.reader_id === record.context?.reader_id)
        || !Number.isInteger(record.context?.source_chapter) || record.context.source_chapter < 1
        || !model.scope_paths.some(p => p.id === record.scope)
        || record.fields === null || typeof record.fields !== 'object') throw new Error('Invalid reading record.');
    const fields = record.fields;
    for (const key of [...FIELDS, ...TIME_FIELDS.map(k => 'time-' + k), ...TRANSLATION_FIELDS.map(k => 'utc-' + k)]) {
      if (typeof fields[key] !== 'string' || fields[key].length > 5000) throw new Error('Invalid reading record field: ' + key);
    }
    if (!fields.passage.trim() || !fields.observation.trim()) throw new Error('Give the passage and a source observation.');
    if ((fields.standing && !model.standings.includes(fields.standing))
        || (fields.review && !model.review_steps.includes(fields.review))) throw new Error('Keep standing and review step separate; TO_BE is not a standing.');
    if (!KINDS.includes(fields.kind) || !STATUSES.includes(fields.evidence)
        || !['unresolved', 'same', 'distinct'].includes(fields.identity)
        || !['', 'Analogical', 'Partial', 'Exact under stated assumptions'].includes(fields.relation)) throw new Error('Unsupported reading-record classification.');
    if (fields.evidence === 'Validated' && !fields['evidence-basis'].trim()) throw new Error('Record the basis for your validation label; it is not the library’s certification.');
    if (!Array.isArray(record.checks) || record.checks.length !== 7 || record.checks.some(x => typeof x !== 'boolean')) throw new Error('Invalid local review checklist.');
    const status = record.checks.every(Boolean) ? 'user_reviewed_local_course' : 'open_course';
    if (record.course_status !== status) throw new Error('Local course status does not match the checklist.');
    if (record.authority !== 'reader_authored_not_library_verified') throw new Error('Reading records must retain their author/review boundary.');
    return record;
  }
  function readStore(storage) {
    try {
      const raw = storage.getItem(KEY);
      if (raw === null) return {records: [], error: null};
      if (raw.length > MAX_BYTES) throw new Error('Stored notes exceed the supported size. Export or recover the existing browser value before clearing it.');
      const data = JSON.parse(raw);
      if (data?.schema_version !== 1 || !Array.isArray(data.records) || data.records.length > LIMIT) throw new Error('Stored notes have an unsupported format. They have not been overwritten.');
      return {records: data.records, error: null};
    } catch (error) { return {records: [], error: error.message}; }
  }
  function appendRecord(storage, records, record, model) {
    validateRecord(record, model);
    records.forEach(item => validateRecord(item, model));
    if (records.length >= LIMIT) throw new Error('The 200-revision limit is reached. Export notes before clearing saved copies.');
    if (records.some(item => item.id === record.id)) throw new Error('This revision ID already exists.');
    if (record.parent_id) {
      const parent = records.find(item => item.id === record.parent_id);
      if (!parent || parent.context.reader_id !== record.context.reader_id
          || parent.context.source_chapter !== record.context.source_chapter
          || record.revision !== parent.revision + 1) throw new Error('A revision must retain its source witness and chapter.');
    } else if (record.revision !== 1) throw new Error('A new course starts at revision 1.');
    const next = [...records, record];
    const data = JSON.stringify({schema_version: 1, records: next});
    if (data.length > MAX_BYTES) throw new Error('Notes are too large for this local store; export before starting a fresh store.');
    storage.setItem(KEY, data); // Exceptions are reported; nothing is claimed saved until this returns.
    return next;
  }
  function create({document, readers, openReader}) {
    const byId = id => document.getElementById('the-book-' + id);
    if (!byId('disclosure')) return null;
    const win = document.defaultView;
    let model, current, bound, parent = null, records = [], storageError = null, loading = false, dirty = false, scope = 'D', currentReady = false;
    const node = (tag, text, parentNode) => {
      const element = document.createElement(tag);
      if (text !== undefined) element.textContent = text;
      if (parentNode) parentNode.append(element);
      return element;
    };
    const message = text => { byId('note-status').textContent = text; };
    const fields = () => [...FIELDS, ...TIME_FIELDS.map(k => 'time-' + k), ...TRANSLATION_FIELDS.map(k => 'utc-' + k)];
    function download(data, name) {
      const blob = new win.Blob([JSON.stringify(data, null, 2) + '\n'], {type: 'application/json'});
      const url = win.URL.createObjectURL(blob);
      const link = node('a'); link.href = url; link.download = name;
      document.body.append(link); link.click(); link.remove();
      win.setTimeout(() => win.URL.revokeObjectURL(url), 1000);
    }
    function showContext() {
      byId('context').textContent = current
        ? `${current.title} · source position ${current.source_chapter}${current.source_label ? ' / label ' + current.source_label : ''} · ${current.language_tag || 'und'}. Edition: ${current.edition || 'Unknown'}. Sources: ${(current.source_ids || []).join(', ') || 'Unknown'}. An English comparison may be a separate edition.`
        : 'Open any bundled reader above to choose a passage.';
      byId('start').disabled = !current || !currentReady;
    }
    function renderReaders() {
      const query = byId('search').value.normalize('NFKC').trim().toLocaleLowerCase();
      const matches = readers.filter(r => !query || [r.reader_id, r.title, r.display_name, r.language, r.language_tag, r.edition].filter(Boolean).join(' ').normalize('NFKC').toLocaleLowerCase().includes(query));
      const previous = byId('reader').value;
      byId('reader').replaceChildren();
      for (const reader of matches) {
        const option = node('option', reader.display_name || reader.title, byId('reader'));
        option.value = reader.reader_id;
      }
      if (matches.some(r => r.reader_id === previous)) byId('reader').value = previous;
      byId('reader-count').textContent = `${matches.length} matching witnesses / ${readers.length} bundled readers. Not a count of canonical books.`;
      byId('open-reader').disabled = matches.length === 0;
    }
    function setScope(value) {
      scope = value;
      const path = model.scope_paths.find(p => p.id === scope);
      byId('path-description').textContent = path.description;
      byId('paths').querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.scope === scope)));
    }
    function renderNotes() {
      byId('notes').replaceChildren();
      byId('storage-status').textContent = storageError
        ? 'Local storage is unavailable or needs recovery: ' + storageError + ' Existing values have not been overwritten.'
        : `${records.length} saved revisions on this browser profile (maximum ${LIMIT}). Earlier revisions remain in the export.${win.navigator.locks?.request ? '' : ' This browser cannot coordinate simultaneous tab saves; use one tab for notes.'}`;
      for (const item of records.slice(-30).reverse()) {
        const li = node('li', undefined, byId('notes'));
        node('span', `${item.context?.title || item.context?.reader_id || 'Unknown witness'} · ${item.fields?.passage || 'Unresolved passage'} · revision ${item.revision} · ${item.recorded_at} · ${item.course_status}. `, li);
        const button = node('button', 'Open this revision', li); button.type = 'button';
        button.addEventListener('click', () => {
          if (!discardDraft()) return;
          try {
            validateRecord(item, model);
            bound = structuredClone(item.context); parent = item;
            for (const name of fields()) byId(name).value = item.fields[name];
            setScope(item.scope);
            item.checks.forEach((checked, i) => { byId('check-' + i).checked = checked; });
            byId('bound-context').textContent = `${bound.title} · bound source position ${bound.source_chapter}${bound.source_label ? ' / label ' + bound.source_label : ''}. This opens revision ${item.revision}; saving adds a new revision.`;
            byId('form').hidden = false; dirty = false; byId('passage').focus();
          } catch (error) { message(error.message + ' The saved value has not been changed.'); }
        });
      }
      if (records.length > 30) node('li', 'Only the latest 30 revisions are listed. Export includes all saved revisions.', byId('notes'));
    }
    function discardDraft() { return !dirty || win.confirm('Discard this unsaved worksheet? Saved revisions will remain.'); }
    function start() {
      if (!model || !current || !currentReady || !discardDraft()) return;
      bound = structuredClone(current); parent = null;
      byId('form').reset();
      byId('passage').value = bound.source_label ? `Source label ${bound.source_label} (position ${bound.source_chapter})` : `Source chapter ${bound.source_chapter}`;
      byId('bound-context').textContent = `${bound.title} · bound source position ${bound.source_chapter}${bound.source_label ? ' / label ' + bound.source_label : ''}. Reader changes will not reassign this note.`;
      byId('form').hidden = false; dirty = false; message('New unsaved reading record.'); byId('observation').focus();
    }
    async function load() {
      if (loading || model) return;
      loading = true; byId('retry').hidden = true;
      byId('load-status').textContent = 'Loading the reading map…';
      try {
        const response = await win.fetch('the-book.json', {credentials: 'same-origin'});
        if (!response.ok) throw new Error('The local reading map could not be loaded.');
        const candidate = validateModel(await response.json(), readers);
        for (const id of ['paths', 'principles', 'canon-sources', 'times', 'translation-fields', 'checks']) byId(id).replaceChildren();
        for (const id of ['standing', 'review']) while (byId(id).options.length > 1) byId(id).remove(1);
        // Populate only from the checked local map. Supplied strings never execute as HTML.
        for (const path of candidate.scope_paths) {
          const button = node('button', path.id + ' · ' + path.title, byId('paths'));
          button.type = 'button'; button.dataset.scope = path.id; button.setAttribute('aria-pressed', 'false');
          button.addEventListener('click', () => { setScope(path.id); if (bound) dirty = true; });
        }
        for (const principle of candidate.principles) {
          const details = node('details', undefined, byId('principles'));
          node('summary', principle.title, details); node('p', principle.text, details);
        }
        for (const source of candidate.canon_sources) {
          const p = node('p', undefined, byId('canon-sources'));
          const url = new URL(source.url);
          if (url.protocol !== 'https:') throw new Error('Unsupported canon source link.');
          const a = node('a', source.title, p); a.href = url.href; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.referrerPolicy = 'no-referrer';
          node('span', ` · reviewed ${source.reviewed_on}. ${source.limit}`, p);
        }
        for (const field of TIME_FIELDS) {
          const box = node('div', undefined, byId('times'));
          const label = node('label', field.replaceAll('_', ' ') + ' time (optional)', box); label.htmlFor = 'the-book-time-' + field;
          const input = node('input', undefined, box); input.id = label.htmlFor; input.maxLength = 300; input.placeholder = 'Unknown unless you can identify it';
        }
        for (const field of TRANSLATION_FIELDS) {
          const box = node('div', undefined, byId('translation-fields'));
          const label = node('label', field.replaceAll('_', ' '), box); label.htmlFor = 'the-book-utc-' + field;
          const input = node('textarea', undefined, box); input.id = label.htmlFor; input.maxLength = 2000; input.rows = 2;
        }
        for (const [i, text] of candidate.completion_checks.entries()) {
          const label = node('label', undefined, byId('checks'));
          const input = node('input', undefined, label); input.type = 'checkbox'; input.id = 'the-book-check-' + i;
          node('span', `${i + 1}. ${text}`, label);
        }
        for (const [name, values] of [['standing', candidate.standings], ['review', candidate.review_steps]]) {
          for (const value of values) { const option = node('option', value, byId(name)); option.value = value; }
        }
        model = candidate;
        let loaded;
        try { loaded = readStore(win.localStorage); } catch (error) { loaded = {records: [], error: error.message}; }
        records = loaded.records; storageError = loaded.error;
        if (!storageError) {
          try { records.forEach(record => validateRecord(record, model)); }
          catch (error) { storageError = error.message; }
        }
        byId('load-status').textContent = `${candidate.reader_count} reader worksheets available. ${candidate.source.coverage}`;
        byId('map').hidden = false;
        renderReaders(); setScope(scope); showContext(); renderNotes();
      } catch (error) {
        byId('load-status').textContent = error.message + ' Scripture readers remain available above.';
        byId('retry').hidden = false;
      } finally { loading = false; }
    }
    byId('disclosure').addEventListener('toggle', () => { if (byId('disclosure').open) void load(); });
    byId('retry').addEventListener('click', load);
    byId('search').addEventListener('input', renderReaders);
    byId('open-reader').addEventListener('click', () => { if (readers.some(r => r.reader_id === byId('reader').value)) openReader(byId('reader').value); });
    byId('start').addEventListener('click', start);
    byId('form').addEventListener('input', () => { dirty = true; });
    byId('form').addEventListener('change', () => { dirty = true; });
    byId('form').addEventListener('submit', async event => {
      event.preventDefault();
      if (!bound || !model) return;
      const submit = byId('form').querySelector('[type="submit"]');
      submit.disabled = true;
      try {
        const save = () => {
        if (storageError) throw new Error('Resolve or export the existing local-store problem before saving.');
        // Reject stale concurrent writes from another tab rather than losing a revision.
        const latest = readStore(win.localStorage);
        if (latest.error || JSON.stringify(latest.records) !== JSON.stringify(records)) throw new Error('Saved notes changed in another tab or are unavailable. Export this worksheet, then reload before saving.');
        const checks = model.completion_checks.map((_, i) => byId('check-' + i).checked);
        const record = {
          schema_version: 1, id: win.crypto.randomUUID(), parent_id: parent?.id || null,
          revision: parent ? parent.revision + 1 : 1, recorded_at: new Date().toISOString(),
          context: structuredClone(bound), scope,
          fields: Object.fromEntries(fields().map(name => [name, byId(name).value])), checks,
          course_status: checks.every(Boolean) ? 'user_reviewed_local_course' : 'open_course',
          authority: 'reader_authored_not_library_verified', framework_source_sha256: model.source.sha256,
        };
        records = appendRecord(win.localStorage, records, record, model);
        parent = record; dirty = false; renderNotes();
        message(`Saved revision ${record.revision} on this device. ${record.course_status === 'open_course' ? 'The local course remains open.' : 'Your review is recorded; no factual or theological certification is implied.'}`);
        };
        if (win.navigator.locks?.request) await win.navigator.locks.request(KEY, save);
        else save();
      } catch (error) { message('Not saved: ' + error.message); }
      finally { submit.disabled = false; }
    });
    byId('export').addEventListener('click', () => {
      try {
        const existing = win.localStorage.getItem(KEY);
        download({schema_version: 1, kind: 'reader_authored_notes_not_scripture', saved_store_raw: existing,
          records, unsaved_worksheet: bound && model ? {context: bound, scope, fields: Object.fromEntries(fields().map(name => [name, byId(name).value]))} : null,
          framework_source: model?.source || null}, 'the-book-reading-notes.json');
        message('Export prepared. It includes saved revisions and the current worksheet separately; an unsaved worksheet remains unsaved.');
      } catch (error) { message('Could not export: ' + error.message); }
    });
    byId('clear').addEventListener('click', () => {
      if (!win.confirm('Clear The Book saved notes on this browser profile? Export a backup first if you need them.')) return;
      try { win.localStorage.removeItem(KEY); records = []; storageError = null; parent = null; renderNotes(); message('Saved notes cleared on this device. The open worksheet and scripture were not changed.'); }
      catch (error) { message('Could not clear saved notes: ' + error.message); }
    });
    win.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
    if (byId('disclosure').open) void load();
    return {setContext(reader, chapter) {
      currentReady = Array.isArray(reader.chapters);
      const sourceChapter = reader.chapters?.find(item => item.chapter === Number(chapter));
      current = {reader_id: reader.reader_id, title: reader.display_name || reader.title,
        source_chapter: Number(chapter) || 1, language_tag: reader.language_tag,
        source_label: sourceChapter?.source_page_label || null,
        edition: reader.edition, source_ids: [...(reader.source_ids || [])]};
      showContext();
    }};
  }
  const api = {create, validateModel, validateRecord, readStore, appendRecord, KEY, TIME_FIELDS, TRANSLATION_FIELDS, FIELDS};
  if (typeof module === 'object' && module.exports) module.exports = api;
  else global.TheBook = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
