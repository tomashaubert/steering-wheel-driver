import evdev
import json
import os
import sys

CONFIG_PATH = os.path.expanduser("~/.fgt_calibration.json")

def get_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if "Thrustmaster FGT" in device.name:
            return device
    return None

def calibrate():
    device = get_device()
    if not device:
        print("Chyba: Volant Thrustmaster FGT nebyl nalezen!")
        return

    print(f"Nalezeno zařízení: {device.name}")
    print("-" * 40)
    print("KALIBRACE V2: ROBUSTNÍ REŽIM")
    print("V tomto režimu budeme sledovat všechny změny nezávisle na směru.")
    
    # Inicializace s aktuálními hodnotami získáme přes device.absinfo
    def get_axis_val(code):
        return device.absinfo(code).value

    config = {
        'version': 2,
        'axes': {
            0: {'name': 'Volant', 'min': get_axis_val(0), 'max': get_axis_val(0), 'rest': get_axis_val(0)},
            5: {'name': 'Plyn',   'min': get_axis_val(5), 'max': get_axis_val(5), 'rest': get_axis_val(5)},
            1: {'name': 'Brzda',  'min': get_axis_val(1), 'max': get_axis_val(1), 'rest': get_axis_val(1)}
        }
    }

    steps = [
        (0, "VOLANT: Otočte nadoraz DOLEVA, pak nadoraz DOPRAVA a nechte ve STŘEDU."),
        (5, "PLYN: Sešlápněte PLYN až na podlahu a úplně jej UVOLNĚTE."),
        (1, "BRZDA: Sešlápněte BRZDU až na podlahu a úplně jej UVOLNĚTE.")
    ]

    for code, msg in steps:
        print(f"\n>>> {msg}")
        print("Poté STISKNĚTE LIBOVOLNÉ TLAČÍTKO na volantu.")
        
        while True:
            event = device.read_one()
            if event:
                if event.type == evdev.ecodes.EV_ABS and event.code in config['axes']:
                    c = event.code
                    config['axes'][c]['min'] = min(config['axes'][c]['min'], event.value)
                    config['axes'][c]['max'] = max(config['axes'][c]['max'], event.value)
                    # Vypisujeme jen aktuálně kalibrovanou osu
                    if c == code:
                        print(f"\r{config['axes'][c]['name']}: Aktuální={event.value:3} | Naměřeno: {config['axes'][c]['min']:3} až {config['axes'][c]['max']:3}   ", end="", flush=True)
                
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                    break

    print("\n\nKalibrace dokončena!")
    print("-" * 40)
    # Určení, co je u pedálů "stisk" a co "klid"
    # U tohoto volantu víme, že 255 je klid, ale uděláme to logicky:
    # Střed volantu je cca (min+max)/2. U pedálů je rest to, co tam bylo na začátku.
    for code, info in config['axes'].items():
        print(f"{info['name']}: Rozsah {info['min']} až {info['max']} (Klidový stav: {info['rest']})")
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"\nKonfigurace uložena do: {CONFIG_PATH}")

if __name__ == "__main__":
    calibrate()
