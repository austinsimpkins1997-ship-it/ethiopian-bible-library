/* Offline app shell and on-demand archive assets. */
const CACHE_PREFIX = 'ethiopian-bible-library-';
const CACHE_NAME = `${CACHE_PREFIX}shell-v44`;
const SITE_BASE = new URL(self.registration.scope);
const PRECACHE_PATHS = [
  'index.html',
  'offline.html',
  'styles.css',
  'app.js',
  'reader-package.js',
  'reader-alignment.js',
  'offline-reader-cache.js',
  'manifest.webmanifest',
  'archive-manifest.json',
  'schemas/source-record.schema.json',
  'schemas/reader-package.schema.json',
  'schemas/catalogue-research-view.schema.json',
  'schemas/text-layer.schema.json',
  'schemas/eotc-canon-registry.schema.json',
  'schemas/textual-lens.schema.json',
  'schemas/book-coverage.schema.json',
  'research/source-encoding-audit.md',
  'research/source-encoding-audit.html',
  'research/source-encoding-audit.json',
  'readers/source/amos-tau-2009/SOURCE-CAPTURE.json',
  'readers/source/amos-tau-2009/amos-information.html',
  'readers/source/amos-tau-2009/amos-information.utf8.html',
  'readers/source/obadiah-tau-2010/SOURCE-CAPTURE.json',
  'readers/source/obadiah-tau-2010/obadiah-information.html',
  'readers/source/obadiah-tau-2010/obadiah-information.utf8.html',
  'readers/source/sirach-tau-2026/SOURCE-CAPTURE.json',
  'readers/source/sirach-tau-2026/apocryphi-information.html',
  'readers/source/sirach-tau-2026/apocryphi-information.utf8.html',
  'readers/source/sirach-tau-2026/sirach-information.html',
  'readers/source/sirach-tau-2026/sirach-information.utf8.html',
  'readers/source/tau-platt-nt-menu/SOURCE-CAPTURE.json',
  'readers/source/tau-platt-nt-menu/nt-information.html',
  'readers/source/tau-platt-nt-menu/nt-information.utf8.html',

  'research/genesis-1-divine-person-lens.html',
  'research/genesis-1-divine-person-lens.json',
  'research/gamo-maale-provenance.html',
  'research/maale-edition-rights-audit.json',
  'research/tegsats-source-review.md',
  'readers/source/alaba-kabeena/alw-copyright.html',
  'readers/source/tegsats-bl-add-ms-16186/capture-manifest.json',
  'readers/source/tegsats-bl-add-ms-16186/iiif-manifest.json',
  'examples/review-coverage.json',
  'research/rights-coverage.html',
  'examples/rights-coverage.json',
  'assets/icon-192.png',
  'assets/icon-512.png',
  'assets/apple-touch-icon.png'
];
const PRECACHE_FILES = PRECACHE_PATHS.map(path => new URL(path, SITE_BASE).href);
const INDEX_URL = new URL('index.html', SITE_BASE).href;
const OFFLINE_URL = new URL('offline.html', SITE_BASE).href;

async function notifyReaderCached() {
  const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
  for (const client of windows) client.postMessage({ type: 'OFFLINE_READER_CACHE_UPDATED' });
}

async function matchAcrossCaches(request) {
  const names = await caches.keys();
  const ordered = [CACHE_NAME, ...names.filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)];
  for (const name of ordered) {
    const cache = await caches.open(name);
    const response = await cache.match(request);
    if (response) return response;
  }
  return undefined;
}

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    const smallShellFiles = PRECACHE_FILES.filter(url => url !== INDEX_URL);
    await cache.addAll(smallShellFiles);
    // The app shell is cacheable, but limited storage must not prevent install.
    try {
      const response = await fetch(INDEX_URL);
      if (response.ok) {
        await cache.put(INDEX_URL, response.clone());
        await notifyReaderCached();
      }
    } catch {
      // The current visit still works online; a later navigation can cache it.
    }
  })());
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    const hasCurrentReader = Boolean(await cache.match(INDEX_URL));
    if (hasCurrentReader) {
      const names = await caches.keys();
      await Promise.all(names.filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME).map(name => caches.delete(name)));
    }
    await self.clients.claim();
  })());
});

self.addEventListener('message', event => {
  if (event.data?.type !== 'CHECK_OFFLINE_READER') return;
  const reply = event.ports?.[0];
  event.waitUntil((async () => {
    try {
      const cache = await caches.open(CACHE_NAME);
      const savedPage = await cache.match(INDEX_URL);
      const readerUrl = event.data?.readerUrl;
      const savedText = readerUrl ? await matchAcrossCaches(new URL(readerUrl, SITE_BASE).href) : true;
      reply?.postMessage({
        type: 'OFFLINE_READER_STATUS',
        available: Boolean(savedPage && savedText),
        page_available: Boolean(savedPage),
        reader_available: Boolean(savedText),
      });
    } catch {
      reply?.postMessage({ type: 'OFFLINE_READER_STATUS', available: null });
    }
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET' || new URL(request.url).origin !== SITE_BASE.origin) return;
  const url = new URL(request.url);
  if (!url.href.startsWith(SITE_BASE.href)) return;

  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(CACHE_NAME);
          try {
            await cache.put(request, response.clone());
            if (url.href === INDEX_URL || url.href === SITE_BASE.href) {
              await cache.put(INDEX_URL, response.clone());
              await notifyReaderCached();
            }
          } catch {
            // Storage limits must not turn an available network response into an error.
          }
          return response;
        }
        return (await matchAcrossCaches(request))
          || (await matchAcrossCaches(INDEX_URL))
          || (await matchAcrossCaches(OFFLINE_URL))
          || response;
      } catch {
        return (await matchAcrossCaches(request))
          || (await matchAcrossCaches(INDEX_URL))
          || (await matchAcrossCaches(OFFLINE_URL));
      }
    })());
    return;
  }

  const relativePath = url.pathname.startsWith(SITE_BASE.pathname)
    ? url.pathname.slice(SITE_BASE.pathname.length)
    : '';
  const isBundledReaderPackage = /^readers\/[a-z0-9-]+\.json$/.test(relativePath);
  const isBulkReaderRequest = request.headers?.get?.('X-Archive-Bulk-Cache') === '1';
  // Every successful same-origin file under this static site can be fetched from
  // the local archive. Cache it on first access so newly added source records,
  // rights notices, and research files do not need a separate allowlist entry.
  if (relativePath) {
    event.respondWith((async () => {
      try {
        const response = await fetch(request);
        if (response.ok) {
          try {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(request, response.clone());
            if (isBundledReaderPackage && !isBulkReaderRequest) await notifyReaderCached();
          } catch {
            // Keep optional source pages usable online when offline storage is full.
          }
        }
        return response;
      } catch (error) {
        const cached = await matchAcrossCaches(request);
        if (cached) return cached;
        throw error;
      }
    })());
  }
});
