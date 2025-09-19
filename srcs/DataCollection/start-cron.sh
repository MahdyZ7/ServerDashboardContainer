#!/bin/bash
echo "Starting DataCollection with Cron Scheduler"
echo "Crontab entries:"
crontab -l
echo "Starting cron daemon..."
cron
echo "Cron daemon started. Tailing log file..."
touch /var/log/datacollection.log
tail -f /var/log/datacollection.log