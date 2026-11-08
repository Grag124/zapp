#include "perception.h"

#include <cmath>
#include <algorithm>

Perception::Perception()
    : pixels_per_cm_(PIXELS_PER_CM) {}

ObjectDetection Perception::analyze() {
    ObjectDetection det;

    const uint8_t* pixels = camera.getFrame();
    if (!pixels) {
        det.label = "no_frame";
        return det;
    }

    size_t len = static_cast<size_t>(CAM_WIDTH) * CAM_HEIGHT;

    // 1) Bright-target detection (ground marker / reflective object).
    uint32_t sum_x = 0, sum_y = 0, count = 0;
    for (size_t i = 0; i < len; i++) {
        if (pixels[i] > VISION_BRIGHTNESS_THRESHOLD) {
            uint16_t x = static_cast<uint16_t>(i % CAM_WIDTH);
            uint16_t y = static_cast<uint16_t>(i / CAM_WIDTH);
            sum_x += x;
            sum_y += y;
            count++;
        }
    }

    if (count > 0) {
        det.centroid_x = static_cast<int16_t>(sum_x / count);
        det.centroid_y = static_cast<int16_t>(sum_y / count);

        // 2) Distance estimation via known-size marker.
        // Pixel count scales with marker area; distance ∝ 1/sqrt(count).
        // This is a rough heuristic — calibrated at runtime.
        float est_distance = MARKER_SIZE_CM * PIXELS_PER_CM /
                             (static_cast<float>(count) / 100.0f + 1.0f);
        det.distance_cm = est_distance;

        det.label = "bright_target";
        det.confidence = std::min<float>(count / 500.0f, 1.0f);
    } else {
        // 3) Edge detection: check if bottom rows are dark (cliff ahead).
        // If the lower portion of the image is uniformly dark, we may be
        // approaching an edge or drop-off.
        uint32_t bottom_sum = 0;
        int bottom_rows = CAM_HEIGHT / 4;
        for (int y = CAM_HEIGHT - bottom_rows; y < CAM_HEIGHT; y++) {
            for (int x = 0; x < CAM_WIDTH; x++) {
                bottom_sum += pixels[y * CAM_WIDTH + x];
            }
        }
        float bottom_avg = static_cast<float>(bottom_sum) /
                           (bottom_rows * CAM_WIDTH);
        if (bottom_avg < 40.0f) {
            det.label = "edge_ahead";
            det.confidence = 0.6f;
            det.distance_cm = -1.0f;
        } else {
            det.label = "clear";
            det.confidence = 0.5f;
        }
    }

    return det;
}

void Perception::calibrateMarker(float known_distance_cm) {
    // Place marker at known_distance_cm, capture frame, count bright pixels,
    // then compute PIXELS_PER_CM. Call this once during bench calibration.
    const uint8_t* pixels = camera.getFrame();
    if (!pixels) return;

    size_t len = static_cast<size_t>(CAM_WIDTH) * CAM_HEIGHT;
    uint32_t count = 0;
    for (size_t i = 0; i < len; i++) {
        if (pixels[i] > VISION_BRIGHTNESS_THRESHOLD) count++;
    }

    if (count > 0) {
        // Pixels per cm ≈ sqrt(count) / marker_size_cm, scaled by distance.
        pixels_per_cm_ = static_cast<float>(count) /
                         (MARKER_SIZE_CM * known_distance_cm);
    }
}

Perception perception;
