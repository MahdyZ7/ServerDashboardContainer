# Server Monitoring Dashboard - Architecture & Schema Flow

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REMOTE SERVERS (SSH)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  mini_monitering.sh          TopUsers.sh                                │
│  (CSV format output)         (space-separated output)                    │
│                                                                           │
│  Arch,OS,PCPU,VCPU,RAM,      USERNAME CPU MEM DISK PROCS TOP PRC...     │
│  DISK,CPU_LOAD,BOOT,TCP,     alice 5.25 12.50 nan 3 java...            │
│  USERS,VNC,SSH               bob 2.15 8.75 OFF 2 python...              │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │                            │
         │ SSH (via BashGetInfo.sh)   │ SSH (via BashGetInfo.sh)
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            DATACOLLECTION SERVICE (Python - backend.py)                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Metrics Stream              User Data Stream                           │
│  ───────────────              ──────────────                            │
│                                                                           │
│  run_monitoring_script()     get_top_users()                            │
│  └─ Returns CSV string       └─ Returns raw output                      │
│                                                                           │
│  parse_monitoring_data()     parse_top_users()                          │
│  (lines 211-270)             (lines 184-208)                            │
│  ├─ Split on commas          ├─ Split on whitespace                     │
│  ├─ Map to 18 fields         ├─ Map to user dicts                       │
│  └─ Return Dict              └─ Return {"top_users": [Dict, ...]}       │
│                                                                           │
│  store_metrics()             store_top_users()                          │
│  └─ INSERT INTO...           └─ INSERT ... ON CONFLICT DO UPDATE        │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │                            │
         │ INSERT                     │ UPSERT
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database (server_db)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  server_metrics table          top_users table                          │
│  ──────────────────────         ────────────────                        │
│                                                                           │
│  id (BIGSERIAL)                id (BIGSERIAL)                           │
│  timestamp (TIMESTAMP)          timestamp (TIMESTAMP)                    │
│  server_name (VARCHAR)          server_name (VARCHAR)                    │
│  architecture (VARCHAR)         username (VARCHAR)                       │
│  operating_system (VARCHAR)     cpu (DECIMAL)                            │
│  physical_cpus (INT)            mem (DECIMAL)                            │
│  virtual_cpus (INT)             disk (DECIMAL)                           │
│  ram_used (VARCHAR)             process_count (INT)                      │
│  ram_total (VARCHAR)            top_process (VARCHAR)                    │
│  ram_percentage (INT)           last_login (TIMESTAMP)                   │
│  disk_used (VARCHAR)            full_name (VARCHAR)                      │
│  disk_total (VARCHAR)           UNIQUE(server_name, username)            │
│  disk_percentage (INT)                                                   │
│  cpu_load_1min (DECIMAL)                                                 │
│  cpu_load_5min (DECIMAL)                                                 │
│  cpu_load_15min (DECIMAL)                                                │
│  last_boot (VARCHAR)                                                     │
│  tcp_connections (INT)                                                   │
│  logged_users (INT)                                                      │
│  active_vnc_users (INT)                                                  │
│  active_ssh_users (INT)                                                  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │                            │
         │ Query via Flask            │ Query via Flask
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Flask REST API (srcs/Backend/api.py)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  GET /api/servers/metrics/latest                                        │
│  ├─ SELECT ... WITH latest_records AS ...                               │
│  └─ Returns: List[{id, timestamp, server_name, arch, os, pcpu, vcpu,   │
│                    ram_used, ram_total, ram_perc, disk_used, disk_total,│
│                    disk_perc, cpu_load_1min, cpu_load_5min, cpu_load_15,│
│                    last_boot, tcp_connections, logged_users, vnc, ssh}] │
│                                                                           │
│  GET /api/servers/<server>/metrics/historical/<hours>                   │
│  ├─ WHERE timestamp > NOW() - INTERVAL '<hours> hours'                  │
│  └─ Returns: List[{timestamp, ram_perc, disk_perc, cpu_load_*,         │
│                    tcp_connections, logged_users}]                      │
│                                                                           │
│  GET /api/users/top[/<server>]                                          │
│  ├─ SELECT ... FROM top_users [WHERE server_name = ...]                │
│  └─ Returns: List[{server_name, username, cpu, mem, disk, process_count│
│                    top_process, last_login, full_name, timestamp}]      │
│                                                                           │
│  GET /api/servers/<server>/status                                       │
│  ├─ SELECT * ... ORDER BY timestamp DESC LIMIT 1                        │
│  ├─ Adds: status = "online" | "warning" | "offline"                     │
│  └─ Returns: Single dict (all fields + status)                          │
│                                                                           │
│  GET /api/servers/list                                                   │
│  └─ Returns: ["server1", "server2", ...]                                │
│                                                                           │
│  GET /api/system/overview                                                │
│  └─ Returns: {total_servers, online, warning, offline, avg_cpu, avg_ram,│
│               avg_disk, total_users, uptime_pct, trends}                │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │                            │
         │ HTTP GET JSON              │ HTTP GET JSON
         │ (with retry logic)         │ (with retry logic)
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            Frontend API Client (srcs/Frontend/api_client.py)            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  @retry_on_failure(max_retries=3, backoff_factor=2)                     │
│  get_latest_server_metrics() → List[Dict]                               │
│                                                                           │
│  @retry_on_failure()                                                     │
│  get_historical_metrics(server_name, hours=24) → List[Dict]             │
│                                                                           │
│  @retry_on_failure()                                                     │
│  get_top_users() → List[Dict]                                            │
│                                                                           │
│  @retry_on_failure()                                                     │
│  get_server_status(server_name) → Dict                                   │
│                                                                           │
│  Timeout: 10s per request                                                │
│  On failure: Return [] or {}                                             │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │                            │
         │ Data (List[Dict])          │ Data (List[Dict])
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│         Data Processing (srcs/Frontend/data_processing.py)              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  safe_create_dataframe(data, name)                                       │
│  └─ List[Dict] → pd.DataFrame (or empty on error)                       │
│                                                                           │
│  prepare_historical_dataframe(data, server_name)                         │
│  ├─ safe_create_dataframe()                                              │
│  ├─ parse_dataframe_timestamps(df, "timestamp")                          │
│  ├─ convert_numeric_columns(df, [                                        │
│  │   "cpu_load_1min", "cpu_load_5min", "cpu_load_15min",               │
│  │   "ram_percentage", "disk_percentage",                              │
│  │   "logged_users", "tcp_connections"                                 │
│  │ ])                                                                   │
│  ├─ validate_dataframe_range(col, 0, 100, clip=True) [% columns]       │
│  ├─ validate_dataframe_range(col, 0, 1000) [CPU load columns]          │
│  └─ Sort by timestamp                                                    │
│                                                                           │
│  aggregate_metrics(metrics_list, operation="mean"|"sum"|"max"|"min")    │
│  └─ Returns: Dict with aggregated values                                 │
│                                                                           │
│  detect_anomalies(df, column, threshold_std=3.0)                         │
│  └─ pd.Series with boolean flags                                         │
│                                                                           │
│  calculate_trends(df, column, window=5)                                  │
│  └─ Returns: "increasing" | "decreasing" | "stable"                     │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │                            │
         │ DataFrame                  │ Dict
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            Validation (srcs/Frontend/validation.py)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  validate_server_metrics(metrics: Dict)                                  │
│  ├─ Required: server_name                                                │
│  ├─ Numeric fields with ranges:                                          │
│  │  - cpu_load_1min: (0, 100)                                            │
│  │  - cpu_load_5min: (0, 100)                                            │
│  │  - cpu_load_15min: (0, 100)                                           │
│  │  - ram_percentage: (0, 100)                                           │
│  │  - disk_percentage: (0, 100)                                          │
│  │  - logged_users: (0, 10000)                                           │
│  │  - tcp_connections: (0, 100000)                                       │
│  └─ Return: Validated Dict                                               │
│                                                                           │
│  validate_user_data(user: Dict)                                          │
│  ├─ Required: username                                                   │
│  ├─ Numeric: cpu, mem, disk (convert to float)                           │
│  └─ Return: Validated Dict                                               │
│                                                                           │
│  validate_percentage(value, field_name)                                  │
│  └─ Ensure 0 <= value <= 100                                             │
│                                                                           │
│  validate_server_name(server_name)                                       │
│  ├─ Must be non-empty string                                             │
│  ├─ Max 255 chars                                                        │
│  └─ Stripped of whitespace                                               │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │                            │
         │ Validated Data             │ Validated Data
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Frontend Components (srcs/Frontend/)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Dash.py - Main application layout                                       │
│  components.py - UI component generators                                 │
│  callbacks.py - Event handlers                                           │
│                                                                           │
│  Components:                                                             │
│  ├─ Server Status Cards (latest metrics)                                │
│  ├─ Historical Charts (time-series graphs)                              │
│  ├─ User Activity Table (top users per server)                          │
│  ├─ System Overview Panel (aggregated stats)                            │
│  └─ Performance Alerts (thresholds from config.py)                      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │
         │ HTML/CSS/JavaScript
         │
         ▼
    ┌──────────────────┐
    │  Browser (Port  │
    │      3000)       │
    │ Dashboard UI     │
    └──────────────────┘
```

---

## Data Type Flow for a Single Metric: RAM Percentage

This example shows how one metric flows through all layers:

```
COLLECTION LAYER
┌─────────────────────────────────────────────────┐
│ mini_monitering.sh                               │
│ RAM_PERC=$(echo "$RAM_DATA" | awk '{printf      │
│   "%.0f"), $3 / $2 * 100}')                      │
│ → Bash variable: "45"                            │
└─────────────────────────────────────────────────┘
                    ↓ (CSV output)
PARSING LAYER
┌─────────────────────────────────────────────────┐
│ backend.py:parse_monitoring_data()               │
│ ram_perc = int(disk_perc.strip("%"))             │
│ → Python: ram_percentage = 45 (int)              │
└─────────────────────────────────────────────────┘
                    ↓ (store_metrics)
DATABASE LAYER
┌─────────────────────────────────────────────────┐
│ PostgreSQL server_metrics table                  │
│ ram_percentage INT, VALUES: 45                   │
└─────────────────────────────────────────────────┘
                    ↓ (SELECT ram_percentage)
API LAYER
┌─────────────────────────────────────────────────┐
│ Flask endpoint response JSON:                    │
│ {                                                │
│   "success": true,                               │
│   "data": [{                                     │
│     "ram_percentage": 45,                        │
│     ...                                          │
│   }]                                             │
│ }                                                │
└─────────────────────────────────────────────────┘
                    ↓ (HTTP GET)
FRONTEND CLIENT
┌─────────────────────────────────────────────────┐
│ api_client.py:get_latest_server_metrics()        │
│ response.json() → List[Dict]                     │
│ [{"ram_percentage": 45, ...}]                    │
└─────────────────────────────────────────────────┘
                    ↓ (safe_create_dataframe)
DATA PROCESSING
┌─────────────────────────────────────────────────┐
│ data_processing.py:prepare_historical_dataframe()│
│ convert_numeric_columns(df, ["ram_percentage"]) │
│ validate_dataframe_range(df, "ram_percentage",  │
│                          0, 100, clip=True)     │
│ → DataFrame: ram_percentage column = 45.0 (float)
└─────────────────────────────────────────────────┘
                    ↓ (to_dict)
VALIDATION
┌─────────────────────────────────────────────────┐
│ validation.py:validate_server_metrics()          │
│ numeric_fields["ram_percentage"] = (0, 100)     │
│ → Validated: 45 is OK (0 <= 45 <= 100)          │
└─────────────────────────────────────────────────┘
                    ↓ (dict)
COMPONENTS
┌─────────────────────────────────────────────────┐
│ components.py generates HTML:                    │
│ <div>RAM: 45%</div>                              │
│ Applies CSS (if > 85: warning, if > 95: danger) │
└─────────────────────────────────────────────────┘
                    ↓
UI DISPLAY
┌─────────────────────────────────────────────────┐
│ Browser shows: RAM: 45%                          │
│ Color: Normal (performance_good color)           │
└─────────────────────────────────────────────────┘
```

---

## Where Schema is Currently Defined (Scattered)

```
mini_monitering.sh (line 44-47)
├─ CSV field order: architecture, os, pcpu, vcpu, ram_ratio, ram_perc, 
│  disk_ratio, disk_perc, cpu_load, last_boot, tcp, users, vnc, ssh
│  (16 fields output)
│
backend.py:parse_monitoring_data() (line 232)
├─ ( arch, os_info, pcpu, vcpu, ram_ratio, ram_perc, disk_ratio, disk_perc,
│   cpu_load_1min, cpu_load_5min, cpu_load_15min, last_boot, tcp, users, 
│   active_vnc_users, active_ssh_users ) = data.split(",")
│  (hardcoded field parsing)
│
backend.py:init_db() (line 41-63)
├─ CREATE TABLE server_metrics (
│   id, timestamp, server_name, architecture, operating_system, physical_cpus,
│   virtual_cpus, ram_used, ram_total, ram_percentage, disk_used, disk_total,
│   disk_percentage, cpu_load_1min, cpu_load_5min, cpu_load_15min, last_boot,
│   tcp_connections, logged_users, active_vnc_users, active_ssh_users
│  )
│
backend.py:store_metrics() (line 275-287)
├─ INSERT INTO server_metrics (
│   server_name, architecture, operating_system, physical_cpus, virtual_cpus,
│   ram_used, ram_total, ram_percentage, disk_used, disk_total, disk_percentage,
│   cpu_load_1min, cpu_load_5min, cpu_load_15min, last_boot, tcp_connections,
│   logged_users, active_vnc_users, active_ssh_users
│  ) VALUES (...)
│
api.py:get_latest_server_metrics() (line 99-102)
├─ SELECT sm.* FROM server_metrics sm ...
│ (returns all 19 columns)
│
api.py:get_historical_metrics() (line 137-139)
├─ SELECT timestamp, ram_percentage, disk_percentage, cpu_load_1min,
│        cpu_load_5min, cpu_load_15min, tcp_connections, logged_users
│ (returns 8 columns)
│
validation.py:validate_server_metrics() (line 173-181)
├─ numeric_fields = {
│   "cpu_load_1min": (0, 100),
│   "cpu_load_5min": (0, 100),
│   "cpu_load_15min": (0, 100),
│   "ram_percentage": (0, 100),
│   "disk_percentage": (0, 100),
│   "logged_users": (0, 10000),
│   "tcp_connections": (0, 100000),
│  }
│
data_processing.py:prepare_historical_dataframe() (line 163-170)
├─ numeric_columns = [
│   "cpu_load_1min", "cpu_load_5min", "cpu_load_15min",
│   "ram_percentage", "disk_percentage",
│   "logged_users", "tcp_connections"
│  ]
│
config.py:PERFORMANCE_THRESHOLDS (line 57-68)
├─ {
│   "cpu_warning": 50.0,
│   "cpu_critical": 80.0,
│   "memory_warning": 85,
│   "memory_critical": 95,
│   "disk_warning": 85,
│   "disk_critical": 95,
│   ...
│  }
```

Each time you add a field, you must update ALL these places.

---

## Problem Severity Matrix

| Problem | Severity | Impact |
|---------|----------|--------|
| No schema registry | CRITICAL | 10+ files must change per new metric |
| String storage (RAM/Disk) | HIGH | Can't aggregate, frontend must parse |
| Hardcoded field names | HIGH | Brittle, error-prone |
| Validation defined twice | MEDIUM | Easy to get out of sync |
| No type safety | MEDIUM | Runtime errors instead of compile-time |
| Scattered definitions | HIGH | Risk of inconsistencies |

---

## Recommendation Priority

**MUST DO (for maintainability)**:
1. Create centralized schema definitions (Python dataclasses)
2. Fix numeric storage (convert VARCHAR to NUMERIC)
3. Generate validation from schema

**SHOULD DO (for robustness)**:
4. Add migration for existing data
5. Implement typed API responses
6. Create field registry with metadata

**NICE TO HAVE (for developer experience)**:
7. Generate API documentation from schema
8. Add schema versioning/evolution tracking
9. Create type stubs for frontend

