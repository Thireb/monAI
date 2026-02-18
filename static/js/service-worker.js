// Service Worker for Budget Tracker PWA
// Version for cache management - increment to force full cache clear
const CACHE_VERSION = 'v3';
const CACHE_NAME = `budget-tracker-${CACHE_VERSION}`;

// Offline fallback page
const OFFLINE_URL = '/minimal/offline/';

// Core assets to pre-cache on install (without version params)
// These are cached as base URLs - versioned requests will match them
const CORE_ASSETS = [
  '/minimal/',
  '/minimal/offline/',
  '/static/material/favicon/site.webmanifest',
  '/static/material/favicon/android-chrome-192x192.png',
  '/static/material/favicon/android-chrome-512x512.png',
  '/static/material/favicon/monai-icon.svg',
];

/**
 * Get the base URL without query parameters for cache key matching.
 * This allows versioned URLs (?h=123456) to match cached entries.
 */
function getBaseUrl(url) {
  const urlObj = new URL(url);
  urlObj.search = '';
  return urlObj.href;
}

/**
 * Get the version hash from a URL's query params.
 * Returns null if no version param exists.
 */
function getVersionHash(url) {
  const urlObj = new URL(url);
  return urlObj.searchParams.get('h');
}

// Install event - cache core assets
self.addEventListener('install', event => {
  console.log('[Service Worker] Installing...', CACHE_VERSION);
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[Service Worker] Caching core assets');
      return cache
        .addAll(
          CORE_ASSETS.map(url => {
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

// Fetch event - smart caching strategies
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

  // Check if this is a static asset request
  const isStaticAsset =
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'image' ||
    request.destination === 'font' ||
    url.pathname.startsWith('/static/');

  if (isStaticAsset) {
    // Stale-While-Revalidate for static assets with version-aware caching
    event.respondWith(staleWhileRevalidate(request, url));
  } else {
    // Network first for HTML pages
    event.respondWith(networkFirst(request));
  }
});

/**
 * Stale-While-Revalidate Strategy with Version-Aware Caching
 *
 * 1. Check if URL has version hash (?h=123456)
 * 2. If versioned, check cache using base URL as key
 * 3. If cached version matches requested version, return cached
 * 4. Otherwise, fetch from network and update cache
 * 5. For non-versioned requests, use standard stale-while-revalidate
 */
async function staleWhileRevalidate(request, url) {
  const cache = await caches.open(CACHE_NAME);
  const baseUrl = getBaseUrl(request.url);
  const requestedVersion = getVersionHash(request.url);

  // Try to find a cached response using the base URL
  const cachedResponse = await cache.match(baseUrl);

  if (cachedResponse) {
    // Check if we have a versioned request
    if (requestedVersion) {
      // Get the cached version from headers (we store it when caching)
      const cachedVersion = cachedResponse.headers.get('X-Cached-Version');

      if (cachedVersion === requestedVersion) {
        // Versions match - serve from cache, no revalidation needed
        console.log('[SW] Cache hit (version match):', baseUrl);
        return cachedResponse;
      } else {
        // Version mismatch - fetch new version
        console.log('[SW] Version mismatch, fetching new:', baseUrl);
        return fetchAndCache(request, cache, baseUrl, requestedVersion);
      }
    } else {
      // Non-versioned request - use stale-while-revalidate
      // Return cached immediately, update in background
      console.log('[SW] Stale-while-revalidate:', baseUrl);
      fetchAndCache(request, cache, baseUrl, null);
      return cachedResponse;
    }
  }

  // No cache hit - fetch from network
  console.log('[SW] Cache miss, fetching:', baseUrl);
  return fetchAndCache(request, cache, baseUrl, requestedVersion);
}

/**
 * Fetch a resource and cache it with version metadata
 */
async function fetchAndCache(request, cache, baseUrl, version) {
  try {
    const response = await fetch(request);

    // Don't cache non-successful responses
    if (!response || response.status !== 200 || response.type !== 'basic') {
      return response;
    }

    // Clone response to cache
    const responseToCache = response.clone();

    // Create a new response with version header for future matching
    const headers = new Headers(responseToCache.headers);
    if (version) {
      headers.set('X-Cached-Version', version);
    }

    const blob = await responseToCache.blob();
    const cachedResponse = new Response(blob, {
      status: responseToCache.status,
      statusText: responseToCache.statusText,
      headers: headers,
    });

    // Cache using base URL as key (without query params)
    cache.put(baseUrl, cachedResponse);

    return response;
  } catch (error) {
    console.log('[SW] Fetch failed:', error);
    // Return a basic error response
    return new Response('Network error', { status: 503 });
  }
}

/**
 * Network First Strategy for HTML pages
 */
async function networkFirst(request) {
  try {
    const response = await fetch(request);

    // Cache successful responses
    if (response && response.status === 200 && response.type === 'basic') {
      const cache = await caches.open(CACHE_NAME);
      const responseToCache = response.clone();
      cache.put(request, responseToCache);
    }

    return response;
  } catch (error) {
    // Fallback to cache if network fails
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Fallback to offline page if nothing in cache
    if (request.destination === 'document' || request.mode === 'navigate') {
      return caches.match(OFFLINE_URL);
    }

    // For other requests, return minimal home if available
    return caches.match('/minimal/');
  }
}
