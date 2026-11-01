import os
import subprocess
import psutil
from config import APP_PATHS

class AppControl:
    @staticmethod
    def launch_app(app_name):
        cleaned = app_name.strip().lower()
        # Direct lookup
        target_exec = APP_PATHS.get(cleaned)
        
        if not target_exec:
            # Partial match
            for name, exe in APP_PATHS.items():
                if name in cleaned or cleaned in name:
                    target_exec = exe
                    break

        if target_exec:
            try:
                subprocess.Popen(target_exec, shell=True)
                return f"Launching {app_name}, sir."
            except Exception as e:
                return f"Attempted to open {app_name}, but encountered: {e}"
        else:
            # Try launching by raw name via Windows start
            try:
                subprocess.Popen(f"start {cleaned}", shell=True)
                return f"Opening {cleaned}, sir."
            except Exception as e:
                return f"I could not locate an application named {app_name}, sir."

    @staticmethod
    def close_app(app_name):
        cleaned = app_name.strip().lower()
        if cleaned in ("jarvis", "self", "hud", "jarvis hud", "core"):
            return "Jarvis self-protection engaged: I cannot terminate myself, sir."

        # If user asked to close a tab or web service (e.g. "youtube tab", "youtube", "browser tab", "tab")
        if "tab" in cleaned or cleaned in ("youtube", "google", "netflix", "spotify web", "twitter", "reddit"):
            from automation.browser_control import BrowserControl
            target_site = "youtube" if "youtube" in cleaned else cleaned
            return BrowserControl.close_tab(target=target_site)

        target_proc = cleaned.replace(" ", "")
        if not target_proc.endswith(".exe"):
            target_proc += ".exe"

        # Check mapped executable name in APP_PATHS (e.g., edge -> msedge.exe, vs code -> code.exe, calc -> calc.exe)
        mapped_exe = APP_PATHS.get(cleaned)
        if not mapped_exe:
            for name, exe in APP_PATHS.items():
                if name in cleaned or cleaned in name:
                    mapped_exe = exe
                    break
        mapped_exe = mapped_exe.lower() if mapped_exe else ""

        my_pid = os.getpid()
        killed = False
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                # NEVER kill current Jarvis process
                if proc.info['pid'] == my_pid:
                    continue
                pname = proc.info['name'].lower()
                if (cleaned in pname or 
                    target_proc in pname or 
                    (mapped_exe and mapped_exe in pname)):
                    proc.terminate()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if killed:
            return f"Terminated {app_name} successfully, sir."
        else:
            return f"I could not find an active process for {app_name}, sir."

