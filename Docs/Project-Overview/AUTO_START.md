# Auto-Start Configuration Guide

Configure the Server Monitoring Dashboard to automatically start on system boot using systemd.

---

## Quick Start

### Enable Auto-Start

```bash
# Method 1: Using Makefile (Recommended)
make enable-autostart

# Method 2: Manual installation
sudo ./setup-autostart.sh
```

### Check Status

```bash
make autostart-status
```

### Disable Auto-Start

```bash
make disable-autostart
```

---

## How It Works

### Architecture

1. **Systemd Service** (`server-dashboard.service`)
   - Starts after Docker and network are ready
   - Runs `docker compose up -d` in project directory
   - Logs to systemd journal

2. **Makefile Integration**
   - Simple commands for common operations
   - Status checking and log viewing
   - Easy enable/disable

3. **Boot Sequence**
   ```
   System Boot
     ↓
   Docker Service Starts
     ↓
   Network Ready
     ↓
   server-dashboard.service Starts
     ↓
   Docker Compose Up
     ↓
   All Containers Running
   ```

---

## Commands Reference

### Setup

```bash
# Enable auto-start on boot
make enable-autostart

# Disable auto-start
make disable-autostart
```

### Status & Logs

```bash
# Check if auto-start is enabled
make autostart-status

# View recent logs (last 50 lines)
make autostart-logs

# Follow logs in real-time
make autostart-logs-follow

# View all logs
journalctl -u server-dashboard
```

### Control

```bash
# Start manually (won't auto-start on boot unless enabled)
sudo systemctl start server-dashboard

# Stop manually
sudo systemctl stop server-dashboard

# Restart
sudo systemctl restart server-dashboard

# Check detailed status
sudo systemctl status server-dashboard
```

### Maintenance

```bash
# Reload systemd after manual edits
sudo systemctl daemon-reload

# Re-enable (if service file changed)
make disable-autostart
make enable-autostart

# View service configuration
sudo systemctl cat server-dashboard
```

---

## Systemd Service File

Location: `/etc/systemd/system/server-dashboard.service`

```ini
[Unit]
Description=Server Monitoring Dashboard
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ayassin/Developer/ServerDashboardContainer
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300
User=ayassin
Group=ayassin

[Install]
WantedBy=multi-user.target
```

### Configuration Details

| Setting | Value | Purpose |
|---------|-------|---------|
| **After** | `docker.service network-online.target` | Wait for Docker and network |
| **Requires** | `docker.service` | Must have Docker running |
| **Type** | `oneshot` | Runs once at startup |
| **RemainAfterExit** | `yes` | Service marked as active after startup |
| **WorkingDirectory** | Project path | Where to run docker compose |
| **ExecStart** | `docker compose up -d` | Start all containers |
| **ExecStop** | `docker compose down` | Stop all containers on shutdown |
| **TimeoutStartSec** | `300` | 5 minutes to start (pulling images) |
| **User/Group** | Your username | Run as non-root user |

---

## Troubleshooting

### Issue: Services Don't Start on Boot

**Check systemd status:**
```bash
make autostart-status
sudo systemctl status server-dashboard
```

**Check logs:**
```bash
make autostart-logs
```

**Common causes:**
- Docker service not started before dashboard service
- Network not ready
- Permissions issues
- Port conflicts (see [TROUBLESHOOTING.md](TROUBLESHOOTING.md))

**Solution:**
```bash
# Re-install auto-start
make disable-autostart
make enable-autostart

# Test manually
sudo systemctl start server-dashboard
make ps
```

### Issue: Permission Denied

**Symptoms:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Re-login for changes to take effect
exit
# SSH back in

# Test Docker access
docker ps

# Restart service
sudo systemctl restart server-dashboard
```

### Issue: Port Conflicts on Boot

**Symptoms:**
- Service fails to start
- Logs show "address already in use"

**Solution:**

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#port-conflicts) for detailed solutions.

Quick fix:
```bash
# Disable conflicting services
sudo systemctl disable httpd  # Apache
sudo systemctl disable nginx  # Nginx

# Reboot to test
sudo reboot
```

### Issue: Slow Startup

**Symptoms:**
- Services take > 5 minutes to start
- Timeout errors in logs

**Solution:**

```bash
# Increase timeout in service file
sudo systemctl edit server-dashboard

# Add override:
[Service]
TimeoutStartSec=600

# Save and reload
sudo systemctl daemon-reload
sudo systemctl restart server-dashboard
```

### Issue: Containers Not Ready

**Symptoms:**
- Service starts but containers not responding
- Health checks failing

**Solution:**

```bash
# Add delay to allow containers to initialize
sudo systemctl edit server-dashboard

# Add ExecStartPost to wait for readiness:
[Service]
ExecStartPost=/bin/sleep 30

# Reload and test
sudo systemctl daemon-reload
sudo systemctl restart server-dashboard
```

---

## Advanced Configuration

### Custom Docker Compose File

If using a different compose file:

```bash
sudo systemctl edit server-dashboard

# Add override:
[Service]
ExecStart=
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
```

### Environment Variables

To pass environment variables to docker compose:

```bash
sudo systemctl edit server-dashboard

# Add:
[Service]
Environment="COMPOSE_PROJECT_NAME=server_dashboard"
Environment="DEBUG=False"
```

### Email Notifications on Failure

Get notified if the service fails:

```bash
# Install mail utilities
sudo dnf install mailx

# Edit service
sudo systemctl edit server-dashboard

# Add:
[Unit]
OnFailure=failure-email@%n.service

# Create email service
sudo nano /etc/systemd/system/failure-email@.service
```

Content:
```ini
[Unit]
Description=Send email on service failure

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo "Service %i failed" | mail -s "Service Failure: %i" your@email.com'
```

---

## Verification After Reboot

After enabling auto-start, verify it works:

```bash
# 1. Enable auto-start
make enable-autostart

# 2. Reboot system
sudo reboot

# 3. After reboot, check services (wait 2-3 minutes)
make ps
make status

# 4. Check auto-start logs
make autostart-logs

# 5. Test dashboard
curl http://localhost:3000
curl http://localhost:5000/api/health

# 6. Verify auto-start is enabled
make autostart-status
```

Expected output:
```
● server-dashboard.service - Server Monitoring Dashboard
   Loaded: loaded (/etc/systemd/system/server-dashboard.service; enabled; vendor preset: disabled)
   Active: active (exited) since ...
```

---

## Disabling Auto-Start

To stop services from starting on boot:

```bash
# Disable auto-start
make disable-autostart

# Verify
make autostart-status
# Should show: disabled

# Services will still run until reboot or manual stop
make down  # Stop now
```

---

## Related Documentation

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick command reference
- [Docs/INDEX.md](../INDEX.md) - Documentation index

---

## Quick Reference Card

```bash
# Setup
make enable-autostart       # Enable auto-start on boot
make disable-autostart      # Disable auto-start

# Status
make autostart-status       # Check if enabled
make autostart-logs         # View recent logs
make autostart-logs-follow  # Follow logs live

# Control (Manual)
sudo systemctl start server-dashboard    # Start now
sudo systemctl stop server-dashboard     # Stop now
sudo systemctl restart server-dashboard  # Restart now
sudo systemctl status server-dashboard   # Detailed status

# Maintenance
sudo systemctl daemon-reload             # Reload after edits
sudo systemctl edit server-dashboard     # Edit overrides
sudo systemctl cat server-dashboard      # View full config

# Verification
make ps                     # Check containers running
make status                 # Check services status
curl http://localhost:3000  # Test frontend
```

---

**Last Updated:** 2025-12-04
**Tested On:** RHEL 9.7, Docker Compose v2.20+
