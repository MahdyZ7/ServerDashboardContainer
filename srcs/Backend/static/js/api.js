/**
 * API Client
 * Handles all API communication with retry logic, timeout, and exponential backoff
 */

(function() {
    'use strict';

    const API_BASE = DASHBOARD_CONFIG.apiBaseUrl || '/api';
    const MAX_RETRIES = 3;
    const BASE_DELAY = 500;
    const FETCH_TIMEOUT = 10000;

    /**
     * Fetch with timeout
     */
    function fetchWithTimeout(url, options, timeout = FETCH_TIMEOUT) {
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeout);

        return fetch(url, {
            ...options,
            signal: controller.signal
        }).finally(() => clearTimeout(id));
    }

    /**
     * Fetch with retry logic and exponential backoff
     */
    async function fetchWithRetry(url, options = {}, retries = MAX_RETRIES) {
        try {
            const response = await fetchWithTimeout(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            if (retries > 0) {
                const attempt = MAX_RETRIES - retries + 1;
                const delay = BASE_DELAY * Math.pow(2, attempt - 1);
                console.warn(`Retry ${attempt}/${MAX_RETRIES} in ${delay}ms...`);
                await sleep(delay);
                return fetchWithRetry(url, options, retries - 1);
            } else {
                throw error;
            }
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    const API = {
        async getLatestMetrics() {
            return fetchWithRetry(`${API_BASE}/servers/metrics/latest`);
        },

        async getHistoricalMetrics(serverName, hours = 24) {
            return fetchWithRetry(`${API_BASE}/servers/${encodeURIComponent(serverName)}/metrics/historical/${hours}`);
        },

        async getServerStatus(serverName) {
            return fetchWithRetry(`${API_BASE}/servers/${encodeURIComponent(serverName)}/status`);
        },

        async getServerList() {
            return fetchWithRetry(`${API_BASE}/servers/list`);
        },

        async getTopUsers() {
            return fetchWithRetry(`${API_BASE}/users/top`);
        },

        async getTopUsersByServer(serverName) {
            return fetchWithRetry(`${API_BASE}/users/top/${encodeURIComponent(serverName)}`);
        },

        async getSystemOverview() {
            return fetchWithRetry(`${API_BASE}/system/overview`);
        },

        async getServerHealth(serverName) {
            return fetchWithRetry(`${API_BASE}/health/${encodeURIComponent(serverName)}`);
        }
    };

    window.API = API;
})();
