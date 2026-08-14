/**
 * AI Service Desk Frontend Application JavaScript
 * Core utilities for UI feedback, dark mode, and toast notifications.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Dark Mode Toggle
    initDarkMode();
});

/**
 * Handles Dark Mode toggling and persistent user preference
 */
function initDarkMode() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (!themeToggleBtn) return;

    // Check saved theme or system preference
    if (localStorage.getItem('color-theme') === 'dark' || 
        (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }

    themeToggleBtn.addEventListener('click', () => {
        if (document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('color-theme', 'light');
        } else {
            document.documentElement.classList.add('dark');
            localStorage.setItem('color-theme', 'dark');
        }
    });
}

/**
 * Toast Notification Utility
 * @param {string} message 
 * @param {string} type - 'success', 'error', 'info', 'warning'
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    const colorClasses = {
        success: 'bg-emerald-600 text-white',
        error: 'bg-rose-600 text-white',
        warning: 'bg-amber-500 text-white',
        info: 'bg-indigo-600 text-white'
    };

    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.className = `flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${colorClasses[type] || colorClasses.info} animate-slide-in transition-all duration-300 transform`;
    toast.innerHTML = `
        <span class="text-base font-bold">${icons[type] || 'ℹ'}</span>
        <span class="flex-1">${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-2 hover:opacity-75 focus:outline-none">✕</button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('opacity-0', 'scale-95');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
