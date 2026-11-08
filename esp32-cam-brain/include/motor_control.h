#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include "config.h"

#include <cstdint>
#include <algorithm>

#ifdef PHASE0_SIMULATION
#  include <cstdio>
#else
#  include <Arduino.h>
#endif

// ============================================================================
// MOTOR_CONTROL_H — DRV8833 dual H-Bridge interface
// ============================================================================
// Drives two DC motor channels (left + right) via LEDC PWM.
// Every duty value passes through a hard clamp: min(duty, PWM_MAX_DUTY).
// In bench mode that's 102/255 (40%). Flight mode allows 255.
//
// Think of this as the robot's "muscles." It translates high-level
// throttle/steer commands into safe PWM signals for the DRV8833.

enum class MotorDir : uint8_t {
    Coast = 0,
    Forward = 1,
    Reverse = 2,
    Brake = 3
};

class MotorChannel {
public:
    MotorChannel(uint8_t ledc_channel, uint8_t in1_pin, uint8_t in2_pin);

    bool begin();
    void setDuty(uint8_t duty, MotorDir dir);
    void setThrottle(float throttle, MotorDir dir);  // throttle in [0,1]
    void stop();
    void brake();

    uint8_t duty() const { return duty_; }
    MotorDir direction() const { return direction_; }

    // Set the hard duty cap (bench=102, flight=255).
    void setMaxDuty(uint8_t maxDuty);

private:
    void apply();

    uint8_t ledc_channel_;
    uint8_t in1_pin_;
    uint8_t in2_pin_;
    uint8_t duty_;
    uint8_t max_duty_;
    MotorDir direction_;
};

// Differential-drive mixer: left = throttle + steer, right = throttle - steer.
// Both clamped to [0, maxDuty]. Negative throttle = reverse.
class ActionMixer {
public:
    ActionMixer(MotorChannel* left, MotorChannel* right);

    bool begin();

    // throttle in [-1,1], steer in [-1,1].
    // steer > 0 turns right (left motor faster), steer < 0 turns left.
    void mix(float throttle, float steer);

    // --- Manual control interface ---
    void setMode(ControlMode mode);
    ControlMode getMode() const { return mode_; }
    void setManualDrive(float throttle, float steer);
    void manualUpdate();  // applies manual throttle/steer via mix()

    void stop();
    void brake();

    MotorChannel* left() { return left_; }
    MotorChannel* right() { return right_; }

private:
    MotorChannel* left_;
    MotorChannel* right_;
    ControlMode mode_ = ControlMode::AUTONOMOUS;
    float manual_throttle_ = 0.0f;
    float manual_steer_ = 0.0f;
};

extern ActionMixer motors;

#endif  // MOTOR_CONTROL_H
