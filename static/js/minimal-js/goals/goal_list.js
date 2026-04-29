// Goals list — AJAX create / edit / delete (minimal theme)

$(document).ready(function () {
  var $dash = $('#goal-dashboard');
  var urlCreate = $dash.data('url-create');
  var urlUpdate = $dash.data('url-update');
  var urlDelete = $dash.data('url-delete');

  $('#createGoalForm').on('submit', function (e) {
    e.preventDefault();
    var $form = $(this);
    clearFormErrors($form);
    $.ajax({
      url: urlCreate,
      method: 'POST',
      data: $form.serialize(),
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          closeModalWithAnimation('#createGoalModal');
          $form[0].reset();
          clearFormErrors($form);
          location.reload();
        } else {
          showToast('Error', response.error, 'error');
        }
      },
      error: function (xhr) {
        var response = xhr.responseJSON;
        showToast('Error', response && response.error ? response.error : 'Request failed', 'error');
      },
    });
  });

  $(document).on('click', '.edit-goal-btn', function () {
    var $btn = $(this);
    $('#editGoalId').val($btn.data('goal-id'));
    $('#edit_name').val($btn.data('goal-name'));
    $('#edit_description').val($btn.data('goal-description'));
    $('#edit_target_amount').val($btn.data('goal-target'));
    $('#edit_current_amount').val($btn.data('goal-current'));
    $('#edit_start_date').val($btn.data('goal-start'));
    $('#edit_target_date').val($btn.data('goal-target-date'));
    $('#edit_category').val(String($btn.data('goal-category') || ''));
    $('#edit_is_active').prop('checked', String($btn.data('goal-active')) === '1');
    clearFormErrors($('#editGoalForm'));
    openModalWithAnimation('#editGoalModal');
  });

  $('#editGoalForm').on('submit', function (e) {
    e.preventDefault();
    var $form = $(this);
    clearFormErrors($form);
    $.ajax({
      url: urlUpdate,
      method: 'POST',
      data: $form.serialize(),
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          closeModalWithAnimation('#editGoalModal');
          location.reload();
        } else {
          showToast('Error', response.error, 'error');
        }
      },
      error: function (xhr) {
        var response = xhr.responseJSON;
        showToast('Error', response && response.error ? response.error : 'Request failed', 'error');
      },
    });
  });

  $(document).on('click', '.delete-goal-btn', function () {
    var goalId = $(this).data('goal-id');
    var goalName = $(this).data('goal-name') || 'this goal';
    $('#deleteGoalName').text(goalName);
    $('#confirmGoalDeleteBtn')
      .off('click')
      .on('click', function () {
        $.ajax({
          url: urlDelete,
          method: 'POST',
          data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').first().val(),
            goal_id: goalId,
          },
          success: function (response) {
            if (response.success) {
              showToast('Success', response.message, 'success');
              closeModalWithAnimation('#deleteGoalModal');
              var card = document.querySelector('[data-goal-id="' + goalId + '"]');
              if (card) {
                card.remove();
              }
              if (document.querySelectorAll('.goal-card').length === 0) {
                location.reload();
              }
            } else {
              showToast('Error', response.error, 'error');
            }
          },
          error: function (xhr) {
            var response = xhr.responseJSON;
            showToast('Error', response && response.error ? response.error : 'Request failed', 'error');
          },
        });
      });
    openModalWithAnimation('#deleteGoalModal');
  });
});
