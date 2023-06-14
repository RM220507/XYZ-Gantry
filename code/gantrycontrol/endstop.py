import RPi.GPIO as GPIO

class EndStops:
    def __init__(self, X_pin, Y_pin, Z_pin):
        self.X_pin = X_pin
        self.Y_pin = Y_pin
        self.Z_pin = Z_pin

        GPIO.setup(self.X_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.Y_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.Z_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def check_values(self):
        active = []

        if GPIO.input(self.X_pin):
            active.append("X")
        if GPIO.input(self.Y_pin):
            active.append("Y")
        if GPIO.input(self.Z_pin):
            active.append("Z")
        return active
