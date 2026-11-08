#!/usr/bin/env python3
"""
trainer/fetch_data.py — Download targeted training images for the robot brain.

This script fetches public-domain / CC0 image datasets from the internet
so we can train a TinyML classifier on the PC, then export to .tflite for
the ESP32-CAM.

We do NOT scrape "the whole internet." Instead we grab small, curated sets:
- white ground markers (for distance estimation)
- obstacles / clutter (for avoidance training)
- clear floor / open space (for "safe to drive" class)

Usage:
    python3 trainer/fetch_data.py --out data/training --samples 100
"""

import argparse
import os
import sys
import urllib.request
import json

# Small, curated list of public image URLs (CC0 / public domain).
# These are example sources — replace with your preferred dataset mirrors.
DATA_SOURCES = {
    "white_marker": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/320px-PNG_transparency_demonstration_1.png",
    ],
    "obstacle": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/320px-PNG_transparency_demonstration_1.png",
    ],
    "clear_floor": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/320px-PNG_transparency_demonstration_1.png",
    ],
}

def download(url, out_path):
    try:
        urllib.request.urlretrieve(url, out_path)
        return True
    except Exception as e:
        print(f"[fetch] Failed {url}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Fetch training images")
    parser.add_argument("--out", default="data/training",
                        help="Output directory")
    parser.add_argument("--samples", type=int, default=50,
                        help="Samples per class")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    for cls in DATA_SOURCES:
        cls_dir = os.path.join(args.out, cls)
        os.makedirs(cls_dir, exist_ok=True)
        print(f"[fetch] Class: {cls} -> {cls_dir}")

        for i in range(args.samples):
            url = DATA_SOURCES[cls][i % len(DATA_SOURCES[cls])]
            out_path = os.path.join(cls_dir, f"{cls}_{i:04d}.jpg")
            if download(url, out_path):
                print(f"  [fetch] {cls}/{i:04d}.jpg")
            else:
                print(f"  [fetch] SKIP {cls}/{i:04d}.jpg")

    print(f"\n[fetch] Done. Images in {args.out}/")
    print("[fetch] Next: python3 trainer/train_model.py --data", args.out)

if __name__ == "__main__":
    main()
