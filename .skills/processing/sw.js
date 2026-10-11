const CACHE_NAME = 'reverse-geocoding-cache-v2';
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
      .then(async cache => {
        console.log('SW: Caching app shell assets individually to avoid transactional failures');
        for (const url of urlsToCache) {
          try {
            const response = await fetch(url);
            if (response.ok) {
              const contentType = response.headers.get('content-type') || '';
              // Evitar cachear fallbacks HTML de rutas SPA para archivos CSS/JS
              const isHtmlFallback = (url.match(/\.(css|js)$/i) && contentType.includes('text/html'));
              if (!isHtmlFallback) {
                await cache.put(url, response);
                console.log(`SW: Cached ${url} successfully`);
              } else {
                console.warn(`SW: Skipped caching HTML fallback for asset ${url}`);
              }
            } else {
              console.warn(`SW: Skipped caching ${url} (Status: ${response.status})`);
            }
          } catch (err) {
            console.warn(`SW: Failed to cache ${url}:`, err.message);
          }
        }
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
            console.log('SW: Deleting old cache', cacheName);
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

  // Bypass service worker interception completely on localhost for development live reload
  const isLocalhost = self.location.hostname === 'localhost' || self.location.hostname === '127.0.0.1' || self.location.hostname === '[::1]';
  if (isLocalhost) return;

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
                const contentType = networkResponse.headers.get('content-type') || '';
                const isHtmlFallbackForAsset = (event.request.url.match(/\.(css|js)$/i) && contentType.includes('text/html'));
                if (!isHtmlFallbackForAsset) {
                  caches.open(CACHE_NAME).then(cache => cache.put(event.request, networkResponse));
                }
              }
            }).catch(() => {/* Ignore background updates errors when offline */});
            return cachedResponse;
          }
          
          return fetch(event.request)
            .then(networkResponse => {
              if (networkResponse && networkResponse.status === 200) {
                const contentType = networkResponse.headers.get('content-type') || '';
                const isHtmlFallbackForAsset = (event.request.url.match(/\.(css|js)$/i) && contentType.includes('text/html'));
                if (!isHtmlFallbackForAsset) {
                  const responseToCache = networkResponse.clone();
                  caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseToCache));
                }
              }
              return networkResponse;
            })
            .catch(err => {
              console.warn('[SW Fetch Fail] falling back to clean browser request:', err.message);
              return fetch(event.request);
            });
        })
        .catch(err => {
          console.error('[SW Match Fail] falling back to clean browser request:', err.message);
          return fetch(event.request);
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
