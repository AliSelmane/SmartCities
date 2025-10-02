from machine import Pin
from utime import sleep

pin = Pin(16, Pin.OUT)
btn = Pin(20, Pin.IN)
pin.value(0)
#A
while True:

    if (btn.value()):
      pin.on()

    else:
       pin.off()
