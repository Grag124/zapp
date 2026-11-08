#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include "power_metrics.h"

#include <Arduino.h>

#include <cstdint>
#include <algorithm>

enum class MotorId : uint8_t {
    Left = 0,
    Right = 1,
    Count = 2
};

enum class MotorDirection : uint8_t {
    Coast = 0,
    Forward = 1,
    Reverse = 2,
    Brake = 3
};

class MotorChannel {
public:
    MotorChannel(uint8_t ledcChannel, uint8_t in1Pin, uint8_t in2Pin)
        : ledcChannel_(ledcChannel),
          in1Pin_(in1Pin),
          in2Pin_(in2Pin),
          duty_(0),
          direction_(MotorDirection::Coast),
          calibrated_(false),
          maxDuty_(PowerMetrics::LedcMaxDuty) {}

    virtual ~MotorChannel() = default;

    virtual bool begin() {
        pinMode(in1Pin_, OUTPUT);
        pinMode(in2Pin_, OUTPUT);
        ledcSetup(ledcChannel_, PowerMetrics::LedcFrequencyHz,
                  PowerMetrics::LedcResolutionBits);
        ledcAttachPin(in1Pin_, ledcChannel_);
        stop();
        calibrated_ = true;
        return true;
    }

    virtual void setDuty(uint32_t duty, MotorDirection direction) {
        duty_ = std::min<uint32_t>(duty, maxDuty_);
        direction_ = direction;
        apply();
    }

    virtual void setThrottle(float throttle, MotorDirection direction) {
        throttle = std::clamp<float>(throttle, 0.0f, 1.0f);
        uint32_t duty = static_cast<uint32_t>(
            throttle * static_cast<float>(PowerMetrics::LedcMaxDuty) + 0.5f);
        setDuty(duty, direction);
    }

    virtual void setVoltage(float targetVoltageV, MotorDirection direction) {
        setDuty(PowerMetrics::voltageToDuty(targetVoltageV), direction);
    }

    virtual void stop() {
        setDuty(0, MotorDirection::Coast);
    }

    virtual void brake() {
        setDuty(PowerMetrics::LedcMaxDuty, MotorDirection::Brake);
    }

    void setMaxDuty(uint32_t maxDuty) {
        maxDuty_ = std::min<uint32_t>(maxDuty, PowerMetrics::LedcMaxDuty);
        duty_ = std::min<uint32_t>(duty_, maxDuty_);
    }

    uint32_t duty() const { return duty_; }
    MotorDirection direction() const { return direction_; }
    bool calibrated() const { return calibrated_; }
    uint32_t maxDuty() const { return maxDuty_; }

protected:
    virtual void apply() {
        uint32_t effective = duty_;
        switch (direction_) {
            case MotorDirection::Forward:
                digitalWrite(in2Pin_, LOW);
                ledcWrite(ledcChannel_, static_cast<int>(effective));
                break;
            case MotorDirection::Reverse:
                digitalWrite(in2Pin_, HIGH);
                ledcWrite(ledcChannel_, static_cast<int>(effective));
                break;
            case MotorDirection::Brake:
                digitalWrite(in2Pin_, HIGH);
                ledcWrite(ledcChannel_, static_cast<int>(PowerMetrics::LedcMaxDuty));
                break;
            case MotorDirection::Coast:
            default:
                digitalWrite(in2Pin_, LOW);
                ledcWrite(ledcChannel_, 0);
                break;
        }
    }

    uint8_t ledcChannel_;
    uint8_t in1Pin_;
    uint8_t in2Pin_;
    uint32_t duty_;
    MotorDirection direction_;
    bool calibrated_;
    uint32_t maxDuty_;
};

class ThrottleRamp {
public:
    ThrottleRamp(float maxStepPerMs = 0.05f)
        : maxStepPerMs_(maxStepPerMs), lastMs_(0), current_(0.0f) {}

    void reset() {
        lastMs_ = 0;
        current_ = 0.0f;
    }

    float step(float target, uint32_t nowMs) {
        target = std::clamp<float>(target, 0.0f, 1.0f);
        if (lastMs_ == 0) {
            lastMs_ = nowMs;
            current_ = target;
            return current_;
        }
        float dt = static_cast<float>(nowMs - lastMs_);
        lastMs_ = nowMs;
        float maxStep = maxStepPerMs_ * dt;
        if (target > current_) {
            current_ = std::min<float>(target, current_ + maxStep);
        } else if (target < current_) {
            current_ = std::max<float>(target, current_ - maxStep);
        }
        return current_;
    }

private:
    float maxStepPerMs_;
    uint32_t lastMs_;
    float current_;
};

class MotorController {
public:
    MotorController(MotorChannel* left, MotorChannel* right)
        : left_(left), right_(right), leftRamp_(nullptr), rightRamp_(nullptr) {}

    void attachRamps(ThrottleRamp* leftRamp, ThrottleRamp* rightRamp) {
        leftRamp_ = leftRamp;
        rightRamp_ = rightRamp;
    }

    bool begin() {
        bool ok = true;
        if (left_) ok &= left_->begin();
        if (right_) ok &= right_->begin();
        return ok;
    }

    void setThrottles(float leftThrottle, float rightThrottle, uint32_t nowMs = 0) {
        float l = leftThrottle;
        float r = rightThrottle;
        if (leftRamp_ && nowMs != 0) l = leftRamp_->step(l, nowMs);
        if (rightRamp_ && nowMs != 0) r = rightRamp_->step(r, nowMs);

        MotorDirection lDir = l >= 0.0f ? MotorDirection::Forward : MotorDirection::Reverse;
        MotorDirection rDir = r >= 0.0f ? MotorDirection::Forward : MotorDirection::Reverse;

        if (left_) left_->setThrottle(std::abs(l), lDir);
        if (right_) right_->setThrottle(std::abs(r), rDir);
    }

    void setVoltages(float leftVoltageV, float rightVoltageV) {
        MotorDirection lDir = leftVoltageV >= 0.0f
                                  ? MotorDirection::Forward
                                  : MotorDirection::Reverse;
        MotorDirection rDir = rightVoltageV >= 0.0f
                                  ? MotorDirection::Forward
                                  : MotorDirection::Reverse;
        if (left_) left_->setVoltage(std::abs(leftVoltageV), lDir);
        if (right_) right_->setVoltage(std::abs(rightVoltageV), rDir);
    }

    void stop() {
        if (left_) left_->stop();
        if (right_) right_->stop();
    }

    void brake() {
        if (left_) left_->brake();
        if (right_) right_->brake();
    }

    MotorChannel* left() { return left_; }
    MotorChannel* right() { return right_; }

private:
    MotorChannel* left_;
    MotorChannel* right_;
    ThrottleRamp* leftRamp_;
    ThrottleRamp* rightRamp_;
};

#endif  // MOTOR_CONTROL_H
