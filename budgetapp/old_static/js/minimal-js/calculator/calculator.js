let calcInput = '';
const calcDisplay = document.getElementById('calcDisplay');

function syncInput() {
  calcInput = calcDisplay.value;
}

function appendToCalc(val) {
  // Insert at cursor position or replace selection
  const start = calcDisplay.selectionStart;
  const end = calcDisplay.selectionEnd;
  const before = calcDisplay.value.slice(0, start);
  const after = calcDisplay.value.slice(end);
  calcDisplay.value = before + val + after;
  calcInput = calcDisplay.value;
  // Move cursor after inserted value
  const newPos = start + val.length;
  calcDisplay.setSelectionRange(newPos, newPos);
  calcDisplay.focus();
}

function clearCalc() {
  calcInput = '';
  calcDisplay.value = '';
  calcDisplay.focus();
}

function calculate() {
  try {
    // eslint-disable-next-line no-eval
    let result = eval(calcDisplay.value);
    calcDisplay.value = result;
    calcInput = result.toString();
    calcDisplay.focus();
    calcDisplay.setSelectionRange(calcDisplay.value.length, calcDisplay.value.length);
  } catch (e) {
    calcDisplay.value = 'Error';
    calcInput = '';
    setTimeout(clearCalc, 900);
  }
}

// Keep calcInput in sync with manual edits
calcDisplay.addEventListener('input', syncInput);

// Keyboard support
calcDisplay.addEventListener('keydown', function (e) {
  // Allow numbers, operators, parentheses, dot, Backspace, Delete, arrows, Home, End
  const allowed = /[0-9\+\-\*\/\.\(\)]/;
  if (
    e.key.length === 1 &&
    !allowed.test(e.key) &&
    e.key !== 'Enter' &&
    e.key !== '=' &&
    e.key !== 'Backspace' &&
    e.key !== 'Delete' &&
    e.key !== 'ArrowLeft' &&
    e.key !== 'ArrowRight' &&
    e.key !== 'Home' &&
    e.key !== 'End'
  ) {
    e.preventDefault();
  }
  // Enter or = triggers calculate
  if (e.key === 'Enter' || e.key === '=') {
    e.preventDefault();
    calculate();
  }
  // Esc closes modal
  if (e.key === 'Escape') {
    $('#calculatorModal').modal('hide');
  }
});

// --- Minimal UI Calculator Animations ---
$(document).on('show.bs.modal', '#calculatorModal', function () {
  const modal = document.querySelector('.minimal-calc-content');
  if (modal) {
    modal.style.opacity = 0;
    modal.style.transform = 'scale(0.92)';
    anime({
      targets: modal,
      opacity: [0, 1],
      scale: [0.92, 1],
      duration: 350,
      easing: 'easeOutCubic',
    });
  }
  // Focus input on open
  setTimeout(() => {
    document.getElementById('calcDisplay').focus();
  }, 200);
});

// Button hover pop effect
$(document).on('mouseenter focusin', '.minimal-calc-btn', function () {
  anime({
    targets: this,
    scale: 1.08,
    duration: 180,
    easing: 'easeOutCubic',
  });
});
$(document).on('mouseleave focusout', '.minimal-calc-btn', function () {
  anime({
    targets: this,
    scale: 1,
    duration: 180,
    easing: 'easeOutCubic',
  });
});

// Optional: clear on modal close
$(document).on('hidden.bs.modal', '#calculatorModal', function () {
  clearCalc();
});
