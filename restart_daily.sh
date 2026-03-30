#!/bin/bash
# Daily restart script — kills and restarts both processes
# Add to crontab: 0 8 * * 1-5 /opt/HSIOrderBook/restart_daily.sh >> /var/log/hsi-collector.log 2>&1
# (Starts at 09:00 HKT Mon-Fri — cron uses UTC so adjust: HKT = UTC+8, so 01:00 UTC)

cd "$(dirname "$0")"

echo "[$(date)] Daily restart triggered"

# Kill existing sessions
screen -S futud -X quit 2>/dev/null || true
screen -S hsi-collector -X quit 2>/dev/null || true

sleep 3
bash start.sh
echo "[$(date)] Restart complete"
