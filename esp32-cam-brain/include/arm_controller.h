#ifndef ARM_CONTROLLER_H
#define ARM_CONTROLLER_H

#include "config.h"

#include <cstdint>

// ============================================================================
// ARM_CONTROLLER_H — Stepper arm + gripper stubs (Phase 1)
// ============================================================================
// Placeholder for the arm/gripper subsystem. All methods are no-ops until
// physical arm hardware is wired. The brain can call these without crashing.
//
// Think of this as the robot's "hands" — not built yet, but the interface
// is reserved so we don't have to refactor later.

class ArmController {
public:
    ArmController();
    bool begin();

    // Move arm to angle (degrees). Stub: logs intent only.
    void moveToAngle(float degrees);

    // Open/close gripper. Stub: logs intent only.
    void setGripper(bool open);

    // Home the arm. Stub.
    void home();

private:
    bool initialized_ = false;
};

extern ArmController arm;

#endif  // ARM_CONTROLLER_H
