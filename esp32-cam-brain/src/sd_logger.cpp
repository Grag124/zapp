#include "sd_logger.h"

#ifdef PHASE0_SIMULATION
#  include <ctime>
#  include <iomanip>
#  include <sstream>
#else
#  include <Arduino.h>
#endif

SDLogger::SDLogger() {
#ifdef PHASE0_SIMULATION
    log_file_.open("robot_log.csv", std::ios::out | std::ios::app);
    if (log_file_.is_open()) {
        log_file_ << "timestamp_ms,intent,left_pwm,right_pwm,confidence,reason\n";
    }
#endif
}

bool SDLogger::begin() {
#ifdef PHASE0_SIMULATION
    return log_file_.is_open();
#else
    if (!SD_MMC.begin(SD_MOUNT_POINT, true)) {
        std::printf("[SD] Mount failed\n");
        return false;
    }
    if (!SD_MMC.mkdir(LOGS_DIR)) {
        // Directory may already exist; ignore error.
    }
    File f = SD_MMC.open(LOG_CSV_PATH, FILE_APPEND);
    if (!f) {
        f = SD_MMC.open(LOG_CSV_PATH, FILE_WRITE);
    }
    if (f) {
        f.println("timestamp_ms,intent,left_pwm,right_pwm,confidence,reason");
        f.close();
    }
    sd_ready_ = true;
    std::printf("[SD] Logger initialized\n");
    return true;
#endif
}

void SDLogger::log(uint32_t timestamp_ms,
                   const std::string& intent,
                   uint8_t left_pwm,
                   uint8_t right_pwm,
                   float confidence,
                   const std::string& reason) {
#ifdef PHASE0_SIMULATION
    if (!log_file_.is_open()) return;
    log_file_ << timestamp_ms << ","
              << intent << ","
              << static_cast<int>(left_pwm) << ","
              << static_cast<int>(right_pwm) << ","
              << confidence << ","
              << reason << "\n";
    log_file_.flush();
#else
    if (!sd_ready_) return;
    File f = SD_MMC.open(LOG_CSV_PATH, FILE_APPEND);
    if (f) {
        f.print(timestamp_ms);
        f.print(",");
        f.print(intent.c_str());
        f.print(",");
        f.print(static_cast<int>(left_pwm));
        f.print(",");
        f.print(static_cast<int>(right_pwm));
        f.print(",");
        f.print(confidence);
        f.print(",");
        f.println(reason.c_str());
        f.close();
    }
#endif
}

void SDLogger::flush() {
#ifdef PHASE0_SIMULATION
    if (log_file_.is_open()) log_file_.flush();
#else
    // SD writes are immediate in FILE_APPEND mode.
#endif
}

SDLogger sd_logger;
