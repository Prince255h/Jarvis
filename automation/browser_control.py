import webbrowser
import urllib.parse
import pyautogui
pyautogui.FAILSAFE = False
import time
import threading
import tkinter as tk
from config import WEB_SHORTCUTS
from automation.computer_control import ComputerControl

class BrowserControl:
    """
    Intelligent Web Navigation Engine
    - Tracks active web service (YouTube, Google, etc.)
    - Reuses active browser tabs during conversational flow
    """
    active_service = None
    last_opened_at = 0.0

    @classmethod
    def open_website(cls, site_name: str) -> str:
        """Open a predefined or requested web address."""
        cleaned = site_name.strip().lower()
        cls.active_service = cleaned
        cls.last_opened_at = time.time()

        # If user opened YouTube, inform YouTubeControl session
        if "youtube" in cleaned:
            from automation.youtube_control import YouTubeControl
            YouTubeControl.mark_opened()

        if cleaned in WEB_SHORTCUTS:
            webbrowser.open(WEB_SHORTCUTS[cleaned])
            return f"Opening {cleaned.capitalize()}, sir."

        # Handle full URL or domain
        if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
            url = f"https://www.{cleaned}.com"
        else:
            url = cleaned
        webbrowser.open(url)
        return f"Opening {cleaned}, sir."

    @classmethod
    def _focus_browser(cls):
        """Focuses browser window safely."""
        from automation.youtube_control import YouTubeControl
        if not YouTubeControl._focus_browser_safely():
            focused = ComputerControl.focus_window("chrome")
            if "Could not find" in focused:
                focused = ComputerControl.focus_window("edge")
            if "Could not find" in focused:
                ComputerControl.focus_window("brave")

    @classmethod
    def _navigate_active_tab(cls, url: str):
        """Focuses browser window and navigates current tab via address bar."""
        cls._focus_browser()
        time.sleep(0.15)
        try:
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.08)
            pyautogui.write(url, interval=0.005)
            time.sleep(0.05)
            pyautogui.press('enter')
        except Exception:
            pass

    @classmethod
    def google_search(cls, query: str, force_new_tab: bool = False) -> str:
        """Perform Google Search in default browser or active tab."""
        encoded = urllib.parse.quote_plus(query.strip())
        url = f"https://www.google.com/search?q={encoded}"

        # If Google was opened in the last 15 minutes, reuse the active tab
        if not force_new_tab and cls.active_service == "google" and (time.time() - cls.last_opened_at < 900):
            cls.last_opened_at = time.time()
            threading.Thread(target=lambda: cls._navigate_active_tab(url), daemon=True).start()
            return f"Searching Google for {query} in your active tab, sir."
        else:
            cls.active_service = "google"
            cls.last_opened_at = time.time()
            webbrowser.open(url)
            return f"Searching Google for {query}, sir."

    @classmethod
    def scroll_down(cls, amount=600):
        cls._focus_browser()
        time.sleep(0.05)
        pyautogui.scroll(-amount)
        pyautogui.press('pagedown')
        return "Scrolling down."

    @classmethod
    def scroll_up(cls, amount=600):
        cls._focus_browser()
        time.sleep(0.05)
        pyautogui.scroll(amount)
        pyautogui.press('pageup')
        return "Scrolling up."

    @classmethod
    def scroll_to_top(cls):
        cls._focus_browser()
        time.sleep(0.05)
        pyautogui.press('home')
        return "Scrolled to top of the page."

    @classmethod
    def scroll_to_bottom(cls):
        cls._focus_browser()
        time.sleep(0.05)
        pyautogui.press('end')
        return "Scrolled to bottom of the page."

    @classmethod
    def new_tab(cls):
        cls._focus_browser()
        time.sleep(0.05)
        pyautogui.hotkey('ctrl', 't')
        return "Opened a new browser tab."

    @classmethod
    def close_tab(cls, target: str = None):
        """
        Closes the active tab in browser or targeted web service (e.g. YouTube).
        Guarantees that the browser window is focused and Jarvis HUD is never targeted.
        """
        import os
        import ctypes
        from ctypes import wintypes
        from automation.youtube_control import YouTubeControl

        t_clean = (target or "").strip().lower()
        if "youtube" in t_clean or (not target and YouTubeControl.is_open):
            YouTubeControl._focus_browser_safely()
            YouTubeControl.is_open = False
            target_name = "YouTube"
        elif t_clean and t_clean not in ("browser", "tab", "active"):
            ComputerControl.focus_window(t_clean)
            target_name = target.capitalize()
        else:
            cls._focus_browser()
            target_name = "browser"

        time.sleep(0.12)

        # Safety verification: ensure foreground window is NOT Jarvis
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            fg_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(fg_pid))
            if fg_pid.value == os.getpid():
                # Foreground is Jarvis HUD! Do not send Ctrl+W or close to Jarvis
                print("[BrowserControl Safety] Jarvis HUD is in foreground. Re-focusing browser.")
                if not YouTubeControl._focus_browser_safely():
                    for b_name in ("chrome", "edge", "brave", "firefox"):
                        if "Could not find" not in ComputerControl.focus_window(b_name):
                            break
                time.sleep(0.1)

        # Re-check foreground
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            fg_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(fg_pid))
            if fg_pid.value == os.getpid():
                return "Could not safely locate the browser tab to close without disturbing Jarvis, sir."

        pyautogui.hotkey('ctrl', 'w')
        return f"Closed active {target_name} tab, sir."

    @classmethod
    def switch_tab(cls):
        cls._focus_browser()
        time.sleep(0.05)
        pyautogui.hotkey('ctrl', 'tab')
        return "Switched to next tab."

    @classmethod
    def reload_page(cls):
        cls._focus_browser()
        time.sleep(0.05)
        pyautogui.hotkey('ctrl', 'r')
        return "Reloading page."

