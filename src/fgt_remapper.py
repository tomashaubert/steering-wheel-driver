import evdev
import json
import os
import sys
import argparse
import time

# --- HARDWARE CONSTANTS ---
# Thrustmaster FGT has 8-bit sensors
HW_MIN = 0
HW_MAX = 255
HW_CENTER = 128

# Default calibrated ranges (sensible defaults if no config is found)
DEFAULT_CALIBRATION = {
    "axes": {
        "0": {"name": "Wheel", "min": 0, "max": 255},
        "5": {"name": "Gas",   "min": 76, "max": 255},
        "1": {"name": "Brake", "min": 20, "max": 255}
    }
}

CONFIG_PATH = os.path.expanduser("~/.fgt_calibration.json")

def load_calibration():
    """Loads calibration from JSON or returns defaults."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                # Convert keys to int if they are strings from JSON
                config['axes'] = {int(k): v for k, v in config['axes'].items()}
                print(f"[*] Loaded calibration from {CONFIG_PATH}")
                return config
        except Exception as e:
            print(f"[!] Error loading calibration: {e}. Using defaults.")
    return DEFAULT_CALIBRATION

def get_device():
    """Finds the Thrustmaster FGT device, ignoring virtual ones."""
    try:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    except PermissionError:
        print("[!] Permission denied when listing devices. Are you in the 'input' group?")
        sys.exit(1)

    for device in devices:
        # Ignore virtual devices created by this script or others
        if "Linux Driver" in device.name or "X-Box" in device.name:
            continue
        if "Thrustmaster" in device.name:
            return device
    return None

def map_val(val, in_min, in_max, out_min, out_max):
    """Linear mapping of a value from one range to another."""
    # Clamp input to the defined range
    true_min = min(in_min, in_max)
    true_max = max(in_min, in_max)
    val = max(min(val, true_max), true_min)
    
    # Calculate position in range (0.0 to 1.0)
    # Avoid division by zero
    if in_max == in_min:
        return out_min
        
    norm = (val - in_min) / (in_max - in_min)
    
    # Map to output range
    return int(out_min + norm * (out_max - out_min))

def create_uinput_wheel():
    """Creates a virtual steering wheel (Native mode - Thrustmaster FGT)"""
    v_abs = [
        (evdev.ecodes.ABS_X,     evdev.AbsInfo(value=512, min=0, max=1024, fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_GAS,   evdev.AbsInfo(value=0,   min=0, max=1024, fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_BRAKE, evdev.AbsInfo(value=0,   min=0, max=1024, fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_HAT0X, evdev.AbsInfo(value=0,   min=-1, max=1,   fuzz=0, flat=0, resolution=0)),
        (evdev.ecodes.ABS_HAT0Y, evdev.AbsInfo(value=0,   min=-1, max=1,   fuzz=0, flat=0, resolution=0)),
    ]
    # Enable buttons FGT has (304..320 range)
    v_keys = list(range(304, 320))

    return evdev.UInput(events={evdev.ecodes.EV_KEY: v_keys, evdev.ecodes.EV_ABS: v_abs}, 
                        name="Thrustmaster FGT (Linux Driver)", 
                        vendor=0x044f, product=0xb655)

def create_uinput_xbox():
    """Creates a virtual Xbox 360 controller (for Cloud Gaming / modern titles)"""
    # Xbox 360 Controller: Vendor=0x045e, Product=0x028e
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
    
    # Standard Xbox buttons
    v_keys = [
        evdev.ecodes.BTN_SOUTH,  # A
        evdev.ecodes.BTN_EAST,   # B
        evdev.ecodes.BTN_NORTH,  # Y
        evdev.ecodes.BTN_WEST,   # X
        evdev.ecodes.BTN_TL,     # LB
        evdev.ecodes.BTN_TR,     # RB
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
                        help="Emulation mode: 'wheel' for native games, 'xbox' for Cloud Gaming (default: xbox)")
    parser.add_argument("--debug", action="store_true", help="Print axis values for debugging")
    parser.add_argument("--wait", action="store_true", help="Wait for device to be connected")
    args = parser.parse_args()

    config = load_calibration()
    
    source_device = None
    while not source_device:
        source_device = get_device()
        if not source_device:
            if args.wait:
                print("\r[*] Waiting for Thrustmaster FGT device...", end="", flush=True)
                time.sleep(2)
                continue
            else:
                print("[!] Error: Thrustmaster FGT device not found!")
                return
    
    if args.wait: print("\n[*] Device found!")
    print(f"[*] Steering wheel: {source_device.name} ({source_device.path})")

    # Create virtual device
    try:
        if args.mode == "xbox":
            ui = create_uinput_xbox()
            print(f"[*] Mode: XBOX 360 (Recommended for Cloud Gaming)")
        else:
            ui = create_uinput_wheel()
            print(f"[*] Mode: WHEEL (Native Steering Wheel)")
    except Exception as e:
        print(f"[!] Error creating virtual device: {e}")
        return

    print(f"[*] Virtual driver active: {ui.name}")
    print("[*] Press Ctrl+C to stop.")
    
    try:
        source_device.grab()
        
        # --- BUTTON MAPPING ---
        # Map FGT codes to Xbox buttons
        btn_map_xbox = {
            304: evdev.ecodes.BTN_SOUTH, # Cross -> A
            305: evdev.ecodes.BTN_EAST,  # Circle -> B
            306: evdev.ecodes.BTN_WEST,  # Square -> X
            307: evdev.ecodes.BTN_NORTH, # Triangle -> Y
            308: evdev.ecodes.BTN_TL,    # L1 -> LB
            309: evdev.ecodes.BTN_TR,    # R1 -> RB
            310: evdev.ecodes.BTN_THUMBL, # L2 -> L3
            311: evdev.ecodes.BTN_THUMBR, # R2 -> R3
            312: evdev.ecodes.BTN_SELECT, # Select -> Back
            313: evdev.ecodes.BTN_START,  # Start -> Start
            316: evdev.ecodes.BTN_MODE    # Mode -> Guide (Home)
        }

        # Axis codes
        WHEEL_AXIS = 0
        GAS_AXIS = 5
        BRAKE_AXIS = 1

        for event in source_device.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                
                # Calibration values
                c_wheel = config['axes'][WHEEL_AXIS]
                c_gas   = config['axes'][GAS_AXIS]
                c_brake = config['axes'][BRAKE_AXIS]

                if args.mode == "xbox":
                    # Gas: Map to RT (ABS_RZ)
                    if event.code == GAS_AXIS:
                        val = map_val(event.value, c_gas['max'], c_gas['min'], 0, 255)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_RZ, val)
                        if args.debug: print(f"Gas: {event.value} -> {val}")

                    # Brake: Map to LT (ABS_Z)
                    elif event.code == BRAKE_AXIS:
                        val = map_val(event.value, c_brake['max'], c_brake['min'], 0, 255)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_Z, val)
                        if args.debug: print(f"Brake: {event.value} -> {val}")

                    # Wheel: Map to Left Stick X (ABS_X)
                    elif event.code == WHEEL_AXIS:
                        val = map_val(event.value, c_wheel['min'], c_wheel['max'], -32768, 32767)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_X, val)
                        if args.debug: print(f"Wheel: {event.value} -> {val}")

                    # D-Pad / HAT Switch (16, 17) -> Map 1:1
                    elif event.code in [16, 17]:
                        ui.write(evdev.ecodes.EV_ABS, event.code, event.value)

                else: # WHEEL MODE
                    if event.code == WHEEL_AXIS:
                        val = map_val(event.value, c_wheel['min'], c_wheel['max'], 0, 1024)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_X, val)
                    elif event.code == GAS_AXIS:
                        val = map_val(event.value, c_gas['max'], c_gas['min'], 0, 1024)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_GAS, val)
                    elif event.code == BRAKE_AXIS:
                        val = map_val(event.value, c_brake['max'], c_brake['min'], 0, 1024)
                        ui.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_BRAKE, val)
                    elif event.code in [16, 17]:
                        ui.write(evdev.ecodes.EV_ABS, event.code, event.value)
                
                ui.syn()

            elif event.type == evdev.ecodes.EV_KEY:
                if args.mode == "xbox":
                    target = btn_map_xbox.get(event.code)
                    if target:
                        ui.write(evdev.ecodes.EV_KEY, target, event.value)
                        ui.syn()
                        if args.debug: print(f"Button: {event.code} -> {target} ({event.value})")
                else:
                    # Wheel mode: forward as is
                    ui.write(evdev.ecodes.EV_KEY, event.code, event.value)
                    ui.syn()

    except KeyboardInterrupt:
        print("\n[*] Stopping driver...")
    finally:
        try:
            source_device.ungrab()
        except:
            pass
        ui.close()

if __name__ == "__main__":
    run_remapper()
