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

  // Handle income form submission with AJAX
  $('#income-form').on('submit', function (e) {
    e.preventDefault();
    const form = $(this);
    const url = form.attr('action');

    $.ajax({
      url: url,
      type: 'POST',
      data: form.serialize(),
      success: function (response) {
        // Update the UI with new income values
        $('.income-value').text(response.currency + ' ' + response.income_display);
        $('.remaining-budget-value').text(
          response.currency + ' ' + response.remaining_budget_display
        );

        // Show success message
        showToast('Success', response.message, 'success');

        // Close the modal
        closeModalWithAnimation('#incomeModal');
      },
      error: function (xhr) {
        let errorMsg = 'An error occurred while updating income.';
        if (xhr.responseJSON && xhr.responseJSON.message) {
          errorMsg = xhr.responseJSON.message;
        }
        showToast('Error', errorMsg, 'error');
      },
    });
  });

  // Handle expense form submission with AJAX
  $('#expense-form').on('submit', function (e) {
    e.preventDefault();

    // Validate form
    let valid = true;
    const name = $(this).find('[name=name]');
    const amount = $(this).find('[name=amount]');

    if (!name.val().trim()) {
      name.addClass('is-invalid');
      valid = false;
    } else {
      name.removeClass('is-invalid');
    }

    if (!amount.val().trim() || isNaN(amount.val()) || Number(amount.val()) <= 0) {
      amount.addClass('is-invalid');
      valid = false;
    } else {
      amount.removeClass('is-invalid');
    }

    if (!valid) {
      return;
    }

    const form = $(this);
    const url = form.attr('action');

    $.ajax({
      url: url,
      type: 'POST',
      data: form.serialize(),
      success: function (response) {
        if (response.action === 'create') {
          // Add new row to the expenses table
          addExpenseRow(response.expense);
        } else if (response.action === 'update') {
          // Update existing row
          updateExpenseRow(response.expense);
        }

        // Update totals
        updateBudgetTotals();

        // Show success message
        showToast('Success', response.message, 'success');

        // Close the modal
        closeModalWithAnimation('#expenseModal');

        // Reset the form
        resetExpenseForm();
      },
      error: function (xhr) {
        let errorMsg = 'An error occurred while saving the expense.';
        if (xhr.responseJSON && xhr.responseJSON.message) {
          errorMsg = xhr.responseJSON.message;
        }
        showToast('Error', errorMsg, 'error');
      },
    });
  });

  // Store the expense ID to delete
  let expenseIdToDelete = null;

  // Open delete modal on delete icon click
  $(document).on('click', '.delete-expense-btn', function () {
    expenseIdToDelete = $(this).data('expense-id');
    openModalWithAnimation('#deleteExpenseModal');
  });

  // Handle cancel button in delete modal
  $(document).on('click', '.delete-cancel-btn', function () {
    closeModalWithAnimation('#deleteExpenseModal');
    expenseIdToDelete = null;
  });

  // Handle confirm delete button in delete modal
  $(document).on('click', '.delete-confirm-btn', function () {
    if (!expenseIdToDelete) return;
    const year = $('#js-budget-meta').data('year');
    const month = $('#js-budget-meta').data('month');

    $.ajax({
      url: `/minimal/budget/${year}/${month}/expense/delete/`,
      type: 'POST',
      data: {
        csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
        expense_id: expenseIdToDelete,
      },
      success: function (response) {
        const $row = $(`.expense-row[data-expense-id="${response.expense_id}"]`);
        anime({
          targets: $row[0],
          opacity: [1, 0],
          height: [$row.outerHeight(), 0],
          duration: 400,
          easing: 'easeInOutCubic',
          complete: function () {
            $row.remove();
          },
        });
        $('.total-expenses-value').text(
          $('.budget-currency').text() + ' ' + response.new_total_expenses_display
        );
        $('.remaining-budget-value').text(
          $('.budget-currency').text() + ' ' + response.new_remaining_budget_display
        );
        showToast('Success', response.message, 'success');
        updateCategoryStats();
        closeModalWithAnimation('#deleteExpenseModal');
        expenseIdToDelete = null;
      },
      error: function (xhr) {
        let errorMsg = 'An error occurred while deleting the expense.';
        if (xhr.responseJSON && xhr.responseJSON.message) {
          errorMsg = xhr.responseJSON.message;
        }
        showToast('Error', errorMsg, 'error');
        closeModalWithAnimation('#deleteExpenseModal');
        expenseIdToDelete = null;
      },
    });
  });

  // Reset expense form helper
  function resetExpenseForm() {
    $('#expense-form')[0].reset();
    $('#expense_id').val('');
  }

  // Helper function to add a new expense row to the table
  function addExpenseRow(expense) {
    const newRow = $('<tr>').addClass('expense-row').attr('data-expense-id', expense.id);

    // Add cells
    newRow.append($('<td>').text(expense.name));

    // Always format with currency to ensure consistency
    const currencyText = $('.budget-currency').text();
    newRow.append($('<td>').text(currencyText + ' ' + expense.amount_display));

    const categoryCell = $('<td>').attr('data-category-id', expense.category_id || '');
    if (expense.category_name) {
      categoryCell.text(expense.category_name);
    } else {
      categoryCell.append($('<span>').addClass('text-muted').text('Uncategorized'));
    }
    newRow.append(categoryCell);

    newRow.append($('<td>').text(expense.tag_display));

    const recurringCell = $('<td>');
    if (expense.is_recurring) {
      recurringCell.append($('<span>').addClass('badge bg-success').text('Yes'));
    } else {
      recurringCell.append($('<span>').addClass('badge bg-secondary').text('No'));
    }
    newRow.append(recurringCell);

    const subExpensesCell = $('<td>');
    if (expense.sub_expenses && expense.sub_expenses.length > 0) {
      const subList = $('<ul>').addClass('sub-expense-list');
      expense.sub_expenses.forEach(function (sub) {
        const subItem = $('<li>');
        subItem.append($('<span>').addClass('sub-expense-name').text(sub.name));
        subItem.append(' - ');
        const currencyText = $('.budget-currency').text();
        subItem.append(
          $('<span>')
            .addClass('sub-expense-amount')
            .text(currencyText + ' ' + sub.amount_display)
        );
        if (sub.is_return) {
          subItem.append($('<span>').addClass('badge bg-info').text('Return'));
        }
        subList.append(subItem);
      });
      subExpensesCell.append(subList);
    } else {
      subExpensesCell.append($('<span>').addClass('text-muted').text('—'));
    }
    newRow.append(subExpensesCell);

    // Add action buttons
    const actionsCell = $('<td>').addClass('expense-actions-cell');

    // Edit button
    const editBtn = $('<button>')
      .addClass('btn-icon edit-expense-btn minimal-tooltip-trigger')
      .attr({
        'aria-label': 'Edit',
        'data-tooltip': 'Edit',
        'data-expense-id': expense.id,
        'data-expense-name': expense.name,
        'data-expense-amount': expense.amount,
        'data-expense-category': expense.category_id || '',
        'data-expense-tag': expense.tag,
        'data-expense-recurring': expense.is_recurring,
      })
      .text('✏️');

    // Delete button
    const deleteBtn = $('<button>')
      .addClass('btn-icon btn-danger delete-expense-btn minimal-tooltip-trigger')
      .attr({
        'aria-label': 'Delete',
        'data-tooltip': 'Delete',
        'data-expense-id': expense.id,
      })
      .text('🗑️');

    actionsCell.append(editBtn, deleteBtn);
    newRow.append(actionsCell);

    // Add the new row to the table
    $('.wide-expense-table tbody').append(newRow);

    // Initialize tooltips on the new buttons
    if (window.initMinimalTooltips) {
      window.initMinimalTooltips('.minimal-tooltip-trigger');
    }

    // Rebind event handlers for the new buttons
    editBtn.on('click', function () {
      $('#expense_id').val($(this).data('expense-id'));
      $('#expense_name').val($(this).data('expense-name'));
      $('#expense_amount').val($(this).data('expense-amount'));
      $('#expense_category').val($(this).data('expense-category'));
      $('#expense_tag').val($(this).data('expense-tag'));
      $('#expense_recurring').prop(
        'checked',
        $(this).data('expense-recurring') === true || $(this).data('expense-recurring') === 'true'
      );
      openModalWithAnimation('#expenseModal');
    });

    deleteBtn.on('click', function () {
      if (confirm('Are you sure you want to delete this expense?')) {
        const expenseId = $(this).data('expense-id');
        const year = $('#js-budget-meta').data('year');
        const month = $('#js-budget-meta').data('month');

        $.ajax({
          url: `/minimal/budget/${year}/${month}/expense/delete/`,
          type: 'POST',
          data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
            expense_id: expenseId,
          },
          success: function (response) {
            // Remove the row from the table
            $(`.expense-row[data-expense-id="${response.expense_id}"]`).fadeOut(300, function () {
              $(this).remove();
            });

            // Update totals
            $('.total-expenses-value').text(
              $('.budget-currency').text() + ' ' + response.new_total_expenses_display
            );
            $('.remaining-budget-value').text(
              $('.budget-currency').text() + ' ' + response.new_remaining_budget_display
            );

            // Show success message
            showToast('Success', response.message, 'success');

            // Update category stats if needed
            updateCategoryStats();
          },
          error: function (xhr) {
            let errorMsg = 'An error occurred while deleting the expense.';
            if (xhr.responseJSON && xhr.responseJSON.message) {
              errorMsg = xhr.responseJSON.message;
            }
            showToast('Error', errorMsg, 'error');
          },
        });
      }
    });

    // Update totals
    updateBudgetTotals();
  }

  // Helper function to update an existing expense row
  function updateExpenseRow(expense) {
    const row = $(`.expense-row[data-expense-id="${expense.id}"]`);

    // Update cells
    row.find('td:nth-child(1)').text(expense.name);

    // Always format with currency to ensure consistency
    const currencyText = $('.budget-currency').text();
    row.find('td:nth-child(2)').text(currencyText + ' ' + expense.amount_display);

    const categoryCell = row.find('td:nth-child(3)');
    categoryCell.attr('data-category-id', expense.category_id || '');
    categoryCell.empty();
    if (expense.category_name) {
      categoryCell.text(expense.category_name);
    } else {
      categoryCell.append($('<span>').addClass('text-muted').text('Uncategorized'));
    }

    row.find('td:nth-child(4)').text(expense.tag_display);

    const recurringCell = row.find('td:nth-child(5)');
    recurringCell.empty();
    if (expense.is_recurring) {
      recurringCell.append($('<span>').addClass('badge bg-success').text('Yes'));
    } else {
      recurringCell.append($('<span>').addClass('badge bg-secondary').text('No'));
    }

    // Update data attributes on the edit button
    const editBtn = row.find('.edit-expense-btn');
    editBtn.attr({
      'data-expense-name': expense.name,
      'data-expense-amount': expense.amount,
      'data-expense-category': expense.category_id || '',
      'data-expense-tag': expense.tag,
      'data-expense-recurring': expense.is_recurring,
    });

    // Reinitialize tooltips on the updated row
    if (window.initMinimalTooltips) {
      window.initMinimalTooltips('.minimal-tooltip-trigger');
    }

    // Update totals
    updateBudgetTotals();
  }

  // Helper function to update budget totals
  // Helper function to format currency
  function formatCurrency(amount) {
    return amount.toLocaleString('en', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  function updateBudgetTotals() {
    // Calculate total expenses
    let totalExpenses = 0;
    $('.expense-row').each(function () {
      const amountText = $(this).find('td:nth-child(2)').text();
      const amount = parseFloat(amountText.replace(/[^0-9.-]+/g, ''));
      if (!isNaN(amount)) {
        totalExpenses += amount;
      }
    });

    // Get income
    const incomeText = $('.income-value').text();
    const income = parseFloat(incomeText.replace(/[^0-9.-]+/g, ''));

    // Calculate remaining budget
    const remainingBudget = income - totalExpenses;

    // Format numbers
    const currency = $('.budget-currency').text();

    // Update UI with client-side formatting
    $('.total-expenses-value').text(currency + ' ' + formatCurrency(totalExpenses));
    $('.remaining-budget-value').text(currency + ' ' + formatCurrency(remainingBudget));

    // Update category stats
    updateCategoryStats();
  }

  // Helper function to update category stats
  function updateCategoryStats() {
    const year = $('#js-budget-meta').data('year');
    const month = $('#js-budget-meta').data('month');

    $.ajax({
      url: `/minimal/budget/${year}/${month}/category-stats/`,
      type: 'GET',
      success: function (response) {
        $('.category-stats-toggle-content').html(response.html);
      },
    });
  }

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

  // Initialize tooltips for all elements on page load
  if (window.initMinimalTooltips) {
    window.initMinimalTooltips();
  }
});

// Add Select2 initialization
$(document).ready(function () {
  // For selects inside modals, set dropdownParent to the modal
  $('#expenseModal select.form-select, #expenseModal select.form-control').select2({
    dropdownParent: $('#expenseModal'),
    width: '100%',
    minimumResultsForSearch: Infinity, // Hide search box for short lists
  });
  $('#incomeModal select.form-select, #incomeModal select.form-control').select2({
    dropdownParent: $('#incomeModal'),
    width: '100%',
    minimumResultsForSearch: Infinity,
  });
  $('#deleteExpenseModal select.form-select, #deleteExpenseModal select.form-control').select2({
    dropdownParent: $('#deleteExpenseModal'),
    width: '100%',
    minimumResultsForSearch: Infinity,
  });
  // For selects outside modals
  $('select.form-select, select.form-control')
    .not('#expenseModal select, #incomeModal select, #deleteExpenseModal select')
    .select2({
      width: '100%',
      minimumResultsForSearch: Infinity,
    });
});
