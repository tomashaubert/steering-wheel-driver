import evdev
import sys
import time

def monitor_virtual(device_path):
    try:
        device = evdev.InputDevice(device_path)
        print(f"Monitorování virtuálního zařízení: {device.name}")
        print("MACEJTE VOLANTEM! (Ctrl+C pro ukončení)")
        
        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                name = evdev.ecodes.ABS.get(event.code, "Unknown")
                print(f"\rOsa {name:10}: {event.value:4}   ", end="", flush=True)
            elif event.type == evdev.ecodes.EV_KEY:
                print(f"\nTlačítko {event.code}: {'Stisknuto' if event.value == 1 else 'Uvolněno'}")
                
    except KeyboardInterrupt:
        print("\nKončím monitorování.")
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/dev/input/event6"
    monitor_virtual(path)
