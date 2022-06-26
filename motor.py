import utime
from machine import Pin, PWM
from math import ceil

class Motor:
    def __init__(self, pin1, pin2, pin3):
        self.pinA = PWM(Pin(pin1))
        self.pinB = PWM(Pin(pin2))
        self.pinA.freq(1000)
        self.pinB.freq(1000)
        self.pinEnable = Pin(pin3, Pin.OUT)

    def set_speed(self, speed, direction):
        self.direction(direction)
        self.speed(speed)
        self.pwm.duty_u16(self.speed)

    def enable(self):
        self.pinEnable(1)

    def disable(self):
        self.pinEnable(0)

    def forward(self, speed):
        # Give speed from 0-1
        if speed > 1:
            speed = 1
        elif speed < 0:
            speed = 0            
        actual_speed = ceil(65535 * speed)
        self.pinA.duty_u16(actual_speed)
        self.pinB.duty_u16(0)

    def back(self, speed):
        if speed > 1:
            speed = 1
        elif speed < 0:
            speed = 0            
        actual_speed = ceil(65535 * speed)
        self.pinA.duty_u16(actual_speed)
        self.pinB.duty_u16(0)

        self.pinA.duty_u16(0)
        self.pinB.duty_u16(actual_speed)

    def stop(self):
        self.pinA.duty_u16(0)
        self.pinB.duty_u16(0)
