import speech_recognition as sr
import threading
import time
from config import STT_LANGUAGES

class Listener:
    """
    STARK INDUSTRIES // MULTILINGUAL ACOUSTIC SENSOR & STT ENGINE
    Supports:
    - Real-time speech recognition across 20+ world languages
    - Dynamic listening language switching via voice or UI
    - Adaptive background noise suppression and energy calibration
    - Non-blocking async loop with speech-avoidance interlock
    """
    def __init__(self, on_result=None, on_status_change=None, speaker_ref=None, default_lang="en-IN"):
        self.recognizer = sr.Recognizer()
        # Tuning parameters for fast & accurate recognition
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
        
        self.on_result = on_result
        self.on_status_change = on_status_change
        self.speaker = speaker_ref
        
        self.current_language = default_lang
        self.is_running = False
        self.is_listening = False
        self.is_muted = False
        self.thread = None

    def set_language(self, lang_name_or_code: str) -> str:
        """Sets active speech recognition language (e.g. 'hi-IN', 'es-ES', 'english', 'hindi')."""
        normalized = lang_name_or_code.strip().lower()
        code = STT_LANGUAGES.get(normalized, normalized)
        self.current_language = code
        print(f"[Listener] Speech recognition language set to: {self.current_language}")
        return self.current_language

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.on_status_change:
            self.on_status_change("MUTED" if self.is_muted else "STANDBY")
        return self.is_muted

    def _listen_loop(self):
        # Ambient noise calibration
        try:
            with sr.Microphone() as source:
                if self.on_status_change:
                    self.on_status_change("CALIBRATING")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                if self.on_status_change:
                    self.on_status_change("READY")
        except Exception as e:
            print(f"[Listener] Mic calibration warning: {e}")

        while self.is_running:
            if self.is_muted:
                time.sleep(0.2)
                continue

            # Don't listen to self while speaking
            if self.speaker and self.speaker.is_speaking:
                time.sleep(0.2)
                continue

            try:
                with sr.Microphone() as source:
                    if self.on_status_change:
                        self.on_status_change("LISTENING")
                    self.is_listening = True
                    
                    # Listen with timeout
                    audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=8)
                    
                    self.is_listening = False
                    if self.on_status_change:
                        self.on_status_change("PROCESSING")

                    # Recognize using Google Speech Recognition in active language
                    target_lang = self.current_language if self.current_language != "auto" else "en-IN"
                    text = self.recognizer.recognize_google(audio, language=target_lang)
                    
                    if text and text.strip():
                        print(f"[USER HEARD ({target_lang})]: {text}")
                        if self.on_result:
                            self.on_result(text.strip())

            except sr.WaitTimeoutError:
                # Normal when silence
                pass
            except sr.UnknownValueError:
                # Unintelligible noise
                pass
            except sr.RequestError as e:
                print(f"[Listener] Network error in Google STT: {e}")
                time.sleep(1)
            except Exception as e:
                # Other audio glitches
                time.sleep(0.5)
            finally:
                self.is_listening = False
                if self.on_status_change and not self.is_muted:
                    self.on_status_change("STANDBY")
