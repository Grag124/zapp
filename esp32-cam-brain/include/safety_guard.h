#ifndef SAFETY_GUARD_H
#define SAFETY_GUARD_H

#include "config.h"

#include <cstdint>

// ============================================================================
// SAFETY_GUARD_H — Watchdog, e-stop, duty clamp
// ============================================================================
// The robot's "lizard brain" — reflex-level safety that overrides
// everything else. If the main loop hangs (>100 ms) or e-stop is pressed,
// PWM is killed immediately.
//
// Duty is always hard-clamped: min(duty, PWM_MAX_DUTY) where PWM_MAX_DUTY
// is 102 in bench mode (40%).

class SafetyGuard {
public:
    SafetyGuard();

    // Initialize: read e-stop pin, reset watchdog state.
    bool begin();

    // Call at the start of every loop iteration. Records the timestamp.
    void loopStart();

    // Call at the end of every loop iteration. Returns true if loop time
    // exceeded the watchdog limit (in which case PWM should be killed).
    bool checkWatchdog();

    // Emergency stop: kill all PWM immediately.
    void eStop();

    // Clear e-stop and resume normal operation.
    void clearEStop();

    bool isEstopActive() const { return estop_active_; }
    bool isWatchdogTripped() const { return watchdog_tripped_; }

    // Hard duty clamp: returns min(duty, PWM_MAX_DUTY).
    static uint8_t clampDuty(uint8_t duty);

    void setPowerProfile(PowerProfile profile);

private:
    uint32_t loop_start_ms_ = 0;
    bool     estop_active_ = false;
    bool     watchdog_tripped_ = false;
    PowerProfile power_profile_ = PowerProfile::Bench;
};

// Global safety guard instance.
extern SafetyGuard safety;

#endif  // SAFETY_GUARD_H
