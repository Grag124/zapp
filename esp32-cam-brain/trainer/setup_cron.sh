#!/usr/bin/env bash
"""
trainer/setup_cron.sh — Set up cron jobs for the automated training pipeline.

- Scraper runs every 6 hours
- Trainer runs 30 minutes after each scrape
- Log rotation for training.log
- Makes all scripts executable

Usage:
    chmod +x trainer/setup_cron.sh
    ./trainer/setup_cron.sh
    crontab -l   # verify
"""

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================="
echo "  ESP32-CAM Robot Brain — Cron Setup"
echo "============================================="
echo "Project root: $PROJECT_ROOT"
echo "Script dir:   $SCRIPT_DIR"
echo

# 1. Make all scripts executable
echo "[cron] Making scripts executable..."
chmod +x "$SCRIPT_DIR"/*.py
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true
echo "  OK: Python and shell scripts are executable"
echo

# 2. Build cron lines
# Use absolute paths so cron can find everything
PYTHON=$(command -v python3 || command -v python)
SCRAPER="$SCRIPT_DIR/scraper.py"
TRAINER="$SCRIPT_DIR/auto_trainer.py"
DASHBOARD="$SCRIPT_DIR/training_dashboard.py"
LOG_FILE="$PROJECT_ROOT/training.log"

# Scraper: every 6 hours (at :00 of 0, 6, 12, 18)
SCRAPER_CRON="0 */6 * * * $PYTHON $SCRAPER --all --limit 100 >> $LOG_FILE 2>&1"

# Trainer: 30 minutes after each scrape (at :30 of 0, 6, 12, 18)
TRAINER_CRON="30 */6 * * * $PYTHON $TRAINER --train-once --data data/train --out models/model.tflite >> $LOG_FILE 2>&1"

echo "[cron] Scraper cron (every 6 hours):"
echo "  $SCRAPER_CRON"
echo
echo "[cron] Trainer cron (30 min after scrape):"
echo "  $TRAINER_CRON"
echo

# 3. Install cron jobs (avoid duplicates)
EXISTING=$(crontab -l 2>/dev/null || true)

if echo "$EXISTING" | grep -q "$SCRAPER"; then
    echo "[cron] Scraper job already installed — skipping"
else
    (echo "$EXISTING"; echo "$SCRAPER_CRON") | crontab -
    echo "[cron] Scraper job installed"
fi

if echo "$EXISTING" | grep -q "$TRAINER"; then
    echo "[cron] Trainer job already installed — skipping"
else
    (crontab -l 2>/dev/null || true; echo "$TRAINER_CRON") | crontab -
    echo "[cron] Trainer job installed"
fi

echo
echo "[cron] Current crontab:"
crontab -l
echo

# 4. Log rotation setup (optional, via logrotate if available)
if command -v logrotate &>/dev/null; then
    echo "[cron] Setting up log rotation for training.log..."
    cat > /tmp/robot-brain-logrotate <<EOF
$LOG_FILE {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
    # Note: user must install this into /etc/logrotate.d/ manually
    echo "  Logrotate config written to /tmp/robot-brain-logrotate"
    echo "  sudo cp /tmp/robot-brain-logrotate /etc/logrotate.d/robot-brain"
else
    echo "[cron] logrotate not installed — skipping log rotation setup"
    echo "  (training.log will grow; consider rotating manually)"
fi

echo
echo "============================================="
echo "  Cron setup complete!"
echo "============================================="
echo "Next steps:"
echo "  1. Verify: crontab -l"
echo "  2. Test scraper:  python3 $SCRAPER --class water_bottle --limit 10"
echo "  3. Test trainer:  python3 $TRAINER --train-once"
echo "  4. Launch dashboard: python3 $DASHBOARD --refresh 10"
echo
