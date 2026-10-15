// monAI bill alerts (Web Push) on this device. The card on the More page has
// [data-push] with data-key-url, data-subscribe-url and data-unsubscribe-url.
// The server sends the alerts; static/js/service-worker.js shows them.
(function () {
  'use strict';

  const card = document.querySelector('[data-push]');
  if (!card) return;
  const state = card.querySelector('[data-push-state]');
  const onButton = card.querySelector('[data-push-on]');
  const offButton = card.querySelector('[data-push-off]');
  const testButton = card.querySelector('[data-push-test]');

  function csrfToken() {
    try {
      return JSON.parse(document.body.getAttribute('hx-headers') || '{}')['X-CSRFToken'] || '';
    } catch (e) {
      return '';
    }
  }

  function show(text, isOn) {
    state.textContent = text;
    onButton.hidden = isOn;
    offButton.hidden = !isOn;
    testButton.hidden = !isOn;
  }

  // The server key is URL-safe base64; pushManager wants the bytes.
  function keyBytes(base64) {
    const padded = (base64 + '='.repeat((4 - (base64.length % 4)) % 4))
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    const raw = atob(padded);
    return Uint8Array.from(raw, c => c.charCodeAt(0));
  }

  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(body),
    }).then(response =>
      response.json().then(data => {
        if (!response.ok) throw new Error(data.error || 'The server said no.');
        return data;
      })
    );
  }

  function turnOn() {
    onButton.disabled = true;
    Notification.requestPermission()
      .then(permission => {
        if (permission !== 'granted') {
          throw new Error('Notifications are blocked. Allow them in the browser settings.');
        }
        return fetch(card.dataset.keyUrl, { credentials: 'same-origin' }).then(r => r.json());
      })
      .then(data =>
        navigator.serviceWorker.ready.then(registration =>
          registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: keyBytes(data.public_key),
          })
        )
      )
      .then(subscription => post(card.dataset.subscribeUrl, subscription.toJSON()))
      .then(() => show('On. You get an alert on the days before a bill is due.', true))
      .catch(error => show(error.message, false))
      .finally(() => {
        onButton.disabled = false;
      });
  }

  function turnOff() {
    navigator.serviceWorker.ready
      .then(registration => registration.pushManager.getSubscription())
      .then(subscription => {
        if (!subscription) return null;
        const endpoint = subscription.endpoint;
        return subscription
          .unsubscribe()
          .then(() => post(card.dataset.unsubscribeUrl, { endpoint: endpoint }));
      })
      .then(() => show('Off on this device.', false))
      .catch(error => show(error.message, true));
  }

  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    show(
      'This browser cannot show bill alerts. On iPhone, add monAI to the home screen first.',
      false
    );
    onButton.hidden = true;
    return;
  }

  // The worker is not ready over plain HTTP, or when the browser blocks it.
  const timeout = new Promise((resolve, reject) => {
    setTimeout(() => reject(new Error('timeout')), 5000);
  });

  Promise.race([navigator.serviceWorker.ready, timeout])
    .then(registration => registration.pushManager.getSubscription())
    .then(subscription => {
      if (subscription) {
        show('On. You get an alert on the days before a bill is due.', true);
      } else {
        show('Off on this device.', false);
      }
    })
    .catch(() => {
      show('Bill alerts need monAI over HTTPS, for example the Tailscale address.', false);
      onButton.hidden = true;
    });

  onButton.addEventListener('click', turnOn);
  offButton.addEventListener('click', turnOff);
})();
