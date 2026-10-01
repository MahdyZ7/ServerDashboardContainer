/**
 * Charts Management
 * Chart.js wrapper with readability-first configuration:
 * clear grid lines, readable axis ticks, informative tooltips,
 * gradient fills, and full dark-mode support.
 */

(function() {
    'use strict';

    const charts = {};

    /* ─── Theme colors ─────────────────────────────────────────── */
    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            isDark,
            gridColor:    isDark ? 'rgba(255, 255, 255, 0.07)' : 'rgba(0, 0, 0, 0.06)',
            tickColor:    isDark ? '#8B95A5' : '#64748B',
            tooltipBg:    isDark ? 'rgba(15, 20, 30, 0.97)' : 'rgba(15, 25, 55, 0.95)',
            tooltipBorder:isDark ? 'rgba(91, 156, 237, 0.25)' : 'rgba(0, 61, 165, 0.2)',
            legendColor:  isDark ? '#C8D0DC' : '#334155',
        };
    }

    /* ─── Gradient helper ──────────────────────────────────────── */
    function makeGradient(ctx, color, alphaTop = 0.22, alphaBot = 0.01) {
        const height = ctx.canvas.clientHeight || 280;
        const grad = ctx.createLinearGradient(0, 0, 0, height);
        grad.addColorStop(0, hexToRgba(color, alphaTop));
        grad.addColorStop(1, hexToRgba(color, alphaBot));
        return grad;
    }

    /* ─── Default config ───────────────────────────────────────── */
    function getDefaultConfig() {
        const tc = getThemeColors();

        return {
            responsive: true,
            maintainAspectRatio: false,   // lets CSS height control canvas height
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        font: { family: "'Inter', sans-serif", size: 12, weight: '600' },
                        padding: 18,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        pointStyleWidth: 9,
                        color: tc.legendColor,
                        boxHeight: 9
                    }
                },
                tooltip: {
                    backgroundColor: tc.tooltipBg,
                    titleFont: { size: 13, weight: '700', family: "'Inter', sans-serif" },
                    bodyFont:  { size: 12, weight: '500', family: "'Inter', sans-serif" },
                    footerFont:{ size: 11, family: "'Inter', sans-serif" },
                    titleColor: '#FFFFFF',
                    bodyColor:  '#CBD5E1',
                    footerColor:'#64748B',
                    padding: { top: 10, right: 14, bottom: 10, left: 14 },
                    cornerRadius: 8,
                    displayColors: true,
                    borderColor: tc.tooltipBorder,
                    borderWidth: 1,
                    boxPadding: 5,
                    caretSize: 6,
                    // Show unit suffix in tooltip — override per chart via callbacks.label
                    callbacks: {
                        label: function(ctx) {
                            const label = ctx.dataset.label || '';
                            const val   = ctx.parsed.y;
                            if (val == null) return label;
                            const unit = ctx.dataset.unit || '';
                            const formatted = Number.isInteger(val) ? val : val.toFixed(1);
                            return `  ${label}: ${formatted}${unit}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    border: { display: false },
                    ticks: {
                        font:  { size: 11, family: "'Inter', sans-serif", weight: '500' },
                        color: tc.tickColor,
                        maxRotation: 30,
                        autoSkipPadding: 16,
                        // Show fewer labels on narrow charts to avoid crowding
                        maxTicksLimit: 10
                    }
                },
                y: {
                    position: 'left',
                    grid: {
                        color: tc.gridColor,
                        drawBorder: false,
                        // Dashed gridlines are softer and easier to scan
                        lineWidth: 1
                    },
                    border: { display: false, dash: [4, 4] },
                    ticks: {
                        font:   { size: 11, family: "'Inter', sans-serif", weight: '500' },
                        color:  tc.tickColor,
                        padding: 8,
                        // 5–6 ticks is the readable sweet spot
                        maxTicksLimit: 6,
                        callback: function(val) {
                            // Auto-abbreviate large numbers: 1500 → 1.5k
                            if (Math.abs(val) >= 1000) {
                                return (val / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
                            }
                            return val;
                        }
                    }
                }
            },
            elements: {
                line: {
                    borderWidth: 2.5,
                    tension: 0.35          // slight curve — easier on the eye than sharp angles
                },
                point: {
                    radius: 0,             // hide points by default (less clutter)
                    hoverRadius: 5,
                    hoverBorderWidth: 2,
                    hoverBorderColor: '#fff',
                    hitRadius: 12          // generous hit area for touch
                },
                bar: {
                    borderRadius: 4,
                    borderSkipped: 'bottom'
                }
            },
            // Smooth 400ms animation on load
            animation: {
                duration: 400,
                easing: 'easeOutQuart'
            }
        };
    }

    /* ─── Deep merge ───────────────────────────────────────────── */
    function deepMerge(target, source) {
        const result = { ...target };
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = deepMerge(result[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }
        return result;
    }

    /* ─── Line chart ───────────────────────────────────────────── */
    function createLineChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        if (charts[canvasId]) charts[canvasId].destroy();

        const ctx = canvas.getContext('2d');

        // Apply gradient fills
        data.datasets = data.datasets.map(ds => {
            if (ds.fill !== false && (ds.borderColor || ds.backgroundColor)) {
                const baseColor = ds.borderColor || ds.backgroundColor;
                if (typeof baseColor === 'string') {
                    return {
                        ...ds,
                        backgroundColor: makeGradient(ctx, baseColor),
                        fill: true
                    };
                }
            }
            return ds;
        });

        const merged = deepMerge(getDefaultConfig(), options);
        charts[canvasId] = new Chart(ctx, { type: 'line', data, options: merged });
        return charts[canvasId];
    }

    /* ─── Bar chart ────────────────────────────────────────────── */
    function createBarChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        if (charts[canvasId]) charts[canvasId].destroy();

        const ctx = canvas.getContext('2d');
        const merged = deepMerge(getDefaultConfig(), options);
        charts[canvasId] = new Chart(ctx, { type: 'bar', data, options: merged });
        return charts[canvasId];
    }

    /* ─── Update / destroy helpers ─────────────────────────────── */
    function updateChart(canvasId, newData) {
        const chart = charts[canvasId];
        if (!chart) return;
        chart.data = newData;
        chart.update('active');
    }

    function destroyChart(canvasId) {
        if (charts[canvasId]) {
            charts[canvasId].destroy();
            delete charts[canvasId];
        }
    }

    function destroyAllCharts() {
        Object.keys(charts).forEach(destroyChart);
    }

    /* ─── Hex → rgba ───────────────────────────────────────────── */
    function hexToRgba(hex, alpha) {
        if (!hex) return `rgba(0,0,0,${alpha})`;
        if (hex.startsWith('rgba') || hex.startsWith('rgb')) {
            return hex.replace(/[\d.]+\)$/, `${alpha})`);
        }
        const clean = hex.replace('#', '');
        const full  = clean.length === 3
            ? clean.split('').map(c => c + c).join('')
            : clean;
        const r = parseInt(full.slice(0, 2), 16);
        const g = parseInt(full.slice(2, 4), 16);
        const b = parseInt(full.slice(4, 6), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    /* ─── Theme change handler ─────────────────────────────────── */
    window.addEventListener('themechange', function() {
        const tc = getThemeColors();
        Object.values(charts).forEach(chart => {
            if (chart.options.scales) {
                ['x', 'y', 'y1'].forEach(axis => {
                    if (!chart.options.scales[axis]) return;
                    const s = chart.options.scales[axis];
                    if (s.grid)  s.grid.color  = tc.gridColor;
                    if (s.ticks) s.ticks.color  = tc.tickColor;
                });
            }
            if (chart.options.plugins) {
                if (chart.options.plugins.legend?.labels) {
                    chart.options.plugins.legend.labels.color = tc.legendColor;
                }
                if (chart.options.plugins.tooltip) {
                    chart.options.plugins.tooltip.backgroundColor = tc.tooltipBg;
                    chart.options.plugins.tooltip.borderColor     = tc.tooltipBorder;
                }
            }
            chart.update('none');
        });
    });

    /* ─── Public API ────────────────────────────────────────────── */
    window.ChartManager = {
        createLineChart,
        createBarChart,
        updateChart,
        destroyChart,
        destroyAllCharts,
        getChart: (id) => charts[id],
        hexToRgba
    };
})();
