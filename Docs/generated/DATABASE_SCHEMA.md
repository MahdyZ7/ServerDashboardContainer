# Database Schema Documentation

**Schema Version:** 1.0.0  
**Generated:** 2025-11-05T00:11:46.315719  

This documentation is auto-generated from `schema/metrics_schema.yaml`.

---

## Table: `server_metrics`

System monitoring metrics collected from remote servers

### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | serial | No | Primary key |
| `server_name` | varchar(255) | No | Server identifier |
| `timestamp` | timestamp | No | Collection timestamp |
| `architecture` | varchar(255) | Yes | System architecture (kernel, release, machine) |
| `os` | varchar(100) | Yes | Operating system name and version |
| `physical_cpus` | integer | Yes | Number of physical CPU sockets |
| `virtual_cpus` | integer | Yes | Number of virtual CPU cores (threads) |
| `ram_used` | varchar(20) | Yes | RAM currently in use |
| `ram_total` | varchar(20) | Yes | Total RAM available |
| `ram_percentage` | integer | Yes | RAM usage percentage |
| `disk_used` | varchar(20) | Yes | Disk space used |
| `disk_total` | varchar(20) | Yes | Total disk space |
| `disk_percentage` | varchar(10) | Yes | Disk usage percentage |
| `cpu_load_1min` | varchar(10) | Yes | CPU load average (1 minute) |
| `cpu_load_5min` | varchar(10) | Yes | CPU load average (5 minutes) |
| `cpu_load_15min` | varchar(10) | Yes | CPU load average (15 minutes) |
| `last_boot` | varchar(50) | Yes | Last system boot time |
| `tcp_connections` | integer | Yes | Number of TCP connections |
| `logged_users` | integer | Yes | Number of logged-in users |
| `active_vnc` | integer | Yes | Active VNC sessions |
| `active_ssh` | integer | Yes | Active SSH sessions |

---

## Table: `top_users`

Per-user resource usage metrics

### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | serial | No | Primary key |
| `server_name` | varchar(255) | No | Server identifier |
| `timestamp` | timestamp | No | Collection timestamp |
| `username` | varchar(50) | No | Username |
| `cpu_percentage` | decimal(5,2) | Yes | CPU usage percentage |
| `memory_percentage` | decimal(5,2) | Yes | Memory usage percentage |
| `disk_usage_gb` | decimal(10,2) | Yes | Disk usage in GB |
| `process_count` | integer | Yes | Number of processes |
| `top_process` | varchar(255) | Yes | Top CPU-consuming process |
| `last_login` | varchar(50) | Yes | Last login timestamp |
| `full_name` | varchar(255) | Yes | User's full name |
