// jQuery-based modal and toggle logic for budget detail page
$(function () {
  // Show Add Expense modal (clear form)
  $('[data-modal-target="#expenseModal"]').on('click', function () {
    $('#expense-form')[0].reset();
    $('#expense_id').val('');
    openModalWithAnimation('#expenseModal');
  });

  // Show Edit Expense modal (fill form)
  $('.edit-expense-btn').on('click', function () {
    var btn = $(this);
    $('#expense_id').val(btn.data('expense-id'));
    $('#expense_name').val(btn.data('expense-name'));
    $('#expense_amount').val(btn.data('expense-amount'));
    $('#expense_category').val(btn.data('expense-category'));
    $('#expense_tag').val(btn.data('expense-tag'));
    $('#expense_recurring').prop(
      'checked',
      btn.data('expense-recurring') === true || btn.data('expense-recurring') === 'true'
    );
    openModalWithAnimation('#expenseModal');
  });

  // Cancel Expense modal
  $('.expense-cancel-btn').on('click', function () {
    closeModalWithAnimation('#expenseModal');
  });

  // Show Income modal
  $('.edit-income-btn').on('click', function () {
    openModalWithAnimation('#incomeModal');
  });

  // Cancel Income modal
  $('.income-cancel-btn').on('click', function () {
    closeModalWithAnimation('#incomeModal');
  });

  // Close modal when clicking outside the modal content
  $('.modal.glassy').on('click', function (e) {
    if ($(e.target).hasClass('modal')) {
      closeModalWithAnimation('#' + $(this).attr('id'));
    }
  });

  // Helper function to open modal with animation
  function openModalWithAnimation(modalId) {
    const $modal = $(modalId);
    $modal.css('display', 'flex');

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
  }

  // Helper function to close modal with animation
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
        $modal.hide();
      },
    });
  }

  // Toggle summary section with animation
  $('.summary-toggle-btn').on('click', function () {
    var content = $('.summary-toggle-content');
    var text = $('.summary-toggle-text');
    var isVisible = content.is(':visible');

    if (isVisible) {
      // Hide with animation
      anime({
        targets: '.summary-toggle-content',
        opacity: [1, 0],
        height: [content.height(), 0],
        duration: 300,
        easing: 'easeInOutQuad',
        complete: function () {
          content.hide();
          text.text('Show Summary');
        },
      });
    } else {
      // Show with animation
      content.css({
        opacity: 0,
        height: 0,
        display: 'block',
        overflow: 'hidden',
      });

      anime({
        targets: '.summary-toggle-content',
        opacity: [0, 1],
        height: [0, content[0].scrollHeight],
        duration: 400,
        easing: 'easeOutQuad',
        complete: function () {
          content.css({
            height: '',
            overflow: '',
          });
          text.text('Hide Summary');
        },
      });
    }
  });

  // Toggle category stats section with animation
  $('.category-stats-toggle-btn').on('click', function () {
    var content = $('.category-stats-toggle-content');
    var text = $('.category-stats-toggle-text');
    var isVisible = content.is(':visible');

    if (isVisible) {
      // Hide with animation
      anime({
        targets: '.category-stats-toggle-content',
        opacity: [1, 0],
        height: [content.height(), 0],
        duration: 300,
        easing: 'easeInOutQuad',
        complete: function () {
          content.hide();
          text.text('Show Category Stats');
        },
      });
    } else {
      // Show with animation
      content.css({
        opacity: 0,
        height: 0,
        display: 'block',
        overflow: 'hidden',
      });

      anime({
        targets: '.category-stats-toggle-content',
        opacity: [0, 1],
        height: [0, content[0].scrollHeight],
        duration: 400,
        easing: 'easeOutQuad',
        complete: function () {
          content.css({
            height: '',
            overflow: '',
          });
          text.text('Hide Category Stats');
        },
      });
    }
  });

  // Basic client-side validation for expense form
  const expenseForm = document.getElementById('expense-form');
  if (expenseForm) {
    expenseForm.addEventListener('submit', function (e) {
      let valid = true;
      const name = expenseForm.querySelector('[name=name]');
      const amount = expenseForm.querySelector('[name=amount]');
      if (!name.value.trim()) {
        name.classList.add('is-invalid');
        valid = false;
      } else {
        name.classList.remove('is-invalid');
      }
      if (!amount.value.trim() || isNaN(amount.value) || Number(amount.value) <= 0) {
        amount.classList.add('is-invalid');
        valid = false;
      } else {
        amount.classList.remove('is-invalid');
      }
      if (!valid) {
        e.preventDefault();
      }
    });
  }
});
