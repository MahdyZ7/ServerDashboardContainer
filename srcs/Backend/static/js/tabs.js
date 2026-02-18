/**
 * Tab Navigation
 * Handles tab switching with sliding indicator animation and keyboard navigation
 */

(function() {
    'use strict';

    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanels = document.querySelectorAll('.tab-panel');
    let indicator = null;

    /**
     * Create and insert the sliding indicator element
     */
    function createIndicator() {
        const nav = document.querySelector('.tabs-nav');
        if (!nav) return;

        indicator = document.createElement('div');
        indicator.className = 'tab-indicator';
        nav.appendChild(indicator);

        // Position on active tab
        const activeBtn = nav.querySelector('.tab-button.active');
        if (activeBtn) {
            positionIndicator(activeBtn);
        }
    }

    /**
     * Position the indicator under a given button
     */
    function positionIndicator(btn) {
        if (!indicator || !btn) return;

        const nav = btn.parentElement;
        const navRect = nav.getBoundingClientRect();
        const btnRect = btn.getBoundingClientRect();

        indicator.style.left = (btnRect.left - navRect.left) + 'px';
        indicator.style.width = btnRect.width + 'px';
    }

    /**
     * Switch to a specific tab
     */
    function switchTab(tabId) {
        tabButtons.forEach(btn => {
            const isActive = btn.dataset.tab === tabId;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-selected', isActive);

            if (isActive) {
                positionIndicator(btn);
            }
        });

        tabPanels.forEach(panel => {
            const isActive = panel.id === `${tabId}-panel`;
            panel.classList.toggle('active', isActive);

            if (isActive) {
                window.dispatchEvent(new CustomEvent('tabactivated', { detail: { tabId } }));

                const url = new URL(window.location);
                url.searchParams.set('tab', tabId);
                window.history.pushState({}, '', url);

                // Resize charts after tab becomes visible so they
                // can measure their container correctly
                requestAnimationFrame(() => {
                    if (window.ChartManager) {
                        panel.querySelectorAll('canvas').forEach(canvas => {
                            const chart = ChartManager.getChart(canvas.id);
                            if (chart) chart.resize();
                        });
                    }
                });
            }
        });
    }

    /**
     * Setup tab button event listeners
     */
    function setupTabButtons() {
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => switchTab(btn.dataset.tab));

            btn.addEventListener('keydown', (e) => {
                const currentIndex = Array.from(tabButtons).indexOf(btn);
                let newIndex;

                switch (e.key) {
                    case 'ArrowLeft':
                        e.preventDefault();
                        newIndex = currentIndex > 0 ? currentIndex - 1 : tabButtons.length - 1;
                        tabButtons[newIndex].focus();
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        newIndex = currentIndex < tabButtons.length - 1 ? currentIndex + 1 : 0;
                        tabButtons[newIndex].focus();
                        break;
                    case 'Home':
                        e.preventDefault();
                        tabButtons[0].focus();
                        break;
                    case 'End':
                        e.preventDefault();
                        tabButtons[tabButtons.length - 1].focus();
                        break;
                }
            });
        });
    }

    /**
     * Initialize tabs from URL parameter
     */
    function initializeFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        const tabId = urlParams.get('tab');
        if (tabId) switchTab(tabId);
    }

    /**
     * Handle browser back/forward
     */
    function handlePopState() {
        window.addEventListener('popstate', initializeFromUrl);
    }

    /**
     * Recalculate indicator on resize
     */
    function handleResize() {
        window.addEventListener('resize', () => {
            const activeBtn = document.querySelector('.tab-button.active');
            if (activeBtn) positionIndicator(activeBtn);
        });
    }

    // Initialize
    setupTabButtons();
    createIndicator();
    initializeFromUrl();
    handlePopState();
    handleResize();
})();
