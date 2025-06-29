// jQuery-based modal and toggle logic for budget detail page
$(function () {
  // Show Add Expense modal (clear form)
  $('.add-expense-btn').on('click', function () {
    $('#expense-form')[0].reset();
    $('#expense_id').val('');
    $('#expenseModal').show();
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
    $('#expenseModal').show();
  });

  // Cancel Expense modal
  $('.expense-cancel-btn').on('click', function () {
    $('#expenseModal').hide();
  });

  // Show Income modal
  $('.edit-income-btn').on('click', function () {
    $('#incomeModal').show();
  });
  // Cancel Income modal
  $('.income-cancel-btn').on('click', function () {
    $('#incomeModal').hide();
  });

  // Toggle summary section
  $('.summary-toggle-btn').on('click', function () {
    var content = $('.summary-toggle-content');
    var text = $('.summary-toggle-text');
    content.toggle();
    text.text(content.is(':visible') ? 'Hide Summary' : 'Show Summary');
  });
  // Toggle category stats section
  $('.category-stats-toggle-btn').on('click', function () {
    var content = $('.category-stats-toggle-content');
    var text = $('.category-stats-toggle-text');
    content.toggle();
    text.text(content.is(':visible') ? 'Hide Category Stats' : 'Show Category Stats');
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
