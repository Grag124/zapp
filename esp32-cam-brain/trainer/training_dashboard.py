#!/usr/bin/env python3
"""
trainer/training_dashboard.py — Training progress monitor.

Displays a real-time dashboard of training progress:
- Current model accuracy and version
- Image counts per class
- Training history
- Recent log entries
- Next scheduled scrape/train times

Usage:
    python3 trainer/training_dashboard.py --refresh 10
    python3 trainer/training_dashboard.py --once
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Paths
DATA_TRAIN_DIR = Path("data/train")
MODELS_DIR = Path("models")
MODEL_VERSIONS_DIR = Path("models/versions")
TRAINING_LOG = Path("training.log")
HISTORY_FILE = Path("training_history.json")

# Add trainer dir to path for model_version_manager
sys.path.insert(0, str(Path(__file__).parent))
try:
    from model_version_manager import ModelVersionManager
except ImportError:
    ModelVersionManager = None


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def count_images(data_dir: Path) -> dict:
    """Count images per class."""
    counts = {}
    if not data_dir.exists():
        return counts
    for class_dir in sorted(data_dir.iterdir()):
        if class_dir.is_dir():
            jpg = len(list(class_dir.glob("*.jpg")))
            png = len(list(class_dir.glob("*.png")))
            counts[class_dir.name] = jpg + png
    return counts


def format_bytes(size: int) -> str:
    """Format bytes as human-readable."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def print_dashboard(refresh: int = 0, once: bool = False):
    """Print the training dashboard."""
    mgr = ModelVersionManager(str(MODEL_VERSIONS_DIR)) if ModelVersionManager else None

    while True:
        clear_screen()
        print("=" * 60)
        print("  ESP32-CAM Robot Brain — Training Dashboard")
        print("=" * 60)
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Image counts
        print("  TRAINING DATA (data/train/)")
        print("  " + "-" * 56)
        counts = count_images(DATA_TRAIN_DIR)
        if counts:
            total = sum(counts.values())
            for cls, cnt in sorted(counts.items()):
                bar = "#" * min(cnt // 5, 40)
                print(f"  {cls:<20} {cnt:>5} images  {bar}")
            print(f"  {'TOTAL':<20} {total:>5} images")
        else:
            print("  (no training data found — run scraper.py first)")
        print()

        # Model versions
        print("  MODEL VERSIONS (models/versions/)")
        print("  " + "-" * 56)
        if mgr:
            versions = mgr.list_versions()
            if versions:
                print(f"  {'Version':<10} {'Accuracy':<10} {'Size':<12} {'Notes'}")
                for v in versions[-5:]:  # show last 5
                    size_kb = v["size_bytes"] / 1024
                    print(f"  v{v['version']:03d}    {v['accuracy']:<10.3f} "
                          f"{size_kb:<12.1f}KB {v['notes'][:30]}")
                best = mgr.get_best_version()
                if best:
                    print(f"\n  Best: v{best['version']:03d} "
                          f"(acc={best['accuracy']:.3f})")
            else:
                print("  (no model versions yet — run trainer first)")
        else:
            print("  (model_version_manager not available)")
        print()

        # Current model
        print("  CURRENT MODEL (models/model.tflite)")
        print("  " + "-" * 56)
        model_file = MODELS_DIR / "model.tflite"
        if model_file.exists():
            size = model_file.stat().st_size
            print(f"  Path: {model_file}")
            print(f"  Size: {format_bytes(size)}")
        else:
            print("  (no model.tflite found — placeholder only)")
        print()

        # Recent log
        print("  RECENT TRAINING LOG (training.log)")
        print("  " + "-" * 56)
        if TRAINING_LOG.exists():
            try:
                with open(TRAINING_LOG, 'r') as f:
                    lines = f.readlines()
                for line in lines[-8:]:
                    print(f"  {line.rstrip()[:70]}")
            except OSError:
                print("  (could not read log)")
        else:
            print("  (no training log yet)")
        print()

        print("  Commands: Ctrl+C to exit")
        if once:
            break

        if refresh > 0:
            time.sleep(refresh)


def main():
    parser = argparse.ArgumentParser(
        description="Training dashboard for ESP32-CAM robot brain"
    )
    parser.add_argument("--refresh", type=int, default=0,
                        help="Auto-refresh interval in seconds (0 = no refresh)")
    parser.add_argument("--once", action="store_true",
                        help="Print dashboard once and exit")
    args = parser.parse_args()

    try:
        print_dashboard(refresh=args.refresh, once=args.once)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
