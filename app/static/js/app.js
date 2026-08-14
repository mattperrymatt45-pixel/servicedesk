/**
 * Minimal Enterprise Application Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    if (window.lucide) {
        lucide.createIcons();
    }
});

function initDarkMode() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (!themeToggleBtn) return;

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

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    const colorClasses = {
        success: 'bg-emerald-700 text-white',
        error: 'bg-rose-700 text-white',
        warning: 'bg-amber-600 text-white',
        info: 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
    };

    toast.className = `flex items-center gap-2 px-3 py-2 rounded text-xs font-medium shadow-md ${colorClasses[type] || colorClasses.info} transition-all duration-200`;
    toast.innerHTML = `
        <span class="flex-1">${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-2 hover:opacity-75 focus:outline-none">✕</button>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 200);
    }, 4000);
}
