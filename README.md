![PiPod Banner](https://github.com/kavdev123/PiPod/blob/main/PiPod.png)

# PiPod - Raspberry Pi Zero based music player

This is a Python script that allows you to use your Pi Zero to play local music through MP3 files. It utilizes an OLED display, 6 buttons, and an audio output to let you enjoy your music on the go.

---

## Features

1. **Album Organizing**
2. **Music Metadata Display**
3. **Music Playing Modes**
4. **Kodi launch from menu** *(Unreliable)*

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
git clone "https://github.com/kavdev123/PiPod/"
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

## Upcoming Features

1. Bluetooth
2. Built-in games
3. Equaliser
---
## Acknowledgements 
1. **[Luma.Oled](https://github.com/rm-hull/luma.oled)** - For the fantastic OLED display driver library.
2. **[Python-VLC](https://wiki.videolan.org/Python_bindings)** - For providing robust media playback control.
3. **[Gpiozero](https://gpiozero.readthedocs.io/)** - For making hardware button integration simple and reliable.
4. **[Mutagen](https://mutagen.readthedocs.io/)** - For handling MP3 metadata and ID3 tag parsing.
5. **[Raspberry Pi Foundation](https://www.raspberrypi.org/)** - For creating the compact and versatile Pi Zero hardware.
6. **Google Gemini** - For assistance with coding, debugging, and documentation.
---

## Contact Me

* **Email:** kavyaan.bindlish@outlook.com
