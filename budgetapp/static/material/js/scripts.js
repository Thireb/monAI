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