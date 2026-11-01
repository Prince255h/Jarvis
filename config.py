import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SFX_DIR = os.path.join(DATA_DIR, "sfx")
MUSIC_DIR = os.path.join(DATA_DIR, "music")
DIALOGS_FILE = os.path.join(DATA_DIR, "dialogs.json")

# Ensure required folders exist
os.makedirs(SFX_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# Sound Effects
STARTUP_SFX = os.path.join(SFX_DIR, "startup.wav")
ACK_SFX = os.path.join(SFX_DIR, "ack.wav")
WAKE_SFX = os.path.join(SFX_DIR, "wake.wav")

# Voice & Speech Settings
ASSISTANT_NAME = "Jarvis"
SPEECH_RATE = 175          # Fast, crisp Iron Man cadence
SPEECH_VOLUME = 1.0        # 0.0 to 1.0
TTS_VOICE_ID = 0           # 0 for David (Male), 1 for Zira (Female)

# Neural Voice Configuration (Studio-Grade Edge-TTS with pyttsx3 fallback)
ENABLE_NEURAL_VOICE = True
DEFAULT_NEURAL_VOICE = "en-GB-RyanNeural"  # Authentic British Jarvis cadence
FALLBACK_NEURAL_VOICE = "en-US-GuyNeural"

# Multilingual Neural Voice Map for International Fluency
LANGUAGE_VOICES = {
    "en": "en-GB-RyanNeural",       # English (UK - Jarvis)
    "hi": "hi-IN-MadhurNeural",     # Hindi (India)
    "es": "es-ES-AlvaroNeural",     # Spanish (Spain)
    "fr": "fr-FR-HenriNeural",      # French (France)
    "de": "de-DE-ConradNeural",     # German (Germany)
    "ja": "ja-JP-KeitaNeural",      # Japanese
    "it": "it-IT-DiegoNeural",      # Italian
    "ru": "ru-RU-DmitryNeural",     # Russian
    "zh": "zh-CN-YunxiNeural",      # Chinese (Mandarin)
    "ar": "ar-SA-HamedNeural",      # Arabic (Saudi)
    "pt": "pt-BR-AntonioNeural",    # Portuguese (Brazil)
    "ko": "ko-KR-InJoonNeural",     # Korean
    "bn": "bn-IN-BashkarNeural",    # Bengali
    "te": "te-IN-MohanNeural",      # Telugu
    "ta": "ta-IN-ValluvarNeural",   # Tamil
    "mr": "mr-IN-AarohiNeural",     # Marathi
    "gu": "gu-IN-NiranjanNeural",   # Gujarati
    "ur": "ur-PK-AsadNeural",       # Urdu
    "tr": "tr-TR-AhmetNeural",      # Turkish
    "nl": "nl-NL-MaartenNeural"     # Dutch
}

# Recognition Language Mapping
STT_LANGUAGES = {
    "auto": "en-IN",
    "english": "en-IN",
    "hindi": "hi-IN",
    "spanish": "es-ES",
    "french": "fr-FR",
    "german": "de-DE",
    "japanese": "ja-JP",
    "italian": "it-IT",
    "russian": "ru-RU",
    "chinese": "zh-CN",
    "arabic": "ar-SA",
    "portuguese": "pt-BR",
    "korean": "ko-KR",
    "bengali": "bn-IN",
    "telugu": "te-IN",
    "tamil": "ta-IN",
    "marathi": "mr-IN",
    "gujarati": "gu-IN",
    "urdu": "ur-PK"
}

# Wake & Standby Triggers (Multilingual Wake Support)
WAKE_WORDS = [
    "jarvis", "wake up jarvis", "wake up", "hey jarvis", 
    "hello jarvis", "ok jarvis", "are you there jarvis",
    "जार्विस", "उठो जार्विस", "नमस्ते जार्विस", "सुनो जार्विस",
    "despierta jarvis", "hola jarvis", "reveille toi jarvis"
]

SLEEP_WORDS = [
    "goodbye jarvis", "bye jarvis", "sleep jarvis", 
    "go to sleep", "sleep now", "standby jarvis", "standby",
    "सो जाओ जार्विस", "अलविदा जार्विस", "स्टैंडबाय"
]

EXIT_WORDS = [
    "terminate jarvis", "shutdown jarvis", "close jarvis", "exit jarvis", "quit jarvis",
    "बंद करो जार्विस"
]

# Common Desktop Applications
APP_PATHS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "code": "code.exe",
    "vs code": "code.exe",
    "visual studio code": "code.exe",
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "paint": "mspaint.exe"
}

# Web URL Shortcuts
WEB_SHORTCUTS = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "chatgpt": "https://chatgpt.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "netflix": "https://www.netflix.com"
}

# Optional API Keys (read from environment or .env)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

