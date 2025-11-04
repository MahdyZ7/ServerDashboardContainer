# Schema-Driven Architecture Migration Guide

## Overview

This guide walks you through migrating your current manually-synchronized codebase to a schema-driven architecture where a single YAML file drives all code generation.

**Time Estimate:** 1-2 days
**Risk Level:** Low (can run in parallel with existing code)
**Rollback:** Easy (keep old code until fully tested)

---

## Migration Strategy

We'll use a **gradual migration** approach:
1. Set up schema system alongside existing code
2. Generate code and test in isolation
3. Gradually replace manual code with generated code
4. Remove old code once verified

---

## Phase 1: Setup (2 hours)

### Step 1.1: Create Directory Structure

```bash
cd /home/ayassin/Developer/ServerDashboardContainer

# Create schema directories
mkdir -p schema/generators

# Create output directories for generated code
mkdir -p srcs/Backend/generated/models
mkdir -p srcs/Backend/migrations
mkdir -p srcs/DataCollection/generated
mkdir -p srcs/Frontend/generated
mkdir -p docs/generated

# Create backup of current code
git checkout -b backup/before-schema-migration
git commit -am "Backup before schema migration"
git checkout -b feature/schema-driven-architecture
```

### Step 1.2: Install Dependencies

```bash
# Backend dependencies (UV)
cd srcs/Backend
uv add pyyaml

# DataCollection dependencies (UV)
cd ../DataCollection
uv add pyyaml

# Frontend dependencies (UV)
cd ../Frontend
uv add pyyaml  # If needed for validation

cd ../..
```

### Step 1.3: Create Schema File

Copy the complete schema from `SCHEMA_DRIVEN_REFACTORING_PLAN.md` section "Create Central Schema File":

```bash
# Copy the metrics_schema.yaml content from the refactoring plan
# Save as: schema/metrics_schema.yaml
```

### Step 1.4: Create Generator Scripts

Create all generator files from the refactoring plan:

```bash
# Create these files with content from SCHEMA_DRIVEN_REFACTORING_PLAN.md:
# - schema/generators/generate_all.py
# - schema/generators/generate_sql.py
# - schema/generators/generate_python.py
# - schema/generators/generate_parsers.py
# - schema/generators/generate_validators.py
# - schema/generators/generate_typescript.py
# - schema/generators/generate_docs.py

# Make executable
chmod +x schema/generators/*.py
```

### Step 1.5: Validate Setup

```bash
cd schema/generators

# Test schema validation
python generate_all.py --validate-only

# Should output:
# ✅ Schema validation passed

# Show schema summary
python generate_all.py --summary

# Should show counts of fields, endpoints, etc.
```

---

## Phase 2: Generate Code (1 hour)

### Step 2.1: Generate All Code

```bash
cd schema/generators
python generate_all.py

# You should see:
# 📊 Generating SQL migration... ✅
# 🐍 Generating Python models... ✅
# 🔧 Generating parsers... ✅
# ✔️  Generating validators... ✅
# 📘 Generating TypeScript types... ✅
# 📚 Generating documentation... ✅
```

### Step 2.2: Review Generated Files

```bash
# Check generated files
tree srcs/Backend/generated/
tree srcs/DataCollection/generated/
tree srcs/Frontend/generated/
tree docs/generated/

# Review SQL migration
cat srcs/Backend/migrations/*_schema_migration.sql

# Review Python models
cat srcs/Backend/generated/models/server_metrics.py

# Review parsers
cat srcs/DataCollection/generated/bash_parser.py

# Review documentation
cat docs/generated/ADDING_METRICS_GUIDE.md
```

### Step 2.3: Test SQL Migration (Dry Run)

```bash
# Create test database
docker exec postgres psql -U postgres -c "CREATE DATABASE server_db_test;"

# Apply migration to test database
docker exec -i postgres psql -U postgres server_db_test < srcs/Backend/migrations/*_schema_migration.sql

# Verify tables created
docker exec postgres psql -U postgres server_db_test -c "\d server_metrics"
docker exec postgres psql -U postgres server_db_test -c "\d top_users"

# Check indexes
docker exec postgres psql -U postgres server_db_test -c "\di"

# If successful, drop test database
docker exec postgres psql -U postgres -c "DROP DATABASE server_db_test;"
```

---

## Phase 3: Backend Integration (3-4 hours)

### Step 3.1: Update DataCollection Service

**Current file:** `srcs/DataCollection/backend.py` (or equivalent)

**Find the parsing logic** (around lines 25-145):

```python
# OLD CODE (DON'T DELETE YET - comment out):
# def parse_monitoring_output(output):
#     parts = output.strip().split(',')
#     data = {
#         'architecture': parts[0] if len(parts) > 0 else None,
#         'os': parts[1] if len(parts) > 1 else None,
#         # ... many more lines ...
#     }
#     return data
```

**Add new code using generated parser:**

```python
# NEW CODE (ADD):
import sys
sys.path.append('/app/generated')  # Adjust path as needed
from bash_parser import parse_server_metrics, parse_top_users

def parse_monitoring_output_v2(output):
    """New parsing using generated code."""
    return parse_server_metrics(output)

def parse_top_users_output_v2(output):
    """New parsing using generated code."""
    return parse_top_users(output)
```

**Test both side-by-side:**

```python
# In your collection loop:
old_data = parse_monitoring_output(bash_output)  # Keep for comparison
new_data = parse_monitoring_output_v2(bash_output)  # Test generated code

# Log comparison
logger.info(f"Old parser: {old_data}")
logger.info(f"New parser: {new_data}")
logger.info(f"Match: {old_data == new_data}")
```

### Step 3.2: Update Database Insert Logic

**Find INSERT statement** (around lines 180-200):

```python
# OLD CODE (DON'T DELETE YET):
# cursor.execute("""
#     INSERT INTO server_metrics
#     (server_name, architecture, os, physical_cpus, ...)
#     VALUES (%s, %s, %s, %s, ...)
# """, (server_name, data['architecture'], data['os'], ...))
```

**Add new code using generated models:**

```python
# NEW CODE (ADD):
sys.path.append('/app/generated/models')
from server_metrics import ServerMetrics

def insert_metrics_v2(cursor, server_name, data):
    """New insert using generated model."""
    # Add server_name to data
    data['server_name'] = server_name

    # Create model instance
    metrics = ServerMetrics.from_dict(data)

    # Convert to dict for insert
    values = metrics.to_dict()

    # Build column list dynamically
    columns = ', '.join(values.keys())
    placeholders = ', '.join(['%s'] * len(values))

    query = f"""
        INSERT INTO server_metrics ({columns})
        VALUES ({placeholders})
    """

    cursor.execute(query, tuple(values.values()))
```

### Step 3.3: Test DataCollection

```bash
# Restart DataCollection service
make restart-service SERVICE=DataCollection

# Watch logs
make logs-DataCollection

# Should see:
# - Successful parsing with new parser
# - Successful inserts
# - No errors

# Verify data in database
docker exec postgres psql -U postgres server_db -c "SELECT * FROM server_metrics ORDER BY timestamp DESC LIMIT 1;"
```

---

## Phase 4: API Integration (2-3 hours)

### Step 4.1: Update API Models

**File:** `srcs/Backend/api.py`

**Add generated models:**

```python
# At top of file
import sys
sys.path.append('/app/generated/models')
from server_metrics import ServerMetrics
from top_users import TopUsers

# Use in endpoints
@app.route('/api/servers/metrics/latest')
def get_latest_metrics():
    cursor.execute("SELECT * FROM server_metrics WHERE ...")
    rows = cursor.fetchall()

    # Convert to models
    metrics = [ServerMetrics(*row).to_dict() for row in rows]

    return jsonify({
        'success': True,
        'data': metrics
    })
```

### Step 4.2: Test API

```bash
# Restart API service
make restart-service SERVICE=api

# Test endpoints
curl http://localhost:5000/api/servers/metrics/latest | jq

# Verify structure matches schema
curl http://localhost:5000/api/servers/Server1/metrics/historical/24 | jq

# Test all endpoints from API_DOCUMENTATION.md
```

---

## Phase 5: Frontend Integration (3-4 hours)

### Step 5.1: Update API Client

**File:** `srcs/Frontend/api_client.py`

```python
# Add generated validators
import sys
sys.path.append('/app/generated')
from validators import ServerMetricsValidator, ValidationError

class APIClient:
    def fetch_latest_metrics(self):
        response = self._request('/api/servers/metrics/latest')

        # Validate each metric
        validated_data = []
        for metric in response['data']:
            try:
                # Validate fields that have validators
                if 'ram_percentage' in metric:
                    metric['ram_percentage'] = ServerMetricsValidator.validate_ram_percentage(
                        metric['ram_percentage']
                    )
                # ... validate other fields ...

                validated_data.append(metric)
            except ValidationError as e:
                logger.warning(f"Validation error: {e}")
                # Use default or skip

        return validated_data
```

### Step 5.2: Test Frontend

```bash
# Restart Frontend
make restart-service SERVICE=Frontend

# Check logs for validation errors
make logs-Frontend

# Open browser
firefox http://localhost:3000

# Verify:
# - All data displays correctly
# - No validation errors in browser console
# - Graphs render properly
# - Auto-refresh works
```

---

## Phase 6: Cleanup (1-2 hours)

### Step 6.1: Remove Old Code

Once everything is verified working:

```python
# File: srcs/DataCollection/backend.py

# REMOVE old parser:
# def parse_monitoring_output(output): ...

# REMOVE old insert logic:
# cursor.execute("INSERT INTO server_metrics ...") ...

# RENAME _v2 functions:
parse_monitoring_output = parse_monitoring_output_v2
parse_top_users_output = parse_top_users_output_v2
```

### Step 6.2: Update Documentation

```bash
# Update CLAUDE.md
# - Add section on schema-driven architecture
# - Link to generated documentation
# - Update "Adding New Metrics" section

# Update README.md
# - Mention schema.yaml as source of truth
# - Add link to ADDING_METRICS_GUIDE.md

# Commit changes
git add .
git commit -m "Migrate to schema-driven architecture

- Add schema/metrics_schema.yaml as single source of truth
- Add code generators for SQL, Python, TypeScript, validators, parsers
- Replace manual parsing with generated code
- Replace manual validation with generated validators
- Add auto-generated documentation

Adding new metrics now requires:
1. Edit schema/metrics_schema.yaml
2. Run python schema/generators/generate_all.py
3. Apply migration and restart services

Benefits:
- 10+ files reduced to 1 file to edit
- 2-4 hours reduced to 15-30 minutes per metric
- Zero synchronization bugs
- Full type safety
- Auto-updated documentation"
```

---

## Phase 7: Testing & Validation (2-3 hours)

### Step 7.1: End-to-End Testing

```bash
# Test complete flow:

# 1. Add a test metric to schema
# Edit schema/metrics_schema.yaml, add:
- name: test_metric
  type: integer
  nullable: true
  bash_output: false  # We'll add manually to backend
  group: system_info
  description: "Test metric for validation"

# 2. Regenerate code
cd schema/generators
python generate_all.py

# 3. Apply migration
docker exec -i postgres psql -U postgres server_db < srcs/Backend/migrations/*_schema_migration.sql

# 4. Verify column added
docker exec postgres psql -U postgres server_db -c "\d server_metrics" | grep test_metric

# 5. Insert test data
docker exec postgres psql -U postgres server_db -c "INSERT INTO server_metrics (server_name, test_metric) VALUES ('TestServer', 42);"

# 6. Query via API
curl http://localhost:5000/api/servers/metrics/latest | jq '.data[] | select(.server_name=="TestServer") | .test_metric'

# 7. Clean up
docker exec postgres psql -U postgres server_db -c "DELETE FROM server_metrics WHERE server_name='TestServer';"
```

### Step 7.2: Load Testing

```bash
# Test performance impact

# Before optimization:
ab -n 100 -c 10 http://localhost:5000/api/servers/metrics/latest

# After optimization:
ab -n 100 -c 10 http://localhost:5000/api/servers/metrics/latest

# Compare response times
# Should be similar or better (generated code is optimized)
```

### Step 7.3: Validation Testing

```python
# Test file: srcs/Frontend/test_generated_validators.py

import pytest
from generated.validators import ServerMetricsValidator, ValidationError

def test_ram_percentage_valid():
    assert ServerMetricsValidator.validate_ram_percentage(50) == 50

def test_ram_percentage_invalid():
    with pytest.raises(ValidationError):
        ServerMetricsValidator.validate_ram_percentage(150)

def test_cpu_count_valid():
    assert ServerMetricsValidator.validate_physical_cpus(8) == 8

def test_cpu_count_invalid():
    with pytest.raises(ValidationError):
        ServerMetricsValidator.validate_physical_cpus(-1)
```

```bash
# Run tests
cd srcs/Frontend
pytest test_generated_validators.py -v
```

---

## Phase 8: Production Deployment (1 hour)

### Step 8.1: Pre-Deployment Checklist

- [ ] All tests passing
- [ ] End-to-end flow verified
- [ ] Performance acceptable
- [ ] Database backup created
- [ ] Rollback plan documented
- [ ] Team notified of changes

### Step 8.2: Backup Production

```bash
# Backup database
docker exec postgres pg_dump -U postgres server_db > backup_before_schema_$(date +%Y%m%d_%H%M%S).sql

# Backup current code
git tag v1.0-before-schema-migration
git push origin v1.0-before-schema-migration
```

### Step 8.3: Deploy

```bash
# Pull latest code
git pull origin feature/schema-driven-architecture

# Stop services
make down

# Apply database migration
docker compose up -d postgres
sleep 5
docker exec -i postgres psql -U postgres server_db < srcs/Backend/migrations/*_schema_migration.sql

# Start all services
make build
make up

# Monitor logs
make logs-follow

# Watch for errors (Ctrl+C to stop)
```

### Step 8.4: Post-Deployment Verification

```bash
# 1. Check all services running
make status

# 2. Check API health
curl http://localhost:5000/api/health

# 3. Check data collection
make logs-DataCollection | tail -20

# 4. Check frontend
curl -I http://localhost:3000

# 5. Manual testing
# - Open http://localhost:3000 in browser
# - Verify all metrics display
# - Check graphs update
# - Test different time ranges

# 6. Monitor for 15-30 minutes
# Watch logs for any errors
make logs-follow
```

---

## Rollback Procedure

If anything goes wrong:

### Quick Rollback (keeps data)

```bash
# 1. Stop services
make down

# 2. Checkout previous code
git checkout backup/before-schema-migration

# 3. Restart services
make build
make up

# Data is preserved in PostgreSQL volume
```

### Full Rollback (restores database)

```bash
# 1. Stop services
make down

# 2. Restore database
docker compose up -d postgres
docker exec -i postgres psql -U postgres -c "DROP DATABASE server_db;"
docker exec -i postgres psql -U postgres -c "CREATE DATABASE server_db;"
docker exec -i postgres psql -U postgres server_db < backup_before_schema_TIMESTAMP.sql

# 3. Checkout previous code
git checkout backup/before-schema-migration

# 4. Restart services
make build
make up
```

---

## Post-Migration: Adding Your First New Metric

Let's add swap memory as a real example:

### Step 1: Update Bash Script

```bash
# File: srcs/DataCollection/mini_monitering.sh
# Add after line 14 (after RAM section):

SWAP_DATA=$(free -m | grep Swap)
SWAP_USED=$(echo "$SWAP_DATA" | awk '{printf("%.2fG"), $3/1024.0}')
SWAP_TOTAL=$(echo "$SWAP_DATA" | awk '{printf("%.2fG"), $2/1024.0}')
SWAP_PERC=$(echo "$SWAP_DATA" | awk '{if($2>0) printf("%.0f"), $3 / $2 * 100; else print "0"}')

# Update line format output (line 45):
# Add: ,${SWAP_USED}/${SWAP_TOTAL},${SWAP_PERC}
```

### Step 2: Update Schema

```yaml
# File: schema/metrics_schema.yaml
# Add to server_metrics.fields:

    - name: swap_used
      type: varchar(20)
      nullable: true
      bash_output: true
      bash_index: 14
      bash_format: "part_before_slash"
      group: resources
      description: "Swap memory in use"
      frontend_display: "Swap Used"

    - name: swap_total
      type: varchar(20)
      nullable: true
      bash_output: true
      bash_index: 14
      bash_format: "part_after_slash"
      group: resources
      description: "Total swap memory"
      frontend_display: "Swap Total"

    - name: swap_percentage
      type: integer
      nullable: true
      bash_output: true
      bash_index: 15
      group: resources
      description: "Swap usage percentage"
      frontend_display: "Swap %"
      visualization:
        type: progress_bar
        thresholds:
          warning: 50
          critical: 75
      validation:
        type: percentage
        min: 0
        max: 100
```

### Step 3: Generate Code

```bash
cd schema/generators
python generate_all.py

# Output:
# 📊 Generating SQL migration... ✅
# 🐍 Generating Python models... ✅
# 🔧 Generating parsers... ✅
# ✔️  Generating validators... ✅
# 📘 Generating TypeScript types... ✅
# 📚 Generating documentation... ✅
```

### Step 4: Apply & Test

```bash
# Apply migration
docker exec -i postgres psql -U postgres server_db < srcs/Backend/migrations/*_schema_migration.sql

# Restart services
make restart

# Test
curl http://localhost:5000/api/servers/metrics/latest | jq '.[0].swap_percentage'

# Should return a number between 0-100
```

### Step 5: Add Frontend Display

```python
# File: srcs/Frontend/components.py

def create_swap_card(data):
    swap_perc = data.get('swap_percentage', 0)

    return dbc.Card([
        dbc.CardBody([
            html.H5("Swap Memory"),
            html.H3(f"{data.get('swap_used', 'N/A')}/{data.get('swap_total', 'N/A')}"),
            dbc.Progress(
                value=swap_perc,
                color="info" if swap_perc < 50 else "warning" if swap_perc < 75 else "danger"
            )
        ])
    ])
```

**Total time: 15-30 minutes!** (vs 2-4 hours before)

---

## Success Metrics

Track these metrics before and after migration:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Time to add metric | 2-4 hours | 15-30 min | <30 min |
| Files to edit | 10+ | 1 | 1 |
| Manual validation steps | 15+ | 1 | <5 |
| Bugs per metric added | 1-3 | 0 | 0 |
| Code generation time | N/A | ~30 sec | <1 min |
| Documentation currency | Often outdated | Always current | 100% |

---

## Troubleshooting

### Problem: Generated parser returns None

**Cause:** bash_index doesn't match actual CSV position

**Solution:**
```bash
./mini_monitering.sh --line-format | tr ',' '\n' | nl
# Check which line number your field appears on
# Update bash_index in schema accordingly
```

### Problem: Database migration fails

**Cause:** Column already exists or type mismatch

**Solution:**
```bash
# Check existing schema
docker exec postgres psql -U postgres server_db -c "\d server_metrics"

# Drop column if needed (DANGEROUS - backup first!)
# ALTER TABLE server_metrics DROP COLUMN column_name;

# Or modify migration to use ALTER instead of ADD
```

### Problem: Import errors for generated modules

**Cause:** Python path not set correctly

**Solution:**
```python
# Add to top of file:
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generated'))
```

### Problem: Frontend validation errors

**Cause:** Schema validation rules too strict for actual data

**Solution:**
```yaml
# Adjust validation ranges in schema:
validation:
  type: percentage
  min: 0
  max: 150  # Allow >100% if needed
```

---

## Resources

- **Schema File:** `schema/metrics_schema.yaml`
- **Generator Master:** `schema/generators/generate_all.py`
- **Generated Docs:** `docs/generated/`
- **Adding Metrics Guide:** `docs/generated/ADDING_METRICS_GUIDE.md`
- **Architecture Plan:** `SCHEMA_DRIVEN_REFACTORING_PLAN.md`

---

## Next Steps

1. Complete migration following this guide
2. Add your first new metric using schema-driven approach
3. Measure time savings
4. Train team on new workflow
5. Update onboarding docs
6. Consider extending to other parts of system (alerts, dashboards, reports)

---

**Questions?** See `SCHEMA_DRIVEN_REFACTORING_PLAN.md` for complete technical details.

**Migration Status Tracking:**
Create a file `MIGRATION_STATUS.md` to track progress through phases.