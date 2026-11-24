// Keeps the app shell on the phone so the field app opens without network. API calls are never cached here;
// the app keeps its own offline copies of the data it needs (src/offline).
const CACHE_NAME = 'up4ds-shell-v1'

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()))

function saveCopy(key, response) {
  if (response.ok) {
    const copy = response.clone()
    caches.open(CACHE_NAME).then((cache) => cache.put(key, copy))
  }
  return response
}

self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)
  if (
    request.method !== 'GET' ||
    url.origin !== self.location.origin ||
    url.pathname.startsWith('/v1/')
  )
    return

  if (request.mode === 'navigate') {
    // Pages: network first so updates arrive; the saved shell when offline.
    event.respondWith(
      fetch(request)
        .then((response) => saveCopy('/', response))
        .catch(() => caches.match('/')),
    )
    return
  }
  // Built assets have hashed names, so a saved copy is always the right one.
  event.respondWith(
    caches
      .match(request)
      .then((saved) => saved ?? fetch(request).then((r) => saveCopy(request, r))),
  )
})
