import os
import glob
import time
import random
import subprocess
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
import vlc
from gpiozero import Button

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# ==========================================
# GPIO PIN CONFIGURATION
# ==========================================
PIN_PLAY_SELECT = 12
PIN_NEXT        = 25
PIN_PREV_BACK   = 20
PIN_UP          = 19
PIN_DOWN        = 26
PIN_SHUFFLE     = 6
PIN_MENU        = 16  # Menu Toggle

MUSIC_DIR = os.path.expanduser("~/Music")

# ==========================================
# OLED DISPLAY SETUP
# ==========================================
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)
font = ImageFont.load_default()

class MP3PlayerSystem:
    def __init__(self):
        self.instance = vlc.Instance('--no-xlib', '--quiet', '--aout=pulse')
        self.player = self.instance.media_player_new()

        # UI Modes: "NOW_PLAYING" or "MENU"
        self.ui_state = "NOW_PLAYING"

        # Library Data
        self.tracks = []       # List of dicts: {path, title, artist, album}
        self.artists = {}      # {artist_name: [track_dicts]}
        self.albums = {}       # {album_name: [track_dicts]}

        # Playback State
        self.playlist = []
        self.current_index = 0
        self.volume = 80
        self.is_playing = False
        self.shuffle = False
        self.loop_mode = 0    # 0 = Off, 1 = Repeat One, 2 = Repeat All
        self.scroll_x = 0

        # Menu State
        self.menu_stack = []   # Navigation path history
        self.menu_items = []   # Current active menu list: [(Label, callback_or_submenu)]
        self.menu_index = 0
        self.menu_scroll = 0

        self.set_volume(self.volume)
        self.show_loading("Scanning Music...")
        self.scan_library()

        if self.tracks:
            self.playlist = [t['path'] for t in self.tracks]
            self.load_track(0)

        self.build_main_menu()

    def show_loading(self, text):
        img = Image.new("1", (device.width, device.height))
        draw = ImageDraw.Draw(img)
        draw.text((15, 25), text, font=font, fill=255)
        device.display(img)

    # --- LIBRARY SCANNER & METADATA ---
    def scan_library(self):
        """Recursively scans ~/Music for MP3 files and indexes metadata."""
        self.tracks.clear()
        self.artists.clear()
        self.albums.clear()

        if not os.path.exists(MUSIC_DIR):
            os.makedirs(MUSIC_DIR)

        mp3_files = []
        for root, _, files in os.walk(MUSIC_DIR):
            for file in files:
                if file.lower().endswith(".mp3"):
                    mp3_files.append(os.path.join(root, file))

        for filepath in sorted(mp3_files):
            title = os.path.basename(filepath)
            artist = "Unknown Artist"
            album = "Unknown Album"

            if MUTAGEN_AVAILABLE:
                try:
                    audio = MP3(filepath, ID3=ID3)
                    if 'TIT2' in audio: title = str(audio['TIT2'].text[0])
                    if 'TPE1' in audio: artist = str(audio['TPE1'].text[0])
                    if 'TALB' in audio: album = str(audio['TALB'].text[0])
                except Exception:
                    pass

            track_info = {'path': filepath, 'title': title, 'artist': artist, 'album': album}
            self.tracks.append(track_info)

            # Categorize by Artist
            if artist not in self.artists:
                self.artists[artist] = []
            self.artists[artist].append(track_info)

            # Categorize by Album
            if album not in self.albums:
                self.albums[album] = []
            self.albums[album].append(track_info)

    # --- MENU NAVIGATION SYSTEM ---
    def build_main_menu(self):
        self.menu_stack = []
        self.set_menu("Main Menu", [
            ("Now Playing", self.open_now_playing),
            ("All Songs", self.open_all_songs),
            ("Artists", self.open_artists_menu),
            ("Albums", self.open_albums_menu),
            ("Settings", self.open_settings_menu),
            ("Rescan Library", self.rescan_action)
        ])

    def set_menu(self, title, items):
        self.menu_stack.append({'title': title, 'items': items, 'index': 0, 'scroll': 0})
        self.load_current_menu()

    def load_current_menu(self):
        current = self.menu_stack[-1]
        self.menu_items = current['items']
        self.menu_index = current['index']
        self.menu_scroll = current['scroll']

    def menu_back(self):
        if len(self.menu_stack) > 1:
            self.menu_stack.pop()
            self.load_current_menu()
        else:
            self.ui_state = "NOW_PLAYING"

    def menu_up(self):
        if self.menu_index > 0:
            self.menu_index -= 1
            if self.menu_index < self.menu_scroll:
                self.menu_scroll = self.menu_index
            self.menu_stack[-1]['index'] = self.menu_index
            self.menu_stack[-1]['scroll'] = self.menu_scroll

    def menu_down(self):
        if self.menu_index < len(self.menu_items) - 1:
            self.menu_index += 1
            if self.menu_index >= self.menu_scroll + 4:
                self.menu_scroll = self.menu_index - 3
            self.menu_stack[-1]['index'] = self.menu_index
            self.menu_stack[-1]['scroll'] = self.menu_scroll

    def menu_select(self):
        if not self.menu_items:
            return
        _, action = self.menu_items[self.menu_index]
        if callable(action):
            action()

    # --- MENU ACTIONS & SUBMENUS ---
    def launch_kodi(self):
        self.show_loading("Launching Kodi...")
        self.player.stop()
        time.sleep(1)
        try:
            subprocess.Popen(["kodi"])
        except Exception as e:
            print(f"Error launching Kodi: {e}")
            self.show_loading("Kodi Error!")
            time.sleep(1.5)
            self.open_settings_menu()

    def open_now_playing(self):
        self.ui_state = "NOW_PLAYING"

    def open_all_songs(self):
        items = []
        for t in self.tracks:
            items.append((t['title'], lambda tr=t: self.play_selected_track(tr, self.tracks)))
        self.set_menu("All Songs", items)

    def open_artists_menu(self):
        items = []
        for artist in sorted(self.artists.keys()):
            items.append((artist, lambda a=artist: self.open_artist_tracks(a)))
        self.set_menu("Artists", items)

    def open_artist_tracks(self, artist):
        artist_tracks = self.artists[artist]
        items = [(t['title'], lambda tr=t: self.play_selected_track(tr, artist_tracks)) for t in artist_tracks]
        self.set_menu(artist[:15], items)

    def open_albums_menu(self):
        items = []
        for album in sorted(self.albums.keys()):
            items.append((album, lambda a=album: self.open_album_tracks(a)))
        self.set_menu("Albums", items)

    def open_album_tracks(self, album):
        album_tracks = self.albums[album]
        items = [(t['title'], lambda tr=t: self.play_selected_track(tr, album_tracks)) for t in album_tracks]
        self.set_menu(album[:15], items)

    def open_settings_menu(self):
        shf_label = f"Shuffle: {'ON' if self.shuffle else 'OFF'}"
        loop_labels = {0: "Loop: OFF", 1: "Loop: REPEAT 1", 2: "Loop: REPEAT ALL"}
        
        items = [
            (shf_label, self.toggle_shuffle_setting),
            (loop_labels[self.loop_mode], self.toggle_loop_setting),
            (f"Volume: {self.volume}%", lambda: None),
            ("Launch Kodi", self.launch_kodi)
        ]
        self.set_menu("Settings", items)

    def toggle_shuffle_setting(self):
        self.toggle_shuffle()
        self.menu_stack.pop()
        self.open_settings_menu()

    def toggle_loop_setting(self):
        self.toggle_loop()
        self.menu_stack.pop()
        self.open_settings_menu()

    def rescan_action(self):
        self.show_loading("Rescanning...")
        self.scan_library()
        self.build_main_menu()

    def play_selected_track(self, track_dict, context_tracks):
        self.playlist = [t['path'] for t in context_tracks]
        self.current_index = self.playlist.index(track_dict['path'])
        self.load_track(self.current_index)
        self.player.play()
        self.is_playing = True
        self.ui_state = "NOW_PLAYING"

    # --- PLAYBACK CONTROLS ---
    def load_track(self, index):
        if not self.playlist: return
        media = self.instance.media_new(self.playlist[index])
        self.player.set_media(media)
        self.scroll_x = 0

    def toggle_play_pause(self):
        if not self.playlist: return
        if self.player.is_playing():
            self.player.pause()
            self.is_playing = False
        else:
            self.player.play()
            self.is_playing = True

    def next_track(self):
        if not self.playlist: return
        if self.shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)
        self.load_track(self.current_index)
        if self.is_playing: self.player.play()

    def prev_track(self):
        if not self.playlist: return
        if self.shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index - 1) % len(self.playlist)
        self.load_track(self.current_index)
        if self.is_playing: self.player.play()

    def vol_up(self):
        self.volume = min(100, self.volume + 5)
        self.set_volume(self.volume)

    def vol_down(self):
        self.volume = max(0, self.volume - 5)
        self.set_volume(self.volume)

    def set_volume(self, vol):
        self.player.audio_set_volume(vol)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle

    def toggle_loop(self):
        self.loop_mode = (self.loop_mode + 1) % 3

    def toggle_ui_mode(self):
        if self.ui_state == "NOW_PLAYING":
            self.ui_state = "MENU"
        else:
            self.ui_state = "NOW_PLAYING"

    def check_track_end(self):
        if self.player.get_state() == vlc.State.Ended:
            if self.loop_mode == 1:
                self.load_track(self.current_index)
                self.player.play()
            elif self.loop_mode == 2 or self.shuffle or self.current_index < len(self.playlist) - 1:
                self.next_track()
            else:
                self.is_playing = False

    # --- RENDERING ENGINE ---
    def render(self):
        img = Image.new("1", (device.width, device.height))
        draw = ImageDraw.Draw(img)

        if self.ui_state == "MENU":
            self.render_menu(draw)
        else:
            self.render_now_playing(draw)

        device.display(img)

    def render_menu(self, draw):
        title = self.menu_stack[-1]['title']
        draw.text((0, 0), f"= {title} =", font=font, fill=255)
        draw.line((0, 11, 128, 11), fill=255)

        visible_items = self.menu_items[self.menu_scroll : self.menu_scroll + 4]
        for i, (label, _) in enumerate(visible_items):
            idx = self.menu_scroll + i
            y = 14 + (i * 12)
            if idx == self.menu_index:
                draw.rectangle((0, y, 127, y + 11), fill=255)
                draw.text((2, y), label[:18], font=font, fill=0)
            else:
                draw.text((2, y), label[:18], font=font, fill=255)

    def render_now_playing(self, draw):
        if not self.playlist:
            draw.text((10, 20), "No MP3s Found!", font=font, fill=255)
            draw.text((10, 35), "Add files to ~/Music", font=font, fill=255)
            return

        current_file = self.playlist[self.current_index]
        track_data = next((t for t in self.tracks if t['path'] == current_file), None)
        title = track_data['title'] if track_data else os.path.basename(current_file)
        artist = track_data['artist'] if track_data else "Unknown"
        album = track_data['album'] if track_data else "Unknown"

        # Top Bar
        status_str = "PLAY" if self.is_playing else "PAUS"
        shf_str = "[S]" if self.shuffle else "   "
        loop_map = {0: "   ", 1: "[L1]", 2: "[LA]"}
        draw.text((0, 0), f"{status_str} {shf_str}{loop_map[self.loop_mode]} V:{self.volume}%", font=font, fill=255)
        draw.line((0, 12, 128, 12), fill=255)

        # Scrolling Title
        title_width = len(title) * 6
        if title_width > 128:
            self.scroll_x = (self.scroll_x + 2) % (title_width + 30)
            draw.text((128 - self.scroll_x, 15), title, font=font, fill=255)
        else:
            draw.text((0, 15), title, font=font, fill=255)

        draw.text((0, 27), f"A: {artist[:18]}", font=font, fill=255)
        draw.text((0, 37), f"B: {album[:18]}", font=font, fill=255)

        # Progress Bar
        length_ms = self.player.get_length()
        time_ms = self.player.get_time()
        length_sec = max(0, length_ms // 1000) if length_ms > 0 else 1
        time_sec = max(0, time_ms // 1000) if time_ms > 0 else 0

        progress_pct = min(1.0, time_sec / length_sec)
        draw.rectangle((0, 49, 127, 54), outline=255, fill=0)
        draw.rectangle((0, 49, int(127 * progress_pct), 54), outline=255, fill=255)

        curr_str = f"{time_sec // 60:02d}:{time_sec % 60:02d}"
        tot_str = f"{length_sec // 60:02d}:{length_sec % 60:02d}"
        draw.text((25, 55), f"{curr_str} / {tot_str}", font=font, fill=255)

# Initialize Player
system = MP3PlayerSystem()

# Handlers mapped to state-aware functions
def handle_select():
    if system.ui_state == "MENU": system.menu_select()
    else: system.toggle_play_pause()

def handle_next():
    if system.ui_state == "MENU": system.menu_select()
    else: system.next_track()

def handle_prev():
    if system.ui_state == "MENU": system.menu_back()
    else: system.prev_track()

def handle_up():
    if system.ui_state == "MENU": system.menu_up()
    else: system.vol_up()

def handle_down():
    if system.ui_state == "MENU": system.menu_down()
    else: system.vol_down()

# Setup Hardware Buttons
btn_select  = Button(PIN_PLAY_SELECT, bounce_time=0.1)
btn_next    = Button(PIN_NEXT, bounce_time=0.1)
btn_prev    = Button(PIN_PREV_BACK, bounce_time=0.1)
btn_up      = Button(PIN_UP, bounce_time=0.1)
btn_down    = Button(PIN_DOWN, bounce_time=0.1)
btn_shuffle = Button(PIN_SHUFFLE, bounce_time=0.1)
btn_menu    = Button(PIN_MENU, bounce_time=0.1)

btn_select.when_pressed  = handle_select
btn_next.when_pressed    = handle_next
btn_prev.when_pressed    = handle_prev
btn_up.when_pressed      = handle_up
btn_down.when_pressed    = handle_down
btn_shuffle.when_pressed = system.toggle_shuffle
btn_menu.when_pressed    = system.toggle_ui_mode

print("MP3 Player with Menu System Running...")
try:
    while True:
        system.check_track_end()
        system.render()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nExiting...")