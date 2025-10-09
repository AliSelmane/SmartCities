from machine import Pin, PWM, ADC
import time

# Broches
buzzer = PWM(Pin(20))
pot = ADC(Pin(26))
led = Pin(16, Pin.OUT)
btn = Pin(18, Pin.IN, Pin.PULL_DOWN)

# Fréquences des notes
C5=523; D5=587; E5=659; F5=698; Fs5=740; G5=784; A5=880

# Mélodies
mario_notes = [E5, G5, E5, C5, D5, G5]
mario_tempos = [0.1, 0.1, 0.1, 0.1, 0.1, 0.15]

megalovania_notes = [D5, D5, D5, 0, A5, D5, 0, G5, 0, Fs5, 0, F5, 0, E5, 0, C5, E5]
megalovania_tempos = [0.1]*len(megalovania_notes)

# Variables globales
mode = 0               # 0 = Mario, 1 = Megalovania
arret_immediat = False # indicateur d'interruption immédiate

# Fonctions utilitaires
def duty_depuis_potar():
    val = pot.read_u16()
    return int(val / 16)  # volume adouci

def check_bouton():
    # Surveille le bouton et change de mode si on appuie
    global mode, arret_immediat
    if btn.value():
        mode = 1 - mode          # on change de morceau
        arret_immediat = True    # on coupe la lecture en cours
        print(">> Mode :", "Megalovania" if mode else "Mario")
        time.sleep(0.25)         # anti-rebond

def jouer_note(freq, duree):
    # Joue une note, mais peut être interrompue à tout moment
    global arret_immediat

    # Si c’est une pause
    if freq == 0:
        led.value(0)
        t_fin = time.ticks_add(time.ticks_ms(), int(duree*1000))
        while time.ticks_diff(t_fin, time.ticks_ms()) > 0:
            check_bouton()
            if arret_immediat:
                return
            time.sleep(0.01)
        return

    # Sinon on joue la note
    buzzer.freq(freq)
    led.value(1)
    t_fin = time.ticks_add(time.ticks_ms(), int(duree*1000))
    while time.ticks_diff(t_fin, time.ticks_ms()) > 0:
        check_bouton()
        if arret_immediat:
            break
        duty = duty_depuis_potar()
        buzzer.duty_u16(duty)
        time.sleep(0.01)

    buzzer.duty_u16(0)
    led.value(0)

# --- Boucle principale ---
print("Appuie sur le bouton pour changer de musique !")

while True:
    arret_immediat = False

    # Sélection du morceau courant
    if mode == 0:
        notes = mario_notes
        tempos = mario_tempos
    else:
        notes = megalovania_notes
        tempos = megalovania_tempos

    # Lecture du morceau
    for i in range(len(notes)):
        jouer_note(notes[i], tempos[i])
        if arret_immediat:
            arret_immediat = False  # on relâche le boolean
            break                   # on quitte la boucle pour changer direct
