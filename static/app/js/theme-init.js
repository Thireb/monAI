// Apply the saved light/dark choice before the page paints (no flash of the wrong theme).
(function () {
  'use strict';
  try {
    const theme = localStorage.getItem('monai-theme');
    if (theme === 'light' || theme === 'dark') {
      document.documentElement.setAttribute('data-theme', theme);
    }
  } catch (e) {
    // Storage can be blocked; the system setting applies then.
  }
})();
