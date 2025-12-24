// Service Worker for Budget Tracker PWA
// Version for cache management - increment to force update
const CACHE_VERSION = 'v2';
const CACHE_NAME = `budget-tracker-${CACHE_VERSION}`;

// Offline fallback page
const OFFLINE_URL = '/minimal/offline/';

// Assets to cache on install
const STATIC_ASSETS = [
  '/minimal/',
  '/minimal/offline/',
  '/static/css/minimal-css/theme/theme.css',
  '/static/css/minimal-css/nav/nav.css',
  '/static/css/minimal-css/calculator/calculator.css',
  '/static/css/minimal-css/modal/modal.css',
  '/static/css/minimal-css/debt/debt_common.css',
  '/static/css/minimal-css/debt/debt_dashboard.css',
  '/static/css/minimal-css/debt/debt_detail.css',
  '/static/js/minimal-js/nav/nav.js',
  '/static/js/minimal-js/calculator/calculator.js',
  '/static/js/minimal-js/modal/modal.js',
  '/static/js/minimal-js/debt/debt_list.js',
  '/static/js/minimal-js/debt/debt_detail.js',
  '/static/material/favicon/site.webmanifest',
  '/static/material/favicon/android-chrome-192x192.png',
  '/static/material/favicon/android-chrome-512x512.png',
  '/static/material/favicon/monai-icon.svg',
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
            // Fallback to offline page if nothing in cache
            if (request.destination === 'document' || request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
            // For other requests, return minimal home if available
            return caches.match('/minimal/');
          });
        })
    );
  }
});
