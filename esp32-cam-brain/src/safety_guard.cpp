#include "safety_guard.h"

#ifdef PHASE0_SIMULATION
#  include <cstdio>
#  include <ctime>
#  include <algorithm>
#else
#  include <Arduino.h>
#endif

SafetyGuard::SafetyGuard() {
    loop_start_ms_ = 0;
    estop_active_ = false;
    watchdog_tripped_ = false;
    power_profile_ = PowerProfile::Bench;
}

bool SafetyGuard::begin() {
#ifdef PHASE0_SIMULATION
    std::printf("[SAFETY] Simulation mode: watchdog + e-stop ready\n");
#else
    if (PIN_ESTOP_BUTTON != 255) {
        pinMode(PIN_ESTOP_BUTTON, INPUT_PULLUP);
    }
#endif
    estop_active_ = false;
    watchdog_tripped_ = false;
    return true;
}

void SafetyGuard::loopStart() {
#ifdef PHASE0_SIMULATION
    loop_start_ms_ = static_cast<uint32_t>(std::time(nullptr)) * 1000;
#else
    loop_start_ms_ = millis();
#endif
    watchdog_tripped_ = false;
}

bool SafetyGuard::checkWatchdog() {
#ifdef PHASE0_SIMULATION
    uint32_t now = static_cast<uint32_t>(std::time(nullptr)) * 1000;
#else
    uint32_t now = millis();
#endif
    uint32_t elapsed = now - loop_start_ms_;
    if (elapsed > WATCHDOG_MAX_LOOP_MS) {
        watchdog_tripped_ = true;
        std::printf("[SAFETY] Watchdog tripped: loop took %u ms (> %u ms)\n",
                    elapsed, WATCHDOG_MAX_LOOP_MS);
        return true;
    }
    return false;
}

void SafetyGuard::eStop() {
    estop_active_ = true;
    std::printf("[SAFETY] E-STOP ACTIVE — PWM killed\n");
}

void SafetyGuard::clearEStop() {
    estop_active_ = false;
    std::printf("[SAFETY] E-stop cleared\n");
}

uint8_t SafetyGuard::clampDuty(uint8_t duty) {
    return std::min<uint8_t>(duty, PWM_MAX_DUTY_BENCH);
}

void SafetyGuard::setPowerProfile(PowerProfile profile) {
    power_profile_ = profile;
}

SafetyGuard safety;
