(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.ReaderEnglish = api;
})(typeof globalThis === 'undefined' ? this : globalThis, function () {
  'use strict';
  function referenceFor(index, readers, readerId) {
    const record = index?.readers?.[readerId];
    if (!record?.english_reader_id || record.english_reader_id === readerId) return null;
    return readers.find(reader => reader.reader_id === record.english_reader_id && reader.language_tag === 'en') || null;
  }
  function suggestedChapter(source, chapters) {
    // This is a visible navigation convenience, never a statement of alignment.
    const label = source?.source_page_label;
    const number = label && /^\d+[ab]?$/.test(label) ? Number.parseInt(label, 10) : source?.chapter;
    return chapters.find(chapter => chapter.chapter === number)?.chapter || null;
  }
  function safeReaderPath(path) { return typeof path === 'string' && /^readers\/[a-z0-9-]+\.json$/.test(path); }
  return { referenceFor, suggestedChapter, safeReaderPath };
});
