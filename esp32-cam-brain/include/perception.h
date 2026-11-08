#ifndef PERCEPTION_H
#define PERCEPTION_H

#include "config.h"
#include "camera_hal.h"

#include <cstdint>
#include <cstddef>
#include <string>

#ifdef PHASE0_SIMULATION
#else
#  include <esp_camera.h>
#endif

// ============================================================================
// PERCEPTION_H — TinyML + classical CV interface
// ============================================================================
// Three perception primitives:
//   1) Ground-marker distance estimation (known-size marker → cm).
//   2) Obstacle edge detection (dark horizon line = cliff/edge).
//   3) TinyML object classifier interface (stubbed, ready for .tflite).
//
// Think of this as the robot's "visual cortex." It turns raw pixels into
// meaningful labels: "I see a white marker 30 cm ahead" or "edge ahead."

struct ObjectDetection {
    std::string label;   // e.g. "white_marker", "obstacle", "unknown"
    float     confidence = 0.0f;   // 0..1
    float     distance_cm = -1.0f; // -1 = unknown
    int16_t   centroid_x = -1;     // pixel x of target
    int16_t   centroid_y = -1;     // pixel y of target
};

class Perception {
public:
    Perception();

    // Run full perception on the latest camera frame.
    // Returns an ObjectDetection with label, confidence, distance, centroid.
    ObjectDetection analyze();

    // Calibration: place a MARKER_SIZE_CM marker at known distance,
    // count bright pixels, compute PIXELS_PER_CM.
    void calibrateMarker(float known_distance_cm);

    float getPixelsPerCm() const { return pixels_per_cm_; }

    // TinyML classifier stub: set when model is deployed to SD.
    void setModelLoaded(bool loaded) { model_loaded_ = loaded; }
    bool isModelLoaded() const { return model_loaded_; }

private:
    float pixels_per_cm_;
    bool  model_loaded_ = false;
};

// Global perception instance.
extern Perception perception;

#endif  // PERCEPTION_H
