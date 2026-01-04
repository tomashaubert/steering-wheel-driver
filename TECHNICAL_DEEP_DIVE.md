# Reviving the Thrustmaster FGT: A Linux Driver Deep Dive

**Author:** Tomáš Haubert
**Date:** January 4, 2026

How do you make a 15-year-old steering wheel work with modern Cloud Gaming on Linux? That was the challenge I faced with the **Thrustmaster Ferrari GT Experience (FGT) 3-in-1**.

While Linux "saw" the device, it was unusable for gaming. The pedals were inverted, the ranges were incomplete, and most importantly, modern web browsers (Xbox Cloud Gaming, GeForce Now) didn't know what to do with it.

Here is the technical journey of building a userspace driver in Python to solve this.

## 1. The Hardware Analysis

The first step was to understand what the hardware was actually sending. Using `evtest` and a custom Python script, we grabbed the raw HID reports.

**Device ID:** `044f:b655`

### The "Raw" Data
We immediately hit three problems:

1.  **Inverted Logic:** The pedals rested at `255` and went down to `0` when pressed. Most games expect `0` at rest and `255` (or higher) when pressed.
2.  **Dead Zones & Limits:**
    *   **Gas:** Pressed fully, it only reached `76` (not `0`).
    *   **Brake:** Pressed fully, it only reached `20` (not `0`).
    *   *Result:* In a game, you would never reach 100% throttle or braking.
3.  **Weird Mapping:**
    *   **Gas** was on Event Code `5` (often ABS_RZ).
    *   **Brake** was on Event Code `1` (often ABS_Y).

## 2. The Solution: Userspace Remapper

Instead of writing a kernel module (which is hard to maintain), I opted for a userspace approach using `python-evdev` and `uinput`. This allows us to:
1.  **Grab** the physical device (hiding it from the OS).
2.  **Read** raw events.
3.  **Process/Map** the values.
4.  **Inject** clean events into a virtual device.

### The Algorithm

We implemented a linear mapping function with clamping to handle the weird hardware ranges:

```python
def map_val(val, in_min, in_max, out_min, out_max):
    # Clamp input to hardware limits
    true_min = min(in_min, in_max)
    true_max = max(in_min, in_max)
    val = max(min(val, true_max), true_min)
    
    # Normalize position (0.0 - 1.0)
    norm = (val - in_min) / (in_max - in_min)
    
    # Scale to output
    return int(out_min + norm * (out_max - out_min))
```

This simple function solves both the inversion (by swapping min/max) and the range calibration (by using 76/20 as the limits).

## 3. The "Xbox Mode" Breakthrough

The biggest hurdle was Cloud Gaming. Browsers rely on the **standard Gamepad API**. Old DirectInput wheels often don't map correctly to this standard.

To fix this, we created a virtual **Xbox 360 Controller** instead of a generic joystick.

*   **Wheel (Axis 0)** -> Mapped to Left Stick X (`ABS_X`)
*   **Gas (Axis 5)** -> Mapped to Right Trigger (`ABS_RZ`)
*   **Brake (Axis 1)** -> Mapped to Left Trigger (`ABS_Z`)

This was the magic bullet. As soon as we emulated an XInput device, Xbox Cloud Gaming instantly recognized the controller, and the triggers provided precise analog control for gas and brake.

## 4. Automation

To make it a true "driver," it needs to be invisible. We used `systemd` to start the remapper automatically.

**Service File (`fgt-remapper.service`):**
```ini
[Service]
ExecStart=/usr/bin/python3 /path/to/driver.py --mode xbox
Restart=always
```

## Conclusion

With about 200 lines of Python, we turned e-waste into a fully functional cloud gaming controller. The latency is negligible, and the experience is on par with modern hardware.

You can find the full source code and installation instructions on my GitHub:
[Link to Repository]
