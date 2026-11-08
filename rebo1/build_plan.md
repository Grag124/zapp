# 🛠️ Robot Build Plan — Current Free Inventory

## ✅ Acquired / On-hand (this round)
- Flying material: bought (use as wing / flying surface).
- Battery: power bank 10,000 mAh (5V USB, ~2A+; good for Pi brain, not ideal for 4 motors directly).
- Chassis: cardboard boxes, plastic bins.
- Wheels: plastic bottle caps (+ bottles as tires).
- Wooden sticks: scavenged from outside.

## 🎯 Immediate mechanical build
1. Chassis: cardboard box/plastic bin base.
2. Mount motors (from off-brand controllers) to plastic bins/cardboard.
3. Wheels: bottle cap + bottle as spinner wheel; or plastic bin as wheel/mount.
4. Flying wing: bought material + servo/motor; servo for flap/steering.
5. Wooden sticks: use as axles, frame, or wing ribs as needed.

## ⚡ Electrical build
1. Pi <- power bank 10,000 mAh via USB (5V).
2. Motors <- scavenged H-bridge (RC ESC / printer / toy / relay+diode) powered by scavenged battery or power bank.
3. Servo <- Pi 5V or separate battery.

## 📦 Still needed (free scavenge targets)
- Motor controller: RC ESC, printer H-bridge, toy board, relay+diode, transistor.
- Sensors/camera: old webcam/phone, DIY bumper/IR.
- Storage: old phone/camera SD, USB stick.

## 🧪 Next code step
- Integrate `RobotMotors`, `ObstacleSensor`, `AIBrain` into `robot_brain.py`.
- Modes: console W/A/S/D/Q, autonomous AI.

## 🧠 AI / Storage Roadmap
- 29.5GB SD likely enough for an advanced AI prototype: Pi OS (~3GB) + Python/OpenCV/libs (~0.5GB) + lightweight model (~0.05–0.1GB) + logs/data (<2GB) ≈ under 10GB. 29.5GB usable is enough, but use SSD/external storage for growth/training.
- "Crazy advanced AI" flying obstacle avoidance: storage is likely fine; bigger limits are compute/sensors/control (Pi 4/5 recommended, Pi 2 is weak).
- Manual brain: code your own policy/state machine first; later modular AI/RL.
- Future: perception, cognition, actuation, memory, learning; grasping/moving.
