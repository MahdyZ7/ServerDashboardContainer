#!/bin/bash
# Auto-start setup script for Server Monitoring Dashboard
# This script configures the system to automatically start the dashboard on boot

set -e

echo "==================================="
echo "Server Dashboard Auto-Start Setup"
echo "==================================="
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./setup-autostart.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$(whoami)}
PROJECT_DIR="/home/ayassin/Developer/ServerDashboardContainer"

echo "Checking for port 80 conflicts..."

# Check and disable Apache/httpd if it's enabled
if systemctl is-enabled --quiet httpd 2>/dev/null; then
    echo "  Found: Apache HTTP Server (httpd) is enabled"
    echo "  Disabling Apache to free port 80..."
    systemctl stop httpd 2>/dev/null || true
    systemctl disable httpd
    echo "  ✓ Apache disabled"
else
    echo "  ✓ Apache not found or already disabled"
fi

# Check and disable system nginx if it's enabled
if systemctl is-enabled --quiet nginx 2>/dev/null; then
    echo "  Found: Nginx system service is enabled"
    echo "  Disabling Nginx to free port 80..."
    systemctl stop nginx 2>/dev/null || true
    systemctl disable nginx
    echo "  ✓ Nginx disabled"
else
    echo "  ✓ System Nginx not found or already disabled"
fi

echo ""
echo "Installing systemd service..."

# Create systemd service file
cat > /etc/systemd/system/server-dashboard.service << 'EOF'
[Unit]
Description=Server Monitoring Dashboard Docker Compose
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target
Conflicts=httpd.service nginx.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ayassin/Developer/ServerDashboardContainer
# Stop conflicting services before starting (- prefix means don't fail if service doesn't exist)
ExecStartPre=-/usr/bin/systemctl stop httpd.service
ExecStartPre=-/usr/bin/systemctl stop nginx.service
# Clean Docker state
ExecStartPre=/usr/bin/docker compose down
# Start services
ExecStart=/usr/bin/docker compose up -d
# Stop services
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "Setting correct permissions..."
chmod 644 /etc/systemd/system/server-dashboard.service

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling service to start on boot..."
systemctl enable server-dashboard.service

echo ""
echo "✓ Auto-start setup complete!"
echo ""
echo "Available commands:"
echo "  sudo systemctl start server-dashboard    # Start the dashboard"
echo "  sudo systemctl stop server-dashboard     # Stop the dashboard"
echo "  sudo systemctl restart server-dashboard  # Restart the dashboard"
echo "  sudo systemctl status server-dashboard   # Check status"
echo "  sudo systemctl disable server-dashboard  # Disable auto-start"
echo "  sudo journalctl -u server-dashboard -f   # View logs"
echo ""
echo "The dashboard will now start automatically on system boot!"
echo ""
