/**
 * Charts Management
 * Chart.js wrapper with readability-first configuration:
 * clear grid lines, readable axis ticks, informative tooltips,
 * gradient fills, and full dark-mode support.
 */

(function() {
    'use strict';

    const charts = {};
    const FONT_FAMILY = "'DIN Next LT Pro', 'DIN Next', 'Barlow', 'Helvetica Neue', Arial, sans-serif";

    /* ─── Theme colors ─────────────────────────────────────────── */
    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            isDark,
            gridColor:    isDark ? 'rgba(232, 233, 234, 0.08)' : 'rgba(60, 60, 59, 0.09)',
            tickColor:    isDark ? '#8C9095' : '#75787B',
            tooltipBg:    isDark ? '#E8E9EA' : '#3C3C3B',
            tooltipText:  isDark ? '#0D1420' : '#FFFFFF',
            legendColor:  isDark ? '#B7BABE' : '#3C3C3B',
            pointBorder:  isDark ? '#0D1420' : '#FFFFFF',
        };
    }

    /* ─── Brand palette (KU Brand Guidelines 2020, §3.01) ─────────
       Light mode uses the official digital RGB values. Dark mode lifts
       only the colours that would fall below 3:1 against the navy ground. */
    const PALETTE = {
        light: {
            blue: '#0057B8', blueSoft: '#99BCE3', purple: '#6F5091', cyan: '#00A9CE',
            green: '#5FB536', orange: '#FF8F1C', red: '#F8485E', warmGray: '#C5B9AC',
            grayLight: '#75787B'
        },
        dark: {
            blue: '#5C9CE6', blueSoft: '#2E4D74', purple: '#A68BC7', cyan: '#33C3E3',
            green: '#78D64B', orange: '#FF8F1C', red: '#F8485E', warmGray: '#C5B9AC',
            grayLight: '#8C9095'
        }
    };

    function paletteColor(key) {
        const set = getThemeColors().isDark ? PALETTE.dark : PALETTE.light;
        return set[key] || key;
    }

    /* Resolve colorKey / colorKeys on datasets into concrete colours */
    function applyPalette(ctx, dataset, type) {
        if (dataset.colorKeys) {
            const colors = dataset.colorKeys.map(paletteColor);
            dataset.backgroundColor = colors;
            dataset.borderColor = colors;
            return dataset;
        }
        if (!dataset.colorKey) return dataset;
        const color = paletteColor(dataset.colorKey);
        dataset.borderColor = color;
        dataset.pointHoverBackgroundColor = color;
        if (type === 'line') {
            dataset.backgroundColor = dataset.fill === false ? color : makeGradient(ctx, color);
        } else {
            dataset.backgroundColor = color;
        }
        return dataset;
    }

    /* ─── Gradient helper ──────────────────────────────────────── */
    function makeGradient(ctx, color, alphaTop = 0.16, alphaBot = 0) {
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
                        font: { family: FONT_FAMILY, size: 12, weight: '500' },
                        padding: 18,
                        usePointStyle: true,
                        pointStyle: 'line',
                        pointStyleWidth: 18,
                        color: tc.legendColor,
                        boxHeight: 3
                    }
                },
                tooltip: {
                    backgroundColor: tc.tooltipBg,
                    titleFont: { size: 13, weight: '500', family: FONT_FAMILY },
                    bodyFont:  { size: 12, weight: '400', family: FONT_FAMILY },
                    footerFont:{ size: 11, family: FONT_FAMILY },
                    titleColor: tc.tooltipText,
                    bodyColor:  tc.tooltipText,
                    footerColor: tc.tooltipText,
                    padding: { top: 10, right: 14, bottom: 10, left: 14 },
                    cornerRadius: 0,
                    displayColors: true,
                    borderWidth: 0,
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
                        font:  { size: 11, family: FONT_FAMILY, weight: '400' },
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
                        font:   { size: 11, family: FONT_FAMILY, weight: '400' },
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
                    borderWidth: 2,
                    tension: 0.25          // slight curve — easier on the eye than sharp angles
                },
                point: {
                    radius: 0,             // hide points by default (less clutter)
                    hoverRadius: 5,
                    hoverBorderWidth: 2,
                    hoverBorderColor: getThemeColors().pointBorder,
                    hitRadius: 12          // generous hit area for touch
                },
                bar: {
                    borderRadius: 0,
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

        // Resolve brand colours (and gradient fills) for each dataset
        data.datasets = data.datasets.map(ds => {
            if (ds.colorKey) return applyPalette(ctx, { ...ds, fill: ds.fill !== false }, 'line');
            if (ds.fill !== false && typeof ds.borderColor === 'string') {
                return { ...ds, backgroundColor: makeGradient(ctx, ds.borderColor), fill: true };
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
        data.datasets = data.datasets.map(ds => applyPalette(ctx, { ...ds }, 'bar'));
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
                    const tt = chart.options.plugins.tooltip;
                    tt.backgroundColor = tc.tooltipBg;
                    tt.titleColor = tt.bodyColor = tt.footerColor = tc.tooltipText;
                }
            }
            // Re-resolve brand colours for the new theme
            chart.data.datasets.forEach(ds => applyPalette(chart.ctx, ds, chart.config.type));
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
        hexToRgba,
        color: paletteColor
    };
})();
