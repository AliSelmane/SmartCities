from machine import Pin, PWM, ADC, I2C
from time import sleep, sleep_ms, ticks_ms, ticks_diff
from lcd1602 import LCD1602
from dht20 import DHT20

# Broches
buzzer = PWM(Pin(20))
pot = ADC(Pin(26))
LED = Pin(18, Pin.OUT); LED.value(0)

# I2C LCD (bus 0)
i2c_lcd = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
lcd = LCD1602(i2c_lcd, 2, 16); lcd.display()

# I2C DHT20 (bus 1)
i2c_dht = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000) 
sleep_ms(100)  # tempo alim
dht20 = DHT20(i2c_dht)

# ADC 0..65535 -> 25..45 °C
def temp_conversion(pot_value):
    return 25.0 + (pot_value / 65535.0) * 20.0

# Etat clignotement
t_led = ticks_ms()
t_msg = ticks_ms()
led_state = 0
msg_state = 0

# pour le défilement
in_alarm = False



while True:
    # Consigne
    tmp_set = temp_conversion(pot.read_u16())

    # Ambiante
    try:
        tmp_amb = dht20.dht20_temperature()  
    except:
        try:
            dht20 = DHT20(i2c_dht)
            amb = dht20.dht20_temperature()
        except:
            amb = None

    if (tmp_set> 35.0) and (tmp_set < 38.0):
        in_alarm = False
    # LED 5 Hz (toggle chaque 100 ms)
        if ticks_diff(ticks_ms(), t_led) >= 100:
            t_led = ticks_ms()
            led_state ^= 1 # toggle
            LED.value(led_state)

        buzzer.duty_u16(0)
        #LCD
        lcd.clear()
        lcd.setCursor(0, 0); lcd.print("Set:     {:>5.1f}C".format(tmp_set))
        lcd.setCursor(0, 1)
        lcd.print("Ambiant: {:>5.1f}C".format(tmp_amb) if tmp_amb is not None else "Ambiant:   --.-C")

    elif (tmp_set >= 38.0):
        if ticks_diff(ticks_ms(), t_led) >= 10:
            t_led = ticks_ms()
            led_state ^= 1 # toggle
            LED.value(led_state)

        buzzer.freq(1000)
        buzzer.duty_u16(3000)

       
        if not in_alarm:
            lcd.clear()
            lcd.setCursor(5, 0)
            lcd.print("        ALARM")
            in_alarm = True

        # Clignotement et défilement
        if ticks_diff(ticks_ms(), t_msg) >= 300:
            t_msg = ticks_ms()
            msg_state ^= 1
            if msg_state:
                lcd.scrollDisplayLeft()
            else:
                # petit effet on/off
                lcd.setCursor(0, 0)
                lcd.print("            ")
                lcd.scrollDisplayLeft()  # défile seulement quand visible   

    else:
        in_alarm = False
        LED.value(0)
        buzzer.duty_u16(0)
        # LCD
        lcd.clear()
        lcd.setCursor(0, 0); lcd.print("Set:     {:>5.1f}C".format(tmp_set))
        lcd.setCursor(0, 1)
        lcd.print("Ambiant: {:>5.1f}C".format(tmp_amb) if tmp_amb is not None else "Ambiant:   --.-C")
        
