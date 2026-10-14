/**
 * Minimal Theme Modal Functionality
 * Provides smooth animations and functionality for modals
 */

/**
 * Opens a modal with animation
 * @param {string} modalId - The ID of the modal to open (with # prefix)
 */
function openModalWithAnimation(modalId) {
  const $modal = $(modalId);
  if (!$modal.length) {
    console.warn('Modal not found:', modalId);
    return;
  }
  // Several click handlers can ask for the same modal; open it only once.
  if ($modal.hasClass('show') && !$modal.hasClass('closing')) return;
  // Opened again while closing: stop the close animation first.
  if ($modal.hasClass('closing')) {
    anime.remove(modalId);
    anime.remove(modalId + ' .modal-content');
    $modal.removeClass('closing');
  }

  // Remove Bootstrap classes if present
  $modal.removeClass('modal fade');

  $modal.css('display', 'flex').addClass('show');

  // Use anime.js for smooth animation
  anime({
    targets: modalId,
    opacity: [0, 1],
    duration: 300,
    easing: 'easeOutQuad',
  });

  anime({
    targets: modalId + ' .modal-content',
    translateY: [20, 0],
    opacity: [0.8, 1],
    duration: 400,
    easing: 'easeOutQuad',
  });

  // Trigger custom event for modal opened
  $modal.trigger('modal:opened');
}

/**
 * Closes a modal with animation
 * @param {string} modalId - The ID of the modal to close (with # prefix)
 */
function closeModalWithAnimation(modalId) {
  const $modal = $(modalId);
  if (!$modal.length || !$modal.hasClass('show') || $modal.hasClass('closing')) return;
  $modal.addClass('closing');

  // Use anime.js for smooth animation
  anime({
    targets: modalId + ' .modal-content',
    translateY: [0, 20],
    opacity: [1, 0.8],
    duration: 250,
    easing: 'easeInQuad',
  });

  anime({
    targets: modalId,
    opacity: [1, 0],
    duration: 300,
    easing: 'easeInQuad',
    complete: function () {
      $modal.hide().removeClass('show closing');
      // Trigger custom event for modal closed
      $modal.trigger('modal:closed');
    },
  });
}

/**
 * Resets a modal form
 * @param {string} modalId - The ID of the modal containing the form to reset (with # prefix)
 */
function resetModalForm(modalId) {
  const $form = $(modalId + ' form');
  if ($form.length) {
    $form[0].reset();
    // Remove any validation classes
    $form.find('.is-invalid').removeClass('is-invalid');
  }
}

// Initialize modals when document is ready
$(function () {
  // Bind the shared handlers only once, even if this file loads twice.
  if (window.minimalModalsInitialized) return;
  window.minimalModalsInitialized = true;

  // Prevent Bootstrap from initializing on our custom modals
  $('.modal-minimal').each(function () {
    // Remove any Bootstrap modal attributes that might cause conflicts
    $(this).removeAttr('data-bs-toggle data-bs-target data-bs-dismiss');
    $(this).removeClass('modal fade');
  });

  // Handle modal triggers with data-modal-target attribute
  $(document).on('click', '[data-modal-target]', function () {
    const modalId = $(this).data('modal-target');
    openModalWithAnimation(modalId);
  });

  // Close modal when clicking outside the modal content (delegated)
  $(document).on('click', '.modal-minimal', function (e) {
    if ($(e.target).hasClass('modal-minimal')) {
      closeModalWithAnimation('#' + $(this).attr('id'));
    }
  });

  // Generic modal cancel buttons - delegated event handler
  // Matches any button with aria-label="Cancel" inside modal-minimal
  $(document).on('click', '.modal-minimal .btn[aria-label="Cancel"]', function () {
    const modalId = '#' + $(this).closest('.modal-minimal').attr('id');
    closeModalWithAnimation(modalId);
  });

  // Handle close buttons (X button in header) - delegated
  $(document).on('click', '.modal-minimal .btn-close', function () {
    const modalId = '#' + $(this).closest('.modal-minimal').attr('id');
    closeModalWithAnimation(modalId);
  });

  // ESC key to close any open modal
  $(document).on('keydown', function (e) {
    if (e.key === 'Escape') {
      const $openModal = $('.modal-minimal.show');
      if ($openModal.length) {
        closeModalWithAnimation('#' + $openModal.attr('id'));
      }
    }
  });

  // Reset forms when modal closes
  $(document).on('modal:closed', '.modal-minimal', function () {
    const $form = $(this).find('form');
    if ($form.length) {
      $form[0].reset();
    }
    $(this).find('.is-invalid').removeClass('is-invalid');
  });
});
