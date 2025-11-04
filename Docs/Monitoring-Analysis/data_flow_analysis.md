# Server Monitoring Dashboard - Data Flow & Schema Analysis

## Overview
This document maps the complete data flow from data collection through to frontend presentation, and identifies where schema/structure definitions currently reside.

---

## 1. DATA COLLECTION LAYER (srcs/DataCollection/)

### 1.1 Bash Scripts - Output Format Definition

**mini_monitering.sh** - System Metrics Collection
- **Output Mode**: CSV line format (when `--line-format` flag is used)
- **Output Format** (comma-separated, single line):
  ```
  ARCH,OS,PCPU,VCPU,RAM_USED/RAM_TOTAL,RAM_PERC,DISK_USED/DISK_TOTAL,DISK_PERC,CPU_LOAD_1,CPU_LOAD_5,CPU_LOAD_15,LAST_BOOT,TCP_CONNECTIONS,LOGGED_USERS,ACTIVE_VNC,ACTIVE_SSH
  ```
- **Example**:
  ```
  x86_64,Ubuntu 20.04,4,8,2.50G/16.00G,15,100G/500G,20%,1.25,1.50,1.75,2024-01-15 10:30,150,5,1,3
  ```
- **Field Mapping**:
  - Architecture: `uname -srvmo`
  - OS: `lsb_release`
  - CPU cores: `/proc/cpuinfo`
  - RAM: `free -m` (GB format)
  - Disk: `df -h` (human readable)
  - CPU Load: `/proc/loadavg` (3 values)
  - Last Boot: `who -b`
  - TCP Connections: `/proc/net/sockstat`
  - Users: `who` count
  - VNC/SSH: `lsof` count

**TopUsers.sh** - User Resource Usage Collection
- **Output Mode**: Space-separated, no headers (when `--no-headers` flag is used)
- **Output Format** (per user, one per line):
  ```
  USERNAME CPU MEM DISK PROCS TOP_PROCESS LAST_LOGIN FULLNAME
  ```
- **Example**:
  ```
  alice 5.25 12.50 nan 3 java_process 2024-01-15_10:30 Alice_Smith
  bob 2.15 8.75 OFF 2 python 2024-01-14_15:45 Bob_Johnson
  ```
- **Field Mapping**:
  - CPU: Aggregated from `ps` output
  - Memory: Aggregated from `ps` output
  - Disk: `du` command (can be OFF if not collected)
  - Processes: Count from `ps`
  - Top Process: Highest CPU consuming process
  - Last Login: `last` command
  - Full Name: `getent passwd` GECOS field

---

## 2. PARSING LAYER (backend.py - DataCollection Service)

### 2.1 Parse Monitoring Data Function

**Location**: `DataCollection/backend.py:211-270`

**Function**: `parse_monitoring_data(data: str) -> Dict`

**Input**: CSV string from mini_monitering.sh

**Output Dictionary**:
```python
{
    "architecture": str,
    "operating_system": str,
    "physical_cpus": int,
    "virtual_cpus": int,
    "ram_used": str,           # e.g., "2.50G"
    "ram_total": str,          # e.g., "16.00G"
    "ram_percentage": int,     # 0-100
    "disk_used": str,          # e.g., "100G"
    "disk_total": str,         # e.g., "500G"
    "disk_percentage": int,    # 0-100
    "cpu_load_1min": float,    # e.g., 1.25
    "cpu_load_5min": float,
    "cpu_load_15min": float,
    "last_boot": str,          # date format
    "tcp_connections": int,
    "logged_users": int,
    "active_vnc_users": int,
    "active_ssh_users": int,
}
```

### 2.2 Parse Top Users Function

**Location**: `DataCollection/backend.py:184-208`

**Function**: `parse_top_users(data: str) -> Dict`

**Input**: Space-separated lines from TopUsers.sh

**Output Dictionary**:
```python
{
    "top_users": [
        {
            "user": str,
            "cpu": float,
            "mem": float,
            "disk": float,                    # 0 if "nan" or "OFF"
            "process_count": int,
            "top_process": str or None,       # None if "nan"
            "last_login": str,
            "full_name": str or None,         # None if "nan"
        },
        # ... more users
    ]
}
```

---

## 3. DATABASE LAYER (PostgreSQL Schema)

### 3.1 Table: server_metrics

**Location**: `DataCollection/backend.py:40-64`

**Schema**:
```sql
CREATE TABLE IF NOT EXISTS server_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    server_name VARCHAR(255),
    
    -- System Info
    architecture VARCHAR(255),
    operating_system VARCHAR(255),
    physical_cpus INT,
    virtual_cpus INT,
    
    -- RAM (stored as strings: "2.50G", etc)
    ram_used VARCHAR(30),
    ram_total VARCHAR(30),
    ram_percentage INT,
    
    -- Disk (stored as strings: "100G", etc)
    disk_used VARCHAR(30),
    disk_total VARCHAR(30),
    disk_percentage INT,
    
    -- CPU Load (3 separate fields)
    cpu_load_1min DECIMAL(5,2),
    cpu_load_5min DECIMAL(5,2),
    cpu_load_15min DECIMAL(5,2),
    
    -- System State
    last_boot VARCHAR(255),
    tcp_connections INT,
    logged_users INT,
    active_vnc_users INT,
    active_ssh_users INT
);
```

**Important Notes**:
- RAM/Disk are stored as strings (e.g., "2.50G") rather than numeric values
- No conversion to standard units (GB, MB) happens at database level
- Timestamps are auto-generated

### 3.2 Table: top_users

**Location**: `DataCollection/backend.py:66-81`

**Schema**:
```sql
CREATE TABLE IF NOT EXISTS top_users (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    server_name VARCHAR(255),
    username VARCHAR(255),
    cpu DECIMAL(5,2),
    mem DECIMAL(5,2),
    disk DECIMAL(5,2) DEFAULT 0,
    process_count INT DEFAULT 0,
    top_process VARCHAR(255) DEFAULT NULL,
    last_login TIMESTAMP DEFAULT NULL,
    full_name VARCHAR(255) DEFAULT NULL,
    UNIQUE (server_name, username)
);
```

**Important Notes**:
- Uses UNIQUE constraint on (server_name, username) pair
- Uses ON CONFLICT to update existing user records
- Disk field is optional (defaults to 0)
- Last login stored as TIMESTAMP, not string

---

## 4. API LAYER (srcs/Backend/api.py)

### 4.1 API Response Format

All endpoints follow a consistent JSON response format:
```json
{
    "success": true,
    "data": [],  // or {} for single object
    "count": 5,
    "message": "Optional message"
}
```

### 4.2 Endpoint: GET /api/servers/metrics/latest

**Returns**: Latest metrics for all servers

**Response Data** (list of objects):
```json
{
    "id": 12345,
    "timestamp": "2024-01-15T10:30:00",
    "server_name": "server1",
    "architecture": "x86_64",
    "operating_system": "Ubuntu 20.04",
    "physical_cpus": 4,
    "virtual_cpus": 8,
    "ram_used": "2.50G",
    "ram_total": "16.00G",
    "ram_percentage": 15,
    "disk_used": "100G",
    "disk_total": "500G",
    "disk_percentage": 20,
    "cpu_load_1min": 1.25,
    "cpu_load_5min": 1.50,
    "cpu_load_15min": 1.75,
    "last_boot": "2024-01-15 10:30",
    "tcp_connections": 150,
    "logged_users": 5,
    "active_vnc_users": 1,
    "active_ssh_users": 3
}
```

**Code Location**: `api.py:83-122`

### 4.3 Endpoint: GET /api/servers/<server>/metrics/historical/<hours>

**Returns**: Historical metrics for a server (time range in hours)

**Response Data** (list of objects):
```json
{
    "timestamp": "2024-01-15T10:30:00",
    "ram_percentage": 15,
    "disk_percentage": 20,
    "cpu_load_1min": 1.25,
    "cpu_load_5min": 1.50,
    "cpu_load_15min": 1.75,
    "tcp_connections": 150,
    "logged_users": 5
}
```

**Code Location**: `api.py:125-169`

### 4.4 Endpoint: GET /api/users/top

**Returns**: Top users from all servers

**Response Data** (list of objects):
```json
{
    "server_name": "server1",
    "username": "alice",
    "cpu": 5.25,
    "mem": 12.50,
    "disk": 0,
    "process_count": 3,
    "top_process": "java_process",
    "last_login": "2024-01-15T10:30:00",
    "full_name": "Alice_Smith",
    "timestamp": "2024-01-15T10:30:00"
}
```

**Code Location**: `api.py:172-207`

### 4.5 Endpoint: GET /api/users/top/<server>

**Returns**: Top users for specific server

**Response Data**: Same as above but filtered by server

**Code Location**: `api.py:210-253`

### 4.6 Endpoint: GET /api/servers/list

**Returns**: List of all server names

**Response Data** (list of strings):
```json
["server1", "server2", "server3"]
```

**Code Location**: `api.py:256-282`

### 4.7 Endpoint: GET /api/servers/<server>/status

**Returns**: Current status of a server with calculated status field

**Response Data** (single object):
```json
{
    "id": 12345,
    "timestamp": "2024-01-15T10:30:00",
    "server_name": "server1",
    // ... all fields from server_metrics ...
    "status": "online"  // Added field: "online", "warning", or "offline"
}
```

**Status Logic**:
- "warning": if ram_percentage > 90 OR disk_percentage > 90 OR cpu_load_5min > 5
- "offline": if timestamp > 15 minutes old
- "online": otherwise

**Code Location**: `api.py:285-342`

### 4.8 Endpoint: GET /api/system/overview

**Returns**: Aggregated system statistics

**Response Data** (single object):
```json
{
    "total_servers": 7,
    "online_servers": 6,
    "warning_servers": 1,
    "offline_servers": 0,
    "avg_cpu_load": 2.5,
    "avg_ram_usage": 45.3,
    "avg_disk_usage": 62.1,
    "total_active_users": 12,
    "uptime_percentage": 85.7,
    "trends": {
        "servers": "stable",  // or "up", "down"
        "cpu": "stable",
        "ram": "stable"
    }
}
```

**Code Location**: `api.py:345-468`

---

## 5. FRONTEND API CLIENT LAYER (srcs/Frontend/api_client.py)

### 5.1 API Result Wrapper

**Class**: `APIResult` (lines 26-41)

Wraps API responses with success/error information:
```python
APIResult(
    success: bool,
    data: Any = None,
    error: Optional[Exception] = None
)
```

### 5.2 API Client Functions

All functions follow the pattern:
```python
@retry_on_failure()
def get_<resource>() -> List[Dict]:
    success, data, error = _make_api_request("/endpoint")
    if success and isinstance(data, list):
        return data
    else:
        return []  # Empty list on error
```

**Available Functions**:
- `get_latest_server_metrics()` -> List[Dict]
- `get_top_users()` -> List[Dict]
- `get_historical_metrics(server_name, hours=24)` -> List[Dict]
- `get_server_status(server_name)` -> Dict
- `get_server_health(server_name)` -> Dict
- `get_server_list()` -> List[str]
- `get_top_users_by_server(server_name)` -> List[Dict]
- `get_system_overview()` -> Dict
- `check_api_health()` -> bool

**Retry Logic**:
- Maximum 3 retries with exponential backoff (2^attempt seconds)
- Only retries on `APIConnectionError` and `APITimeoutError`
- Default timeout: 10 seconds

**Code Location**: `api_client.py:193-394`

---

## 6. DATA PROCESSING LAYER (srcs/Frontend/data_processing.py)

### 6.1 Data Processing Functions

**Purpose**: Safe, error-handled DataFrame operations with validation

**Key Functions**:

1. **safe_create_dataframe(data, name)** -> pd.DataFrame
   - Converts list of dicts to DataFrame
   - Returns empty DataFrame on error

2. **parse_dataframe_timestamps(df, column)** -> pd.DataFrame
   - Parses timestamp columns
   - Handles coercion with error logging

3. **convert_numeric_columns(df, columns)** -> pd.DataFrame
   - Converts specific columns to numeric
   - Fills NaN with default value (0.0)

4. **validate_dataframe_range(df, column, min, max)** -> pd.DataFrame
   - Validates values are within range
   - Can clip values to range

5. **prepare_historical_dataframe(data, server_name)** -> pd.DataFrame
   - Complete pipeline for historical data:
     - Parse timestamps
     - Convert numeric columns
     - Validate ranges
     - Sort by timestamp
   - Numeric columns: cpu_load_1min, cpu_load_5min, cpu_load_15min, ram_percentage, disk_percentage, logged_users, tcp_connections
   - Percentage columns clipped to 0-100
   - CPU load validated to 0-1000

6. **aggregate_metrics(metrics_list, operation)** -> Dict
   - Aggregates metrics across servers
   - Operations: mean, sum, max, min

7. **filter_recent_data(df, timestamp_column, hours)** -> pd.DataFrame
   - Filters to last N hours

8. **calculate_trends(df, column, window)** -> str
   - Returns: "increasing", "decreasing", or "stable"

9. **detect_anomalies(df, column, threshold_std)** -> pd.Series
   - Uses standard deviation detection

**Code Location**: `data_processing.py:1-369`

---

## 7. VALIDATION LAYER (srcs/Frontend/validation.py)

### 7.1 Validation Functions

**Purpose**: Input validation with type checking and range validation

**Key Validators**:

1. **validate_percentage(value, field_name)** -> float
   - Range: 0-100

2. **validate_positive_number(value, field_name)** -> float
   - Range: >= 0

3. **validate_server_name(server_name)** -> str
   - Max length: 255
   - Strips whitespace
   - Must be non-empty string

4. **validate_time_range(hours)** -> int
   - Range: 1 to 8760 (1 year)

5. **validate_server_metrics(metrics)** -> Dict
   - Required fields: server_name
   - Numeric fields with ranges:
     - cpu_load_1min: 0-100
     - cpu_load_5min: 0-100
     - cpu_load_15min: 0-100
     - ram_percentage: 0-100
     - disk_percentage: 0-100
     - logged_users: 0-10000
     - tcp_connections: 0-100000

6. **validate_user_data(user)** -> Dict
   - Required fields: username
   - Numeric fields: cpu, mem, disk

7. **validate_timestamp(timestamp)** -> datetime
   - Supports multiple formats
   - Handles ISO format with timezone

**Code Location**: `validation.py:1-323`

---

## 8. EXCEPTION HIERARCHY (srcs/Frontend/exceptions.py)

**Base Exception**: `DashboardException`

**API Exceptions**:
- `APIConnectionError` - Network/connection issues
- `APITimeoutError` - Request timeout
- `APIResponseError` - API returned error response
- `APIDataError` - Invalid/unexpected response data

**Domain Exceptions**:
- `DataProcessingError` - DataFrame/data manipulation errors
- `ValidationError` - Input validation failures
- `ConfigurationError` - Configuration issues

**Code Location**: `exceptions.py:1-64`

---

## 9. CURRENT STATE ANALYSIS

### 9.1 Where Schema/Structure is Currently Defined

| Component | Location | Type | Format |
|-----------|----------|------|--------|
| Bash Output Format | mini_monitering.sh, TopUsers.sh | Shell Scripts | CSV/Space-separated |
| Python Parsing | backend.py (parse_* functions) | Python (Dict return types) | Hardcoded field names |
| Database Schema | backend.py (CREATE TABLE) | SQL DDL | Raw SQL strings |
| API Response | api.py (endpoints) | Python/JSON | Query result -> dict conversion |
| Frontend Validation | validation.py | Python functions | Hardcoded field names & ranges |
| Data Processing | data_processing.py | Python (column lists) | Hardcoded column lists |
| Configuration | config.py | Python dict | Hardcoded constants |

### 9.2 Schema Definition Problems

1. **No Single Source of Truth**: Schema defined in multiple places:
   - SQL in backend.py
   - Python parsing logic in backend.py
   - Field lists in validation.py (lines 163-180)
   - Column lists in data_processing.py (lines 163-170)
   - API queries in api.py

2. **String Storage**: RAM/Disk stored as strings ("2.50G") instead of numeric values
   - No conversion to standard units
   - Makes calculations difficult
   - Frontend must parse strings again

3. **Hardcoded Field Names**: All field references are hardcoded strings
   - No type safety
   - Changes require updates in multiple files
   - Prone to inconsistencies

4. **No Formal Type Definitions**: 
   - No Python dataclasses/TypedDict
   - No JSON Schema
   - No OpenAPI/Swagger documentation

5. **Parser-Database Mismatch**: 
   - Parser produces python dicts
   - Database schema doesn't match field names exactly
   - Manual mapping required in store_metrics/store_top_users

---

## 10. DATA FLOW DIAGRAM

```
BASH SCRIPTS (on remote servers)
│
├─> mini_monitering.sh (--line-format)
│   Output: CSV string with 16 comma-separated fields
│
├─> TopUsers.sh (--no-headers)
│   Output: Space-separated lines, one user per line
│
↓ (SSH via BashGetInfo.sh)

DATACOLLECTION SERVICE
│
├─> run_monitoring_script()
│   Returns: CSV string
│   ↓
│   parse_monitoring_data()
│   Returns: Dict with ~18 fields
│   ↓
│   store_metrics()
│   Inserts into server_metrics table
│
├─> get_top_users()
│   Returns: Dict with "top_users" list
│   ↓
│   parse_top_users()
│   Returns: Dict with list of dicts
│   ↓
│   store_top_users()
│   Upserts into top_users table (ON CONFLICT)
│
↓

POSTGRESQL DATABASE
│
├─> server_metrics table (19 columns)
│   - id, timestamp, server_name
│   - architecture, operating_system
│   - physical_cpus, virtual_cpus
│   - ram_used, ram_total, ram_percentage
│   - disk_used, disk_total, disk_percentage
│   - cpu_load_1min, cpu_load_5min, cpu_load_15min
│   - last_boot, tcp_connections, logged_users
│   - active_vnc_users, active_ssh_users
│
├─> top_users table (11 columns)
│   - id, timestamp, server_name, username
│   - cpu, mem, disk, process_count
│   - top_process, last_login, full_name
│
↓

FLASK API (Backend)
│
GET /api/servers/metrics/latest
├─> Query: latest record per server
│   Returns: List of dicts (all 19 fields)
│
GET /api/servers/<server>/metrics/historical/<hours>
├─> Query: Last N hours of specific columns
│   Returns: List of dicts (8 fields: timestamp + 7 metrics)
│
GET /api/users/top[/<server>]
├─> Query: All users or by server
│   Returns: List of dicts (10 fields)
│
GET /api/servers/list
├─> Query: Distinct server names
│   Returns: List of strings
│
GET /api/servers/<server>/status
├─> Query: Latest record + calculated status
│   Returns: Single dict (19 fields + "status")
│
GET /api/system/overview
├─> Query: Multiple aggregations
│   Returns: Single dict (12 fields)
│
↓

FRONTEND API CLIENT
│
@retry_on_failure() decorator
├─> _make_api_request()
│   - Validates response.success
│   - Validates response structure (dict vs list)
│   - Returns (success, data, error) tuple
│
├─> get_latest_server_metrics() -> List[Dict]
├─> get_top_users() -> List[Dict]
├─> get_historical_metrics(server, hours) -> List[Dict]
├─> get_server_status(server) -> Dict
├─> get_server_list() -> List[str]
├─> etc.
│
↓

DATA PROCESSING & VALIDATION
│
├─> safe_create_dataframe() -> DataFrame
├─> prepare_historical_dataframe() -> DataFrame
│   - parse timestamps
│   - convert numeric columns (7 hardcoded column names)
│   - validate ranges (0-100 for %, 0-1000 for CPU load)
│   - sort by timestamp
│
├─> validate_server_metrics()
│   - Check server_name present
│   - Validate numeric field ranges
│
├─> validate_user_data()
│   - Check username present
│   - Convert cpu, mem, disk to numeric
│
├─> aggregate_metrics()
│   - mean/sum/max/min across servers
│
↓

FRONTEND COMPONENTS & DISPLAY
│
├─> Server cards (latest metrics)
├─> Historical charts (time series)
├─> User table (top users per server)
├─> System overview (aggregated stats)
├─> Server status indicators
```

---

## 11. KEY INTERDEPENDENCIES

### Critical Field Dependencies

**1. Server Metrics Flow**:
```
mini_monitering.sh fields → parse_monitoring_data() dict → server_metrics table → API response
```

If bash script changes output format:
1. parse_monitoring_data() split() call fails (line 232)
2. Field mapping in parse_monitoring_data() needs updates
3. Database columns must match (19 columns)
4. API queries select specific columns
5. Frontend assumes certain fields exist

**2. User Data Flow**:
```
TopUsers.sh fields → parse_top_users() dict → top_users table → API response
```

Similar dependencies but with on-conflict update logic.

**3. Frontend Processing**:
```
API response List[Dict] → safe_create_dataframe() → prepare_historical_dataframe()
                          ↓
                    validate_dataframe_range() on hardcoded columns
```

Hardcoded column names in prepare_historical_dataframe (lines 163-170):
- cpu_load_1min, cpu_load_5min, cpu_load_15min
- ram_percentage, disk_percentage
- logged_users, tcp_connections

If API response changes field names, DataFrame processing breaks.

---

## 12. CHANGE PROPAGATION REQUIREMENTS

To add a new field (e.g., "network_in_bytes"):

1. **Bash Script**: Add collection logic to mini_monitering.sh
2. **Bash Output**: Add to CSV line format
3. **Parser**: Update parse_monitoring_data() split() and dict
4. **Database**: Add column to server_metrics table
5. **API**: Add to SELECT queries in endpoints
6. **Validation**: Add to validate_server_metrics() numeric_fields
7. **Data Processing**: Add to prepare_historical_dataframe() numeric_columns list
8. **Components**: Update visualizations
9. **Config**: Add thresholds if applicable

Each change is manual and error-prone without a centralized schema.

---

## 13. RECOMMENDATIONS FOR IMPROVEMENT

See IMPROVEMENT_PROPOSAL.md for a comprehensive schema management strategy.

Key areas:
1. Create centralized schema definitions (Python dataclasses or Pydantic)
2. Convert numeric fields to proper types in database
3. Generate type hints and validation from single source
4. Implement strongly-typed API responses
5. Create data migration strategy for existing fields
