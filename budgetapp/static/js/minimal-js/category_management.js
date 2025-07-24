$(document).ready(function () {
  let isEditMode = false;
  let currentEditCategoryId = null;

  // Initialize page animations
  initializeAnimations();

  // Handle category form submission
  $('#category-form').on('submit', function (e) {
    e.preventDefault();

    if (isEditMode) {
      updateCategory();
    } else {
      createCategory();
    }
  });

  // Handle ESC key to cancel edit mode
  $(document).on('keydown', function (e) {
    if (e.key === 'Escape' && isEditMode) {
      cancelEdit();
    }
  });

  // Handle edit category button clicks
  $(document).on('click', '.edit-category-btn', function () {
    const categoryId = $(this).data('category-id');
    const categoryName = $(this).data('category-name');
    const categoryDescription = $(this).data('category-description');
    const categoryColor = $(this).data('category-color');

    // Populate form with category data
    $('#category-name').val(categoryName);
    $('#category-description').val(categoryDescription);
    $('#category-color').val(categoryColor);

    // Change form to edit mode
    isEditMode = true;
    currentEditCategoryId = categoryId;
    $('#category-submit-btn').text('Update Category');

    // Add hidden input for category ID
    if (!$('#category-id').length) {
      $('#category-form').append('<input type="hidden" id="category-id" name="category_id">');
    }
    $('#category-id').val(categoryId);

    // Add cancel hint
    addCancelHint();

    // Scroll to form and focus on name field
    $('html, body').animate(
      {
        scrollTop: $('#category-form').offset().top - 100,
      },
      500
    );
    $('#category-name').focus();
  });

  // Handle delete category button clicks
  $(document).on('click', '.delete-category-btn', function () {
    const categoryId = $(this).data('category-id');
    const categoryName = $(this).data('category-name');

    if (confirm(`Are you sure you want to delete the category "${categoryName}"?`)) {
      deleteCategory(categoryId);
    }
  });

  // Create new category
  function createCategory() {
    const formData = {
      name: $('#category-name').val(),
      description: $('#category-description').val(),
      color: $('#category-color').val(),
      csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
    };

    $.ajax({
      url: '/minimal/categories/create/',
      type: 'POST',
      data: formData,
      beforeSend: function () {
        $('#category-submit-btn').addClass('loading').text('Creating...');
      },
      success: function (response) {
        if (response.success) {
          showAlert('success', response.message || 'Category created successfully!');
          addCategoryToList(response.category);
          resetForm();

          // Animate new category entry with enhanced animation
          anime({
            targets: '.category-item:last-child',
            opacity: [0, 1],
            translateY: [30, 0],
            scale: [0.95, 1],
            duration: 800,
            easing: 'easeOutCubic',
          });
        } else {
          showAlert('danger', response.error || 'Error creating category');
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showAlert('danger', response?.error || 'Error creating category');
      },
      complete: function () {
        $('#category-submit-btn').removeClass('loading').text('Add Category');
      },
    });
  }

  // Update existing category
  function updateCategory() {
    const formData = {
      category_id: currentEditCategoryId,
      name: $('#category-name').val(),
      description: $('#category-description').val(),
      color: $('#category-color').val(),
      csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
    };

    $.ajax({
      url: '/minimal/categories/update/',
      type: 'POST',
      data: formData,
      beforeSend: function () {
        $('#category-submit-btn').addClass('loading').text('Updating...');
      },
      success: function (response) {
        if (response.success) {
          showAlert('success', response.message || 'Category updated successfully!');
          updateCategoryInList(response.category);
          resetForm();

          // Enhanced animation for updated category
          const categoryItem = $(`.category-item[data-category-id="${currentEditCategoryId}"]`);
          anime({
            targets: categoryItem[0],
            backgroundColor: ['rgba(76, 175, 80, 0.15)', 'rgba(255, 255, 255, 0.7)'],
            scale: [1.02, 1],
            duration: 1200,
            easing: 'easeInOutQuad',
          });

          // Scroll to top if the updated item was at the bottom
          const itemPosition = categoryItem.offset().top;
          const windowHeight = $(window).height();
          const documentHeight = $(document).height();

          if (itemPosition > windowHeight * 0.7) {
            $('html, body').animate(
              {
                scrollTop: $('#category-form').offset().top - 100,
              },
              800,
              'easeOutCubic'
            );
          }
        } else {
          showAlert('danger', response.error || 'Error updating category');
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showAlert('danger', response?.error || 'Error updating category');
      },
      complete: function () {
        $('#category-submit-btn').removeClass('loading').text('Add Category');
      },
    });
  }

  // Delete category
  function deleteCategory(categoryId) {
    const formData = {
      category_id: categoryId,
      csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
    };

    $.ajax({
      url: '/minimal/categories/delete/',
      type: 'POST',
      data: formData,
      success: function (response) {
        if (response.success) {
          showAlert('success', response.message || 'Category deleted successfully!');
          removeCategoryFromList(categoryId);
        } else {
          showAlert('danger', response.error || 'Error deleting category');
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showAlert('danger', response?.error || 'Error deleting category');
      },
    });
  }

  // Load categories
  function loadCategories() {
    $.ajax({
      url: '/minimal/categories/list/',
      type: 'GET',
      success: function (response) {
        const container = $('#categories-container');
        if (response.categories && response.categories.length > 0) {
          const categoriesHtml = response.categories
            .map(
              category => `
            <li class="category-item" data-category-id="${category.id}">
                <div class="category-info">
                    <span class="category-color-dot" style="background-color: ${category.color};"></span>
                    <span class="category-name">${category.name}</span>
                    ${category.description ? `<span class="category-description">- ${category.description}</span>` : ''}
                </div>
                <div class="category-actions">
                    <button class="btn-icon edit-category-btn" data-category-id="${category.id}"
                            data-category-name="${category.name}"
                            data-category-description="${category.description || ''}"
                            data-category-color="${category.color}"
                            title="Edit category">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                    <button class="btn-icon btn-danger delete-category-btn" data-category-id="${category.id}"
                            data-category-name="${category.name}" title="Delete category">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 6h18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            </li>
          `
            )
            .join('');

          container.html(`<ul class="categories-list">${categoriesHtml}</ul>`);
        } else {
          container.html(`
            <div class="no-categories-message">
                <p class="text-muted">No categories created yet. Add your first category above!</p>
            </div>
          `);
        }
      },
      error: function () {
        $('#categories-container').html(
          '<div class="text-center text-danger">Error loading categories. Please try again.</div>'
        );
      },
    });
  }

  // Add category to list
  function addCategoryToList(category) {
    const categoryHtml = `
            <li class="category-item" data-category-id="${category.id}">
                <div class="category-info">
                    <span class="category-color-dot" style="background-color: ${category.color};"></span>
                    <span class="category-name">${category.name}</span>
                    ${category.description ? `<span class="category-description">- ${category.description}</span>` : ''}
                </div>
                <div class="category-actions">
                    <button class="btn-icon edit-category-btn" data-category-id="${category.id}"
                            data-category-name="${category.name}"
                            data-category-description="${category.description || ''}"
                            data-category-color="${category.color}"
                            title="Edit category">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                    <button class="btn-icon btn-danger delete-category-btn" data-category-id="${category.id}"
                            data-category-name="${category.name}" title="Delete category">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 6h18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            </li>
        `;

    // Remove no-categories message if it exists
    $('.no-categories-message').remove();

    // Add to list
    if ($('.categories-list').length) {
      $('.categories-list').append(categoryHtml);
    } else {
      $('#categories-container').html(`<ul class="categories-list">${categoryHtml}</ul>`);
    }
  }

  // Update category in list
  function updateCategoryInList(category) {
    const categoryItem = $(`.category-item[data-category-id="${category.id}"]`);
    categoryItem.find('.category-color-dot').css('background-color', category.color);
    categoryItem.find('.category-name').text(category.name);
    categoryItem
      .find('.category-description')
      .text(category.description ? `- ${category.description}` : '');

    // Update data attributes
    categoryItem.find('.edit-category-btn').data({
      'category-name': category.name,
      'category-description': category.description || '',
      'category-color': category.color,
    });
    categoryItem.find('.delete-category-btn').data('category-name', category.name);
  }

  // Remove category from list
  function removeCategoryFromList(categoryId) {
    const categoryItem = $(`.category-item[data-category-id="${categoryId}"]`);

    // Enhanced removal animation
    anime({
      targets: categoryItem[0],
      opacity: [1, 0],
      translateX: [0, -30],
      scale: [1, 0.9],
      duration: 500,
      easing: 'easeInOutQuad',
      complete: function () {
        categoryItem.remove();

        // Show no-categories message if no categories left
        if ($('.category-item').length === 0) {
          $('#categories-container').html(`
                        <div class="no-categories-message">
                            <p class="text-muted">No categories created yet. Add your first category above!</p>
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
      $('#category-submit-btn').parent().append(hintHtml);

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
    $('#category-form')[0].reset();
    $('#category-color').val('#2196f3');
    isEditMode = false;
    currentEditCategoryId = null;
    $('#category-submit-btn').text('Add Category');
    $('#category-id').remove();

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
    $('.category-management-container').prepend(alertHtml);

    // Animate alert in
    anime({
      targets: '.alert',
      opacity: [0, 1],
      translateY: [-20, 0],
      scale: [0.95, 1],
      duration: 500,
      easing: 'easeOutCubic',
    });

    // Handle manual close button with smooth animation
    $('.alert .btn-close').on('click', function (e) {
      e.preventDefault();
      e.stopPropagation();

      anime({
        targets: '.alert',
        opacity: [1, 0],
        translateY: [0, -30],
        scale: [1, 0.9],
        duration: 600,
        easing: 'easeOutCubic',
        complete: function () {
          $('.alert').remove();
        },
      });
    });

    // Auto-dismiss after 5 seconds with smooth animation
    setTimeout(function () {
      anime({
        targets: '.alert',
        opacity: [1, 0],
        translateY: [0, -20],
        scale: [1, 0.95],
        duration: 400,
        easing: 'easeInQuad',
        complete: function () {
          $('.alert').remove();
        },
      });
    }, 5000);
  }

  // Initialize page animations
  function initializeAnimations() {
    // Animate header
    anime({
      targets: '.category-header',
      opacity: [0, 1],
      translateY: [-30, 0],
      duration: 800,
      easing: 'easeOutCubic',
    });

    // Animate form section
    anime({
      targets: '.add-category-section',
      opacity: [0, 1],
      translateY: [20, 0],
      duration: 600,
      delay: 200,
      easing: 'easeOutCubic',
    });

    // Animate categories list
    anime({
      targets: '.categories-list-section',
      opacity: [0, 1],
      translateY: [20, 0],
      duration: 600,
      delay: 400,
      easing: 'easeOutCubic',
    });

    // Animate existing categories with staggered effect
    anime({
      targets: '.category-item',
      opacity: [0, 1],
      translateY: [20, 0],
      scale: [0.95, 1],
      delay: anime.stagger(100, { start: 600 }),
      duration: 600,
      easing: 'easeOutCubic',
    });
  }

  // Load categories on page load
  loadCategories();

  // Handle form reset button (optional)
  $(document).on('click', '#reset-form-btn', function () {
    resetForm();
  });
});
