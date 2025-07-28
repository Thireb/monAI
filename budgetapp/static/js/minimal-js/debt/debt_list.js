// Debt List Page JavaScript

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
  // Dynamic content update functions
  function updateDebtCard(debtData) {
    const debtCard = document.querySelector(`[data-debt-id="${debtData.id}"]`);
    if (debtCard) {
      // Update card content
      debtCard.querySelector('.debt-card-title').textContent = debtData.name;
      debtCard.querySelector('.debt-card-description').textContent = debtData.description || '';

      // Update stats
      const stats = debtCard.querySelectorAll('.debt-stat-value');
      if (stats.length >= 4) {
        stats[0].textContent = debtData.total_amount;
        stats[1].textContent = debtData.borrowed_amount;
        stats[2].textContent = debtData.repaid_amount;
        stats[3].textContent = debtData.remaining_to_repay;
      }

      // Update progress
      const progressFill = debtCard.querySelector('.debt-progress-fill');
      const progressText = debtCard.querySelector('.debt-progress-text');
      if (progressFill && progressText) {
        progressFill.style.width = `${debtData.repayment_progress_percentage}%`;
        progressText.textContent = `${debtData.repayment_progress_percentage}%`;
      }

      // Update delete button data attributes
      const deleteBtn = debtCard.querySelector('.delete-debt-btn');
      if (deleteBtn) {
        deleteBtn.setAttribute('data-debt-name', debtData.name);
      }
    }
  }

  function addDebtCard(debtData) {
    const debtGrid = document.querySelector('.debt-grid');
    if (!debtGrid) return;

    const debtCard = createDebtCardHTML(debtData);
    debtGrid.insertAdjacentHTML('afterbegin', debtCard);

    // Animate the new card
    const newCard = debtGrid.querySelector(`[data-debt-id="${debtData.id}"]`);
    if (newCard) {
      newCard.style.opacity = '0';
      newCard.style.transform = 'translateY(20px)';
      setTimeout(() => {
        newCard.style.transition = 'all 0.3s ease';
        newCard.style.opacity = '1';
        newCard.style.transform = 'translateY(0)';
      }, 100);
    }
  }

  function createDebtCardHTML(debtData) {
    return `
      <div class="debt-card debt-card-active" data-debt-id="${debtData.id}">
        <div class="debt-card-header">
          <h3 class="debt-card-title">${debtData.name}</h3>
          <p class="debt-card-description">${debtData.description || ''}</p>
        </div>

        <div class="debt-card-stats">
          <div class="debt-stat">
            <span class="debt-stat-label">Total:</span>
            <span class="debt-stat-value">${debtData.total_amount}</span>
          </div>
          <div class="debt-stat">
            <span class="debt-stat-label">Borrowed:</span>
            <span class="debt-stat-value">${debtData.borrowed_amount}</span>
          </div>
          <div class="debt-stat">
            <span class="debt-stat-label">Repaid:</span>
            <span class="debt-stat-value">${debtData.repaid_amount}</span>
          </div>
          <div class="debt-stat">
            <span class="debt-stat-label">Remaining:</span>
            <span class="debt-stat-value debt-stat-remaining">${debtData.remaining_to_repay}</span>
          </div>
        </div>

        <div class="debt-progress-section">
          <div class="debt-progress-label">Repayment Progress</div>
          <div class="debt-progress-bar">
            <div class="debt-progress-fill" style="width: ${debtData.repayment_progress_percentage}%"></div>
          </div>
          <div class="debt-progress-text">${debtData.repayment_progress_percentage}%</div>
        </div>

        <div class="debt-card-actions">
          <a href="/minimal/debts/${debtData.id}/" class="btn btn-minimal">
            <i class="fas fa-eye"></i> View
          </a>
          <button type="button" class="btn btn-minimal" onclick="editDebt(${debtData.id}, '${debtData.name.replace(/'/g, "\\'")}', '${(debtData.description || '').replace(/'/g, "\\'")}', ${debtData.total_amount})">
            <i class="fas fa-edit"></i> Edit
          </button>
          <button type="button" class="btn btn-minimal btn-danger delete-debt-btn" data-debt-id="${debtData.id}" data-debt-name="${debtData.name.replace(/"/g, '&quot;').replace(/'/g, '&#39;')}">
            <i class="fas fa-trash"></i> Delete
          </button>
        </div>
      </div>
    `;
  }

  function removeDebtCard(debtId) {
    const debtCard = document.querySelector(`[data-debt-id="${debtId}"]`);
    if (debtCard) {
      debtCard.style.transition = 'all 0.3s ease';
      debtCard.style.opacity = '0';
      debtCard.style.transform = 'translateY(-20px)';
      setTimeout(() => {
        debtCard.remove();
      }, 300);
    }
  }

  function hideEmptyState() {
    const emptyState = document.querySelector('.debt-empty-state');
    if (emptyState) {
      emptyState.style.transition = 'all 0.3s ease';
      emptyState.style.opacity = '0';
      setTimeout(() => {
        emptyState.remove();
      }, 300);
    }
  }

  // Create Debt - Dynamic Update
  $('#createDebtForm').on('submit', function (e) {
    e.preventDefault();

    $.ajax({
      url: '/minimal/debts/create/',
      method: 'POST',
      data: $(this).serialize(),
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          $('#createDebtModal').modal('hide');

          // Hide empty state if it exists
          hideEmptyState();

          // Add new debt card dynamically
          addDebtCard(response.debt);

          // Reset form
          $('#createDebtForm')[0].reset();
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

  // Edit Debt
  window.editDebt = function (debtId, name, description, totalAmount) {
    $('#editDebtId').val(debtId);
    $('#editDebtName').val(name);
    $('#editDebtDescription').val(description);
    $('#editDebtTotalAmount').val(totalAmount);
    $('#editDebtModal').modal('show');
  };

  // Edit Debt - Dynamic Update
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

          // Update debt card dynamically
          updateDebtCard(response.debt);
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

  // Delete Debt - Event Handler
  $(document).on('click', '.delete-debt-btn', function () {
    const debtId = $(this).data('debt-id');
    const debtName = $(this).data('debt-name');

    console.log('deleteDebt clicked with:', { debtId, debtName });
    console.log('Button element:', this);
    console.log('All data attributes:', $(this).data());

    // Ensure debtName is not empty and properly escape it for display
    const safeDebtName = debtName || 'this debt';
    const escapedDebtName = safeDebtName.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    console.log('Setting debt name to:', escapedDebtName);
    console.log('Target element:', $('#deleteDebtName'));

    $('#deleteDebtName').html(escapedDebtName);
    console.log('After setting HTML:', $('#deleteDebtName').html());
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

              // Remove debt card dynamically
              removeDebtCard(debtId);

              // Show empty state if no more debts
              const remainingCards = document.querySelectorAll('.debt-card');
              if (remainingCards.length === 0) {
                location.reload(); // Reload to show empty state
              }
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
  });

  // Modal form reset
  $('.modal').on('hidden.bs.modal', function () {
    $(this).find('form')[0].reset();
    $(this).find('.is-invalid').removeClass('is-invalid');
  });
});
