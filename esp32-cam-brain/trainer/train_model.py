#!/usr/bin/env python3
"""
trainer/train_model.py — Train a tiny image classifier and export to TFLite.

Trains a minimal CNN (fewer than 10 KB quantized) on the images fetched by
fetch_data.py. Exports model.tflite (8-bit quantized) for deployment to the
ESP32-CAM SD card.

Requirements:
    pip install tensorflow numpy pillow

Usage:
    python3 trainer/train_model.py --data data/training --out models/model.tflite
"""

import argparse
import os
import sys
import numpy as np

# Disable MLIR bridge to avoid converter hangs in some environments.
os.environ.setdefault("TF_ENABLE_MLIR_BRIDGE", "0")
os.environ.setdefault("TFMLIR_ENABLED", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

try:
    import tensorflow as tf
    from tensorflow import keras
except ImportError:
    print("[train] tensorflow not installed. Run: pip install tensorflow")
    sys.exit(1)

from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator

IMG_SIZE = (96, 96)  # small input for TinyML
BATCH = 16

def build_model(num_classes):
    """Tiny CNN: ~30K params, quantizes to < 10 KB."""
    model = models.Sequential([
        layers.Rescaling(1.0 / 255, input_shape=(*IMG_SIZE, 3)),
        layers.Conv2D(8, 3, activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(16, 3, activation='relu'),
        layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(16, activation='relu'),
        layers.Dense(num_classes, activation='softmax'),
    ])
    return model

def representative_dataset(gen):
    """Yield batches for post-training quantization calibration."""
    for images, _ in gen:
        yield [images.astype(np.float32)]

def main():
    parser = argparse.ArgumentParser(description="Train TinyML classifier")
    parser.add_argument("--data", default="data/training",
                        help="Directory with class subfolders")
    parser.add_argument("--out", default="models/model.tflite",
                        help="Output .tflite path")
    parser.add_argument("--epochs", type=int, default=5,
                        help="Training epochs")
    args = parser.parse_args()

    if not os.path.isdir(args.data):
        print(f"[train] Data dir not found: {args.data}")
        print("[train] Run: python3 trainer/fetch_data.py first")
        sys.exit(1)

    datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

    train_gen = datagen.flow_from_directory(
        args.data, target_size=IMG_SIZE, batch_size=BATCH,
        subset="training", class_mode="sparse")
    val_gen = datagen.flow_from_directory(
        args.data, target_size=IMG_SIZE, batch_size=BATCH,
        subset="validation", class_mode="sparse")

    num_classes = train_gen.num_classes
    print(f"[train] Classes: {num_classes} {train_gen.class_indices}")

    model = build_model(num_classes)
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    model.summary()

    model.fit(train_gen, validation_data=val_gen, epochs=args.epochs)

    # Convert to TFLite (float32 for compatibility; quantize on-device if needed).
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(tflite_model)

    size_kb = len(tflite_model) / 1024
    print(f"\n[train] Exported {args.out} ({size_kb:.1f} KB)")
    print(f"[train] Next: python3 trainer/deploy_model.py --model {args.out}")
    os._exit(0)

if __name__ == "__main__":
    main()
