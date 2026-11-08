#ifndef POWER_METRICS_H
#define POWER_METRICS_H

#include <cstdint>

namespace PowerMetrics {

constexpr float FlightNominalVoltageV = 3.7f;
constexpr float FlightMinVoltageV = 3.0f;
constexpr float FlightMaxVoltageV = 4.2f;
constexpr const char* FlightPowerSource = "1S 3.7V LiPo";

constexpr float BenchUsbVoltageV = 5.0f;
constexpr float BenchSteadyVoltageV = 3.7f;
constexpr const char* BenchPowerSourceA = "5V USB backplane";
constexpr const char* BenchPowerSourceB = "3.7V high-capacity";

constexpr float PwmCalibrationBaselineV = 3.7f;
constexpr uint8_t LedcResolutionBits = 8;
constexpr uint32_t LedcMaxDuty = (1u << LedcResolutionBits) - 1u;
constexpr uint32_t LedcFrequencyHz = 5000;

inline uint32_t voltageToDuty(float targetVoltageV) {
    if (targetVoltageV <= 0.0f) return 0;
    if (targetVoltageV >= PwmCalibrationBaselineV) return LedcMaxDuty;
    return static_cast<uint32_t>(
        (targetVoltageV / PwmCalibrationBaselineV) * static_cast<float>(LedcMaxDuty) + 0.5f);
}

inline float dutyToVoltage(uint32_t duty) {
    if (duty >= LedcMaxDuty) return PwmCalibrationBaselineV;
    return (static_cast<float>(duty) / static_cast<float>(LedcMaxDuty)) *
           PwmCalibrationBaselineV;
}

}  // namespace PowerMetrics

#endif  // POWER_METRICS_H
