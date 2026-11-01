import sys
import os
import threading
import time

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Ensure full UTF-8 Unicode support for global multilingual speech & terminal logs
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

from core.speaker import Speaker
from core.listener import Listener
from core.brain import Brain
from core.clapper import Clapper
from ui.hud_gui import JarvisHUD

def main():
    print("=" * 60)
    print("◈ INITIALIZING J.A.R.V.I.S. // STARK OS 5.0 AI-FIRST")
    print("=" * 60)

    # 1. Initialize Speaker
    speaker = Speaker()
    speaker.play_startup_sfx()

    # 2. Forward declare HUD variable for callbacks
    app = None

    def on_speech_start(text):
        if app:
            app.after(0, lambda: app.set_status("SPEAKING"))
            if text:
                app.after(0, lambda: app.log_message("JARVIS", text))

    def on_speech_end():
        if app:
            current_st = brain.state if brain else "STANDBY"
            app.after(0, lambda: app.set_status(current_st))

    speaker.on_speech_start = on_speech_start
    speaker.on_speech_end = on_speech_end

    # 3. Initialize Brain
    def on_brain_state_change(new_state):
        if app:
            app.after(0, lambda: app.set_status(new_state))

    brain = Brain(speaker_ref=speaker, on_state_change=on_brain_state_change)

    # 4. Initialize Listener
    def on_listener_result(text):
        if app:
            app.after(0, lambda: app.log_message("USER", text))
            
        def _process():
            res = brain.process(text)
            if res and app:
                if "reply" in res and not (speaker and speaker.on_speech_start):
                    app.after(0, lambda: app.log_message("JARVIS", res["reply"]))
                if "terminal_output" in res:
                    app.after(0, lambda: app.log_terminal(res["terminal_output"]))
            if res and res.get("action") == "exit":
                time.sleep(2)
                if app:
                    app.after(0, app.destroy)
                sys.exit(0)
                
        threading.Thread(target=_process, daemon=True).start()

    def on_listener_status_change(status):
        if app and speaker and not speaker.is_speaking:
            app.after(0, lambda: app.set_status(status))

    listener = Listener(
        on_result=on_listener_result,
        on_status_change=on_listener_status_change,
        speaker_ref=speaker
    )
    brain.listener = listener

    # 5. Initialize Clapper
    clapper = Clapper(speaker_ref=speaker)

    # 6. Initialize GUI
    app = JarvisHUD(
        brain_ref=brain,
        listener_ref=listener,
        speaker_ref=speaker,
        clapper_ref=clapper
    )

    # 7. Initialize Global Hotkey (Ctrl + Alt + J)
    from core.hotkey_manager import GlobalHotkeyManager
    def on_global_hotkey():
        if app:
            try:
                app.after(0, lambda: app.deiconify())
                app.after(0, lambda: app.lift())
                app.after(0, lambda: app.focus_force())
            except Exception:
                pass
        if speaker and speaker.is_speaking:
            speaker.stop_speech()
            return
        if brain:
            if brain.state == "STANDBY":
                brain.state = "AWAKE"
                if on_brain_state_change:
                    on_brain_state_change("AWAKE")
                if speaker:
                    speaker.play_wake_sfx()
            else:
                brain.state = "STANDBY"
                if on_brain_state_change:
                    on_brain_state_change("STANDBY")

    hotkey_mgr = GlobalHotkeyManager(on_hotkey=on_global_hotkey)
    hotkey_mgr.start()

    # 8. Start listening in background
    listener.start()

    # Initial vocal greeting
    def _initial_greeting():
        time.sleep(1.0)
        speaker.speak("Initial checks completed. All systems operational. Jarvis standing by, sir.")
    threading.Thread(target=_initial_greeting, daemon=True).start()

    print("[SUCCESS] J.A.R.V.I.S. HUD loaded. Starting main interface loop...")
    try:
        app.mainloop()
    finally:
        print("[JARVIS] Shutdown initiated. Cleaning up threads...")
        listener.stop()
        clapper.stop()
        if 'hotkey_mgr' in locals() and hotkey_mgr:
            hotkey_mgr.stop()
        print("[JARVIS] Offline.")

if __name__ == "__main__":
    main()
