// Generated TypeScript Types
// Schema Version: 1.0.0
// Generated At: 2025-11-05T00:11:46.315719
// DO NOT EDIT MANUALLY

/**
 * ServerMetrics interface (auto-generated from schema)
 * Table: server_metrics
 */
export interface ServerMetrics {
  /** Primary key */
  id: number;
  /** Server identifier */
  server_name: string;
  /** Collection timestamp */
  timestamp: Date | string;
  /** System architecture (kernel, release, machine) */
  architecture?: string;
  /** Operating system name and version */
  os?: string;
  /** Number of physical CPU sockets */
  physical_cpus?: number;
  /** Number of virtual CPU cores (threads) */
  virtual_cpus?: number;
  /** RAM currently in use */
  ram_used?: string;
  /** Total RAM available */
  ram_total?: string;
  /** RAM usage percentage */
  ram_percentage?: number;
  /** Disk space used */
  disk_used?: string;
  /** Total disk space */
  disk_total?: string;
  /** Disk usage percentage */
  disk_percentage?: string;
  /** CPU load average (1 minute) */
  cpu_load_1min?: string;
  /** CPU load average (5 minutes) */
  cpu_load_5min?: string;
  /** CPU load average (15 minutes) */
  cpu_load_15min?: string;
  /** Last system boot time */
  last_boot?: string;
  /** Number of TCP connections */
  tcp_connections?: number;
  /** Number of logged-in users */
  logged_users?: number;
  /** Active VNC sessions */
  active_vnc?: number;
  /** Active SSH sessions */
  active_ssh?: number;
}

/**
 * TopUsers interface (auto-generated from schema)
 * Table: top_users
 */
export interface TopUsers {
  /** Primary key */
  id: number;
  /** Server identifier */
  server_name: string;
  /** Collection timestamp */
  timestamp: Date | string;
  /** Username */
  username: string;
  /** CPU usage percentage */
  cpu_percentage?: number;
  /** Memory usage percentage */
  memory_percentage?: number;
  /** Disk usage in GB */
  disk_usage_gb?: number;
  /** Number of processes */
  process_count?: number;
  /** Top CPU-consuming process */
  top_process?: string;
  /** Last login timestamp */
  last_login?: string;
  /** User's full name */
  full_name?: string;
}

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

/**
 * API error response
 */
export interface ApiError {
  success: false;
  message: string;
  error?: string;
}
