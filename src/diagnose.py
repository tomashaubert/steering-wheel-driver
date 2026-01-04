import evdev
import json
import os
import sys

CONFIG_PATH = os.path.expanduser("~/.fgt_calibration.json")

def show_info():
    print("--- 1. KONFIGURACE (KALIBRACE) ---")
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
            print(json.dumps(data, indent=2))
    else:
        print("SOUBOR NEEXISTUJE!")

    print("\n--- 2. SUROVÁ DATA Z VOLANTU ---")
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    fgt = None
    for d in devices:
        # Ignorujeme naše virtuální zařízení
        if "Linux Driver" in d.name or "X-Box" in d.name:
            continue
            
        if "Thrustmaster" in d.name:
            fgt = d
            break
    
    if not fgt:
        print("Volant nenalezen!")
        return

    print(f"Zařízení: {fgt.name}")
    print("Testování vstupů (Stiskněte Ctrl+C pro ukončení)...")
    print("Hýbejte volantem a mačkejte pedály.")
    
    try:
        fgt.grab() # Abychom viděli jen my
        for event in fgt.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                print(f"Osa {event.code}: Hodnota {event.value}")
            elif event.type == evdev.ecodes.EV_KEY:
                print(f"Tlačítko {event.code}: {event.value}")
    except KeyboardInterrupt:
        pass
    finally:
        try:
            fgt.ungrab()
        except:
            pass

if __name__ == "__main__":
    show_info()
