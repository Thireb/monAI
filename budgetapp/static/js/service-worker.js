// Service Worker for Budget Tracker PWA
// Version for cache management
const CACHE_VERSION = 'v1';
const CACHE_NAME = `budget-tracker-${CACHE_VERSION}`;

// Assets to cache on install
const STATIC_ASSETS = [
  '/minimal/',
  '/static/css/minimal-css/theme/theme.css',
  '/static/css/minimal-css/nav/nav.css',
  '/static/css/minimal-css/calculator/calculator.css',
  '/static/css/minimal-css/modal/modal.css',
  '/static/material/css/style.css',
  '/static/material/css/table-styles.css',
  '/static/material/css/goal-styles.css',
  '/static/js/minimal-js/nav/nav.js',
  '/static/js/minimal-js/calculator/calculator.js',
  '/static/js/minimal-js/modal/modal.js',
  '/static/material/js/scripts.js',
  '/static/material/js/alerts.js',
  '/static/material/favicon/site.webmanifest',
  '/static/material/favicon/android-chrome-192x192.png',
  '/static/material/favicon/android-chrome-512x512.png',
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('[Service Worker] Installing...', CACHE_VERSION);
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[Service Worker] Caching static assets');
      return cache
        .addAll(
          STATIC_ASSETS.map(url => {
            try {
              return new Request(url, { mode: 'no-cors' });
            } catch (e) {
              return url;
            }
          })
        )
        .catch(err => {
          console.log('[Service Worker] Cache addAll failed:', err);
          // Continue even if some assets fail to cache
        });
    })
  );
  // Force the waiting service worker to become the active service worker
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activating...', CACHE_VERSION);
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Take control of all pages immediately
  return self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Skip API calls - always use network for API
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Strategy: Cache first for static assets, network first for pages
  if (
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'image' ||
    request.destination === 'font' ||
    url.pathname.startsWith('/static/')
  ) {
    // Cache first for static assets
    event.respondWith(
      caches.match(request).then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then(response => {
          // Don't cache non-successful responses
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(request, responseToCache);
          });
          return response;
        });
      })
    );
  } else {
    // Network first for HTML pages
    event.respondWith(
      fetch(request)
        .then(response => {
          // Cache successful responses
          if (response && response.status === 200 && response.type === 'basic') {
            const responseToCache = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(request).then(cachedResponse => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Fallback to minimal theme home page if nothing in cache
            return caches.match('/minimal/');
          });
        })
    );
  }
});
