$(document).ready(function () {
  let isEditMode = false;
  let currentEditTagId = null;

  // Initialize page animations
  initializeAnimations();

  // Handle tag form submission
  $('#tag-form').on('submit', function (e) {
    e.preventDefault();

    if (isEditMode) {
      updateTag();
    } else {
      createTag();
    }
  });

  // Handle ESC key to cancel edit mode
  $(document).on('keydown', function (e) {
    if (e.key === 'Escape' && isEditMode) {
      cancelEdit();
    }
  });

  // Handle edit tag button clicks
  $(document).on('click', '.edit-tag-btn', function () {
    const tagId = $(this).data('tag-id');
    const tagName = $(this).data('tag-name');
    const tagDescription = $(this).data('tag-description');
    const tagColor = $(this).data('tag-color');

    // Populate form with tag data
    $('#tag-name').val(tagName);
    $('#tag-description').val(tagDescription);
    $('#tag-color').val(tagColor);

    // Change form to edit mode
    isEditMode = true;
    currentEditTagId = tagId;
    $('#tag-submit-btn').text('Update Tag');

    // Add hidden input for tag ID
    if (!$('#tag-id').length) {
      $('#tag-form').append('<input type="hidden" id="tag-id" name="tag_id">');
    }
    $('#tag-id').val(tagId);

    // Add cancel hint
    addCancelHint();

    // Scroll to form and focus on name field
    $('html, body').animate(
      {
        scrollTop: $('#tag-form').offset().top - 100,
      },
      500
    );
    $('#tag-name').focus();
  });

  // Handle delete tag button clicks
  $(document).on('click', '.delete-tag-btn', function () {
    const tagId = $(this).data('tag-id');
    const tagName = $(this).data('tag-name');

    if (confirm(`Are you sure you want to delete the tag "${tagName}"?`)) {
      deleteTag(tagId);
    }
  });

  // Create new tag
  function createTag() {
    const formData = {
      name: $('#tag-name').val(),
      description: $('#tag-description').val(),
      color: $('#tag-color').val(),
      csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
    };

    $.ajax({
      url: '/minimal/tags/create/',
      type: 'POST',
      data: formData,
      beforeSend: function () {
        $('#tag-submit-btn').addClass('loading').text('Creating...');
      },
      success: function (response) {
        if (response.status === 'success') {
          showAlert('success', response.message);
          addTagToList(response.tag);
          resetForm();

          // Animate new tag entry with enhanced animation
          anime({
            targets: '.tag-item:last-child',
            opacity: [0, 1],
            translateY: [30, 0],
            scale: [0.95, 1],
            duration: 800,
            easing: 'easeOutCubic',
          });
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showAlert('danger', response.message || 'Error creating tag');
      },
      complete: function () {
        $('#tag-submit-btn').removeClass('loading').text('Add Tag');
      },
    });
  }

  // Update existing tag
  function updateTag() {
    const formData = {
      tag_id: currentEditTagId,
      name: $('#tag-name').val(),
      description: $('#tag-description').val(),
      color: $('#tag-color').val(),
      csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
    };

    $.ajax({
      url: '/minimal/tags/update/',
      type: 'POST',
      data: formData,
      beforeSend: function () {
        $('#tag-submit-btn').addClass('loading').text('Updating...');
      },
      success: function (response) {
        if (response.status === 'success') {
          showAlert('success', response.message);
          updateTagInList(response.tag);
          resetForm();

          // Enhanced animation for updated tag
          const tagItem = $(`.tag-item[data-tag-id="${currentEditTagId}"]`);
          anime({
            targets: tagItem[0],
            backgroundColor: ['rgba(76, 175, 80, 0.15)', 'rgba(255, 255, 255, 0.7)'],
            scale: [1.02, 1],
            duration: 1200,
            easing: 'easeInOutQuad',
          });

          // Scroll to top if the updated item was at the bottom
          const itemPosition = tagItem.offset().top;
          const windowHeight = $(window).height();
          const documentHeight = $(document).height();

          if (itemPosition > windowHeight * 0.7) {
            $('html, body').animate(
              {
                scrollTop: $('#tag-form').offset().top - 100,
              },
              800,
              'easeOutCubic'
            );
          }
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showAlert('danger', response.message || 'Error updating tag');
      },
      complete: function () {
        // Ensure loading class is removed even if resetForm() wasn't called
        $('#tag-submit-btn').removeClass('loading');
      },
    });
  }

  // Delete tag
  function deleteTag(tagId) {
    const formData = {
      tag_id: tagId,
      csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
    };

    $.ajax({
      url: '/minimal/tags/delete/',
      type: 'POST',
      data: formData,
      success: function (response) {
        if (response.status === 'success') {
          showAlert('success', response.message);
          removeTagFromList(tagId);
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showAlert('danger', response.message || 'Error deleting tag');
      },
    });
  }

  // Add tag to list
  function addTagToList(tag) {
    const tagHtml = `
            <li class="tag-item" data-tag-id="${tag.id}">
                <div class="tag-info">
                    <span class="tag-color-dot" style="background-color: ${tag.color};"></span>
                    <span class="tag-name">${tag.name}</span>
                    ${tag.description ? `<span class="tag-description">- ${tag.description}</span>` : ''}
                </div>
                <div class="tag-actions">
                    <button class="btn-icon edit-tag-btn" data-tag-id="${tag.id}"
                            data-tag-name="${tag.name}"
                            data-tag-description="${tag.description || ''}"
                            data-tag-color="${tag.color}"
                            title="Edit tag">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                    <button class="btn-icon btn-danger delete-tag-btn" data-tag-id="${tag.id}"
                            data-tag-name="${tag.name}" title="Delete tag">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 6h18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            </li>
        `;

    // Remove no-tags message if it exists
    $('.no-tags-message').remove();

    // Add to list
    if ($('.tags-list').length) {
      $('.tags-list').append(tagHtml);
    } else {
      $('#tags-list').html(`<ul class="tags-list">${tagHtml}</ul>`);
    }
  }

  // Update tag in list
  function updateTagInList(tag) {
    const tagItem = $(`.tag-item[data-tag-id="${tag.id}"]`);
    tagItem.find('.tag-color-dot').css('background-color', tag.color);
    tagItem.find('.tag-name').text(tag.name);
    tagItem.find('.tag-description').text(tag.description ? `- ${tag.description}` : '');

    // Update data attributes
    tagItem.find('.edit-tag-btn').data({
      'tag-name': tag.name,
      'tag-description': tag.description || '',
      'tag-color': tag.color,
    });
    tagItem.find('.delete-tag-btn').data('tag-name', tag.name);
  }

  // Remove tag from list
  function removeTagFromList(tagId) {
    const tagItem = $(`.tag-item[data-tag-id="${tagId}"]`);

    // Enhanced removal animation
    anime({
      targets: tagItem[0],
      opacity: [1, 0],
      translateX: [0, -30],
      scale: [1, 0.9],
      duration: 500,
      easing: 'easeInOutQuad',
      complete: function () {
        tagItem.remove();

        // Show no-tags message if no tags left
        if ($('.tag-item').length === 0) {
          $('#tags-list').html(`
                        <div class="no-tags-message">
                            <p class="text-muted">No tags created yet. Add your first tag above!</p>
                        </div>
                    `);
        }
      },
    });
  }

  // Cancel edit mode
  function cancelEdit() {
    resetForm();
    showAlert('info', 'Edit cancelled');
  }

  // Add cancel hint
  function addCancelHint() {
    if (!$('.cancel-hint').length) {
      const hintHtml =
        '<div class="cancel-hint text-muted mt-2 text-center"><small>Press ESC to cancel</small></div>';
      $('#tag-submit-btn').parent().append(hintHtml);

      // Animate the hint in
      anime({
        targets: '.cancel-hint',
        opacity: [0, 1],
        translateY: [10, 0],
        duration: 400,
        easing: 'easeOutCubic',
      });
    }
  }

  // Reset form
  function resetForm() {
    $('#tag-form')[0].reset();
    $('#tag-color').val('#2196f3');
    isEditMode = false;
    currentEditTagId = null;
    $('#tag-submit-btn').removeClass('loading').text('Add Tag');
    $('#tag-id').remove();

    // Remove cancel hint with animation
    const cancelHint = $('.cancel-hint');
    if (cancelHint.length) {
      anime({
        targets: cancelHint[0],
        opacity: [1, 0],
        translateY: [0, -10],
        duration: 300,
        easing: 'easeInQuad',
        complete: function () {
          cancelHint.remove();
        },
      });
    }
  }

  // Show alert message with enhanced animations
  // Helper function to show toast notifications
  function showToast(title, message, type) {
    // Check if we have a toast container, if not create one
    if ($('#toast-container').length === 0) {
      $('body').append(
        '<div id="toast-container" class="position-fixed top-0 end-0 p-3" style="z-index: 1050;"></div>'
      );
    }

    // Create a unique ID for this toast
    const toastId = 'toast-' + Date.now();

    // Create the toast element
    const toast = $(`
      <div id="${toastId}" class="toast align-items-center border-0" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">
            <strong>${title}:</strong> ${message}
          </div>
          <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>
    `);

    // Add color based on type
    if (type === 'success') {
      toast.addClass('bg-success text-white');
    } else if (type === 'error') {
      toast.addClass('bg-danger text-white');
    } else if (type === 'warning') {
      toast.addClass('bg-warning');
    } else {
      toast.addClass('bg-info text-white');
    }

    // Add to container
    $('#toast-container').append(toast);

    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast[0], {
      autohide: true,
      delay: 5000,
    });
    bsToast.show();

    // Remove from DOM after hidden
    toast.on('hidden.bs.toast', function () {
      $(this).remove();
    });
  }

  // Legacy showAlert function for backward compatibility
  function showAlert(type, message) {
    const title = type.charAt(0).toUpperCase() + type.slice(1);
    showToast(title, message, type);
  }

  // Initialize page animations
  function initializeAnimations() {
    // Animate header
    anime({
      targets: '.tag-header',
      opacity: [0, 1],
      translateY: [-30, 0],
      duration: 800,
      easing: 'easeOutCubic',
    });

    // Animate form section
    anime({
      targets: '.add-tag-section',
      opacity: [0, 1],
      translateY: [20, 0],
      duration: 600,
      delay: 200,
      easing: 'easeOutCubic',
    });

    // Animate tags list
    anime({
      targets: '.tags-list-section',
      opacity: [0, 1],
      translateY: [20, 0],
      duration: 600,
      delay: 400,
      easing: 'easeOutCubic',
    });

    // Animate existing tags with staggered effect
    anime({
      targets: '.tag-item',
      opacity: [0, 1],
      translateY: [20, 0],
      scale: [0.95, 1],
      delay: anime.stagger(100, { start: 600 }),
      duration: 600,
      easing: 'easeOutCubic',
    });
  }

  // Handle form reset button (optional)
  $(document).on('click', '#reset-form-btn', function () {
    resetForm();
  });
});
