import pyaudio
import struct
import math
import time
import os
import random
import threading
import pygame
from config import MUSIC_DIR

class Clapper:
    def __init__(self, speaker_ref=None, on_clap_detected=None):
        self.speaker = speaker_ref
        self.on_clap_detected = on_clap_detected
        self.is_running = False
        self.thread = None
        
        # Audio configuration
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.THRESHOLD = 3500  # Amplitude threshold for clap transient
        self.cooldown = 1.5    # Seconds between triggers
        self.last_trigger_time = 0

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._clap_listener, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False

    def toggle(self):
        if self.is_running:
            self.stop()
            return False
        else:
            self.start()
            return True

    def _clap_listener(self):
        p = pyaudio.PyAudio()
        stream = None
        try:
            stream = p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
        except Exception as e:
            print(f"[Clapper] Mic stream error: {e}")
            p.terminate()
            return

        while self.is_running:
            # Skip checking if speaker is actively speaking
            if self.speaker and self.speaker.is_speaking:
                time.sleep(0.1)
                continue

            try:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                # Calculate RMS
                count = len(data) // 2
                shorts = struct.unpack(f"{count}h", data)
                sum_squares = sum(s * s for s in shorts)
                rms = math.sqrt(sum_squares / count)

                now = time.time()
                if rms > self.THRESHOLD and (now - self.last_trigger_time) > self.cooldown:
                    # Quick transient check: read next chunk, claps die quickly unlike vowels
                    next_data = stream.read(self.CHUNK, exception_on_overflow=False)
                    next_shorts = struct.unpack(f"{count}h", next_data)
                    next_rms = math.sqrt(sum(s * s for s in next_shorts) / count)
                    
                    if next_rms < (rms * 0.75):
                        # Transient verified
                        self.last_trigger_time = now
                        print(f"[Clapper] CLAP DETECTED! (RMS: {rms:.0f})")
                        self._trigger_music()
                        if self.on_clap_detected:
                            self.on_clap_detected()

            except Exception as e:
                time.sleep(0.1)

        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()

    def _trigger_music(self):
        """Play a random song from data/music or open YouTube music."""
        music_files = [
            os.path.join(MUSIC_DIR, f) for f in os.listdir(MUSIC_DIR) 
            if f.endswith(('.mp3', '.wav', '.ogg'))
        ]
        
        if music_files:
            song = random.choice(music_files)
            try:
                pygame.mixer.music.load(song)
                pygame.mixer.music.play()
                if self.speaker:
                    self.speaker.speak(f"Playing {os.path.basename(song)}, sir.")
            except Exception as e:
                print(f"[Clapper] Music play error: {e}")
        else:
            if self.speaker:
                self.speaker.speak("Clap detected, sir. Opening ambient music.")
            import webbrowser
            webbrowser.open("https://www.youtube.com/watch?v=jfKfPfyJRdk") # Lofi / ambient
