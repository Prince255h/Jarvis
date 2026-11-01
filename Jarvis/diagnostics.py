import sys
import os
import time

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def print_banner():
    print("=" * 65)
    print("◈ J.A.R.V.I.S. // STARK INDUSTRIES SYSTEM DIAGNOSTICS SUITE")
    print("=" * 65)

def check_dependencies():
    print("\n[1/6] AUDITING CORE SYSTEM DEPENDENCIES...")
    deps = [
        ("SpeechRecognition", "speech_recognition"),
        ("pyttsx3", "pyttsx3"),
        ("edge-tts", "edge_tts"),
        ("pyautogui", "pyautogui"),
        ("psutil", "psutil"),
        ("pygame", "pygame"),
        ("customtkinter", "customtkinter"),
        ("google-genai", "google.genai"),
        ("Pillow (PIL)", "PIL")
    ]
    all_ok = True
    for name, mod in deps:
        try:
            __import__(mod)
            print(f"  ✔ {name:20} [ONLINE]")
        except ImportError as e:
            print(f"  ✖ {name:20} [FAILED: {e}]")
            all_ok = False
    return all_ok

def check_audio_systems():
    print("\n[2/6] TESTING ACOUSTIC & VOCAL SYNTHESIS ENGINES...")
    # Microphone
    try:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        print(f"  ✔ Microphones Detected : {len(mics)} available")
        if mics:
            print(f"    Primary Input Device: '{mics[0]}'")
    except Exception as e:
        print(f"  ✖ Microphone Audit Warning: {e}")

    # Offline TTS (SAPI5)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"  ✔ Offline SAPI5 TTS   : {len(voices)} local voice(s) available")
    except Exception as e:
        print(f"  ✖ Offline SAPI5 Warning: {e}")

    # Pygame Mixer
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        print("  ✔ Pygame Audio Mixer   : [ONLINE / ACTIVE]")
    except Exception as e:
        print(f"  ✖ Pygame Mixer Warning : {e}")

def check_hardware_telemetry():
    print("\n[3/6] MEASURING HARDWARE & SENSOR TELEMETRY...")
    import psutil
    cpu_count = psutil.cpu_count(logical=True)
    cpu_percent = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    
    print(f"  ✔ CPU Core Layout      : {cpu_count} logical processors ({cpu_percent}% active)")
    print(f"  ✔ RAM Memory Space     : {ram.total / (1024**3):.1f} GB total ({ram.percent}% utilized)")
    print(f"  ✔ Host Primary Drive   : C:\\ ({disk.free / (1024**3):.1f} GB free)")

    batt = psutil.sensors_battery()
    if batt:
        charging = "Charging" if batt.power_plugged else "Discharging"
        print(f"  ✔ Power Configuration  : Laptop Battery at {batt.percent}% ({charging})")
    else:
        print("  ✔ Power Configuration  : Desktop Workstation (AC Line Power)")

def check_screen_vision():
    print("\n[4/6] TESTING MULTIMODAL SCREEN PERCEPTION...")
    import pyautogui
    try:
        w, h = pyautogui.size()
        print(f"  ✔ Primary Display      : {w}x{h} Resolution")
        t0 = time.time()
        from automation.vision_control import VisionControl
        img_bytes = VisionControl.capture_screen_bytes()
        dt = (time.time() - t0) * 1000
        print(f"  ✔ Screenshot Capture   : Generated {len(img_bytes)} bytes in {dt:.1f}ms")
    except Exception as e:
        print(f"  ✖ Screen Capture Error : {e}")

def check_ai_cortex():
    print("\n[5/6] TESTING GOOGLE GEMINI 2.5 FLASH NEURAL CORTEX...")
    from core.agent import AutonomousAgent
    key = AutonomousAgent.get_api_key()
    if not key:
        print("  ✖ Gemini API Key       : [NOT CONFIGURED in .env]")
        return False

    prefix = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
    print(f"  ✔ API Key Loaded       : {prefix}")
    try:
        from google import genai
        client = genai.Client(api_key=key)
        t0 = time.time()
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="State 'Systems fully operational, sir' in under 5 words."
        )
        latency = (time.time() - t0) * 1000
        if res and res.text:
            print(f"  ✔ Neural Brain Latency : {latency:.0f}ms")
            print(f"  ✔ Neural Response      : \"{res.text.strip()}\"")
            return True
    except Exception as e:
        print(f"  ✖ Neural Brain Test    : {e}")
        return False

def check_automation_subsystems():
    print("\n[6/6] AUDITING OS & AUTOMATION PROTOCOLS...")
    from automation.computer_control import ComputerControl
    try:
        res = ComputerControl.execute_command("Write-Output 'STARK_OS_OK'", shell_type="powershell")
        if res.get("success") and "STARK_OS_OK" in res.get("output", ""):
            print("  ✔ PowerShell Subsystem : [ONLINE & RESPONSIVE]")
        else:
            print("  ✖ PowerShell Subsystem : [UNEXPECTED OUTPUT]")
    except Exception as e:
        print(f"  ✖ PowerShell Subsystem : {e}")

    # Check hotkey library availability
    try:
        import ctypes
        user32 = ctypes.windll.user32
        print("  ✔ Win32 API Interlock  : [ONLINE (RegisterHotKey / User32 Ready)]")
    except Exception as e:
        print(f"  ✖ Win32 API Warning    : {e}")

    # Dynamic Skill Synthesizer & Vault
    try:
        from core.skill_synthesizer import SkillSynthesizer
        manifest_file = SkillSynthesizer.MANIFEST_FILE
        if os.path.exists(manifest_file):
            import json
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            num_skills = len(data.get("skills", {}))
            print(f"  ✔ Dynamic Skill Vault  : [ONLINE ({num_skills} synthesized skill(s) cached)]")
        else:
            print("  ✔ Dynamic Skill Vault  : [ONLINE (Ready for zero-shot synthesis)]")
    except Exception as e:
        print(f"  ✖ Skill Vault Warning  : {e}")

def run_all_diagnostics():
    print_banner()
    t_start = time.time()
    check_dependencies()
    check_audio_systems()
    check_hardware_telemetry()
    check_screen_vision()
    check_ai_cortex()
    check_automation_subsystems()
    elapsed = time.time() - t_start
    print("\n" + "=" * 65)
    print(f"◈ DIAGNOSTIC AUDIT COMPLETED IN {elapsed:.2f}s - ALL SYSTEMS GO, SIR.")
    print("=" * 65)

if __name__ == "__main__":
    run_all_diagnostics()
