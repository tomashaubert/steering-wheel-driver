import evdev
import json
import os
import sys
import argparse

# --- KONSTANTY PRO HARDWARE ---
# Thrustmaster FGT má 8-bit senzory
HW_MIN = 0
HW_MAX = 255
HW_CENTER = 128

# Kalibrované rozsahy (zjištěno analýzou)
GAS_HW_MIN = 76
GAS_HW_MAX = 255
BRAKE_HW_MIN = 20
BRAKE_HW_MAX = 255

def get_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        # Ignorujeme virtuální zařízení
        if "Linux Driver" in device.name or "X-Box" in device.name:
            continue
        if "Thrustmaster" in device.name:
            return device
    return None

def map_val(val, in_min, in_max, out_min, out_max):
    """Lineární mapování hodnoty z jednoho rozsahu do druhého."""
    # Oříznutí vstupu
    # Musíme detekovat, který limit je menší pro správné oříznutí
    true_min = min(in_min, in_max)
    true_max = max(in_min, in_max)
    val = max(min(val, true_max), true_min)
    
    # Výpočet pozice v rozsahu (0.0 až 1.0)
    norm = (val - in_min) / (in_max - in_min)
    
    # Přepočet na výstupní rozsah
    return int(out_min + norm * (out_max - out_min))

def create_uinput_wheel():
    """Vytvoří virtuální volant (původní režim - Thrustmaster FGT)"""
    v_abs = [
        (evdev.ecodes.ABS_X,     evdev.AbsInfo(value=512, min=0, max=1024, fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_GAS,   evdev.AbsInfo(value=0,   min=0, max=1024, fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_BRAKE, evdev.AbsInfo(value=0,   min=0, max=1024, fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_HAT0X, evdev.AbsInfo(value=0,   min=-1, max=1,   fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_HAT0Y, evdev.AbsInfo(value=0,   min=-1, max=1,   fuzz=0, flat=0, resolution=0)),
    ]
    # Povolíme všechna tlačítka, která FGT má (304..316 a další)
    v_keys = list(range(304, 320))

    return evdev.UInput(events={evdev.ecodes.EV_KEY: v_keys, evdev.ecodes.EV_ABS: v_abs}, 
                        name="Thrustmaster FGT (Linux Driver)", 
                        vendor=0x044f, product=0xb655)

def create_uinput_xbox():
    """Vytvoří virtuální Xbox 360 ovladač (pro GeForce Now / Cloud)"""
    # Xbox 360 Controller: Vendor=0x045e, Product=0x028e
    # Důležité: Definujeme přesně ty osy, které XInput používá.
    
    v_abs = [
        (evdev.ecodes.ABS_X,   evdev.AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)), # Left Stick X
        (evdev.ecodes.ABS_Y,   evdev.AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)), # Left Stick Y
        (evdev.ecodes.ABS_RX,  evdev.AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)), # Right Stick X
        (evdev.ecodes.ABS_RY,  evdev.AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)), # Right Stick Y
        (evdev.ecodes.ABS_Z,   evdev.AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),  # Left Trigger
        (evdev.ecodes.ABS_RZ,  evdev.AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),  # Right Trigger
        (evdev.ecodes.ABS_HAT0X, evdev.AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_HAT0Y, evdev.AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
    ]
    
    # Standardní Xbox tlačítka (ABXY, LB, RB, Back, Start, Guide, Thumbs)
    v_keys = [
        evdev.ecodes.BTN_SOUTH, # A
        evdev.ecodes.BTN_EAST,  # B
        evdev.ecodes.BTN_NORTH, # X (někdy značen jako WEST v evdev?) - Ne, NORTH je Y, WEST je X na Xboxu.
        evdev.ecodes.BTN_WEST,  # Y
        evdev.ecodes.BTN_TL,    # LB
        evdev.ecodes.BTN_TR,    # RB
        evdev.ecodes.BTN_SELECT, # Back
        evdev.ecodes.BTN_START,  # Start
        evdev.ecodes.BTN_MODE,   # Guide
        evdev.ecodes.BTN_THUMBL, # L3
        evdev.ecodes.BTN_THUMBR  # R3
    ]
    
    return evdev.UInput(events={evdev.ecodes.EV_KEY: v_keys, evdev.ecodes.EV_ABS: v_abs}, 
                        name="Microsoft X-Box 360 pad", 
                        vendor=0x045e, product=0x028e)

def run_remapper():
    parser = argparse.ArgumentParser(description="Thrustmaster FGT Remapper")
    parser.add_argument("--mode", choices=["wheel", "xbox"], default="xbox", 
                        help="Režim emulace: 'wheel' pro nativní hry, 'xbox' pro GeForce Now (default: xbox)")
    parser.add_argument("--debug", action="store_true", help="Vypisovat hodnoty os pro ladění")
    args = parser.parse_args()

    source_device = get_device()
    if not source_device:
        print("Chyba: Volant Thrustmaster FGT nebyl nalezen!")
        return

    # Vytvoření virtuálního zařízení
    try:
        if args.mode == "xbox":
            ui = create_uinput_xbox()
            print(f"Mód: XBOX 360 (Vhodné pro GeForce Now)")
        else:
            ui = create_uinput_wheel()
            print(f"Mód: WHEEL (Nativní volant)")
    except Exception as e:
        print(f"Chyba při vytváření virtuálního zařízení: {e}")
        return

    print(f"Virtuální ovladač spuštěn: {ui.name}")
    print("Ukončete pomocí Ctrl+C.")
    
    try:
        source_device.grab()
        
        # --- MAPOVÁNÍ TLAČÍTEK ---
        # Mapování FGT kódů (key) na Xbox kódy (val)
        # FGT: A=304, B=305, C=306, X=307, L1=308, R1=309, L2=310, R2=311, SE=312, ST=313
        # Xbox: A=BTN_SOUTH, B=BTN_EAST, X=BTN_WEST, Y=BTN_NORTH...
        
        # Oprava mapování podle testu:
        # FGT tlacitka 304..307 jsou hlavni celni tlacitka (Krizek, Kolecko, Ctverec, Trojuhelnik)
        btn_map_xbox = {
            304: evdev.ecodes.BTN_SOUTH, # Krizek -> A
            305: evdev.ecodes.BTN_EAST,  # Kolecko -> B
            306: evdev.ecodes.BTN_WEST,  # Ctverec -> X
            307: evdev.ecodes.BTN_NORTH, # Trojuhelnik -> Y
            308: evdev.ecodes.BTN_TL,    # L1 -> LB
            309: evdev.ecodes.BTN_TR,    # R1 -> RB
            310: evdev.ecodes.BTN_THUMBL, # L2 -> L3 (nebo kamkoliv jinam, Xbox nema tlacitka L2/R2, ma triggery)
            311: evdev.ecodes.BTN_THUMBR, # R2 -> R3
            312: evdev.ecodes.BTN_SELECT, # Select -> Back
            313: evdev.ecodes.BTN_START,  # Start -> Start
            316: evdev.ecodes.BTN_MODE    # Mode -> Guide
        }

        for event in source_device.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                
                # --- XBOX MODE ---
                if args.mode == "xbox":
                    # Plyn (5): 255(uvolnen)..76(plny) -> 0..255
                    # Mapujeme na RT (ABS_RZ)
                    if event.code == 5:
                        val = map_val(event.value, GAS_HW_MAX, GAS_HW_MIN, 0, 255)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_RZ, val)
                        if args.debug: print(f"Gas: {event.value} -> {val}")

                    # Brzda (1): 255(uvolnen)..20(plny) -> 0..255
                    # Mapujeme na LT (ABS_Z)
                    elif event.code == 1:
                        val = map_val(event.value, BRAKE_HW_MAX, BRAKE_HW_MIN, 0, 255)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_Z, val)
                        if args.debug: print(f"Brake: {event.value} -> {val}")

                    # Volant (0): 0..255 -> -32768..32767
                    elif event.code == 0:
                        val = map_val(event.value, 0, 255, -32768, 32767)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_X, val)
                        if args.debug: print(f"Wheel: {event.value} -> {val}")

                    # HAT Switch (16, 17) -> Mapujeme 1:1
                    elif event.code in [16, 17]:
                        ui.write(evdev.ecodes.EV_ABS, event.code, event.value)

                # --- WHEEL MODE ---
                else:
                    if event.code == 0:
                        val = map_val(event.value, 0, 255, 0, 1024)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_X, val)
                    elif event.code == 5:
                        val = map_val(event.value, GAS_HW_MAX, GAS_HW_MIN, 0, 1024)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_GAS, val)
                    elif event.code == 1:
                        val = map_val(event.value, BRAKE_HW_MAX, BRAKE_HW_MIN, 0, 1024)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_BRAKE, val)
                    elif event.code in [16, 17]:
                        ui.write(evdev.ecodes.EV_ABS, event.code, event.value)
                
                ui.syn()

            elif event.type == evdev.ecodes.EV_KEY:
                if args.mode == "xbox":
                    # Přemapování tlačítek
                    target = btn_map_xbox.get(event.code)
                    if target:
                        ui.write(evdev.ecodes.EV_KEY, target, event.value)
                        ui.syn()
                        if args.debug: print(f"Button: {event.code} -> {target} ({event.value})")
                else:
                    # Wheel mode: posíláme jak je
                    ui.write(evdev.ecodes.EV_KEY, event.code, event.value)
                    ui.syn()

    except KeyboardInterrupt:
        print("\nUkončuji ovladač...")
    finally:
        try:
            source_device.ungrab()
        except:
            pass
        ui.close()

if __name__ == "__main__":
    run_remapper()
