const assert = require('node:assert/strict');
const archive = require('../archive.json');
const schema = require('../schemas/reader-package.schema.json');
const { createReaderPackage, filename } = require('../reader-package.js');

const genesisId = 'genesis-geez-dillmann-hacohen';
const geez = createReaderPackage(archive, genesisId, 'gez');
assert.equal(geez.export_scope, 'single_text_layer');
assert.equal(geez.text_layers.length, 1);
assert.equal(geez.text_layers[0].language_tag, 'gez');
assert.equal('parallel_translation' in geez.text_layers[0].record, false);
assert.ok(geez.text_layers[0].record.chapters.length > 0);
assert.ok(geez.language_profiles.some(item => item.language_tag === 'gez'));
assert.ok(geez.source_records.length > 0);
assert.deepEqual(geez.unresolved_source_ids, []);
assert.ok(geez.language_layer_records.every(item => item.language_tag === 'gez'));

const english = createReaderPackage(archive, genesisId, 'en');
assert.equal(english.text_layers.length, 1);
assert.equal(english.text_layers[0].language_tag, 'en');
assert.equal(english.text_layers[0].record.translation_id, 'genesis-english-brenton-lxx-1851');
assert.ok(english.basis_language_records.some(item => item.language_tag === 'grc'));
assert.ok(english.language_layer_records.every(item => item.language_tag === 'en'));

const parallel = createReaderPackage(archive, genesisId, 'parallel');
assert.equal(parallel.export_scope, 'parallel_witnesses');
assert.deepEqual(parallel.text_layers.map(item => item.language_tag), ['gez', 'en']);
assert.ok(parallel.language_layer_records.some(item => item.language_tag === 'gez'));
assert.ok(parallel.language_layer_records.some(item => item.language_tag === 'en'));

const jobReader = archive.readers.find(item => item.reader_id === 'job-brenton-lxx-1851-research');
const job = createReaderPackage(archive, jobReader.reader_id, 'en');
assert.equal(job.text_layers.length, 1);
assert.equal(job.text_layers[0].record_id, jobReader.translation_id);
assert.equal(job.research_corpus_record.reader_id, jobReader.reader_id);
assert.equal(job.canon_mapping.state, 'uncertain');
assert.equal(job.canon_entry, null);

for (const readerId of ['brenton-lxx-first-ki-research', 'brenton-lxx-pro-research', 'brenton-lxx-lam-research']) {
  const reader = archive.readers.find(item => item.reader_id === readerId);
  assert.ok(reader, `missing standalone research reader ${readerId}`);
  const output = createReaderPackage(archive, readerId, 'en');
  assert.equal(output.research_corpus_record.canon_mapping_state, 'not_mapped');
  assert.equal(output.canon_entry, null);
  assert.ok(output.text_layers[0].record.chapters.length > 0);
}
const proverbsReader = archive.readers.find(item => item.reader_id === 'brenton-lxx-pro-research');
const proverbsPackage = createReaderPackage(archive, proverbsReader.reader_id, 'en');
const proverbsChapter30 = proverbsPackage.text_layers[0].record.chapters.find(item => item.chapter === 30);
assert.ok(proverbsChapter30.verses.some(item => item.number === '1' && item.source_text_state === 'marker_only' && item.text === ''));
assert.ok(proverbsChapter30.notes.some(item => item.verse === '1' && item.text === 'See chapter 24 for the content of chapter 30.'));

for (const output of [geez, english, parallel, job]) {
  assert.equal(output.$schema, schema.$id);
  for (const key of schema.required) assert.ok(Object.hasOwn(output, key), `missing schema field ${key}`);
  const expectedIds = new Set(output.source_ids);
  const recordIds = new Set(output.source_records.map(item => item.source_id));
  assert.deepEqual([...expectedIds].filter(id => !recordIds.has(id)), output.unresolved_source_ids);
}

assert.match(filename('../unsafe reader', ['en', 'gez']), /^unsafe-reader-en-gez\.json$/);
assert.throws(() => createReaderPackage(archive, genesisId, 'ti'), /Language mode is not available/);
assert.throws(() => createReaderPackage(archive, 'missing-reader', 'en'), /Reader not found/);
console.log('Reader package export checks passed for source, translation, parallel, and research views.');
