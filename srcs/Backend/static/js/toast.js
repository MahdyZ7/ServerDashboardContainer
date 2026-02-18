/**
 * Toast Notifications
 * Displays temporary notification messages
 */

(function() {
    'use strict';

    const toastContainer = document.getElementById('toast-container');

    /**
     * Create and show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type of toast: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in milliseconds (default: 3000)
     */
    function showToast(message, type = 'info', duration = 3000) {
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const icon = icons[type] || icons.info;

        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
            <button class="toast-close" aria-label="Close notification">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Add to container
        toastContainer.appendChild(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Setup close button
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => removeToast(toast));

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => removeToast(toast), duration);
        }
    }

    /**
     * Remove a toast notification
     * @param {HTMLElement} toast - The toast element to remove
     */
    function removeToast(toast) {
        toast.classList.remove('show');
        toast.classList.add('hide');

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    /**
     * Show success toast
     */
    function showSuccess(message, duration) {
        showToast(message, 'success', duration);
    }

    /**
     * Show error toast
     */
    function showError(message, duration) {
        showToast(message, 'error', duration);
    }

    /**
     * Show warning toast
     */
    function showWarning(message, duration) {
        showToast(message, 'warning', duration);
    }

    /**
     * Show info toast
     */
    function showInfo(message, duration) {
        showToast(message, 'info', duration);
    }

    // Expose to global scope
    window.Toast = {
        show: showToast,
        success: showSuccess,
        error: showError,
        warning: showWarning,
        info: showInfo
    };
})();
