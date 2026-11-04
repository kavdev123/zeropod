#!/usr/bin/env bash

# Exit immediately if a command fails
set -e

echo "=========================================="
echo " Starting Pi MP3 Player Installation "
echo "=========================================="

# 1. Update package lists
echo "[1/7] Updating APT system package index..."
sudo apt-get update -y

# 2. Install System Dependencies & Audio Drivers
echo "[2/7] Installing required system dependencies, VLC, PulseAudio, and Bluetooth tools..."
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-pil \
    libffi-dev \
    libssl-dev \
    vlc \
    libvlc-dev \
    pulseaudio \
    pulseaudio-module-bluetooth \
    bluez \
    wireplumber \
    i2c-tools \
    python3-smbus

# 3. Enable I2C Interface on Raspberry Pi
echo "[3/7] Enabling I2C interface..."
if command -v raspi-config > /dev/null; then
    sudo raspi-config nonint do_i2c 0
    echo "I2C interface enabled via raspi-config."
else
    echo "Warning: raspi-config not found. Please ensure I2C is enabled in /boot/config.txt."
fi

# 4. Install Python Dependencies
echo "[4/7] Installing Python library dependencies..."
pip3 install --break-system-packages --upgrade pip setuptools wheel || pip3 install --upgrade pip setuptools wheel

pip3 install --break-system-packages \
    luma.oled \
    python-vlc \
    gpiozero \
    mutagen \
    RPi.GPIO || \
pip3 install \
    luma.oled \
    python-vlc \
    gpiozero \
    mutagen \
    RPi.GPIO

# 5. Create Default Music Directory
echo "[5/7] Setting up Music directory..."
MUSIC_PATH="$HOME/Music"
if [ ! -d "$MUSIC_PATH" ]; then
    mkdir -p "$MUSIC_PATH"
    echo "Created directory: $MUSIC_PATH"
else
    echo "Directory already exists: $MUSIC_PATH"
fi

# 6. Configure Permissions (I2C & GPIO groups)
echo "[6/7] Adding user '$USER' to 'i2c' and 'gpio' groups..."
sudo usermod -aG i2c,gpio "$USER" || true

# 7. Setup Systemd Service to Run at Boot
echo "[7/7] Configuring auto-start service..."

# Assuming your python script is named 'player.py' and located in your home directory or current folder.
# We will point it to the absolute path of player.py where install.sh is run, or look in $HOME.
SCRIPT_PATH="$(pwd)/player.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Warning: 'player.py' not found in current directory ($(pwd))."
    echo "Please ensure your Python script is named 'player.py' or update the service file later."
fi

SERVICE_FILE="/etc/systemd/system/mp3player.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Raspberry Pi OLED MP3 Player
After=network.target sound.target bluetooth.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $SCRIPT_PATH
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mp3player.service

echo "=========================================="
echo "        Installation Completed!          "
echo "=========================================="
echo "Notes:"
echo " 1. Add your .mp3 files into ~/Music"
echo " 2. The script is configured to start automatically on boot."
echo " 3. Control the service manually using:"
echo "    sudo systemctl start mp3player"
echo "    sudo systemctl stop mp3player"
echo "    sudo systemctl status mp3player"
echo "=========================================="