/**
 * Dashboard Main JavaScript
 * Handles data loading and rendering for all dashboard sections
 * Features: circular progress rings, animated number transitions, skeleton loading
 */

(function() {
    'use strict';

    let refreshInterval = null;
    let countdownInterval = null;
    let lastUpdatedTime = null;
    let nextRefreshTime = null;
    let analyticsControlsBound = false;

    /**
     * Initialize dashboard
     */
    function initializeDashboard() {
        setupAutoRefresh();
        setupRefreshButton();
        setupExportDropdown();
        bindUserTableControls();
        loadInitialData();
    }

    /**
     * Setup automatic refresh with countdown
     */
    function setupAutoRefresh() {
        const interval = DASHBOARD_CONFIG.refreshInterval;

        if (refreshInterval) clearInterval(refreshInterval);
        if (countdownInterval) clearInterval(countdownInterval);

        nextRefreshTime = Date.now() + interval;

        refreshInterval = setInterval(() => {
            refreshActiveTab();
            nextRefreshTime = Date.now() + interval;
        }, interval);

        countdownInterval = setInterval(updateCountdown, 1000);
    }

    /**
     * Update countdown display
     */
    function updateCountdown() {
        const el = document.getElementById('refresh-countdown');
        if (!el || !nextRefreshTime) return;

        const remaining = Math.max(0, nextRefreshTime - Date.now());
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        el.textContent = `Next refresh in ${minutes}:${String(seconds).padStart(2, '0')}`;
    }

    /**
     * Setup manual refresh button
     */
    function setupRefreshButton() {
        const refreshBtn = document.getElementById('refresh-button');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                refreshBtn.classList.add('spinning');
                refreshActiveTab().finally(() => {
                    setTimeout(() => refreshBtn.classList.remove('spinning'), 500);
                    nextRefreshTime = Date.now() + DASHBOARD_CONFIG.refreshInterval;
                });
            });
        }
    }

    /**
     * Setup export dropdown
     */
    function setupExportDropdown() {
        const exportBtn = document.getElementById('export-button');
        const exportMenu = document.getElementById('export-menu');
        if (!exportBtn || !exportMenu) return;

        exportBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            exportMenu.classList.toggle('show');
        });

        document.addEventListener('click', () => {
            exportMenu.classList.remove('show');
        });
    }

    /**
     * Load initial data based on active tab
     */
    function loadInitialData() {
        const activePanel = document.querySelector('.tab-panel.active');
        if (activePanel) {
            const tabId = activePanel.id.replace('-panel', '');
            loadTabData(tabId);
        }
    }

    /**
     * Refresh active tab
     */
    async function refreshActiveTab() {
        const activePanel = document.querySelector('.tab-panel.active');
        if (activePanel) {
            const tabId = activePanel.id.replace('-panel', '');
            await loadTabData(tabId);
        }
    }

    /**
     * Load data for specific tab
     */
    async function loadTabData(tabId) {
        try {
            switch (tabId) {
                case 'overview':
                    await loadServerGrid();
                    break;
                case 'servers':
                    await Promise.all([loadSystemOverview(), loadEnhancedServerCards()]);
                    break;
                case 'users':
                    await loadUserActivity();
                    break;
                case 'analytics':
                    await loadPerformanceAnalytics();
                    break;
                case 'network':
                    await loadNetworkMonitor();
                    break;
            }
            updateLastRefreshTime();
        } catch (error) {
            console.error('Error loading tab data:', error);
            Toast.error('Failed to load dashboard data');
        }
    }

    /**
     * Update last refresh time
     */
    function updateLastRefreshTime() {
        lastUpdatedTime = new Date();
        const element = document.getElementById('last-updated-time');
        if (element) {
            element.textContent = `Last updated: ${formatTimestamp(lastUpdatedTime)}`;
        }
    }

    function formatTimestamp(date) {
        return date.toLocaleString('en-US', {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit', second: '2-digit',
            hour12: false
        });
    }

    // Expose tab loaders globally
    window.loadServerGrid = loadServerGrid;
    window.loadSystemOverview = loadSystemOverview;
    window.loadEnhancedServerCards = loadEnhancedServerCards;
    window.loadUserActivity = loadUserActivity;
    window.loadPerformanceAnalytics = loadPerformanceAnalytics;
    window.loadNetworkMonitor = loadNetworkMonitor;

    /**
     * Map a utilisation percentage to a status tone (CSS custom property)
     */
    function getPercentageColor(value) {
        if (value > 90) return 'var(--ku-danger)';
        if (value > 70) return 'var(--ku-warning)';
        return 'var(--ku-primary)';
    }

    /**
     * Split a percentage into figure + unit markup: 42<small>%</small>
     */
    function pctFigure(value, digits = 0) {
        return `${value.toFixed(digits)}<small>%</small>`;
    }

    /**
     * Build a plain-English summary of fleet health for the overview lede
     */
    // Lede combines connectivity (from latest metrics) with the attention queue
    const ledeState = { total: null, reporting: null, issues: null };

    function renderOverviewLede(servers) {
        const stale = servers.filter(s => getServerStatus(s).class === 'status-offline').length;
        ledeState.total = servers.length;
        ledeState.reporting = servers.length - stale;
        updateLede();
    }

    function updateLede() {
        const lede = document.getElementById('overview-lede');
        if (!lede || ledeState.total === null) return;

        const { total, reporting, issues } = ledeState;
        let text = reporting === total
            ? `All <strong>${total}</strong> servers are reporting`
            : `<strong>${reporting} of ${total}</strong> servers are reporting; <strong class="lede-crit">${total - reporting}</strong> ${total - reporting === 1 ? 'has' : 'have'} gone quiet`;

        if (issues) {
            const parts = [];
            if (issues.critical) parts.push(`<strong class="lede-crit">${issues.critical} critical</strong>`);
            if (issues.warning) parts.push(`<strong class="lede-warn">${issues.warning} ${issues.warning === 1 ? 'warning' : 'warnings'}</strong>`);
            text += parts.length
                ? `, with ${parts.join(' and ')} below.`
                : ', and nothing needs attention.';
        } else {
            text += '.';
        }
        lede.innerHTML = text;
    }

    /**
     * Load server grid (overview tab)
     */
    async function loadServerGrid() {
        const container = document.getElementById('server-grid');
        const loading = document.getElementById('overview-loading');
        const empty = document.getElementById('overview-empty');

        if (!container) return;

        try {
            if (loading) loading.hidden = false;
            container.hidden = true;
            if (empty) empty.hidden = true;

            loadActionBand();
            const response = await API.getLatestMetrics();

            if (!response.success || !response.data || response.data.length === 0) {
                if (loading) loading.hidden = true;
                if (empty) empty.hidden = false;
                return;
            }

            renderOverviewLede(response.data);
            container.innerHTML = response.data.map((server, i) => renderSimplifiedServerCard(server, i)).join('');

            if (loading) loading.hidden = true;
            container.hidden = false;

        } catch (error) {
            console.error('Error loading server grid:', error);
            if (loading) loading.hidden = true;
            if (empty) {
                empty.hidden = false;
                empty.innerHTML = `
                    <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                    <h3>Failed to load data</h3>
                    <p>Could not connect to the server. Please try again.</p>
                    <button class="btn btn-primary" onclick="loadServerGrid()">
                        <i class="fas fa-sync-alt" aria-hidden="true"></i> Retry
                    </button>
                `;
            }
            Toast.error('Failed to load server metrics');
        }
    }

    /**
     * Load the overview action band: attention queue (admins) + placement (users)
     */
    async function loadActionBand() {
        await Promise.all([loadAttention(), loadPlacement()]);
    }

    async function loadAttention() {
        const list = document.getElementById('attention-list');
        const counts = document.getElementById('attention-counts');
        if (!list) return;

        try {
            const response = await API.getAttentionItems();
            if (!response.success) throw new Error(response.error || 'Bad response');
            const items = response.data || [];

            const tally = { critical: 0, warning: 0, info: 0 };
            items.forEach(i => { tally[i.severity] = (tally[i.severity] || 0) + 1; });
            ledeState.issues = tally;
            updateLede();
            if (counts) {
                counts.innerHTML = ['critical', 'warning', 'info']
                    .filter(k => tally[k])
                    .map(k => `<span class="count-chip sev-${k}">${tally[k]} ${k}</span>`)
                    .join('');
            }

            if (items.length === 0) {
                list.innerHTML = `
                    <li class="attention-clear">
                        <strong>Nothing needs attention.</strong>
                        Every reporting server is within its disk, memory and CPU thresholds.
                    </li>`;
                return;
            }

            list.innerHTML = items.map((item, i) => `
                <li class="attention-item sev-${escapeHtml(item.severity)}" style="--i:${i}">
                    <div class="attention-meta">
                        <span class="sev-label">${escapeHtml(item.severity)}</span>
                        <span class="attention-cat">${escapeHtml(item.category)}</span>
                    </div>
                    <div class="attention-body">
                        <p class="attention-title">${escapeHtml(item.title)}</p>
                        <p class="attention-detail">${escapeHtml(item.detail)}</p>
                        <p class="attention-action"><span>Next step</span>${escapeHtml(item.action)}</p>
                    </div>
                </li>`).join('');
        } catch (error) {
            console.error('Error loading attention items:', error);
            list.innerHTML = `
                <li class="attention-clear">
                    Could not load the attention queue.
                    <button class="btn btn-secondary" onclick="loadActionBand()">Retry</button>
                </li>`;
        }
    }

    async function loadPlacement() {
        const list = document.getElementById('placement-list');
        if (!list) return;

        try {
            const response = await API.getPlacement();
            if (!response.success) throw new Error(response.error || 'Bad response');
            const servers = response.data || [];

            const badge = {
                both: 'Best for CPU &amp; memory',
                cpu: 'Most free cores',
                memory: 'Most free memory'
            };

            list.innerHTML = servers.map((s, i) => `
                <li class="placement-item ${s.available ? '' : 'is-unavailable'}" style="--i:${i}">
                    <span class="placement-rank">${s.available ? String(i + 1).padStart(2, '0') : '—'}</span>
                    <div class="placement-main">
                        <div class="placement-name">
                            ${escapeHtml(s.server_name)}
                            ${s.best_for ? `<span class="placement-badge">${badge[s.best_for]}</span>` : ''}
                            ${s.available ? '' : '<span class="placement-badge is-off">Unavailable</span>'}
                        </div>
                        <div class="placement-facts">
                            <span><strong>${s.free_cores}</strong> of ${s.virtual_cpus} cores free</span>
                            <span><strong>${s.free_ram_gb ?? '?'} GB</strong> of ${s.ram_total_gb ?? '?'} GB RAM free</span>
                            <span>${s.sessions} session${s.sessions === 1 ? '' : 's'}</span>
                        </div>
                        <div class="placement-bar" aria-hidden="true"><i style="width:${s.score}%"></i></div>
                    </div>
                    <span class="placement-score" title="Headroom score">${s.available ? s.score : ''}</span>
                </li>`).join('');
        } catch (error) {
            console.error('Error loading placement:', error);
            list.innerHTML = `<li class="attention-clear">Could not rank servers right now.</li>`;
        }
    }

    /**
     * "Look up your usage" — one user's footprint across servers
     */
    let footprintBound = false;

    function setupFootprintLookup(users) {
        const form = document.getElementById('footprint-form');
        const input = document.getElementById('footprint-username');
        const datalist = document.getElementById('footprint-usernames');
        if (!form || !input) return;

        if (datalist) {
            const names = [...new Set(users.map(u => u.username).filter(Boolean))].sort();
            datalist.innerHTML = names.map(n => `<option value="${escapeHtml(n)}"></option>`).join('');
        }

        if (footprintBound) return;
        footprintBound = true;

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = input.value.trim();
            if (name) lookupFootprint(name);
        });

        // Deep link: /?tab=users&user=alice
        const initial = new URLSearchParams(window.location.search).get('user');
        if (initial) {
            input.value = initial;
            lookupFootprint(initial);
        }
    }

    async function lookupFootprint(username) {
        const result = document.getElementById('footprint-result');
        if (!result) return;
        result.innerHTML = '<div class="spinner" style="margin: 1rem 0;"></div>';

        const url = new URL(window.location);
        url.searchParams.set('user', username);
        window.history.replaceState({}, '', url);

        let response;
        try {
            response = await API.getUserFootprint(username);
        } catch (error) {
            // A 404 surfaces here as an HTTP error after retries
            result.innerHTML = `
                <p class="footprint-empty">No records found for <strong>${escapeHtml(username)}</strong>.
                Check the spelling, or the account may not have run anything on a monitored server.</p>`;
            return;
        }

        const d = response.data;
        const rows = d.servers.map(s => `
            <tr>
                <td class="cell-server">${escapeHtml(s.server_name)}</td>
                <td class="cell-numeric">${(s.disk ?? 0).toFixed(1)} GB</td>
                <td class="cell-numeric">${s.process_count ?? 0}</td>
                <td class="cell-truncate" title="${escapeHtml(s.top_process || '')}">${escapeHtml(s.top_process || '—')}</td>
                <td class="cell-numeric">${(s.mem ?? 0).toFixed(1)}%</td>
                <td class="cell-muted">${formatUserTimestamp(s.last_login)}</td>
                <td class="cell-muted">${formatUserTimestamp(s.timestamp)}</td>
            </tr>`).join('');

        result.innerHTML = `
            <div class="footprint-card">
                <div class="footprint-summary">
                    <div class="fig"><span class="fig-value">${escapeHtml(d.username)}</span><span class="fig-label">${escapeHtml(d.full_name || 'Account')}</span></div>
                    <div class="fig"><span class="fig-value">${d.servers.length}</span><span class="fig-label">Servers used</span></div>
                    <div class="fig"><span class="fig-value">${d.total_disk_gb}<small> GB</small></span><span class="fig-label">Disk across servers</span></div>
                    <div class="fig"><span class="fig-value">${d.total_processes}</span><span class="fig-label">Processes</span></div>
                </div>
                <div class="table-wrapper">
                    <table class="data-table">
                        <thead><tr>
                            <th scope="col">Server</th>
                            <th scope="col" class="col-numeric">Disk</th>
                            <th scope="col" class="col-numeric">Procs</th>
                            <th scope="col">Top process</th>
                            <th scope="col" class="col-numeric">Memory</th>
                            <th scope="col">Last login</th>
                            <th scope="col">Recorded</th>
                        </tr></thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
                <p class="action-note">Disk is measured once a day; "Recorded" is when this account was last observed on that server.</p>
                ${d.licenses && d.licenses.length ? `
                <div class="table-wrapper">
                    <table class="data-table">
                        <thead><tr>
                            <th scope="col">License held</th>
                            <th scope="col">Vendor</th>
                            <th scope="col">From</th>
                            <th scope="col">Held for</th>
                        </tr></thead>
                        <tbody>${d.licenses.map(l => `
                            <tr>
                                <td><strong>${escapeHtml(l.feature)}</strong></td>
                                <td>${escapeHtml(l.vendor)}</td>
                                <td class="cell-server">${escapeHtml(l.server_name || l.client_host || '—')}${l.display ? ` <span class="cell-muted">${escapeHtml(l.display)}</span>` : ''}</td>
                                <td class="cell-muted">${escapeHtml(l.held || l.start_raw || '—')}</td>
                            </tr>`).join('')}
                        </tbody>
                    </table>
                </div>
                <p class="action-note">Exit tools you are not using to release their licenses for others.</p>` : ''}
            </div>`;
    }

    window.loadActionBand = loadActionBand;

    /**
     * Format bytes into human-readable string (KB, MB, GB, TB)
     */
    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const b = parseInt(bytes);
        if (b < 1024) return b + ' B';
        if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
        if (b < 1073741824) return (b / 1048576).toFixed(1) + ' MB';
        if (b < 1099511627776) return (b / 1073741824).toFixed(2) + ' GB';
        return (b / 1099511627776).toFixed(2) + ' TB';
    }

    /**
     * Build a gauge row: label + figure, hairline track with threshold ticks
     */
    function gaugeBar(label, valueHtml, pct, color) {
        const clampedPct = Math.min(100, Math.max(0, pct));
        return `
            <div class="gauge-row">
                <span class="gauge-label">${label}</span>
                <span class="gauge-value">${valueHtml}</span>
                <div class="gauge-track" role="meter" aria-label="${label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${clampedPct.toFixed(0)}">
                    <div class="gauge-fill" style="width:${clampedPct}%;background:${color};"></div>
                </div>
            </div>`;
    }

    /**
     * Render overview entry for one server
     */
    function renderSimplifiedServerCard(server, index = 0) {
        const cpuLoad = parseFloat(server.cpu_load_5min || 0);
        const cpuUsage = server.cpu_usage_percent != null ? parseFloat(server.cpu_usage_percent) : null;
        const ramUsage = parseFloat(server.ram_percentage || 0);
        const diskUsage = parseFloat(server.disk_percentage || 0);
        const swapPerc = parseFloat(server.swap_percentage || 0);

        const cpuPct = cpuUsage !== null ? cpuUsage : Math.min(cpuLoad * 10, 100);
        const cpuDisplay = cpuUsage !== null ? pctFigure(cpuUsage, 1) : cpuLoad.toFixed(2);
        const cpuLabel = cpuUsage !== null ? 'CPU' : 'Load (5m)';

        const status = getServerStatus(server);
        const hasNet = server.net_rx_bytes > 0 || server.net_tx_bytes > 0;

        return `
            <article class="sc-overview ${status.class}" style="--i:${index}">
                <header class="sc-head">
                    <span class="sc-index">${String(index + 1).padStart(2, '0')}</span>
                    <h3 class="sc-name" title="${escapeHtml(server.server_name)}">${escapeHtml(server.server_name)}</h3>
                    <span class="sc-badge ${status.class}"><span class="sc-status-dot"></span>${status.label}</span>
                </header>
                <div class="sc-gauges">
                    ${gaugeBar(cpuLabel, cpuDisplay, cpuPct, getPercentageColor(cpuPct))}
                    ${gaugeBar('Memory', pctFigure(ramUsage), ramUsage, getPercentageColor(ramUsage))}
                    ${gaugeBar('Disk', pctFigure(diskUsage), diskUsage, getPercentageColor(diskUsage))}
                    ${swapPerc > 0 ? gaugeBar('Swap', pctFigure(swapPerc), swapPerc, getPercentageColor(swapPerc)) : ''}
                </div>
                <footer class="sc-footer">
                    <span class="sc-pill"><strong>${server.logged_users || 0}</strong> users</span>
                    <span class="sc-pill"><strong>${server.tcp_connections || 0}</strong> TCP</span>
                    ${hasNet ? `
                    <span class="sc-pill" title="Received (cumulative)"><i class="fas fa-arrow-down" aria-hidden="true"></i><strong>${formatBytes(server.net_rx_bytes)}</strong></span>
                    <span class="sc-pill" title="Transmitted (cumulative)"><i class="fas fa-arrow-up" aria-hidden="true"></i><strong>${formatBytes(server.net_tx_bytes)}</strong></span>` : ''}
                </footer>
            </article>
        `;
    }

    /**
     * Render a server specification sheet (Servers tab)
     */
    function renderDetailedServerCard(server, index = 0) {
        const cpuLoad = parseFloat(server.cpu_load_5min || 0);
        const cpuUsage = server.cpu_usage_percent != null ? parseFloat(server.cpu_usage_percent) : null;
        const ramUsage = parseFloat(server.ram_percentage || 0);
        const diskUsage = parseFloat(server.disk_percentage || 0);
        const swapPerc = parseFloat(server.swap_percentage || 0);
        const swapUsedMb = parseInt(server.swap_used_mb || 0);
        const swapTotalMb = parseInt(server.swap_total_mb || 0);

        const cpuPct = cpuUsage !== null ? cpuUsage : Math.min(cpuLoad * 10, 100);
        const cpuFigure = cpuUsage !== null ? pctFigure(cpuUsage, 1) : cpuLoad.toFixed(2);
        const cpuLabel = cpuUsage !== null ? 'CPU' : 'CPU load';

        const status = getServerStatus(server);
        const performance = getPerformanceRating(cpuPct, ramUsage, diskUsage);

        function fig(label, valueHtml, pct) {
            const p = Math.min(100, Math.max(0, pct));
            return `
                <div class="fig">
                    <span class="fig-value">${valueHtml}</span>
                    <div class="fig-bar"><i style="width:${p}%;background:${getPercentageColor(p)}"></i></div>
                    <span class="fig-label">${label}</span>
                </div>`;
        }

        function infoRow(label, value) {
            return `
                <div class="server-info-row">
                    <span class="server-info-label">${label}</span>
                    <span class="server-info-value">${value}</span>
                </div>`;
        }

        return `
            <article class="server-card ${status.class}" style="--i:${index}">
                <header class="server-card-header">
                    <div>
                        <p class="kicker">Server ${String(index + 1).padStart(2, '0')}</p>
                        <h3>${escapeHtml(server.server_name)}</h3>
                    </div>
                    <span class="status-badge ${status.class}">
                        <span class="status-dot"></span>
                        ${status.label}
                    </span>
                </header>

                <div class="server-figures">
                    ${fig(cpuLabel, cpuFigure, cpuPct)}
                    ${fig('Memory', pctFigure(ramUsage), ramUsage)}
                    ${fig('Disk', pctFigure(diskUsage), diskUsage)}
                    ${swapPerc > 0 ? fig('Swap', pctFigure(swapPerc), swapPerc) : ''}
                </div>

                <div class="server-info">
                    ${infoRow('Operating system', escapeHtml(server.operating_system || 'N/A'))}
                    ${infoRow('Last boot', escapeHtml(server.last_boot || 'N/A'))}
                    ${infoRow('CPUs', `${server.physical_cpus || '?'} physical / ${server.virtual_cpus || '?'} virtual`)}
                    ${infoRow('Memory', `${escapeHtml(server.ram_used || '?')} of ${escapeHtml(server.ram_total || '?')}`)}
                    ${swapTotalMb > 0 ? infoRow('Swap', `${swapUsedMb} MB of ${swapTotalMb} MB`) : ''}
                    ${infoRow('Disk', `${escapeHtml(server.disk_used || '?')} of ${escapeHtml(server.disk_total || '?')}`)}
                    ${server.net_rx_bytes ? infoRow('Network (cumulative)', `↓ ${formatBytes(server.net_rx_bytes)} &nbsp; ↑ ${formatBytes(server.net_tx_bytes)}`) : ''}
                </div>

                <div class="server-metrics-grid">
                    <div class="metric-item"><span class="metric-label">Connections</span><span class="metric-value">${server.tcp_connections || 0}</span></div>
                    <div class="metric-item"><span class="metric-label">Users</span><span class="metric-value">${server.logged_users || 0}</span></div>
                    <div class="metric-item"><span class="metric-label">SSH</span><span class="metric-value">${server.active_ssh_users || 0}</span></div>
                    <div class="metric-item"><span class="metric-label">VNC</span><span class="metric-value">${server.active_vnc_users || 0}</span></div>
                </div>

                <footer class="server-card-footer">
                    <span>Performance rating</span>
                    <span class="performance-badge ${performance.class}">${performance.rating}</span>
                </footer>
            </article>
        `;
    }

    /**
     * Get server status based on metrics and timestamp
     */
    function getServerStatus(server) {
        const now = new Date();
        const timestamp = new Date(server.timestamp);
        const minutesSinceUpdate = (now - timestamp) / 1000 / 60;

        const ram = parseFloat(server.ram_percentage || 0);
        const disk = parseFloat(server.disk_percentage || 0);
        const cpuLoad = parseFloat(server.cpu_load_5min || 0);
        const cpuUsage = server.cpu_usage_percent != null ? parseFloat(server.cpu_usage_percent) : null;
        const swapPerc = parseFloat(server.swap_percentage || 0);

        // Use actual CPU utilization if available, otherwise fall back to load heuristic
        const cpuHigh = cpuUsage !== null ? cpuUsage > 85 : cpuLoad > 5;

        if (minutesSinceUpdate > 15) {
            return { label: 'Offline', class: 'status-offline', icon: 'fa-times-circle' };
        } else if (ram > 90 || disk > 90 || cpuHigh || swapPerc > 90) {
            return { label: 'Warning', class: 'status-warning', icon: 'fa-exclamation-triangle' };
        } else {
            return { label: 'Online', class: 'status-online', icon: 'fa-check-circle' };
        }
    }

    /**
     * Get performance rating
     */
    function getPerformanceRating(cpu, ram, disk) {
        const score = (cpu * 10) + (ram * 0.4) + (disk * 0.2);

        if (score < 40) {
            return { rating: 'Excellent', class: 'perf-excellent', icon: 'fa-check-circle' };
        } else if (score < 60) {
            return { rating: 'Good', class: 'perf-good', icon: 'fa-thumbs-up' };
        } else if (score < 80) {
            return { rating: 'Fair', class: 'perf-fair', icon: 'fa-exclamation-triangle' };
        } else {
            return { rating: 'Poor', class: 'perf-poor', icon: 'fa-exclamation-circle' };
        }
    }

    /**
     * Load system overview with trend arrows
     */
    async function loadSystemOverview() {
        const container = document.getElementById('system-overview');
        if (!container) return;

        try {
            const response = await API.getSystemOverview();

            if (!response.success) {
                throw new Error('Failed to load system overview');
            }

            const data = response.data;
            const trends = data.trends || {};

            function trendArrow(trend) {
                if (trend === 'up') return '<span class="stat-trend trend-up" title="Rising"><i class="fas fa-arrow-up"></i></span>';
                if (trend === 'down') return '<span class="stat-trend trend-down" title="Falling"><i class="fas fa-arrow-down"></i></span>';
                return '';
            }

            function stat(label, valueHtml, tone = '') {
                return { label, valueHtml, tone };
            }

            const cpuStat = data.avg_cpu_usage != null
                ? stat('Avg CPU usage', `${data.avg_cpu_usage.toFixed(1)}<small>%</small> ${trendArrow(trends.cpu)}`)
                : stat('Avg CPU load', `${(data.avg_cpu_load || 0).toFixed(2)} ${trendArrow(trends.cpu)}`);

            const stats = [
                stat('Servers', `${data.total_servers || 0} ${trendArrow(trends.servers)}`),
                stat('Online', `${data.online_servers || 0}`, 'tone-ok'),
                stat('Warning', `${data.warning_servers || 0}`, data.warning_servers ? 'tone-warn' : 'tone-idle'),
                stat('Offline', `${data.offline_servers || 0}`, data.offline_servers ? 'tone-crit' : 'tone-idle'),
                cpuStat,
                stat('Avg memory', `${(data.avg_ram_usage || 0).toFixed(1)}<small>%</small> ${trendArrow(trends.ram)}`),
                data.avg_swap_usage > 0 ? stat('Avg swap', `${data.avg_swap_usage.toFixed(1)}<small>%</small>`) : null,
                stat('Active users', `${data.total_active_users || 0}`),
                stat('Uptime', `${(data.uptime_percentage || 0).toFixed(1)}<small>%</small>`),
                data.total_net_rx_bytes ? stat('Total RX', formatBytes(data.total_net_rx_bytes)) : null,
                data.total_net_rx_bytes ? stat('Total TX', formatBytes(data.total_net_tx_bytes)) : null
            ].filter(Boolean);

            container.innerHTML = stats.map((s, i) => `
                <div class="overview-stat ${s.tone}" style="--i:${i}">
                    <div class="stat-value">${s.valueHtml}</div>
                    <div class="stat-label">${s.label}</div>
                </div>`).join('');

        } catch (error) {
            console.error('Error loading system overview:', error);
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1;">
                    <i class="fas fa-exclamation-triangle fa-2x"></i>
                    <p>Failed to load system overview</p>
                    <button class="btn btn-secondary" onclick="loadSystemOverview()">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </div>
            `;
        }
    }

    /**
     * Load enhanced server cards
     */
    async function loadEnhancedServerCards() {
        const container = document.getElementById('enhanced-server-cards');
        if (!container) return;

        try {
            const response = await API.getLatestMetrics();
            if (!response.success || !response.data) return;

            // Use detailed cards for server details tab
            container.innerHTML = response.data.map((server, i) => renderDetailedServerCard(server, i)).join('');
        } catch (error) {
            console.error('Error loading enhanced server cards:', error);
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1;">
                    <i class="fas fa-server fa-2x"></i>
                    <p>Failed to load server cards</p>
                    <button class="btn btn-secondary" onclick="loadEnhancedServerCards()">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </div>
            `;
        }
    }

    /**
     * Load user activity table
     */
    async function loadUserActivity() {
        const tableBody = document.getElementById('users-table-body');
        const serverFilter = document.getElementById('server-filter');

        if (!tableBody) return;

        try {
            const response = await API.getTopUsers();

            if (!response.success || !response.data) {
                tableBody.innerHTML = '<tr><td colspan="9" class="text-center">No user data available</td></tr>';
                return;
            }

            const users = response.data;

            if (serverFilter && serverFilter.children.length === 1) {
                const servers = [...new Set(users.map(u => u.server_name))];
                servers.forEach(server => {
                    const option = document.createElement('option');
                    option.value = server;
                    option.textContent = server;
                    serverFilter.appendChild(option);
                });
            }

            setupUserTableFilters(users);  // filters, sorts and renders
            setupFootprintLookup(users);
            loadLicenses();

            // Set initial result count
            const countEl = document.getElementById('users-result-count');
            if (countEl) countEl.textContent = `${users.length} user${users.length !== 1 ? 's' : ''}`;

        } catch (error) {
            console.error('Error loading user activity:', error);
            if (tableBody) {
                tableBody.innerHTML = `<tr><td colspan="9" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle fa-2x"></i>
                        <p>Failed to load user data</p>
                        <button class="btn btn-secondary" onclick="loadUserActivity()">
                            <i class="fas fa-sync-alt"></i> Retry
                        </button>
                    </div>
                </td></tr>`;
            }
            Toast.error('Failed to load user activity');
        }
    }

    /**
     * EDA license pools: per-vendor query status and features in use with holders
     */
    async function loadLicenses() {
        const vendorsEl = document.getElementById('license-vendors');
        const body = document.getElementById('licenses-table-body');
        if (!vendorsEl || !body) return;

        try {
            const response = await API.getLicenseSummary();
            const { vendors, features } = response.data;

            vendorsEl.innerHTML = vendors.length ? vendors.map(v => {
                const tone = v.status === 'failed' || v.stale ? 'status-offline'
                    : v.status === 'partial' ? 'status-warning' : 'status-online';
                const name = v.vendor === 'all' ? 'License query' : v.vendor.charAt(0).toUpperCase() + v.vendor.slice(1);
                const state = v.status === 'failed' ? 'query failed — last good data shown'
                    : v.stale ? `no update for ${v.minutes_since_query} min`
                    : v.status === 'partial' ? 'incomplete' : 'up to date';
                return `<span class="status-badge ${tone}" title="${escapeHtml(v.error || '')}">
                    <span class="status-dot"></span>${escapeHtml(name)}: ${escapeHtml(state)}</span>`;
            }).join('') : '<p class="cell-muted">License collection is not configured.</p>';

            if (!features.length) {
                body.innerHTML = '<tr><td colspan="4" class="table-empty">No licenses checked out right now.</td></tr>';
                return;
            }
            body.innerHTML = features.map(f => {
                const pct = f.issued ? Math.min(100, f.in_use / f.issued * 100) : 0;
                const tone = pct >= 100 ? 'danger' : pct >= 80 ? 'warning' : 'good';
                // One line per person and machine; extra seats shown as ×N
                const grouped = new Map();
                f.holders.forEach(h => {
                    const key = `${h.username}|${h.server_name || h.client_host || ''}`;
                    const g = grouped.get(key) || { ...h, seats: 0 };
                    g.seats += h.licenses || 1;
                    grouped.set(key, g);
                });
                const holders = [...grouped.values()].map(h =>
                    `${escapeHtml(h.username)}${h.seats > 1 ? ` ×${h.seats}` : ''}${h.server_name || h.client_host ? ` <span class="cell-muted">on ${escapeHtml(h.server_name || h.client_host)}</span>` : ''}${h.held ? ` <span class="cell-muted">· ${escapeHtml(h.held)}</span>` : ''}`
                ).join('<br>');
                return `
                    <tr>
                        <td><strong>${escapeHtml(f.feature)}</strong></td>
                        <td>${escapeHtml(f.vendor)}</td>
                        <td><div class="cell-bar">
                            <div class="bar-track"><div class="bar-fill ${tone}" style="width:${pct}%"></div></div>
                            <span class="bar-label">${f.in_use} / ${f.issued ?? '?'}</span>
                        </div></td>
                        <td class="license-holders">${holders || '—'}</td>
                    </tr>`;
            }).join('');
        } catch (error) {
            console.error('Error loading licenses:', error);
            body.innerHTML = `<tr><td colspan="4" class="table-empty">
                Failed to load license usage.
                <button class="btn btn-secondary" onclick="loadLicenses()"><i class="fas fa-sync-alt"></i> Retry</button>
            </td></tr>`;
        }
    }

    window.loadLicenses = loadLicenses;

    function renderUsersTable(users) {
        const tableBody = document.getElementById('users-table-body');
        if (!tableBody) return;

        if (users.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="9" class="table-empty">
                <i class="fas fa-users-slash"></i>No users found</td></tr>`;
            return;
        }

        tableBody.innerHTML = users.map(user => {
            // cpu is percent of one CPU (400 = four cores); the bar caps at one core
            const cpuRaw = Math.max(0, parseFloat(user.cpu || 0));
            const cpuVal = Math.min(100, cpuRaw);
            const cpuLabel = cpuRaw >= 100 ? `${(cpuRaw / 100).toFixed(1)} cores` : `${cpuRaw.toFixed(1)}%`;
            const memVal = Math.min(100, Math.max(0, parseFloat(user.mem || 0)));
            const cpuClass = cpuVal > 90 ? 'danger' : cpuVal > 70 ? 'warning' : 'good';
            const memClass = memVal > 90 ? 'danger' : memVal > 70 ? 'warning' : 'good';
            // Licenses held from this server: feature, extra seats, how long
            // Grouped under a vendor subheading; one line per feature (and client
            // host), seats summed, longest hold shown
            const byVendor = new Map();
            (user.licenses || []).forEach(l => {
                if (!byVendor.has(l.vendor)) byVendor.set(l.vendor, new Map());
                const features = byVendor.get(l.vendor);
                const key = `${l.feature}|${l.client_host}`;
                const g = features.get(key);
                if (!g) { features.set(key, { ...l, licenses: l.licenses || 1 }); return; }
                g.licenses += l.licenses || 1;
                if ((l.held_minutes || 0) > (g.held_minutes || 0)) {
                    Object.assign(g, { held: l.held, held_minutes: l.held_minutes, start_raw: l.start_raw });
                }
            });
            const licenses = [...byVendor.entries()]
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([vendor, features]) => `
                    <div class="license-group">
                        <span class="license-vendor">${escapeHtml(vendor)}</span>
                        ${[...features.values()].map(l => {
                            const seats = l.licenses > 1 ? ` ×${l.licenses}` : '';
                            const from = l.server_name ? '' : ` <span class="cell-muted">from ${escapeHtml(l.client_host || '?')}</span>`;
                            const held = escapeHtml(l.held || l.start_raw || '—');
                            return `<span class="license-chip" title="Checked out ${escapeHtml(l.start_raw || 'at an unknown time')}">`
                                + `${escapeHtml(l.feature)}${seats}${from} <span class="cell-muted">· ${held}</span></span>`;
                        }).join('')}
                    </div>`).join('') || '<span class="cell-muted">—</span>';

            // Inline mini-bar for CPU
            const cpuBar = `<div class="cell-bar">
                <div class="bar-track"><div class="bar-fill ${cpuClass}" style="width:${cpuVal}%"></div></div>
                <span class="bar-label">${cpuLabel}</span>
            </div>`;

            // Inline mini-bar for Memory
            const memBar = `<div class="cell-bar">
                <div class="bar-track"><div class="bar-fill ${memClass}" style="width:${memVal}%"></div></div>
                <span class="bar-label">${memVal.toFixed(1)}%</span>
            </div>`;

            return `
                <tr>
                    <td class="cell-server">${escapeHtml(user.server_name || 'N/A')}</td>
                    <td class="cell-user">
                        <strong>${escapeHtml(user.username || 'N/A')}</strong>
                        ${user.full_name && user.full_name !== 'N/A' ? `<span class="cell-subline" title="${escapeHtml(user.full_name)}">${escapeHtml(user.full_name)}</span>` : ''}
                    </td>
                    <td>${cpuBar}</td>
                    <td>${memBar}</td>
                    <td class="cell-numeric">${user.disk == null ? '—' : `${parseFloat(user.disk).toFixed(1)} GB`}</td>
                    <td class="cell-numeric">${user.process_count || 0}</td>
                    <td class="cell-truncate" title="${escapeHtml(user.top_process || '')}">${escapeHtml(user.top_process || '—')}</td>
                    <td class="cell-licenses">${licenses}</td>
                    <td class="cell-muted cell-date" title="${escapeHtml(formatUserTimestamp(user.last_login))}">${formatUserDate(user.last_login)}</td>
                </tr>
            `;
        }).join('');
    }

    let userFiltersBound = false;
    let allUsersCache = [];
    let usersLoaded = false;

    // Users table sort state; any column header toggles it
    const userSort = { key: 'cpu', dir: 'desc' };

    /** Value used to sort a row by `key`; null/empty always sorts last. */
    function userSortValue(user, key, type) {
        if (key === 'licenses') {
            const lic = user.licenses || [];
            if (!lic.length) return null;
            // Seats held, then the longest hold breaks ties
            const longest = Math.max(0, ...lic.map(l => l.held_minutes || 0));
            return lic.reduce((n, l) => n + (l.licenses || 1), 0) * 1e7 + longest;
        }
        const value = user[key];
        if (value === null || value === undefined || value === '') return null;
        if (type === 'number') {
            const n = parseFloat(value);
            return Number.isNaN(n) ? null : n;
        }
        return String(value).toLowerCase();
    }

    function sortUsers(users) {
        const header = document.querySelector(`#users-table .th-sort[data-sort="${userSort.key}"]`);
        const type = header ? header.dataset.type : 'number';
        const sign = userSort.dir === 'asc' ? 1 : -1;
        return [...users].sort((a, b) => {
            const av = userSortValue(a, userSort.key, type);
            const bv = userSortValue(b, userSort.key, type);
            if (av === null && bv === null) return 0;
            if (av === null) return 1;
            if (bv === null) return -1;
            const cmp = type === 'number' ? av - bv : av.localeCompare(bv);
            return sign * cmp;
        });
    }

    function updateSortHeaders() {
        document.querySelectorAll('#users-table .th-sort').forEach(btn => {
            const active = btn.dataset.sort === userSort.key;
            btn.closest('th').setAttribute('aria-sort',
                active ? (userSort.dir === 'asc' ? 'ascending' : 'descending') : 'none');
        });
    }

    function applyUserFilters() {
        const searchBox = document.getElementById('user-search');
        const serverFilter = document.getElementById('server-filter');
        const allUsers = allUsersCache;
        let filteredUsers = allUsers;

        if (serverFilter && serverFilter.value) {
            filteredUsers = filteredUsers.filter(u => u.server_name === serverFilter.value);
        }

        if (searchBox && searchBox.value) {
            const search = searchBox.value.toLowerCase();
            filteredUsers = filteredUsers.filter(u =>
                (u.username || '').toLowerCase().includes(search) ||
                (u.full_name || '').toLowerCase().includes(search) ||
                (u.server_name || '').toLowerCase().includes(search) ||
                (u.licenses || []).some(l => l.feature.toLowerCase().includes(search))
            );
        }

        updateSortHeaders();
        if (!usersLoaded) return;  // sort choice is kept and applied once data arrives
        renderUsersTable(sortUsers(filteredUsers));

        // Update result count
        const countEl = document.getElementById('users-result-count');
        if (countEl) {
            const total = allUsers.length;
            const shown = filteredUsers.length;
            countEl.textContent = shown === total
                ? `${total} user${total !== 1 ? 's' : ''}`
                : `${shown} of ${total} users`;
        }
    }

    /** Bind search, server filter and sortable headers once, at page load. */
    function bindUserTableControls() {
        if (userFiltersBound) return;
        userFiltersBound = true;
        document.getElementById('user-search')?.addEventListener('input', applyUserFilters);
        document.getElementById('server-filter')?.addEventListener('change', applyUserFilters);
        document.querySelectorAll('#users-table .th-sort').forEach(btn => {
            btn.addEventListener('click', () => {
                if (userSort.key === btn.dataset.sort) {
                    userSort.dir = userSort.dir === 'asc' ? 'desc' : 'asc';
                } else {
                    // Text columns start A→Z, numbers start largest first
                    userSort.key = btn.dataset.sort;
                    userSort.dir = btn.dataset.type === 'text' ? 'asc' : 'desc';
                }
                applyUserFilters();
            });
        });
    }

    function setupUserTableFilters(users) {
        allUsersCache = users;
        usersLoaded = true;
        bindUserTableControls();
        applyUserFilters();
    }

    /** Date only ("Oct 1, 2026"); the full timestamp goes in the cell's title. */
    function formatUserDate(timestamp) {
        if (!timestamp) return '—';
        const date = new Date(timestamp);
        if (isNaN(date)) return '—';
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function formatUserTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            if (isNaN(date)) return 'N/A';
            // Logins are recorded as dates only; a midnight time carries no information
            const dateOnly = date.getHours() === 0 && date.getMinutes() === 0;
            return date.toLocaleString('en-US', dateOnly
                ? { year: 'numeric', month: 'short', day: 'numeric' }
                : { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        } catch {
            return 'N/A';
        }
    }

    /**
     * Load performance analytics charts
     */
    async function loadPerformanceAnalytics() {
        const serverSelect = document.getElementById('analytics-server');
        const timeRange = document.getElementById('time-range');

        if (!serverSelect) return;

        try {
            const serversResponse = await API.getServerList();
            if (serversResponse.success && serversResponse.data) {
                if (serverSelect.children.length === 0) {
                    serversResponse.data.forEach(server => {
                        const option = document.createElement('option');
                        option.value = server;
                        option.textContent = server;
                        serverSelect.appendChild(option);
                    });
                }

                if (serversResponse.data.length > 0) {
                    const hours = parseInt(timeRange?.value || '24');
                    await loadServerCharts(serverSelect.value || serversResponse.data[0], hours);
                }
            }

            if (!analyticsControlsBound) {
                analyticsControlsBound = true;

                serverSelect.addEventListener('change', async () => {
                    const hours = parseInt(timeRange?.value || '24');
                    await loadServerCharts(serverSelect.value, hours);
                });

                if (timeRange) {
                    timeRange.addEventListener('change', async () => {
                        await loadServerCharts(serverSelect.value, parseInt(timeRange.value));
                    });
                }

                const refreshBtn = document.getElementById('refresh-charts');
                if (refreshBtn) {
                    refreshBtn.addEventListener('click', async () => {
                        const hours = parseInt(timeRange?.value || '24');
                        await loadServerCharts(serverSelect.value, hours);
                        Toast.success('Charts refreshed');
                    });
                }
            }

        } catch (error) {
            console.error('Error loading performance analytics:', error);
            Toast.error('Failed to load analytics');
        }
    }

    /**
     * Show or clear a "no data" placeholder over a chart canvas
     */
    function setChartEmpty(canvasId, message) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const wrapper = canvas.parentElement;
        let note = wrapper.querySelector('.chart-empty');
        if (message) {
            if (window.ChartManager) ChartManager.destroyChart(canvasId);
            if (!note) {
                note = document.createElement('div');
                note.className = 'chart-empty';
                wrapper.appendChild(note);
            }
            note.textContent = message;
        } else if (note) {
            note.remove();
        }
    }

    /**
     * Load charts for specific server
     */
    async function loadServerCharts(serverName, hours) {
        if (!serverName || !window.ChartManager) return;

        try {
            const response = await API.getHistoricalMetrics(serverName, hours);

            if (!response.success || !response.data || response.data.length === 0) {
                Toast.warning('No historical data available');
                return;
            }

            const data = response.data;
            const labels = data.map(d => {
                const date = new Date(d.timestamp);
                return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' });
            });

            // Use actual CPU utilization if available, else fall back to load
            const hasCpuUsage = data.some(d => d.cpu_usage_percent != null);
            ChartManager.createLineChart('cpu-chart', {
                labels,
                datasets: hasCpuUsage ? [
                    {
                        label: 'CPU Utilization %',
                        data: data.map(d => d.cpu_usage_percent != null ? parseFloat(d.cpu_usage_percent) : null),
                        colorKey: 'blue',
                        tension: 0.4, fill: true
                    },
                    {
                        label: 'CPU Load (5min)',
                        data: data.map(d => parseFloat(d.cpu_load_5min || 0)),
                        colorKey: 'grayLight',
                        tension: 0.4, fill: false, borderDash: [4, 4]
                    }
                ] : [{
                    label: 'CPU Load (5min)',
                    data: data.map(d => parseFloat(d.cpu_load_5min || 0)),
                    colorKey: 'blue',
                    tension: 0.4, fill: true
                }]
            }, hasCpuUsage ? { scales: { y: { min: 0, max: 100, title: { display: true, text: 'CPU %' } } } } : {});

            ChartManager.createLineChart('memory-chart', {
                labels,
                datasets: [{
                    label: 'RAM Usage %',
                    data: data.map(d => parseFloat(d.ram_percentage || 0)),
                    colorKey: 'purple',
                    tension: 0.4, fill: true
                }]
            }, { scales: { y: { min: 0, max: 100 } } });

            ChartManager.createLineChart('disk-chart', {
                labels,
                datasets: [{
                    label: 'Disk Usage %',
                    data: data.map(d => parseFloat(d.disk_percentage || 0)),
                    colorKey: 'green',
                    tension: 0.4, fill: true
                }]
            }, { scales: { y: { min: 0, max: 100 } } });

            ChartManager.createLineChart('connections-chart', {
                labels,
                datasets: [{
                    label: 'TCP Connections',
                    data: data.map(d => parseInt(d.tcp_connections || 0)),
                    colorKey: 'orange',
                    tension: 0.4, fill: true
                }]
            }, { scales: { y: { ticks: { precision: 0 } } } });

            // Network throughput chart (bytes → MB for readability)
            const hasNetData = data.some(d => d.net_rx_bytes || d.net_tx_bytes);
            setChartEmpty('network-throughput-chart', hasNetData ? null : 'No network counters reported in this window');
            if (hasNetData && document.getElementById('network-throughput-chart')) {
                ChartManager.createLineChart('network-throughput-chart', {
                    labels,
                    datasets: [
                        {
                            label: 'RX (cumulative MB)',
                            data: data.map(d => ((parseInt(d.net_rx_bytes) || 0) / 1048576).toFixed(2)),
                            colorKey: 'cyan',
                            tension: 0.4, fill: true
                        },
                        {
                            label: 'TX (cumulative MB)',
                            data: data.map(d => ((parseInt(d.net_tx_bytes) || 0) / 1048576).toFixed(2)),
                            colorKey: 'green',
                            tension: 0.4, fill: true
                        }
                    ]
                }, { scales: { y: { title: { display: true, text: 'Megabytes' } } } });
            }

            // Swap usage chart
            const hasSwapData = data.some(d => d.swap_percentage > 0);
            setChartEmpty('swap-chart', hasSwapData ? null : 'No swap in use during this window');
            if (hasSwapData && document.getElementById('swap-chart')) {
                ChartManager.createLineChart('swap-chart', {
                    labels,
                    datasets: [{
                        label: 'Swap Usage %',
                        data: data.map(d => parseFloat(d.swap_percentage || 0)),
                        colorKey: 'red',
                        tension: 0.4, fill: true
                    }]
                }, { scales: { y: { min: 0, max: 100, title: { display: true, text: '%' } } } });
            }

            ChartManager.createLineChart('users-chart', {
                labels,
                datasets: [{
                    label: 'Logged Users',
                    data: data.map(d => parseInt(d.logged_users || 0)),
                    colorKey: 'cyan',
                    tension: 0.4, fill: true
                }]
            }, { scales: { y: { ticks: { precision: 0 } } } });

            ChartManager.createLineChart('combined-chart', {
                labels,
                datasets: [
                    {
                        label: 'CPU Load (5min)',
                        data: data.map(d => parseFloat(d.cpu_load_5min || 0) * 10),
                        colorKey: 'blue',
                        yAxisID: 'y', tension: 0.4, fill: true
                    },
                    {
                        label: 'RAM %',
                        data: data.map(d => parseFloat(d.ram_percentage || 0)),
                        colorKey: 'purple',
                        yAxisID: 'y1', tension: 0.4, fill: true
                    },
                    {
                        label: 'Disk %',
                        data: data.map(d => parseFloat(d.disk_percentage || 0)),
                        colorKey: 'green',
                        yAxisID: 'y1', tension: 0.4, fill: true
                    }
                ]
            }, {
                scales: {
                    y: { type: 'linear', position: 'left', title: { display: true, text: 'CPU Load (x10)' } },
                    y1: { type: 'linear', position: 'right', title: { display: true, text: 'Percentage' }, min: 0, max: 100, grid: { drawOnChartArea: false } }
                }
            });

        } catch (error) {
            console.error('Error loading server charts:', error);
            Toast.error('Failed to load charts');
        }
    }

    /**
     * Load network monitor with connections chart
     */
    async function loadNetworkMonitor() {
        const overviewContainer = document.getElementById('network-overview');
        const connectionsContainer = document.getElementById('server-connections');

        if (!overviewContainer) return;

        try {
            const metricsResponse = await API.getLatestMetrics();

            if (!metricsResponse.success || !metricsResponse.data || metricsResponse.data.length === 0) return;

            const servers = metricsResponse.data;

            const totalConnections = servers.reduce((sum, s) => sum + (parseInt(s.tcp_connections) || 0), 0);
            const avgConnections = totalConnections / servers.length;
            const maxConnections = Math.max(...servers.map(s => parseInt(s.tcp_connections) || 0));
            const activeServers = servers.filter(s => (parseInt(s.tcp_connections) || 0) > 0).length;

            const netStats = [
                ['Total connections', totalConnections],
                ['Avg per server', avgConnections.toFixed(1)],
                ['Peak on one server', maxConnections],
                ['Servers with traffic', `${activeServers}<small>/${servers.length}</small>`]
            ];
            overviewContainer.innerHTML = netStats.map(([label, value], i) => `
                <div class="overview-stat" style="--i:${i}">
                    <div class="stat-value">${value}</div>
                    <div class="stat-label">${label}</div>
                </div>`).join('');

            // Connections bar chart — one brand colour; the busiest server is emphasised
            if (window.ChartManager) {
                const counts = servers.map(s => parseInt(s.tcp_connections) || 0);
                ChartManager.createBarChart('network-activity-chart', {
                    labels: servers.map(s => s.server_name),
                    datasets: [{
                        label: 'TCP connections',
                        data: counts,
                        colorKeys: counts.map(c => (c === maxConnections && c > 0) ? 'blue' : 'blueSoft'),
                        borderRadius: 0,
                        borderSkipped: false,
                        maxBarThickness: 56
                    }]
                }, { plugins: { legend: { display: false } } });
            }

            if (connectionsContainer) {
                const hasNet = servers.some(s => s.net_rx_bytes || s.net_tx_bytes);
                connectionsContainer.innerHTML = `
                    <div class="table-wrapper">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th scope="col">Server</th>
                                    <th scope="col" style="min-width:200px">TCP connections</th>
                                    <th scope="col" class="col-numeric">Users</th>
                                    ${hasNet ? '<th scope="col" class="col-numeric">RX (cumulative)</th><th scope="col" class="col-numeric">TX (cumulative)</th>' : ''}
                                </tr>
                            </thead>
                            <tbody>
                                ${servers.map(server => {
                                    const c = parseInt(server.tcp_connections) || 0;
                                    const share = maxConnections > 0 ? (c / maxConnections) * 100 : 0;
                                    return `
                                    <tr>
                                        <td class="cell-server">${escapeHtml(server.server_name)}</td>
                                        <td>
                                            <div class="cell-bar">
                                                <div class="bar-track"><div class="bar-fill good" style="width:${share}%"></div></div>
                                                <span class="bar-label">${c}</span>
                                            </div>
                                        </td>
                                        <td class="cell-numeric">${server.logged_users || 0}</td>
                                        ${hasNet ? `<td class="cell-numeric">${formatBytes(server.net_rx_bytes)}</td><td class="cell-numeric">${formatBytes(server.net_tx_bytes)}</td>` : ''}
                                    </tr>`;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>`;
            }

        } catch (error) {
            console.error('Error loading network monitor:', error);
            Toast.error('Failed to load network data');
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Initialize on DOM load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDashboard);
    } else {
        initializeDashboard();
    }
})();
