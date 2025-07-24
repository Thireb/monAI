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

    // Scroll to form and focus on name field
    $('html, body').animate(
      {
        scrollTop: $('#tag-form').offset().top - 100,
      },
      500
    );
    $('#tag-name').focus();

    // Remove the blue background highlight animation
    // anime({
    //     targets: '#tag-form',
    //     backgroundColor: ['rgba(33, 150, 243, 0.05)', 'rgba(255, 255, 255, 0.8)'],
    //     duration: 1000,
    //     easing: 'easeInOutQuad'
    // });
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

          // Animate new tag entry
          anime({
            targets: '.tag-item:last-child',
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 600,
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

          // Animate updated tag
          const tagItem = $(`.tag-item[data-tag-id="${currentEditTagId}"]`);
          anime({
            targets: tagItem[0],
            backgroundColor: ['rgba(76, 175, 80, 0.1)', 'rgba(255, 255, 255, 0.7)'],
            duration: 1000,
            easing: 'easeInOutQuad',
          });
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showAlert('danger', response.message || 'Error updating tag');
      },
      complete: function () {
        $('#tag-submit-btn').removeClass('loading').text('Add Tag');
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

    // Animate removal
    anime({
      targets: tagItem[0],
      opacity: [1, 0],
      translateX: [0, -20],
      duration: 400,
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

  // Reset form
  function resetForm() {
    $('#tag-form')[0].reset();
    $('#tag-color').val('#2196f3');
    isEditMode = false;
    currentEditTagId = null;
    $('#tag-submit-btn').text('Add Tag');
    $('#tag-id').remove();

    // Remove form highlight - no longer needed
    // $('#tag-form').css('background-color', 'rgba(255, 255, 255, 0.8)');
  }

  // Show alert message
  function showAlert(type, message) {
    const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

    // Remove existing alerts
    $('.alert').remove();

    // Add new alert
    $('.tag-management-container').prepend(alertHtml);

    // Auto-dismiss after 5 seconds with smooth animation
    setTimeout(function () {
      $('.alert').fadeOut(800, function () {
        $(this).remove();
      });
    }, 5000);
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

    // Animate existing tags
    anime({
      targets: '.tag-item',
      opacity: [0, 1],
      translateY: [20, 0],
      delay: anime.stagger(100, { start: 600 }),
      duration: 500,
      easing: 'easeOutCubic',
    });
  }

  // Handle form reset button (optional)
  $(document).on('click', '#reset-form-btn', function () {
    resetForm();
  });
});
