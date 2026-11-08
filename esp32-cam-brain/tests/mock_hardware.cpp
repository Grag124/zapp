// ============================================================================
// tests/mock_hardware.cpp — Phase 0 laptop simulation
// ============================================================================
// This file provides mock implementations of all ESP32 Arduino APIs so the
// robot brain compiles and runs on a standard laptop (Linux/macOS/Windows)
// without any ESP32 hardware.
//
// Build: g++ -DPHASE0_SIMULATION=1 src/*.cpp tests/mock_hardware.cpp -o robot_sim
// Run:   ./robot_sim
//
// This is how we develop the brain today, before hardware arrives.

#include "config.h"
#include "camera_hal.h"

// --- Arduino API mocks ---
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <cstring>
#include <thread>
#include <chrono>

#ifndef LOW
#  define LOW 0
#endif
#ifndef HIGH
#  define HIGH 1
#endif

unsigned long millis() {
    return static_cast<unsigned long>(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count());
}

void delay(unsigned long ms) {
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

void pinMode(int pin, int mode) {
    // No-op in simulation.
}

void digitalWrite(int pin, int value) {
    // No-op in simulation.
}

int digitalRead(int pin) {
    return LOW;  // e-stop not pressed by default
}

unsigned long pulseIn(int pin, int value, unsigned long timeout) {
    return 0;  // no echo in simulation
}

void ledcSetup(uint8_t channel, uint32_t freq, uint8_t resolution) {
    // No-op in simulation.
}

void ledcAttachPin(uint8_t pin, uint8_t channel) {
    // No-op in simulation.
}

void ledcWrite(uint8_t channel, int value) {
    // No-op in simulation.
}

// --- ESP32 camera API mocks ---
// esp_camera_fb_get / esp_camera_fb_return are handled inside camera_hal.cpp
// simulation branch, so we just declare the types here for completeness.

namespace {
struct camera_fb_t {
    uint8_t* buf;
    size_t len;
    uint16_t width;
    uint16_t height;
};
}

typedef int esp_err_t;
#define ESP_OK 0

struct camera_config_t {
    int pin_pwdn;
    int pin_reset;
    int pin_xclk;
    int pin_sscb_sda;
    int pin_sscb_scl;
    int pin_d7;
    int pin_d6;
    int pin_d5;
    int pin_d4;
    int pin_d3;
    int pin_d2;
    int pin_d1;
    int pin_d0;
    int pin_vsync;
    int pin_href;
    int pin_pclk;
    int xclk_freq_hz;
    int ledc_timer;
    int ledc_channel;
    int pixel_format;
    int frame_size;
    int jpeg_quality;
    int fb_count;
    int grab_mode;
};

extern "C" {

esp_err_t esp_camera_init(const camera_config_t* config) {
    (void)config;
    return ESP_OK;
}

camera_fb_t* esp_camera_fb_get() {
    static camera_fb_t fb;
    static uint8_t buf[CAM_WIDTH * CAM_HEIGHT];
    fb.buf = buf;
    fb.len = CAM_WIDTH * CAM_HEIGHT;
    fb.width = CAM_WIDTH;
    fb.height = CAM_HEIGHT;
    return &fb;
}

void esp_camera_fb_return(camera_fb_t* fb) {
    (void)fb;
}

}

// --- SD_MMC API mocks ---
struct File {
    bool open_ = false;
    bool write(const uint8_t* data, size_t len) { (void)data; (void)len; return true; }
    bool write(const char* data) { (void)data; return true; }
    void println(const char* data) { (void)data; }
    void print(unsigned long v) { (void)v; }
    void print(int v) { (void)v; }
    void print(float v) { (void)v; }
    void print(const char* v) { (void)v; }
    void close() {}
};

struct SD_MMC {
    static bool begin(const char* point, bool mode) {
        (void)point; (void)mode;
        return true;
    }
    static uint64_t cardSize() {
        return 29500ULL * 1024 * 1024;  // 29.5 GB
    }
    static bool mkdir(const char* path) {
        (void)path;
        return true;
    }
    static File open(const char* path, uint8_t mode) {
        (void)path; (void)mode;
        File f;
        f.open_ = true;
        return f;
    }
    static void end() {
        // No-op.
    }
    static bool remove(const char* path) {
        (void)path;
        return true;
    }
};
