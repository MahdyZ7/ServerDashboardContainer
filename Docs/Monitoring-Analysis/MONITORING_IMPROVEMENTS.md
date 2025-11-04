# Monitoring Scripts Improvement Plan

## Overview
This document outlines improvements to the monitoring scripts (`mini_monitering.sh` and `TopUsers.sh`) and provides step-by-step integration instructions for the entire project.

---

## Critical Fixes (Must Do)

### 1. Fix Syntax Error in mini_monitering.sh
**Location:** `mini_monitering.sh:3-6`

**Current Code:**
```bash
ARCH=$(uname -srvmo) || "Unknown"
OS_NAME=$(lsb_release -i | awk '{print $3}') || "Unknown OS"
OS_VER=$(lsb_release -r | awk '{print $2}') || "Unknown Version"
```

**Problem:** The `|| "Unknown"` syntax doesn't work as intended in bash command substitution.

**Fix:**
```bash
ARCH=$(uname -srvmo 2>/dev/null || echo "Unknown")
OS_NAME=$(lsb_release -i 2>/dev/null | awk '{print $3}' || echo "Unknown OS")
OS_VER=$(lsb_release -r 2>/dev/null | awk '{print $2}' || echo "Unknown Version")
```

**Integration Steps:**
1. Edit `srcs/DataCollection/mini_monitering.sh` lines 3-6
2. Test locally: `./mini_monitering.sh`
3. Test with line format: `./mini_monitering.sh --line-format`
4. No backend/frontend changes needed (output format unchanged)

---

### 2. Optimize find Command Order in TopUsers.sh
**Location:** `TopUsers.sh:6`

**Current Code:**
```bash
files=$(find /eda_work/ -user "$1" -maxdepth 1 2> /dev/null)
```

**Problem:** `-maxdepth` should come before other options for efficiency.

**Fix:**
```bash
files=$(find /eda_work/ -maxdepth 1 -user "$1" 2> /dev/null)
```

**Integration Steps:**
1. Edit `srcs/DataCollection/TopUsers.sh` line 6
2. Also fix line 10 (duplicate find command)
3. Test: `./TopUsers.sh`
4. No backend/frontend changes needed

---

### 3. Remove Redundant find Call in TopUsers.sh
**Location:** `TopUsers.sh:10`

**Current Code:**
```bash
du -scb /home/$1 $(find /eda_work/ -user "$1" -maxdepth 1 2> /dev/null) 2> /dev/null | tail -1
```

**Problem:** The find command is called twice (lines 6 and 10).

**Fix:**
```bash
# Use the $files variable already computed
du -scb /home/$1 $files 2> /dev/null | tail -1 | awk '{printf("%.2f"), $1/1024/1024/1024}'
```

**Integration Steps:**
1. Edit `srcs/DataCollection/TopUsers.sh` line 10
2. Ensure `$files` variable is properly expanded
3. Test disk collection: `./TopUsers.sh --collect-disk`

---

## High Priority Additions

### 4. Add Swap Memory Monitoring
**Location:** `mini_monitering.sh` (after RAM section)

**Add After Line 14:**
```bash
SWAP_DATA=$(free -m | grep Swap)
SWAP_TOTAL=$(echo "$SWAP_DATA" | awk '{printf("%.2fG"), $2/1024.0}')
SWAP_USED=$(echo "$SWAP_DATA" | awk '{printf("%.2fG"), $3/1024.0}')
SWAP_PERC=$(echo "$SWAP_DATA" | awk '{if($2>0) printf("%.0f"), $3 / $2 * 100; else print "0"}')
```

**Update Line Format Output (line 45-47):**
```bash
printf "${ARCH},${OS},${PCPU},${VCPU},${RAM_USED}/${RAM_TOTAL},${RAM_PERC},\
${SWAP_USED}/${SWAP_TOTAL},${SWAP_PERC},\
${DISK_USED}/${DISK_TOTAL},${DISK_PERC},${CPU_LOAD},${LAST_BOOT},\
${TCP},${USER_LOG},${ACTIVE_VNC},${ACTIVE_SSH}\n"
```

**Update Human-Readable Output (after line 53):**
```bash
printf "%-25s: %s/%s (%.0f%%)\n" "Swap" "${SWAP_USED}" "${SWAP_TOTAL}" "${SWAP_PERC}"
```

**Integration Steps:**
1. Update `mini_monitering.sh` with new SWAP variables
2. Update DataCollection parser in `srcs/DataCollection/BashGetInfo.py` or equivalent
3. Update database schema to include swap columns:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN swap_used VARCHAR(20);
   ALTER TABLE server_metrics ADD COLUMN swap_total VARCHAR(20);
   ALTER TABLE server_metrics ADD COLUMN swap_percentage INTEGER;
   ```
4. Update API response in `srcs/Backend/api.py` to include swap data
5. Update Frontend components to display swap metrics
6. Test end-to-end data flow

---

### 5. Add Network I/O Statistics
**Location:** `mini_monitering.sh` (after TCP connections section)

**Add After Line 24:**
```bash
# Network statistics (total bytes since boot)
NET_RX=$(cat /sys/class/net/*/statistics/rx_bytes 2>/dev/null | awk '{sum+=$1} END {printf("%.2f"), sum/1024/1024/1024}')
NET_TX=$(cat /sys/class/net/*/statistics/tx_bytes 2>/dev/null | awk '{sum+=$1} END {printf("%.2f"), sum/1024/1024/1024}')
# Or if you want rates (requires saving previous values)
```

**Update Outputs:**
```bash
# Line format (add to printf)
,${NET_RX},${NET_TX}

# Human-readable format
printf "%-25s: %s GB / %s GB\n" "Network RX/TX" "${NET_RX}" "${NET_TX}"
```

**Integration Steps:**
1. Add network variables to `mini_monitering.sh`
2. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN net_rx_gb DECIMAL(10,2);
   ALTER TABLE server_metrics ADD COLUMN net_tx_gb DECIMAL(10,2);
   ```
3. Update DataCollection parser to extract network data
4. Update API to include network stats
5. Add network graph to Frontend dashboard
6. Consider calculating rates (GB/hour) in Frontend using historical data

---

### 6. Add Disk I/O Statistics
**Location:** `mini_monitering.sh` (requires `iostat` or sysfs)

**Add After Line 19:**
```bash
# Disk I/O (reads and writes per second - snapshot)
if command -v iostat &> /dev/null; then
    DISK_IO=$(iostat -x 1 2 | awk '/^[sv]d/ {sum+=$4+$5} END {printf("%.2f"), sum}')
else
    # Fallback to /proc/diskstats (more complex parsing)
    DISK_IO="N/A"
fi
```

**Alternative (Cumulative Disk I/O):**
```bash
# Total sectors read/written since boot
DISK_READ=$(awk '{sum+=$6} END {printf("%.2f"), sum*512/1024/1024/1024}' /proc/diskstats)
DISK_WRITE=$(awk '{sum+=$10} END {printf("%.2f"), sum*512/1024/1024/1024}' /proc/diskstats)
```

**Integration Steps:**
1. Choose approach (rate vs cumulative)
2. Update `mini_monitering.sh`
3. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN disk_read_gb DECIMAL(10,2);
   ALTER TABLE server_metrics ADD COLUMN disk_write_gb DECIMAL(10,2);
   ```
4. Update DataCollection parser
5. Update API endpoints
6. Add disk I/O graph to Frontend (similar to network)

---

### 7. Add System Uptime (Human-Readable)
**Location:** `mini_monitering.sh` (replace or supplement LAST_BOOT)

**Add After Line 23:**
```bash
UPTIME=$(uptime -p 2>/dev/null || echo "N/A")
```

**Integration Steps:**
1. Add UPTIME variable to `mini_monitering.sh`
2. Update output formats to include uptime
3. Update Frontend to display uptime (optional: can calculate from LAST_BOOT)
4. No database changes needed if calculating from existing LAST_BOOT field

---

### 8. Add Failed Login Attempts (Security)
**Location:** `mini_monitering.sh` (new security section)

**Add After Line 29:**
```bash
# Security metrics
FAILED_LOGINS=$(grep "Failed password" /var/log/auth.log 2>/dev/null | wc -l || echo "0")
FAILED_LOGINS_RECENT=$(grep "Failed password" /var/log/auth.log 2>/dev/null | grep "$(date '+%b %d')" | wc -l || echo "0")
```

**Integration Steps:**
1. Add failed login tracking to `mini_monitering.sh`
2. May require script to run as root or with proper permissions
3. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN failed_logins_total INTEGER;
   ALTER TABLE server_metrics ADD COLUMN failed_logins_today INTEGER;
   ```
4. Update DataCollection to parse security metrics
5. Update API to expose security data
6. Add security alerts to Frontend dashboard (red badge if > threshold)
7. Consider adding to email alerts if threshold exceeded

---

## Medium Priority Additions

### 9. Add Top System Processes (CPU & Memory)
**Location:** `mini_monitering.sh` (new section)

**Add After Line 29:**
```bash
# Top 5 CPU-consuming processes
TOP_CPU=$(ps -eo comm,%cpu --sort=-%cpu | head -n 6 | tail -n 5 | awk '{printf("%s(%.1f%%) ", $1, $2)}')

# Top 5 Memory-consuming processes
TOP_MEM=$(ps -eo comm,%mem --sort=-%mem | head -n 6 | tail -n 5 | awk '{printf("%s(%.1f%%) ", $1, $2)}')
```

**Integration Steps:**
1. Add to `mini_monitering.sh`
2. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN top_cpu_processes TEXT;
   ALTER TABLE server_metrics ADD COLUMN top_mem_processes TEXT;
   ```
3. Update DataCollection parser
4. Update API
5. Add expandable section in Frontend to show top processes
6. Consider storing as JSON for better parsing

---

### 10. Add Zombie Process Count
**Location:** `mini_monitering.sh` (with process metrics)

**Add After Line 29:**
```bash
ZOMBIE_PROCS=$(ps aux | awk '$8=="Z" {count++} END {print count+0}')
```

**Integration Steps:**
1. Add to `mini_monitering.sh`
2. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN zombie_processes INTEGER;
   ```
3. Update DataCollection parser
4. Update API
5. Add warning badge in Frontend if zombie_processes > 0
6. Consider adding to alert system

---

### 11. Add Load Average per CPU
**Location:** `mini_monitering.sh` (with CPU_LOAD)

**Modify Line 21:**
```bash
CPU_LOAD=$(cat /proc/loadavg | awk '{print $1 "," $2 "," $3}')
LOAD_1MIN=$(cat /proc/loadavg | awk '{print $1}')
LOAD_PER_CPU=$(echo "$LOAD_1MIN" | awk -v vcpu=$VCPU '{printf("%.2f"), $1/vcpu}')
```

**Integration Steps:**
1. Update `mini_monitering.sh`
2. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN load_per_cpu DECIMAL(5,2);
   ```
3. Update DataCollection parser
4. Update API
5. Add load/CPU ratio to Frontend dashboard
6. Use for better CPU utilization context (>1.0 = overloaded)

---

### 12. Add GPU Monitoring (If Applicable)
**Location:** `mini_monitering.sh` (conditional section)

**Add After Line 29:**
```bash
# GPU metrics (if nvidia-smi available)
if command -v nvidia-smi &> /dev/null; then
    GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -n 1)
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | awk '{sum+=$1} END {printf("%.0f"), sum/NR}')
    GPU_MEM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk '{sum+=$1} END {printf("%.2f"), sum/1024}')
    GPU_MEM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | awk '{sum+=$1} END {printf("%.2f"), sum/1024}')
else
    GPU_COUNT="0"
    GPU_UTIL="N/A"
    GPU_MEM_USED="N/A"
    GPU_MEM_TOTAL="N/A"
fi
```

**Integration Steps:**
1. Add GPU detection to `mini_monitering.sh`
2. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN gpu_count INTEGER DEFAULT 0;
   ALTER TABLE server_metrics ADD COLUMN gpu_utilization INTEGER;
   ALTER TABLE server_metrics ADD COLUMN gpu_mem_used_gb DECIMAL(10,2);
   ALTER TABLE server_metrics ADD COLUMN gpu_mem_total_gb DECIMAL(10,2);
   ```
3. Update DataCollection parser
4. Update API
5. Add GPU section to Frontend (conditionally displayed if GPU_COUNT > 0)
6. Add GPU graphs (utilization, memory)

---

## Low Priority Additions

### 13. Add Inode Usage
**Location:** `mini_monitering.sh` (with disk section)

**Add After Line 19:**
```bash
INODE_DATA=$(df -i / | awk 'NR==2 {print}')
INODE_USED=$(echo "$INODE_DATA" | awk '{print $3}')
INODE_TOTAL=$(echo "$INODE_DATA" | awk '{print $2}')
INODE_PERC=$(echo "$INODE_DATA" | awk '{print $5}')
```

**Integration Steps:**
1. Add to `mini_monitering.sh`
2. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN inode_used BIGINT;
   ALTER TABLE server_metrics ADD COLUMN inode_total BIGINT;
   ALTER TABLE server_metrics ADD COLUMN inode_percentage VARCHAR(10);
   ```
3. Update DataCollection, API, Frontend
4. Display in disk usage section

---

### 14. Add Docker Container Count
**Location:** `mini_monitering.sh` (conditional section)

**Add After GPU section:**
```bash
# Docker metrics (if docker available)
if command -v docker &> /dev/null && docker info &> /dev/null; then
    DOCKER_RUNNING=$(docker ps -q 2>/dev/null | wc -l)
    DOCKER_TOTAL=$(docker ps -a -q 2>/dev/null | wc -l)
else
    DOCKER_RUNNING="N/A"
    DOCKER_TOTAL="N/A"
fi
```

**Integration Steps:**
1. Add Docker detection to `mini_monitering.sh`
2. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN docker_running INTEGER;
   ALTER TABLE server_metrics ADD COLUMN docker_total INTEGER;
   ```
3. Update DataCollection, API, Frontend
4. Display in system overview section

---

### 15. Add Temperature Monitoring (Physical Servers)
**Location:** `mini_monitering.sh` (conditional section)

**Add After Docker section:**
```bash
# Temperature sensors (if available)
if command -v sensors &> /dev/null; then
    TEMP_CPU=$(sensors 2>/dev/null | grep -i 'core 0' | awk '{print $3}' | tr -d '+°C' | head -n 1)
    TEMP_MAX=$(sensors 2>/dev/null | grep -i 'core' | awk '{print $3}' | tr -d '+°C' | sort -n | tail -n 1)
else
    TEMP_CPU="N/A"
    TEMP_MAX="N/A"
fi
```

**Integration Steps:**
1. Add temperature monitoring (requires `lm-sensors` package)
2. Update database schema:
   ```sql
   ALTER TABLE server_metrics ADD COLUMN temp_cpu DECIMAL(5,1);
   ALTER TABLE server_metrics ADD COLUMN temp_max DECIMAL(5,1);
   ```
3. Update DataCollection, API, Frontend
4. Add temperature warnings (>80°C = warning, >90°C = critical)

---

## Complete Integration Workflow

### Phase 1: Script Updates (Days 1-2)
1. **Fix Critical Issues**
   - [ ] Fix syntax errors in `mini_monitering.sh`
   - [ ] Optimize `TopUsers.sh` find commands
   - [ ] Test both scripts locally
   - [ ] Commit: "Fix critical bugs in monitoring scripts"

2. **Add High Priority Metrics**
   - [ ] Add swap monitoring to `mini_monitering.sh`
   - [ ] Add network I/O statistics
   - [ ] Add disk I/O statistics
   - [ ] Add security metrics (failed logins)
   - [ ] Test all new metrics
   - [ ] Commit: "Add swap, network, disk I/O, and security metrics"

### Phase 2: Database Updates (Day 3)
1. **Create Migration Script**
   - [ ] Create `srcs/Backend/migrations/add_new_metrics.sql`
   - [ ] Include all ALTER TABLE statements
   - [ ] Test on local database copy
   - [ ] Apply to development database

2. **Backup Strategy**
   - [ ] Backup existing database: `docker exec postgres pg_dump -U postgres server_db > backup.sql`
   - [ ] Document rollback procedure

### Phase 3: DataCollection Service Updates (Days 4-5)
1. **Update Parser**
   - [ ] Modify `srcs/DataCollection/BashGetInfo.py` (or equivalent)
   - [ ] Parse new fields from script output
   - [ ] Handle missing/N/A values gracefully
   - [ ] Add logging for new metrics

2. **Update Database Insert Logic**
   - [ ] Modify INSERT statements to include new columns
   - [ ] Test with mock data
   - [ ] Test end-to-end with actual scripts

3. **Test DataCollection Service**
   ```bash
   make rebuild-service SERVICE=DataCollection
   make logs-DataCollection
   # Verify new data appears in database
   ```

### Phase 4: Backend API Updates (Days 6-7)
1. **Update API Response Models**
   - [ ] Modify `srcs/Backend/api.py`
   - [ ] Add new fields to `/api/servers/metrics/latest`
   - [ ] Add new fields to `/api/servers/<server_name>/metrics/historical/<hours>`
   - [ ] Update `/api/system/overview` with new metrics

2. **Add New Endpoints (Optional)**
   - [ ] `/api/servers/<server_name>/security` - Security-specific metrics
   - [ ] `/api/servers/<server_name>/network` - Network statistics
   - [ ] `/api/servers/<server_name>/gpu` - GPU metrics (if applicable)

3. **Test API**
   ```bash
   make rebuild-service SERVICE=api
   curl http://localhost:5000/api/servers/metrics/latest | jq
   ```

### Phase 5: Frontend Updates (Days 8-10)
1. **Update API Client**
   - [ ] Modify `srcs/Frontend/api_client.py`
   - [ ] Add parsing for new fields
   - [ ] Update type hints/validation

2. **Update Components**
   - [ ] Modify `srcs/Frontend/components.py`
   - [ ] Add swap memory display component
   - [ ] Add network I/O graphs
   - [ ] Add disk I/O graphs
   - [ ] Add security alerts section
   - [ ] Add GPU section (conditional)

3. **Update Layout**
   - [ ] Modify `srcs/Frontend/Dash.py`
   - [ ] Integrate new components
   - [ ] Update grid layout

4. **Update Callbacks**
   - [ ] Modify `srcs/Frontend/callbacks.py` or `callbacks_enhanced.py`
   - [ ] Add callbacks for new interactive elements
   - [ ] Update existing callbacks to handle new data

5. **Update Styles**
   - [ ] Modify `srcs/Frontend/assets/styles.css`
   - [ ] Add styles for new components
   - [ ] Ensure KU brand compliance

6. **Test Frontend**
   ```bash
   cd srcs/Frontend
   pytest  # Run existing tests
   # Add new tests for new components
   make rebuild-service SERVICE=Frontend
   # Manual testing at http://localhost:3000
   ```

### Phase 6: Testing & Documentation (Days 11-12)
1. **Integration Testing**
   - [ ] Test full data flow: Script → DataCollection → Database → API → Frontend
   - [ ] Test all server types
   - [ ] Test edge cases (missing data, N/A values)
   - [ ] Test performance impact of new metrics

2. **Update Documentation**
   - [ ] Update `README.md` with new metrics
   - [ ] Update `CLAUDE.md` with new database schema
   - [ ] Update API documentation
   - [ ] Add screenshots of new dashboard features

3. **Create Testing Checklist**
   - [ ] Update `TESTING_CHECKLIST.md`
   - [ ] Add tests for each new metric
   - [ ] Document expected values/ranges

### Phase 7: Deployment (Day 13)
1. **Pre-Deployment**
   - [ ] Code review
   - [ ] Run full test suite
   - [ ] Backup production database
   - [ ] Create rollback plan

2. **Deployment Steps**
   ```bash
   # Pull latest code
   git pull origin main

   # Stop services
   make down

   # Apply database migrations
   docker compose up -d postgres
   docker exec -i postgres psql -U postgres server_db < srcs/Backend/migrations/add_new_metrics.sql

   # Rebuild and start all services
   make build
   make up

   # Monitor logs
   make logs-follow
   ```

3. **Post-Deployment**
   - [ ] Verify all services running
   - [ ] Check data collection working
   - [ ] Verify new metrics appearing in dashboard
   - [ ] Monitor for errors (24-48 hours)

---

## Database Migration Script Template

Create file: `srcs/Backend/migrations/add_new_metrics.sql`

```sql
-- Migration: Add new monitoring metrics
-- Date: 2025-11-04
-- Description: Adds swap, network, disk I/O, security, and optional GPU/Docker metrics

BEGIN;

-- Swap metrics
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS swap_used VARCHAR(20);
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS swap_total VARCHAR(20);
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS swap_percentage INTEGER;

-- Network metrics
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS net_rx_gb DECIMAL(10,2);
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS net_tx_gb DECIMAL(10,2);

-- Disk I/O metrics
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS disk_read_gb DECIMAL(10,2);
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS disk_write_gb DECIMAL(10,2);

-- Security metrics
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS failed_logins_total INTEGER DEFAULT 0;
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS failed_logins_today INTEGER DEFAULT 0;

-- System process metrics
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS zombie_processes INTEGER DEFAULT 0;
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS load_per_cpu DECIMAL(5,2);
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS top_cpu_processes TEXT;
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS top_mem_processes TEXT;

-- Inode metrics
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS inode_used BIGINT;
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS inode_total BIGINT;
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS inode_percentage VARCHAR(10);

-- GPU metrics (optional)
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS gpu_count INTEGER DEFAULT 0;
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS gpu_utilization INTEGER;
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS gpu_mem_used_gb DECIMAL(10,2);
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS gpu_mem_total_gb DECIMAL(10,2);

-- Docker metrics (optional)
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS docker_running INTEGER;
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS docker_total INTEGER;

-- Temperature metrics (optional)
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS temp_cpu DECIMAL(5,1);
ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS temp_max DECIMAL(5,1);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_swap_percentage ON server_metrics(swap_percentage);
CREATE INDEX IF NOT EXISTS idx_failed_logins ON server_metrics(failed_logins_today);
CREATE INDEX IF NOT EXISTS idx_zombie_procs ON server_metrics(zombie_processes);
CREATE INDEX IF NOT EXISTS idx_gpu_util ON server_metrics(gpu_utilization);

COMMIT;

-- Rollback script (save separately as rollback_add_new_metrics.sql)
-- BEGIN;
-- ALTER TABLE server_metrics DROP COLUMN IF EXISTS swap_used;
-- ALTER TABLE server_metrics DROP COLUMN IF EXISTS swap_total;
-- ... (drop all added columns)
-- COMMIT;
```

---

## Testing Checklist

After each phase, verify:

### Script Testing
- [ ] Scripts run without errors
- [ ] Output format is correct (line format and human-readable)
- [ ] All new metrics have valid values
- [ ] Scripts handle missing commands gracefully (N/A fallbacks)
- [ ] No syntax errors (shellcheck)

### Database Testing
- [ ] Migration runs successfully
- [ ] New columns created with correct types
- [ ] Existing data preserved
- [ ] Indexes created
- [ ] Rollback script tested on copy

### DataCollection Testing
- [ ] Service starts successfully
- [ ] Scripts executed on remote servers
- [ ] Data parsed correctly
- [ ] New fields inserted into database
- [ ] Errors logged appropriately
- [ ] Service restarts after errors

### API Testing
- [ ] Endpoints return new fields
- [ ] Response format valid JSON
- [ ] No breaking changes to existing clients
- [ ] Error handling for missing data
- [ ] Performance acceptable (< 1s response)

### Frontend Testing
- [ ] New components render correctly
- [ ] Data displays accurately
- [ ] Graphs update in real-time
- [ ] Responsive design maintained
- [ ] No console errors
- [ ] Toast notifications working
- [ ] All existing features still work

### Integration Testing
- [ ] End-to-end data flow works
- [ ] Historical data graphs include new metrics
- [ ] Alerts trigger correctly
- [ ] Auto-refresh includes new data
- [ ] Multiple servers display correctly
- [ ] Performance acceptable with new metrics

---

## Performance Considerations

### Script Optimization
- Network/disk I/O collection adds ~100-500ms per run
- GPU monitoring adds ~50-200ms if nvidia-smi present
- Temperature monitoring adds ~100-300ms if sensors present
- Consider running heavy metrics less frequently (e.g., every 30 min instead of 15 min)

### Database Optimization
- New columns increase row size by ~200-400 bytes
- Indexes improve query speed but increase write time
- Consider partitioning if table grows > 10M rows
- Regular VACUUM ANALYZE recommended

### Frontend Optimization
- More metrics = more data transferred
- Consider pagination for historical data
- Implement lazy loading for heavy components
- Cache aggressively (current 15 min TTL is good)

---

## Rollback Procedures

### If Scripts Break
1. Revert to previous version: `git checkout HEAD~1 -- srcs/DataCollection/*.sh`
2. Restart DataCollection service: `make restart-service SERVICE=DataCollection`

### If Database Migration Fails
1. Restore backup: `docker exec -i postgres psql -U postgres server_db < backup.sql`
2. Check error logs
3. Fix migration script
4. Retry

### If Frontend Breaks
1. Check browser console for errors
2. Revert Frontend changes: `git checkout HEAD~1 -- srcs/Frontend/`
3. Rebuild: `make rebuild-service SERVICE=Frontend`

### Complete Rollback
```bash
make down
git revert HEAD
docker volume rm serverdashboardcontainer_postgres_data
docker volume create serverdashboardcontainer_postgres_data
# Restore database from backup
docker compose up -d postgres
docker exec -i postgres psql -U postgres server_db < backup.sql
make up
```

---

## Future Enhancements (Beyond This Plan)

- **Predictive Alerts**: ML-based anomaly detection
- **Custom Metrics**: Allow users to define custom monitoring scripts
- **Multi-Tenancy**: Support for multiple organizations
- **Mobile App**: React Native or Flutter mobile dashboard
- **Alerting Integration**: Slack, PagerDuty, email notifications
- **Historical Analysis**: Trend detection, capacity planning
- **Comparison View**: Compare metrics across servers
- **Export Features**: CSV, PDF reports

---

## Support & Resources

### Documentation
- See `CLAUDE.md` for project architecture
- See `README.md` for general usage
- See `TESTING_CHECKLIST.md` for testing procedures

### Useful Commands
```bash
# Test scripts locally
./mini_monitering.sh
./mini_monitering.sh --line-format
./TopUsers.sh
./TopUsers.sh --no-headers --collect-disk

# Check database schema
docker exec -it postgres psql -U postgres server_db
\d server_metrics

# Tail logs
make logs-follow

# Quick rebuild
make restart
```

### Troubleshooting
- Check service logs: `make logs-<service>`
- Verify database connectivity: `docker exec postgres pg_isready`
- Test API manually: `curl http://localhost:5000/api/health`
- Check Frontend errors: Browser DevTools Console

---

## Summary

**Total Estimated Time:** 13 days (with testing)
**Complexity:** Medium-High
**Risk:** Low (with proper backups and testing)

**Key Metrics to Add:**
1. Swap memory (critical)
2. Network I/O (high value)
3. Disk I/O (high value)
4. Security metrics (high value)
5. GPU stats (if applicable)
6. System processes (nice to have)

**Success Criteria:**
- All new metrics displayed in dashboard
- No breaking changes to existing features
- Performance impact < 10%
- Zero data loss
- Positive user feedback

---

**Document Version:** 1.0
**Last Updated:** 2025-11-04
**Author:** Claude Code Analysis
