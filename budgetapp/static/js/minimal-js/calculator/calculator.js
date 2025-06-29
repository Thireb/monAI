let calcInput = '';
function appendToCalc(val) {
  calcInput += val;
  document.getElementById('calcDisplay').value = calcInput;
}
function clearCalc() {
  calcInput = '';
  document.getElementById('calcDisplay').value = '';
}
function calculate() {
  try {
    // eslint-disable-next-line no-eval
    let result = eval(calcInput);
    document.getElementById('calcDisplay').value = result;
    calcInput = result.toString();
  } catch (e) {
    document.getElementById('calcDisplay').value = 'Error';
    calcInput = '';
  }
}
// Optional: clear on modal close
$(document).on('hidden.bs.modal', '#calculatorModal', function () {
  clearCalc();
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
