/**
 * Time Display
 * Updates system time display every second
 */

(function() {
    'use strict';

    const timeElement = document.getElementById('current-time');

    /**
     * Update time display
     */
    function updateTime() {
        if (!timeElement) return;

        const now = new Date();
        const options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };

        timeElement.textContent = now.toLocaleString('en-US', options);
    }

    // Initialize and update every second
    updateTime();
    setInterval(updateTime, 1000);
})();
