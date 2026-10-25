(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.ReaderAlignment = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function printedLabel(item, sourceWitness) {
    if (!item) return null;
    // unit_order is an archival sequence, not a printed verse label.
    const value = sourceWitness && item.source_marker != null
      ? item.source_marker
      : sourceWitness && item.unit_order != null
        ? null
        : item.number;
    return value == null || String(value).trim() === '' ? null : String(value);
  }

  function buildParallelRows(sourceUnits, englishVerses) {
    const source = Array.isArray(sourceUnits) ? sourceUnits : [];
    const english = Array.isArray(englishVerses) ? englishVerses : [];
    const sourceCounts = new Map();
    const englishCounts = new Map();
    for (const item of source) {
      const label = printedLabel(item, true);
      if (label !== null) sourceCounts.set(label, (sourceCounts.get(label) || 0) + 1);
    }
    for (const item of english) {
      const label = printedLabel(item, false);
      if (label !== null) englishCounts.set(label, (englishCounts.get(label) || 0) + 1);
    }

    const pairedEnglish = new Set();
    const rows = source.map(item => {
      const label = printedLabel(item, true);
      const candidate = label !== null && sourceCounts.get(label) === 1 && englishCounts.get(label) === 1
        ? english.findIndex((verse, index) => !pairedEnglish.has(index) && printedLabel(verse, false) === label)
        : -1;
      if (candidate >= 0) pairedEnglish.add(candidate);
      return { source: item, english: candidate >= 0 ? english[candidate] : null, label };
    });

    english.forEach((item, index) => {
      if (!pairedEnglish.has(index)) rows.push({ source: null, english: item, label: printedLabel(item, false) });
    });
    return rows;
  }

  return { buildParallelRows, printedLabel };
});
