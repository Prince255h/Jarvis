import threading
import queue
import time
import os
import re
import asyncio
import pygame
from config import (
    SPEECH_RATE, SPEECH_VOLUME, TTS_VOICE_ID,
    STARTUP_SFX, ACK_SFX, WAKE_SFX,
    ENABLE_NEURAL_VOICE, DEFAULT_NEURAL_VOICE, LANGUAGE_VOICES
)

class Speaker:
    """
    STARK INDUSTRIES // DUAL-ENGINE STUDIO NEURAL SPEECH SYNTHESIZER
    Features:
    - Primary: Microsoft Azure Neural Voices via edge-tts (Authentic British Jarvis voice)
    - Multilingual Neural Voice Map: Speaks English, Hindi, Spanish, French, Japanese, etc.
    - Fallback: Local offline pyttsx3 engine with dedicated COM thread
    - Markdown & syntax cleanup for natural conversational human cadence
    - Asynchronous non-blocking speech queue with sound effect playback
    """
    def __init__(self, on_speech_start=None, on_speech_end=None):
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end
        
        self.use_neural = ENABLE_NEURAL_VOICE
        self.current_neural_voice = DEFAULT_NEURAL_VOICE
        self.voice_index = TTS_VOICE_ID
        self.rate = SPEECH_RATE
        self.volume = SPEECH_VOLUME
        
        # Audio directory for temporary neural voice buffers
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_dir = os.path.join(base_dir, "data", "tts_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize pygame mixer for sound effects and neural audio
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as e:
            print(f"[Speaker] Pygame mixer init warning: {e}")
            
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    @staticmethod
    def clean_text_for_speech(text: str) -> str:
        """Strips markdown, URLs, JSON artifacts, and terminal formatting for clean vocal delivery."""
        if not text:
            return ""
        t = text.strip()
        # Remove markdown code blocks and inline code
        t = re.sub(r"```[\s\S]*?```", "", t)
        t = re.sub(r"`([^`]+)`", r"\1", t)
        # Remove markdown bold/italics
        t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
        t = re.sub(r"\*([^*]+)\*", r"\1", t)
        # Remove markdown links [text](url)
        t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
        # Remove URLs
        t = re.sub(r"https?://\S+", "link", t)
        # Remove brackets/braces often seen in logs
        t = re.sub(r"^\[.*?\]\s*", "", t)
        # Remove excessive whitespace
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def detect_voice_for_text(self, text: str) -> str:
        """Selects optimal neural voice based on language or Unicode script."""
        for char in text:
            cp = ord(char)
            if 0x0900 <= cp <= 0x097F:
                return LANGUAGE_VOICES.get("hi", self.current_neural_voice)
            elif 0x3040 <= cp <= 0x30FF or 0x4E00 <= cp <= 0x9FFF:
                return LANGUAGE_VOICES.get("ja", self.current_neural_voice)
            elif 0x0400 <= cp <= 0x04FF:
                return LANGUAGE_VOICES.get("ru", self.current_neural_voice)
            elif 0x0600 <= cp <= 0x06FF:
                return LANGUAGE_VOICES.get("ar", self.current_neural_voice)
            elif 0xAC00 <= cp <= 0xD7AF:
                return LANGUAGE_VOICES.get("ko", self.current_neural_voice)
        return self.current_neural_voice

    def _play_neural_tts(self, clean_text: str, voice_name: str, raw_text: str = None) -> bool:
        """Synthesizes and plays speech using edge-tts and pygame mixer."""
        import edge_tts
        temp_file = os.path.join(self.cache_dir, f"tts_{os.getpid()}_{int(time.time()*1000)}.mp3")
        try:
            async def _synthesize():
                communicate = edge_tts.Communicate(clean_text, voice_name)
                await communicate.save(temp_file)

            # Run in isolated event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_synthesize())
            loop.close()

            if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                return False

            # Play via pygame mixer
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()

            # Synchronized trigger: Audio has started playing right now
            self.is_speaking = True
            if self.on_speech_start:
                try:
                    self.on_speech_start(raw_text or clean_text)
                except Exception as e:
                    print(f"[Speaker] on_speech_start warning: {e}")

            while pygame.mixer.music.get_busy():
                time.sleep(0.05)

            pygame.mixer.music.unload()
            try:
                os.remove(temp_file)
            except Exception:
                pass
            return True
        except Exception as e:
            # Clean up temp file on error
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
            return False

    def _speech_worker(self):
        """Dedicated thread with COM apartment for pyttsx3 and async loop for edge-tts."""
        # Initialize pyttsx3 as local fallback
        pyttsx_engine = None
        try:
            import pyttsx3
            pyttsx_engine = pyttsx3.init()
            voices = pyttsx_engine.getProperty('voices')
            if voices:
                chosen_idx = min(self.voice_index, len(voices) - 1)
                pyttsx_engine.setProperty('voice', voices[chosen_idx].id)
            pyttsx_engine.setProperty('rate', self.rate)
            pyttsx_engine.setProperty('volume', self.volume)
        except Exception as e:
            print(f"[Speaker] Local pyttsx3 init warning: {e}")

        while True:
            item = self.speech_queue.get()
            if item is None:
                break
            
            # Item can be a string or a tuple (text, explicit_voice)
            if isinstance(item, tuple):
                raw_text, explicit_voice = item
            else:
                raw_text, explicit_voice = item, None

            clean_text = self.clean_text_for_speech(raw_text)
            if not clean_text:
                self.speech_queue.task_done()
                continue

            speech_succeeded = False
            # 1. Try Ultra-Realistic Studio Neural Voice (edge-tts)
            if self.use_neural:
                target_voice = explicit_voice if explicit_voice else self.detect_voice_for_text(clean_text)
                speech_succeeded = self._play_neural_tts(clean_text, target_voice, raw_text=raw_text)

            # 2. Seamless Local Offline Fallback (pyttsx3)
            if not speech_succeeded:
                try:
                    self.is_speaking = True
                    if self.on_speech_start:
                        try:
                            self.on_speech_start(raw_text or clean_text)
                        except Exception:
                            pass
                    if pyttsx_engine:
                        pyttsx_engine.say(clean_text)
                        pyttsx_engine.runAndWait()
                    else:
                        print(f"[JARVIS VOCAL]: {clean_text}")
                except Exception as e:
                    print(f"[Speaker] Offline TTS Error: {e}")
                    try:
                        import pyttsx3
                        pyttsx_engine = pyttsx3.init()
                    except Exception:
                        pass

            self.is_speaking = False
            if self.on_speech_end:
                try:
                    self.on_speech_end()
                except Exception:
                    pass
            self.speech_queue.task_done()

    def speak(self, text: str, voice: str = None):
        """Queue text to be spoken asynchronously with optional language voice override."""
        if text:
            print(f"[JARVIS]: {text}")
            self.speech_queue.put((text, voice))

    def play_sfx(self, sfx_path):
        """Play sound effects asynchronously."""
        def _play():
            try:
                if os.path.exists(sfx_path):
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    sound = pygame.mixer.Sound(sfx_path)
                    sound.play()
            except Exception as e:
                print(f"[Speaker] SFX play error: {e}")
        threading.Thread(target=_play, daemon=True).start()

    def play_startup_sfx(self):
        self.play_sfx(STARTUP_SFX)

    def play_ack_sfx(self):
        self.play_sfx(ACK_SFX)

    def play_wake_sfx(self):
        self.play_sfx(WAKE_SFX)

    def set_voice(self, index):
        self.voice_index = index

    def set_neural_voice(self, voice_name: str):
        """Sets the active neural voice (e.g. 'en-GB-RyanNeural', 'hi-IN-MadhurNeural')."""
        self.current_neural_voice = voice_name

    def toggle_neural(self) -> bool:
        """Toggles between studio neural TTS and local offline TTS."""
        self.use_neural = not self.use_neural
        return self.use_neural

    def stop_speech(self):
        """Immediately halts any active speech output and clears pending queue."""
        try:
            # Clear pending speech queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except Exception:
                    break
            # Halt active pygame mixer output
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
            self.is_speaking = False
            if self.on_speech_end:
                try:
                    self.on_speech_end()
                except Exception:
                    pass
        except Exception as e:
            print(f"[Speaker] stop_speech error: {e}")

