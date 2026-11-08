#include "action_mixer.h"
#include <algorithm>

// ============================================================================
// ACTION_MIXER.CPP — Manual control mixing implementation
// ============================================================================
// Differential drive mixing: left = throttle + steer, right = throttle - steer.
// Both outputs are clamped to the bench 40% cap (≤ 102/255) by
// MotorChannel::setThrottle() before reaching the DRV8833.
//
// This file holds the manual-control mixing implementation, separate from
// the ActionMixer class definition in motor_control.h, to keep autonomous
// and manual code paths clearly separated.

// manualUpdate() applies the last manual throttle/steer values through mix().
// It is declared in motor_control.h and implemented here.
void ActionMixer::manualUpdate() {
    mix(manual_throttle_, manual_steer_);
}
