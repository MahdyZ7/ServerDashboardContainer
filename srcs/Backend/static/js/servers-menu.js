/**
 * Servers menu (navigation, partials/nav.html)
 * Click or Enter/Space/ArrowDown opens it, arrows move, Escape or Tab closes it.
 * Status dots: ServersMenu.mark(latestMetrics), or fetched on first open.
 */

(function() {
    'use strict';

    // Offline after two missed collection cycles, as on the server API
    const STALE_MINUTES = 30;
    let marked = false;

    function mark(servers) {
        marked = true;
        const latest = Object.fromEntries((servers || []).map(s => [s.server_name, s]));
        document.querySelectorAll('.server-link[data-server]').forEach(link => {
            const m = latest[link.dataset.server];
            const online = !!m && (Date.now() - new Date(m.timestamp).getTime()) / 60000 <= STALE_MINUTES;
            link.classList.toggle('is-online', online);
            link.classList.toggle('is-offline', !online);
        });
    }

    function setup() {
        const button = document.getElementById('servers-menu-button');
        const menu = document.getElementById('servers-menu');
        if (!button || !menu) return;
        const items = () => Array.from(menu.querySelectorAll('.servers-menu-item'));

        function open(focusIndex) {
            if (!marked && window.API) {
                API.getLatestMetrics().then(r => r.success && mark(r.data))
                    .catch(err => console.warn('Server status unavailable:', err));
            }
            menu.classList.add('show');
            button.setAttribute('aria-expanded', 'true');
            if (focusIndex != null) items().at(focusIndex)?.focus();
        }

        function close(returnFocus) {
            if (!menu.classList.contains('show')) return;
            menu.classList.remove('show');
            button.setAttribute('aria-expanded', 'false');
            if (returnFocus) button.focus();
        }

        button.addEventListener('click', e => {
            e.stopPropagation();
            // detail 0 = keyboard activation: move focus into the list
            menu.classList.contains('show') ? close(false) : open(e.detail === 0 ? 0 : null);
        });
        button.addEventListener('keydown', e => {
            if (e.key === 'ArrowDown') { e.preventDefault(); open(0); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); open(-1); }
            else if (e.key === 'Escape') { close(true); }
        });
        menu.addEventListener('keydown', e => {
            const list = items();
            const i = list.indexOf(document.activeElement);
            if (e.key === 'ArrowDown') { e.preventDefault(); list[(i + 1) % list.length].focus(); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); list[(i - 1 + list.length) % list.length].focus(); }
            else if (e.key === 'Home') { e.preventDefault(); list[0].focus(); }
            else if (e.key === 'End') { e.preventDefault(); list[list.length - 1].focus(); }
            else if (e.key === 'Escape') { e.preventDefault(); close(true); }
            else if (e.key === 'Tab') { close(false); }
        });
        document.addEventListener('click', e => { if (!menu.contains(e.target)) close(false); });
    }

    window.ServersMenu = { mark };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
