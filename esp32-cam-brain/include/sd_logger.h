#ifndef SD_LOGGER_H
#define SD_LOGGER_H

#include "config.h"

#include <cstdint>
#include <cstdio>
#include <string>

#ifdef PHASE0_SIMULATION
#  include <fstream>
#else
#  include <SD_MMC.h>
#endif

// ============================================================================
// SD_LOGGER_H — Timestamped CSV logging to SD card
// ============================================================================
// Every robot decision is appended to /sdcard/logs/robot_log.csv:
//   timestamp_ms, intent, left_pwm, right_pwm, confidence, reason
//
// Think of this as the robot's "diary." If anything goes wrong, we can
// replay exactly what it saw, what it decided, and why.

class SDLogger {
public:
    SDLogger();

    // Initialize SD_MMC and create the log file with header.
    bool begin();

    // Log one decision row.
    void log(uint32_t timestamp_ms,
             const std::string& intent,
             uint8_t left_pwm,
             uint8_t right_pwm,
             float confidence,
             const std::string& reason);

    void flush();

private:
#ifdef PHASE0_SIMULATION
    std::ofstream log_file_;
#else
    bool sd_ready_ = false;
#endif
};

// Global logger instance.
extern SDLogger sd_logger;

#endif  // SD_LOGGER_H
