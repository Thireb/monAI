/**
 * Core utilities for minimal theme
 * Load this file BEFORE other page-specific JS
 */

/**
 * Show toast notification
 * @param {string} title - Toast title
 * @param {string} message - Toast message
 * @param {string} type - Type: 'success', 'error', 'warning', 'info'
 */
function showToast(title, message, type) {
  // Check if we have a toast container, if not create one
  if ($('#toast-container').length === 0) {
    $('body').append(
      '<div id="toast-container" class="position-fixed top-0 end-0 p-3" style="z-index: 1050;"></div>'
    );
  }

  // Create a unique ID for this toast
  var toastId = 'toast-' + Date.now();

  // Create the toast element
  var toast = $(
    '<div id="' +
      toastId +
      '" class="toast align-items-center border-0" role="alert" aria-live="assertive" aria-atomic="true">' +
      '<div class="d-flex">' +
      '<div class="toast-body">' +
      '<strong>' +
      title +
      ':</strong> ' +
      message +
      '</div>' +
      '<button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
      '</div>' +
      '</div>'
  );

  // Add color based on type
  var colorMap = {
    success: 'bg-success text-white',
    error: 'bg-danger text-white',
    warning: 'bg-warning',
    info: 'bg-info text-white',
  };
  toast.addClass(colorMap[type] || colorMap.info);

  // Add to container
  $('#toast-container').append(toast);

  // Initialize and show the toast
  var bsToast = new bootstrap.Toast(toast[0], {
    autohide: true,
    delay: 5000,
  });
  bsToast.show();

  // Remove from DOM after hidden
  toast.on('hidden.bs.toast', function () {
    $(this).remove();
  });
}

/**
 * Format currency value with proper separators
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
  return amount.toLocaleString('en', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Escape string for use in HTML attributes
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeForAttr(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

/**
 * Escape HTML to prevent XSS
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
  if (!str) return '';
  return $('<div>').text(str).html();
}

/**
 * Display form validation errors from server response
 * @param {jQuery} $form - The form jQuery element
 * @param {Object} errors - Error object { field: [errors], __all__: [errors] }
 */
function displayFormErrors($form, errors) {
  clearFormErrors($form);
  if (!errors) return;

  for (var field in errors) {
    if (errors.hasOwnProperty(field)) {
      var fieldErrors = errors[field];
      if (field === '__all__' || field === 'non_field_errors') {
        var $errorContainer = $form.find('.form-errors');
        if ($errorContainer.length) {
          $errorContainer.html(fieldErrors.join('<br>')).show();
        }
      } else {
        var $input = $form.find('[name="' + field + '"]');
        if ($input.length) {
          $input.addClass('is-invalid');
          var $feedback = $input.siblings('.invalid-feedback');
          if ($feedback.length) {
            $feedback.html(fieldErrors.join(' ')).show();
          }
        }
      }
    }
  }
}

/**
 * Clear all form validation errors
 * @param {jQuery} $form - The form jQuery element
 */
function clearFormErrors($form) {
  $form.find('.is-invalid').removeClass('is-invalid');
  $form.find('.invalid-feedback').text('').hide();
  $form.find('.form-errors').text('').hide();
}

// Make functions globally available
window.showToast = showToast;
window.formatCurrency = formatCurrency;
window.escapeForAttr = escapeForAttr;
window.escapeHtml = escapeHtml;
window.displayFormErrors = displayFormErrors;
window.clearFormErrors = clearFormErrors;

