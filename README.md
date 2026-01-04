# Thrustmaster Ferrari GT Experience (FGT) Linux Driver

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.x-yellow.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

A userspace driver and remapper for the **Thrustmaster Ferrari GT Experience Rumble 3-in-1** steering wheel on Linux. 

This project solves common issues with this older hardware on modern Linux systems, making it fully compatible with **Xbox Cloud Gaming (xCloud)**, **GeForce Now**, and native Linux titles that expect an Xbox controller.

## 🚀 Key Features

*   **Xbox 360 Emulation:** Tricks the system into thinking the wheel is a standard Xbox 360 controller (XInput), ensuring compatibility with almost all modern games and cloud streaming services.
*   **Pedal Fixes:**
    *   **Inverted Logic:** Handles pedals that rest at 255 and go to 0.
    *   **Deadzone Calibration:** Automatically maps the active physical range (e.g., Gas 76-255) to the full logical range (0-100%).
    *   **Split Axes:** Ensures Gas and Brake act as independent triggers (RT/LT) rather than a combined axis.
*   **Plug & Play:** Can run as a systemd service that automatically grabs the device when plugged in.

## 🛠️ Requirements

*   Linux OS
*   Python 3
*   `uinput` kernel module (standard on most distros)

```bash
# Install dependencies
sudo apt install python3-pip
pip3 install -r requirements.txt
```

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/steering-wheel-driver.git
cd steering-wheel-driver
```

### 2. Setup Udev Rules
To access the hardware and create virtual devices without root privileges:

```bash
sudo cp 99-thrustmaster-fgt.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 3. Usage (Manual)
You can run the driver directly from the terminal. This is useful for testing.

```bash
# Xbox 360 Mode (Recommended for Cloud Gaming)
python3 src/fgt_remapper.py --mode xbox

# Native Wheel Mode (Legacy)
python3 src/fgt_remapper.py --mode wheel
```

*Note: The script will "grab" the physical device, so no other app will see the raw, broken input. Only the corrected virtual device will be visible.*

### 4. Setup Systemd Service (Auto-start)
To have the driver start automatically in the background:

1.  Edit `fgt-remapper.service` and update the `ExecStart` path to match your installation:
    ```ini
    ExecStart=/usr/bin/python3 /home/YOUR_USER/path/to/steering-wheel-driver/src/fgt_remapper.py --mode xbox
    ```
2.  Install and enable the user service:
    ```bash
    mkdir -p ~/.config/systemd/user/
    cp fgt-remapper.service ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user enable --now fgt-remapper.service
    ```

## 🔧 Calibration & Troubleshooting

### Axis Mapping (Technical Details)
Through reverse engineering, we found the following mapping for this specific model (ID `044f:b655`):

*   **Wheel:** Axis 0 (ABS_X)
*   **Gas Pedal:** Axis 5 (Mapped to Xbox Right Trigger)
*   **Brake Pedal:** Axis 1 (Mapped to Xbox Left Trigger)

### Recalibration
The script currently uses hardcoded calibration values found to be optimal for the tested unit:
*   **Gas:** 76 (Full) to 255 (Released)
*   **Brake:** 20 (Full) to 255 (Released)

If your pedals behave differently, you can modify the constants `GAS_HW_MIN` and `BRAKE_HW_MIN` at the top of `src/fgt_remapper.py`.

To check your raw values, use the provided debug tool:
```bash
python3 src/debug_device.py
```

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author
**Tomáš Haubert**  
<info@tomashaubert.cz>