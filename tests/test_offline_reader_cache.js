const assert = require('node:assert/strict');
const { createPlan, formatMiB, inspect, save } = require('../offline-reader-cache.js');

const readers = [
  { reader_id: 'book-one', reader_data_url: 'readers/book-one.json' },
  { reader_id: 'book-two', reader_data_url: 'readers/book-two.json' },
];
const manifest = { files: [
  { path: 'readers/book-one.json', size_bytes: 1024 },
  { path: 'readers/book-two.json', size_bytes: 2048 },
] };
const entries = new Map();
const cache = {
  async match(url) { return entries.get(typeof url === 'string' ? url : url.url); },
  async put(url, value) { entries.set(typeof url === 'string' ? url : url.url, value); },
};
const cacheStorage = {
  async keys() { return ['ethiopian-bible-library-shell-v28']; },
  async open() { return cache; },
};

(async () => {
  const plan = createPlan(readers, manifest);
  assert.equal(plan.count, 2);
  assert.equal(plan.totalBytes, 3072);
  assert.equal(formatMiB(1024 * 1024), '1.0 MiB');
  assert.throws(() => createPlan([{ reader_data_url: '../secret.json' }], manifest), /unsafe/);
  assert.throws(() => createPlan([{ reader_data_url: 'readers/missing.json' }], manifest), /missing/);

  const baseUrl = 'https://example.test/library/';
  await cache.put(`${baseUrl}readers/book-one.json`, { ok: true });
  const before = await inspect(plan, { baseUrl, cacheStorage });
  assert.deepEqual(before, { cachedCount: 1, cachedBytes: 1024, remainingCount: 1, remainingBytes: 2048 });

  const progress = [];
  let fetchCount = 0;
  const result = await save(plan, {
    baseUrl,
    cacheStorage,
    fetchImpl: async (url, options) => {
      fetchCount += 1;
      assert.equal(url, `${baseUrl}readers/book-two.json`);
      assert.equal(options.headers['X-Archive-Bulk-Cache'], '1');
      await cache.put(url, { ok: true });
      return { ok: true, status: 200 };
    },
    onProgress: value => progress.push(value),
  });
  assert.equal(fetchCount, 1, 'already cached reader files should be skipped');
  assert.deepEqual(result, { completed: 2, total: 2, completedBytes: 3072, totalBytes: 3072, skipped: 1 });
  assert.equal(progress.at(-1).completed, 2);
  assert.equal(progress.at(-1).skipped, 1);

  const controller = new AbortController();
  controller.abort();
  await assert.rejects(save(createPlan([readers[1]], manifest), {
    baseUrl,
    cacheStorage: { async keys() { return []; }, async open() { return { async match() { return undefined; } }; } },
    fetchImpl: async () => { throw new Error('an aborted save must not start a request'); },
    signal: controller.signal,
  }), error => error.name === 'AbortError');

  await assert.rejects(save(createPlan([readers[1]], manifest), {
    baseUrl,
    cacheStorage: { async keys() { return []; }, async open() { return { async match() { return undefined; } }; } },
    fetchImpl: async () => ({ ok: false, status: 503 }),
  }), /HTTP 503/);
  process.stdout.write('Offline reader-cache checks passed: safe manifest plan, cached-file skipping, progress, storage confirmation, and HTTP errors.\n');
})().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; });
