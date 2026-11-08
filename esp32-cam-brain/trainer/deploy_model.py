#!/usr/bin/env python3
"""
trainer/deploy_model.py — Copy the trained .tflite model to the SD card image.

The ESP32-CAM reads the model from /sdcard/model.tflite at runtime. This
script prepares an SD card image (or copies directly to a mounted SD card)
so the robot can run inference locally — no cloud dependency.

Usage:
    # Copy to a mounted SD card:
    python3 trainer/deploy_model.py --model models/model.tflite --sd /mnt/sdcard

    # Or create a disk image for flashing later:
    python3 trainer/deploy_model.py --model models/model.tflite --image sd_card.img
"""

import argparse
import os
import sys
import shutil

def main():
    parser = argparse.ArgumentParser(description="Deploy model to SD card")
    parser.add_argument("--model", required=True, help="Path to .tflite file")
    parser.add_argument("--sd", help="Mounted SD card path")
    parser.add_argument("--image", help="Output disk image path")
    args = parser.parse_args()

    if not os.path.isfile(args.model):
        print(f"[deploy] Model not found: {args.model}")
        sys.exit(1)

    if args.sd:
        dest_dir = os.path.join(args.sd, "model.tflite")
        os.makedirs(os.path.join(args.sd), exist_ok=True)
        shutil.copy(args.model, dest_dir)
        print(f"[deploy] Copied {args.model} -> {dest_dir}")
        print("[deploy] Insert SD card into ESP32-CAM and reboot.")

    if args.image:
        # Create a simple FAT-like image placeholder; in production you'd
        # use mkfs.fat and mcopy to populate a real FAT16/FAT32 image.
        size_mb = 32
        with open(args.image, "wb") as f:
            f.truncate(size_mb * 1024 * 1024)
        print(f"[deploy] Created {args.image} ({size_mb} MB)")
        print("[deploy] Format as FAT and copy model.tflite to /sdcard/")

    print("\n[deploy] On the ESP32-CAM, perception checks MODEL_PATH:")
    print("         /sdcard/model.tflite")
    print("[deploy] Then cognition uses ML confidence with fallback rules.")

if __name__ == "__main__":
    main()
