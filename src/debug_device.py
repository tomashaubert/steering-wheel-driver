import evdev
import time
import sys

def get_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if "Thrustmaster" in device.name and "Linux" not in device.name:
            return device
    return None

def main():
    device = get_device()
    if not device:
        print("Zařízení nenalezeno.")
        return

    print(f"Sleduji: {device.name}")
    print("Stiskněte Ctrl+C pro ukončení.")
    print("-" * 50)
    print(f"{'Volant (ABS_X)':<20} | {'Plyn (ABS_Y - Code 5)':<25} | {'Brzda (ABS_RZ - Code 1)':<25}")

    # Inicializace hodnot
    val_wheel = 128
    val_gas = 255
    val_brake = 255

    try:
        # Čteme ve smyčce
        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                if event.code == 0: # ABS_X
                    val_wheel = event.value
                elif event.code == 5: # Plyn je Code 5
                    val_gas = event.value
                elif event.code == 1: # Brzda je Code 1
                    val_brake = event.value
                
                # Výpis na jeden řádek s přepsáním (carriage return)
                sys.stdout.write(f"\r{val_wheel:<20} | {val_gas:<25} | {val_brake:<25}")
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\nUkončeno.")

if __name__ == "__main__":
    main()
