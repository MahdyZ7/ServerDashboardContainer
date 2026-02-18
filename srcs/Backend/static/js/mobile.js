/**
 * Mobile Enhancements
 * Touch-optimized interactions and mobile-specific features
 */

(function() {
    'use strict';

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

    if (isMobile || isTouch) {
        initializeMobileEnhancements();
    }

    function initializeMobileEnhancements() {
        // Add mobile class to body
        document.body.classList.add('mobile-device');

        // Prevent double-tap zoom on interactive elements
        preventDoubleTapZoom();

        // Enhanced touch feedback
        addTouchFeedback();

        // Optimize scroll performance
        optimizeScrolling();

        // Handle orientation changes
        handleOrientationChange();

        // Fix viewport height for mobile browsers
        fixViewportHeight();
    }

    /**
     * Prevent double-tap zoom on buttons and interactive elements
     */
    function preventDoubleTapZoom() {
        document.addEventListener('touchend', function(e) {
            const target = e.target;
            if (target.tagName === 'BUTTON' ||
                target.classList.contains('clickable') ||
                target.closest('button') ||
                target.closest('.tab-button')) {
                e.preventDefault();
                target.click();
            }
        }, { passive: false });
    }

    /**
     * Add visual touch feedback
     */
    function addTouchFeedback() {
        document.addEventListener('touchstart', function(e) {
            const target = e.target;
            if (target.tagName === 'BUTTON' ||
                target.classList.contains('clickable') ||
                target.closest('button')) {
                target.style.opacity = '0.7';
                setTimeout(() => { target.style.opacity = '1'; }, 100);
            }
        }, { passive: true });
    }

    /**
     * Optimize scrolling performance
     */
    function optimizeScrolling() {
        const scrollables = document.querySelectorAll('.table-wrapper, .tab-panel');
        scrollables.forEach(element => {
            element.style.webkitOverflowScrolling = 'touch';
        });
    }

    /**
     * Handle orientation changes
     */
    function handleOrientationChange() {
        window.addEventListener('orientationchange', function() {
            setTimeout(() => {
                // Trigger resize event for charts and responsive elements
                window.dispatchEvent(new Event('resize'));
            }, 200);
        });
    }

    /**
     * Fix viewport height for mobile browsers (address bar issue)
     */
    function fixViewportHeight() {
        function setVHProperty() {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        }

        setVHProperty();
        window.addEventListener('resize', setVHProperty);
        window.addEventListener('orientationchange', setVHProperty);
    }

    /**
     * Smooth scroll for anchor links
     */
    function setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    setupSmoothScroll();
})();
