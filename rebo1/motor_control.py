"""motor_control.py - Controls the robot's DC motors via GPIO (L298N / TB6612H)."""

try:
    from gpiozero import Motor
    GPIO_AVAILABLE = True
except Exception:
    GPIO_AVAILABLE = False


class RobotMotors:
    """
    4-wheel drive robot.

    Two DC motors per side (left pair / right pair), each driven through
    an H-bridge (L298N or TB6612). Speeds are floats in range -1.0..1.0
    (negative value = reverse direction).
    """

    def __init__(self, left_f, left_b, right_f, right_b):
        self.left_f = left_f
        self.left_b = left_b
        self.right_f = right_f
        self.right_b = right_b
        self.left = Motor(left_f, left_b) if GPIO_AVAILABLE else None
        self.right = Motor(right_f, right_b) if GPIO_AVAILABLE else None

    def _move(self, left_speed, right_speed):
        if not GPIO_AVAILABLE:
            return
        if left_speed >= 0:
            self.left.forward(left_speed)
        else:
            self.left.backward(-left_speed)
        if right_speed >= 0:
            self.right.forward(right_speed)
        else:
            self.right.backward(-right_speed)

    def forward(self, speed=0.6):
        self._move(speed, speed)

    def backward(self, speed=0.6):
        self._move(-speed, -speed)

    def turn_left(self, speed=0.6):
        # left wheel reverses, right wheel drives -> robot turns left
        self._move(-speed, speed)

    def turn_right(self, speed=0.6):
        # left wheel drives, right wheel reverses -> robot turns right
        self._move(speed, -speed)

    def stop(self):
        self._move(0, 0)

    def cleanup(self):
        if GPIO_AVAILABLE:
            self.left.stop()
            self.right.stop()
