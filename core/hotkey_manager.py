import ctypes
from ctypes import wintypes
import threading
import time

class GlobalHotkeyManager:
    """
    STARK INDUSTRIES OS 5.0 // GLOBAL SYSTEM HOTKEY SUMMON INTERLOCK
    Registers OS-level global hotkeys via Win32 RegisterHotKey:
    - Default Hotkey: Ctrl + Alt + J (or Win + J)
    - Works universally across all Windows apps, full-screen games, and browser sessions
    - Non-blocking Win32 message pump thread
    - Action: Instantly summons Jarvis to the foreground & toggles wake/sleep state
    """
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    MOD_NOREPEAT = 0x4000

    WM_HOTKEY = 0x0312

    def __init__(self, on_hotkey=None):
        self.on_hotkey = on_hotkey
        self.is_running = False
        self.thread = None
        self.hotkey_id = 101
        self.user32 = ctypes.windll.user32

    def start(self, vk=0x4A, modifiers=MOD_CONTROL | MOD_ALT):  # 0x4A is 'J'
        """Starts the background hotkey listener thread."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._msg_loop, args=(vk, modifiers), daemon=True)
            self.thread.start()

    def stop(self):
        """Stops the hotkey listener and unregisters the hook."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            # Post a quit message to break GetMessageW
            self.user32.PostQuitMessage(0)

    def _msg_loop(self, vk, modifiers):
        # Register HotKey on this thread
        flags = modifiers | self.MOD_NOREPEAT
        success = self.user32.RegisterHotKey(None, self.hotkey_id, flags, vk)
        if not success:
            # Try without MOD_NOREPEAT if unsupported on older OS
            success = self.user32.RegisterHotKey(None, self.hotkey_id, modifiers, vk)
            
        if success:
            print("[GlobalHotkeyManager] Global hotkey registered: Ctrl + Alt + J (Summon Jarvis)")
        else:
            print("[GlobalHotkeyManager] Warning: Could not register Ctrl + Alt + J (might be bound by another app)")

        msg = wintypes.MSG()
        while self.is_running:
            res = self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break
            if msg.message == self.WM_HOTKEY and msg.wParam == self.hotkey_id:
                print("[GlobalHotkeyManager] Hotkey triggered!")
                if self.on_hotkey:
                    try:
                        self.on_hotkey()
                    except Exception as e:
                        print(f"[GlobalHotkeyManager] Callback error: {e}")
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))

        self.user32.UnregisterHotKey(None, self.hotkey_id)
        print("[GlobalHotkeyManager] Hotkey unregistered.")
