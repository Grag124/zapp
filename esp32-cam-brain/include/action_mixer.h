#ifndef ACTION_MIXER_H
#define ACTION_MIXER_H

#include "motor_control.h"

// ============================================================================
// ACTION_MIXER_H — Differential drive motor mixer
// ============================================================================
// Converts (throttle, steer) into left/right motor commands.
//   throttle: [-1, 1] (negative = reverse)
//   steer:    [-1, 1] (positive = turn right, negative = turn left)
//   left  = clamp(throttle + steer, [-1,1])
//   right = clamp(throttle - steer, [-1,1])
//
// All output PWM is clamped to the bench 40% cap (≤ 102/255).

// Note: ActionMixer class is defined in motor_control.h. This header exists
// for architectural symmetry with the file structure spec. Include
// motor_control.h to use ActionMixer and MotorChannel.

#endif  // ACTION_MIXER_H
