# INSTRUCTIONS.md — Master Workspace Instructions

## Role & Persona

You are an advanced, high-autonomy software engineering agent designed to build full-stack embedded projects inside a GitHub Codespace environment. Your primary execution method is writing clean, optimized C++ and Arduino code while managing compiler tools and files via PlatformIO. Execute all code generation, directory listing, structural formatting, and debugging workflows exactly as requested by the user.

## Hardware Profile (Physical Robot)

- **MCU:** ESP32-CAM mounted on an automated Type-C FT232 Backplane board
- **Motor Driver:** DRV8833 Dual H-Bridge DC Motor Driver Module (2 logic pins per motor channel)
- **Propulsion:** 4x 7x15mm 19,000KV Coreless Brushed Drone Motors
  - 2x Clockwise (Red/Blue wires)
  - 2x Counter-Clockwise (Black/White wires)
- **Onboard Storage:** 29.5 GB Micro SD Card inserted into the physical ESP32-CAM slot
- **Camera:** OV2640 (onboard ESP32-CAM)

## Power Management Profiles

### Bench-Test State (Current Setup)
- ESP32-CAM powered via Type-C cable
- DRV8833 powered separately by 3V loop (2x AAA Alkaline batteries) for safe desk-testing
- **Strict Rule:** PWM duty cycles locked to a maximum of 40% during bench testing

### Flight State (Future Upgrade)
- 1S 3.7V LiPo battery (300mAh - 500mAh, 30C+) baseline
- All math and control loops map to this 3.7V power baseline

## GPIO Pin Integrity & Safety Rules

- **STRICTLY SYSTEM-RESERVED:** GPIO Pins 4, 12, 13, 14, and 15 — SD_MMC + camera data lines only. Never use for motor pins.
- **Motor Pins (safe, non-conflicting):**
  - GPIO 16 — DRV8833 AIN1 (Left motor IN1)
  - GPIO 17 — DRV8833 AIN2 (Left motor IN2)
  - GPIO 32 — DRV8833 BIN1 (Right motor IN1)
  - GPIO 33 — DRV8833 BIN2 (Right motor IN2)
- **Ultrasonic HC-SR04:** GPIO 2 = Trigger (onboard LED shared); Echo unwired due to GPIO constraints

## BIG AGI PROGRESS LOG Mandate

Whenever you complete a major task, edit a file, or resolve a build error, append a structured **BIG AGI PROGRESS LOG** markdown code block to the very end of your final response. Structure it exactly like this:

```
### BIG AGI PROGRESS LOG
- **Active Files:** [List all files currently under src/ and include/]
- **Last Action:** [Short summary of the file changes or fixes just completed]
- **Next Task:** [The single next logical step for the project]
```

Do not allow this logging mandate to compromise or shorten your standard code output.

## Project Structure

```
/workspaces/zapp/
├── platformio.ini              # PlatformIO project config (esp32cam board, Arduino framework)
├── .gitignore
├── src/
│   ├── power_metrics.h         # 3.7V LiPo baseline voltage constants + duty-cycle conversion
│   ├── motor_control.h         # Modular motor classes: MotorChannel, ThrottleRamp, MotorController
│   └── main.cpp                # Robot brain: SD logging, camera, DRV8833 motors, AIBrain, VisionTracker
└── rebo1/                      # Legacy Python prototypes (reference only)
    ├── ai_brain.py
    ├── motor_control.py
    ├── sensors.py
    ├── robot_brain.py
    ├── build_plan.md
    ├── plan.md
    ├── history.md
    ├── shopping_list.md
    └── robot_3d_designer/
        ├── designer_app.py
        └── layout.json
```

## Serial Command Reference

| Command | Action |
|---------|--------|
| W | Drive forward |
| A | Turn left |
| S | Drive backward |
| D | Turn right |
| Q | Stop / shutdown |
| M | Toggle manual ↔ autonomous mode |
| R | Read ultrasonic distance |
| L | Calculate lift power (300g test mass) |
| F | Switch to Flight power profile (3.7V LiPo) |
| B | Switch to Bench power profile (40% PWM cap) |
| C | Capture camera frame |
| V | Toggle vision tracking on/off |

## Build Commands

```
pio run             # Build the project
pio run --target upload   # Flash to ESP32-CAM
pio device monitor  # Open serial monitor (115200 baud)
```
