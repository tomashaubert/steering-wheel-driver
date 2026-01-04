import evdev
import sys

def debug_device(device_path):
    try:
        device = evdev.InputDevice(device_path)
        print(f"Device name: {device.name}")
        print(f"Device phys: {device.phys}")
        print(f"Device uniq: {device.uniq}")
        print(f"Vendor: {device.info.vendor:#06x}")
        print(f"Product: {device.info.product:#06x}")
        print(f"Version: {device.info.version:#06x}")
        
        print("\nCapabilities:")
        caps = device.capabilities(verbose=True)
        for cap_type, cap_list in caps.items():
            print(f"  {cap_type}:")
            for cap in cap_list:
                if isinstance(cap, tuple):
                    # For Absolute Axes, it returns (code, AbsInfo)
                    code, info = cap
                    print(f"    {code}: {info}")
                else:
                    print(f"    {cap}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/dev/input/event5"
    debug_device(path)
