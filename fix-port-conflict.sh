#!/bin/bash
# Port 80 Conflict Resolution Script
# Stops Apache/httpd and disables it from starting on boot

set -e

echo "========================================="
echo "Port 80 Conflict Resolution"
echo "========================================="
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./fix-port-conflict.sh"
    exit 1
fi

echo "Checking for services using port 80..."
echo ""

# Check if httpd (Apache) is running
if systemctl is-active --quiet httpd; then
    echo "✓ Found: Apache HTTP Server (httpd) is running"
    echo "  Status: $(systemctl is-enabled httpd 2>/dev/null || echo 'unknown')"

    echo ""
    echo "Stopping Apache HTTP Server..."
    systemctl stop httpd
    echo "✓ Apache stopped"

    echo ""
    echo "Disabling Apache from starting on boot..."
    systemctl disable httpd
    echo "✓ Apache disabled"
else
    echo "✓ Apache HTTP Server (httpd) is not running"
fi

# Check if nginx is running as a system service (not Docker)
if systemctl is-active --quiet nginx; then
    echo ""
    echo "✓ Found: Nginx system service is running"
    echo "  Status: $(systemctl is-enabled nginx 2>/dev/null || echo 'unknown')"

    echo ""
    echo "Stopping Nginx system service..."
    systemctl stop nginx
    echo "✓ Nginx stopped"

    echo ""
    echo "Disabling Nginx from starting on boot..."
    systemctl disable nginx
    echo "✓ Nginx disabled"
else
    echo "✓ Nginx system service is not running"
fi

# Check what's using port 80
echo ""
echo "Current port 80 status:"
if ss -tlnp | grep -q ':80 '; then
    echo "⚠ Port 80 is still in use:"
    ss -tlnp | grep ':80 '
    echo ""
    echo "You may need to manually investigate and stop the process above."
else
    echo "✓ Port 80 is now available"
fi

echo ""
echo "========================================="
echo "Resolution Complete"
echo "========================================="
echo ""
echo "You can now start your Docker Compose stack:"
echo "  docker compose up -d"
echo ""
echo "Or use the auto-start service:"
echo "  sudo systemctl start server-dashboard"
echo ""
