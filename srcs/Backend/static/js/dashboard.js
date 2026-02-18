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

    /**
     * Initialize dashboard
     */
    function initializeDashboard() {
        setupAutoRefresh();
        setupRefreshButton();
        setupExportDropdown();
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
     * Build circular progress ring style (conic-gradient)
     */
    function progressRingStyle(percentage, color) {
        const p = Math.min(100, Math.max(0, percentage));
        const trackColor = getComputedStyle(document.documentElement)
            .getPropertyValue('--bg-tertiary').trim() || '#EEF0F4';
        return `background: conic-gradient(${color} ${p * 3.6}deg, ${trackColor} ${p * 3.6}deg);`;
    }

    /**
     * Get color for percentage value
     */
    function getPercentageColor(value) {
        if (value > 90) return 'var(--ku-danger)';
        if (value > 70) return 'var(--ku-warning)';
        return 'var(--ku-primary)';
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
            if (loading) loading.style.display = 'flex';
            if (container) container.style.display = 'none';
            if (empty) empty.style.display = 'none';

            const response = await API.getLatestMetrics();

            if (!response.success || !response.data || response.data.length === 0) {
                if (loading) loading.style.display = 'none';
                if (empty) empty.style.display = 'flex';
                return;
            }

            // Use simplified cards for overview
            container.innerHTML = response.data.map(server => renderSimplifiedServerCard(server)).join('');

            if (loading) loading.style.display = 'none';
            container.style.display = 'grid';

        } catch (error) {
            console.error('Error loading server grid:', error);
            if (loading) loading.style.display = 'none';
            if (empty) {
                empty.style.display = 'flex';
                empty.innerHTML = `
                    <i class="fas fa-exclamation-triangle fa-3x"></i>
                    <h3>Failed to Load Data</h3>
                    <p>Could not connect to the server. Please try again.</p>
                    <button class="btn btn-primary" onclick="loadServerGrid()">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                `;
            }
            Toast.error('Failed to load server metrics');
        }
    }

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
     * Build a gauge bar row for the simplified overview card
     */
    function gaugeBar(label, value, pct, color) {
        const clampedPct = Math.min(100, Math.max(0, pct));
        return `
            <div class="gauge-row">
                <span class="gauge-label">${label}</span>
                <div class="gauge-track">
                    <div class="gauge-fill" style="width:${clampedPct}%;background:${color};"></div>
                </div>
                <span class="gauge-value">${value}</span>
            </div>`;
    }

    /**
     * Render simplified server card for overview — horizontal gauge layout
     */
    function renderSimplifiedServerCard(server) {
        const cpuLoad = parseFloat(server.cpu_load_5min || 0);
        const cpuUsage = server.cpu_usage_percent != null ? parseFloat(server.cpu_usage_percent) : null;
        const ramUsage = parseFloat(server.ram_percentage || 0);
        const diskUsage = parseFloat(server.disk_percentage || 0);
        const swapPerc = parseFloat(server.swap_percentage || 0);

        const cpuPct = cpuUsage !== null ? cpuUsage : Math.min(cpuLoad * 10, 100);
        const cpuDisplayVal = cpuUsage !== null ? `${cpuUsage.toFixed(1)}%` : `${cpuLoad.toFixed(2)}`;
        const cpuLabel = cpuUsage !== null ? 'CPU' : 'Load';

        function gaugeColor(pct) {
            if (pct > 90) return 'var(--ku-danger)';
            if (pct > 70) return 'var(--ku-warning)';
            return 'var(--ku-primary)';
        }

        const status = getServerStatus(server);

        const hasNet = server.net_rx_bytes > 0 || server.net_tx_bytes > 0;

        return `
            <div class="sc-overview ${status.class}">
                <div class="sc-head">
                    <div class="sc-name-row">
                        <span class="sc-status-dot ${status.class}"></span>
                        <h3 class="sc-name">${escapeHtml(server.server_name)}</h3>
                    </div>
                    <span class="sc-badge ${status.class}">${status.label}</span>
                </div>
                <div class="sc-gauges">
                    ${gaugeBar(cpuLabel, cpuDisplayVal, cpuPct, gaugeColor(cpuPct))}
                    ${gaugeBar('RAM', `${ramUsage.toFixed(0)}%`, ramUsage, gaugeColor(ramUsage))}
                    ${gaugeBar('Disk', `${diskUsage.toFixed(0)}%`, diskUsage, gaugeColor(diskUsage))}
                    ${swapPerc > 0 ? gaugeBar('Swap', `${swapPerc.toFixed(0)}%`, swapPerc, gaugeColor(swapPerc)) : ''}
                </div>
                <div class="sc-footer">
                    <div class="sc-pill">
                        <i class="fas fa-users"></i>
                        <strong>${server.logged_users || 0}</strong>
                        <span>users</span>
                    </div>
                    <div class="sc-pill">
                        <i class="fas fa-ethernet"></i>
                        <strong>${server.tcp_connections || 0}</strong>
                        <span>TCP</span>
                    </div>
                    ${hasNet ? `
                    <div class="sc-pill">
                        <i class="fas fa-arrow-down"></i>
                        <strong>${formatBytes(server.net_rx_bytes)}</strong>
                    </div>
                    <div class="sc-pill">
                        <i class="fas fa-arrow-up"></i>
                        <strong>${formatBytes(server.net_tx_bytes)}</strong>
                    </div>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Render detailed server card (full information)
     */
    function renderDetailedServerCard(server) {
        const cpuLoad = parseFloat(server.cpu_load_5min || 0);
        const cpuUsage = server.cpu_usage_percent != null ? parseFloat(server.cpu_usage_percent) : null;
        const ramUsage = parseFloat(server.ram_percentage || 0);
        const diskUsage = parseFloat(server.disk_percentage || 0);
        const swapPerc = parseFloat(server.swap_percentage || 0);
        const swapUsedMb = parseInt(server.swap_used_mb || 0);
        const swapTotalMb = parseInt(server.swap_total_mb || 0);

        // Use actual CPU utilization for ring if available
        const cpuRingValue = cpuUsage !== null ? cpuUsage : Math.min(cpuLoad * 10, 100);
        const cpuLabel = cpuUsage !== null ? `${cpuUsage.toFixed(1)}%` : cpuLoad.toFixed(1);
        const cpuRingLabel = cpuUsage !== null ? 'CPU %' : 'CPU Load';

        const status = getServerStatus(server);
        const performance = getPerformanceRating(cpuRingValue, ramUsage, diskUsage);

        return `
            <div class="server-card ${status.class}">
                <div class="server-card-header">
                    <h3>${escapeHtml(server.server_name)}</h3>
                    <span class="status-badge ${status.class}">
                        <span class="status-dot"></span>
                        ${status.label}
                    </span>
                </div>
                <div class="server-info">
                    <div class="server-info-row">
                        <i class="fas fa-desktop"></i>
                        <span class="server-info-label">OS</span>
                        <span class="server-info-value">${escapeHtml(server.operating_system || 'N/A')}</span>
                    </div>
                    <div class="server-info-row">
                        <i class="fas fa-clock"></i>
                        <span class="server-info-label">Last Boot</span>
                        <span class="server-info-value">${escapeHtml(server.last_boot || 'N/A')}</span>
                    </div>
                    <div class="server-info-row">
                        <i class="fas fa-cogs"></i>
                        <span class="server-info-label">CPUs</span>
                        <span class="server-info-value">${server.physical_cpus || '?'}P / ${server.virtual_cpus || '?'}V</span>
                    </div>
                    <div class="server-info-row">
                        <i class="fas fa-memory"></i>
                        <span class="server-info-label">RAM</span>
                        <span class="server-info-value">${escapeHtml(server.ram_used || '?')} / ${escapeHtml(server.ram_total || '?')}</span>
                    </div>
                    ${swapTotalMb > 0 ? `
                    <div class="server-info-row">
                        <i class="fas fa-layer-group"></i>
                        <span class="server-info-label">Swap</span>
                        <span class="server-info-value">${swapUsedMb} MB / ${swapTotalMb} MB (${swapPerc}%)</span>
                    </div>` : ''}
                    <div class="server-info-row">
                        <i class="fas fa-hdd"></i>
                        <span class="server-info-label">Disk</span>
                        <span class="server-info-value">${escapeHtml(server.disk_used || '?')} / ${escapeHtml(server.disk_total || '?')}</span>
                    </div>
                    ${server.net_rx_bytes ? `
                    <div class="server-info-row">
                        <i class="fas fa-network-wired"></i>
                        <span class="server-info-label">Network</span>
                        <span class="server-info-value">↓${formatBytes(server.net_rx_bytes)} ↑${formatBytes(server.net_tx_bytes)}</span>
                    </div>` : ''}
                </div>
                <div class="progress-rings">
                    <div class="progress-ring-item">
                        <div class="progress-ring" style="${progressRingStyle(cpuRingValue, getPercentageColor(cpuRingValue))}">
                            <span>${cpuLabel}</span>
                        </div>
                        <span class="progress-ring-label">${cpuRingLabel}</span>
                    </div>
                    <div class="progress-ring-item">
                        <div class="progress-ring" style="${progressRingStyle(ramUsage, getPercentageColor(ramUsage))}">
                            <span>${ramUsage.toFixed(0)}%</span>
                        </div>
                        <span class="progress-ring-label">RAM</span>
                    </div>
                    <div class="progress-ring-item">
                        <div class="progress-ring" style="${progressRingStyle(diskUsage, getPercentageColor(diskUsage))}">
                            <span>${diskUsage.toFixed(0)}%</span>
                        </div>
                        <span class="progress-ring-label">Disk</span>
                    </div>
                    ${swapPerc > 0 ? `
                    <div class="progress-ring-item">
                        <div class="progress-ring" style="${progressRingStyle(swapPerc, getPercentageColor(swapPerc))}">
                            <span>${swapPerc.toFixed(0)}%</span>
                        </div>
                        <span class="progress-ring-label">Swap</span>
                    </div>` : ''}
                </div>
                <div class="server-metrics-grid">
                    <div class="metric-item">
                        <div class="metric-icon-bg connections">
                            <i class="fas fa-plug"></i>
                        </div>
                        <div class="metric-content">
                            <span class="metric-label">Connections</span>
                            <span class="metric-value">${server.tcp_connections || 0}</span>
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-icon-bg users">
                            <i class="fas fa-users"></i>
                        </div>
                        <div class="metric-content">
                            <span class="metric-label">Users</span>
                            <span class="metric-value">${server.logged_users || 0}</span>
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-icon-bg ssh">
                            <i class="fas fa-terminal"></i>
                        </div>
                        <div class="metric-content">
                            <span class="metric-label">SSH</span>
                            <span class="metric-value">${server.active_ssh_users || 0}</span>
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-icon-bg vnc">
                            <i class="fas fa-tv"></i>
                        </div>
                        <div class="metric-content">
                            <span class="metric-label">VNC</span>
                            <span class="metric-value">${server.active_vnc_users || 0}</span>
                        </div>
                    </div>
                </div>
                <div class="server-card-footer">
                    <span class="performance-badge ${performance.class}">
                        <i class="fas ${performance.icon}"></i>
                        ${performance.rating}
                    </span>
                </div>
            </div>
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
                if (trend === 'up') return '<span class="stat-trend trend-up"><i class="fas fa-arrow-up"></i></span>';
                if (trend === 'down') return '<span class="stat-trend trend-down"><i class="fas fa-arrow-down"></i></span>';
                return '<span class="stat-trend trend-stable"><i class="fas fa-minus"></i></span>';
            }

            const cpuDisplay = data.avg_cpu_usage != null
                ? `${data.avg_cpu_usage.toFixed(1)}%`
                : `${(data.avg_cpu_load || 0).toFixed(1)}`;
            const cpuSubLabel = data.avg_cpu_usage != null ? 'Avg CPU Usage' : 'Avg CPU Load';

            container.innerHTML = `
                <div class="overview-stat">
                    <i class="fas fa-server"></i>
                    <div>
                        <div class="stat-value">${data.total_servers || 0} ${trendArrow(trends.servers)}</div>
                        <div class="stat-label">Total Servers</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-check-circle" style="color: var(--ku-success);"></i>
                    <div>
                        <div class="stat-value">${data.online_servers || 0}</div>
                        <div class="stat-label">Online</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-exclamation-triangle" style="color: var(--ku-warning);"></i>
                    <div>
                        <div class="stat-value">${data.warning_servers || 0}</div>
                        <div class="stat-label">Warning</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-times-circle" style="color: var(--ku-danger);"></i>
                    <div>
                        <div class="stat-value">${data.offline_servers || 0}</div>
                        <div class="stat-label">Offline</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-microchip"></i>
                    <div>
                        <div class="stat-value">${cpuDisplay} ${trendArrow(trends.cpu)}</div>
                        <div class="stat-label">${cpuSubLabel}</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-memory"></i>
                    <div>
                        <div class="stat-value">${(data.avg_ram_usage || 0).toFixed(1)}% ${trendArrow(trends.ram)}</div>
                        <div class="stat-label">Avg RAM Usage</div>
                    </div>
                </div>
                ${data.avg_swap_usage > 0 ? `
                <div class="overview-stat">
                    <i class="fas fa-layer-group"></i>
                    <div>
                        <div class="stat-value">${(data.avg_swap_usage || 0).toFixed(1)}%</div>
                        <div class="stat-label">Avg Swap Usage</div>
                    </div>
                </div>` : ''}
                <div class="overview-stat">
                    <i class="fas fa-users"></i>
                    <div>
                        <div class="stat-value">${data.total_active_users || 0}</div>
                        <div class="stat-label">Active Users</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-chart-line"></i>
                    <div>
                        <div class="stat-value">${(data.uptime_percentage || 0).toFixed(1)}%</div>
                        <div class="stat-label">Uptime</div>
                    </div>
                </div>
                ${data.total_net_rx_bytes ? `
                <div class="overview-stat">
                    <i class="fas fa-download"></i>
                    <div>
                        <div class="stat-value">${formatBytes(data.total_net_rx_bytes)}</div>
                        <div class="stat-label">Total RX</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-upload"></i>
                    <div>
                        <div class="stat-value">${formatBytes(data.total_net_tx_bytes)}</div>
                        <div class="stat-label">Total TX</div>
                    </div>
                </div>` : ''}
            `;

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
            container.innerHTML = response.data.map(server => renderDetailedServerCard(server)).join('');
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
                tableBody.innerHTML = '<tr><td colspan="11" class="text-center">No user data available</td></tr>';
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

            renderUsersTable(users);
            setupUserTableFilters(users);

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

    function renderUsersTable(users) {
        const tableBody = document.getElementById('users-table-body');
        if (!tableBody) return;

        if (users.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="11" class="text-center">No users found</td></tr>';
            return;
        }

        tableBody.innerHTML = users.map(user => {
            const cpuVal = parseFloat(user.cpu || 0);
            const memVal = parseFloat(user.mem || 0);
            const cpuClass = cpuVal > 50 ? 'high' : cpuVal > 20 ? 'medium' : 'low';
            const memClass = memVal > 50 ? 'high' : memVal > 20 ? 'medium' : 'low';
            const ioRead = user.io_read_bytes ? formatBytes(user.io_read_bytes) : '—';
            const ioWrite = user.io_write_bytes ? formatBytes(user.io_write_bytes) : '—';

            return `
                <tr>
                    <td>${escapeHtml(user.server_name || 'N/A')}</td>
                    <td><strong>${escapeHtml(user.username || 'N/A')}</strong></td>
                    <td>${escapeHtml(user.full_name || 'N/A')}</td>
                    <td class="cell-numeric"><span class="cell-badge ${cpuClass}">${cpuVal.toFixed(1)}%</span></td>
                    <td class="cell-numeric"><span class="cell-badge ${memClass}">${memVal.toFixed(1)}%</span></td>
                    <td class="cell-numeric">${parseFloat(user.disk || 0).toFixed(2)} GB</td>
                    <td class="cell-numeric">${user.process_count || 0}</td>
                    <td>${escapeHtml(user.top_process || 'N/A')}</td>
                    <td class="cell-numeric">${ioRead}</td>
                    <td class="cell-numeric">${ioWrite}</td>
                    <td>${formatUserTimestamp(user.last_login)}</td>
                </tr>
            `;
        }).join('');
    }

    function setupUserTableFilters(allUsers) {
        const searchBox = document.getElementById('user-search');
        const serverFilter = document.getElementById('server-filter');
        const sortBy = document.getElementById('sort-by');

        function applyFilters() {
            let filteredUsers = allUsers;

            if (serverFilter && serverFilter.value) {
                filteredUsers = filteredUsers.filter(u => u.server_name === serverFilter.value);
            }

            if (searchBox && searchBox.value) {
                const search = searchBox.value.toLowerCase();
                filteredUsers = filteredUsers.filter(u =>
                    (u.username || '').toLowerCase().includes(search) ||
                    (u.full_name || '').toLowerCase().includes(search) ||
                    (u.server_name || '').toLowerCase().includes(search)
                );
            }

            if (sortBy && sortBy.value) {
                const sortField = sortBy.value;
                filteredUsers = [...filteredUsers].sort((a, b) => {
                    const aVal = parseFloat(a[sortField]) || 0;
                    const bVal = parseFloat(b[sortField]) || 0;
                    return bVal - aVal;
                });
            }

            renderUsersTable(filteredUsers);
        }

        if (searchBox) searchBox.addEventListener('input', applyFilters);
        if (serverFilter) serverFilter.addEventListener('change', applyFilters);
        if (sortBy) sortBy.addEventListener('change', applyFilters);
    }

    function formatUserTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('en-US', {
                year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            });
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
                    await loadServerCharts(serversResponse.data[0], hours);
                }
            }

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

        } catch (error) {
            console.error('Error loading performance analytics:', error);
            Toast.error('Failed to load analytics');
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
                        borderColor: '#003DA5',
                        backgroundColor: 'rgba(0, 61, 165, 0.1)',
                        tension: 0.4, fill: true
                    },
                    {
                        label: 'CPU Load (5min)',
                        data: data.map(d => parseFloat(d.cpu_load_5min || 0)),
                        borderColor: '#A0B8E0',
                        backgroundColor: 'rgba(160, 184, 224, 0.05)',
                        tension: 0.4, fill: false, borderDash: [4, 4]
                    }
                ] : [{
                    label: 'CPU Load (5min)',
                    data: data.map(d => parseFloat(d.cpu_load_5min || 0)),
                    borderColor: '#003DA5',
                    backgroundColor: 'rgba(0, 61, 165, 0.1)',
                    tension: 0.4, fill: true
                }]
            }, hasCpuUsage ? { scales: { y: { min: 0, max: 100, title: { display: true, text: 'CPU %' } } } } : {});

            ChartManager.createLineChart('memory-chart', {
                labels,
                datasets: [{
                    label: 'RAM Usage %',
                    data: data.map(d => parseFloat(d.ram_percentage || 0)),
                    borderColor: '#6F5091',
                    backgroundColor: 'rgba(111, 80, 145, 0.1)',
                    tension: 0.4, fill: true
                }]
            }, { scales: { y: { min: 0, max: 100 } } });

            ChartManager.createLineChart('disk-chart', {
                labels,
                datasets: [{
                    label: 'Disk Usage %',
                    data: data.map(d => parseFloat(d.disk_percentage || 0)),
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4, fill: true
                }]
            }, { scales: { y: { min: 0, max: 100 } } });

            ChartManager.createLineChart('connections-chart', {
                labels,
                datasets: [{
                    label: 'TCP Connections',
                    data: data.map(d => parseInt(d.tcp_connections || 0)),
                    borderColor: '#F57F29',
                    backgroundColor: 'rgba(245, 127, 41, 0.1)',
                    tension: 0.4, fill: true
                }]
            });

            // Network throughput chart (bytes → MB for readability)
            const hasNetData = data.some(d => d.net_rx_bytes || d.net_tx_bytes);
            if (hasNetData && document.getElementById('network-throughput-chart')) {
                ChartManager.createLineChart('network-throughput-chart', {
                    labels,
                    datasets: [
                        {
                            label: 'RX (cumulative MB)',
                            data: data.map(d => ((parseInt(d.net_rx_bytes) || 0) / 1048576).toFixed(2)),
                            borderColor: '#00A9CE',
                            backgroundColor: 'rgba(0, 169, 206, 0.1)',
                            tension: 0.4, fill: true
                        },
                        {
                            label: 'TX (cumulative MB)',
                            data: data.map(d => ((parseInt(d.net_tx_bytes) || 0) / 1048576).toFixed(2)),
                            borderColor: '#78D64B',
                            backgroundColor: 'rgba(120, 214, 75, 0.1)',
                            tension: 0.4, fill: true
                        }
                    ]
                }, { scales: { y: { title: { display: true, text: 'Megabytes' } } } });
            }

            // Swap usage chart
            const hasSwapData = data.some(d => d.swap_percentage > 0);
            if (hasSwapData && document.getElementById('swap-chart')) {
                ChartManager.createLineChart('swap-chart', {
                    labels,
                    datasets: [{
                        label: 'Swap Usage %',
                        data: data.map(d => parseFloat(d.swap_percentage || 0)),
                        borderColor: '#E31E24',
                        backgroundColor: 'rgba(227, 30, 36, 0.1)',
                        tension: 0.4, fill: true
                    }]
                }, { scales: { y: { min: 0, max: 100, title: { display: true, text: '%' } } } });
            }

            ChartManager.createLineChart('users-chart', {
                labels,
                datasets: [{
                    label: 'Logged Users',
                    data: data.map(d => parseInt(d.logged_users || 0)),
                    borderColor: '#00A9CE',
                    backgroundColor: 'rgba(0, 169, 206, 0.1)',
                    tension: 0.4, fill: true
                }]
            });

            ChartManager.createLineChart('combined-chart', {
                labels,
                datasets: [
                    {
                        label: 'CPU Load (5min)',
                        data: data.map(d => parseFloat(d.cpu_load_5min || 0) * 10),
                        borderColor: '#003DA5',
                        backgroundColor: 'rgba(0, 61, 165, 0.05)',
                        yAxisID: 'y', tension: 0.4, fill: true
                    },
                    {
                        label: 'RAM %',
                        data: data.map(d => parseFloat(d.ram_percentage || 0)),
                        borderColor: '#6F5091',
                        backgroundColor: 'rgba(111, 80, 145, 0.05)',
                        yAxisID: 'y1', tension: 0.4, fill: true
                    },
                    {
                        label: 'Disk %',
                        data: data.map(d => parseFloat(d.disk_percentage || 0)),
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.05)',
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
            const [metricsResponse, serversResponse] = await Promise.all([
                API.getLatestMetrics(),
                API.getServerList()
            ]);

            if (!metricsResponse.success || !metricsResponse.data) return;

            const servers = metricsResponse.data;

            const totalConnections = servers.reduce((sum, s) => sum + (parseInt(s.tcp_connections) || 0), 0);
            const avgConnections = totalConnections / servers.length;
            const maxConnections = Math.max(...servers.map(s => parseInt(s.tcp_connections) || 0));
            const activeServers = servers.filter(s => (parseInt(s.tcp_connections) || 0) > 0).length;

            overviewContainer.innerHTML = `
                <div class="overview-stat">
                    <i class="fas fa-network-wired"></i>
                    <div>
                        <div class="stat-value">${totalConnections}</div>
                        <div class="stat-label">Total Connections</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-chart-line"></i>
                    <div>
                        <div class="stat-value">${avgConnections.toFixed(1)}</div>
                        <div class="stat-label">Avg per Server</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-arrow-up"></i>
                    <div>
                        <div class="stat-value">${maxConnections}</div>
                        <div class="stat-label">Peak Connections</div>
                    </div>
                </div>
                <div class="overview-stat">
                    <i class="fas fa-server"></i>
                    <div>
                        <div class="stat-value">${activeServers}</div>
                        <div class="stat-label">Active Servers</div>
                    </div>
                </div>
            `;

            // Render connections bar chart
            if (window.ChartManager) {
                ChartManager.createBarChart('network-activity-chart', {
                    labels: servers.map(s => s.server_name),
                    datasets: [{
                        label: 'TCP Connections',
                        data: servers.map(s => parseInt(s.tcp_connections) || 0),
                        backgroundColor: servers.map((_, i) => {
                            const colors = ['rgba(0, 61, 165, 0.7)', 'rgba(111, 80, 145, 0.7)', 'rgba(0, 169, 206, 0.7)', 'rgba(245, 127, 41, 0.7)', 'rgba(120, 214, 75, 0.7)', 'rgba(227, 30, 36, 0.7)', 'rgba(0, 61, 165, 0.5)'];
                            return colors[i % colors.length];
                        }),
                        borderRadius: 6,
                        borderSkipped: false
                    }]
                });
            }

            if (connectionsContainer) {
                connectionsContainer.innerHTML = servers.map(server => `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <i class="fas fa-server"></i>
                                ${escapeHtml(server.server_name)}
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="metric-item">
                                <div class="metric-icon-bg connections">
                                    <i class="fas fa-plug"></i>
                                </div>
                                <div class="metric-content">
                                    <span class="metric-label">TCP Connections</span>
                                    <span class="metric-value">${server.tcp_connections || 0}</span>
                                </div>
                            </div>
                            <div class="metric-item" style="margin-top: var(--spacing-sm);">
                                <div class="metric-icon-bg users">
                                    <i class="fas fa-users"></i>
                                </div>
                                <div class="metric-content">
                                    <span class="metric-label">Active Users</span>
                                    <span class="metric-value">${server.logged_users || 0}</span>
                                </div>
                            </div>
                            ${server.net_rx_bytes ? `
                            <div class="metric-item" style="margin-top: var(--spacing-sm);">
                                <div class="metric-icon-bg" style="background: rgba(0,169,206,0.15);">
                                    <i class="fas fa-download" style="color:#00A9CE;"></i>
                                </div>
                                <div class="metric-content">
                                    <span class="metric-label">RX (cumulative)</span>
                                    <span class="metric-value">${formatBytes(server.net_rx_bytes)}</span>
                                </div>
                            </div>
                            <div class="metric-item" style="margin-top: var(--spacing-sm);">
                                <div class="metric-icon-bg" style="background: rgba(120,214,75,0.15);">
                                    <i class="fas fa-upload" style="color:#78D64B;"></i>
                                </div>
                                <div class="metric-content">
                                    <span class="metric-label">TX (cumulative)</span>
                                    <span class="metric-value">${formatBytes(server.net_tx_bytes)}</span>
                                </div>
                            </div>` : ''}
                        </div>
                    </div>
                `).join('');
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
