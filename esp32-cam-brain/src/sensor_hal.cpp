#include "sensor_hal.h"

#ifdef PHASE0_SIMULATION
#  include <cmath>
#  include <ctime>
#else
#  include <Arduino.h>
#endif

SensorHAL::SensorHAL() {}

bool SensorHAL::begin() {
#ifdef PHASE0_SIMULATION
    std::printf("[SENSOR] Simulation mode: ultrasonic, encoder, IMU stubbed\n");
    return true;
#else
    if (PIN_ULTRASONIC_TRIGGER != 255) {
        pinMode(PIN_ULTRASONIC_TRIGGER, OUTPUT);
    }
    if (PIN_ULTRASONIC_ECHO != 255) {
        pinMode(PIN_ULTRASONIC_ECHO, INPUT);
    }
    return true;
#endif
}

float SensorHAL::readDistanceCm() {
#ifdef PHASE0_SIMULATION
    // Simulate: no obstacle most of the time, occasional reading.
    static unsigned long last_toggle = 0;
    unsigned long now = std::time(nullptr) * 1000;
    if (now - last_toggle > 5000) {
        last_toggle = now;
    }
    return -1.0f;  // echo not wired in bench setup
#else
    if (PIN_ULTRASONIC_ECHO == 255 || PIN_ULTRASONIC_TRIGGER == 255) {
        return -1.0f;
    }
    digitalWrite(PIN_ULTRASONIC_TRIGGER, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_ULTRASONIC_TRIGGER, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_ULTRASONIC_TRIGGER, LOW);
    unsigned long duration = pulseIn(PIN_ULTRASONIC_ECHO, HIGH, 30000);
    if (duration == 0) return -1.0f;
    return duration * 0.0343f / 2.0f;
#endif
}

void SensorHAL::readEncoderTicks(int32_t& left, int32_t& right) {
#ifdef PHASE0_SIMULATION
    left = enc_left_;
    right = enc_right_;
    // Simulate slow drift
    enc_left_ += 1;
    enc_right_ += 1;
#else
    left = enc_left_;
    right = enc_right_;
#endif
}

float SensorHAL::readImuTiltDeg() {
#ifdef PHASE0_SIMULATION
    return imu_tilt_;  // 0 = level
#else
    return 0.0f;  // IMU not wired yet
#endif
}

bool SensorHAL::isEstopPressed() {
#ifdef PHASE0_SIMULATION
    return false;
#else
    if (PIN_ESTOP_BUTTON == 255) return false;
    return digitalRead(PIN_ESTOP_BUTTON) == HIGH;
#endif
}

SensorHAL sensors;
