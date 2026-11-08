import time

from motor_control import RobotMotors, GPIO_AVAILABLE as MOTORS_GPIO
from sensors import ObstacleSensor, GPIO_AVAILABLE as SENSORS_GPIO
from ai_brain import AIBrain

# GPIO pin map (L298N/TB6612 H-bridge + HC-SR04). Change to match your wiring.
PIN_MAP = {
    "left_f": 17,
    "left_b": 18,
    "right_f": 27,
    "right_b": 22,
    "sensor_trigger": 23,
    "sensor_echo": 24,
}


class Robot:
    """
    Robot brain: wires RobotMotors + ObstacleSensor + AIBrain together.

    Falls back to simulation mode automatically if GPIO hardware is not
    available (e.g. running on a Chromebook / non-Pi machine).
    """

    def __init__(self, mode="auto"):
        # Decide the real run mode: 'simulation' or 'hardware'.
        if mode == "auto":
            hardware_ready = MOTORS_GPIO and SENSORS_GPIO
            self.mode = "hardware" if hardware_ready else "simulation"
        else:
            self.mode = mode

        # Build the physical-layer objects only when hardware is reachable.
        if self.mode == "hardware":
            self.motors = RobotMotors(
                PIN_MAP["left_f"],
                PIN_MAP["left_b"],
                PIN_MAP["right_f"],
                PIN_MAP["right_b"],
            )
            self.sensor = ObstacleSensor(
                PIN_MAP["sensor_trigger"], PIN_MAP["sensor_echo"]
            )
        else:
            self.motors = None
            self.sensor = None

        # AIBrain is available in both modes; defaults to "manual".
        self.brain = AIBrain()

        print(
            f"Robot initialized in {self.mode} mode "
            f"(motors_gpio={MOTORS_GPIO}, sensors_gpio={SENSORS_GPIO})."
        )

    # ------------------------------------------------------------------
    # Actuation
    # ------------------------------------------------------------------
    def control_wheels(self, direction):
        """Send a high-level direction to the motors (hardware or sim)."""
        if self.mode == "hardware" and self.motors is not None:
            if direction == "forward":
                self.motors.forward()
            elif direction == "backward":
                self.motors.backward()
            elif direction == "left":
                self.motors.turn_left()
            elif direction == "right":
                self.motors.turn_right()
            else:
                self.motors.stop()
            print(f"[WHEELS] Moving: {direction.upper()}")
            return

        # Simulation fallback — just log the command.
        print(f"[WHEELS] Moving: {direction.upper()}")

    def stop(self):
        if self.mode == "hardware" and self.motors is not None:
            self.motors.stop()
        print("[WHEELS] Stopped.")

    # ------------------------------------------------------------------
    # Sensing
    # ------------------------------------------------------------------
    def read_distance(self):
        """Return obstacle distance in cm, or None in simulation mode."""
        if self.mode == "hardware" and self.sensor is not None:
            distance = self.sensor.distance_cm()
            if distance is not None:
                print(f"[SENSOR] Distance: {distance} cm")
            return distance
        return None

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------
    def set_brain_mode(self, mode):
        """'manual' or 'autonomous' (autonomous is only meaningful on hardware)."""
        self.brain.set_mode(mode)
        print(f"[BRAIN] Mode set to: {self.brain.mode}")

    def run_autonomous_step(self):
        """One tick of autonomous obstacle-avoidance. Hardware only."""
        if self.mode != "hardware":
            print("[BRAIN] Autonomous mode requires hardware. Staying in simulation.")
            return

        distance = self.read_distance()
        action = self.brain.decide(distance)

        if action is None:
            # Manual mode returns None; fall back to idle.
            action = "stop"

        if action == "turn_left":
            action = "left"
        elif action == "turn_right":
            action = "right"

        print(f"[BRAIN] Decided: {action}")
        self.control_wheels(action)

    # ------------------------------------------------------------------
    # Physics
    # ------------------------------------------------------------------
    def calculate_lift_power(self, mass_grams):
        mass_kg = mass_grams / 1000
        power = mass_kg * 9.81
        print(f"[PHYSICS] To lift {mass_grams}g box, you need {power:.2f} Newtons of motor thrust.")
        return power

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def cleanup(self):
        """Release GPIO resources on shutdown."""
        if self.mode == "hardware":
            if self.motors is not None:
                self.motors.cleanup()
            if self.sensor is not None:
                self.sensor.cleanup()
        print("Robot brain cleaned up GPIO. Goodbye!")


if __name__ == "__main__":
    bot = Robot()
    bot.calculate_lift_power(300)  # Test the physics right away!

    print("\n=== CARDBOARD ROBOT TERMINAL CONTROL ===")
    print("Commands: W (Forward), A (Left), S (Backward), D (Right), Q (Quit)")
    print("          M (Toggle autonomous brain), R (Read distance), L (Lift power test)")

    while True:
        # Lowercase .strip() prevents crashes if you hit spacebar or capital letters
        command = input("Enter command: ").strip().lower()

        if command == "w":
            bot.control_wheels("forward")
        elif command == "a":
            bot.control_wheels("left")
        elif command == "s":
            bot.control_wheels("backward")
        elif command == "d":
            bot.control_wheels("right")
        elif command == "q":
            print("Shutting down robot brain... Goodbye!")
            bot.cleanup()
            break
        elif command == "m":
            # Toggle between manual and autonomous AI mode.
            new_mode = "autonomous" if bot.brain.mode == "manual" else "manual"
            bot.set_brain_mode(new_mode)
            if new_mode == "autonomous":
                bot.run_autonomous_step()
        elif command == "r":
            distance = bot.read_distance()
            if distance is None:
                print("[SENSOR] No distance available (simulation mode or no GPIO).")
        elif command == "l":
            bot.calculate_lift_power(300)
        elif command == "":
            continue
        else:
            print("Invalid command! Use W, A, S, D, M, R, L, or Q.")

        time.sleep(0.1)  # Prevents Chromebook CPU from running hot
