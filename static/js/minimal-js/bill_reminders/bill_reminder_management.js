/* global showToast from utils.js */
$(function () {
  const saveUrl = window.BILL_REMINDER_SAVE_URL;
  const deleteUrl = window.BILL_REMINDER_DELETE_URL;

  function clearErrors() {
    $('.form-errors').hide().empty();
  }

  function showErrors(msg) {
    $('.form-errors').text(msg).show();
  }

  $('#bill-reminder-form').on('submit', function (e) {
    e.preventDefault();
    clearErrors();
    $.post(saveUrl, $(this).serialize())
      .done(function (res) {
        if (res.status === 'success') {
          showToast('Saved', res.message, 'success');
          window.location.reload();
        } else {
          showErrors(res.message || 'Could not save');
        }
      })
      .fail(function (xhr) {
        const r = xhr.responseJSON;
        showErrors(r && r.message ? r.message : 'Could not save');
      });
  });

  $('#br_reset_form').on('click', function () {
    $('#bill-reminder-form')[0].reset();
    $('#reminder_id').val('');
    $('#br_active').prop('checked', true);
    clearErrors();
  });

  $(document).on('click', '.br-edit-btn', function () {
    const b = $(this);
    $('#reminder_id').val(b.data('id'));
    $('#br_name').val(b.data('name'));
    $('#br_amount').val(b.data('amount'));
    $('#br_next').val(b.data('next'));
    $('#br_days').val(b.data('days'));
    $('#br_severity').val(b.data('severity'));
    $('#br_rec').val(b.data('recurrence'));
    $('#br_active').prop('checked', b.data('active') === true || b.data('active') === 'true');
    $('#br_category').val(b.data('category') ? String(b.data('category')) : '');
    $('#br_tag').val(b.data('tag') ? String(b.data('tag')) : '');
    $('#br_notes').val(b.data('notes') || '');
    clearErrors();
    $('html, body').animate({ scrollTop: $('#bill-reminder-form').offset().top - 80 }, 300);
  });

  $(document).on('click', '.br-delete-btn', function () {
    const id = $(this).data('id');
    const name = $(this).data('name');
    if (!window.confirm('Delete reminder "' + name + '"?')) {
      return;
    }
    $.post(deleteUrl, {
      csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
      reminder_id: id,
    })
      .done(function (res) {
        if (res.status === 'success') {
          showToast('Deleted', res.message, 'success');
          window.location.reload();
        }
      })
      .fail(function () {
        showToast('Error', 'Could not delete', 'error');
      });
  });
});
