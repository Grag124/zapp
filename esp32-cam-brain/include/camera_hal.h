#ifndef CAMERA_HAL_H
#define CAMERA_HAL_H

#include "config.h"

#include <cstdint>
#include <cstddef>

#ifdef PHASE0_SIMULATION
#  include <cstdio>
#  include <ctime>
#  include <random>
#else
#  include <esp_camera.h>
#  include <SD_MMC.h>
#endif

// ============================================================================
// CAMERA_HAL — ESP32-CAM (OV2640) abstraction
// ============================================================================
// Captures grayscale QVGA frames, optionally saves debug JPEGs to SD,
// and exposes the raw pixel buffer for the perception layer.
//
// Think of this as the robot's "eyes." It handles the hardware fiddly bits
// (clocks, I2C, DMA buffers) so perception just sees a flat array of bytes.
//
// Phase 0 (simulation): generates synthetic frames with a bright blob at a
// configurable (x, y) so you can test vision tracking without a camera.

class CameraHAL {
public:
    CameraHAL();

    // Initialize the OV2640 sensor. Returns true on success.
    bool begin();

    // Capture one grayscale frame. Returns true if a frame is available.
    // Call getFrame() afterwards to read pixels.
    bool capture();

    // Return pointer to the current grayscale frame buffer.
    // Buffer size is width() * height() bytes (one byte per pixel).
    const uint8_t* getFrame() const;

    uint16_t width() const { return CAM_WIDTH; }
    uint16_t height() const { return CAM_HEIGHT; }

    // Save the current frame as a debug JPEG to SD (filename includes timestamp).
    void saveDebugFrame(const char* label = "frame");

    // Simulation-only: set the bright-blob position (normalized 0..1).
    void setSimTargetPosition(float nx, float ny);

    // Simulation-only: enable/disable target presence.
    void setSimTargetPresent(bool present);

private:
#ifdef PHASE0_SIMULATION
    uint8_t sim_frame_[CAM_WIDTH * CAM_HEIGHT];
    float   sim_target_nx_ = 0.5f;
    float   sim_target_ny_ = 0.5f;
    bool    sim_target_present_ = true;
#else
    camera_fb_t* fb_ = nullptr;
#endif
};

// Global camera instance (singleton pattern, like Serial or Wire).
extern CameraHAL camera;

#endif  // CAMERA_HAL_H
