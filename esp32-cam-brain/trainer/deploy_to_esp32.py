#!/usr/bin/env python3
"""
trainer/deploy_to_esp32.py — Deploy trained model to ESP32-CAM SD card.

Copies the latest model.tflite to the SD card mount point so the robot can
run inference locally (no cloud dependency for movement).

Usage:
    python3 trainer/deploy_to_esp32.py --model models/model.tflite --sd /media/sdcard
    python3 trainer/deploy_to_esp32.py --latest --sd /media/sdcard
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

MODELS_DIR = Path("models")
SD_MODELS_DIR_NAME = "models"  # folder on SD card


def find_latest_model() -> Path:
    """Find the most recent model.tflite in models/."""
    candidates = [
        MODELS_DIR / "model.tflite",
    ]
    # Also check versioned models
    versions_dir = MODELS_DIR / "versions"
    if versions_dir.exists():
        for v in sorted(versions_dir.iterdir()):
            m = v / "model.tflite"
            if m.exists():
                candidates.append(m)

    existing = [c for c in candidates if c.exists()]
    if not existing:
        return None
    # Return the most recently modified
    return max(existing, key=lambda p: p.stat().st_mtime)


def deploy_model(model_path: Path, sd_mount: Path) -> bool:
    """Copy model to SD card /models/ folder. Returns True on success."""
    if not model_path.exists():
        logger.error("Model not found: %s", model_path)
        return False

    dest_dir = sd_mount / SD_MODELS_DIR_NAME
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error("Cannot create SD models dir %s: %s", dest_dir, e)
        return False

    dest_file = dest_dir / "model.tflite"
    try:
        shutil.copy2(model_path, dest_file)
        logger.info("[deploy] Copied %s -> %s", model_path, dest_file)
        logger.info("[deploy] Size: %d bytes", dest_file.stat().st_size)
        logger.info("[deploy] Model ready for ESP32-CAM SD card deployment")
        return True
    except OSError as e:
        logger.error("Failed to copy model to SD: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Deploy model to ESP32-CAM SD card"
    )
    parser.add_argument("--model", help="Path to .tflite model file")
    parser.add_argument("--latest", action="store_true",
                        help="Deploy the most recent model in models/")
    parser.add_argument("--sd", required=True,
                        help="SD card mount point (e.g. /media/sdcard)")
    args = parser.parse_args()

    sd_mount = Path(args.sd)
    if not sd_mount.exists():
        logger.error("SD card mount point not found: %s", sd_mount)
        logger.info("Insert the ESP32-CAM SD card and mount it, then re-run")
        sys.exit(1)

    if args.latest:
        model_path = find_latest_model()
        if model_path is None:
            logger.error("No model.tflite found in models/")
            sys.exit(1)
        logger.info("[deploy] Using latest model: %s", model_path)
    elif args.model:
        model_path = Path(args.model)
    else:
        logger.error("Specify --model <path> or --latest")
        sys.exit(1)

    success = deploy_model(model_path, sd_mount)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
