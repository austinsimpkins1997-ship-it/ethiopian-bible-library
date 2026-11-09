const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const handlers = {};
const cacheEntries = new Map();
let networkFetch = async () => { throw new Error('unexpected fetch'); };
const keyOf = value => typeof value === 'string' ? value : value.url ?? value.href;
const cache = {
  async match(key) { return cacheEntries.get(keyOf(key)); },
  async put(key, response) { cacheEntries.set(keyOf(key), response); },
  async addAll(urls) { for (const url of urls) cacheEntries.set(keyOf(url), { ok: true }); }
};
const self = {
  registration: { scope: 'https://example.test/library/' },
  clients: { async claim() {} },
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

(async () => {
  const cachedIndex = { ok: true, body: 'cached-reader', clone() { return this; } };
  cacheEntries.set('https://example.test/library/index.html', cachedIndex);

  const offline = await navigateWith(async () => { throw new Error('offline'); });
  assert.equal(offline.body, 'cached-reader', 'network failure should use the cached reader');

  const unavailable = await navigateWith(async () => ({ ok: false, status: 503 }));
  assert.equal(unavailable.body, 'cached-reader', 'HTTP server errors should use the cached reader');

  const fresh = { ok: true, body: 'fresh-reader', clone() { return this; } };
  const updated = await navigateWith(async () => fresh);
  assert.equal(updated.body, 'fresh-reader');
  assert.equal(cacheEntries.get('https://example.test/library/index.html').body, 'fresh-reader');
  process.stdout.write('Service-worker navigation fallback checks passed for offline, HTTP error, and fresh responses.\n');
})().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; });
