(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.OfflineReaderCache = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const CACHE_PREFIX = 'ethiopian-bible-library-';
  const SAFE_READER_PATH = /^readers\/[a-z0-9-]+\.json$/;

  function createPlan(readerRecords, manifest) {
    if (!Array.isArray(readerRecords) || !Array.isArray(manifest?.files)) {
      throw new TypeError('Reader records and a file manifest are required.');
    }
    const files = new Map(manifest.files.map(file => [file.path, file]));
    const seen = new Set();
    const readers = readerRecords.map(reader => {
      const path = reader.reader_data_url;
      const file = files.get(path);
      if (typeof path !== 'string' || !SAFE_READER_PATH.test(path) || !file
          || !Number.isSafeInteger(file.size_bytes) || file.size_bytes < 0 || seen.has(path)) {
        throw new Error(`Reader file is missing, unsafe, duplicated, or lacks a valid size: ${String(path)}.`);
      }
      seen.add(path);
      return { reader_id: reader.reader_id, path, size_bytes: file.size_bytes };
    });
    return {
      readers,
      count: readers.length,
      totalBytes: readers.reduce((sum, reader) => sum + reader.size_bytes, 0),
    };
  }

  function formatMiB(bytes) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
  }

  function absoluteURL(path, baseUrl) {
    const base = new URL(baseUrl);
    const target = new URL(path, base);
    if (target.origin !== base.origin || !target.href.startsWith(base.href)) {
      throw new Error(`Reader path escapes this site: ${path}.`);
    }
    return target.href;
  }

  async function cachedReaderURLs(plan, { baseUrl, cacheStorage = globalThis.caches } = {}) {
    if (!cacheStorage?.keys || !cacheStorage?.open) throw new Error('This browser does not expose Cache Storage.');
    const cacheNames = (await cacheStorage.keys()).filter(name => name.startsWith(CACHE_PREFIX));
    const caches = await Promise.all(cacheNames.map(name => cacheStorage.open(name)));
    const cached = new Set();
    for (const reader of plan.readers) {
      const url = absoluteURL(reader.path, baseUrl);
      for (const cache of caches) {
        if (await cache.match(url)) {
          cached.add(reader.path);
          break;
        }
      }
    }
    return cached;
  }

  async function inspect(plan, options = {}) {
    const cached = await cachedReaderURLs(plan, options);
    const cachedBytes = plan.readers.reduce((sum, reader) => sum + (cached.has(reader.path) ? reader.size_bytes : 0), 0);
    return { cachedCount: cached.size, cachedBytes, remainingCount: plan.count - cached.size, remainingBytes: plan.totalBytes - cachedBytes };
  }

  async function save(plan, { baseUrl, cacheStorage = globalThis.caches, fetchImpl = globalThis.fetch, signal, onProgress = () => {} } = {}) {
    if (typeof fetchImpl !== 'function') throw new Error('This browser cannot download the reader files.');
    const cached = await cachedReaderURLs(plan, { baseUrl, cacheStorage });
    const initiallyCachedCount = cached.size;
    let completed = cached.size;
    let completedBytes = plan.readers.reduce((sum, reader) => sum + (cached.has(reader.path) ? reader.size_bytes : 0), 0);
    onProgress({ completed, total: plan.count, completedBytes, totalBytes: plan.totalBytes, skipped: cached.size });

    for (const reader of plan.readers) {
      if (signal?.aborted) throw new DOMException('Offline save cancelled.', 'AbortError');
      if (cached.has(reader.path)) continue;
      const url = absoluteURL(reader.path, baseUrl);
      const response = await fetchImpl(url, {
        credentials: 'same-origin',
        headers: { 'X-Archive-Bulk-Cache': '1' },
        signal,
      });
      if (!response?.ok) throw new Error(`Could not save ${reader.path} (HTTP ${response?.status ?? 'unknown'}).`);
      const updated = await cachedReaderURLs({ readers: [reader] }, { baseUrl, cacheStorage });
      if (!updated.has(reader.path)) throw new Error(`The browser did not confirm saved storage for ${reader.path}.`);
      cached.add(reader.path);
      completed += 1;
      completedBytes += reader.size_bytes;
      onProgress({ completed, total: plan.count, completedBytes, totalBytes: plan.totalBytes, skipped: initiallyCachedCount });
    }
    return { completed, total: plan.count, completedBytes, totalBytes: plan.totalBytes, skipped: initiallyCachedCount };
  }

  return { createPlan, formatMiB, inspect, save };
});
