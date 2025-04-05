// Budget Management JavaScript

class BudgetManager {
  constructor() {
    this.initializeComponents();
    this.attachEventListeners();
  }

  initializeComponents() {
    // Initialize Material Design components
    $('body').bootstrapMaterialDesign();

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(
      document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Initialize modals
    this.initializeModals();
  }

  initializeModals() {
    const incomeModalEl = document.getElementById('incomeModal');
    if (incomeModalEl) {
      this.incomeModal = new bootstrap.Modal(incomeModalEl, {
        keyboard: false,
        backdrop: 'static',
      });

      // Show modal if no income set
      if (incomeModalEl.dataset.showOnLoad === 'true') {
        this.incomeModal.show();
      }

      // Reset form on modal hide
      incomeModalEl.addEventListener('hidden.bs.modal', () => {
        document.querySelector('.income-form')?.reset();
      });
    }
  }

  attachEventListeners() {
    // Expense form handling
    this.setupExpenseForm();

    // Income modal handling
    this.setupIncomeModal();

    // Delete confirmation handling
    this.setupDeleteConfirmation();
  }

  setupExpenseForm() {
    const editButtons = document.querySelectorAll('.edit-expense');
    const expenseForm = document.getElementById('expense-form');
    const expenseFormTitle = document.getElementById('expense-form-title');
    const submitBtn = document.getElementById('expense-submit-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');

    if (!expenseForm) return;

    // Handle edit button clicks
    editButtons.forEach(button => {
      button.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        this.populateExpenseForm(button.dataset);
      });
    });

    // Handle cancel edit
    if (cancelEditBtn) {
      cancelEditBtn.addEventListener('click', () => {
        this.resetExpenseForm();
      });
    }
  }

  populateExpenseForm(expenseData) {
    const expenseForm = document.getElementById('expense-form');
    const expenseFormTitle = document.getElementById('expense-form-title');
    const submitBtn = document.getElementById('expense-submit-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');

    // Update form fields
    document.getElementById('expense_id').value = expenseData.expenseId || '';
    document.getElementById('expense_name').value = expenseData.expenseName || '';
    document.getElementById('expense_amount').value = expenseData.expenseAmount || '';
    document.getElementById('expense_category').value = expenseData.expenseCategory || '';
    document.getElementById('expense_recurring').checked = expenseData.expenseRecurring === 'true';

    // Update form appearance
    expenseFormTitle.textContent = 'Edit Expense';
    submitBtn.innerHTML = '<i class="material-icons align-middle">save</i> Update Expense';
    cancelEditBtn.classList.remove('d-none');

    // Scroll to form
    expenseForm.scrollIntoView({ behavior: 'smooth' });
  }

  resetExpenseForm() {
    const expenseForm = document.getElementById('expense-form');
    const expenseFormTitle = document.getElementById('expense-form-title');
    const submitBtn = document.getElementById('expense-submit-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');

    expenseForm.reset();
    document.getElementById('expense_id').value = '';
    expenseFormTitle.textContent = 'Add New Expense';
    submitBtn.innerHTML = '<i class="material-icons align-middle">add</i> Add Expense';
    cancelEditBtn.classList.add('d-none');
  }

  setupIncomeModal() {
    const updateIncomeBtn = document.querySelector('[data-bs-target="#incomeModal"]');
    if (updateIncomeBtn) {
      updateIncomeBtn.addEventListener('click', e => {
        e.preventDefault();
        this.incomeModal?.show();
      });
    }
  }

  async setupDeleteConfirmation() {
    document.querySelectorAll('.delete-form').forEach(form => {
      form.addEventListener('submit', async e => {
        e.preventDefault();
        const expenseName = form.dataset.expenseName;

        const result = await Swal.fire({
          title: 'Delete Expense?',
          text: `Are you sure you want to delete "${expenseName}"?`,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#dc3545',
          cancelButtonColor: '#6c757d',
          confirmButtonText: 'Yes, delete it!',
          cancelButtonText: 'No, keep it',
          reverseButtons: true,
        });

        if (result.isConfirmed) {
          form.submit();
        }
      });
    });
  }
}

// Initialize budget manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.budgetManager = new BudgetManager();
});
