/* Offline app shell only. Scripture and catalogue data remain embedded in index.html. */
const CACHE_PREFIX = 'ethiopian-bible-library-';
const CACHE_NAME = `${CACHE_PREFIX}shell-v1`;
const SITE_BASE = new URL(self.registration.scope);
const APP_FILES = [
  'index.html',
  'styles.css',
  'app.js',
  'manifest.webmanifest',
  'assets/icon-192.png',
  'assets/icon-512.png',
  'assets/apple-touch-icon.png'
].map(path => new URL(path, SITE_BASE).href);

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME).map(name => caches.delete(name)));
    await self.clients.claim();
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
          await Promise.all([
            cache.put(request, response.clone()),
            cache.put(new URL('index.html', SITE_BASE), response.clone())
          ]);
        }
        return response;
      } catch {
        const cache = await caches.open(CACHE_NAME);
        return (await cache.match(request)) || (await cache.match(new URL('index.html', SITE_BASE).href));
      }
    })());
    return;
  }

  if (APP_FILES.includes(url.href)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        const response = await fetch(request);
        if (response.ok) await cache.put(request, response.clone());
        return response;
      } catch (error) {
        const cached = await cache.match(request);
        if (cached) return cached;
        throw error;
      }
    })());
  }
});
