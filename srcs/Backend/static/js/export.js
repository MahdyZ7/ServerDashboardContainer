/**
 * Export Functionality
 * Handles dashboard data export to JSON and CSV with dropdown menu
 */

(function() {
    'use strict';

    /**
     * Export dashboard data to JSON
     */
    async function exportToJSON() {
        try {
            Toast.info('Preparing JSON export...');
            const data = await collectDashboardData();

            const jsonString = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            downloadFile(url, `dashboard-export-${getTimestamp()}.json`);
            Toast.success('Dashboard data exported as JSON');
        } catch (error) {
            console.error('Export error:', error);
            Toast.error('Failed to export dashboard data');
        }
    }

    /**
     * Export dashboard data to CSV
     */
    async function exportToCSV() {
        try {
            Toast.info('Preparing CSV export...');
            const data = await collectDashboardData();

            // Build CSV from server metrics
            let csv = '';

            if (data.servers && data.servers.length > 0) {
                csv += '=== Server Metrics ===\n';
                csv += convertToCSV(data.servers);
                csv += '\n\n';
            }

            if (data.users && data.users.length > 0) {
                csv += '=== User Activity ===\n';
                csv += convertToCSV(data.users);
            }

            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);

            downloadFile(url, `dashboard-export-${getTimestamp()}.csv`);
            Toast.success('Dashboard data exported as CSV');
        } catch (error) {
            console.error('Export error:', error);
            Toast.error('Failed to export to CSV');
        }
    }

    /**
     * Collect all dashboard data
     */
    async function collectDashboardData() {
        const [metrics, users, overview] = await Promise.all([
            API.getLatestMetrics(),
            API.getTopUsers(),
            API.getSystemOverview()
        ]);

        return {
            timestamp: new Date().toISOString(),
            overview: overview.data,
            servers: metrics.data || [],
            users: users.data || []
        };
    }

    /**
     * Convert data array to CSV format
     */
    function convertToCSV(data) {
        if (!data || data.length === 0) return '';

        const headers = Object.keys(data[0]);
        const csvRows = [headers.join(',')];

        for (const row of data) {
            const values = headers.map(header => {
                const value = row[header];
                const escaped = String(value == null ? '' : value).replace(/"/g, '""');
                return `"${escaped}"`;
            });
            csvRows.push(values.join(','));
        }

        return csvRows.join('\n');
    }

    function downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    function getTimestamp() {
        return new Date().toISOString().replace(/:/g, '-').replace(/\..+/, '').replace('T', '_');
    }

    function printDashboard() {
        window.print();
    }

    // Expose to global scope
    window.DashboardExport = {
        toJSON: exportToJSON,
        toCSV: exportToCSV,
        print: printDashboard
    };
})();
