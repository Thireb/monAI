// Debt Detail Page JavaScript

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

$(document).ready(function () {
  // Set default date for borrowing form
  $('#borrowingDate').val(new Date().toISOString().split('T')[0]);

  // Edit Debt
  window.editDebt = function (debtId, name, description, totalAmount) {
    $('#editDebtId').val(debtId);
    $('#editDebtName').val(name);
    $('#editDebtDescription').val(description);
    $('#editDebtTotalAmount').val(totalAmount);
    $('#editDebtModal').modal('show');
  };

  $('#editDebtForm').on('submit', function (e) {
    e.preventDefault();

    // Debug: Log form data
    console.log('Edit form data:', $(this).serialize());

    $.ajax({
      url: '/minimal/debts/update/',
      method: 'POST',
      data: $(this).serialize(),
      success: function (response) {
        console.log('Edit success response:', response);
        if (response.success) {
          showToast('Success', response.message, 'success');
          $('#editDebtModal').modal('hide');
          setTimeout(function () {
            location.reload();
          }, 1000);
        } else {
          showToast('Error', response.error, 'error');
        }
      },
      error: function (xhr) {
        console.log('Edit error response:', xhr.responseText);
        const response = xhr.responseJSON;
        showToast('Error', response ? response.error : 'An error occurred', 'error');
      },
    });
  });

  // Delete Debt
  window.deleteDebt = function (debtId, debtName) {
    $('#debtName').text(debtName);
    $('#confirmDeleteBtn')
      .off('click')
      .on('click', function () {
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
              $('#deleteModal').modal('hide');
              setTimeout(function () {
                window.location.href = '/minimal/debts/';
              }, 1000);
            } else {
              showToast('Error', response.error, 'error');
            }
          },
          error: function (xhr) {
            const response = xhr.responseJSON;
            showToast('Error', response ? response.error : 'An error occurred', 'error');
          },
        });
      });
    $('#deleteModal').modal('show');
  };

  // Add Borrowing
  $('#borrowingForm').on('submit', function (e) {
    e.preventDefault();

    // Debug: Log form data
    console.log('Borrowing form data:', $(this).serialize());

    $.ajax({
      url: '/minimal/debts/borrow/',
      method: 'POST',
      data: $(this).serialize(),
      success: function (response) {
        console.log('Borrowing success response:', response);
        if (response.success) {
          showToast('Success', response.message, 'success');
          $('#borrowModal').modal('hide');
          setTimeout(function () {
            location.reload();
          }, 1000);
        } else {
          showToast('Error', response.error, 'error');
        }
      },
      error: function (xhr) {
        console.log('Borrowing error response:', xhr.responseText);
        const response = xhr.responseJSON;
        showToast('Error', response ? response.error : 'An error occurred', 'error');
      },
    });
  });

  // Modal form reset
  $('.modal').on('hidden.bs.modal', function () {
    $(this).find('form')[0].reset();
    $(this).find('.is-invalid').removeClass('is-invalid');
    // Reset date to today for borrowing form
    if ($(this).attr('id') === 'borrowModal') {
      $('#borrowingDate').val(new Date().toISOString().split('T')[0]);
    }
  });

  // Edit Transaction
  window.editTransaction = function (transactionId, date, amount, notes) {
    $('#editTransactionId').val(transactionId);
    $('#editTransactionAmount').val(amount);
    $('#editTransactionDate').val(date);
    $('#editTransactionNotes').val(notes);
    $('#editTransactionModal').modal('show');
  };

  $('#editTransactionForm').on('submit', function (e) {
    e.preventDefault();

    // Debug: Log form data
    console.log('Edit transaction form data:', $(this).serialize());

    $.ajax({
      url: '/minimal/debts/transaction/update/',
      method: 'POST',
      data: $(this).serialize(),
      success: function (response) {
        console.log('Edit transaction success response:', response);
        if (response.success) {
          showToast('Success', response.message, 'success');
          $('#editTransactionModal').modal('hide');
          setTimeout(function () {
            location.reload();
          }, 1000);
        } else {
          showToast('Error', response.error, 'error');
        }
      },
      error: function (xhr) {
        console.log('Edit transaction error response:', xhr.responseText);
        const response = xhr.responseJSON;
        showToast('Error', response ? response.error : 'An error occurred', 'error');
      },
    });
  });

  // Delete Transaction
  window.deleteTransaction = function (transactionId, amount) {
    $('#transactionAmount').text(amount);
    $('#confirmDeleteTransactionBtn')
      .off('click')
      .on('click', function () {
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
              $('#deleteTransactionModal').modal('hide');
              setTimeout(function () {
                location.reload();
              }, 1000);
            } else {
              showToast('Error', response.error, 'error');
            }
          },
          error: function (xhr) {
            const response = xhr.responseJSON;
            showToast('Error', response ? response.error : 'An error occurred', 'error');
          },
        });
      });
    $('#deleteTransactionModal').modal('show');
  };
});
