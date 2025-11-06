from machine import Pin, ADC
from time import sleep_ms, ticks_ms, ticks_diff
import neopixel
import urandom

# Broches
PIN_MIC = 26          # micro analogique
PIN_NEOPIXEL = 18     # LED RGB WS2813
NB_LEDS = 1

# Matériel
micro = ADC(PIN_MIC)
led = neopixel.NeoPixel(Pin(PIN_NEOPIXEL), NB_LEDS)
led_onboard = Pin("LED", Pin.OUT)

# Paramètres détection
SEUIL = 33000         # valeur trouvée pendant le test
REFRACT_MS = 180      # évite plusieurs détections d’un seul bruit
MIN_BRIGHT = 40       # pas de couleur trop sombre

# Pour le BPM
PERIODE_LOG_MS = 60_000    # on fait une moyenne toutes les 60s
BPM_MIN = 40               # on garde que les BPM réalistes
BPM_MAX = 220

def couleur_aleatoire_vive():
    # couleur random mais visible
    r = urandom.getrandbits(8)
    g = urandom.getrandbits(8)
    b = urandom.getrandbits(8)
    if r < MIN_BRIGHT and g < MIN_BRIGHT and b < MIN_BRIGHT:
        i = urandom.getrandbits(2) % 3
        if i == 0:
            r = 255
        elif i == 1:
            g = 255
        else:
            b = 255
    return (r, g, b)

def ecrire_bpm_moyen(fichier, bpm_moyen):
    # on ouvre , on écrit et on ferme (pour pas perdre les données)
    try:
        with open(fichier, "a") as f:
            f.write(str(bpm_moyen) + "\n")
    except Exception as e:
        print("err écriture:", e)

def main():
    # on part LED éteinte
    led[0] = (0, 0, 0)
    led.write()
    led_onboard.value(0)

    # petit échauffement du capteur (sinon 1ère valeur va être biaisée)
    for _ in range(200):
        micro.read_u16()
        sleep_ms(2)

    last_val = SEUIL          # valeur précédente du micro
    last_hit = ticks_ms()     # dernier beat confirmé
    prev_hit = None           # beat d'avant (pour calcul BPM)

    # pour le log minute
    start_minute = ticks_ms()
    bpms_minute = []          # on stocke les bpm d’ici 60s

    while True:
        val = micro.read_u16()
        now = ticks_ms()

        # détection du passage sous → au-dessus du seuil
        if (last_val <= SEUIL) and (val > SEUIL):
            # on regarde aussi si on n’est pas trop proche du précédent
            if ticks_diff(now, last_hit) > REFRACT_MS:
                last_hit = now

                # on change la couleur
                led[0] = couleur_aleatoire_vive()
                led.write()
                led_onboard.value(1)

                # calcul du bpm à partir du temps entre 2 beats
                if prev_hit is not None:
                    t = ticks_diff(now, prev_hit)
                    if t > 0:
                        bpm = 60000 / t
                        # on garde que les valeurs logiques
                        if BPM_MIN <= bpm <= BPM_MAX:
                            bpms_minute.append(bpm)
                            print("bpm:", bpm)
                # on met à jour le beat précédent
                prev_hit = now
        else:
            led_onboard.value(0)

        # toutes les 60s on fait la moyenne et on écrit
        if ticks_diff(now, start_minute) >= PERIODE_LOG_MS:
            if len(bpms_minute) > 0:
                bpm_moyen = sum(bpms_minute) / len(bpms_minute)
            else:
                bpm_moyen = 0
            print("bpm moyen 1min:", bpm_moyen)
            ecrire_bpm_moyen("bpm_log.txt", bpm_moyen)

            # on repart pour la minute suivante
            bpms_minute = []
            start_minute = now

        last_val = val
        sleep_ms(5)

if __name__ == "__main__":
    main()
