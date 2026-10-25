(function attachReaderPackage(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.ReaderPackage = api;
})(typeof globalThis === 'undefined' ? this : globalThis, function createReaderPackageApi() {
  'use strict';

  const clone = value => JSON.parse(JSON.stringify(value));

  function createReaderPackage(archive, readerId, mode) {
    if (!archive || !Array.isArray(archive.readers)) throw new TypeError('Archive reader records are required.');
    const reader = archive.readers.find(item => item.reader_id === readerId);
    if (!reader) throw new RangeError(`Reader not found: ${readerId}`);

    const companion = reader.parallel_translation || null;
    const parallelMode = mode === 'parallel';
    const companionMode = Boolean(companion && mode === companion.language_tag);
    const sourceMode = mode === (reader.language_tag || 'und');
    if (!(parallelMode && companion) && !companionMode && !sourceMode) {
      throw new RangeError(`Language mode is not available for reader ${readerId}: ${mode}`);
    }

    const layers = [];
    if (sourceMode || parallelMode) {
      const { parallel_translation: omittedCompanion, ...sourceLayerData } = reader;
      const sourceLayer = clone(sourceLayerData);
      layers.push({
        layer_role: reader.text_origin || 'reader_text',
        language_tag: reader.language_tag || 'und',
        record_id: reader.translation_id || reader.reader_id,
        record: sourceLayer,
      });
    }
    if (companionMode || parallelMode) {
      layers.push({
        layer_role: companion.layer_role || 'historical_companion_translation',
        language_tag: companion.language_tag || 'und',
        record_id: companion.translation_id || null,
        record: clone(companion),
      });
    }

    const selectedIds = new Set(layers.map(layer => layer.record_id).filter(Boolean));
    const languageRecords = (archive.translation_registry?.languages || []).flatMap(profile =>
      (profile.records || [])
        .filter(record => record.reader_id === reader.reader_id)
        .filter(record => selectedIds.has(record.translation_id || reader.reader_id))
        .map(record => ({ language_tag: profile.language_tag, record: clone(record) }))
    );
    const selectedLanguageTags = new Set(layers.map(layer => layer.language_tag));
    const languageProfiles = (archive.translation_registry?.languages || [])
      .filter(profile => selectedLanguageTags.has(profile.language_tag))
      .map(profile => {
        const metadata = clone(profile);
        delete metadata.records;
        return metadata;
      });
    const basisLanguageTags = new Set(layers.flatMap(layer => [
      layer.record.basis_language_tag,
      ...(layer.record.translation_path || []),
    ]).filter(Boolean));
    const basisLanguageRecords = (archive.translation_registry?.basis_languages || [])
      .filter(record => basisLanguageTags.has(record.language_tag))
      .map(clone);
    const researchCorpus = (archive.translation_registry?.research_corpora || [])
      .find(item => item.reader_id === reader.reader_id) || null;
    const candidateCanonId = researchCorpus?.candidate_canon_id || null;
    const canonEntry = reader.canon_id
      ? (archive.canon_registry?.books || []).find(item => item.canon_id === reader.canon_id) || null
      : null;

    const referencedSourceIds = [...new Set([
      ...(reader.source_ids || []),
      ...layers.flatMap(layer => layer.record.source_ids || []),
      ...languageRecords.flatMap(item => item.record.source_ids || []),
      ...languageProfiles.flatMap(profile => profile.source_ids || []),
      ...basisLanguageRecords.flatMap(record => record.source_ids || []),
      ...(researchCorpus?.source_ids || []),
      ...(canonEntry?.source_ids || []),
    ])];
    const sourceById = new Map((archive.sources || []).map(source => [source.source_id, source]));
    const sourceRecords = referencedSourceIds.map(id => sourceById.get(id)).filter(Boolean).map(clone);
    const unresolvedSourceIds = referencedSourceIds.filter(id => !sourceById.has(id));

    const { chapters: omittedChapters, parallel_translation: omittedCompanion, ...readerMetadataData } = reader;
    const readerMetadata = clone(readerMetadataData);
    const mapping = researchCorpus ? {
      candidate_canon_id: candidateCanonId,
      state: researchCorpus.canon_mapping_state || 'unknown',
      note: researchCorpus.canon_mapping_note || 'No mapping note recorded.',
    } : (reader.canon_id ? { canon_id: reader.canon_id, state: 'linked' } : null);

    return {
      $schema: 'https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/schemas/reader-package.schema.json',
      format: 'Ethiopian Bible Library selected reader package',
      schema_version: 1,
      export_scope: parallelMode ? 'parallel_witnesses' : 'single_text_layer',
      base_reader: readerMetadata,
      text_layers: layers,
      language_layer_records: languageRecords,
      language_profiles: languageProfiles,
      basis_language_records: basisLanguageRecords,
      research_corpus_record: researchCorpus ? clone(researchCorpus) : null,
      canon_mapping: mapping,
      canon_entry: canonEntry ? clone(canonEntry) : null,
      source_ids: referencedSourceIds,
      source_records: sourceRecords,
      unresolved_source_ids: unresolvedSourceIds,
      integrity_note: 'Text and metadata are copied from this archive snapshot. Source links and rights notices are preserved; this export does not add textual verification, completeness, translation equivalence, canon authority, or redistribution permission.',
    };
  }

  function filename(readerId, languageTags) {
    const slug = String(readerId).toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '');
    const languages = [...new Set(languageTags)].map(tag => String(tag).toLowerCase().replace(/[^a-z0-9-]+/g, '-')).join('-');
    return `${slug || 'reader'}-${languages || 'und'}.json`;
  }

  return { createReaderPackage, filename };
});
