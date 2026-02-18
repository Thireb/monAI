document.addEventListener('DOMContentLoaded', function () {
  // Create tooltip element
  let tooltip = document.createElement('div');
  tooltip.className = 'minimal-tooltip';
  document.body.appendChild(tooltip);

  function showTooltip(e, text) {
    tooltip.textContent = text;
    tooltip.classList.add('visible');
    positionTooltip(e);
  }
  function hideTooltip() {
    tooltip.classList.remove('visible');
  }
  function positionTooltip(e) {
    let x = e.clientX || (e.touches && e.touches[0].clientX);
    let y = e.clientY || (e.touches && e.touches[0].clientY);
    if (!x || !y) return;
    const tooltipRect = tooltip.getBoundingClientRect();
    let left = x - tooltipRect.width / 2;
    let top = y - tooltipRect.height - 16;
    if (left < 8) left = 8;
    if (left + tooltipRect.width > window.innerWidth - 8)
      left = window.innerWidth - tooltipRect.width - 8;
    if (top < 8) top = y + 24;
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
  }

  // Function to initialize tooltips on elements
  function initTooltips(selector = '.month-abbr, .minimal-tooltip-trigger') {
    document.querySelectorAll(selector).forEach(function (el) {
      // Skip if already initialized
      if (el.dataset.tooltipInitialized === 'true') return;

      el.addEventListener('mouseenter', function (e) {
        let text = el.getAttribute('data-tooltip');
        if (text) showTooltip(e, text);
      });
      el.addEventListener('mousemove', function (e) {
        if (tooltip.classList.contains('visible')) positionTooltip(e);
      });
      el.addEventListener('mouseleave', hideTooltip);
      el.addEventListener('focus', function (e) {
        let text = el.getAttribute('data-tooltip');
        if (text) {
          showTooltip(
            {
              clientX: el.getBoundingClientRect().left + el.offsetWidth / 2,
              clientY: el.getBoundingClientRect().top,
            },
            text
          );
        }
      });
      el.addEventListener('blur', hideTooltip);

      // Mark as initialized
      el.dataset.tooltipInitialized = 'true';
    });
  }

  // Initialize tooltips on page load
  initTooltips();

  // Make the init function available globally
  window.initMinimalTooltips = initTooltips;
});
