import evdev
import json
import time
import sys

def capture_events(device_path, duration=10):
    try:
        device = evdev.InputDevice(device_path)
        print(f"Capturing from {device.name} for {duration} seconds...")
        print("MACEJTE VOLANTEM A PEDÁLY!")
        
        events = []
        start_time = time.time()
        
        # Non-blocking read or just loop
        for event in device.read_loop():
            if time.time() - start_time > duration:
                break
            
            # Record only relevant events (Axes and Buttons)
            if event.type in [evdev.ecodes.EV_KEY, evdev.ecodes.EV_ABS]:
                events.append({
                    'timestamp': event.timestamp(),
                    'type': event.type,
                    'code': event.code,
                    'value': event.value
                })
        
        with open('captured_events.json', 'w') as f:
            json.dump(events, f)
        
        print(f"Captured {len(events)} events to captured_events.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/dev/input/event5"
    dur = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    capture_events(path, dur)
