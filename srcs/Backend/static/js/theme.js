/**
 * Theme Management
 * Handles dark mode toggle with localStorage persistence
 */

(function() {
    'use strict';

    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;

    /**
     * Initialize theme from localStorage or system preference
     */
    function initializeTheme() {
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');

        if (savedTheme) {
            html.setAttribute('data-theme', savedTheme);
        } else {
            // Check system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const defaultTheme = prefersDark ? 'dark' : 'light';
            html.setAttribute('data-theme', defaultTheme);
            localStorage.setItem('theme', defaultTheme);
        }
    }

    /**
     * Toggle theme between light and dark
     */
    function toggleTheme() {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        // Add subtle animation to button
        if (themeToggle) {
            themeToggle.style.transform = 'scale(0.95)';
            setTimeout(() => {
                themeToggle.style.transform = 'scale(1)';
            }, 100);
        }

        // Dispatch custom event for other components to react
        window.dispatchEvent(new CustomEvent('themechange', {
            detail: { theme: newTheme }
        }));
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Button click
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);

            // Keyboard shortcut: Ctrl/Cmd + D
            document.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                    e.preventDefault();
                    toggleTheme();
                }
            });
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            // Only update if user hasn't explicitly set a preference
            if (!localStorage.getItem('theme-user-set')) {
                const newTheme = e.matches ? 'dark' : 'light';
                html.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
            }
        });
    }

    // Initialize on DOM content loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeTheme();
            setupEventListeners();
        });
    } else {
        initializeTheme();
        setupEventListeners();
    }
})();
