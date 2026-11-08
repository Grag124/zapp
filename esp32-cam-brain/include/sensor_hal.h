#ifndef SENSOR_HAL_H
#define SENSOR_HAL_H

#include "config.h"

#include <cstdint>
#include <cstddef>

#ifdef PHASE0_SIMULATION
#  include <cstdio>
#  include <ctime>
#else
#  include <Arduino.h>
#endif

// ============================================================================
// SENSOR_HAL_H — Wheel encoder, limit switch, simulated IMU, buttons
// ============================================================================
// Abstracts all non-vision sensors. Most are planned hardware (arriving in
// 2 weeks) so Phase 0 returns simulated values.
//
// Think of this as the robot's "inner ear" — balance, motion, and touch.

class SensorHAL {
public:
    SensorHAL();

    bool begin();

    // Ultrasonic distance in cm, or -1 if echo not wired.
    float readDistanceCm();

    // Simulated wheel encoder ticks (left, right).
    void readEncoderTicks(int32_t& left, int32_t& right);

    // Simulated IMU: returns tilt angle in degrees (0 = level).
    float readImuTiltDeg();

    // Limit switch / e-stop state (true = pressed).
    bool isEstopPressed();

private:
    int32_t enc_left_ = 0;
    int32_t enc_right_ = 0;
    float   imu_tilt_ = 0.0f;
};

extern SensorHAL sensors;

#endif  // SENSOR_HAL_H
