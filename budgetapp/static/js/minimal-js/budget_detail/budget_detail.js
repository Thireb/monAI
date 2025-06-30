// Budget detail page specific functionality
$(function () {
  // Show Add Expense modal (clear form)
  $('[data-modal-target="#expenseModal"]').on('click', function () {
    resetExpenseForm();
    openModalWithAnimation('#expenseModal');
  });

  // Show Edit Expense modal (fill form with data)
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

    // Use the shared openModalWithAnimation function
    openModalWithAnimation('#expenseModal');
  });

  // Show Income modal
  $('[data-modal-target="#incomeModal"]').on('click', function () {
    openModalWithAnimation('#incomeModal');
  });

  // Handle modal cancel buttons
  $('.expense-cancel-btn').on('click', function () {
    closeModalWithAnimation('#expenseModal');
  });

  $('.income-cancel-btn').on('click', function () {
    closeModalWithAnimation('#incomeModal');
  });

  // Reset expense form helper
  function resetExpenseForm() {
    $('#expense-form')[0].reset();
    $('#expense_id').val('');
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
