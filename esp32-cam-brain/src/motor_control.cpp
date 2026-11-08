#include "motor_control.h"

#ifdef PHASE0_SIMULATION
#  include <cmath>
#  include <cstdio>
#else
#  include <Arduino.h>
#endif

#include <algorithm>

MotorChannel::MotorChannel(uint8_t ledc_channel, uint8_t in1_pin, uint8_t in2_pin)
    : ledc_channel_(ledc_channel),
      in1_pin_(in1_pin),
      in2_pin_(in2_pin),
      duty_(0),
      max_duty_(PWM_MAX_DUTY_BENCH),
      direction_(MotorDir::Coast) {}

bool MotorChannel::begin() {
#ifdef PHASE0_SIMULATION
    std::printf("[MOTOR] Ch%d: IN1=%u IN2=%u (simulation)\n",
                ledc_channel_, in1_pin_, in2_pin_);
    return true;
#else
    pinMode(in1_pin_, OUTPUT);
    pinMode(in2_pin_, OUTPUT);
    ledcSetup(ledc_channel_, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
    ledcAttachPin(in1_pin_, ledc_channel_);
    stop();
    return true;
#endif
}

void MotorChannel::setDuty(uint8_t duty, MotorDir dir) {
    duty_ = std::min<uint8_t>(duty, max_duty_);
    direction_ = dir;
    apply();
}

void MotorChannel::setThrottle(float throttle, MotorDir dir) {
    throttle = std::clamp<float>(throttle, 0.0f, 1.0f);
    uint8_t duty = static_cast<uint8_t>(
        throttle * static_cast<float>(max_duty_) + 0.5f);
    setDuty(duty, dir);
}

void MotorChannel::stop() {
    setDuty(0, MotorDir::Coast);
}

void MotorChannel::brake() {
    setDuty(max_duty_, MotorDir::Brake);
}

void MotorChannel::setMaxDuty(uint8_t maxDuty) {
    max_duty_ = maxDuty;
    duty_ = std::min<uint8_t>(duty_, max_duty_);
    apply();
}

void MotorChannel::apply() {
#ifdef PHASE0_SIMULATION
    const char* dir_str = "";
    switch (direction_) {
        case MotorDir::Forward:  dir_str = "FWD"; break;
        case MotorDir::Reverse:  dir_str = "REV"; break;
        case MotorDir::Brake:    dir_str = "BRK"; break;
        case MotorDir::Coast:    dir_str = "CST"; break;
    }
    std::printf("[MOTOR] Ch%d: duty=%u/%u dir=%s\n",
                ledc_channel_, duty_, max_duty_, dir_str);
#else
    uint8_t effective = duty_;
    switch (direction_) {
        case MotorDir::Forward:
            digitalWrite(in2_pin_, LOW);
            ledcWrite(ledc_channel_, effective);
            break;
        case MotorDir::Reverse:
            digitalWrite(in2_pin_, HIGH);
            ledcWrite(ledc_channel_, effective);
            break;
        case MotorDir::Brake:
            digitalWrite(in2_pin_, HIGH);
            ledcWrite(ledc_channel_, max_duty_);
            break;
        case MotorDir::Coast:
        default:
            digitalWrite(in2_pin_, LOW);
            ledcWrite(ledc_channel_, 0);
            break;
    }
#endif
}

ActionMixer::ActionMixer(MotorChannel* left, MotorChannel* right)
    : left_(left), right_(right) {}

bool ActionMixer::begin() {
    bool ok = true;
    if (left_) ok &= left_->begin();
    if (right_) ok &= right_->begin();
    return ok;
}

void ActionMixer::mix(float throttle, float steer) {
    throttle = std::clamp<float>(throttle, -1.0f, 1.0f);
    steer    = std::clamp<float>(steer,    -1.0f, 1.0f);

    float left_t  = std::clamp<float>(throttle + steer, -1.0f, 1.0f);
    float right_t = std::clamp<float>(throttle - steer, -1.0f, 1.0f);

    if (left_) {
        MotorDir dir = left_t >= 0 ? MotorDir::Forward : MotorDir::Reverse;
        left_->setThrottle(std::abs(left_t), dir);
    }
    if (right_) {
        MotorDir dir = right_t >= 0 ? MotorDir::Forward : MotorDir::Reverse;
        right_->setThrottle(std::abs(right_t), dir);
    }
}

void ActionMixer::setMode(ControlMode mode) {
    mode_ = mode;
    std::printf("[MIXER] Mode: %s\n",
                mode == ControlMode::MANUAL ? "MANUAL" : "AUTONOMOUS");
}

void ActionMixer::setManualDrive(float throttle, float steer) {
    manual_throttle_ = std::clamp<float>(throttle, -1.0f, 1.0f);
    manual_steer_    = std::clamp<float>(steer,    -1.0f, 1.0f);
}

void ActionMixer::stop() {
    if (left_) left_->stop();
    if (right_) right_->stop();
}

void ActionMixer::brake() {
    if (left_) left_->brake();
    if (right_) right_->brake();
}

ActionMixer motors(
    new MotorChannel(0, PIN_MOTOR_LEFT_IN1,  PIN_MOTOR_LEFT_IN2),
    new MotorChannel(1, PIN_MOTOR_RIGHT_IN1, PIN_MOTOR_RIGHT_IN2)
);
