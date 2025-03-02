export interface ServerMetric {
  id: number;
  timestamp: string;
  server_name: string;
  architecture: string;
  operating_system: string;
  physical_cpus: number;
  virtual_cpus: number;
  ram_used: string;
  ram_total: string;
  ram_percentage: number;
  disk_used: string;
  disk_total: string;
  disk_percentage: number;
  cpu_load_1min: number;
  cpu_load_5min: number;
  cpu_load_15min: number;
  last_boot: string;
  tcp_connections: number;
  logged_users: number;
  active_vnc_users: number;
  active_ssh_users: number;
}

export interface ServerUser {
  id: number;
  timestamp: string;
  server_name: string;
  user: string;
  cpu: number;
  mem: number;
  disk: number;
}

export interface ServerSummary {
  server_name: string;
  status: 'online' | 'warning' | 'offline';
  ip_address?: string;
  last_updated?: string;
}

export interface ServerStats {
  totalServers: number;
  onlineServers: number;
  offlineServers: number;
  averageCpuLoad: number;
  averageMemoryUsage: number;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  server?: string;
}

export interface ServerStatus {
  status: 'success' | 'warning' | 'error';
  timestamp: string;
}

export type TimeRange = '1h' | '24h' | '7d' | '30d';
