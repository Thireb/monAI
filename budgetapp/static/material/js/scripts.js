// Initialize Material Design
$(document).ready(function() {
    $('body').bootstrapMaterialDesign();
});

// Dark mode functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeText = document.getElementById('theme-text');
    const themeIcon = themeToggle.querySelector('i');
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeUI(savedTheme === 'dark');
    }
    
    // Theme toggle handler
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const isDark = currentTheme === 'dark';
        const theme = isDark ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateThemeUI(!isDark);
    });
    
    function updateThemeUI(isDark) {
        themeText.textContent = isDark ? 'Light Mode' : 'Dark Mode';
        themeIcon.textContent = isDark ? 'light_mode' : 'dark_mode';
    }
});

// Calculator functions
function appendToCalc(value) {
    const display = document.getElementById('calcDisplay');
    display.value += value;
}

function clearCalc() {
    document.getElementById('calcDisplay').value = '';
}

function calculate() {
    const display = document.getElementById('calcDisplay');
    try {
        display.value = eval(display.value);
    } catch (error) {
        display.value = 'Error';
        setTimeout(clearCalc, 1000);
    }
}

// Add keyboard support for calculator
document.addEventListener('keydown', function(event) {
    const calculatorModal = document.getElementById('calculatorModal');
    if (calculatorModal.classList.contains('show')) {
        const key = event.key;
        if (/[\d\+\-\*\/\(\)\.]/.test(key)) {
            event.preventDefault();
            appendToCalc(key);
        } else if (key === 'Enter') {
            event.preventDefault();
            calculate();
        } else if (key === 'Escape') {
            clearCalc();
        }
    }
}); 