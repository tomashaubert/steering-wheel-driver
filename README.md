# Thrustmaster Ferrari GT Experience (FGT) Linux Driver

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.x-yellow.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

A userspace driver and remapper for the **Thrustmaster Ferrari GT Experience Rumble 3-in-1** steering wheel on Linux.

This project makes this older hardware fully compatible with **Xbox Cloud Gaming (xCloud)**, **GeForce Now**, and native Linux titles by emulating a standard Xbox 360 controller or a generic steering wheel.

## 🚀 Key Features

* **Xbox 360 Emulation (XInput):** Ensures out-of-the-box compatibility with cloud streaming services and modern games.
* **Dynamic Calibration:** Includes a calibration tool to measure your specific wheel/pedal ranges and save them.
* **Pedal Logic Correction:** Handles inverted pedal logic and ensures Gas and Brake act as independent triggers (RT/LT).
* **Auto-Wait Mode:** The driver can wait for the device to be plugged in, making it ideal for background services.
* **Plug & Play:** Automated setup script for udev rules and systemd services.

## ⚙️ Installation & Setup

### 1. Fast Setup (Recommended)

Clone the repository and run the automated setup script:

```bash
git clone https://github.com/thaubert/steering-wheel-driver.git
cd steering-wheel-driver
./setup.sh
```

*This script will install udev rules (so you don't need sudo) and can set up a systemd service for you.*

### 2. Install Dependencies

```bash
pip install .
```

## 🔧 Calibration

Every Thrustmaster FGT unit might have slightly different sensor ranges. To get the best experience, run the calibration tool:

```bash
# Run the calibration wizard
fgt-calibrate
```

Follow the on-screen instructions. This will save a `~/.fgt_calibration.json` file which the driver will load automatically.

## 🎮 Usage

### Manual Start

```bash
# Xbox 360 Mode (Recommended for Cloud Gaming)
fgt-remapper --mode xbox

# Native Wheel Mode
fgt-remapper --mode wheel

# Wait for device to be plugged in
fgt-remapper --wait
```

### Background Service

If you enabled the systemd service during `setup.sh`, the driver will start automatically when you log in.

* **Start:** `systemctl --user start fgt-remapper.service`
* **Status:** `systemctl --user status fgt-remapper.service`
* **Logs:** `journalctl --user -u fgt-remapper.service -f`

## 🛠️ Technical Details

* **Device ID:** `044f:b655`
* **Library:** Uses `python-evdev` for userspace input handling and `uinput` for virtual device creation.
* **Calibration:** Maps raw 8-bit values (0-255) to High-res 16rd-bit virtual axes for smooth control.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Tomáš Haubert** - [info@tomashaubert.cz](mailto:info@tomashaubert.cz)