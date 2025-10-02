from machine import Pin
from utime import sleep

led = Pin(16, Pin.OUT)
btn = Pin(20, Pin.IN) 
mode = 0
last_etat = 0   # pour détecter les changements

while True:
    
    etat_actuel = btn.value()
    
    if last_etat == 0 and etat_actuel == 1:
        mode = (mode + 1) % 3   # cycle entre 0,1,2
        print("Nouveau mode:", mode)
        sleep(0.2)  

    last_etat = etat_actuel

    # appliquer le mode
    if mode == 0:
        led.off() 

    elif mode == 1:  # clignotement lent 0,5 Hz
        led.on()
        sleep(1)
        led.off()
        sleep(1)

    elif mode == 2:  # clignotement rapide
        led.on()
        sleep(0.25)
        led.off()
        sleep(0.25)
