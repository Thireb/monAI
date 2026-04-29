// Goal detail — contributions and goal edit/delete

$(document).ready(function () {
  var $root = $('#goal-detail-root');
  if (!$root.length) {
    return;
  }

  var goalId = $root.data('goal-id');
  var urlContribCreate = $root.data('url-contrib-create');
  var urlContribUpdate = $root.data('url-contrib-update');
  var urlContribDelete = $root.data('url-contrib-delete');
  var urlGoalUpdate = $root.data('url-goal-update');
  var urlGoalDelete = $root.data('urlGoalDelete');
  var urlGoalList = $root.data('url-goal-list');

  function csrf() {
    return $('[name=csrfmiddlewaretoken]').first().val();
  }

  $('#addContributionForm').on('submit', function (e) {
    e.preventDefault();
    var $form = $(this);
    clearFormErrors($form);
    var data = $form.serialize();
    if (data.indexOf('goal_id') === -1) {
      data += '&goal_id=' + encodeURIComponent(goalId);
    }
    $.ajax({
      url: urlContribCreate,
      method: 'POST',
      data: data,
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          closeModalWithAnimation('#addContributionModal');
          $form[0].reset();
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

  $(document).on('click', '.edit-contrib-btn', function () {
    var cid = $(this).data('contrib-id');
    var $tr = $(this).closest('tr');
    $('#editContribId').val(cid);
    $('#edit_contrib_amount').val($tr.find('.contrib-amount').text().trim());
    $('#edit_contrib_date').val($.trim($tr.find('td').first().text()));
    $('#edit_contrib_source').val($tr.find('.contrib-source').text().trim());
    $('#edit_contrib_notes').val($tr.find('.contrib-notes').text().trim());
    clearFormErrors($('#editContributionForm'));
    openModalWithAnimation('#editContributionModal');
  });

  $('#editContributionForm').on('submit', function (e) {
    e.preventDefault();
    var $form = $(this);
    clearFormErrors($form);
    var data =
      $form.serialize() +
      '&goal_id=' +
      encodeURIComponent(goalId);
    $.ajax({
      url: urlContribUpdate,
      method: 'POST',
      data: data,
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          closeModalWithAnimation('#editContributionModal');
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

  $(document).on('click', '.delete-contrib-btn', function () {
    var cid = $(this).data('contrib-id');
    if (!window.confirm('Remove this contribution?')) {
      return;
    }
    $.ajax({
      url: urlContribDelete,
      method: 'POST',
      data: {
        csrfmiddlewaretoken: csrf(),
        contribution_id: cid,
      },
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
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

  $('#openEditGoalBtn').on('click', function () {
    clearFormErrors($('#editGoalDetailForm'));
    openModalWithAnimation('#editGoalModal');
  });

  $('#editGoalDetailForm').on('submit', function (e) {
    e.preventDefault();
    var $form = $(this);
    clearFormErrors($form);
    $.ajax({
      url: urlGoalUpdate,
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

  $('#openDeleteGoalBtn').on('click', function () {
    openModalWithAnimation('#deleteGoalModal');
  });

  $('#confirmDeleteGoalBtn').on('click', function () {
    $.ajax({
      url: urlGoalDelete,
      method: 'POST',
      data: {
        csrfmiddlewaretoken: csrf(),
        goal_id: goalId,
      },
      success: function (response) {
        if (response.success) {
          showToast('Success', response.message, 'success');
          window.location.href = urlGoalList;
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
});
