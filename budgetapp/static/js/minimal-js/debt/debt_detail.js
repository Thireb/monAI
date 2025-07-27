// Debt Detail Page JavaScript
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

    $.ajax({
      url: '/minimal/debts/update/',
      method: 'POST',
      data: $(this).serialize(),
      success: function (response) {
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

    $.ajax({
      url: '/minimal/debts/borrow/',
      method: 'POST',
      data: $(this).serialize(),
      success: function (response) {
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
});
