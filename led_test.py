from machine import Pin
from utime import sleep

led_cockpit = Pin(2, Pin.OUT)
led_cabin_1 = Pin(6, Pin.OUT)
led_cabin_2 = Pin(10, Pin.OUT)
led_cabin_3 = Pin(14, Pin.OUT)

while True:
    led_cockpit.toggle()
    led_cabin_1.toggle()
    led_cabin_2.toggle()
    led_cabin_3.toggle()
    sleep(1)