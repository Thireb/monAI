// monAI sign-in pages: the "Show" / "Hide" password button and a short entrance.
(function () {
  'use strict';

  document.querySelectorAll('.password-toggle').forEach(button => {
    button.textContent = 'Show';
    button.addEventListener('click', () => {
      const input = button.closest('.password-wrapper').querySelector('input');
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      button.textContent = show ? 'Hide' : 'Show';
      button.setAttribute('aria-pressed', show ? 'true' : 'false');
    });
  });

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducedMotion || typeof window.anime !== 'function') return;
  window.anime({
    targets: '.auth-card',
    opacity: [0, 1],
    translateY: [16, 0],
    duration: 300,
    easing: 'easeOutCubic',
  });
})();
