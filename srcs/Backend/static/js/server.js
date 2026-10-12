/**
 * Server page
 * One machine's latest collection: spare CPU and memory, required mounts,
 * open VNC desktops and SSH logins, and the heaviest accounts.
 */

(function() {
    'use strict';

    const REFRESH_MS = 60 * 1000;

    const page = document.getElementById('server-page');
    const serverName = page?.dataset.server;

    function escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    function plural(n, word, many = word + 's') {
        return `${n} ${n === 1 ? word : many}`;
    }

    function duration(seconds) {
        if (seconds == null) return '—';
        const m = Math.floor(seconds / 60);
        if (m < 1) return 'under a minute';
        if (m < 60) return `${m} min`;
        const h = Math.floor(m / 60);
        if (h < 48) return `${h} h ${m % 60 ? `${m % 60} min` : ''}`.trim();
        return `${Math.floor(h / 24)} days`;
    }

    function since(iso) {
        if (!iso) return '—';
        return duration((Date.now() - new Date(iso).getTime()) / 1000);
    }

    function formatDate(iso) {
        if (!iso) return '—';
        return new Date(iso).toLocaleString(undefined, {
            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
        });
    }

    function formatGb(kb) {
        if (kb == null) return '—';
        const gb = kb / 1048576;
        return gb >= 10 ? `${gb.toFixed(0)} GB` : gb >= 1 ? `${gb.toFixed(1)} GB` : `${(kb / 1024).toFixed(0)} MB`;
    }

    function badge(state, label) {
        const tone = { ok: '', warn: 'status-warning', off: 'status-offline' }[state];
        return `<span class="status-badge ${tone}"><span class="status-dot"></span>${label}</span>`;
    }

    function table(head, rows, empty) {
        return `
            <div class="table-wrapper">
                <table class="data-table data-table--compact">
                    <thead><tr>${head.map(([h, cls]) => `<th scope="col"${cls ? ` class="${cls}"` : ''}>${h}</th>`).join('')}</tr></thead>
                    <tbody>${rows || `<tr><td colspan="${head.length}" class="table-empty">${empty}</td></tr>`}</tbody>
                </table>
            </div>`;
    }

    function userCell(name, fullName, extra = '') {
        return `<td class="cell-user"><strong>${escapeHtml(name)}</strong>${extra}
            ${fullName ? `<span class="cell-subline" title="${escapeHtml(fullName)}">${escapeHtml(fullName)}</span>` : ''}</td>`;
    }

    // ── Figures ────────────────────────────────────────────────────────
    function figure(label, valueHtml, note, pctUsed, tone = '') {
        const bar = pctUsed == null ? '' : `
            <div class="fig-bar" role="meter" aria-label="${label} in use" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(pctUsed)}">
                <i style="width:${Math.min(100, Math.max(0, pctUsed))}%"></i>
            </div>`;
        return `
            <div class="server-figure ${tone}">
                <span class="fig-label">${label}</span>
                <span class="fig-value">${valueHtml}</span>
                ${bar}
                <span class="server-figure-note">${note}</span>
            </div>`;
    }

    const MOUNT_STATES = {
        mounted: { value: 'Mounted', tone: '', note: m => escapeHtml(m.source || m.mount_point) },
        unresponsive: { value: 'Not responding', tone: 'is-crit', note: m => `${escapeHtml(m.mount_point)} is mounted but did not answer within 10 s` },
        missing: { value: 'Not mounted', tone: 'is-crit', note: () => 'Not in this server\'s mount table' },
    };

    function renderFigures(d) {
        const c = d.capacity;
        const cpuUsed = c.virtual_cpus ? (c.load_5min / c.virtual_cpus) * 100 : null;
        const ramUsed = c.ram_total_gb ? (1 - c.ram_free_gb / c.ram_total_gb) * 100 : null;
        const cpuTone = c.virtual_cpus && c.free_cores < Math.max(1, c.virtual_cpus * 0.1) ? 'is-warn' : '';
        const ramTone = ramUsed != null && ramUsed >= 90 ? 'is-warn' : '';

        const figures = [
            figure('CPU available',
                `${c.free_cores}<small> of ${c.virtual_cpus} cores</small>`,
                `5-minute load ${c.load_5min}${c.cpu_usage_percent != null ? ` · ${c.cpu_usage_percent.toFixed(0)}% busy now` : ''}`,
                cpuUsed, cpuTone),
            figure('Memory available',
                c.ram_free_gb != null ? `${c.ram_free_gb}<small> of ${c.ram_total_gb} GB</small>` : '—',
                c.swap_percentage ? `Swap ${c.swap_percentage}% used` : 'Free for new work, including reclaimable cache',
                ramUsed, ramTone),
        ];

        if (!d.mounts.length) {
            figures.push(figure('Lab share', '—', d.detail_collected
                ? 'No required mounts configured' : 'Checked from the next collection', null));
        }
        d.mounts.forEach(m => {
            const s = MOUNT_STATES[m.state] || { value: escapeHtml(m.state), tone: 'is-warn', note: () => '' };
            figures.push(figure(escapeHtml(m.name), s.value, s.note(m), null, s.tone));
        });

        const s = d.sessions;
        figures.push(figure('Sessions',
            `${s.vnc.length}<small> VNC</small> · ${s.ssh.filter(x => x.terminal).length}<small> SSH</small>`,
            `${plural(s.vnc_in_use, 'desktop')} with a viewer connected · ${plural(s.ssh_in_use, 'terminal')} active`,
            null));

        document.getElementById('server-figures').innerHTML = figures.join('');
    }

    // ── Lede and status ────────────────────────────────────────────────
    function renderHead(d) {
        const statusLabel = { online: 'Online', warning: 'Under load', offline: 'Not reporting' }[d.status];
        const el = document.getElementById('server-status');
        el.className = `status-badge ${d.status === 'online' ? '' : `status-${d.status}`}`;
        el.innerHTML = `<span class="status-dot"></span>${statusLabel}`;
        document.getElementById('server-collected').textContent =
            `Collected ${formatDate(d.collected_at)} (${since(d.collected_at)} ago)`;

        const c = d.capacity;
        const s = d.sessions;
        const parts = [];
        if (d.status === 'offline') {
            parts.push(`<span class="lede-crit">${escapeHtml(d.server_name)} has not reported for ${since(d.collected_at)}</span>; figures below are from its last report.`);
        }
        parts.push(`<strong>${c.free_cores}</strong> of ${c.virtual_cpus} cores and <strong>${c.ram_free_gb ?? '?'} GB</strong> of memory are free.`);
        if (d.detail_collected) {
            const vnc = s.vnc.length
                ? `${plural(s.vnc.length, 'VNC desktop')} open (${s.vnc_in_use} with a viewer connected)`
                : 'no VNC desktops open';
            const terms = s.ssh.filter(x => x.terminal).length;
            const ssh = terms ? `${plural(terms, 'SSH terminal')} (${s.ssh_in_use} active)` : 'no SSH terminals';
            parts.push(`${vnc[0].toUpperCase()}${vnc.slice(1)}, ${ssh}.`);
        }
        d.mounts.filter(m => m.state !== 'mounted').forEach(m => {
            parts.push(`<span class="lede-crit">${escapeHtml(m.name)} is ${m.state === 'missing' ? 'not mounted' : 'not responding'}.</span>`);
        });
        document.getElementById('server-lede').innerHTML = parts.join(' ');
    }

    // ── Sessions ───────────────────────────────────────────────────────
    function hostLabel(h) {
        return h === '127.0.0.1' || h === '::1' ? 'SSH tunnel' : escapeHtml(h);
    }

    function renderVnc(d) {
        const s = d.sessions;
        const container = document.getElementById('vnc-sessions');
        if (!d.detail_collected) {
            container.innerHTML = '<p class="cell-muted">Session detail arrives with the next collection.</p>';
            return;
        }
        const counts = Object.fromEntries(s.vnc_multiple.map(u => [u.username, u.count]));
        const note = s.vnc_multiple.length
            ? `<p class="server-callout"><strong>${plural(s.vnc_multiple.length, 'user')} with more than one desktop:</strong>
                ${s.vnc_multiple.map(u => `${escapeHtml(u.username)} (${u.count})`).join(', ')}</p>`
            : '';
        const rows = s.vnc.map(v => {
            const state = v.state === 'in_use' ? badge('ok', 'Viewer connected')
                : v.state === 'no_viewer' ? badge('off', 'No viewer') : badge('off', 'Unknown');
            const multi = counts[v.username] ? `<span class="multi-badge">${counts[v.username]} desktops</span>` : '';
            return `<tr class="${counts[v.username] ? 'row-multi' : ''}">
                ${userCell(v.username, v.full_name, multi)}
                <td class="cell-numeric">${escapeHtml(v.display || '—')}</td>
                <td>${state}</td>
                <td>${v.remote_hosts.length ? v.remote_hosts.map(hostLabel).join(', ') : '<span class="cell-muted">—</span>'}</td>
                <td class="cell-date">${formatDate(v.started_at)}<span class="cell-subline">${since(v.started_at)}</span></td>
            </tr>`;
        }).join('');
        container.innerHTML = note + table(
            [['User'], ['Display', 'col-numeric'], ['Viewer'], ['Connected from'], ['Running since']],
            rows, 'No VNC desktops are running.');
    }

    function renderSsh(d) {
        const s = d.sessions;
        const container = document.getElementById('ssh-sessions');
        if (!d.detail_collected) {
            container.innerHTML = '<p class="cell-muted">Session detail arrives with the next collection.</p>';
            return;
        }
        const rows = s.ssh.map(x => {
            if (!x.terminal) {
                return `<tr>
                    ${userCell(x.username, x.full_name)}
                    <td>No terminal${x.connections > 1 ? ` ×${x.connections}` : ''}
                        <span class="cell-subline">VS Code, file transfer or tunnel</span></td>
                    <td><span class="cell-muted">—</span></td>
                    <td class="cell-date">${formatDate(x.started_at)}</td>
                    <td><span class="cell-muted">—</span></td>
                    <td>${badge('ok', 'Connected')}</td>
                </tr>`;
            }
            const state = x.state === 'in_use' ? badge('ok', 'Active')
                : x.state === 'idle' ? badge('off', 'Idle') : badge('off', 'Unknown');
            return `<tr>
                ${userCell(x.username, x.full_name)}
                <td class="cell-numeric">${escapeHtml(x.terminal)}</td>
                <td>${escapeHtml(x.remote_host || '—')}</td>
                <td class="cell-date">${formatDate(x.started_at)}</td>
                <td>${x.idle_seconds == null ? '—' : `${duration(x.idle_seconds)} ago`}</td>
                <td>${state}</td>
            </tr>`;
        }).join('');
        container.innerHTML = table(
            [['User'], ['Terminal'], ['From'], ['Logged in'], ['Last input'], ['State']],
            rows, 'No one is logged in over SSH.')
            + `<p class="action-note">Active = keyboard input in the last ${s.idle_minutes} minutes before collection.</p>`;
    }

    function renderTopUsers(d) {
        const rows = d.top_users.map(u => {
            const cores = u.cpu != null ? u.cpu / 100 : null;
            return `<tr>
                ${userCell(u.username, u.full_name && u.full_name !== 'N/A' ? u.full_name : '')}
                <td class="cell-numeric">${cores == null ? '—' : cores >= 0.1 ? `${cores.toFixed(1)} cores` : 'idle'}</td>
                <td class="cell-numeric">${formatGb(u.rss_kb)}${u.mem != null ? `<span class="cell-subline">${u.mem.toFixed(1)}%</span>` : ''}</td>
                <td class="cell-numeric">${u.process_count}</td>
                <td class="cell-truncate" title="${escapeHtml(u.top_process || '')}">${escapeHtml(u.top_process || '—')}</td>
            </tr>`;
        }).join('');
        document.getElementById('server-top-users').innerHTML = table(
            [['User'], ['CPU', 'col-numeric'], ['Memory', 'col-numeric'], ['Processes', 'col-numeric'], ['Top process']],
            rows, 'No accounts have running processes.')
            + '<p class="action-note">CPU is sampled over a few seconds at collection time; 1 core = one logical CPU fully busy.</p>';
    }

    // ── Load ───────────────────────────────────────────────────────────
    async function load(manual = false) {
        try {
            const res = await API.getServerSummary(serverName);
            if (!res.success) throw new Error(res.message || res.error);
            const d = res.data;
            renderHead(d);
            renderFigures(d);
            renderVnc(d);
            renderSsh(d);
            renderTopUsers(d);
            if (manual) Toast.success('Server data refreshed');
        } catch (error) {
            console.error('Error loading server summary:', error);
            const message = error.status === 404
                ? `No data has been collected for ${escapeHtml(serverName)} yet.`
                : `Could not load ${escapeHtml(serverName)}.`;
            document.getElementById('server-lede').innerHTML = message;
            document.getElementById('server-figures').innerHTML = `
                <div class="empty-state">
                    <p>${message}</p>
                    <button class="btn btn-secondary" id="server-retry"><i class="fas fa-sync-alt" aria-hidden="true"></i> Retry</button>
                </div>`;
            document.getElementById('server-retry')?.addEventListener('click', () => load(true));
            ['vnc-sessions', 'ssh-sessions', 'server-top-users'].forEach(id => {
                document.getElementById(id).innerHTML = '';
            });
            if (manual) Toast.error('Failed to load server data');
        }
    }

    if (!serverName) return;
    document.getElementById('server-refresh')?.addEventListener('click', () => load(true));
    load();
    setInterval(() => { if (!document.hidden) load(); }, REFRESH_MS);
})();
