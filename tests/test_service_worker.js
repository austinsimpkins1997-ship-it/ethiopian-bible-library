const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const handlers = {};
const cacheEntries = new Map();
let networkFetch = async () => { throw new Error('unexpected fetch'); };
let notificationCalls = 0;
const keyOf = value => typeof value === 'string' ? value : value.url ?? value.href;
const cache = {
  async match(key) { return cacheEntries.get(keyOf(key)); },
  async put(key, response) { cacheEntries.set(keyOf(key), response); },
  async addAll(urls) { for (const url of urls) cacheEntries.set(keyOf(url), { ok: true }); }
};
const self = {
  registration: { scope: 'https://example.test/library/' },
  clients: { async claim() {}, async matchAll() { notificationCalls += 1; return []; } },
  addEventListener(name, handler) { handlers[name] = handler; },
  skipWaiting() {}
};
const caches = {
  async open() { return cache; },
  async keys() { return []; },
  async delete() { return true; }
};

vm.runInNewContext(fs.readFileSync('sw.js', 'utf8'), { self, caches, URL, Promise, fetch: (...args) => networkFetch(...args) });

async function navigateWith(fetchImpl, path = 'deep-link/') {
  networkFetch = fetchImpl;
  let responsePromise;
  const request = { method: 'GET', mode: 'navigate', url: `https://example.test/library/${path}` };
  handlers.fetch({ request, respondWith(promise) { responsePromise = promise; } });
  return responsePromise;
}

async function fetchAssetWith(fetchImpl, path) {
  networkFetch = fetchImpl;
  let responsePromise;
  handlers.fetch({
    request: { method: 'GET', mode: 'cors', url: `https://example.test/library/${path}` },
    respondWith(promise) { responsePromise = promise; }
  });
  return responsePromise;
}

(async () => {
  let installPromise;
  handlers.install({ waitUntil(promise) { installPromise = promise; } });
  await installPromise;
  assert.equal(cacheEntries.get('https://example.test/library/offline.html').ok, true, 'a small offline explanation must install even if the full reader is too large');
  assert.equal(cacheEntries.get('https://example.test/library/app.js').ok, true, 'the application shell must be precached');
  assert.equal(cacheEntries.get('https://example.test/library/readers/source/tegsats-bl-add-ms-16186/iiif-manifest.json').ok, true, 'small source metadata must be available offline');
  assert.equal(cacheEntries.get('https://example.test/library/research/tegsats-source-review.md').ok, true, 'the linked source review must be available offline');
  assert.equal(cacheEntries.get('https://example.test/library/readers/source/alaba-kabeena/alw-copyright.html').ok, true, 'the publisher-stated text rights must be available offline at install');
  for (const path of ['examples/portable-text-layers.json', 'translation-registry.json', 'book-coverage.json']) {
    assert.equal(cacheEntries.get(`https://example.test/library/${path}`), undefined, `${path} should not inflate first-install storage`);
  }
  assert.equal(cacheEntries.get('https://example.test/library/readers/source/bilin-mark-1890/Bilin-1890-Mark.pdf'), undefined, 'the large Bilen scan must not be part of first-install storage');
  assert.equal(cacheEntries.get('https://example.test/library/readers/source/didascalia-platt1834/internet-archive-djvu.xml'), undefined, 'the large OCR XML must not be part of first-install storage');
  assert.equal(cacheEntries.get('https://example.test/library/research/didascalia-harden1920-ocr-reader.html'), undefined, 'the research viewer should be cached only after it is opened');
  assert.equal(cacheEntries.get('https://example.test/library/research/didascalia-harden1920-ocr-chapters.json'), undefined, 'the chapter-indexed OCR data should be cached only after requested');

  for (const path of ['examples/portable-text-layers.json', 'translation-registry.json', 'book-coverage.json']) {
    const exportResponse = { ok: true, body: `cached-${path}`, clone() { return this; } };
    const fetched = await fetchAssetWith(async () => exportResponse, path);
    assert.equal(fetched.body, `cached-${path}`);
    assert.equal(cacheEntries.get(`https://example.test/library/${path}`).body, `cached-${path}`, `${path} should become available offline after opening`);
  }
  for (const path of ['examples/portable-text-layers.json', 'translation-registry.json', 'book-coverage.json']) {
    const cached = await fetchAssetWith(async () => { throw new Error('offline'); }, path);
    assert.equal(cached.body, `cached-${path}`, `${path} should stay available offline after its first fetch`);
  }

  const previouslyUnlistedPath = 'research/hadiyya-source-review.md';
  const unlistedResponse = { ok: true, body: 'archived-hadiyya-review', clone() { return this; } };
  const onlineUnlisted = await fetchAssetWith(async () => unlistedResponse, previouslyUnlistedPath);
  assert.equal(onlineUnlisted.body, 'archived-hadiyya-review');
  assert.equal(
    cacheEntries.get(`https://example.test/library/${previouslyUnlistedPath}`).body,
    'archived-hadiyya-review',
    'a same-site archive file outside the former explicit allowlist should be cached on access'
  );
  const offlineUnlisted = await fetchAssetWith(async () => { throw new Error('offline'); }, previouslyUnlistedPath);
  assert.equal(offlineUnlisted.body, 'archived-hadiyya-review', 'an unlisted local archive file should reopen offline after first access');

  const readerUrl = 'https://example.test/library/readers/genesis-geez-dillmann-hacohen.json';
  const readerResponse = { ok: true, body: 'selected-reader-text', clone() { return this; } };
  const cachedIndex = { ok: true, body: 'cached-reader', clone() { return this; } };
  cacheEntries.set('https://example.test/library/index.html', cachedIndex);
  networkFetch = async () => readerResponse;
  let readerPromise;
  handlers.fetch({ request: { method: 'GET', mode: 'cors', url: readerUrl }, respondWith(promise) { readerPromise = promise; } });
  assert.equal((await readerPromise).body, 'selected-reader-text');
  assert.equal(cacheEntries.get(readerUrl).body, 'selected-reader-text', 'an opened bundled reader should be saved on demand');

  const bulkReaderUrl = 'https://example.test/library/readers/book-two.json';
  const bulkResponse = { ok: true, body: 'bulk-reader-text', clone() { return this; } };
  networkFetch = async () => bulkResponse;
  const notificationsBeforeBulk = notificationCalls;
  let bulkPromise;
  handlers.fetch({ request: {
    method: 'GET', mode: 'cors', url: bulkReaderUrl,
    headers: { get(name) { return name === 'X-Archive-Bulk-Cache' ? '1' : null; } }
  }, respondWith(promise) { bulkPromise = promise; } });
  assert.equal((await bulkPromise).body, 'bulk-reader-text');
  assert.equal(cacheEntries.get(bulkReaderUrl).body, 'bulk-reader-text', 'a bulk reader request should still be cached');
  assert.equal(notificationCalls, notificationsBeforeBulk, 'bulk caching should suppress per-reader status messages');

  let statusPromise;
  let readerStatus;
  handlers.message({
    data: { type: 'CHECK_OFFLINE_READER', readerUrl: 'readers/genesis-geez-dillmann-hacohen.json' },
    ports: [{ postMessage(message) { readerStatus = message; } }],
    waitUntil(promise) { statusPromise = promise; }
  });
  await statusPromise;
  assert.equal(readerStatus.available, true, 'offline status should verify both app page and selected reader text');

  const sourceUrl = 'https://example.test/library/readers/source/bilin-mark-1890/Bilin-1890-Mark.pdf';
  const sourceResponse = { ok: true, body: 'opened-source', clone() { return this; } };
  networkFetch = async () => sourceResponse;
  let sourcePromise;
  handlers.fetch({ request: { method: 'GET', mode: 'cors', url: sourceUrl }, respondWith(promise) { sourcePromise = promise; } });
  assert.equal((await sourcePromise).body, 'opened-source');
  assert.equal(cacheEntries.get(sourceUrl).body, 'opened-source', 'a source opened online should be stored for later offline access');
  networkFetch = async () => { throw new Error('offline'); };
  let cachedReaderPromise;
  handlers.fetch({ request: { method: 'GET', mode: 'cors', url: readerUrl }, respondWith(promise) { cachedReaderPromise = promise; } });
  assert.equal((await cachedReaderPromise).body, 'selected-reader-text', 'an opened reader should be available from cache offline');
  let cachedSourcePromise;
  handlers.fetch({ request: { method: 'GET', mode: 'cors', url: sourceUrl }, respondWith(promise) { cachedSourcePromise = promise; } });
  assert.equal((await cachedSourcePromise).body, 'opened-source', 'an opened source should be served from cache offline');

  const offline = await navigateWith(async () => { throw new Error('offline'); });
  assert.equal(offline.body, 'cached-reader', 'network failure should use the cached reader');

  const unavailable = await navigateWith(async () => ({ ok: false, status: 503 }));
  assert.equal(unavailable.body, 'cached-reader', 'HTTP server errors should use the cached reader');

  const fresh = { ok: true, body: 'fresh-reader', clone() { return this; } };
  const updated = await navigateWith(async () => fresh);
  assert.equal(updated.body, 'fresh-reader');
  assert.equal(cacheEntries.get('https://example.test/library/index.html').body, 'cached-reader', 'a deep link must not replace the app shell cache');
  assert.equal(cacheEntries.get('https://example.test/library/deep-link/').body, 'fresh-reader');

  const research = { ok: true, body: 'cached-research', clone() { return this; } };
  const researchPage = await navigateWith(async () => research, 'research/eritrea.html');
  assert.equal(researchPage.body, 'cached-research');
  assert.equal(cacheEntries.get('https://example.test/library/research/eritrea.html').body, 'cached-research');
  assert.equal(cacheEntries.get('https://example.test/library/index.html').body, 'cached-reader', 'a research page must not replace the app shell cache');

  const clementReview = { ok: true, body: 'clement-review', clone() { return this; } };
  const clementReviewPage = await navigateWith(async () => clementReview, 'research/clement-source-review.md');
  assert.equal(clementReviewPage.body, 'clement-review');
  assert.equal(cacheEntries.get('https://example.test/library/research/clement-source-review.md').body, 'clement-review');
  networkFetch = async () => { throw new Error('offline'); };
  const offlineClementReview = await navigateWith(networkFetch, 'research/clement-source-review.md');
  assert.equal(offlineClementReview.body, 'clement-review', 'an opened local source review should remain available offline');

  const didascaliaView = { ok: true, body: 'chapter-indexed-raw-ocr-view', clone() { return this; } };
  const didascaliaPage = await navigateWith(async () => didascaliaView, 'research/didascalia-harden1920-ocr-reader.html');
  assert.equal(didascaliaPage.body, 'chapter-indexed-raw-ocr-view');
  assert.equal(cacheEntries.get('https://example.test/library/research/didascalia-harden1920-ocr-reader.html').body, 'chapter-indexed-raw-ocr-view');
  const didascaliaData = { ok: true, body: 'audited-43-chapter-data', clone() { return this; } };
  const didascaliaJson = await fetchAssetWith(async () => didascaliaData, 'research/didascalia-harden1920-ocr-chapters.json');
  assert.equal(didascaliaJson.body, 'audited-43-chapter-data');
  assert.equal(cacheEntries.get('https://example.test/library/research/didascalia-harden1920-ocr-chapters.json').body, 'audited-43-chapter-data');
  const offlineDidascaliaPage = await navigateWith(async () => { throw new Error('offline'); }, 'research/didascalia-harden1920-ocr-reader.html');
  const offlineDidascaliaData = await fetchAssetWith(async () => { throw new Error('offline'); }, 'research/didascalia-harden1920-ocr-chapters.json');
  assert.equal(offlineDidascaliaPage.body, 'chapter-indexed-raw-ocr-view', 'the opened research view should remain available offline');
  assert.equal(offlineDidascaliaData.body, 'audited-43-chapter-data', 'the chapter data should remain available offline after first load');

  const clementCapture = { ok: true, body: 'pinned-clement-metadata', clone() { return this; } };
  const clementCapturePage = await navigateWith(async () => clementCapture, 'readers/source/clement-betamasaheft/capture-manifest.json');
  assert.equal(clementCapturePage.body, 'pinned-clement-metadata');
  assert.equal(cacheEntries.get('https://example.test/library/readers/source/clement-betamasaheft/capture-manifest.json').body, 'pinned-clement-metadata');
  const offlineClementCapture = await navigateWith(async () => { throw new Error('offline'); }, 'readers/source/clement-betamasaheft/capture-manifest.json');
  assert.equal(offlineClementCapture.body, 'pinned-clement-metadata', 'the pinned source metadata should reopen offline');

  const rightsNotice = { ok: true, body: 'archived-publisher-rights-notice', clone() { return this; } };
  const onlineRightsNotice = await navigateWith(async () => rightsNotice, 'readers/source/alaba-kabeena/alw-copyright.html');
  assert.equal(onlineRightsNotice.body, 'archived-publisher-rights-notice');
  assert.equal(
    cacheEntries.get('https://example.test/library/readers/source/alaba-kabeena/alw-copyright.html').body,
    'archived-publisher-rights-notice',
    'a visited local rights notice should be cached for offline access'
  );
  const offlineRightsNotice = await navigateWith(async () => { throw new Error('offline'); }, 'readers/source/alaba-kabeena/alw-copyright.html');
  assert.equal(offlineRightsNotice.body, 'archived-publisher-rights-notice', 'the archived rights notice should reopen offline');

  const freshIndex = { ok: true, body: 'fresh-index', clone() { return this; } };
  const indexPage = await navigateWith(async () => freshIndex, 'index.html');
  assert.equal(indexPage.body, 'fresh-index');
  assert.equal(cacheEntries.get('https://example.test/library/index.html').body, 'fresh-index');
  process.stdout.write('Service-worker checks passed: on-demand reader caching, offline fallback, page-specific caching, and app-shell cache integrity.\n');
})().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; });
