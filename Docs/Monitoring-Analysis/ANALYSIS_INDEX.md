# Project Structure & Schema Analysis - Complete Index

This directory contains comprehensive analysis of the Server Monitoring Dashboard's data flow and schema architecture.

## Documents Generated

### 1. **SUMMARY.md** (Quick Reference)
**Best for**: Getting oriented quickly, understanding the big picture
- 6KB document
- Key problems identified
- Critical interdependencies
- Recommendations summary
- Example: Adding a new metric requires changes in 10 places

**Read first if you have 5 minutes**

### 2. **data_flow_analysis.md** (Comprehensive Reference)
**Best for**: Deep understanding of every layer and component
- 21KB document  
- 13 sections with detailed specifications
- Complete database schema documentation
- All API endpoint structures
- Bash script output formats
- Data transformation pipeline
- Field range constraints and type conversions

**Read this for complete technical reference**

### 3. **ARCHITECTURE_VISUAL.md** (Visual & Diagrams)
**Best for**: Understanding system flow, visualizing data movement
- ASCII diagrams of system architecture
- Data flow through all 9 layers
- Single metric flow example (RAM percentage)
- Schema scattered across 7 files (visual tree)
- Problem severity matrix
- Recommendation priority levels

**Read this to see how pieces fit together**

---

## Quick Navigation

### Understanding the Problem

**Question**: "Where is schema defined?"
- Answer: SUMMARY.md (Table of 7 files) + ARCHITECTURE_VISUAL.md (visual tree)

**Question**: "What happens when I add a new metric?"
- Answer: SUMMARY.md (10-step process) + data_flow_analysis.md (section 12)

**Question**: "How does data flow from collection to UI?"
- Answer: ARCHITECTURE_VISUAL.md (system overview diagram)

**Question**: "What are the critical issues?"
- Answer: SUMMARY.md (Key Interdependencies section) + ARCHITECTURE_VISUAL.md (Problem Severity Matrix)

### Implementation Reference

**Question**: "What does server_metrics table look like?"
- Answer: data_flow_analysis.md (section 3.1)

**Question**: "What are all API endpoints?"
- Answer: data_flow_analysis.md (section 4)

**Question**: "What validation rules exist?"
- Answer: data_flow_analysis.md (section 7) + validation.py lines 163-180

**Question**: "What data processing happens?"
- Answer: data_flow_analysis.md (section 6)

---

## Key Findings

### The Core Problem
Schema definitions are **scattered across 7 different files**:
1. mini_monitering.sh - Bash script output format
2. TopUsers.sh - Bash script output format  
3. backend.py:parse_monitoring_data() - Parsing logic
4. backend.py:init_db() - Database schema (CREATE TABLE)
5. api.py - SELECT queries
6. validation.py - Numeric field ranges
7. data_processing.py - Column lists for processing

**Result**: Adding one new metric requires changes in 10+ places

### Three Critical Issues

1. **No Single Source of Truth**
   - Field definitions scattered across codebase
   - Easy to introduce inconsistencies
   - High maintenance burden

2. **String Storage for Numeric Values**
   - RAM/Disk stored as VARCHAR ("2.50G") not NUMERIC
   - Frontend must parse strings
   - Database can't perform calculations

3. **Hardcoded Field Names**
   - All field references are hardcoded strings
   - Changes break code in multiple places
   - No compile-time type checking

### Four Data Transformation Layers

```
Bash Scripts (CSV/space-separated)
    ↓ (string)
DataCollection Service (parses, creates dict)
    ↓ (dict)
PostgreSQL Database (stores structured)
    ↓ (query result)
Flask API (converts to JSON dict)
    ↓ (JSON)
Frontend API Client (retries, error handling)
    ↓ (dict)
Data Processing (DataFrame operations)
    ↓ (DataFrame)
Validation & Components (render UI)
    ↓
Browser Display
```

Each transformation is independent, no shared schema definition.

---

## File Structure in Project

```
ServerDashboardContainer/
├── srcs/
│   ├── DataCollection/
│   │   ├── backend.py                 ← Parsing logic + DB schema + storage
│   │   ├── mini_monitering.sh         ← System metrics collection
│   │   └── TopUsers.sh                ← User activity collection
│   │
│   ├── Backend/
│   │   └── api.py                     ← REST endpoints, SELECT queries
│   │
│   └── Frontend/
│       ├── api_client.py              ← HTTP calls with retry logic
│       ├── data_processing.py         ← DataFrame operations, hardcoded columns
│       ├── validation.py              ← Input validation, hardcoded ranges
│       ├── config.py                  ← Configuration constants
│       ├── exceptions.py              ← Exception hierarchy
│       └── components.py              ← UI component generators
│
├── data_flow_analysis.md              ← This analysis (detailed)
├── ARCHITECTURE_VISUAL.md             ← Visual diagrams
├── SUMMARY.md                         ← Quick reference
└── ANALYSIS_INDEX.md                  ← This file
```

---

## Critical Code Locations

### Data Collection
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py`
  - `parse_monitoring_data()` (lines 211-270) - Parses CSV
  - `parse_top_users()` (lines 184-208) - Parses user data
  - `init_db()` (lines 40-88) - Database schema
  - `store_metrics()` (lines 273-301) - Inserts metrics
  - `store_top_users()` (lines 304-354) - Upserts user data

### Database Schema
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/DataCollection/backend.py` (lines 40-81)
  - CREATE TABLE server_metrics (19 columns)
  - CREATE TABLE top_users (11 columns)

### API Endpoints
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Backend/api.py`
  - Lines 83-122: GET /api/servers/metrics/latest
  - Lines 125-169: GET /api/servers/<server>/metrics/historical/<hours>
  - Lines 172-207: GET /api/users/top
  - Lines 210-253: GET /api/users/top/<server>
  - Lines 285-342: GET /api/servers/<server>/status
  - Lines 345-468: GET /api/system/overview

### Frontend Data Processing
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/data_processing.py`
  - Lines 141-194: `prepare_historical_dataframe()` with hardcoded columns
  - Lines 163-170: Hardcoded numeric_columns list

### Frontend Validation  
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/validation.py`
  - Lines 144-199: `validate_server_metrics()` with hardcoded ranges
  - Lines 173-181: numeric_fields dict with ranges

### Configuration
- `/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend/config.py`
  - Lines 57-68: PERFORMANCE_THRESHOLDS (alert levels)

---

## Metrics & Fields Tracked

### Server Metrics (19 fields in database)
1. id - Record ID
2. timestamp - Collection time
3. server_name - Server identifier
4. architecture - CPU architecture
5. operating_system - OS name/version
6. physical_cpus - Physical CPU count
7. virtual_cpus - Virtual CPU count
8. ram_used - RAM used (string: "2.50G")
9. ram_total - RAM total (string: "16.00G")
10. ram_percentage - RAM utilization (0-100)
11. disk_used - Disk used (string: "100G")
12. disk_total - Disk total (string: "500G")
13. disk_percentage - Disk utilization (0-100)
14. cpu_load_1min - 1-minute load average
15. cpu_load_5min - 5-minute load average
16. cpu_load_15min - 15-minute load average
17. last_boot - Last boot timestamp
18. tcp_connections - Active TCP connections
19. logged_users - Logged-in user count

Plus frontend-calculated:
- active_vnc_users - Active VNC sessions
- active_ssh_users - Active SSH sessions

### User Metrics (11 fields in database)
1. id - Record ID
2. timestamp - Collection time
3. server_name - Server identifier
4. username - Username
5. cpu - CPU percentage
6. mem - Memory percentage
7. disk - Disk usage (GB)
8. process_count - Process count
9. top_process - Top consuming process name
10. last_login - Last login timestamp
11. full_name - User's full name

---

## Validation Rules Currently Enforced

### Numeric Field Ranges (from validation.py:173-181)
- cpu_load_1min: 0-100
- cpu_load_5min: 0-100
- cpu_load_15min: 0-100
- ram_percentage: 0-100
- disk_percentage: 0-100
- logged_users: 0-10000
- tcp_connections: 0-100000

### Performance Thresholds (from config.py:57-68)
- cpu_warning: 50.0%
- cpu_critical: 80.0%
- memory_warning: 85%
- memory_critical: 95%
- disk_warning: 85%
- disk_critical: 95%

### Data Processing Rules (from data_processing.py)
- Percentage columns: clipped to 0-100
- CPU load columns: validated to 0-1000 range
- Timestamp parsing: multiple format support
- Numeric conversion: with NaN handling (fill with 0.0)
- Anomaly detection: 3 standard deviation threshold

---

## Recommendations Summary

**High Priority (Maintainability)**:
1. Create centralized schema definitions (Python dataclasses or Pydantic)
2. Convert RAM/Disk to NUMERIC columns in database
3. Generate validation automatically from schema

**Medium Priority (Robustness)**:
4. Add database migration for existing data
5. Implement strongly-typed API responses
6. Create field metadata registry

**Nice to Have (Developer Experience)**:
7. Generate API documentation from schema
8. Add schema versioning and evolution tracking
9. Create TypeScript/type stub files for frontend

---

## How to Use This Analysis

### For Understanding the System
1. Start with **SUMMARY.md** (5-10 min read)
2. Review **ARCHITECTURE_VISUAL.md** diagrams
3. Deep-dive into **data_flow_analysis.md** as needed

### For Adding a New Metric
1. Identify all 7 schema definition locations
2. Check data_flow_analysis.md section 12 for step-by-step process
3. Cross-reference field names from ARCHITECTURE_VISUAL.md
4. Validate range constraints exist in all 4 places

### For Implementing Improvements
1. Review ARCHITECTURE_VISUAL.md "Problem Severity Matrix"
2. Check "Recommendation Priority" section
3. Use data_flow_analysis.md for exact code locations
4. Plan migrations using current schema in section 3

---

## Generated Date
November 4, 2024

## Files Analyzed
- srcs/DataCollection/backend.py (599 lines)
- srcs/DataCollection/mini_monitering.sh (64 lines)
- srcs/DataCollection/TopUsers.sh (109 lines)
- srcs/Backend/api.py (473 lines)
- srcs/Frontend/api_client.py (395 lines)
- srcs/Frontend/data_processing.py (369 lines)
- srcs/Frontend/validation.py (323 lines)
- srcs/Frontend/exceptions.py (64 lines)
- srcs/Frontend/config.py (127 lines)

Total: 2,523 lines analyzed

