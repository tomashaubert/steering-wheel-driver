#!/bin/bash

# Setup script for Thrustmaster FGT Linux Driver

set -e

echo "--- Thrustmaster FGT Linux Driver Setup ---"

# 1. Install udev rules
echo "[*] Installing udev rules..."
UDEV_FILE="99-thrustmaster-fgt.rules"
if [ -f "$UDEV_FILE" ]; then
    sudo cp "$UDEV_FILE" /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "[+] udev rules installed successfully."
else
    echo "[!] Error: $UDEV_FILE not found."
    exit 1
fi

# 2. Add user to input and uinput groups if necessary
echo "[*] Checking user groups..."
if ! groups $USER | grep -q "\binput\b"; then
    echo "[!] Adding $USER to 'input' group..."
    sudo usermod -aG input $USER
    echo "[+] Done. You might need to log out and back in for changes to take effect."
fi

# 3. Setup systemd user service
read -p "[?] Do you want to install the systemd user service for auto-start? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "[*] Setting up systemd service..."
    SERVICE_FILE="fgt-remapper.service"
    DEST_DIR="$HOME/.config/systemd/user"
    
    mkdir -p "$DEST_DIR"
    
    # Update path in service file
    SCRIPT_PATH=$(realpath src/fgt_remapper.py)
    PYTHON_PATH=$(which python3)
    
    sed "s|ExecStart=.*|ExecStart=$PYTHON_PATH $SCRIPT_PATH --mode xbox --wait|" "$SERVICE_FILE" > "$DEST_DIR/$SERVICE_FILE"
    
    systemctl --user daemon-reload
    systemctl --user enable "$SERVICE_FILE"
    echo "[+] systemd service installed and enabled."
    echo "[i] You can start it now with: systemctl --user start $SERVICE_FILE"
fi

echo "--- Setup Complete ---"
echo "[i] Next steps:"
echo "    1. Run 'python3 src/calibrate.py' to calibrate your wheel."
echo "    2. Start the driver with 'python3 src/fgt_remapper.py --mode xbox'."
