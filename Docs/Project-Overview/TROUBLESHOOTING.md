# Troubleshooting Guide

Common issues and solutions for the Server Dashboard Container project.

---

## Table of Contents
1. [Port Conflicts](#port-conflicts)
2. [Container Issues](#container-issues)
3. [Database Problems](#database-problems)
4. [Frontend Issues](#frontend-issues)
5. [API Issues](#api-issues)
6. [Performance Problems](#performance-problems)

---

## Port Conflicts

### Issue: Port 80 Already in Use

**Symptoms:**
```
failed to bind host port 0.0.0.0:80/tcp: address already in use
```

**Common Causes:**
- Apache HTTP Server (httpd) running on RHEL systems
- Nginx running outside Docker
- Another Docker container using port 80

**Solution:**

```bash
# 1. Identify what's using port 80
sudo ss -tlnp | grep :80
# or
sudo lsof -i :80

# 2. If it's Apache (httpd)
sudo systemctl stop httpd
sudo systemctl disable httpd  # Prevent auto-start

# 3. If it's nginx
sudo systemctl stop nginx
sudo systemctl disable nginx

# 4. If it's another Docker container
docker ps  # Find the container
docker stop <container_name>

# 5. Verify port is free
sudo ss -tlnp | grep :80  # Should return nothing

# 6. Start your services
docker compose up -d

# 7. Verify containers are running
docker ps
curl http://localhost | head -20
```

### Issue: Port 3000 or 5000 Already in Use

**Symptoms:**
```
failed to bind host port 0.0.0.0:3000/tcp: address already in use
```

**Solution:**

```bash
# Find process using the port (replace 3000 with your port)
sudo lsof -i :3000

# Kill the process (replace PID)
sudo kill -9 <PID>

# Or change the port in docker-compose.yml
ports:
  - "3001:3000"  # Use 3001 externally instead
```

---

## Container Issues

### Issue: Containers Won't Start

**Symptoms:**
- `docker ps` shows containers constantly restarting
- Containers exit immediately after starting

**Diagnosis:**

```bash
# Check container logs
make logs-Frontend
make logs-api
make logs-DataCollection
make logs-db

# Check container status
docker ps -a

# Inspect specific container
docker inspect <container_name>
```

**Common Solutions:**

```bash
# 1. Rebuild containers
make rebuild

# 2. Clean and restart
make clean
make build

# 3. Complete cleanup (removes volumes!)
make cclean
make build
```

### Issue: Container Running But Not Responsive

**Symptoms:**
- `docker ps` shows container as "Up"
- Service doesn't respond to requests
- No logs being generated

**Solution:**

```bash
# 1. Check if process is actually running inside container
docker exec <container_name> ps aux

# 2. Check network connectivity
docker exec <container_name> ping api
docker exec <container_name> ping postgres

# 3. Restart specific service
make restart-service SERVICE=Frontend

# 4. Check for errors in startup
docker logs <container_name> --tail 100
```

---

## Database Problems

### Issue: Database Connection Failed

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**

```bash
# 1. Check if database container is running
docker ps | grep postgres

# 2. Check database logs
make logs-db

# 3. Verify environment variables
cat .env | grep POSTGRES

# 4. Test connection manually
docker exec -it postgres psql -U postgres -d server_db

# 5. Restart database
make restart-service SERVICE=postgres

# 6. Wait for database to be ready
# Database takes 10-15 seconds to fully start
sleep 15
```

### Issue: Database Tables Missing

**Symptoms:**
```
psycopg2.errors.UndefinedTable: relation "server_metrics" does not exist
```

**Solution:**

```bash
# 1. Connect to database
docker exec -it postgres psql -U postgres -d server_db

# 2. Check if tables exist
\dt

# 3. If tables missing, check schema initialization
# Tables should be created by DataCollection service on first run

# 4. Manually create tables (if needed)
# Check schema/generated/sql/ for table definitions

# 5. Restart DataCollection to trigger initialization
make restart-service SERVICE=datacollection
```

### Issue: Database Performance Slow

**Symptoms:**
- Queries taking > 5 seconds
- Dashboard slow to load

**Solution:**

```bash
# 1. Check database size
docker exec -it postgres psql -U postgres -d server_db -c "\l+"

# 2. Check table sizes
docker exec -it postgres psql -U postgres -d server_db -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# 3. Check for missing indexes
# Add indexes for commonly queried columns

# 4. Archive old data
# Delete metrics older than 30 days
```

---

## Frontend Issues

### Issue: Frontend Not Loading

**Symptoms:**
- Blank page
- "Cannot connect to server" error
- Page stuck loading

**Solution:**

```bash
# 1. Check if Frontend container is running
docker ps | grep Frontend

# 2. Check Frontend logs
make logs-Frontend

# 3. Check API connectivity from Frontend
docker exec Frontend curl http://api:5000/api/health

# 4. Restart Frontend
make restart-service SERVICE=Frontend

# 5. Clear browser cache and reload
# Chrome: Ctrl+Shift+R
# Firefox: Ctrl+Shift+R

# 6. Check for JavaScript errors
# Open browser DevTools (F12) → Console
```

### Issue: Dark Mode Not Working

**Symptoms:**
- Toggle button doesn't switch themes
- Some elements not themed properly
- Graphs remain dark/invisible

**Solution:**

```bash
# 1. Clear browser cache
# 2. Hard reload (Ctrl+Shift+R)
# 3. Check browser console for errors

# 4. Verify files exist
ls srcs/Frontend/assets/dark-mode.css
ls srcs/Frontend/assets/animations.css

# 5. Check CSS is loaded
# DevTools → Network → Filter: CSS
# Should see dark-mode.css loaded

# 6. If still not working, restart Frontend
make restart-service SERVICE=Frontend
```

### Issue: Graphs Not Displaying

**Symptoms:**
- Empty graph areas
- "No data available" message
- Graphs show but are invisible

**Solution:**

```bash
# 1. Check if API is returning data
curl http://localhost:5000/api/servers/metrics/latest | jq

# 2. Check browser console for errors
# Look for Plotly errors or data formatting issues

# 3. Check graph_config.py for correct settings
cat srcs/Frontend/graph_config.py

# 4. If in dark mode, verify CSS styling
# See DARK_MODE_COMPLETE.md for details

# 5. Restart Frontend
make restart-service SERVICE=Frontend
```

---

## API Issues

### Issue: API Returns 500 Errors

**Symptoms:**
```
Internal Server Error
Status: 500
```

**Solution:**

```bash
# 1. Check API logs for stack trace
make logs-api

# 2. Check if database is accessible
docker exec api curl postgres:5432

# 3. Verify environment variables
docker exec api env | grep POSTGRES

# 4. Restart API
make restart-service SERVICE=api

# 5. Test API endpoint directly
curl http://localhost:5000/api/health
curl http://localhost:5000/api/servers/list
```

### Issue: API Returns Empty Data

**Symptoms:**
```json
{"success": true, "data": [], "message": "No data available"}
```

**Solution:**

```bash
# 1. Check if DataCollection is running
docker ps | grep datacollection

# 2. Check DataCollection logs
make logs-DataCollection

# 3. Verify data exists in database
docker exec -it postgres psql -U postgres -d server_db -c "
SELECT COUNT(*) FROM server_metrics;
SELECT COUNT(*) FROM top_users;
"

# 4. Manually trigger data collection
make restart-service SERVICE=datacollection

# 5. Wait 5 minutes for data collection cycle
```

---

## Performance Problems

### Issue: Dashboard Slow to Load

**Symptoms:**
- Page takes > 10 seconds to load
- Browser becomes unresponsive
- High CPU usage

**Solution:**

```bash
# 1. Check container resource usage
docker stats

# 2. Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/servers/metrics/latest

# Create curl-format.txt:
# time_namelookup:  %{time_namelookup}
# time_connect:  %{time_connect}
# time_starttransfer:  %{time_starttransfer}
# time_total:  %{time_total}

# 3. Check database query performance
# See "Database Performance Slow" above

# 4. Reduce data collection frequency
# Edit srcs/DataCollection/main.py
# Increase sleep time from 300s to 600s

# 5. Enable caching (already enabled by default)
# Check config.py: CACHE_TTL = 900
```

### Issue: High Memory Usage

**Symptoms:**
- Docker containers using > 2GB RAM
- System becomes slow
- Out of memory errors

**Solution:**

```bash
# 1. Check memory usage by container
docker stats --no-stream

# 2. Limit container memory in docker-compose.yml
services:
  frontend:
    mem_limit: 512m
  api:
    mem_limit: 512m
  datacollection:
    mem_limit: 512m

# 3. Restart with new limits
docker compose down
docker compose up -d

# 4. Clear old data from database
# See "Database Performance Slow"
```

---

## Auto-Start Issues

### Issue: Services Don't Start on Boot

**Symptoms:**
- After reboot, services not running
- `systemctl status server-dashboard` shows failed

**Solution:**

```bash
# 1. Check auto-start status
make autostart-status

# 2. Check systemd logs
make autostart-logs

# 3. Verify systemd service file
sudo systemctl cat server-dashboard

# 4. Re-enable auto-start
make disable-autostart
make enable-autostart

# 5. Test manually
sudo systemctl start server-dashboard
make ps
```

---

## Getting More Help

If your issue isn't listed here:

1. **Check Logs:**
   ```bash
   make logs-follow  # Follow all logs
   make logs-<service>  # Specific service
   ```

2. **Check Documentation:**
   - [Docs/INDEX.md](../INDEX.md) - Documentation index
   - [CLAUDE.md](../../CLAUDE.md) - Project guide
   - [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick commands

3. **Verify Setup:**
   ```bash
   # Check all services
   make ps
   make status

   # Test connectivity
   curl http://localhost:3000
   curl http://localhost:5000/api/health
   ```

4. **Clean Slate:**
   ```bash
   # Complete rebuild (WARNING: Deletes data!)
   make cclean
   make build
   make up
   ```

---

**Last Updated:** 2025-12-04
**Maintainer:** Project Team
