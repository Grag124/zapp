"""ai_brain.py - Decision-making AI layer for the robot."""


class AIBrain:
    """
    Reactive AI for obstacle avoidance.

    Modes:
      - "manual": action strings come from console input (W/A/S/D).
      - "autonomous": action is decided from sensor distance readings.
    """

    def __init__(self, max_speed=0.6, stop_distance_cm=20.0, turn_speed=0.45):
        self.max_speed = max_speed
        self.stop_distance_cm = stop_distance_cm
        self.turn_speed = turn_speed
        self.mode = "manual"

    def set_mode(self, mode):
        if mode in ("manual", "autonomous"):
            self.mode = mode

    def decide(self, distance_cm):
        """Return an action: 'forward', 'backward', 'left', 'right', 'stop', or None for manual."""
        if self.mode == "manual":
            return None

        if distance_cm is None:
            # No sensor data -> safe default is to keep going
            return "forward"

        if distance_cm > self.stop_distance_cm:
            return "forward"

        if distance_cm > self.stop_distance_cm / 2.0:
            # Obstacle is getting close -> turn to avoid it
            return "turn_left"

        # Obstacle too close -> stop
        return "stop"

    def autonomous_action(self, distance_cm):
        """Convenience: run the AI decision and clamp speed."""
        action = self.decide(distance_cm)
        if action is None:
            return "manual"
        if action in ("forward", "backward"):
            return action
        if action in ("left", "right"):
            return action
        return "stop"
