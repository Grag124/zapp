"""sensors.py - Distance sensing for the robot (HC-SR04 ultrasonic)."""

try:
    from gpiozero import DistanceSensor
    GPIO_AVAILABLE = True
except Exception:
    GPIO_AVAILABLE = False


class ObstacleSensor:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin) if GPIO_AVAILABLE else None

    def distance_cm(self):
        """Returns obstacle distance in centimeters, or None if no sensor/GPIO."""
        if not GPIO_AVAILABLE or self.sensor is None:
            return None
        # gpiozero returns distance in meters
        return round(self.sensor.distance * 100.0, 1)

    def cleanup(self):
        if GPIO_AVAILABLE and self.sensor is not None:
            self.sensor.close()
