#include "cognition.h"
#include "sd_logger.h"
#include "memory_db.h"
#include "safety_guard.h"

#include <cmath>
#include <cstdio>
#include <algorithm>

Cognition::Cognition() {}

void Cognition::setIntent(Intent intent) {
    current_intent_ = intent;
}

bool Cognition::hasSeenObject(const std::string& label) const {
    return memory_db.hasSeen(label);
}

Decision Cognition::decide(const ObjectDetection& detection, float distance_cm) {
    Decision dec;
    dec.action_label = "idle";
    dec.confidence = 0.0f;
    dec.reason = "no decision";

    CognitiveState state;
    state.intent = current_intent_;
    state.obstacle_ahead = (detection.label == "obstacle" ||
                            detection.label == "edge_ahead");
    state.edge_ahead = (detection.label == "edge_ahead");
    state.target_distance_cm = detection.distance_cm;
    state.target_centroid_x = detection.centroid_x;
    state.confidence = detection.confidence;

    // --- Safety override: obstacle or edge ahead → AVOID ---
    if (state.obstacle_ahead || state.edge_ahead) {
        current_intent_ = Intent::Avoid;
        dec.left_throttle = -0.4f;
        dec.right_throttle = -0.4f;  // back up
        dec.action_label = "back_up";
        dec.confidence = 1.0f;
        dec.reason = "obstacle/edge detected: backing up for safety";
        state.intent = Intent::Avoid;
        state.reason = dec.reason;
        sd_logger.log(
            0, "avoid", 0, 0, dec.confidence, dec.reason);
        last_decision_ = dec;
        return dec;
    }

    // --- ML confidence fallback ---
    if (detection.confidence < ML_CONFIDENCE_THRESHOLD &&
        detection.label != "clear") {
        // Low confidence → deterministic safe rule.
        current_intent_ = Intent::Stop;
        dec.left_throttle = 0.0f;
        dec.right_throttle = 0.0f;
        dec.action_label = "stop";
        dec.confidence = detection.confidence;
        dec.reason = "ML confidence below threshold: stopping";
        state.reason = dec.reason;
        sd_logger.log(0, "stop", 0, 0, dec.confidence, dec.reason);
        last_decision_ = dec;
        return dec;
    }

    // --- Intent-based planning ---
    switch (current_intent_) {
        case Intent::Idle:
            dec.left_throttle = 0.0f;
            dec.right_throttle = 0.0f;
            dec.action_label = "stop";
            dec.confidence = 1.0f;
            dec.reason = "idle: waiting for command";
            break;

        case Intent::Fetch: {
            // Drive toward the bright target using centroid steering.
            float cx = static_cast<float>(detection.centroid_x);
            float center = CAM_WIDTH / 2.0f;
            float error = (cx - center) / center;  // [-1, 1]
            float steer = error * 0.8f;
            float throttle = 0.4f;  // moderate approach speed
            dec.left_throttle = std::clamp<float>(throttle + steer, -1.0f, 1.0f);
            dec.right_throttle = std::clamp<float>(throttle - steer, -1.0f, 1.0f);
            dec.action_label = "fetch";
            dec.confidence = detection.confidence;
            dec.reason = "fetching target: steering toward centroid";
            if (memory_db.hasSeen(detection.label)) {
                dec.reason += "; seen this object before";
            }
            break;
        }

        case Intent::Return:
            dec.left_throttle = -0.3f;
            dec.right_throttle = -0.3f;
            dec.action_label = "return";
            dec.confidence = 0.8f;
            dec.reason = "returning to home position";
            break;

        case Intent::Stop:
            dec.left_throttle = 0.0f;
            dec.right_throttle = 0.0f;
            dec.action_label = "stop";
            dec.confidence = 1.0f;
            dec.reason = "stop commanded";
            break;

        case Intent::Avoid:
            dec.left_throttle = -0.4f;
            dec.right_throttle = -0.4f;
            dec.action_label = "avoid";
            dec.confidence = 1.0f;
            dec.reason = "avoiding obstacle";
            break;
    }

    state.reason = dec.reason;
    sd_logger.log(0,
                  current_intent_ == Intent::Fetch ? "fetch" :
                  current_intent_ == Intent::Return ? "return" :
                  current_intent_ == Intent::Stop ? "stop" :
                  current_intent_ == Intent::Avoid ? "avoid" : "idle",
                  static_cast<uint8_t>(std::abs(dec.left_throttle) * 102),
                  static_cast<uint8_t>(std::abs(dec.right_throttle) * 102),
                  dec.confidence, dec.reason);

    last_decision_ = dec;
    return dec;
}

Cognition cognition;
