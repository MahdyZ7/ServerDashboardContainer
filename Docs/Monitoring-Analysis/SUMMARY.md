# Data Flow & Schema Architecture Summary

## Quick Overview

The Server Monitoring Dashboard has **9 distinct layers** where data transforms as it moves through the system:

1. **Bash Scripts** (remote servers) - Collect raw metrics
2. **DataCollection Service** - Parse and store metrics
3. **PostgreSQL Database** - Persist structured data
4. **Flask API** - Expose data via REST endpoints
5. **Frontend API Client** - Fetch with retry logic
6. **Data Processing** - Safe DataFrame operations
7. **Validation Layer** - Type checking and ranges
8. **Components** - Render visualizations
9. **User Interface** - Display dashboards

---

## Data Flow Summary

### Server Metrics Pipeline

```
mini_monitering.sh (CSV format)
    ↓
parse_monitoring_data() → Dict with 18 fields
    ↓
store_metrics() → PostgreSQL server_metrics table (19 columns)
    ↓
GET /api/servers/metrics/latest
    ↓
get_latest_server_metrics() in frontend
    ↓
prepare_historical_dataframe()
    ↓
Charts & Visualizations
```

### User Activity Pipeline

```
TopUsers.sh (space-separated format)
    ↓
parse_top_users() → Dict with list of user dicts
    ↓
store_top_users() → PostgreSQL top_users table (11 columns, ON CONFLICT)
    ↓
GET /api/users/top[/<server>]
    ↓
get_top_users() in frontend
    ↓
User Tables & Visualizations
```

---

## Critical Problem: No Single Source of Truth

Schema definitions are **scattered across 7 different files**:

| File | Contains | Type |
|------|----------|------|
| mini_monitering.sh | Output format (16 CSV fields) | Bash script |
| TopUsers.sh | Output format (8 space-separated fields) | Bash script |
| backend.py (lines 211-270) | Parsing logic (hardcoded split indices) | Python function |
| backend.py (lines 40-81) | Database schema (CREATE TABLE) | SQL DDL |
| api.py | SELECT queries (specific columns) | Python/SQL |
| validation.py (lines 163-180) | Numeric field ranges | Python dict |
| data_processing.py (lines 163-170) | Column lists for processing | Python list |

**Result**: Changes must be made in **multiple places**, creating:
- Risk of inconsistencies
- High maintenance burden
- Difficult to add new metrics
- Easy to make propagation errors

---

## Key Interdependencies

### 1. Bash Script Output → Parser Mismatch

**Problem**: If bash script output format changes:
- `parse_monitoring_data()` uses hardcoded split() at position 232
- Changes break parsing
- Database expectations differ from parser output

**Example**: mini_monitering.sh produces 16 fields, but parser creates dict with 18 fields (server_name added later)

### 2. String Storage for Numeric Values

**RAM/Disk stored as strings**: "2.50G", "100G", etc.
- Database: VARCHAR(30) instead of NUMERIC
- Parser: Returns strings
- API: Returns strings
- Frontend: Must parse strings again

**Impact**: Can't do calculations at database level, performance degradation

### 3. Hardcoded Column Names Throughout

**Example from data_processing.py line 163**:
```python
numeric_columns = [
    "cpu_load_1min",
    "cpu_load_5min", 
    "cpu_load_15min",
    "ram_percentage",
    "disk_percentage",
    "logged_users",
    "tcp_connections",
]
```

If these names change anywhere in the pipeline, frontend breaks.

### 4. Validation Logic Defined Twice

**validation.py** (lines 163-180):
```python
numeric_fields = {
    "cpu_load_1min": (0, 100),
    "cpu_load_5min": (0, 100),
    "cpu_load_15min": (0, 100),
    "ram_percentage": (0, 100),
    "disk_percentage": (0, 100),
    "logged_users": (0, 10000),
    "tcp_connections": (0, 100000),
}
```

**data_processing.py** (lines 163-170):
```python
numeric_columns = [
    "cpu_load_1min",
    "cpu_load_5min",
    "cpu_load_15min",
    "ram_percentage",
    "disk_percentage",
    "logged_users",
    "tcp_connections",
]
```

Same information defined twice, easy to get out of sync.

---

## What Happens When You Add a New Metric

To add "network_interface_errors" metric:

1. **mini_monitering.sh**: Add collection command + CSV output
2. **backend.py parse_monitoring_data()**: Update split() indices (line 232)
3. **backend.py CREATE TABLE**: Add column to server_metrics
4. **backend.py store_metrics()**: Add INSERT field
5. **api.py** (all 3-4 endpoints): Add to SELECT queries
6. **validation.py**: Add to numeric_fields dict
7. **data_processing.py**: Add to numeric_columns list + add range validation
8. **config.py**: Add PERFORMANCE_THRESHOLDS entry
9. **Components**: Update visualizations
10. **Tests**: Update test data fixtures

That's **10 places** to change for one new metric!

---

## Absolute File Paths (for Reference)

Key files explored:
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py`
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/mini_monitering.sh`
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/TopUsers.sh`
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Backend/api.py`
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/api_client.py`
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/data_processing.py`
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/validation.py`
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/exceptions.py`
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/config.py`

---

## Detailed Schema Documentation

**Full analysis**: See the comprehensive data flow document (`/tmp/data_flow_analysis.md`)

It includes:
- Complete database schema (server_metrics, top_users)
- All API endpoint structures
- Bash script output formats
- Parsing logic details
- Data transformation pipeline
- Hardcoded field lists throughout the codebase
- Field range constraints
- Type conversions
- Error handling patterns

---

## Recommendations Summary

1. **Create centralized schema definitions** (Python dataclasses or Pydantic models)
2. **Fix numeric storage** (convert RAM/Disk to NUMERIC in database)
3. **Generate validation from schema** (single source of truth)
4. **Create data migration** (backfill existing records)
5. **Implement typed API responses** (using schema models)
6. **Generate API documentation** (from schema)
7. **Create field registry** (metadata about each metric)

This would eliminate the 10-step process for adding metrics down to 2-3 steps.
