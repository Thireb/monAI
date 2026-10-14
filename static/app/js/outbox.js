// monAI offline quick add: spends added without a network wait in IndexedDB ("the outbox")
// and are sent to the server when the network comes back. Each one keeps the time it was
// added (spent_at), so the day chart counts it on the right day.
// app.js calls window.monaiOutbox.add(), .send() and .count(); this file only stores and sends.
(function () {
  'use strict';

  const DB_NAME = 'monai';
  const STORE = 'outbox';

  function openDb() {
    return new Promise((resolve, reject) => {
      if (!('indexedDB' in window)) {
        reject(new Error('IndexedDB is not available'));
        return;
      }
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        request.result.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  function run(mode, work) {
    return openDb().then(
      db =>
        new Promise((resolve, reject) => {
          const tx = db.transaction(STORE, mode);
          const result = work(tx.objectStore(STORE));
          tx.oncomplete = () => {
            db.close();
            resolve(result && 'result' in result ? result.result : undefined);
          };
          tx.onerror = () => {
            db.close();
            reject(tx.error);
          };
        })
    );
  }

  function all() {
    return run('readonly', store => store.getAll());
  }

  function remove(id) {
    return run('readwrite', store => store.delete(id));
  }

  // Save the fields of the quick-add form and the URL to send them to.
  // Resolve with the number of waiting spends.
  function add(url, fields) {
    const item = { url: url, fields: Object.assign({}, fields, { spent_at: String(Date.now()) }) };
    return run('readwrite', store => store.add(item)).then(() => all().then(list => list.length));
  }

  function csrfToken() {
    try {
      return JSON.parse(document.body.getAttribute('hx-headers') || '{}')['X-CSRFToken'] || '';
    } catch (e) {
      return '';
    }
  }

  let sending = null;

  // Send the waiting spends, oldest first. Resolve with {sent, failed: [messages]}.
  // A spend the server cannot place (for example "Which line?") is removed and reported.
  // A network error stops the run; the rest wait for the next try.
  function send() {
    if (sending) return sending;
    const report = { sent: 0, failed: [] };
    sending = all()
      .then(list =>
        list.reduce(
          (chain, item) =>
            chain.then(stop => {
              if (stop) return true;
              const body = new FormData();
              Object.keys(item.fields).forEach(key => body.append(key, item.fields[key]));
              return fetch(item.url, {
                method: 'POST',
                body: body,
                credentials: 'same-origin',
                headers: { 'X-CSRFToken': csrfToken(), 'HX-Request': 'true' },
              })
                .then(response =>
                  response.text().then(text => {
                    if (response.ok && text.indexOf('toast--added') !== -1) {
                      report.sent += 1;
                    } else if (
                      response.redirected ||
                      response.status === 403 ||
                      response.status >= 500
                    ) {
                      // Keep it: the session ended (login redirect) or the server failed.
                      return true;
                    } else {
                      report.failed.push(item.fields.text || item.fields.amount);
                    }
                    return remove(item.id).then(() => false);
                  })
                )
                .catch(() => true);
            }),
          Promise.resolve(false)
        )
      )
      .then(() => report)
      .finally(() => {
        sending = null;
      });
    return sending;
  }

  function count() {
    return all()
      .then(list => list.length)
      .catch(() => 0);
  }

  window.monaiOutbox = { add: add, send: send, count: count };
})();
