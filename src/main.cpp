#include <Arduino.h>
#include <SD_MMC.h>
#include <esp_camera.h>
#include "power_metrics.h"
#include "motor_control.h"

// ============================================================================
// HARDWARE PROFILE
// ============================================================================
// MCU:        ESP32-CAM on Type-C FT232 Backplane
// Driver:     DRV8833 Dual H-Bridge (2 logic pins per motor channel)
// Motors:     4x 7x15mm 19,000KV coreless brushed (2x CW Red/Blue, 2x CCW Black/White)
// Storage:    29.5 GB Micro SD (SD_MMC)
// Camera:     OV2640 (onboard)
// Power Bench: 5V USB + 3V AAA (DRV8833), PWM capped at 40%
// Power Flight: 1S 3.7V LiPo (300-500mAh, 30C+) baseline

// GPIO 4, 12, 13, 14, 15 RESERVED (SD_MMC + camera) - never for motors.
// Safe non-conflicting GPIOs (not used by camera OV2640 or SD_MMC):
//   ESP32-CAM camera uses: 0,4,5,18,19,22,23,25,26,27,34,35,36,39
//   SD_MMC uses:           4,12,13,14,15
//   Free:                  2, 16, 17, 32, 33  (only 5 pins)
static constexpr uint8_t PIN_MOTOR_LEFT_IN1  = 16;  // DRV8833 AIN1
static constexpr uint8_t PIN_MOTOR_LEFT_IN2  = 17;  // DRV8833 AIN2
static constexpr uint8_t PIN_MOTOR_RIGHT_IN1 = 32;  // DRV8833 BIN1
static constexpr uint8_t PIN_MOTOR_RIGHT_IN2 = 33;  // DRV8833 BIN2
static constexpr uint8_t PIN_TRIGGER = 2;           // HC-SR04 trigger (onboard LED too)
static constexpr uint8_t PIN_ECHO    = 255;         // Not wired (pin-constrained)
static constexpr uint8_t LEDC_CH_LEFT  = 0;
static constexpr uint8_t LEDC_CH_RIGHT = 1;

enum class PowerProfile { Bench, Flight };
static PowerProfile g_power_profile = PowerProfile::Bench;
static constexpr float kBenchMaxDutyFraction = 0.40f;
static constexpr uint32_t kBenchMaxDuty = static_cast<uint32_t>(
    PowerMetrics::LedcMaxDuty * kBenchMaxDutyFraction);

static const char* kSdLogPath = "/robot.log";

static void sd_log(const char* message) {
    if (!SD_MMC.begin("/sdcard", true)) return;
    File file = SD_MMC.open(kSdLogPath, FILE_APPEND);
    if (file) {
        file.print(millis());
        file.print(" | ");
        file.println(message);
        file.close();
    }
    SD_MMC.end();
}

static void sd_init() {
    if (!SD_MMC.begin("/sdcard", true)) {
        Serial.println("[SD] Mount failed.");
        return;
    }
    uint64_t cardSize = SD_MMC.cardSize() / (1024 * 1024);
    Serial.printf("[SD] Card mounted: %llu MB\n", cardSize);
    sd_log("[SD] Initialized.");
    SD_MMC.end();
}

static camera_config_t camera_config = {
    .pin_pwdn = -1, .pin_reset = -1, .pin_xclk = GPIO_NUM_0,
    .pin_sscb_sda = GPIO_NUM_26, .pin_sscb_scl = GPIO_NUM_27,
    .pin_d7 = GPIO_NUM_35, .pin_d6 = GPIO_NUM_34, .pin_d5 = GPIO_NUM_39,
    .pin_d4 = GPIO_NUM_36, .pin_d3 = GPIO_NUM_19, .pin_d2 = GPIO_NUM_18,
    .pin_d1 = GPIO_NUM_5, .pin_d0 = GPIO_NUM_4,
    .pin_vsync = GPIO_NUM_25, .pin_href = GPIO_NUM_23, .pin_pclk = GPIO_NUM_22,
    .xclk_freq_hz = 20000000, .ledc_timer = LEDC_TIMER_0, .ledc_channel = LEDC_CHANNEL_0,
    .pixel_format = PIXFORMAT_GRAYSCALE, .frame_size = FRAMESIZE_QVGA,
    .jpeg_quality = 12, .fb_count = 1, .grab_mode = CAMERA_GRAB_WHEN_EMPTY
};

static bool camera_init() {
    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        Serial.printf("[CAM] Init failed: 0x%x\n", err);
        return false;
    }
    Serial.println("[CAM] OV2640 initialized.");
    sd_log("[CAM] Initialized.");
    return true;
}

static void camera_capture_log() {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) { Serial.println("[CAM] Capture failed."); return; }
    Serial.printf("[CAM] Captured: %u bytes, %ux%u\n", fb->len, fb->width, fb->height);
    char msg[64];
    snprintf(msg, sizeof(msg), "[CAM] Captured %u bytes", fb->len);
    sd_log(msg);
    esp_camera_fb_return(fb);
}

static float read_distance_cm() {
    if (PIN_ECHO == 255) return -1.0f;  // Echo pin not wired (pin-constrained)
    digitalWrite(PIN_TRIGGER, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_TRIGGER, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_TRIGGER, LOW);
    unsigned long duration = pulseIn(PIN_ECHO, HIGH, 30000);
    if (duration == 0) return -1.0f;
    return duration * 0.0343f / 2.0f;
}

class AIBrain {
public:
    AIBrain(float max_speed = 0.6f, float stop_distance_cm = 20.0f,
            float turn_speed = 0.45f)
        : max_speed_(max_speed), stop_distance_cm_(stop_distance_cm),
          turn_speed_(turn_speed), mode_("manual") {}

    void set_mode(const char* mode) {
        if (strcmp(mode, "manual") == 0 || strcmp(mode, "autonomous") == 0)
            mode_ = mode;
    }

    const char* decide(float distance_cm) {
        if (strcmp(mode_.c_str(), "manual") == 0) return nullptr;
        if (distance_cm < 0.0f) return "forward";
        if (distance_cm > stop_distance_cm_) return "forward";
        if (distance_cm > stop_distance_cm_ / 2.0f) return "turn_left";
        return "stop";
    }

    float max_speed() const { return max_speed_; }
    float turn_speed() const { return turn_speed_; }
    const char* mode() const { return mode_.c_str(); }

private:
    float max_speed_;
    float stop_distance_cm_;
    float turn_speed_;
    String mode_;
};

// ============================================================================
// VISION TRACKER (autonomous vision algorithm)
// ============================================================================
// Analyzes the OV2640 grayscale pixel stream for a bright visual target,
// computes its horizontal centroid, and returns a steering value (-1..1)
// that orients the DRV8833-driven motors toward the target.
class VisionTracker {
public:
    VisionTracker(uint16_t width = 320, uint16_t height = 240,
                  uint8_t brightness_threshold = 200)
        : width_(width), height_(height), threshold_(brightness_threshold),
          enabled_(false), gain_(0.8f), base_speed_(0.45f),
          search_speed_(0.30f) {}

    void set_enabled(bool en) { enabled_ = en; }
    bool enabled() const { return enabled_; }
    void set_gain(float g) { gain_ = std::clamp<float>(g, 0.0f, 2.0f); }
    void set_base_speed(float s) { base_speed_ = std::clamp<float>(s, 0.0f, 1.0f); }
    void set_threshold(uint8_t t) { threshold_ = t; }

    // Capture a grayscale frame, find bright target pixels, compute centroid.
    // Returns steering in [-1, 1]: negative = target left (turn left),
    // positive = target right (turn right). 0.0 = no target or disabled.
    float track() {
        if (!enabled_) return 0.0f;

        camera_fb_t* fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("[VISION] Frame capture failed.");
            return 0.0f;
        }

        // Grayscale frame: each byte is one pixel intensity (0..255).
        uint8_t* pixels = reinterpret_cast<uint8_t*>(fb->buf);
        size_t len = fb->len;

        uint32_t sum_x = 0, sum_y = 0, count = 0;
        for (size_t i = 0; i < len; i++) {
            if (pixels[i] > threshold_) {
                uint16_t x = static_cast<uint16_t>(i % width_);
                uint16_t y = static_cast<uint16_t>(i / width_);
                sum_x += x;
                sum_y += y;
                count++;
            }
        }

        esp_camera_fb_return(fb);

        if (count == 0) {
            // No target visible -> slowly rotate to search.
            Serial.println("[VISION] No target found; searching...");
            return -search_speed_;  // spin left to scan
        }

        float cx = static_cast<float>(sum_x) / static_cast<float>(count);
        float cy = static_cast<float>(sum_y) / static_cast<float>(count);
        float center_x = static_cast<float>(width_) / 2.0f;
        float error = (cx - center_x) / center_x;  // -1 .. 1

        // Steer toward target: left = base + steer, right = base - steer.
        float steer = error * gain_;
        steer = std::clamp<float>(steer, -1.0f, 1.0f);

        Serial.printf("[VISION] count=%u cx=%.1f cy=%.1f error=%.2f steer=%.2f\n",
                      count, cx, cy, error, steer);
        return steer;
    }

    // Apply steering to differential-drive throttles.
    void apply_steering(float steer, MotorController* ctrl) {
        if (!ctrl) return;
        float left = std::clamp<float>(base_speed_ + steer, -1.0f, 1.0f);
        float right = std::clamp<float>(base_speed_ - steer, -1.0f, 1.0f);
        ctrl->setThrottles(left, right);
    }

private:
    uint16_t width_;
    uint16_t height_;
    uint8_t threshold_;
    bool enabled_;
    float gain_;
    float base_speed_;
    float search_speed_;
};

// ============================================================================
// ROBOT BRAIN (ported from robot_brain.py)
// ============================================================================
class Robot {
public:
    Robot() {
        left_motor_ = new MotorChannel(LEDC_CH_LEFT, PIN_MOTOR_LEFT_IN1, PIN_MOTOR_LEFT_IN2);
        right_motor_ = new MotorChannel(LEDC_CH_RIGHT, PIN_MOTOR_RIGHT_IN1, PIN_MOTOR_RIGHT_IN2);
        left_ramp_ = new ThrottleRamp(0.05f);
        right_ramp_ = new ThrottleRamp(0.05f);
        controller_ = new MotorController(left_motor_, right_motor_);
        controller_->attachRamps(left_ramp_, right_ramp_);
        brain_ = new AIBrain();
        vision_ = new VisionTracker();
    }

    ~Robot() {
        delete left_ramp_; delete right_ramp_;
        delete left_motor_; delete right_motor_;
        delete controller_; delete brain_;
        delete vision_;
    }

    bool begin() {
        if (PIN_TRIGGER != 255) pinMode(PIN_TRIGGER, OUTPUT);
        if (PIN_ECHO != 255) pinMode(PIN_ECHO, INPUT);
        if (!controller_->begin()) { Serial.println("[MOTOR] Init failed."); return false; }
        applyPowerProfile();
        Serial.println("[MOTOR] DRV8833 + LEDC initialized.");
        sd_log("[MOTOR] Initialized.");
        if (!camera_init()) { Serial.println("[CAM] Init failed."); return false; }
        sd_init();
        Serial.println("[ROBOT] Ready.");
        sd_log("[ROBOT] Ready.");
        return true;
    }

    void applyPowerProfile() {
        uint32_t cap = (g_power_profile == PowerProfile::Bench) ? kBenchMaxDuty : PowerMetrics::LedcMaxDuty;
        left_motor_->setMaxDuty(cap);
        right_motor_->setMaxDuty(cap);
        Serial.printf("[POWER] %s (max duty %u/%u)\n",
                      g_power_profile == PowerProfile::Flight ? "Flight 3.7V LiPo" : "Bench 40% PWM",
                      cap, PowerMetrics::LedcMaxDuty);
    }

    void set_power_profile(PowerProfile profile) {
        g_power_profile = profile;
        applyPowerProfile();
    }

    void control_wheels(const char* direction) {
        float ms = brain_->max_speed();
        float ts = brain_->turn_speed();
        if (strcmp(direction, "forward") == 0)      controller_->setThrottles(ms, ms);
        else if (strcmp(direction, "backward") == 0) controller_->setThrottles(-ms, -ms);
        else if (strcmp(direction, "left") == 0)    controller_->setThrottles(-ts, ts);
        else if (strcmp(direction, "right") == 0)   controller_->setThrottles(ts, -ts);
        else                                         controller_->stop();
        Serial.printf("[WHEELS] %s\n", direction);
        char msg[64]; snprintf(msg, sizeof(msg), "[WHEELS] %s", direction); sd_log(msg);
    }

    void stop() { controller_->stop(); Serial.println("[WHEELS] Stopped."); sd_log("[WHEELS] Stopped."); }

    float read_distance() {
        float d = read_distance_cm();
        if (d >= 0.0f) Serial.printf("[SENSOR] Distance: %.1f cm\n", d);
        else Serial.println("[SENSOR] No echo.");
        return d;
    }

    void set_brain_mode(const char* mode) {
        brain_->set_mode(mode);
        Serial.printf("[BRAIN] Mode: %s\n", brain_->mode());
    }

    void set_vision_enabled(bool en) {
        vision_->set_enabled(en);
        Serial.printf("[VISION] %s\n", en ? "enabled" : "disabled");
        char msg[32]; snprintf(msg, sizeof(msg), "[VISION] %s", en ? "enabled" : "disabled"); sd_log(msg);
    }

    bool vision_enabled() const { return vision_->enabled(); }

    void set_vision_gain(float g) { vision_->set_gain(g); }
    void set_vision_base_speed(float s) { vision_->set_base_speed(s); }
    void set_vision_threshold(uint8_t t) { vision_->set_threshold(t); }

    // One tick of autonomous behavior. Uses vision tracking when enabled,
    // otherwise falls back to ultrasonic + AIBrain obstacle avoidance.
    void run_autonomous_step(uint32_t now_ms) {
        if (vision_->enabled()) {
            float steer = vision_->track();
            vision_->apply_steering(steer, controller_);
            return;
        }

        float distance = read_distance();
        const char* action = brain_->decide(distance);
        if (!action) action = "stop";
        if (strcmp(action, "turn_left") == 0) action = "left";
        if (strcmp(action, "turn_right") == 0) action = "right";
        Serial.printf("[BRAIN] Decided: %s\n", action);
        control_wheels(action);
        (void)now_ms;
    }

    void calculate_lift_power(float mass_grams) {
        float power = (mass_grams / 1000.0f) * 9.81f;
        Serial.printf("[PHYSICS] Lift %g g -> %.2f N thrust\n", mass_grams, power);
        char msg[64]; snprintf(msg, sizeof(msg), "[PHYSICS] Lift %g g -> %.2f N", mass_grams, power); sd_log(msg);
    }

    MotorController* controller() { return controller_; }
    AIBrain* brain() { return brain_; }
    VisionTracker* vision() { return vision_; }

private:
    MotorChannel* left_motor_;
    MotorChannel* right_motor_;
    ThrottleRamp* left_ramp_;
    ThrottleRamp* right_ramp_;
    MotorController* controller_;
    AIBrain* brain_;
    VisionTracker* vision_;
};

static Robot* g_robot = nullptr;

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    Serial.println("\n=== ESP32-CAM Robot Brain ===");
    Serial.println("DRV8833 + 4x coreless + OV2640 + SD_MMC");

    g_robot = new Robot();
    if (!g_robot->begin()) { Serial.println("[FATAL] Robot init failed."); return; }

    g_robot->set_power_profile(PowerProfile::Bench);
    g_robot->calculate_lift_power(300.0f);

    Serial.println("\nW=Forward A=Left S=Backward D=Right Q=Quit");
    Serial.println("M=Toggle autonomous R=Distance L=Lift test F=Flight B=Bench C=Camera V=Vision");
    Serial.println("============================\n");
}

void loop() {
    if (!g_robot) return;

    static char cmd_buf[32];
    static int cmd_idx = 0;
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            if (cmd_idx > 0) { cmd_buf[cmd_idx] = '\0'; handle_command(cmd_buf); cmd_idx = 0; }
        } else if (cmd_idx < (int)sizeof(cmd_buf) - 1) {
            cmd_buf[cmd_idx++] = c;
        }
    }

    static uint32_t last_tick = 0;
    uint32_t now = millis();
    if (strcmp(g_robot->brain()->mode(), "autonomous") == 0 && now - last_tick > 200) {
        g_robot->run_autonomous_step(now);
        last_tick = now;
    }
    delay(10);
}

static void handle_command(char* cmd) {
    for (int i = 0; cmd[i]; i++) cmd[i] = tolower(cmd[i]);
    if (strcmp(cmd, "w") == 0) g_robot->control_wheels("forward");
    else if (strcmp(cmd, "a") == 0) g_robot->control_wheels("left");
    else if (strcmp(cmd, "s") == 0) g_robot->control_wheels("backward");
    else if (strcmp(cmd, "d") == 0) g_robot->control_wheels("right");
    else if (strcmp(cmd, "q") == 0) { g_robot->stop(); Serial.println("[ROBOT] Shutdown."); }
    else if (strcmp(cmd, "m") == 0) {
        const char* next = strcmp(g_robot->brain()->mode(), "manual") == 0 ? "autonomous" : "manual";
        g_robot->set_brain_mode(next);
        if (strcmp(next, "autonomous") == 0) g_robot->run_autonomous_step(millis());
    } else if (strcmp(cmd, "r") == 0) g_robot->read_distance();
    else if (strcmp(cmd, "l") == 0) g_robot->calculate_lift_power(300.0f);
    else if (strcmp(cmd, "f") == 0) g_robot->set_power_profile(PowerProfile::Flight);
    else if (strcmp(cmd, "b") == 0) g_robot->set_power_profile(PowerProfile::Bench);
    else if (strcmp(cmd, "c") == 0) camera_capture_log();
    else if (strcmp(cmd, "v") == 0) g_robot->set_vision_enabled(!g_robot->vision_enabled());
    else if (strlen(cmd) == 0) { /* no-op */ }
    else Serial.println("Invalid! W/A/S/D/Q/M/R/L/F/B/C/V");
}
