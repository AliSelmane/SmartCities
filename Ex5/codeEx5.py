import time
import network
import ntptime
from machine import Pin, PWM

WIFI_SSID = "Orange-2mbHW"
WIFI_PASSWORD = "A9k3ywkqVVT59M3"
BROCHE_SERVO = 26            # A0 = GP26
FREQUENCE_PWM = 50           # 50 Hz
IMPULSION_MIN_US = 500       # ~0°
IMPULSION_MAX_US = 2500      # ~180°
MODE_AFFICHE = "heures"      # "heures" ou "minutes"
PERIODE_MAJ_S = 5            # secondes

btn = Pin(18, Pin.IN, Pin.PULL_DOWN)    
ANTI_REBOND_MS = 250

FUSEAUX = [
    ("UTC", 0),
    ("UTC+1", 3600),
    ("Bruxelles", None),
]
fuseau_idx = 0  # démarrage sur le premier

class Servo:
    def __init__(self, broche, freq=50, us_min=500, us_max=2500):
        self.pwm = PWM(Pin(broche))
        self.pwm.freq(freq)
        self.us_min = us_min
        self.us_max = us_max
        self.periode_us = int(1_000_000 / freq)

    def ecrire_angle(self, angle_deg):
        if angle_deg < 0:
            angle_deg = 0
        if angle_deg > 180:
            angle_deg = 180
        us = self.us_min + (self.us_max - self.us_min) * (angle_deg / 180.0)
        duty = int(us * 65535 / self.periode_us)
        self.pwm.duty_u16(duty)

def wifi_connexion(ssid, mdp, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, mdp)
        t0 = time.time()
        while not wlan.isconnected() and (time.time() - t0) < timeout:
            time.sleep(0.25)
    return wlan.isconnected()

def dernier_dim(an, mois):
    import utime
    jours = [0,31,28,31,30,31,30,31,31,30,31,30,31]
    if (an % 4 == 0 and an % 100 != 0) or (an % 400 == 0):
        jours[2] = 29
    d = jours[mois]
    while d > 0:
        ts = utime.mktime((an, mois, d, 0, 0, 0, 0, 0))
        if utime.localtime(ts)[6] == 6:
            return d
        d -= 1

def decalage_bruxelles(an, mois, jour, heure):
    dm = dernier_dim(an, 3)
    do = dernier_dim(an, 10)
    apres_mars = (mois, jour, heure) > (3, dm, 2)
    avant_oct  = (mois, jour, heure) < (10, do, 2)
    return 7200 if (apres_mars and avant_oct) else 3600

def maintenant_avec_offset(offset_s):
    a, m, j, h, mi, s, _, _ = time.localtime()  # UTC après ntp
    ts = time.mktime((a, m, j, h, mi, s, 0, 0)) + offset_s
    return time.localtime(ts)[:6]

def maintenant_bruxelles():
    a, m, j, h, mi, s, _, _ = time.localtime()  # UTC
    off = decalage_bruxelles(a, m, j, h)
    ts = time.mktime((a, m, j, h, mi, s, 0, 0)) + off
    return time.localtime(ts)[:6]

def maintenant_selon_fuseau(idx):
    nom, off = FUSEAUX[idx]
    if off is None:
        return maintenant_bruxelles()
    else:
        return maintenant_avec_offset(off)

def angle_depuis_heure(h, mi, s, mode="heures"):
    if mode == "heures":
        return ((h % 12) + mi/60 + s/3600) * 15.0
    else:
        return (mi + s/60) * 3.0

def synchroniser_ntp():
    try:
        ntptime.host = "pool.ntp.org"
        ntptime.settime()
        return True
    except:
        try:
            ntptime.host = "time.google.com"
            ntptime.settime()
            return True
        except:
            return False

def main():
    global fuseau_idx

    wifi_connexion(WIFI_SSID, WIFI_PASSWORD)
    synchroniser_ntp()

    bouton = Pin(btn, Pin.IN, Pin.PULL_DOWN)  # au repos=0, appui=1
    etat_prec = bouton.value()
    t_prec = time.ticks_ms()

    servo = Servo(BROCHE_SERVO, FREQUENCE_PWM, IMPULSION_MIN_US, IMPULSION_MAX_US)
    servo.ecrire_angle(90)
    time.sleep(0.3)

    while True:
        etat = bouton.value()
        t_now = time.ticks_ms()
        if etat_prec == 1 and etat == 0 and time.ticks_diff(t_now, t_prec) > ANTI_REBOND_MS:
            fuseau_idx = (fuseau_idx + 1) % len(FUSEAUX)
            t_prec = t_now
            print("Fuseau sélectionné :", FUSEAUX[fuseau_idx][0])
        etat_prec = etat

        a, m, j, h, mi, s = maintenant_selon_fuseau(fuseau_idx)
        ang = angle_depuis_heure(h, mi, s, MODE_AFFICHE)
        servo.ecrire_angle(ang)
        print(f"{FUSEAUX[fuseau_idx][0]}  {h:02d}:{mi:02d}:{s:02d}  -> angle {ang:6.2f}°")
        time.sleep(PERIODE_MAJ_S)

if __name__ == "__main__":
    main()


