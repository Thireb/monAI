// Service Worker for the monAI PWA
// Increment CACHE_VERSION to force a full cache clear.
const CACHE_VERSION = 'v5';
const STATIC_CACHE = `monai-static-${CACHE_VERSION}`;
const PAGE_CACHE = `monai-pages-${CACHE_VERSION}`;

// Offline fallback page
const OFFLINE_URL = '/app/offline/';

// Lists the pages to keep ready offline (see OfflineUrlsView).
const OFFLINE_URLS_ENDPOINT = '/app/offline/urls/';

// A page request waits this long for the network, then falls back to the cache.
// Without it, a phone with Tailscale on but no network waits until the request times out.
const NETWORK_TIMEOUT_MS = 4000;

// Hosts the pages load fonts from. Cached so pages work offline.
// HTMX and anime.js are in static/app/vendor/, so no script comes from a CDN.
const CDN_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];

// Core assets to pre-cache on install (without version params)
const CORE_ASSETS = [
  OFFLINE_URL,
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

/**
 * Fetch with a time limit. Rejects when the network does not answer in time.
 */
function fetchWithTimeout(request, timeoutMs) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Network timeout')), timeoutMs);
    fetch(request).then(
      response => {
        clearTimeout(timer);
        resolve(response);
      },
      error => {
        clearTimeout(timer);
        reject(error);
      }
    );
  });
}

// Install event - cache core assets
self.addEventListener('install', event => {
  console.log('[Service Worker] Installing...', CACHE_VERSION);
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then(cache => cache.addAll(CORE_ASSETS))
      .catch(err => {
        // Continue even if some assets fail to cache
        console.log('[Service Worker] Cache addAll failed:', err);
      })
  );
  // Force the waiting service worker to become the active service worker
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activating...', CACHE_VERSION);
  event.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE && cacheName !== PAGE_CACHE) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
          return null;
        })
      )
    )
  );
  // Take control of all pages immediately
  return self.clients.claim();
});

// Messages from pages
self.addEventListener('message', event => {
  const data = event.data || {};
  if (data.action === 'skipWaiting') {
    self.skipWaiting();
  } else if (data.type === 'WARM_CACHE') {
    event.waitUntil(warmPageCache());
  } else if (data.type === 'CLEAR_PAGES') {
    event.waitUntil(caches.delete(PAGE_CACHE));
  }
});

// Bill alerts (Web Push). The server sends {title, body, url}; see budgetapp/services/push.py.
self.addEventListener('push', event => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { body: event.data ? event.data.text() : '' };
  }
  event.waitUntil(
    self.registration.showNotification(data.title || 'monAI', {
      body: data.body || '',
      icon: '/static/material/favicon/android-chrome-192x192.png',
      badge: '/static/material/favicon/android-chrome-192x192.png',
      tag: 'monai-bills',
      data: { url: data.url || '/app/' },
    })
  );
});

// A tap on the alert opens monAI, or focuses it when it is open.
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = new URL((event.notification.data || {}).url || '/app/', self.location.origin);
  if (target.origin !== self.location.origin) return;
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windows => {
      for (const client of windows) {
        if (new URL(client.url).pathname.startsWith('/app/') && 'focus' in client) {
          client.navigate(target.href);
          return client.focus();
        }
      }
      return self.clients.openWindow(target.href);
    })
  );
});

// Fetch event - smart caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Logging out: drop cached pages, they hold the user's budget data.
  if (request.method === 'POST' && url.pathname.startsWith('/accounts/logout')) {
    event.waitUntil(caches.delete(PAGE_CACHE));
    return;
  }

  // Only GET requests are cached
  if (request.method !== 'GET') {
    return;
  }

  // Fonts from the known hosts: cache first, refresh in the background
  if (url.origin !== location.origin) {
    if (CDN_HOSTS.includes(url.hostname)) {
      event.respondWith(cacheFirstCdn(request));
    }
    return;
  }

  // Network only: API calls, admin and account pages (login, logout)
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/admin/') ||
    url.pathname.startsWith('/accounts/')
  ) {
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
    event.respondWith(staleWhileRevalidate(request));
  } else {
    // Network first (with a time limit) for pages and page partials
    event.respondWith(networkFirst(request));
  }
});

/**
 * Cache-first strategy for CDN files. Opaque responses are cached too:
 * a <script> or <link> without crossorigin gets one.
 */
async function cacheFirstCdn(request) {
  const cache = await caches.open(STATIC_CACHE);
  const cached = await cache.match(request);
  const network = fetch(request)
    .then(response => {
      if (response && (response.ok || response.type === 'opaque')) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);
  if (cached) {
    return cached;
  }
  const response = await network;
  return response || new Response('', { status: 503, statusText: 'Offline' });
}

/**
 * Stale-While-Revalidate Strategy with Version-Aware Caching
 *
 * 1. Check if URL has version hash (?h=123456)
 * 2. If versioned, check cache using base URL as key
 * 3. If cached version matches requested version, return cached
 * 4. Otherwise, fetch from network and update cache
 * 5. If the network fails, return the cached copy even if its version is older
 */
async function staleWhileRevalidate(request) {
  const cache = await caches.open(STATIC_CACHE);
  const baseUrl = getBaseUrl(request.url);
  const requestedVersion = getVersionHash(request.url);
  const cachedResponse = await cache.match(baseUrl);

  if (cachedResponse) {
    if (!requestedVersion) {
      // Return cached immediately, update in background
      fetchAndCache(request, cache, baseUrl, null);
      return cachedResponse;
    }
    if (cachedResponse.headers.get('X-Cached-Version') === requestedVersion) {
      return cachedResponse;
    }
  }

  const fresh = await fetchAndCache(request, cache, baseUrl, requestedVersion);
  return fresh || cachedResponse || new Response('', { status: 503, statusText: 'Offline' });
}

/**
 * Fetch a resource and cache it with version metadata.
 * Resolves to null when the network fails.
 */
async function fetchAndCache(request, cache, baseUrl, version) {
  let response;
  try {
    response = await fetch(request);
  } catch (error) {
    console.log('[SW] Fetch failed:', error);
    return null;
  }

  // Don't cache non-successful responses
  if (!response || response.status !== 200 || response.type !== 'basic') {
    return response;
  }

  // Store a copy with the version in a header, for future matching
  const responseToCache = response.clone();
  const headers = new Headers(responseToCache.headers);
  if (version) {
    headers.set('X-Cached-Version', version);
  }
  const blob = await responseToCache.blob();
  await cache.put(
    baseUrl,
    new Response(blob, {
      status: responseToCache.status,
      statusText: responseToCache.statusText,
      headers: headers,
    })
  );
  return response;
}

/**
 * Store a page response. A redirected response is not stored: the browser refuses
 * to use one for a page request, so it would break the page offline.
 */
async function putPage(request, response) {
  if (response && response.status === 200 && response.type === 'basic' && !response.redirected) {
    const cache = await caches.open(PAGE_CACHE);
    await cache.put(request, response);
  }
}

/**
 * Network First Strategy for pages, with a time limit
 */
async function networkFirst(request) {
  const network = fetch(request);
  try {
    const response = await Promise.race([
      network,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Network timeout')), NETWORK_TIMEOUT_MS)
      ),
    ]);
    putPage(request, response.clone());
    return response;
  } catch (error) {
    // Keep the cache fresh if the slow request finishes later
    network.then(response => putPage(request, response.clone())).catch(() => {});

    const cachedResponse = await caches.match(request, { ignoreVary: true });
    if (cachedResponse) {
      return cachedResponse;
    }
    if (request.mode === 'navigate') {
      const offline = await caches.match(OFFLINE_URL, { ignoreVary: true });
      if (offline) {
        return offline;
      }
    }
    return new Response('', { status: 503, statusText: 'Offline' });
  }
}

/**
 * Fetch the pages listed by the server and store them, so they open offline
 * even if the user never visited them.
 */
async function warmPageCache() {
  let urls;
  try {
    const response = await fetchWithTimeout(
      new Request(OFFLINE_URLS_ENDPOINT, { credentials: 'same-origin' }),
      NETWORK_TIMEOUT_MS
    );
    if (!response.ok || response.redirected) {
      return;
    }
    urls = (await response.json()).urls || [];
  } catch (error) {
    console.log('[SW] Could not load the offline page list:', error);
    return;
  }

  const cache = await caches.open(PAGE_CACHE);
  for (const url of urls) {
    try {
      const response = await fetch(new Request(url, { credentials: 'same-origin' }));
      if (response.ok && !response.redirected) {
        await cache.put(url, response);
      }
    } catch (error) {
      // Skip this page; the next warm-up tries again
    }
  }
  console.log('[SW] Cached', urls.length, 'pages for offline use');
}
