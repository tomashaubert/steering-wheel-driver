# Thrustmaster FGT Linux Driver & Remapper

This project provides a userspace driver (using `python-evdev` and `uinput`) for the **Thrustmaster Ferrari GT Experience (FGT) Rumble 3-in-1** steering wheel on Linux.

It solves common issues when using this wheel on Linux:
- **Pedal Logic:** Fixes inverted pedals (where default is pressed and press is release) and combined axis issues.
- **Deadzones & Range:** Normalizes axis values (0-255 -> 0-1024) and fixes deadzones.
- **Compatibility:** Can emulate a standard Xbox 360 controller for broad compatibility (e.g., GeForce Now, modern games).

## Features
- **Wheel Mode:** Maps inputs to a standard steering wheel layout with corrected ranges.
- **Xbox Mode:** Emulates an Xbox 360 controller (XInput), making the wheel compatible with games that don't support DirectInput wheels directly.
- **Auto-Grab:** Grabs the physical device to prevent double-input issues.

## Requirements
- Python 3
- `python-evdev`

```bash
sudo apt install python3-evdev
# or
pip install evdev
```

## Installation

### 1. Udev Rules
To allow non-root access to the device and uinput:

```bash
sudo cp 99-thrustmaster-fgt.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 2. Running Manually
```bash
# Wheel Mode (Default)
python3 src/fgt_remapper.py

# Xbox 360 Mode
python3 src/fgt_remapper.py --mode xbox
```

### 3. Systemd Service (Auto-start)
A sample service file `fgt-remapper.service` is provided. 
**Note:** You must edit the path in `ExecStart` to match your installation location.

```bash
# Edit the path
nano fgt-remapper.service

# Copy to systemd user directory
mkdir -p ~/.config/systemd/user/
cp fgt-remapper.service ~/.config/systemd/user/

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now fgt-remapper.service
```

## Project Structure
- `src/`: Python source scripts.
  - `fgt_remapper.py`: Main driver script.
  - `capture_inputs.py`, `analyze_inputs.py`: Tools for reverse engineering and debugging.
- `docs/`: Manuals and drivers.
- `BLOG_POST_DRAFT.md`: Development log and details.
