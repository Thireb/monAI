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
