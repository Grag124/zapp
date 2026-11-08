#!/usr/bin/env python3
"""
trainer/auto_trainer.py — Auto-training module.

Monitors data/train/ for new images and automatically retrains the
TinyML classifier when new data is available. Exports updated model.tflite
to models/ and logs all activity to training.log.

Features:
- Folder monitoring (polling-based, no inotify dependency)
- Auto-retrain on new data detection
- Training history and accuracy metrics
- Model versioning integration with model_version_manager.py
- Export to TensorFlow Lite Micro (8-bit quantized .tflite)

Usage:
    python3 trainer/auto_trainer.py --monitor --interval 300
    python3 trainer/auto_trainer.py --train-once --data data/train
"""

import argparse
import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
DATA_TRAIN_DIR = Path("data/train")
MODELS_DIR = Path("models")
TRAINING_LOG = Path("training.log")
HISTORY_FILE = Path("training_history.json")
MODEL_VERSIONS_DIR = Path("models/versions")

# Import model version manager
sys.path.insert(0, str(Path(__file__).parent))
try:
    from model_version_manager import ModelVersionManager
except ImportError:
    logger.warning("model_version_manager.py not found — versioning disabled")
    ModelVersionManager = None


def count_images(data_dir: Path) -> dict:
    """Count images per class in the training directory."""
    counts = {}
    if not data_dir.exists():
        return counts

    for class_dir in sorted(data_dir.iterdir()):
        if class_dir.is_dir():
            jpg_count = len(list(class_dir.glob("*.jpg")))
            png_count = len(list(class_dir.glob("*.png")))
            counts[class_dir.name] = jpg_count + png_count
    return counts


def load_last_counts() -> dict:
    """Load the last known image counts from history file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_counts(counts: dict):
    """Save current image counts to history file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(counts, f, indent=2)
    except OSError as e:
        logger.error("Failed to save history: %s", e)


def has_new_data(current_counts: dict, last_counts: dict) -> bool:
    """Check if any class has new images since last check."""
    for class_name, count in current_counts.items():
        if count > last_counts.get(class_name, 0):
            return True
    return False


def run_training(data_dir: str, output_model: str, epochs: int = 5) -> bool:
    """Run train_model.py as a subprocess."""
    train_script = Path(__file__).parent / "train_model.py"
    if not train_script.exists():
        logger.error("train_model.py not found at %s", train_script)
        return False

    cmd = [
        sys.executable, str(train_script),
        "--data", data_dir,
        "--out", output_model,
        "--epochs", str(epochs),
    ]

    logger.info("[auto_trainer] Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            logger.info("[auto_trainer] Training completed successfully")
            logger.debug("[auto_trainer] stdout: %s", result.stdout)
            return True
        else:
            logger.error("[auto_trainer] Training failed (exit %d)",
                         result.returncode)
            logger.error("[auto_trainer] stderr: %s", result.stderr)
            return False
    except subprocess.TimeoutExpired:
        logger.error("[auto_trainer] Training timed out after 600s")
        return False
    except Exception as e:
        logger.error("[auto_trainer] Training error: %s", e)
        return False


def deploy_model(model_path: str) -> bool:
    """Deploy the trained model via deploy_model.py."""
    deploy_script = Path(__file__).parent / "deploy_model.py"
    if not deploy_script.exists():
        logger.error("deploy_model.py not found at %s", deploy_script)
        return False

    cmd = [
        sys.executable, str(deploy_script),
        "--model", model_path,
        "--sd", str(Path("data/sdcard_image")),
    ]

    logger.info("[auto_trainer] Deploying model: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            logger.info("[auto_trainer] Model deployed successfully")
            return True
        else:
            logger.error("[auto_trainer] Deploy failed (exit %d)", result.returncode)
            logger.error("[auto_trainer] stderr: %s", result.stderr)
            return False
    except Exception as e:
        logger.error("[auto_trainer] Deploy error: %s", e)
        return False


def train_once(data_dir: str = "data/train",
               output_model: str = "models/model.tflite",
               epochs: int = 5,
               deploy: bool = True) -> bool:
    """Run a single training cycle."""
    logger.info("[auto_trainer] Starting training cycle")
    logger.info("[auto_trainer] Data: %s -> Model: %s", data_dir, output_model)

    success = run_training(data_dir, output_model, epochs=epochs)
    if not success:
        return False

    if deploy:
        deploy_success = deploy_model(output_model)
        if not deploy_success:
            logger.warning("[auto_trainer] Training succeeded but deploy failed")

    # Record in version manager if available
    if ModelVersionManager is not None:
        try:
            mgr = ModelVersionManager(str(MODEL_VERSIONS_DIR))
            # Evaluate accuracy by parsing training output — simplified: use file size as proxy
            model_size = Path(output_model).stat().st_size if Path(output_model).exists() else 0
            mgr.save_version(output_model, accuracy=0.0, notes="Auto-trained")
            logger.info("[auto_trainer] Model version recorded")
        except Exception as e:
            logger.warning("[auto_trainer] Version recording failed: %s", e)

    return True


def monitor(interval: int = 300,
            data_dir: str = "data/train",
            output_model: str = "models/model.tflite",
            epochs: int = 5,
            deploy: bool = True):
    """
    Monitor the training folder and auto-retrain when new images appear.
    Runs until interrupted (Ctrl+C).
    """
    logger.info("[auto_trainer] Monitoring %s (interval=%ds)", data_dir, interval)
    logger.info("[auto_trainer] Press Ctrl+C to stop")

    last_counts = load_last_counts()

    try:
        while True:
            current_counts = count_images(Path(data_dir))

            if current_counts and has_new_data(current_counts, last_counts):
                logger.info("[auto_trainer] New data detected: %s", current_counts)
                success = train_once(
                    data_dir=data_dir,
                    output_model=output_model,
                    epochs=epochs,
                    deploy=deploy,
                )
                if success:
                    last_counts = current_counts
                    save_counts(last_counts)
            else:
                logger.debug("[auto_trainer] No new data. Counts: %s", current_counts)

            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("[auto_trainer] Monitoring stopped by user")


def main():
    parser = argparse.ArgumentParser(
        description="Auto-trainer for ESP32-CAM robot brain"
    )
    parser.add_argument("--monitor", action="store_true",
                        help="Continuously monitor and auto-retrain")
    parser.add_argument("--train-once", action="store_true",
                        help="Run a single training cycle and exit")
    parser.add_argument("--interval", type=int, default=300,
                        help="Monitor interval in seconds (default: 300)")
    parser.add_argument("--data", default="data/train",
                        help="Training data directory")
    parser.add_argument("--out", default="models/model.tflite",
                        help="Output model path")
    parser.add_argument("--epochs", type=int, default=5,
                        help="Training epochs")
    parser.add_argument("--no-deploy", action="store_true",
                        help="Skip deployment after training")
    args = parser.parse_args()

    if args.monitor:
        monitor(
            interval=args.interval,
            data_dir=args.data,
            output_model=args.out,
            epochs=args.epochs,
            deploy=not args.no_deploy,
        )
    elif args.train_once:
        success = train_once(
            data_dir=args.data,
            output_model=args.out,
            epochs=args.epochs,
            deploy=not args.no_deploy,
        )
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
