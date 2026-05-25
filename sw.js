const CACHE_NAME = 'reverse-geocoding-cache-v1';
const urlsToCache = [
  './',
  './index.html',
  './src/styles.css',
  './src/app.js',
  './locales/es.json',
  './locales/he.json',
  'https://unpkg.com/exifr/dist/full.umd.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('SW: Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  // Only intercept GET requests
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  const isCDN = url.hostname.includes('unpkg.com') || url.hostname.includes('googleapis.com') || url.hostname.includes('gstatic.com');
  const isStaticAsset = urlsToCache.some(path => url.pathname.endsWith(path.replace('./', ''))) || 
                        /\.(html|css|js|json|png|jpg|jpeg|gif|svg|woff2?|ttf|otf|ico)$/i.test(url.pathname);

  // Cache-First (stale-while-revalidate) strategy for static assets and CDNs
  if (isCDN || isStaticAsset) {
    event.respondWith(
      caches.match(event.request)
        .then(cachedResponse => {
          if (cachedResponse) {
            // Serve from cache instantly, and update cache in background
            fetch(event.request).then(networkResponse => {
              if (networkResponse && networkResponse.status === 200) {
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, networkResponse));
              }
            }).catch(() => {/* Ignore background updates errors when offline */});
            return cachedResponse;
          }
          
          return fetch(event.request).then(networkResponse => {
            if (networkResponse && networkResponse.status === 200) {
              const responseToCache = networkResponse.clone();
              caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseToCache));
            }
            return networkResponse;
          });
        })
    );
  } else {
    // Network-Only / Network-First with fallback to Cache for other GET requests (like API data lookups)
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match(event.request))
    );
  }
});
