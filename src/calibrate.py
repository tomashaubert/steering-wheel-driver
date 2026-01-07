import evdev
import json
import os
import sys

CONFIG_PATH = os.path.expanduser("~/.fgt_calibration.json")

def get_device():
    """Finds the Thrustmaster FGT device, ignoring virtual ones."""
    try:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    except PermissionError:
        print("[!] Permission denied when listing devices. Try with sudo or check udev rules.")
        sys.exit(1)

    for device in devices:
        if "Linux Driver" in device.name or "X-Box" in device.name:
            continue
        if "Thrustmaster" in device.name:
            return device
    return None

def calibrate():
    device = get_device()
    if not device:
        print("[!] Error: Thrustmaster FGT device not found!")
        return

    print(f"[*] Found device: {device.name}")
    print("-" * 40)
    print("CALIBRATION TOOL V2")
    print("This tool will measure the physical range of your wheel and pedals.")
    
    def get_axis_val(code):
        return device.absinfo(code).value

    # We calibrate these axes: 0=Wheel, 5=Gas, 1=Brake
    config = {
        'version': 2,
        'axes': {
            0: {'name': 'Wheel', 'min': get_axis_val(0), 'max': get_axis_val(0)},
            5: {'name': 'Gas',   'min': get_axis_val(5), 'max': get_axis_val(5)},
            1: {'name': 'Brake',  'min': get_axis_val(1), 'max': get_axis_val(1)}
        }
    }

    steps = [
        (0, "WHEEL: Turn fully LEFT, then fully RIGHT, then center it."),
        (5, "GAS: Press the pedal fully to the floor and RELEASE it."),
        (1, "BRAKE: Press the pedal fully to the floor and RELEASE it.")
    ]

    for code, msg in steps:
        print(f"\n>>> {msg}")
        print("PRESS ANY BUTTON on the wheel when finished with this step.")
        
        while True:
            event = device.read_one()
            if event:
                if event.type == evdev.ecodes.EV_ABS and event.code in config['axes']:
                    c = event.code
                    config['axes'][c]['min'] = min(config['axes'][c]['min'], event.value)
                    config['axes'][c]['max'] = max(config['axes'][c]['max'], event.value)
                    
                    if c == code:
                        print(f"\r{config['axes'][c]['name']}: Current={event.value:3} | Range: {config['axes'][c]['min']:3} to {config['axes'][c]['max']:3}   ", end="", flush=True)
                
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                    break

    print("\n\n[*] Calibration complete!")
    print("-" * 40)
    for code, info in config['axes'].items():
        print(f"{info['name']}: Range {info['min']} to {info['max']}")
    
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"\n[*] Configuration saved to: {CONFIG_PATH}")
    except Exception as e:
        print(f"\n[!] Error saving configuration: {e}")

if __name__ == "__main__":
    calibrate()

if __name__ == "__main__":
    calibrate()
