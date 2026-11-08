#ifndef CONFIG_H
#define CONFIG_H

#include <cstdint>

// ============================================================================
// CONFIG.H — Pin map, PWM constants, model paths, safety limits
// ============================================================================
// Think of this file as the robot's "blueprint." Every pin, every limit,
// every magic number lives here so you can tweak hardware without hunting
// through implementation files. If you change a pin, change it once here.

// ----------------------------------------------------------------------------
// POWER / PWM SAFETY
// ----------------------------------------------------------------------------
// Bench-test rule: PWM duty capped at 40% of 8-bit range (≤ 102 of 255).
// This keeps the 4x coreless motors from spinning wildly on 3V AAA cells.
// Flight mode (3.7V LiPo) can go to full 255 when we upgrade power.
static constexpr uint8_t PWM_MAX_DUTY_BENCH = 102;   // 40% of 255
static constexpr uint8_t PWM_MAX_DUTY_FLIGHT = 255;  // 100% on LiPo
static constexpr uint32_t PWM_FREQUENCY_HZ = 20000;  // 20 kHz (inaudible to humans, DRV8833-friendly)
static constexpr uint8_t PWM_RESOLUTION_BITS = 8;    // 0..255 duty range

// Runtime power profile (Bench = current, Flight = future upgrade).
enum class PowerProfile : uint8_t {
    Bench = 0,   // 5V USB + 3V AAA, duty ≤ 102
    Flight = 1   // 1S 3.7V LiPo, duty ≤ 255
};

// Control mode: MANUAL (serial drive) or AUTONOMOUS (perception → cognition).
enum class ControlMode : uint8_t {
    MANUAL = 0,
    AUTONOMOUS = 1
};

// ----------------------------------------------------------------------------
// GPIO PIN MAP (ESP32-CAM AI-Thinker)
// ----------------------------------------------------------------------------
// STRICTLY RESERVED (SD_MMC + camera): GPIO 4, 12, 13, 14, 15.
// NEVER assign these to motors, servos, or anything else.
//
// Free GPIOs on ESP32-CAM: 2, 16, 17, 32, 33 (only 5 available).
//   - GPIO 2 also drives the onboard flash LED (fine for motor logic).
//   - GPIO 16, 17, 32, 33 are clean digital I/O.
//
// Motor driver: 2× DRV8833 (differential drive), 1 spare.
//   Channel A = Left motor pair, Channel B = Right motor pair.
static constexpr uint8_t PIN_MOTOR_LEFT_IN1  = 16;  // DRV8833 AIN1
static constexpr uint8_t PIN_MOTOR_LEFT_IN2  = 17;  // DRV8833 AIN2
static constexpr uint8_t PIN_MOTOR_RIGHT_IN1 = 32;  // DRV8833 BIN1
static constexpr uint8_t PIN_MOTOR_RIGHT_IN2 = 33;  // DRV8833 BIN2

// Ultrasonic HC-SR04 (trigger shares onboard LED on GPIO 2; echo unwired).
static constexpr uint8_t PIN_ULTRASONIC_TRIGGER = 2;
static constexpr uint8_t PIN_ULTRASONIC_ECHO    = 255;  // 255 = not wired

// Wheel encoder (DVD IR sensor) — planned, stubbed for now.
static constexpr uint8_t PIN_ENCODER_LEFT  = 255;  // not wired yet
static constexpr uint8_t PIN_ENCODER_RIGHT = 255;  // not wired yet

// Limit switch / e-stop — planned, stubbed for now.
static constexpr uint8_t PIN_LIMIT_SWITCH = 255;   // not wired yet
static constexpr uint8_t PIN_ESTOP_BUTTON = 255;   // not wired yet

// Arm / gripper (stepper + servo) — stubs for Phase 1.
static constexpr uint8_t PIN_ARM_STEP    = 255;  // not wired yet
static constexpr uint8_t PIN_ARM_DIR     = 255;  // not wired yet
static constexpr uint8_t PIN_GRIPPER_SERVO = 255;  // not wired yet

// ----------------------------------------------------------------------------
// CAMERA (OV2640 on ESP32-CAM)
// ----------------------------------------------------------------------------
// QVGA grayscale for perception: 320×240, 1 byte per pixel.
// Small enough to scan in real time on the ESP32-CAM's dual-core 240 MHz.
static constexpr uint16_t CAM_WIDTH  = 320;
static constexpr uint16_t CAM_HEIGHT = 240;
static constexpr uint8_t  CAM_QUALITY = 12;
static constexpr uint8_t  CAM_FB_COUNT = 1;

// ----------------------------------------------------------------------------
// PERCEPTION
// ----------------------------------------------------------------------------
// Brightness threshold for "target pixel" detection (0..255).
// A white ground marker or reflective object typically reads > 200.
static constexpr uint8_t VISION_BRIGHTNESS_THRESHOLD = 200;

// TinyML classifier path on SD card.
static constexpr char MODEL_PATH[] = "/sdcard/model.tflite";

// Known-size marker for distance estimation (cm).
// Place a 10×10 cm card at a known distance, run calibration, set PIXELS_PER_CM.
static constexpr float MARKER_SIZE_CM = 10.0f;
static constexpr float PIXELS_PER_CM = 2.5f;  // placeholder; set via calibration

// ----------------------------------------------------------------------------
// COGNITION / PLANNING
// ----------------------------------------------------------------------------
// ML confidence threshold. Below this, fall back to deterministic rules.
static constexpr float ML_CONFIDENCE_THRESHOLD = 0.70f;

// Autonomous loop tick interval (ms).
static constexpr uint32_t AUTONOMOUS_TICK_MS = 200;

// Safety watchdog: if the main loop takes longer than this, kill PWM.
static constexpr uint32_t WATCHDOG_MAX_LOOP_MS = 100;

// ----------------------------------------------------------------------------
// SD LOGGING / MEMORY
// ----------------------------------------------------------------------------
static constexpr char SD_MOUNT_POINT[] = "/sdcard";
static constexpr char LOG_CSV_PATH[]   = "/sdcard/logs/robot_log.csv";
static constexpr char MEMORY_DB_PATH[] = "/sdcard/data/objects/memory_db.bin";
static constexpr char OBJECTS_DIR[]    = "/sdcard/data/objects";
static constexpr char LOGS_DIR[]       = "/sdcard/logs";

// ----------------------------------------------------------------------------
// ACTION MIXER
// ----------------------------------------------------------------------------
// Differential drive: left = throttle + steer, right = throttle - steer.
// Both clamped to [0, PWM_MAX_DUTY] after mixing.
static constexpr float DEFAULT_BASE_SPEED = 0.45f;   // 45% throttle
static constexpr float DEFAULT_TURN_GAIN  = 0.80f;   // steering aggressiveness

#endif  // CONFIG_H
