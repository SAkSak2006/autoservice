const CACHE_NAME = 'autoservice-v1';
const OFFLINE_URL = '/portal/offline/';

const PRECACHE_URLS = [
  OFFLINE_URL,
  '/static/css/custom.css',
  '/static/js/main.js',
  '/static/img/icon-192.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
];

// ─── Install: precache static assets ─────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// ─── Activate: clean old caches ──────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// ─── Fetch: Network-first for pages, Cache-first for static ─
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Dynamic content (portal pages, API): network-first
  if (url.pathname.startsWith('/portal/') || url.pathname.startsWith('/orders/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful page responses
          if (response.ok && url.pathname.startsWith('/portal/')) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || caches.match(OFFLINE_URL))
        )
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        // Cache static responses
        if (response.ok && (url.pathname.startsWith('/static/') || url.hostname !== location.hostname)) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      });
    })
  );
});

// ─── Push notifications ──────────────────────────────────────
self.addEventListener('push', (event) => {
  let data = { title: 'АвтоСервис Про', body: 'Новое уведомление', url: '/portal/' };
  try {
    if (event.data) data = { ...data, ...event.data.json() };
  } catch (e) {
    // Use defaults
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/static/img/icon-192.png',
      badge: '/static/img/badge-72.png',
      data: { url: data.url },
      vibrate: [200, 100, 200],
    })
  );
});

// ─── Notification click → open URL ───────────────────────────
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/portal/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((windowClients) => {
      // Focus existing tab if open
      for (const client of windowClients) {
        if (client.url.includes('/portal/') && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      return self.clients.openWindow(url);
    })
  );
});
