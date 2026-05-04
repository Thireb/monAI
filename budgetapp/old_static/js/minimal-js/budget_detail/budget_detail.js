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

    // Handle category - set to empty string if null/undefined
    var categoryValue = btn.data('expense-category');
    $('#expense_category').val(categoryValue || '');

    // Handle tag - use tag_foreign_key_id for the new tag system
    var tagValue = btn.data('expense-tag');
    $('#expense_tag_foreign_key').val(tagValue || '');

    $('#expense_recurring').prop(
      'checked',
      btn.data('expense-recurring') === true || btn.data('expense-recurring') === 'true'
    );

    // Trigger Select2 to update its display for dropdowns
    $('#expense_category').trigger('change');
    $('#expense_tag_foreign_key').trigger('change');

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
    clearFormErrors(form);

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
        applyBudgetSummaryFromResponse(response, response.currency);

        // Show success message
        showToast('Success', response.message, 'success');

        // Close the modal
        closeModalWithAnimation('#incomeModal');
      },
      error: function (xhr) {
        var response = xhr.responseJSON;
        if (response && response.errors) {
          displayFormErrors(form, response.errors);
        } else {
          showToast('Error', response?.message || 'An error occurred while updating income.', 'error');
        }
      },
    });
  });

  // Handle expense form submission with AJAX
  $('#expense-form').on('submit', function (e) {
    e.preventDefault();
    const form = $(this);
    clearFormErrors(form);

    // Validate form
    let valid = true;
    const name = form.find('[name=name]');
    const amount = form.find('[name=amount]');

    if (!name.val().trim()) {
      name.addClass('is-invalid');
      name.siblings('.invalid-feedback').text('Name is required.').show();
      valid = false;
    }

    if (!amount.val().trim() || isNaN(amount.val()) || Number(amount.val()) <= 0) {
      amount.addClass('is-invalid');
      amount.siblings('.invalid-feedback').text('Amount must be a positive number.').show();
      valid = false;
    }

    if (!valid) {
      return;
    }

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
        var response = xhr.responseJSON;
        if (response && response.errors) {
          displayFormErrors(form, response.errors);
        } else {
          showToast('Error', response?.message || 'An error occurred while saving the expense.', 'error');
        }
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
    openModalWithAnimation('#deleteExpenseModal');
  });
  $(document).on('click', '.delete-cancel-btn', function () {
    closeModalWithAnimation('#deleteExpenseModal');
    deleteType = null;
    expenseId = null;
    subexpenseId = null;
  });
  $(document).on('click', '.delete-confirm-btn', function () {
    closeModalWithAnimation('#deleteExpenseModal');
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
          reloadSubExpenseList(expenseId, function () {
            updateBudgetTotals();
          });
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
          updateBudgetTotals();
          showToast('Success', response.message, 'success');
          updateCategoryStats();
          updateTagTotals(); // Update tag totals after expense deletion
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
    var $form = $('#expense-form');
    $form[0].reset();
    $('#expense_id').val('');
    clearFormErrors($form);
  }

  // Helper function to add a new expense row to the table
  function addExpenseRow(expense) {
    // Get the next original index for the new expense
    const existingRows = $('.wide-expense-table > tbody .expense-row');
    const nextIndex = existingRows.length;

    const newRow = $('<tr>')
      .addClass('expense-row')
      .attr('data-expense-id', expense.id)
      .attr('data-original-index', nextIndex);

    // Add cells
    const nameCell = $('<td>')
      .addClass('minimal-tooltip-trigger')
      .attr('data-tooltip', expense.name)
      .text(expense.name);
    newRow.append(nameCell);

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

    // Create tag cell
    const tagCell = $('<td>');
    if (expense.tag_foreign_key && expense.tag_foreign_key.name) {
      const tagSpan = $('<span>')
        .css({
          color: expense.tag_foreign_key.color || '#2196f3',
          fontWeight: '500',
          textTransform: 'capitalize',
        })
        .text(expense.tag_foreign_key.name.toLowerCase().replace(/\b\w/g, l => l.toUpperCase()));
      tagCell.append(tagSpan);
    } else {
      tagCell.append($('<span>').addClass('text-muted').text('No Tag'));
    }
    newRow.append(tagCell);

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

    // Add returns display if returns exist
    if (expense.returns && expense.returns > 0) {
      const returnsSpan = $('<span>')
        .attr('id', 'total-returns')
        .addClass('text-green')
        .attr('data-expense-id', expense.id)
        .css({
          color: '#2a9155 !important',
          'font-weight': '600',
          display: 'block',
          'margin-top': '4px',
        })
        .text('Returns: ' + currencyText + ' ' + expense.total_returns);
      subExpensesCell.append(returnsSpan);
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
        'data-expense-category': expense.category_id || null,
        'data-expense-tag': expense.tag_foreign_key_id || '',
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

    // Add the new row to the table (use > to target only the main table's tbody, not nested ones)
    $('.wide-expense-table > tbody').append(newRow);

    // Initialize tooltips on the new buttons
    if (window.initMinimalTooltips) {
      window.initMinimalTooltips('.minimal-tooltip-trigger');
    }

    // Rebind event handlers for the new buttons
    editBtn.on('click', function () {
      $('#expense_id').val($(this).data('expense-id'));
      $('#expense_name').val($(this).data('expense-name'));
      $('#expense_amount').val($(this).data('expense-amount'));

      // Handle category - set to empty string if null/undefined
      var categoryValue = $(this).data('expense-category');
      $('#expense_category').val(categoryValue || '');

      // Handle tag - use tag_foreign_key_id for the new tag system
      var tagValue = $(this).data('expense-tag');
      $('#expense_tag_foreign_key').val(tagValue || '');

      $('#expense_recurring').prop(
        'checked',
        $(this).data('expense-recurring') === true || $(this).data('expense-recurring') === 'true'
      );

      // Trigger Select2 to update its display for dropdowns
      $('#expense_category').trigger('change');
      $('#expense_tag_foreign_key').trigger('change');

      openModalWithAnimation('#expenseModal');
    });

    // Update totals
    updateBudgetTotals();
    updateTagTotals(); // Update tag totals after expense addition
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

    // Update tag cell
    const tagCell = row.find('td:nth-child(4)');
    tagCell.empty();
    if (expense.tag_foreign_key && expense.tag_foreign_key.name) {
      const tagSpan = $('<span>')
        .css({
          color: expense.tag_foreign_key.color || '#2196f3',
          fontWeight: '500',
          textTransform: 'capitalize',
        })
        .text(expense.tag_foreign_key.name.toLowerCase().replace(/\b\w/g, l => l.toUpperCase()));
      tagCell.append(tagSpan);
    } else {
      tagCell.append($('<span>').addClass('text-muted').text('No Tag'));
    }

    const recurringCell = row.find('td:nth-child(5)');
    recurringCell.empty();
    if (expense.is_recurring) {
      recurringCell.append($('<span>').addClass('badge bg-success').text('Yes'));
    } else {
      recurringCell.append($('<span>').addClass('badge bg-secondary').text('No'));
    }

    // Update sub-expenses cell and returns display
    const subExpensesCell = row.find('td:nth-child(6)');

    // Update sub-expense total
    const subTotal = expense.subexpense_total_display || '0.00';
    const subTotalSpan = subExpensesCell.find('.subexpense-total-toggle');
    if (subTotalSpan.length > 0) {
      subTotalSpan.text(currencyText + ' ' + subTotal);
    }

    // Update returns display
    const currentReturns = subExpensesCell.find('#total-returns');
    if (expense.returns && expense.returns > 0) {
      const returnsText = 'Returns: ' + currencyText + ' ' + expense.total_returns;
      if (currentReturns.length > 0) {
        currentReturns.text(returnsText);
      } else {
        const returnsSpan = $('<span>')
          .attr('id', 'total-returns')
          .addClass('text-green')
          .attr('data-expense-id', expense.id)
          .css({
            color: '#2a9155 !important',
            'font-weight': '600',
            display: 'block',
            'margin-top': '4px',
          })
          .text(returnsText);
        subExpensesCell.append(returnsSpan);
      }
    } else {
      currentReturns.remove();
    }

    // Update data attributes on the edit button
    const editBtn = row.find('.edit-expense-btn');
    editBtn.attr({
      'data-expense-name': expense.name,
      'data-expense-amount': expense.amount,
      'data-expense-category': expense.category_id || null,
      'data-expense-tag': expense.tag_foreign_key_id || '',
      'data-expense-recurring': expense.is_recurring,
    });

    // Reinitialize tooltips on the updated row
    if (window.initMinimalTooltips) {
      window.initMinimalTooltips('.minimal-tooltip-trigger');
    }

    // Update totals
    updateBudgetTotals();
    updateTagTotals(); // Update tag totals after expense update
  }

  function applyBudgetSummaryFromResponse(payload, currencyOverride) {
    if (!payload) {
      return;
    }
    const c = currencyOverride || $('.budget-currency').text();
    const gross =
      payload.gross_expenses_display || payload.new_gross_expenses_display;
    const ret = payload.total_returns_display || payload.new_total_returns_display;
    const net = payload.net_expenses_display || payload.new_net_expenses_display;
    const rem =
      payload.remaining_budget_display || payload.new_remaining_budget_display;
    if (gross) {
      $('.gross-expenses-value').text(c + ' ' + gross);
    }
    if (ret) {
      $('.total-returns-value').text(c + ' ' + ret);
    }
    if (net) {
      $('.net-expenses-value').text(c + ' ' + net);
    }
    if (rem) {
      $('.remaining-budget-value').text(c + ' ' + rem);
    }
  }

  // Helper function to update budget totals
  // NOTE: formatCurrency is provided by core/utils.js (global)

  function updateBudgetTotals() {
    // Instead of client-side calculation, reload the summary cards from server
    const year = $('#js-budget-meta').data('year');
    const month = $('#js-budget-meta').data('month');

    $.ajax({
      url: `/minimal/budget/${year}/${month}/summary-cards/`,
      type: 'GET',
      success: function (response) {
        // Update summary cards with server-calculated values
        $('.summary-cards').html(response.html);

        // Update category stats
        updateCategoryStats();
      },
      error: function () {
        // Fallback to client-side calculation if AJAX fails
        updateBudgetTotalsClientSide();
      },
    });
  }

  // Fallback client-side calculation (kept for backward compatibility)
  function updateBudgetTotalsClientSide() {
    // Calculate total expenses
    let totalExpenses = 0;
    $('.expense-row').each(function () {
      const amountText = $(this).find('td:nth-child(2)').text();
      // Better parsing that handles currency symbols and commas
      const amount = parseFloat(amountText.replace(/[^\d.-]/g, ''));
      if (!isNaN(amount)) {
        totalExpenses += amount;
      }
    });

    // Get income
    const incomeText = $('.income-value').text();
    const income = parseFloat(incomeText.replace(/[^\d.-]/g, ''));

    // Calculate remaining budget
    const remainingBudget = income - totalExpenses;

    // Format numbers
    const currency = $('.budget-currency').text();

    // Update UI with client-side formatting
    $('.total-expenses-value').text(currency + ' ' + formatCurrency(totalExpenses));
    $('.remaining-budget-value').text(currency + ' ' + formatCurrency(remainingBudget));
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

  // Helper function to update tag totals dynamically
  function updateTagTotals() {
    const year = $('#js-budget-meta').data('year');
    const month = $('#js-budget-meta').data('month');

    $.ajax({
      url: `/minimal/budget/${year}/${month}/tag-stats/`,
      type: 'GET',
      success: function (response) {
        // Replace the tag summary section with updated content
        $('.tag-summary-section').replaceWith(response.html);
      },
      error: function () {
        console.warn('Failed to load tag stats via AJAX, using fallback');
        // Fallback to client-side calculation if AJAX fails
        updateTagTotalsClientSide();
      },
    });
  }

  // Fallback function for client-side tag totals calculation
  function updateTagTotalsClientSide() {
    const currency = $('.budget-currency').text();
    const tagTotals = {};

    // Calculate tag totals from the current expense table
    $('.expense-row').each(function () {
      const amountText = $(this).find('td:nth-child(2)').text();
      const amount = parseFloat(amountText.replace(/[^0-9.-]+/g, ''));
      const tagCell = $(this).find('td:nth-child(4)');
      const tagText = tagCell.text().trim();

      if (!isNaN(amount) && tagText && tagText !== 'No Tag') {
        tagTotals[tagText] = (tagTotals[tagText] || 0) + amount;
      }
    });

    // Update tag summary cards
    $('.tag-summary-card').each(function () {
      const tagName = $(this).data('tag');
      const amount = tagTotals[tagName] || 0;

      if (amount > 0) {
        $(this)
          .find('.tag-value')
          .text(currency + ' ' + formatCurrency(amount));
        $(this).show();
      } else {
        $(this).hide();
      }
    });

    // Show/hide tag summary section based on whether any tags have amounts
    const hasVisibleTags = $('.tag-summary-card:visible').length > 0;
    if (hasVisibleTags) {
      $('.tag-summary-section').show();
    } else {
      $('.tag-summary-section').hide();
    }
  }

  // NOTE: showToast is provided by core/utils.js (global)

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

  // Initialize tag totals on page load
  updateTagTotals();

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
          animateNewSubexpenseRow(expenseId);
          highlightLastSubExpense(expenseId);
          if (response.summary) {
            updateSubexpenseSummary(expenseId, response.summary);
          }
          if (response.budget_summary) {
            applyBudgetSummaryFromResponse(response.budget_summary);
          }
        });

        // Update summary cards to reflect changes in expenses/returns
        updateBudgetTotals();

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

      // Update returns display in main table
      const returnsElement = $(doc).find(
        `.expense-row[data-expense-id="${expenseId}"] #total-returns`
      );
      const currentReturnsElement = $(
        `.expense-row[data-expense-id="${expenseId}"] #total-returns`
      );

      if (returnsElement.length > 0) {
        // Returns exist, update or add the element
        if (currentReturnsElement.length > 0) {
          currentReturnsElement.replaceWith(returnsElement);
        } else {
          // Add returns element after the sub-expense total
          $(`.expense-row[data-expense-id="${expenseId}"] .subexpense-total-toggle`).after(
            returnsElement
          );
        }
      } else {
        // No returns, remove the element if it exists
        currentReturnsElement.remove();
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

  // Add this function near other helpers
  function updateSubexpenseSummary(expenseId, summary) {
    const $returns = $(`#subexpenses-${expenseId} #total-returns[data-expense-id='${expenseId}']`);
    const $remaining = $(
      `#subexpenses-${expenseId} #remaining-amount[data-expense-id='${expenseId}']`
    );
    if (summary && $returns.length && $remaining.length) {
      $returns.text($('.budget-currency').text() + ' ' + summary.total_returns);
      $remaining.text(
        'Remaining: ' + $('.budget-currency').text() + ' ' + summary.remaining_amount
      );
    }
  }

  // Add this function near other helpers
  function animateNewSubexpenseRow(expenseId) {
    // Find the last subexpense row (the new one)
    const $rows = $(`#subexpenses-${expenseId} .subexpense-row`);
    if ($rows.length > 0) {
      const $last = $rows.last();
      $last.addClass('subexpense-row-animate');
      setTimeout(function () {
        $last.addClass('subexpense-row-animate-in');
      }, 10);
      setTimeout(function () {
        $last.removeClass('subexpense-row-animate subexpense-row-animate-in');
      }, 400);
    }
  }

  // Email PDF Functionality
  $('#email-pdf-btn').on('click', function () {
    const $btn = $(this);
    const url = $btn.data('url');

    // Prevent double-clicks
    if ($btn.hasClass('loading')) {
      return;
    }

    // Show loading state
    const originalText = $btn.find('.email-pdf-text').text();
    $btn.addClass('loading').prop('disabled', true);
    $btn.find('.email-pdf-text').text('⏳ Sending...');

    $.ajax({
      url: url,
      type: 'POST',
      data: {
        csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
      },
      success: function (response) {
        showToast('Success', response.message, 'success');

        // Animate success state
        $btn.find('.email-pdf-text').text('✅ Sent!');
        anime({
          targets: $btn[0],
          scale: [1, 1.1, 1],
          duration: 400,
          easing: 'easeOutElastic(1, .5)',
        });

        // Reset button after delay
        setTimeout(function () {
          $btn.removeClass('loading').prop('disabled', false);
          $btn.find('.email-pdf-text').text(originalText);
        }, 2000);
      },
      error: function (xhr) {
        let errorMsg = 'Failed to send email. Please try again.';
        if (xhr.responseJSON && xhr.responseJSON.message) {
          errorMsg = xhr.responseJSON.message;
        }
        showToast('Error', errorMsg, 'error');

        // Reset button
        $btn.removeClass('loading').prop('disabled', false);
        $btn.find('.email-pdf-text').text(originalText);
      },
    });
  });

  // Budget Delete Functionality
  $('#delete-budget-btn').on('click', function () {
    openModalWithAnimation('#deleteBudgetModal');
  });

  // Budget delete modal cancel and close buttons
  $('.budget-delete-cancel-btn').on('click', function () {
    closeModalWithAnimation('#deleteBudgetModal');
  });

  $('.budget-delete-close-btn').on('click', function () {
    closeModalWithAnimation('#deleteBudgetModal');
  });

  $('#confirm-delete-budget').on('click', function () {
    const year = $('#js-budget-meta').data('year');
    const month = $('#js-budget-meta').data('month');

    // Disable button and show loading state
    const $btn = $(this);
    const originalText = $btn.html();
    $btn.prop('disabled', true).html('<span class="spinner"></span> Deleting...');

    $.ajax({
      url: `/minimal/budget/${year}/${month}/delete/`,
      type: 'POST',
      data: {
        csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
      },
      success: function (response) {
        // Show success message
        showToast('Success', response.message, 'success');

        // Close modal
        closeModalWithAnimation('#deleteBudgetModal');

        // Redirect to home page after a short delay
        setTimeout(function () {
          window.location.href = $('#js-budget-meta').data('home-url');
        }, 1500);
      },
      error: function (xhr) {
        // Re-enable button
        $btn.prop('disabled', false).html(originalText);

        // Show error message
        let errorMsg = 'An error occurred while deleting the budget.';
        if (xhr.responseJSON && xhr.responseJSON.message) {
          errorMsg = xhr.responseJSON.message;
        }
        showToast('Error', errorMsg, 'error');
      },
    });
  });

  // ============================================
  // EXPENSE TABLE SORTING FUNCTIONALITY
  // ============================================

  // Sorting state
  let currentSortColumn = null;
  let currentSortDirection = null; // 'asc', 'desc', or null

  // Initialize original indices on page load for new rows without them
  function initializeOriginalIndices() {
    const $tbody = $('.wide-expense-table > tbody');
    let index = 0;
    $tbody.find('.expense-row').each(function () {
      if (!$(this).attr('data-original-index')) {
        $(this).attr('data-original-index', index);
      }
      const expenseId = $(this).data('expense-id');
      const $subRow = $(`#subexpenses-${expenseId}`);
      if ($subRow.length && !$subRow.attr('data-original-index')) {
        $subRow.attr('data-original-index', index);
      }
      index++;
    });
  }

  // Get sort value from a row based on column type
  function getSortValue(row, column) {
    const $row = $(row);
    switch (column) {
      case 'name':
        return $row.find('td:nth-child(1)').text().trim().toLowerCase();
      case 'amount':
        // Parse numeric value from currency text
        const amountText = $row.find('td:nth-child(2)').text();
        return parseFloat(amountText.replace(/[^\d.-]/g, '')) || 0;
      case 'category':
        const categoryText = $row.find('td:nth-child(3)').text().trim().toLowerCase();
        // Put "uncategorized" at the end when sorting
        return categoryText === 'uncategorized' ? 'zzz_uncategorized' : categoryText;
      case 'tag':
        const tagText = $row.find('td:nth-child(4)').text().trim().toLowerCase();
        // Put "no tag" at the end when sorting
        return tagText === 'no tag' ? 'zzz_no_tag' : tagText;
      case 'recurring':
        // "Yes" comes before "No" in ascending order
        const isRecurring = $row.find('td:nth-child(5)').text().trim().toLowerCase();
        return isRecurring === 'yes' ? 0 : 1;
      default:
        return 0;
    }
  }

  // Compare function for sorting
  function compareRows(a, b, column, direction) {
    const valA = getSortValue(a, column);
    const valB = getSortValue(b, column);

    let comparison = 0;
    if (typeof valA === 'string' && typeof valB === 'string') {
      comparison = valA.localeCompare(valB);
    } else {
      comparison = valA - valB;
    }

    return direction === 'desc' ? -comparison : comparison;
  }

  // Sort the expense table
  function sortExpenseTable(column, direction) {
    const $tbody = $('.wide-expense-table > tbody');

    // Get all expense rows (not subexpense rows)
    const $expenseRows = $tbody.find('.expense-row').toArray();

    // Sort the rows
    $expenseRows.sort((a, b) => compareRows(a, b, column, direction));

    // Animate and reorder rows
    const rowPairs = [];
    $expenseRows.forEach(row => {
      const $row = $(row);
      const expenseId = $row.data('expense-id');
      const $subRow = $(`#subexpenses-${expenseId}`);
      rowPairs.push({ expense: $row, subexpense: $subRow });
    });

    // Fade out, reorder, fade in with Anime.js
    anime({
      targets: '.expense-row',
      opacity: [1, 0.3],
      duration: 150,
      easing: 'easeOutQuad',
      complete: function () {
        // Detach and reappend in sorted order
        rowPairs.forEach(pair => {
          pair.expense.detach();
          if (pair.subexpense.length) {
            pair.subexpense.detach();
          }
        });

        rowPairs.forEach(pair => {
          $tbody.append(pair.expense);
          if (pair.subexpense.length) {
            $tbody.append(pair.subexpense);
          }
        });

        // Fade back in
        anime({
          targets: '.expense-row',
          opacity: [0.3, 1],
          duration: 200,
          easing: 'easeOutQuad',
        });
      },
    });
  }

  // Clear sorting and restore original order
  function clearSort() {
    const $tbody = $('.wide-expense-table > tbody');

    // Get all expense rows with their original indices
    const $expenseRows = $tbody.find('.expense-row').toArray();

    // Sort by original index
    $expenseRows.sort((a, b) => {
      const indexA = parseInt($(a).attr('data-original-index')) || 0;
      const indexB = parseInt($(b).attr('data-original-index')) || 0;
      return indexA - indexB;
    });

    // Collect row pairs
    const rowPairs = [];
    $expenseRows.forEach(row => {
      const $row = $(row);
      const expenseId = $row.data('expense-id');
      const $subRow = $(`#subexpenses-${expenseId}`);
      rowPairs.push({ expense: $row, subexpense: $subRow });
    });

    // Animate and reorder
    anime({
      targets: '.expense-row',
      opacity: [1, 0.3],
      duration: 150,
      easing: 'easeOutQuad',
      complete: function () {
        rowPairs.forEach(pair => {
          pair.expense.detach();
          if (pair.subexpense.length) {
            pair.subexpense.detach();
          }
        });

        rowPairs.forEach(pair => {
          $tbody.append(pair.expense);
          if (pair.subexpense.length) {
            $tbody.append(pair.subexpense);
          }
        });

        anime({
          targets: '.expense-row',
          opacity: [0.3, 1],
          duration: 200,
          easing: 'easeOutQuad',
        });
      },
    });

    // Reset state
    currentSortColumn = null;
    currentSortDirection = null;

    // Update UI
    updateSortIndicators();
    $('#clear-sort-btn').hide();
  }

  // Update sort indicators on headers
  function updateSortIndicators() {
    $('.sortable-header').each(function () {
      const $header = $(this);
      const column = $header.data('sort');
      const $indicator = $header.find('.sort-indicator');

      $header.removeClass('sorted-asc sorted-desc');

      if (column === currentSortColumn) {
        if (currentSortDirection === 'asc') {
          $indicator.text(' ↑');
          $header.addClass('sorted-asc');
        } else if (currentSortDirection === 'desc') {
          $indicator.text(' ↓');
          $header.addClass('sorted-desc');
        } else {
          $indicator.text('');
        }
      } else {
        $indicator.text('');
      }
    });
  }

  // Handle sortable header clicks
  $(document).on('click keydown', '.sortable-header', function (e) {
    // Handle keyboard navigation
    if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') {
      return;
    }
    if (e.type === 'keydown') {
      e.preventDefault();
    }

    const column = $(this).data('sort');

    // Cycle through: asc -> desc -> none
    if (currentSortColumn === column) {
      if (currentSortDirection === 'asc') {
        currentSortDirection = 'desc';
      } else if (currentSortDirection === 'desc') {
        // Clear sort
        currentSortColumn = null;
        currentSortDirection = null;
        clearSort();
        return;
      } else {
        currentSortDirection = 'asc';
      }
    } else {
      currentSortColumn = column;
      currentSortDirection = 'asc';
    }

    // Perform sort
    sortExpenseTable(currentSortColumn, currentSortDirection);

    // Update indicators
    updateSortIndicators();

    // Show/hide clear sort button
    if (currentSortColumn) {
      $('#clear-sort-btn').fadeIn(200);
    } else {
      $('#clear-sort-btn').fadeOut(200);
    }
  });

  // Handle clear sort button click
  $('#clear-sort-btn').on('click', function () {
    clearSort();
  });

  // Initialize original indices on page load
  initializeOriginalIndices();
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
