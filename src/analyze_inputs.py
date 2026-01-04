import evdev
import json
import os
import sys
import time

def get_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        # Ignorujeme virtuální zařízení
        if "Linux Driver" in device.name or "X-Box" in device.name:
            continue
        if "Thrustmaster" in device.name:
            return device
    return None

def record_inputs():
    device = get_device()
    if not device:
        print("CHYBA: Volant nenalezen!")
        return

    print(f"Nahrávám vstupy ze zařízení: {device.name}")
    print("Máte 45 sekund na to, abyste:")
    print("1. Otočili volantem DOLEVA a DOPRAVA (plný rozsah).")
    print("2. Sešlápli PLYN (úplně) a pustili.")
    print("3. Sešlápli BRZDU (úplně) a pustili.")
    print("4. Zmáčkli VŠECHNA TLAČÍTKA (postupně).")
    print("-" * 40)
    print("START!")

    data = {
        "axes": {},
        "buttons": set()
    }
    
    start_time = time.time()
    try:
        device.grab()
        while time.time() - start_time < 45:
            # Čteme s timeoutem, abychom mohli kontrolovat čas smyčky
            r, w, x = select.select([device.fd], [], [], 0.5)
            if r:
                for event in device.read():
                    if event.type == evdev.ecodes.EV_ABS:
                        if event.code not in data["axes"]:
                            data["axes"][event.code] = {"min": event.value, "max": event.value, "values": []}
                        
                        ax = data["axes"][event.code]
                        ax["min"] = min(ax["min"], event.value)
                        ax["max"] = max(ax["max"], event.value)
                        # Ukládáme jen vzorek hodnot pro analýzu distribuce
                        ax["values"].append(event.value)
                        
                    elif event.type == evdev.ecodes.EV_KEY:
                        if event.value == 1: # Key down
                            data["buttons"].add(event.code)
                            print(f"Detekováno tlačítko: {event.code}")
    except Exception as e:
        print(f"Chyba: {e}")
    finally:
        try:
            device.ungrab()
        except:
            pass

    print("-" * 40)
    print("KONEC NAHRÁVÁNÍ.")
    
    # Zpracování reportu
    report = {
        "device_name": device.name,
        "axes_summary": {},
        "buttons_found": list(data["buttons"])
    }
    
    for code, info in data["axes"].items():
        # Najdeme klidovou polohu (nejčastější hodnota, mode)
        vals = info["values"]
        if vals:
            mode = max(set(vals), key=vals.count)
            report["axes_summary"][code] = {
                "min": info["min"],
                "max": info["max"],
                "most_common": mode,
                "count": len(vals)
            }

    with open("input_report.json", "w") as f:
        json.dump(report, f, indent=4)
    
    print("Report uložen do 'input_report.json'.")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    import select
    record_inputs()
