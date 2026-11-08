#ifndef COGNITION_H
#define COGNITION_H

#include "config.h"
#include "perception.h"

#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>

#ifdef PHASE0_SIMULATION
#else
#  include <SD_MMC.h>
#endif

// ============================================================================
// COGNITION_H — Deterministic planner + intent classifier + memory
// ============================================================================
// The "prefrontal cortex." Maps perception state → action with explainable
// rules. Falls back to hard-coded safety rules when ML confidence is low.
//
// Intents: FETCH (go to object), RETURN (come home), STOP, AVOID (obstacle).
//
// Every decision is logged to SD with timestamp, state, action, confidence,
// and a human-readable reason string.

enum class Intent : uint8_t {
    Idle = 0,
    Fetch = 1,
    Return = 2,
    Stop = 3,
    Avoid = 4
};

struct CognitiveState {
    Intent     intent = Intent::Idle;
    float      confidence = 0.0f;
    float      target_distance_cm = -1.0f;
    int16_t    target_centroid_x = -1;
    bool       obstacle_ahead = false;
    bool       edge_ahead = false;
    std::string reason;
};

struct Decision {
    float      left_throttle = 0.0f;   // [-1, 1]
    float      right_throttle = 0.0f;  // [-1, 1]
    float      confidence = 0.0f;
    std::string reason;
    std::string action_label;  // e.g. "forward", "turn_left", "stop"
};

class Cognition {
public:
    Cognition();

    // Run one cognitive tick: perceive → decide → return motor commands.
    Decision decide(const ObjectDetection& detection, float distance_cm);

    // Set intent manually (e.g. from serial command or memory recall).
    void setIntent(Intent intent);

    // Memory recall: have we seen this object label before?
    bool hasSeenObject(const std::string& label) const;

    // Get last decision for logging.
    const Decision& lastDecision() const { return last_decision_; }

private:
    Intent     current_intent_ = Intent::Idle;
    Decision   last_decision_;
};

// Global cognition instance.
extern Cognition cognition;

#endif  // COGNITION_H
