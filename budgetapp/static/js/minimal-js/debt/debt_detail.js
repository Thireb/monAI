// Debt Detail Page JavaScript - Dynamic Updates with Animations
// Note: openModalWithAnimation and closeModalWithAnimation are defined in modal.js

// Toast notification function
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

// Animation functions
function animateValue(element, startValue, endValue, duration = 1000) {
  const start = performance.now();
  const change = endValue - startValue;

  function updateValue(currentTime) {
    const elapsed = currentTime - start;
    const progress = Math.min(elapsed / duration, 1);

    // Easing function (ease-out)
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const currentValue = startValue + change * easeOut;

    element.text(currentValue.toFixed(2));

    if (progress < 1) {
      requestAnimationFrame(updateValue);
    }
  }

  requestAnimationFrame(updateValue);
}

function animateProgressBar(progressBar, startWidth, endWidth, duration = 800) {
  const start = performance.now();
  const change = endWidth - startWidth;

  function updateProgress(currentTime) {
    const elapsed = currentTime - start;
    const progress = Math.min(elapsed / duration, 1);

    // Easing function (ease-out)
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const currentWidth = startWidth + change * easeOut;

    progressBar.css('width', currentWidth + '%');

    if (progress < 1) {
      requestAnimationFrame(updateProgress);
    }
  }

  requestAnimationFrame(updateProgress);
}

// Update summary cards with animation
function updateSummaryCards(debtData) {
  const cards = {
    'total-amount': debtData.total_amount,
    'borrowed-amount': debtData.borrowed_amount,
    'repaid-amount': debtData.repaid_amount,
    'remaining-amount': debtData.remaining_to_repay,
  };

  Object.keys(cards).forEach(cardId => {
    const card = $(`.summary-card[data-card="${cardId}"] .summary-value`);
    const currentValue = parseFloat(card.text().replace(/[^\d.-]/g, '') || 0);
    const newValue = parseFloat(cards[cardId] || 0);

    if (!isNaN(newValue) && currentValue !== newValue) {
      animateValue(card, currentValue, newValue);
    }
  });
}

// Update progress bars with animation
function updateProgressBars(debtData) {
  // Repayment progress
  const repaymentBar = $('.progress-card:first .progress-bar');
  const repaymentPercentage = parseFloat(debtData.repayment_progress_percentage || 0);
  const currentRepaymentWidth =
    (parseFloat(repaymentBar.css('width')) / parseFloat(repaymentBar.parent().css('width'))) * 100;

  if (!isNaN(repaymentPercentage) && Math.abs(currentRepaymentWidth - repaymentPercentage) > 1) {
    animateProgressBar(repaymentBar, currentRepaymentWidth, repaymentPercentage);
    $('.progress-card:first .progress-percentage').text(repaymentPercentage + '%');
    $('.progress-card:first .progress-description').text(
      `${debtData.repaid_amount || 0} of ${debtData.borrowed_amount || 0} repaid`
    );
  }

  // Borrowing progress
  const borrowingBar = $('.progress-card:last .progress-bar');
  const borrowingPercentage = parseFloat(debtData.progress_percentage || 0);
  const currentBorrowingWidth =
    (parseFloat(borrowingBar.css('width')) / parseFloat(borrowingBar.parent().css('width'))) * 100;

  if (!isNaN(borrowingPercentage) && Math.abs(currentBorrowingWidth - borrowingPercentage) > 1) {
    animateProgressBar(borrowingBar, currentBorrowingWidth, borrowingPercentage);
    $('.progress-card:last .progress-percentage').text(borrowingPercentage + '%');
    $('.progress-card:last .progress-description').text(
      `${debtData.borrowed_amount || 0} of ${debtData.total_amount || 0} borrowed`
    );
  }
}

// Update transaction table with animation
function updateTransactionTable(transactions) {
  const tbody = $('.wide-expense-table tbody');

  // Animate out existing rows
  tbody.find('tr').each(function (index) {
    const row = $(this);
    setTimeout(() => {
      row.fadeOut(300, function () {
        row.remove();
      });
    }, index * 50);
  });

  // After all rows are removed, add new ones
  setTimeout(
    () => {
      transactions.forEach((transaction, index) => {
        const newRow = createTransactionRow(transaction);
        tbody.append(newRow);

        // Animate in new row
        newRow.hide().fadeIn(300);
      });
    },
    transactions.length * 50 + 300
  );
}

function createTransactionRow(transaction) {
  return $(`
    <tr class="transaction-row" data-transaction-id="${transaction.id}">
      <td>${transaction.date}</td>
      <td><strong>${transaction.amount}</strong></td>
      <td>${transaction.notes || '-'}</td>
      <td><small class="text-muted">${transaction.created_at}</small></td>
      <td class="expense-actions-cell">
        <button class="btn-icon edit-transaction-btn minimal-tooltip-trigger" aria-label="Edit"
          data-tooltip="Edit"
          onclick="editTransaction(${transaction.id}, '${transaction.date_iso}', ${transaction.amount}, '${transaction.notes_escaped}')">
          ✏️
        </button>
        <button class="btn-icon btn-danger delete-transaction-btn minimal-tooltip-trigger"
          aria-label="Delete" data-tooltip="Delete"
          onclick="deleteTransaction(${transaction.id}, ${transaction.amount})">
          🗑️
        </button>
      </td>
    </tr>
  `);
}

// Loading state management
function showLoading(element) {
  element.addClass('loading');
  element.append('<div class="loading-spinner"></div>');
}

function hideLoading(element) {
  element.removeClass('loading');
  element.find('.loading-spinner').remove();
}

$(document).ready(function () {
  // Set default date for borrowing form
  $('#borrowingDate').val(new Date().toISOString().split('T')[0]);

  // Add data attributes to summary cards for easy targeting
  $('.summary-card').each(function (index) {
    const labels = ['total-amount', 'borrowed-amount', 'repaid-amount', 'remaining-amount'];
    $(this).attr('data-card', labels[index]);
  });

  // Edit Debt - Dynamic Update
  window.editDebt = function (debtId, name, description, totalAmount) {
    $('#editDebtId').val(debtId);
    $('#editDebtName').val(name);
    $('#editDebtDescription').val(description);
    $('#editDebtTotalAmount').val(totalAmount);
    openModalWithAnimation('#editDebtModal');
  };

  $('#editDebtForm').on('submit', function (e) {
    e.preventDefault();

    const form = $(this);
    const submitBtn = form.find('button[type="submit"]');

    // Prevent double submission
    if (submitBtn.hasClass('loading')) {
      return;
    }

    const originalText = submitBtn.text();

    showLoading(submitBtn);
    submitBtn.text('Updating...').prop('disabled', true);

    $.ajax({
      url: '/minimal/debts/update/',
      method: 'POST',
      data: form.serialize(),
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          closeModalWithAnimation('#editDebtModal');

          // Update page content dynamically
          updateSummaryCards(response.debt);
          updateProgressBars(response.debt);

          // Update debt name in header
          $('.debt-header h1').text(response.debt.name);
          $('.breadcrumb-item.active').text(response.debt.name);
        } else {
          showToast('Error', response.error, 'error');
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showToast('Error', response ? response.error : 'An error occurred', 'error');
      },
      complete: function () {
        hideLoading(submitBtn);
        submitBtn.text(originalText).prop('disabled', false);
      },
    });
  });

  // Delete Debt
  window.deleteDebt = function (debtId, debtName) {
    $('#debtName').text(debtName);
    $('#confirmDeleteBtn')
      .off('click')
      .on('click', function () {
        const btn = $(this);
        const originalText = btn.text();

        showLoading(btn);
        btn.text('Deleting...');

        $.ajax({
          url: '/minimal/debts/delete/',
          method: 'POST',
          data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
            debt_id: debtId,
          },
          success: function (response) {
            if (response.success) {
              showToast('Success', response.message, 'success');
              closeModalWithAnimation('#deleteModal');

              // Animate page transition
              $('body').fadeOut(500, function () {
                window.location.href = '/minimal/debts/';
              });
            } else {
              showToast('Error', response.error, 'error');
            }
          },
          error: function (xhr) {
            const response = xhr.responseJSON;
            showToast('Error', response ? response.error : 'An error occurred', 'error');
          },
          complete: function () {
            hideLoading(btn);
            btn.text(originalText);
          },
        });
      });
    openModalWithAnimation('#deleteModal');
  };

  // Add Borrowing - Dynamic Update
  $('#borrowingForm').on('submit', function (e) {
    e.preventDefault();

    const form = $(this);
    const submitBtn = form.find('button[type="submit"]');

    // Prevent double submission
    if (submitBtn.hasClass('loading')) {
      return;
    }

    // Client-side validation
    const amount = parseFloat($('#borrowingAmount').val());
    const currentBorrowed = parseFloat(
      $('.summary-card[data-card="borrowed-amount"] .summary-value')
        .text()
        .replace(/[^\d.-]/g, '') || 0
    );
    const totalAmount = parseFloat(
      $('.summary-card[data-card="total-amount"] .summary-value')
        .text()
        .replace(/[^\d.-]/g, '') || 0
    );

    if (currentBorrowed + amount > totalAmount) {
      showToast(
        'Error',
        `This borrowing would exceed the total debt amount of ${totalAmount}`,
        'error'
      );
      return;
    }

    const originalText = submitBtn.text();

    showLoading(submitBtn);
    submitBtn.text('Adding...').prop('disabled', true);

    $.ajax({
      url: '/minimal/debts/borrow/',
      method: 'POST',
      data: form.serialize(),
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          closeModalWithAnimation('#borrowModal');

          // Update page content dynamically
          updateSummaryCards(response.debt);
          updateProgressBars(response.debt);

          // Add new transaction to table with animation
          const newRow = createTransactionRow(response.transaction);
          $('.wide-expense-table tbody').prepend(newRow);
          newRow.hide().fadeIn(300);
        } else {
          showToast('Error', response.error, 'error');
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showToast('Error', response ? response.error : 'An error occurred', 'error');
      },
      complete: function () {
        hideLoading(submitBtn);
        submitBtn.text(originalText).prop('disabled', false);
      },
    });
  });

  // Reset date to today for borrowing form when modal closes
  $('#borrowModal').on('modal:closed', function () {
    $('#borrowingDate').val(new Date().toISOString().split('T')[0]);
  });

  // Real-time validation for borrowing form
  $('#borrowingAmount').on('input', function () {
    const amount = parseFloat($(this).val()) || 0;
    const currentBorrowed = parseFloat(
      $('.summary-card[data-card="borrowed-amount"] .summary-value')
        .text()
        .replace(/[^\d.-]/g, '') || 0
    );
    const totalAmount = parseFloat(
      $('.summary-card[data-card="total-amount"] .summary-value')
        .text()
        .replace(/[^\d.-]/g, '') || 0
    );
    const remaining = totalAmount - currentBorrowed;

    if (amount > remaining) {
      $(this).addClass('is-invalid');
      $(this)
        .next('.form-text')
        .text(`Maximum amount you can borrow: ${remaining.toFixed(2)}`)
        .addClass('text-danger');
    } else {
      $(this).removeClass('is-invalid');
      $(this).next('.form-text').text('Amount to borrow').removeClass('text-danger');
    }
  });

  // Edit Transaction - Dynamic Update
  window.editTransaction = function (transactionId, date, amount, notes) {
    $('#editTransactionId').val(transactionId);
    $('#editTransactionAmount').val(amount);
    $('#editTransactionDate').val(date);
    $('#editTransactionNotes').val(notes);
    openModalWithAnimation('#editTransactionModal');
  };

  $('#editTransactionForm').on('submit', function (e) {
    e.preventDefault();

    const form = $(this);
    const submitBtn = form.find('button[type="submit"]');

    // Prevent double submission
    if (submitBtn.hasClass('loading')) {
      return;
    }

    const originalText = submitBtn.text();

    showLoading(submitBtn);
    submitBtn.text('Updating...').prop('disabled', true);

    $.ajax({
      url: '/minimal/debts/transaction/update/',
      method: 'POST',
      data: form.serialize(),
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          closeModalWithAnimation('#editTransactionModal');

          // Update page content dynamically
          updateSummaryCards(response.debt);
          updateProgressBars(response.debt);

          // Update transaction row
          const row = $(`.transaction-row[data-transaction-id="${response.transaction.id}"]`);
          const newRow = createTransactionRow(response.transaction);
          row.fadeOut(200, function () {
            row.replaceWith(newRow);
            newRow.hide().fadeIn(200);
          });
        } else {
          showToast('Error', response.error, 'error');
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        showToast('Error', response ? response.error : 'An error occurred', 'error');
      },
      complete: function () {
        hideLoading(submitBtn);
        submitBtn.text(originalText).prop('disabled', false);
      },
    });
  });

  // Delete Transaction - Dynamic Update
  window.deleteTransaction = function (transactionId, amount) {
    $('#transactionAmount').text(amount);
    $('#confirmDeleteTransactionBtn')
      .off('click')
      .on('click', function () {
        const btn = $(this);
        const originalText = btn.text();

        showLoading(btn);
        btn.text('Deleting...');

        $.ajax({
          url: '/minimal/debts/transaction/delete/',
          method: 'POST',
          data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
            transaction_id: transactionId,
          },
          success: function (response) {
            if (response.success) {
              showToast('Success', response.message, 'success');
              closeModalWithAnimation('#deleteTransactionModal');

              // Update page content dynamically
              updateSummaryCards(response.debt);
              updateProgressBars(response.debt);

              // Remove transaction row with animation
              const row = $(`.transaction-row[data-transaction-id="${transactionId}"]`);
              row.fadeOut(300, function () {
                row.remove();
              });
            } else {
              showToast('Error', response.error, 'error');
            }
          },
          error: function (xhr) {
            const response = xhr.responseJSON;
            showToast('Error', response ? response.error : 'An error occurred', 'error');
          },
          complete: function () {
            hideLoading(btn);
            btn.text(originalText);
          },
        });
      });
    openModalWithAnimation('#deleteTransactionModal');
  };

  // Add cancel button handlers for custom modals
  $('.borrow-cancel-btn').on('click', function () {
    closeModalWithAnimation('#borrowModal');
  });

  $('.edit-debt-cancel-btn').on('click', function () {
    closeModalWithAnimation('#editDebtModal');
  });

  $('.delete-cancel-btn').on('click', function () {
    closeModalWithAnimation('#deleteModal');
  });

  $('.edit-transaction-cancel-btn').on('click', function () {
    closeModalWithAnimation('#editTransactionModal');
  });

  $('.delete-transaction-cancel-btn').on('click', function () {
    closeModalWithAnimation('#deleteTransactionModal');
  });

  // Close modals when clicking outside
  $('.modal-minimal').on('click', function (e) {
    if (e.target === this) {
      closeModalWithAnimation('#' + $(this).attr('id'));
    }
  });
});
