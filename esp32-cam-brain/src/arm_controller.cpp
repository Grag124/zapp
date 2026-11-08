#include "arm_controller.h"

#ifdef PHASE0_SIMULATION
#  include <cstdio>
#else
#  include <Arduino.h>
#endif

ArmController::ArmController() : initialized_(false) {}

bool ArmController::begin() {
#ifdef PHASE0_SIMULATION
    std::printf("[ARM] Simulation mode: arm/gripper stubbed\n");
    initialized_ = true;
    return true;
#else
    initialized_ = true;
    return true;
#endif
}

void ArmController::moveToAngle(float degrees) {
    if (!initialized_) return;
#ifdef PHASE0_SIMULATION
    std::printf("[ARM] moveToAngle(%.1f) — stub (no hardware)\n", degrees);
#else
    // Stepper + servo control would go here.
#endif
}

void ArmController::setGripper(bool open) {
    if (!initialized_) return;
#ifdef PHASE0_SIMULATION
    std::printf("[ARM] setGripper(%s) — stub (no hardware)\n",
                open ? "open" : "close");
#endif
}

void ArmController::home() {
    if (!initialized_) return;
#ifdef PHASE0_SIMULATION
    std::printf("[ARM] home() — stub (no hardware)\n");
#endif
}

ArmController arm;
