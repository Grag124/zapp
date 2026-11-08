#include "camera_hal.h"

#ifdef PHASE0_SIMULATION
#  include <cstring>
#  include <cmath>
#else
#  include <SD_MMC.h>
#endif

CameraHAL::CameraHAL() {
#ifdef PHASE0_SIMULATION
    std::memset(sim_frame_, 0, sizeof(sim_frame_));
#endif
}

bool CameraHAL::begin() {
#ifdef PHASE0_SIMULATION
    std::printf("[CAM] Simulation mode: synthetic grayscale %dx%d\n",
                CAM_WIDTH, CAM_HEIGHT);
    return true;
#else
    camera_config_t config = {
        .pin_pwdn = -1, .pin_reset = -1, .pin_xclk = GPIO_NUM_0,
        .pin_sscb_sda = GPIO_NUM_26, .pin_sscb_scl = GPIO_NUM_27,
        .pin_d7 = GPIO_NUM_35, .pin_d6 = GPIO_NUM_34, .pin_d5 = GPIO_NUM_39,
        .pin_d4 = GPIO_NUM_36, .pin_d3 = GPIO_NUM_19, .pin_d2 = GPIO_NUM_18,
        .pin_d1 = GPIO_NUM_5,  .pin_d0 = GPIO_NUM_4,
        .pin_vsync = GPIO_NUM_25, .pin_href = GPIO_NUM_23, .pin_pclk = GPIO_NUM_22,
        .xclk_freq_hz = 20000000, .ledc_timer = LEDC_TIMER_0,
        .ledc_channel = LEDC_CHANNEL_0,
        .pixel_format = PIXFORMAT_GRAYSCALE, .frame_size = FRAMESIZE_QVGA,
        .jpeg_quality = CAM_QUALITY, .fb_count = CAM_FB_COUNT,
        .grab_mode = CAMERA_GRAB_WHEN_EMPTY
    };
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        std::printf("[CAM] Init failed: 0x%x\n", err);
        return false;
    }
    std::printf("[CAM] OV2640 initialized (%dx%d grayscale)\n", CAM_WIDTH, CAM_HEIGHT);
    return true;
#endif
}

bool CameraHAL::capture() {
#ifdef PHASE0_SIMULATION
    // Generate a synthetic grayscale frame: dark background + bright blob
    std::memset(sim_frame_, 30, sizeof(sim_frame_));  // dark background
    if (sim_target_present_) {
        int cx = static_cast<int>(sim_target_nx_ * CAM_WIDTH);
        int cy = static_cast<int>(sim_target_ny_ * CAM_HEIGHT);
        int radius = 30;
        for (int y = cy - radius; y < cy + radius; y++) {
            for (int x = cx - radius; x < cx + radius; x++) {
                if (x >= 0 && x < CAM_WIDTH && y >= 0 && y < CAM_HEIGHT) {
                    int dx = x - cx, dy = y - cy;
                    if (dx*dx + dy*dy < radius*radius) {
                        sim_frame_[y * CAM_WIDTH + x] = 240;  // bright blob
                    }
                }
            }
        }
    }
    return true;
#else
    if (fb_) {
        esp_camera_fb_return(fb_);
        fb_ = nullptr;
    }
    fb_ = esp_camera_fb_get();
    return fb_ != nullptr;
#endif
}

const uint8_t* CameraHAL::getFrame() const {
#ifdef PHASE0_SIMULATION
    return sim_frame_;
#else
    return fb_ ? reinterpret_cast<const uint8_t*>(fb_->buf) : nullptr;
#endif
}

void CameraHAL::saveDebugFrame(const char* label) {
#ifdef PHASE0_SIMULATION
    std::printf("[CAM] [SIM] Saved debug frame: %s\n", label);
#else
    if (!fb_) return;
    if (!SD_MMC.begin(SD_MOUNT_POINT, true)) return;
    char path[64];
    std::snprintf(path, sizeof(path), "/sdcard/%s_%lu.jpg", label,
                  static_cast<unsigned long>(millis()));
    File f = SD_MMC.open(path, FILE_WRITE);
    if (f) {
        f.write(fb_->buf, fb_->len);
        f.close();
        std::printf("[CAM] Saved %s (%u bytes)\n", path, fb_->len);
    }
    SD_MMC.end();
#endif
}

void CameraHAL::setSimTargetPosition(float nx, float ny) {
#ifdef PHASE0_SIMULATION
    sim_target_nx_ = nx;
    sim_target_ny_ = ny;
#endif
}

void CameraHAL::setSimTargetPresent(bool present) {
#ifdef PHASE0_SIMULATION
    sim_target_present_ = present;
#endif
}

CameraHAL camera;
