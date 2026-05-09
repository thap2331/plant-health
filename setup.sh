#!/bin/bash
# Plant Health Monitor - Installation Script

SCRIPT_DIR="$(pwd)"
USER=$(whoami)

echo "Installing plant health monitor for user: $USER"
echo "Script directory: $SCRIPT_DIR"

# Add cron job
CRON_CMD="*/30 * * * * /usr/bin/python3 $SCRIPT_DIR/water_plant.py >> $SCRIPT_DIR/water.log 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -F "$SCRIPT_DIR/water_plant.py") && {
    echo "Cron job already installed. Skipping."
    exit 0
}

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✓ Cron job installed successfully"
echo "  Runs every 30 minutes"
echo "  Logs to: $SCRIPT_DIR/water.log"
echo ""
echo "To monitor: tail -f $SCRIPT_DIR/water.log"
echo "To remove: crontab -e"
