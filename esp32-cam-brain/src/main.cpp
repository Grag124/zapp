#include "config.h"
#include "camera_hal.h"
#include "motor_control.h"
#include "sensor_hal.h"
#include "perception.h"
#include "cognition.h"
#include "sd_logger.h"
#include "safety_guard.h"
#include "memory_db.h"
#include "arm_controller.h"

#ifdef PHASE0_SIMULATION
#  include <cstdio>
#  include <csignal>
#  include <thread>
#  include <chrono>
#  include <cstring>
#  include <unistd.h>
#else
#  include <Arduino.h>
#endif

// ============================================================================
// MAIN.CPP — Robot brain entry point
// ============================================================================
// Two builds:
//   1) ESP32-CAM hardware (pio run -e esp32cam): real camera, motors, SD.
//   2) Phase 0 simulation (pio run -e phase0-sim): runs on laptop, no HW.
//
// Phase 0 lets you develop and test the brain logic today, before the
// DRV8833s and chassis arrive in 2 weeks.

#ifdef PHASE0_SIMULATION
volatile bool g_running = true;

void handleSignal(int) {
    g_running = false;
}

// Non-blocking serial input in simulation: read one char if available.
static int sim_getchar() {
    struct timeval tv;
    fd_set fds;
    tv.tv_sec = 0;
    tv.tv_usec = 0;
    FD_ZERO(&fds);
    FD_SET(STDIN_FILENO, &fds);
    select(STDIN_FILENO + 1, &fds, nullptr, nullptr, &tv);
    if (FD_ISSET(STDIN_FILENO, &fds)) {
        int c = getchar();
        return c;
    }
    return -1;
}
#endif

// Print the help menu to serial.
static void printHelp() {
#ifdef PHASE0_SIMULATION
    std::printf("\n=== ESP32-CAM Robot Brain — Serial Commands ===\n");
#else
    Serial.println("\n=== ESP32-CAM Robot Brain — Serial Commands ===");
#endif
    const char* lines[] = {
        "W  = Drive forward",
        "A  = Turn left",
        "S  = Drive backward",
        "D  = Turn right",
        "M  = Toggle MANUAL <-> AUTONOMOUS mode",
        "V  = Toggle vision tracking on/off",
        "F  = Fire gripper (arm stub)",
        "B  = Emergency stop (kill all PWM)",
        "C  = Clear object memory database",
        "H  = Show this help menu",
        "",
        "Manual mode: W/A/S/D drive the robot directly.",
        "Autonomous mode: perception + cognition decide.",
        "All PWM capped at 40% bench limit (max 102/255).",
        "===============================================\n",
    };
    for (const char* line : lines) {
#ifdef PHASE0_SIMULATION
        std::printf("%s\n", line);
#else
        Serial.println(line);
#endif
    }
}

// Process one serial command character.
static void handleCommand(char c) {
    c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));

    switch (c) {
        case 'w':  // Forward
            motors.setMode(ControlMode::MANUAL);
            motors.setManualDrive(0.6f, 0.0f);
            motors.manualUpdate();
            sd_logger.log(0, "manual", 102, 102, 1.0f, "drive forward");
#ifdef PHASE0_SIMULATION
            std::printf("[MANUAL] Forward\n");
#else
            Serial.println("[MANUAL] Forward");
#endif
            break;

        case 's':  // Backward
            motors.setMode(ControlMode::MANUAL);
            motors.setManualDrive(-0.6f, 0.0f);
            motors.manualUpdate();
            sd_logger.log(0, "manual", 102, 102, 1.0f, "drive backward");
#ifdef PHASE0_SIMULATION
            std::printf("[MANUAL] Backward\n");
#else
            Serial.println("[MANUAL] Backward");
#endif
            break;

        case 'a':  // Turn left
            motors.setMode(ControlMode::MANUAL);
            motors.setManualDrive(0.0f, -0.8f);
            motors.manualUpdate();
            sd_logger.log(0, "manual", 102, 102, 1.0f, "turn left");
#ifdef PHASE0_SIMULATION
            std::printf("[MANUAL] Turn left\n");
#else
            Serial.println("[MANUAL] Turn left");
#endif
            break;

        case 'd':  // Turn right
            motors.setMode(ControlMode::MANUAL);
            motors.setManualDrive(0.0f, 0.8f);
            motors.manualUpdate();
            sd_logger.log(0, "manual", 102, 102, 1.0f, "turn right");
#ifdef PHASE0_SIMULATION
            std::printf("[MANUAL] Turn right\n");
#else
            Serial.println("[MANUAL] Turn right");
#endif
            break;

        case 'm':  // Toggle manual <-> autonomous
            if (motors.getMode() == ControlMode::MANUAL) {
                motors.setMode(ControlMode::AUTONOMOUS);
                motors.stop();
#ifdef PHASE0_SIMULATION
                std::printf("[MODE] Switched to AUTONOMOUS\n");
#else
                Serial.println("[MODE] Switched to AUTONOMOUS");
#endif
                sd_logger.log(0, "mode", 0, 0, 1.0f, "switched to autonomous");
            } else {
                motors.setMode(ControlMode::MANUAL);
                motors.stop();
#ifdef PHASE0_SIMULATION
                std::printf("[MODE] Switched to MANUAL\n");
#else
                Serial.println("[MODE] Switched to MANUAL");
#endif
                sd_logger.log(0, "mode", 0, 0, 1.0f, "switched to manual");
            }
            break;

        case 'v':  // Toggle vision tracking
            // Vision is handled via perception; toggle cognition intent.
            // In autonomous mode, vision drives steering via centroid.
#ifdef PHASE0_SIMULATION
            std::printf("[VISION] Toggled (vision integrated in perception)\n");
#else
            Serial.println("[VISION] Toggled (vision integrated in perception)");
#endif
            break;

        case 'f':  // Fire gripper
            arm.setGripper(true);
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            arm.setGripper(false);
#ifdef PHASE0_SIMULATION
            std::printf("[ARM] Gripper fired\n");
#else
            Serial.println("[ARM] Gripper fired");
#endif
            sd_logger.log(0, "action", 0, 0, 1.0f, "gripper fired");
            break;

        case 'b':  // Emergency stop
            safety.eStop();
            motors.stop();
            sd_logger.log(0, "estop", 0, 0, 1.0f, "emergency stop");
#ifdef PHASE0_SIMULATION
            std::printf("[SAFETY] E-STOP — all PWM killed\n");
#else
            Serial.println("[SAFETY] E-STOP — all PWM killed");
#endif
            break;

        case 'c':  // Clear memory database
            memory_db.clear();
#ifdef PHASE0_SIMULATION
            std::printf("[MEM] Object memory cleared\n");
#else
            Serial.println("[MEM] Object memory cleared");
#endif
            sd_logger.log(0, "memory", 0, 0, 1.0f, "cleared object database");
            break;

        case 'h':  // Help
            printHelp();
            break;

        case '\n':
        case '\r':
        case -1:
            break;  // ignore

        default:
#ifdef PHASE0_SIMULATION
            std::printf("[CMD] Unknown command: '%c' (press H for help)\n", c);
#else
            Serial.print("[CMD] Unknown command: '");
            Serial.print(c);
            Serial.println("' (press H for help)");
#endif
            break;
    }
}

void setup() {
#ifdef PHASE0_SIMULATION
    std::printf("\n=== ESP32-CAM Robot Brain — Phase 0 Simulation ===\n");
    std::printf("No hardware required. Press Ctrl+C to stop.\n");
    printHelp();
#else
    Serial.begin(115200);
    while (!Serial) { delay(10); }
    std::printf("\n=== ESP32-CAM Robot Brain — Hardware ===\n");
    printHelp();
#endif

    // Initialize all subsystems.
    safety.begin();
    sd_logger.begin();
    memory_db.begin();
    camera.begin();
    motors.begin();
    sensors.begin();
    arm.begin();

    std::printf("[BRAIN] All subsystems initialized.\n");

    // Default intent: idle (wait for command).
    cognition.setIntent(Intent::Idle);
    motors.setMode(ControlMode::AUTONOMOUS);

#ifdef PHASE0_SIMULATION
    std::signal(SIGINT, handleSignal);
#endif
}

void loop() {
#ifdef PHASE0_SIMULATION
    if (!g_running) {
        std::printf("\n[BRAIN] Shutdown requested.\n");
        motors.stop();
        sd_logger.flush();
        memory_db.flush();
        std::exit(0);
    }
#endif

    safety.loopStart();

    // --- Serial command handling (manual override) ---
#ifdef PHASE0_SIMULATION
    int c = sim_getchar();
    if (c != -1) {
        handleCommand(static_cast<char>(c));
    }
#else
    while (Serial.available()) {
        char c = Serial.read();
        handleCommand(c);
    }
#endif

    // Only run autonomous perception/cognition if in autonomous mode
    // and not e-stopped.
    if (motors.getMode() == ControlMode::AUTONOMOUS &&
        !safety.isEstopActive()) {
        // 1) Perception: capture frame + analyze.
        camera.capture();
        ObjectDetection det = perception.analyze();

        // 2) Sensing: ultrasonic distance (may be -1 if echo not wired).
        float distance = sensors.readDistanceCm();

        // 3) Cognition: decide action.
        Decision dec = cognition.decide(det, distance);

        // 4) Action: mix throttle/steer into motor PWM (clamped to 40% bench cap).
        motors.mix(dec.left_throttle, dec.right_throttle);

#ifdef PHASE0_SIMULATION
        std::printf("[CYCLE] intent=%s action=%s L=%.2f R=%.2f conf=%.2f reason=%s\n",
                    (dec.action_label == "fetch" ? "fetch" :
                     dec.action_label == "return" ? "return" :
                     dec.action_label == "stop" ? "stop" : "idle"),
                    dec.action_label.c_str(),
                    dec.left_throttle, dec.right_throttle,
                    dec.confidence, dec.reason.c_str());
#endif
    }

    // 5) Safety: check watchdog and e-stop (always active).
    if (safety.checkWatchdog() || safety.isEstopActive()) {
        motors.stop();
        if (safety.isEstopActive()) {
#ifdef PHASE0_SIMULATION
            std::printf("[SAFETY] E-stop active — motors killed\n");
#else
            Serial.println("[SAFETY] E-stop active — motors killed");
#endif
        }
    }

    // 6) Arm/gripper (stubbed).
    (void)arm;

#ifdef PHASE0_SIMULATION
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
#else
    delay(50);
#endif
}

#ifdef PHASE0_SIMULATION
int main() {
    setup();
    while (true) {
        loop();
    }
    return 0;
}
#endif
