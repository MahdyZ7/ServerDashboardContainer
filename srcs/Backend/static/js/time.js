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
        const date = now.toLocaleDateString('en-GB', {
            weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'
        });
        const time = now.toLocaleTimeString('en-GB', { hour12: false });

        timeElement.textContent = `${date} · ${time}`;
    }

    // Initialize and update every second
    updateTime();
    setInterval(updateTime, 1000);
})();
