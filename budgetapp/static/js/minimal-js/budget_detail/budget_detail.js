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

  // Unified expense/sub-expense delete modal logic
  let deleteType = null;
  let expenseId = null;
  let subexpenseId = null;
  $(document).on('click', '.delete-expense-btn', function () {
    deleteType = $(this).data('type') || 'expense';
    expenseId = $(this).data('expense-id') || null;
    subexpenseId = $(this).data('subexpense-id') || null;
    $('#deleteExpenseModal').fadeIn(150);
  });
  $(document).on('click', '.delete-cancel-btn', function () {
    $('#deleteExpenseModal').fadeOut(150);
    deleteType = null;
    expenseId = null;
    subexpenseId = null;
  });
  $(document).on('click', '.delete-confirm-btn', function () {
    $('#deleteExpenseModal').fadeOut(150);
    const year = $('#js-budget-meta').data('year');
    const month = $('#js-budget-meta').data('month');
    let url, data;
    if (deleteType === 'subexpense') {
      url = `/minimal/budget/${year}/${month}/subexpense/delete/`;
      data = {
        csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
        subexpense_id: subexpenseId,
      };
    } else {
      url = `/minimal/budget/${year}/${month}/expense/delete/`;
      data = {
        csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
        expense_id: expenseId,
      };
    }
    $.ajax({
      url: url,
      type: 'POST',
      data: data,
      success: function (response) {
        if (deleteType === 'subexpense') {
          reloadSubExpenseList(expenseId);
          showUndoSnackbar('Sub-expense deleted.', function () {
            undoDeleteSubExpense();
          });
        } else {
          // Remove the expense row and sub-expense row from the table
          $(`.expense-row[data-expense-id="${expenseId}"]`).fadeOut(300, function () {
            $(this).remove();
          });
          $(`#subexpenses-${expenseId}`).fadeOut(300, function () {
            $(this).remove();
          });
          // Update totals
          if (response.new_total_expenses_display) {
            $('.total-expenses-value').text(
              $('.budget-currency').text() + ' ' + response.new_total_expenses_display
            );
          }
          if (response.new_remaining_budget_display) {
            $('.remaining-budget-value').text(
              $('.budget-currency').text() + ' ' + response.new_remaining_budget_display
            );
          }
          showToast('Success', response.message, 'success');
          updateCategoryStats();
        }
      },
      error: function (xhr) {
        let errorMsg = 'An error occurred while deleting.';
        if (xhr.responseJSON && xhr.responseJSON.message) {
          errorMsg = xhr.responseJSON.message;
        }
        showToast('Error', errorMsg, 'error');
      },
      complete: function () {
        deleteType = null;
        expenseId = null;
        subexpenseId = null;
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

    // Sub-Expenses cell (always clickable, even if 0)
    const subExpensesCell = $('<td>');
    const subTotal = expense.subexpense_total_display || '0.00';
    const subTotalSpan = $('<span>')
      .addClass('subexpense-total-toggle minimal-tooltip-trigger')
      .attr({
        'data-expense-id': expense.id,
        'data-tooltip': 'Click to reveal more',
        tabindex: 0,
      })
      .text(currencyText + ' ' + subTotal);
    subExpensesCell.append(subTotalSpan);
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

  // Expand/collapse sub-expense rows (improved)
  $(document).on('click keydown', '.subexpense-total-toggle', function (e) {
    if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
    const btn = $(this);
    const expenseId = btn.data('expense-id');
    const $row = $('#subexpenses-' + expenseId);
    const $content = $row.find('.subexpenses-content');
    if ($row.is(':visible')) {
      anime({
        targets: $content[0],
        opacity: [1, 0],
        translateY: [0, -16],
        height: [$content.outerHeight(), 0],
        duration: 350,
        easing: 'easeInQuad',
        complete: function () {
          $row.hide();
          $content.css({ height: '', opacity: '', transform: '' });
          btn.attr('data-tooltip', 'Click to reveal more');
          if (window.initMinimalTooltips) window.initMinimalTooltips('.minimal-tooltip-trigger');
        },
      });
    } else {
      $row.show();
      $content.css({ opacity: 0, height: 0, transform: 'translateY(-16px)' });
      anime({
        targets: $content[0],
        opacity: [0, 1],
        translateY: [-16, 0],
        height: [0, $content[0].scrollHeight],
        duration: 350,
        easing: 'easeOutQuad',
        complete: function () {
          $content.css({ height: '', transform: '' });
          btn.attr('data-tooltip', 'Click to close');
          if (window.initMinimalTooltips) window.initMinimalTooltips('.minimal-tooltip-trigger');
        },
      });
    }
  });

  // SUB-EXPENSES HANDLING (REFINED)
  // Show add sub-expense form
  $(document).on('click', '.add-subexpense-btn', function () {
    const $container = $(this).closest('.subexpenses-list');
    const $form = $container.find('.add-edit-subexpense-form');
    $form[0].reset();
    $form.find('[name=subexpense_id]').val('');
    $form.find('[name=name]').val('');
    $form.find('[name=amount]').val('');
    $form.find('[name=is_return]').prop('checked', false);
    $form.find('.form-error').hide();
    $form.addClass('show').show();
    $form.find('[name=name]').focus();
  });

  // Show edit sub-expense form
  $(document).on('click', '.edit-subexpense-btn', function () {
    const btn = $(this);
    const $container = btn.closest('.subexpenses-list');
    const $form = $container.find('.add-edit-subexpense-form');
    $form[0].reset();
    $form.find('[name=subexpense_id]').val(btn.data('subexpense-id'));
    $form.find('[name=name]').val(btn.data('subexpense-name'));
    $form.find('[name=amount]').val(btn.data('subexpense-amount'));
    $form.find('[name=is_return]').prop('checked', btn.data('subexpense-is-return'));
    $form.find('.form-error').hide();
    $form.addClass('show').show();
    $form.find('[name=name]').focus();
  });

  // Cancel add/edit sub-expense (Escape key or Cancel button)
  $(document).on('click', '.cancel-subexpense-btn', function () {
    $(this).closest('.add-edit-subexpense-form').removeClass('show').hide();
  });
  $(document).on('keydown', '.add-edit-subexpense-form', function (e) {
    if (e.key === 'Escape') {
      $(this).removeClass('show').hide();
    }
  });

  // Inline validation for sub-expense form
  function validateSubExpenseForm($form) {
    let valid = true;
    const name = $form.find('[name=name]');
    const amount = $form.find('[name=amount]');
    let errorMsg = '';
    if (!name.val().trim()) {
      name.addClass('is-invalid');
      errorMsg = 'Name is required.';
      valid = false;
    } else {
      name.removeClass('is-invalid');
    }
    if (!amount.val().trim() || isNaN(amount.val()) || Number(amount.val()) <= 0) {
      amount.addClass('is-invalid');
      errorMsg = 'Amount must be a positive number.';
      valid = false;
    } else {
      amount.removeClass('is-invalid');
    }
    if (!valid) {
      $form.find('.form-error').text(errorMsg).show();
    } else {
      $form.find('.form-error').hide();
    }
    return valid;
  }

  // Submit add/edit sub-expense form
  $(document).on('submit', '.add-edit-subexpense-form', function (e) {
    e.preventDefault();
    const $form = $(this);
    if (!validateSubExpenseForm($form)) return;
    const subexpenseId = $form.find('[name=subexpense_id]').val();
    const expenseId = $form.find('[name=expense_id]').val();
    const name = $form.find('[name=name]').val();
    const amount = $form.find('[name=amount]').val();
    const isReturn = $form.find('[name=is_return]').is(':checked');
    const year = $('#js-budget-meta').data('year');
    const month = $('#js-budget-meta').data('month');
    const url = subexpenseId
      ? `/minimal/budget/${year}/${month}/subexpense/update/`
      : `/minimal/budget/${year}/${month}/subexpense/create/`;
    const $saveBtn = $form.find('.submit-subexpense-btn');
    $saveBtn.prop('disabled', true).text('Saving...');
    $form.find('.form-error').hide();
    showSubExpenseLoading($form.closest('.subexpenses-list'));
    $.ajax({
      url: url,
      type: 'POST',
      data: {
        csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
        subexpense_id: subexpenseId,
        expense_id: expenseId,
        name: name,
        amount: amount,
        is_return: isReturn ? 'on' : '',
      },
      success: function (response) {
        reloadSubExpenseList(expenseId, function () {
          highlightLastSubExpense(expenseId);
        });
        showToast('Success', response.message, 'success');
        $form.removeClass('show').hide();
      },
      error: function (xhr) {
        let errorMsg = 'An error occurred while saving the sub-expense.';
        if (xhr.responseJSON && xhr.responseJSON.message) {
          errorMsg = xhr.responseJSON.message;
        }
        $form.find('.form-error').text(errorMsg).show();
        showToast('Error', errorMsg, 'error');
      },
      complete: function () {
        $saveBtn.prop('disabled', false).text('Save');
        hideSubExpenseLoading($form.closest('.subexpenses-list'));
      },
    });
  });

  // Show/hide loading spinner for sub-expense list
  function showSubExpenseLoading($container) {
    if ($container.find('.subexpense-loading').length === 0) {
      $container.append(
        '<div class="subexpense-loading" style="text-align:center; margin:8px 0;"><span class="spinner"></span></div>'
      );
    }
    $container.find('.subexpense-loading').show();
  }
  function hideSubExpenseLoading($container) {
    $container.find('.subexpense-loading').hide();
  }

  // Helper to reload sub-expense list via AJAX, with callback
  function reloadSubExpenseList(expenseId, callback) {
    const year = $('#js-budget-meta').data('year');
    const month = $('#js-budget-meta').data('month');
    $.get(`/minimal/budget/${year}/${month}/`, function (data) {
      // Find the new sub-expense HTML for this expense
      const parser = new DOMParser();
      const doc = parser.parseFromString(data, 'text/html');
      const newSubList = $(doc).find(`#subexpenses-${expenseId} .subexpenses-list`).parent().html();
      $(`#subexpenses-${expenseId} .subexpenses-list`).parent().html(newSubList);
      // Update sub-expense total in main table
      const newTotal = $(doc)
        .find(`.expense-row[data-expense-id="${expenseId}"] .subexpense-total-toggle`)
        .html();
      if (newTotal) {
        $(`.expense-row[data-expense-id="${expenseId}"] .subexpense-total-toggle`).html(newTotal);
      }
      if (callback) callback();
    });
  }

  // Highlight the last sub-expense row (after add/edit)
  function highlightLastSubExpense(expenseId) {
    const $rows = $(`#subexpenses-${expenseId} .subexpense-row`);
    if ($rows.length > 0) {
      const $last = $rows.last();
      $last.addClass('highlight');
      setTimeout(function () {
        $last.removeClass('highlight');
      }, 1200);
    }
  }

  // Undo snackbar
  function showUndoSnackbar(message, onUndo) {
    const $snackbar = $('#subexpense-undo-snackbar');
    $snackbar.html(`${message} <button class="btn-minimal">Undo</button>`).fadeIn(200);
    $snackbar.find('button').on('click', function () {
      $snackbar.fadeOut(200);
      if (onUndo) onUndo();
    });
    setTimeout(function () {
      $snackbar.fadeOut(200);
    }, 5000);
  }

  // Spinner CSS (inject if not present)
  if ($('.spinner').length === 0) {
    $('head').append(
      '<style>.spinner{display:inline-block;width:24px;height:24px;border:3px solid #e3f2fd;border-top:3px solid #1976d2;border-radius:50%;animation:spin 1s linear infinite;}@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}</style>'
    );
  }

  // Tooltips (re-init after AJAX)
  $(document).ajaxComplete(function () {
    if (window.initMinimalTooltips) window.initMinimalTooltips('.minimal-tooltip-trigger');
  });

  // Keyboard: Enter to save, Escape to cancel
  $(document).on('keydown', '.add-edit-subexpense-form input', function (e) {
    if (e.key === 'Enter') {
      $(this).closest('form').submit();
    }
    if (e.key === 'Escape') {
      $(this).closest('form').removeClass('show').hide();
    }
  });

  // Ensure modal-minimal uses flex display when shown (for vertical centering)
  $(document).on('show.bs.modal shown.bs.modal', '.modal-minimal', function () {
    $(this).css('display', 'flex');
  });
  // If using fadeIn/fadeOut, also force display:flex on fadeIn
  $(document).on('fadeIn', '.modal-minimal', function () {
    $(this).css('display', 'flex');
  });
  // When opening via fadeIn, always set display:flex
  const origFadeIn = $.fn.fadeIn;
  $.fn.fadeIn = function (speed, easing, callback) {
    this.filter('.modal-minimal').css('display', 'flex');
    return origFadeIn.apply(this, arguments);
  };
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
