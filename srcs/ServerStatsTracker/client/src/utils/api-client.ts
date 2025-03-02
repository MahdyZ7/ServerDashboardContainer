
/**
 * API Client for external connections to Server Monitoring Dashboard
 * Use this to connect your local applications to this Repl
 */

// Replace with your Replit URL when deployed
const API_BASE_URL = 'https://your-repl-url.replit.app';

interface ApiClientOptions {
  baseUrl?: string;
  headers?: Record<string, string>;
}

export class ServerMonitoringClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl || API_BASE_URL;
    this.headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error (${response.status}): ${error}`);
    }

    return response.json();
  }

  // API Methods
  async getServers() {
    return this.request('/api/servers');
  }

  async getLatestMetrics() {
    return this.request('/api/metrics/latest');
  }

  async getServerMetrics(serverId: string) {
    return this.request(`/api/metrics/server/${serverId}`);
  }

  async getTopUsers() {
    return this.request('/api/users/top');
  }

  async getSystemStats() {
    return this.request('/api/stats');
  }

  // Example of how to use from an external client
  static example() {
    console.log(`
    // Example usage in your local application:
    import { ServerMonitoringClient } from './api-client';
    
    // Create client instance with your deployed Repl URL
    const client = new ServerMonitoringClient({
      baseUrl: 'https://your-deployed-repl.replit.app',
    });
    
    // Fetch server metrics
    async function getMetrics() {
      try {
        const servers = await client.getServers();
        console.log('Servers:', servers);
        
        const metrics = await client.getLatestMetrics();
        console.log('Latest metrics:', metrics);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    }
    
    getMetrics();
    `);
  }
}
