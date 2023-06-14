import RPi.GPIO as GPIO
import time

class L298N:
    def __init__(self, pins, enable):
        self.pins = pins
        self.enable = enable
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        GPIO.setup(self.enable, GPIO.OUT)

    def Stop(self):
        GPIO.output(self.enable, GPIO.LOW)
        for pin in self.pins:
            GPIO.output(pin, GPIO.LOW)

    def step(self, steps, step_sleep=0.002):
        GPIO.output(self.enable, GPIO.HIGH)
        negative = steps > 0
        for i in range(abs(steps)):
            test = i % 4
            if (test == 0 and not negative) or (test == 3 and negative):
                GPIO.output(self.pins[3], GPIO.HIGH)
                GPIO.output(self.pins[2], GPIO.LOW)
                GPIO.output(self.pins[1], GPIO.LOW)
                GPIO.output(self.pins[0], GPIO.LOW)
            elif (test == 1 and not negative) or (test == 2 and negative):
                GPIO.output(self.pins[3], GPIO.LOW)
                GPIO.output(self.pins[2], GPIO.LOW)
                GPIO.output(self.pins[1], GPIO.HIGH)
                GPIO.output(self.pins[0], GPIO.LOW)
            elif (test == 2 and not negative) or (test == 1 and negative):
                GPIO.output(self.pins[3], GPIO.LOW)
                GPIO.output(self.pins[2], GPIO.HIGH)
                GPIO.output(self.pins[1], GPIO.LOW)
                GPIO.output(self.pins[0], GPIO.LOW)
            elif (test == 3 and not negative) or (test == 0 and negative):
                GPIO.output(self.pins[3], GPIO.LOW)
                GPIO.output(self.pins[2], GPIO.LOW)
                GPIO.output(self.pins[1], GPIO.LOW)
                GPIO.output(self.pins[0], GPIO.HIGH)
            time.sleep(step_sleep)
        GPIO.output(self.enable, GPIO.LOW)
