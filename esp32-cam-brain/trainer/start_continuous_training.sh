#!/usr/bin/env bash
"""
trainer/start_continuous_training.sh — One-command startup for the full pipeline.

- Installs Python dependencies
- Makes scripts executable
- Sets up cron jobs
- Starts scraper and trainer in background
- Launches the training dashboard

Usage:
    chmod +x trainer/start_continuous_training.sh
    ./trainer/start_continuous_training.sh
"""

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================="
echo "  ESP32-CAM Robot Brain — Training Pipeline"
echo "============================================="
echo "Project root: $PROJECT_ROOT"
echo

# 1. Install dependencies
echo "[start] Installing Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"
echo "  OK: Dependencies installed"
echo

# 2. Make scripts executable
echo "[start] Making scripts executable..."
chmod +x "$SCRIPT_DIR"/*.py
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true
echo "  OK: Scripts are executable"
echo

# 3. Set up cron jobs
echo "[start] Setting up cron jobs..."
bash "$SCRIPT_DIR/setup_cron.sh"
echo

# 4. Create data directories
echo "[start] Creating data directories..."
mkdir -p "$PROJECT_ROOT/data/train"
mkdir -p "$PROJECT_ROOT/models/versions"
mkdir -p "$PROJECT_ROOT/data/sdcard_image"
echo "  OK: Directories ready"
echo

# 5. Run an initial scrape + train (optional, quick)
echo "[start] Running initial scrape (50 images per class)..."
python3 "$SCRIPT_DIR/scraper.py" --all --limit 50 >> "$PROJECT_ROOT/training.log" 2>&1 || true
echo "  OK: Initial scrape complete"
echo

echo "[start] Running initial training..."
python3 "$SCRIPT_DIR/auto_trainer.py" --train-once \
    --data "$PROJECT_ROOT/data/train" \
    --out "$PROJECT_ROOT/models/model.tflite" \
    >> "$PROJECT_ROOT/training.log" 2>&1 || true
echo "  OK: Initial training complete"
echo

# 6. Launch dashboard in background (optional)
echo "[start] Launching training dashboard..."
python3 "$SCRIPT_DIR/training_dashboard.py" --refresh 10 &
DASHBOARD_PID=$!
echo "  Dashboard PID: $DASHBOARD_PID"
echo

echo "============================================="
echo "  Training pipeline is running!"
echo "============================================="
echo
echo "Cron jobs (verify with: crontab -l):"
echo "  Scraper:  every 6 hours"
echo "  Trainer:  30 min after each scrape"
echo
echo "Dashboard:  python3 $SCRIPT_DIR/training_dashboard.py --refresh 10"
echo "Deploy:     python3 $SCRIPT_DIR/deploy_to_esp32.py --latest --sd /media/sdcard"
echo
echo "To stop:    kill $DASHBOARD_PID  (cron jobs keep running)"
echo

# Keep the script running so the background dashboard stays attached
# (optional — remove 'wait' if you want the script to exit immediately)
wait $DASHBOARD_PID
