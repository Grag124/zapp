#!/usr/bin/env python3
"""
trainer/model_version_manager.py — Model version control.

Manages version history of exported .tflite models, tracks accuracy metrics,
and supports auto-rollback if a new model's accuracy drops below a threshold.

Features:
- Save model versions with metadata (accuracy, timestamp, notes)
- List all versions
- Rollback to a previous version
- Get the "best" (highest accuracy) version
- Auto-rollback logic

Usage:
    python3 trainer/model_version_manager.py --save models/model.tflite --acc 0.92 --notes "v1"
    python3 trainer/model_version_manager.py --list
    python3 trainer/model_version_manager.py --rollback 2
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime


class ModelVersionManager:
    def __init__(self, versions_dir: str = "models/versions"):
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.versions_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> dict:
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {"versions": []}
        return {"versions": []}

    def _save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def save_version(self, model_path: str, accuracy: float = 0.0,
                     notes: str = "", auto_rollback_threshold: float = 0.0):
        """
        Save a new model version. Copies the .tflite file into the versions dir
        and records metadata in the index.

        Returns the version number assigned.
        """
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        version_num = len(self.index["versions"]) + 1
        version_dir = self.versions_dir / f"v{version_num:03d}"
        version_dir.mkdir(parents=True, exist_ok=True)

        dest_model = version_dir / "model.tflite"
        shutil.copy2(model_path, dest_model)

        entry = {
            "version": version_num,
            "path": str(dest_model),
            "accuracy": accuracy,
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
            "size_bytes": dest_model.stat().st_size,
        }
        self.index["versions"].append(entry)
        self._save_index()

        # Auto-rollback check: if this version is worse than previous best,
        # and threshold is set, roll back.
        if auto_rollback_threshold > 0 and len(self.index["versions"]) > 1:
            best = self.get_best_version()
            if best and accuracy < best["accuracy"] * auto_rollback_threshold:
                print(f"[version_manager] New model accuracy {accuracy:.3f} below "
                      f"threshold {best['accuracy'] * auto_rollback_threshold:.3f} — rolling back")
                self.rollback(version_num)

        print(f"[version_manager] Saved v{version_num:03d} "
              f"(acc={accuracy:.3f}, size={entry['size_bytes']} bytes)")
        return version_num

    def list_versions(self) -> list:
        """Return list of all version entries."""
        return self.index["versions"]

    def get_best_version(self) -> dict:
        """Return the version entry with the highest accuracy."""
        versions = self.index["versions"]
        if not versions:
            return None
        return max(versions, key=lambda v: v["accuracy"])

    def get_version(self, version_num: int) -> dict:
        """Get a specific version entry by number."""
        for v in self.index["versions"]:
            if v["version"] == version_num:
                return v
        return None

    def rollback(self, to_version: int) -> bool:
        """
        Roll back to a previous version by copying it over models/model.tflite.
        Returns True on success.
        """
        entry = self.get_version(to_version)
        if not entry:
            print(f"[version_manager] Version v{to_version:03d} not found")
            return False

        model_path = Path(entry["path"])
        if not model_path.exists():
            print(f"[version_manager] Model file missing: {model_path}")
            return False

        dest = Path("models/model.tflite")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(model_path, dest)

        print(f"[version_manager] Rolled back to v{to_version:03d} "
              f"(acc={entry['accuracy']:.3f})")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Manage model versions for ESP32-CAM robot brain"
    )
    parser.add_argument("--save", help="Save a model version (path to .tflite)")
    parser.add_argument("--acc", type=float, default=0.0,
                        help="Accuracy metric for the saved model")
    parser.add_argument("--notes", default="", help="Notes for the saved version")
    parser.add_argument("--auto-rollback-threshold", type=float, default=0.0,
                        help="Rollback if new accuracy < best * threshold (0=disabled)")
    parser.add_argument("--list", action="store_true", help="List all versions")
    parser.add_argument("--best", action="store_true", help="Show best version")
    parser.add_argument("--rollback", type=int, metavar="VERSION",
                        help="Roll back to a specific version number")
    args = parser.parse_args()

    mgr = ModelVersionManager()

    if args.save:
        mgr.save_version(
            args.save,
            accuracy=args.acc,
            notes=args.notes,
            auto_rollback_threshold=args.auto_rollback_threshold,
        )
    elif args.list:
        versions = mgr.list_versions()
        if not versions:
            print("No versions saved yet.")
        else:
            print(f"{'Version':<10} {'Accuracy':<10} {'Size (KB)':<12} {'Notes'}")
            print("-" * 60)
            for v in versions:
                size_kb = v["size_bytes"] / 1024
                print(f"v{v['version']:03d}    {v['accuracy']:<10.3f} "
                      f"{size_kb:<12.1f} {v['notes']}")
    elif args.best:
        best = mgr.get_best_version()
        if best:
            print(f"Best version: v{best['version']:03d} "
                  f"(acc={best['accuracy']:.3f}, {best['notes']})")
        else:
            print("No versions saved yet.")
    elif args.rollback is not None:
        mgr.rollback(args.rollback)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
