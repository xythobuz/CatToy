# https://how2electronics.com/how-to-control-servo-motor-with-raspberry-pi-pico/

import time
from machine import Pin, PWM
from servo import Servo

class Toy:
    """ Tools to control the Cat Toy hardware.
    Attributes:
        servo1: GPIO pin number of the pan servo.
        servo2: GPIO pin number of the tilt servo.
        laser: GPIO pin number of the laser diode.
    """

    # maximum movements on cardboard box
    # pan_min, pan_max, tilt_min, tilt_max
    maximum_limits = (20, 160, 0, 90)

    def __init__(self, servo1 = 28, servo2 = 27, laser = 2):
        self.laserPin = PWM(Pin(laser, Pin.OUT))
        self.laserPin.freq(1000)
        self.laser(0)

        self.pan = Servo(servo1)
        self.tilt = Servo(servo2)

        pan_min, pan_max, tilt_min, tilt_max = self.maximum_limits
        self.angle(self.pan, int((pan_max - pan_min) / 2) + pan_min)
        self.angle(self.tilt, int((tilt_max - tilt_min) / 2) + tilt_min)
        time.sleep(0.1)
        self.pan.free()
        self.tilt.free()

    def map_value(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def angle(self, servo, angle):
        if angle < 0:
            angle = 0
        if angle > 180:
            angle = 180
        servo.goto(int(self.map_value(angle, 0, 180, 0, 1024)))

    def laser(self, value):
        v = 1.0 - value
        self.laserPin.duty_u16(int(v * 65535))

    def test(self, steps = 10):
        pan_min, pan_max, tilt_min, tilt_max = self.maximum_limits

        self.laser(1)

        for y in range(tilt_min, tilt_max, int((tilt_max - tilt_min) / steps)):
            self.angle(self.tilt, y)

            for x in range(pan_min, pan_max, int((pan_max - pan_min) / steps)):
                self.angle(self.pan, x)
                time.sleep(0.2)

        self.tilt.free()
        self.pan.free()

        self.laser(0)
