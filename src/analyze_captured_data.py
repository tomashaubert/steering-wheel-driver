import json
import evdev

def analyze_events(file_path):
    try:
        with open(file_path, 'r') as f:
            events = json.load(f)
        
        axis_info = {}
        buttons_pressed = set()
        
        for event in events:
            if event['type'] == evdev.ecodes.EV_ABS:
                code = event['code']
                val = event['value']
                if code not in axis_info:
                    axis_info[code] = {'min': val, 'max': val, 'values': []}
                axis_info[code]['min'] = min(axis_info[code]['min'], val)
                axis_info[code]['max'] = max(axis_info[code]['max'], val)
                axis_info[code]['values'].append(val)
            elif event['type'] == evdev.ecodes.EV_KEY:
                if event['value'] == 1: # Pressed
                    buttons_pressed.add(event['code'])
        
        print("Analysis for Axis (EV_ABS):")
        for code, info in axis_info.items():
            name = evdev.ecodes.ABS.get(code, f"Unknown({code})")
            print(f"  {name} (Code {code}): Min={info['min']}, Max={info['max']}, Range={info['max']-info['min']}")
        
        print("\nButtons Pressed (EV_KEY Codes):")
        for code in sorted(list(buttons_pressed)):
            name = evdev.ecodes.KEY.get(code, f"Unknown({code})")
            print(f"  {name} (Code {code})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_events('captured_events.json')
