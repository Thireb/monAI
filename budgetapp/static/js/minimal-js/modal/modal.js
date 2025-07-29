/**
 * Minimal Theme Modal Functionality
 * Provides smooth animations and functionality for modals
 */

// Initialize modals when document is ready
$(function () {
  // Prevent Bootstrap from initializing on our custom modals
  $('.modal-minimal').each(function () {
    // Remove any Bootstrap modal attributes that might cause conflicts
    $(this).removeAttr('data-bs-toggle data-bs-target data-bs-dismiss');
  });

  // Handle modal triggers with data-modal-target attribute
  $('[data-modal-target]').on('click', function () {
    const modalId = $(this).data('modal-target');
    openModalWithAnimation(modalId);
  });

  // Close modal when clicking outside the modal content
  $('.modal-minimal').on('click', function (e) {
    if ($(e.target).hasClass('modal-minimal')) {
      closeModalWithAnimation('#' + $(this).attr('id'));
    }
  });

  // Generic modal cancel buttons
  $('.modal-minimal .btn-minimal[aria-label="Cancel"]').on('click', function () {
    const modalId = '#' + $(this).closest('.modal-minimal').attr('id');
    closeModalWithAnimation(modalId);
  });
});

/**
 * Opens a modal with animation
 * @param {string} modalId - The ID of the modal to open (with # prefix)
 */
function openModalWithAnimation(modalId) {
  const $modal = $(modalId);
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
      $modal.hide().removeClass('show');
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
