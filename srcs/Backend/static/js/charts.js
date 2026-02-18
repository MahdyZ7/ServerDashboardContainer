/**
 * Charts Management
 * Handles Chart.js chart creation with gradient fills and KU-styled tooltips
 */

(function() {
    'use strict';

    const charts = {};

    /**
     * Get current theme colors
     */
    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            gridColor: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.04)',
            tickColor: isDark ? '#8B95A5' : '#94A3B8',
            tooltipBg: isDark ? 'rgba(26, 30, 39, 0.95)' : 'rgba(26, 26, 46, 0.92)',
            legendColor: isDark ? '#E8ECF1' : '#1A1A2E',
            titleColor: isDark ? '#E8ECF1' : '#1A1A2E'
        };
    }

    /**
     * Create gradient fill for a dataset
     */
    function createGradient(ctx, color) {
        const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.clientHeight);
        gradient.addColorStop(0, color.replace(')', ', 0.25)').replace('rgb', 'rgba'));
        gradient.addColorStop(1, color.replace(')', ', 0.02)').replace('rgb', 'rgba'));
        return gradient;
    }

    /**
     * Default chart configuration
     */
    function getDefaultConfig() {
        const tc = getThemeColors();
        return {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { family: "'Inter', sans-serif", size: 12, weight: '500' },
                        padding: 16,
                        usePointStyle: true,
                        pointStyleWidth: 8,
                        color: tc.legendColor
                    }
                },
                tooltip: {
                    backgroundColor: tc.tooltipBg,
                    titleFont: { size: 13, weight: '600', family: "'Inter', sans-serif" },
                    bodyFont: { size: 12, family: "'Inter', sans-serif" },
                    titleColor: '#FFFFFF',
                    bodyColor: '#E8ECF1',
                    padding: 14,
                    cornerRadius: 10,
                    displayColors: true,
                    borderColor: 'rgba(91, 156, 237, 0.2)',
                    borderWidth: 1,
                    boxPadding: 4
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 }, color: tc.tickColor, maxRotation: 45 },
                    border: { display: false }
                },
                y: {
                    grid: { color: tc.gridColor, drawBorder: false },
                    ticks: { font: { size: 11 }, color: tc.tickColor },
                    border: { display: false }
                }
            },
            elements: {
                line: { borderWidth: 2 },
                point: { radius: 0, hoverRadius: 5, hoverBorderWidth: 2, backgroundColor: '#fff' }
            }
        };
    }

    /**
     * Deep merge two objects
     */
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

    /**
     * Create or update a line chart
     */
    function createLineChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        if (charts[canvasId]) {
            charts[canvasId].destroy();
        }

        const ctx = canvas.getContext('2d');

        // Apply gradient fills to datasets
        data.datasets = data.datasets.map(ds => {
            if (ds.fill !== false && ds.backgroundColor && typeof ds.backgroundColor === 'string') {
                const baseColor = ds.borderColor || ds.backgroundColor;
                const gradient = ctx.createLinearGradient(0, 0, 0, canvas.clientHeight || 300);
                gradient.addColorStop(0, hexToRgba(baseColor, 0.2));
                gradient.addColorStop(1, hexToRgba(baseColor, 0.01));
                return { ...ds, backgroundColor: gradient, fill: true };
            }
            return ds;
        });

        const mergedOptions = deepMerge(getDefaultConfig(), options);
        charts[canvasId] = new Chart(ctx, { type: 'line', data, options: mergedOptions });
        return charts[canvasId];
    }

    /**
     * Create or update a bar chart
     */
    function createBarChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        if (charts[canvasId]) {
            charts[canvasId].destroy();
        }

        const ctx = canvas.getContext('2d');
        const mergedOptions = deepMerge(getDefaultConfig(), options);
        charts[canvasId] = new Chart(ctx, { type: 'bar', data, options: mergedOptions });
        return charts[canvasId];
    }

    function updateChart(canvasId, newData) {
        const chart = charts[canvasId];
        if (!chart) return;
        chart.data = newData;
        chart.update();
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

    /**
     * Convert hex color to rgba
     */
    function hexToRgba(hex, alpha) {
        if (hex.startsWith('rgba') || hex.startsWith('rgb')) {
            return hex.replace(/[\d.]+\)$/, `${alpha})`);
        }
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    // Handle theme changes - update chart colors
    window.addEventListener('themechange', function() {
        const tc = getThemeColors();
        Object.values(charts).forEach(chart => {
            if (chart.options.scales) {
                ['x', 'y', 'y1'].forEach(axis => {
                    if (chart.options.scales[axis]) {
                        if (chart.options.scales[axis].grid) {
                            chart.options.scales[axis].grid.color = tc.gridColor;
                        }
                        if (chart.options.scales[axis].ticks) {
                            chart.options.scales[axis].ticks.color = tc.tickColor;
                        }
                    }
                });
            }
            if (chart.options.plugins) {
                if (chart.options.plugins.legend?.labels) {
                    chart.options.plugins.legend.labels.color = tc.legendColor;
                }
                if (chart.options.plugins.tooltip) {
                    chart.options.plugins.tooltip.backgroundColor = tc.tooltipBg;
                    chart.options.plugins.tooltip.borderColor = 'rgba(91, 156, 237, 0.2)';
                }
            }
            chart.update('none');
        });
    });

    window.ChartManager = {
        createLineChart,
        createBarChart,
        updateChart,
        destroyChart,
        destroyAllCharts,
        getChart: (id) => charts[id]
    };
})();
