// PWA Service Worker Registration
// Registers the service worker and handles updates

(function () {
  'use strict';

  // Ask the service worker to cache recent pages for offline use,
  // at most once every 15 minutes.
  const WARM_INTERVAL_MS = 15 * 60 * 1000;
  const WARM_KEY = 'monai-offline-warmed-at';

  function warmOfflineCache() {
    if (!navigator.onLine) return;
    let last = 0;
    try {
      last = Number(localStorage.getItem(WARM_KEY)) || 0;
    } catch (e) {
      // Storage can be blocked; warm every time then.
    }
    if (Date.now() - last < WARM_INTERVAL_MS) return;
    // Only a worker that controls the page gets the message reliably. On the
    // first visit there is none yet; the controllerchange reload comes next.
    const controller = navigator.serviceWorker.controller;
    if (!controller) return;
    controller.postMessage({ type: 'WARM_CACHE' });
    try {
      localStorage.setItem(WARM_KEY, String(Date.now()));
    } catch (e) {
      // Ignore: see above.
    }
  }

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      const swUrl = '/service-worker.js';

      navigator.serviceWorker
        .register(swUrl)
        .then(registration => {
          console.log('[PWA] Service Worker registered successfully:', registration.scope);
          warmOfflineCache();

          // Check for updates periodically
          setInterval(() => {
            registration.update();
          }, 60000); // Check every minute

          // Handle updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;

            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // The new worker activates at once (skipWaiting); the
                // controllerchange handler below reloads the page.
                console.log('[PWA] New service worker available');
              }
            });
          });
        })
        .catch(error => {
          console.error('[PWA] Service Worker registration failed:', error);
        });

      // Handle service worker messages
      navigator.serviceWorker.addEventListener('message', event => {
        if (event.data && event.data.type === 'SKIP_WAITING') {
          window.location.reload();
        }
      });

      // Handle service worker controller change
      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    });
  } else {
    console.log('[PWA] Service Workers are not supported in this browser');
  }

  // Handle install prompt
  let deferredPrompt;
  const installButton = document.getElementById('install-pwa-button');

  window.addEventListener('beforeinstallprompt', e => {
    // Only prevent default if we have a custom install button
    // Otherwise, let the browser show its own install banner
    if (installButton) {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault();
      // Stash the event so it can be triggered later
      deferredPrompt = e;
      // Show install button
      installButton.style.display = 'block';
      installButton.addEventListener('click', () => {
        // Show the install prompt
        if (deferredPrompt) {
          deferredPrompt.prompt();
          // Wait for the user to respond to the prompt
          deferredPrompt.userChoice.then(choiceResult => {
            if (choiceResult.outcome === 'accepted') {
              console.log('[PWA] User accepted the install prompt');
            } else {
              console.log('[PWA] User dismissed the install prompt');
            }
            deferredPrompt = null;
            if (installButton) {
              installButton.style.display = 'none';
            }
          });
        }
      });
    } else {
      // No custom button, let browser handle the install prompt
      // Don't prevent default - browser will show its own banner
      console.log('[PWA] Install prompt available - browser will show install banner');
    }
  });

  // Track app installation
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App was installed');
    deferredPrompt = null;
    if (installButton) {
      installButton.style.display = 'none';
    }
  });
})();
