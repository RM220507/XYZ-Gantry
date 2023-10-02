from HR8825 import HR8825
from L298N import L298N
from endstop import EndStops
from position import Position, Position_2D

import RPi.GPIO as GPIO
from ConfigParser import SafeConfigParser

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class Gantry:
    def __init__(self, motorA, motorB, zmotor, endstops, limits, calibration):
        self.XY_motorA = motorA
        self.XY_motorB = motorB
        self.Z_motor = zmotor

        self.endstops = endstops
        self.limits = limits
        self.center = self.limits.floor_div(2)

        self.homed = False
        self.XY_steps_per_mm = calibration[0]
        self.Z_steps_per_mm = calibration[1]

        self.XY_motorA.SetMicroStep("software", "fullstep")
        self.XY_motorB.SetMicroStep("software", "fullstep")

        print("Gantry Initiated")

    def kill(self):
        self.XY_motorA.Stop()
        self.XY_motorB.Stop()
        self.Z_motor.Stop()

    def goto(self, destination):
        print("Go To: ", destination.x, destination.y, destination.z)
        destination.subtract(self.position)
        self.jog(destination)

    def jog(self, distance):
        print("Jog: ", distance.x, distance.y, distance.z)
        destination = self.position.copy()
        destination.add(distance)
        if destination.within(self.limits):
            z_jog = round(-1 * distance.z * self.Z_steps_per_mm)
            self.Z_motor.step(z_jog)
            self.Z_motor.Stop()

            mA_steps = 0
            mB_steps = 0

            x_jog = round(distance.x * self.XY_steps_per_mm)
            mA_steps += x_jog
            mB_steps -= x_jog

            y_jog = round(distance.y * self.XY_steps_per_mm)
            mA_steps -= y_jog
            mB_steps -= y_jog

            self.XY_interlaced(mA_steps, mB_steps)
            self.XY_motorA.Stop()
            self.XY_motorB.Stop()
            self.position.set_from_pos(destination)
        else:
            print("Gantry Error: Cannot move motors - destination surpasses limits")

    def XY_interlaced(self, motorA_steps, motorB_steps):
        motorA_dir = motorA_steps > 0
        motorB_dir = motorB_steps > 0
        motorA_steps = abs(motorA_steps)
        motorB_steps = abs(motorB_steps)
        if motorA_steps > 0 and motorB_steps > 0:
            for _ in range(min(motorA_steps, motorB_steps)):
                self.XY_motorA.TurnStep(motorA_dir, 1)
                self.XY_motorB.TurnStep(motorB_dir, 1)

        if motorA_steps > motorB_steps:
            self.XY_motorA.TurnStep(motorA_dir, (motorA_steps - motorB_steps))
        elif motorB_steps > motorA_steps:
            self.XY_motorB.TurnStep(motorB_dir, (motorB_steps - motorA_steps))

    def home(self):
        print("Homing Gantry...")
        while "Z" not in self.endstops.check_values():
            self.Z_motor.step(10)
        self.Z_motor.Stop()
        print("Axis Homed: Z")

        while "Y" not in self.endstops.check_values():
            self.XY_interlaced(1, 1)
        print("Axis Homed: Y")

        while "X" not in self.endstops.check_values():
            self.XY_interlaced(-1, 1)
        print("Axis Homed: X")
        self.XY_motorA.Stop()
        self.XY_motorB.Stop()

        self.position = Position(0, 0, 0)
        self.homed = True
        print("Homed: XYZ")

    def goto_center(self):
        self.goto(self.center)

    def return_data(self):
        return self.position.return_value()

    def cleanup(self):
        self.XY_motorA.Stop()
        self.XY_motorB.Stop()

        GPIO.cleanup()

def setup_gantry(config_file):
    parser = SafeConfigParser()
    parser.read(config_file)

    XY_A = parser.get("XY-A")
    XY_motorA = HR8825(int(XY_A["dir-pin"]), int(XY_A["step-pin"]), int(XY_A["enable-pin"]), (int(XY_A["mode-pin-1"]), int(XY_A["mode-pin-2"]), int(XY_A["mode-pin-3"])))

    XY_B = parser.get("XY-B")
    XY_motorB = HR8825(int(XY_B["dir-pin"]), int(XY_B["step-pin"]), int(XY_B["enable-pin"]), (int(XY_B["mode-pin-1"]), int(XY_B["mode-pin-2"]), int(XY_B["mode-pin-3"])))

    Z = parser.get("Z")
    Z_motor = L298N((int(Z["pin-1"]), int(Z["pin-2"]), int(Z["pin-3"]), int(Z["pin-4"])), int(Z["enable-pin"]))

    endstop_conf = parser.get("endstops")
    endstops = EndStops(int(endstop_conf["X"]), int(endstop_conf["Y"]), int(endstop_conf["Z"]))

    limit_conf = parser.get("limits")
    limits = Position(int(limit_conf["X"]), int(limit_conf["Y"]), int(limit_conf["Z"]))

    cal = parser.get("calibration")

    gantry = Gantry(XY_motorA, XY_motorB, Z_motor, endstops, limits, (cal["XY"], cal["Z"]))
    return gantry
