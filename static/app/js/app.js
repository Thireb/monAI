// monAI new UI: theme toggle, quick-add sheet, toasts and the "Added!" celebration.
// Page data comes from the server as HTML (HTMX); this file only handles UI state.
(function () {
  'use strict';

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- Theme ----------

  function currentTheme() {
    const set = document.documentElement.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function toggleTheme() {
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try {
      localStorage.setItem('monai-theme', next);
    } catch (e) {
      // Storage can be blocked; the choice lasts for this page only.
    }
  }

  // ---------- Quick-add sheet ----------

  function sheet() {
    return document.getElementById('quick-add');
  }

  function openSheet() {
    const dialog = sheet();
    if (!dialog || dialog.open) return;
    dialog.showModal();
    const amount = dialog.querySelector('[name="amount"]');
    if (amount) amount.focus();
  }

  function closeSheet() {
    const dialog = sheet();
    if (dialog && dialog.open) dialog.close();
  }

  function resetSheet() {
    const dialog = sheet();
    if (!dialog) return;
    const form = dialog.querySelector('form');
    if (form) form.reset();
    const result = dialog.querySelector('#quick-add-result');
    if (result) result.innerHTML = '';
  }

  function isTyping(target) {
    if (!target) return false;
    const tag = target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable;
  }

  // ---------- Celebration ----------

  function celebrate() {
    if (reducedMotion || typeof window.anime !== 'function') return;
    const colors = ['#2e8b57', '#f2b33d', '#d9534f', '#6b5bb5', '#4cc285'];
    const pieces = [];
    const originX = window.innerWidth / 2;
    const originY = window.innerHeight - 140;
    for (let i = 0; i < 28; i += 1) {
      const piece = document.createElement('span');
      piece.className = 'confetti';
      piece.setAttribute('aria-hidden', 'true');
      piece.style.left = originX + 'px';
      piece.style.top = originY + 'px';
      piece.style.background = colors[i % colors.length];
      document.body.appendChild(piece);
      pieces.push(piece);
    }
    window.anime({
      targets: pieces,
      translateX: () => window.anime.random(-180, 180),
      translateY: () => window.anime.random(-320, -120),
      rotate: () => window.anime.random(-360, 360),
      opacity: [1, 0],
      duration: () => window.anime.random(700, 1100),
      easing: 'easeOutCubic',
      complete: () => pieces.forEach(p => p.remove()),
    });
  }

  // ---------- Toasts ----------

  // Remove a toast after its time (the Undo window), unless the pointer is on it.
  function scheduleToast(toast) {
    const ms = Number(toast.getAttribute('data-autoclose')) || 0;
    if (!ms || toast.dataset.scheduled) return;
    toast.dataset.scheduled = '1';
    setTimeout(() => {
      if (toast.isConnected) toast.remove();
    }, ms);
  }

  function scheduleToasts(root) {
    (root || document).querySelectorAll('.toast[data-autoclose]').forEach(scheduleToast);
  }

  // ---------- Wiring ----------

  document.addEventListener('click', event => {
    const target = event.target.closest(
      '[data-theme-toggle], [data-open-quick-add], [data-close-quick-add], [data-close-toast]'
    );
    if (!target) return;
    if (target.hasAttribute('data-theme-toggle')) {
      toggleTheme();
    } else if (target.hasAttribute('data-open-quick-add')) {
      event.preventDefault();
      openSheet();
    } else if (target.hasAttribute('data-close-quick-add')) {
      closeSheet();
    } else if (target.hasAttribute('data-close-toast')) {
      const toast = target.closest('.toast');
      if (toast) toast.remove();
    }
  });

  // "/" or "+" opens quick add, unless the user is typing in a field.
  document.addEventListener('keydown', event => {
    if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
    if ((event.key === '/' || event.key === '+') && !isTyping(event.target)) {
      if (!sheet()) return;
      event.preventDefault();
      openSheet();
    }
  });

  document.addEventListener(
    'close',
    event => {
      if (event.target === sheet()) resetSheet();
    },
    true
  );

  // Sent by the server in the HX-Trigger header after a spend is saved.
  document.body.addEventListener('spendAdded', () => {
    closeSheet();
    celebrate();
  });

  // Toasts arrive out of band, so check the whole page after each swap.
  document.body.addEventListener('htmx:afterSettle', () => scheduleToasts(document));
  scheduleToasts(document);
})();
