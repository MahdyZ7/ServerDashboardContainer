# Absolute File Paths - All Analyzed Files

This document lists absolute paths to all files analyzed during the exploration.

## Analysis Documents Generated

All documents are located in the project root directory:

- `/home/ayassin/Developer/ServerDashboardContainer/SUMMARY.md`
- `/home/ayassin/Developer/ServerDashboardContainer/data_flow_analysis.md`
- `/home/ayassin/Developer/ServerDashboardContainer/ARCHITECTURE_VISUAL.md`
- `/home/ayassin/Developer/ServerDashboardContainer/ANALYSIS_INDEX.md`
- `/home/ayassin/Developer/ServerDashboardContainer/ABSOLUTE_FILE_PATHS.md` (this file)

## Source Code Files Analyzed

### DataCollection Service

**Backend Logic** (599 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py`
  - Contains: Database initialization, parsing functions, storage functions
  - Key functions:
    - Lines 211-270: `parse_monitoring_data()`
    - Lines 184-208: `parse_top_users()`
    - Lines 40-88: `init_db()`
    - Lines 273-301: `store_metrics()`
    - Lines 304-354: `store_top_users()`

**System Metrics Collection** (64 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/mini_monitering.sh`
  - Outputs CSV format: 16 fields
  - Called with `--line-format` flag

**User Activity Collection** (109 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/TopUsers.sh`
  - Outputs space-separated format
  - Called with `--no-headers` and optional `--collect-disk` flags

### Backend API Service

**REST Endpoints** (473 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Backend/api.py`
  - Contains: Flask routes for all API endpoints
  - Key endpoints:
    - Lines 83-122: GET /api/servers/metrics/latest
    - Lines 125-169: GET /api/servers/<server>/metrics/historical/<hours>
    - Lines 172-207: GET /api/users/top
    - Lines 210-253: GET /api/users/top/<server>
    - Lines 256-282: GET /api/servers/list
    - Lines 285-342: GET /api/servers/<server>/status
    - Lines 345-468: GET /api/system/overview

### Frontend Service

**API Client** (395 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/api_client.py`
  - Contains: HTTP request functions with retry logic
  - Implements: @retry_on_failure decorator, APIResult wrapper
  - Provides: get_latest_server_metrics(), get_top_users(), get_historical_metrics(), etc.

**Data Processing** (369 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/data_processing.py`
  - Contains: Safe DataFrame operations
  - Key functions:
    - Lines 141-194: `prepare_historical_dataframe()`
    - Lines 163-170: Hardcoded numeric_columns list
  - Provides: safe_create_dataframe(), validate_dataframe_range(), aggregate_metrics()

**Input Validation** (323 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/validation.py`
  - Contains: Input validation with type checking
  - Key validators:
    - Lines 144-199: `validate_server_metrics()`
    - Lines 173-181: numeric_fields dict with ranges
  - Provides: validate_percentage(), validate_server_name(), validate_timestamp()

**Exception Hierarchy** (64 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/exceptions.py`
  - Contains: Custom exception classes
  - Classes: DashboardException, APIConnectionError, APITimeoutError, ValidationError, etc.

**Configuration** (127 lines):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/config.py`
  - Contains: All configuration constants
  - Sections:
    - Lines 9-39: KU_COLORS (brand colors)
    - Lines 42-43: API_BASE_URL
    - Lines 45-54: DASHBOARD_CONFIG
    - Lines 57-68: PERFORMANCE_THRESHOLDS
    - Lines 71-81: CHART_CONFIG

## Related Configuration Files

**Docker Compose**:
- `/home/ayassin/Developer/ServerDashboardContainer/docker-compose.yml`

**Project Instructions**:
- `/home/ayassin/Developer/ServerDashboardContainer/CLAUDE.md`

## Directory Structure

```
/home/ayassin/Developer/ServerDashboardContainer/
├── srcs/
│   ├── DataCollection/
│   │   ├── backend.py                 ← ANALYZED
│   │   ├── mini_monitering.sh         ← ANALYZED
│   │   ├── TopUsers.sh                ← ANALYZED
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   │
│   ├── Backend/
│   │   ├── api.py                     ← ANALYZED
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   │
│   ├── Frontend/
│   │   ├── api_client.py              ← ANALYZED
│   │   ├── data_processing.py         ← ANALYZED
│   │   ├── validation.py              ← ANALYZED
│   │   ├── exceptions.py              ← ANALYZED
│   │   ├── config.py                  ← ANALYZED
│   │   ├── Dash.py
│   │   ├── components.py
│   │   ├── callbacks.py
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── uv.lock
│   │   ├── assets/
│   │   │   ├── styles.css
│   │   │   └── KU_logo.png
│   │   ├── tests/
│   │   │   ├── conftest.py
│   │   │   ├── test_validation.py
│   │   │   └── test_utils.py
│   │   └── requirements.txt
│   │
│   └── Nginx/
│
├── SUMMARY.md                         ← GENERATED
├── data_flow_analysis.md              ← GENERATED
├── ARCHITECTURE_VISUAL.md             ← GENERATED
├── ANALYSIS_INDEX.md                  ← GENERATED
├── ABSOLUTE_FILE_PATHS.md             ← GENERATED (this file)
│
├── CLAUDE.md
├── README.md
├── QUICK_REFERENCE.md
├── docker-compose.yml
└── Makefile
```

## Critical Code Locations by Function

### Data Collection and Parsing

**CSV Parsing** (mini_monitering.sh output):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py:211-270`
- Function: `parse_monitoring_data()`
- Input: 16 comma-separated CSV fields
- Output: Dict with 18 keys

**User Data Parsing** (TopUsers.sh output):
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py:184-208`
- Function: `parse_top_users()`
- Input: Space-separated lines
- Output: Dict with "top_users" list

### Database Operations

**Schema Definition**:
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py:40-88`
- Tables: server_metrics (19 columns), top_users (11 columns)

**Data Insertion**:
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py:273-301`
- Function: `store_metrics()`

**Data Upsert**:
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py:304-354`
- Function: `store_top_users()`
- Uses: ON CONFLICT ... DO UPDATE

### API Endpoints

All in `/home/ayassin/Developer/ServerDashboardContainer/srcs/Backend/api.py`:

1. **Latest Metrics** (lines 83-122)
   - Endpoint: GET /api/servers/metrics/latest
   - Returns: List of dicts with 19 fields

2. **Historical Metrics** (lines 125-169)
   - Endpoint: GET /api/servers/<server>/metrics/historical/<hours>
   - Returns: List of dicts with 8 fields (timestamp + 7 metrics)

3. **Top Users** (lines 172-207, 210-253)
   - Endpoints: GET /api/users/top, GET /api/users/top/<server>
   - Returns: List of dicts with 10 fields

4. **Server List** (lines 256-282)
   - Endpoint: GET /api/servers/list
   - Returns: List of strings

5. **Server Status** (lines 285-342)
   - Endpoint: GET /api/servers/<server>/status
   - Returns: Single dict with calculated "status" field

6. **System Overview** (lines 345-468)
   - Endpoint: GET /api/system/overview
   - Returns: Single dict with aggregated statistics

### Frontend Data Processing

**DataFrame Preparation**:
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/data_processing.py:141-194`
- Function: `prepare_historical_dataframe()`
- Hardcoded columns at lines 163-170

**Validation Rules**:
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/validation.py:144-199`
- Function: `validate_server_metrics()`
- Hardcoded ranges at lines 173-181

### Configuration Constants

All in `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/config.py`:

**Performance Thresholds** (lines 57-68):
- CPU, Memory, and Disk warning/critical levels

**Hardcoded Numeric Ranges**:
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/validation.py:173-181`
- Fields: cpu_load_*, ram_percentage, disk_percentage, logged_users, tcp_connections

## Total Lines Analyzed

- backend.py: 599 lines
- api.py: 473 lines
- api_client.py: 395 lines
- data_processing.py: 369 lines
- validation.py: 323 lines
- config.py: 127 lines
- exceptions.py: 64 lines
- mini_monitering.sh: 64 lines
- TopUsers.sh: 109 lines

**Total: 2,523 lines analyzed**

## How to Use These Paths

1. **For reading specific functions**:
   - Use the absolute paths with line numbers
   - Example: `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py:211-270`

2. **For understanding dependencies**:
   - Cross-reference between analysis documents and these paths
   - Locate exact code implementation

3. **For making changes**:
   - Identify all affected files using paths
   - Plan changes across multiple files
   - Ensure consistency

4. **For future developers**:
   - Use these paths to locate specific functionality
   - Reference in code review comments
   - Link to in documentation

