# PiPod - Raspberry Pi Zero based music player

This is a Python script that allows you to use your Pi Zero to play local music through MP3 files. It utilizes an OLED display, 6 buttons, and an audio output to let you enjoy your music on the go.

---

## Features

1. **Album Organizing**
2. **Music Metadata Display**
3. **Music Playing Modes**
4. **Bluetooth** *(Unreliable)*

---

## Components Required

1. Raspberry Pi Zero series SBC
2. Anything that converts HDMI to a 3.5mm jack (or a compatible audio HAT/USB sound card)
3. SSD1306 OLED Display (I2C)
4. 6 Push Buttons

---

## Installation Prerequisites

1. Mutagen
2. VLC

---

## Installation Commands

```bash
git clone "URL"
cd pipod
chmod +x install.sh
sudo ./install.sh

```

---

## Pinout

Connect the buttons from **Ground** to the following BCM GPIO pins:

| Button Function | GPIO Pin |
| --- | --- |
| **Play / Select** | `PIN_PLAY_SELECT = 12` |
| **Next** | `PIN_NEXT = 25` |
| **Prev / Back** | `PIN_PREV_BACK = 20` |
| **Volume Up / Menu Up** | `PIN_UP = 19` |
| **Volume Down / Menu Down** | `PIN_DOWN = 26` |
| **Shuffle** | `PIN_SHUFFLE = 6` |
| **Menu Toggle** | `PIN_MENU = 16` |

---

## Steps to Get Started

1. Connect the hardware according to the pinout table above.
2. Add your music files to a folder named `Music` in your home directory (`~/Music`).
3. Run the installation commands.
4. Reboot your Pi to automatically launch into the interface.
5. Use the buttons to navigate the menu and control playback.
6. Enjoy your music!

---

> **Note on Bluetooth:** Bluetooth does not currently work properly and may cause instability when launched. It is **not recommended** for daily use at this time.

---

## Upcoming Features

1. Fixed Bluetooth stability
2. Built-in games
3. Kodi launch straight from the menu
4. EmulationStation support

---

## Acknowledgements

1. Mutagen
2. VLC
3. Google Gemini

---

## Contact Me

* **Email:** kavyaan.bindlish@outlook.com
