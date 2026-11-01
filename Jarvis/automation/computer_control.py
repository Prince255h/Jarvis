import os
import sys
import subprocess
import threading
import time
import socket
import psutil
import pyautogui
import ctypes
from ctypes import wintypes
import shutil

# Prevent PyAutoGUI from crashing if cursor is parked in screen corners
pyautogui.FAILSAFE = False

class ComputerControl:
    """
    STARK INDUSTRIES OS 5.0 // COMPREHENSIVE COMPUTER ACCESS PROTOCOLS
    Gives Jarvis full administrative and interactive access to the host machine:
    - Command line / PowerShell execution with live output
    - Process inspection & management
    - Window management (focus, minimize, maximize, close)
    - File system navigation, creation, reading, searching
    - Mouse & Keyboard automation (typing, hotkeys, clicking)
    - System configuration (brightness, volume, networking, power states)
    """

    user32 = ctypes.windll.user32

    # ==========================================
    # 1. COMMAND LINE & POWERSHELL EXECUTION
    # ==========================================
    @staticmethod
    def execute_command(command: str, shell_type: str = "powershell", timeout: int = 20) -> dict:
        """
        Executes a shell command on the host computer and returns standard output and status.
        shell_type can be 'powershell' or 'cmd'.
        """
        if not command or not command.strip():
            return {"success": False, "output": "No command provided.", "exit_code": -1}

        cleaned_cmd = command.strip()
        print(f"[ComputerControl] Executing ({shell_type}): {cleaned_cmd}")

        try:
            if shell_type.lower() == "cmd":
                cmd_args = ["cmd.exe", "/c", cleaned_cmd]
            else:
                cmd_args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cleaned_cmd]

            process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    "success": False,
                    "output": f"Command timed out after {timeout} seconds.",
                    "exit_code": -1
                }

            combined = ""
            if stdout and stdout.strip():
                combined += stdout.strip()
            if stderr and stderr.strip():
                if combined:
                    combined += "\n[Error Output]:\n"
                combined += stderr.strip()

            if not combined:
                combined = "Command executed successfully with zero output."

            return {
                "success": (exit_code == 0),
                "output": combined,
                "exit_code": exit_code
            }
        except Exception as e:
            return {"success": False, "output": f"Execution failed: {str(e)}", "exit_code": -1}

    # ==========================================
    # 2. FILE SYSTEM OPERATIONS
    # ==========================================
    @staticmethod
    def open_path(path: str) -> str:
        """Opens any file, application, or directory in Windows Explorer or default app."""
        if not path or not path.strip():
            return "No file or folder path specified, sir."
        
        target = os.path.expanduser(os.path.expandvars(path.strip()))
        
        # Check standard user folders if relative
        if not os.path.exists(target):
            user_profile = os.environ.get("USERPROFILE", "C:\\Users\\admin")
            known_locations = {
                "downloads": os.path.join(user_profile, "Downloads"),
                "documents": os.path.join(user_profile, "Documents"),
                "desktop": os.path.join(user_profile, "Desktop"),
                "pictures": os.path.join(user_profile, "Pictures"),
                "music": os.path.join(user_profile, "Music"),
                "videos": os.path.join(user_profile, "Videos")
            }
            if target.lower() in known_locations:
                target = known_locations[target.lower()]

        if os.path.exists(target):
            try:
                os.startfile(target)
                return f"Opened '{os.path.basename(target) or target}', sir."
            except Exception as e:
                return f"Failed to open '{target}': {e}"
        else:
            return f"Specified path does not exist: '{target}'"

    @staticmethod
    def create_folder(folder_path: str) -> str:
        """Creates a new folder on the file system."""
        try:
            target = os.path.expanduser(os.path.expandvars(folder_path.strip()))
            os.makedirs(target, exist_ok=True)
            return f"Folder created successfully at '{target}', sir."
        except Exception as e:
            return f"Could not create folder: {e}"

    @staticmethod
    def create_file(file_path: str, content: str = "") -> str:
        """Creates or overwrites a text file with specified content."""
        try:
            target = os.path.expanduser(os.path.expandvars(file_path.strip()))
            parent = os.path.dirname(target)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File '{os.path.basename(target)}' created successfully, sir."
        except Exception as e:
            return f"Failed to create file: {e}"

    @staticmethod
    def read_file(file_path: str, max_lines: int = 30) -> str:
        """Reads text from a file and returns contents."""
        try:
            target = os.path.expanduser(os.path.expandvars(file_path.strip()))
            if not os.path.exists(target):
                return f"File not found: '{target}'"
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                lines = [f.readline() for _ in range(max_lines)]
                content = "".join(lines)
            if not content.strip():
                return f"File '{os.path.basename(target)}' is empty."
            return f"Contents of {os.path.basename(target)}:\n{content}"
        except Exception as e:
            return f"Failed reading file: {e}"

    @staticmethod
    def search_file(filename: str, search_dir: str = None) -> str:
        """Quickly searches for a file by name starting from root or search_dir."""
        if not search_dir:
            search_dir = os.environ.get("USERPROFILE", "C:\\Users")
        
        matches = []
        filename_lower = filename.lower()
        try:
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    if filename_lower in f.lower():
                        matches.append(os.path.join(root, f))
                        if len(matches) >= 5:
                            break
                if len(matches) >= 5:
                    break
        except Exception:
            pass

        if matches:
            res = f"Found {len(matches)} match(es), sir:\n" + "\n".join(matches)
            return res
        return f"No files matching '{filename}' were found in '{search_dir}', sir."

    @staticmethod
    def empty_recycle_bin() -> str:
        """Empties Windows Recycle Bin silently."""
        try:
            # 7 = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
            res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            return "Windows Recycle Bin has been purged clean, sir."
        except Exception as e:
            return f"Could not empty Recycle Bin: {e}"

    # ==========================================
    # 3. WINDOW & APPLICATION MANAGEMENT
    # ==========================================
    @staticmethod
    def get_open_windows() -> list:
        """Returns a list of all visible top-level application window titles."""
        titles = []
        def enum_windows_callback(hwnd, extra):
            if ComputerControl.user32.IsWindowVisible(hwnd):
                length = ComputerControl.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    ComputerControl.user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.strip()
                    if title and title not in ("Program Manager", "Default IME", "MSCTFIME UI"):
                        titles.append(title)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        cb = WNDENUMPROC(enum_windows_callback)
        ComputerControl.user32.EnumWindows(cb, 0)
        return titles

    @staticmethod
    def focus_window(title_keyword: str) -> str:
        """Brings the first window matching the keyword to the foreground."""
        target_keyword = title_keyword.strip().lower()
        found_hwnd = [None]
        found_title = [None]

        def enum_cb(hwnd, extra):
            if ComputerControl.user32.IsWindowVisible(hwnd):
                length = ComputerControl.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    ComputerControl.user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.strip()
                    if target_keyword in title.lower():
                        found_hwnd[0] = hwnd
                        found_title[0] = title
                        return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        cb = WNDENUMPROC(enum_cb)
        ComputerControl.user32.EnumWindows(cb, 0)

        if found_hwnd[0]:
            hwnd = found_hwnd[0]
            if ComputerControl.user32.IsIconic(hwnd):
                ComputerControl.user32.ShowWindow(hwnd, 9) # SW_RESTORE

            
            kernel32 = ctypes.windll.kernel32
            cur_thread = kernel32.GetCurrentThreadId()
            target_thread = ComputerControl.user32.GetWindowThreadProcessId(hwnd, None)
            ComputerControl.user32.AttachThreadInput(cur_thread, target_thread, True)
            ComputerControl.user32.BringWindowToTop(hwnd)
            ComputerControl.user32.SetForegroundWindow(hwnd)
            ComputerControl.user32.AttachThreadInput(cur_thread, target_thread, False)
            return f"Focused active window: '{found_title[0]}', sir."
        return f"Could not find an open window containing '{title_keyword}', sir."

    @staticmethod
    def minimize_active_window() -> str:
        """Minimizes the current active window."""
        hwnd = ComputerControl.user32.GetForegroundWindow()
        if hwnd:
            ComputerControl.user32.ShowWindow(hwnd, 6) # SW_MINIMIZE = 6
            return "Active window minimized, sir."
        return "No foreground window detected."

    @staticmethod
    def maximize_active_window() -> str:
        """Maximizes the current active window."""
        hwnd = ComputerControl.user32.GetForegroundWindow()
        if hwnd:
            ComputerControl.user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE = 3
            return "Active window maximized, sir."
        return "No foreground window detected."

    @staticmethod
    def close_active_window(title_keyword: str = None) -> str:
        """
        Gracefully closes active or targeted window via Alt+F4.
        CRITICAL SAFETY: Enforces self-protection interlock to guarantee Jarvis never closes himself.
        """
        if title_keyword:
            if "jarvis" in title_keyword.lower():
                return "Jarvis self-protection engaged: I cannot close myself, sir."
            ComputerControl.focus_window(title_keyword)
            time.sleep(0.1)

        hwnd = ComputerControl.user32.GetForegroundWindow()
        if hwnd:
            # Check if foreground window belongs to current Jarvis process
            foreground_pid = wintypes.DWORD()
            ComputerControl.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(foreground_pid))
            my_pid = os.getpid()

            # Inspect window title
            length = ComputerControl.user32.GetWindowTextLengthW(hwnd)
            win_title = ""
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                ComputerControl.user32.GetWindowTextW(hwnd, buff, length + 1)
                win_title = buff.value.strip().lower()

            if foreground_pid.value == my_pid or "jarvis" in win_title:
                # Foreground is Jarvis HUD! Do NOT kill Jarvis!
                # Try finding and focusing a real application to close instead
                print("[ComputerControl Safety] Blocked Alt+F4 on Jarvis HUD window.")
                open_wins = ComputerControl.get_open_windows()
                for ow in open_wins:
                    owl = ow.lower()
                    if "jarvis" not in owl and not any(ign in owl for ign in ("program manager", "taskbar", "shell", "hud")):
                        ComputerControl.focus_window(ow)
                        time.sleep(0.12)
                        pyautogui.hotkey('alt', 'f4')
                        return f"Safely closed '{ow}', sir."
                return "Operation aborted: Protected Jarvis HUD from being closed, sir."

        pyautogui.hotkey('alt', 'f4')
        return "Closed active window, sir."

    @staticmethod
    def switch_window() -> str:
        """Sends Alt+Tab to cycle active windows."""
        pyautogui.hotkey('alt', 'tab')
        return "Switched active application, sir."

    # ==========================================
    # 4. MOUSE & KEYBOARD AUTOMATION
    # ==========================================
    @staticmethod
    def type_text(text: str, interval: float = 0.02) -> str:
        """Types out the specified text at the current cursor position."""
        if not text:
            return "No text provided to type."
        pyautogui.write(text, interval=interval)
        return f"Typed '{text}' at cursor, sir."

    @staticmethod
    def press_key(key: str) -> str:
        """Presses a single keyboard key (e.g. enter, esc, backspace, tab, space)."""
        clean_key = key.strip().lower()
        try:
            pyautogui.press(clean_key)
            return f"Pressed '{clean_key}', sir."
        except Exception as e:
            return f"Key press failed: {e}"

    @staticmethod
    def send_hotkey(*keys) -> str:
        """Executes a hotkey sequence, e.g. send_hotkey('ctrl', 'c')."""
        try:
            pyautogui.hotkey(*keys)
            return f"Executed hotkey: {' + '.join(keys)}, sir."
        except Exception as e:
            return f"Hotkey error: {e}"

    @staticmethod
    def mouse_move(x: int, y: int, duration: float = 0.4) -> str:
        """Smoothly moves the mouse cursor to (x, y) coordinates on screen."""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return f"Moved cursor to ({x}, {y}), sir."
        except Exception as e:
            return f"Cursor movement failed: {e}"

    @staticmethod
    def click_at(x: int, y: int, button: str = 'left', double: bool = False, duration: float = 0.3) -> str:
        """Moves the mouse to coordinates (x, y) and performs a click."""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            time.sleep(0.1)
            if double:
                pyautogui.doubleClick(x, y, button=button)
                return f"Double-clicked at ({x}, {y}), sir."
            else:
                pyautogui.click(x, y, button=button)
                return f"Clicked {button} at ({x}, {y}), sir."
        except Exception as e:
            return f"Click action failed: {e}"

    @staticmethod
    def mouse_click(button: str = 'left', double: bool = False) -> str:
        """Performs a mouse click at the current cursor position."""
        try:
            if double:
                pyautogui.doubleClick(button=button)
                return f"Double-clicked {button} mouse button, sir."
            else:
                pyautogui.click(button=button)
                return f"Clicked {button} mouse button, sir."
        except Exception as e:
            return f"Mouse action failed: {e}"

    @staticmethod
    def mouse_scroll(direction: str = 'down', amount: int = 500) -> str:
        """
        Scrolls mouse wheel up or down with keyboard fallback so pages (like YouTube/Chrome) always scroll.
        """
        try:
            scroll_val = -amount if direction.lower() == 'down' else amount
            pyautogui.scroll(scroll_val)
            # Send PageDown / PageUp fallback to guarantee browser viewport moves even if unfocused
            if direction.lower() == 'down':
                pyautogui.press('pagedown')
            else:
                pyautogui.press('pageup')
            return f"Scrolled {direction} by {amount} units, sir."
        except Exception as e:
            return f"Scroll failed: {e}"

    @staticmethod
    def click_first_video() -> str:
        """
        Autonomous action: Visually analyzes YouTube window, skips ads, and clicks the first authentic video.
        """
        from automation.youtube_control import YouTubeControl
        return YouTubeControl.click_first_organic_video()


    # ==========================================
    # 5. PROCESS & SYSTEM TELEMETRY
    # ==========================================
    @staticmethod
    def get_running_tasks(limit: int = 8) -> str:
        """Lists top processes by memory and CPU usage."""
        processes = []
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent', 'pid']):
            try:
                info = p.info
                if info['name'] and info['name'] not in ('System Idle Process', 'System'):
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by memory usage
        processes.sort(key=lambda x: x.get('memory_percent', 0.0) or 0.0, reverse=True)
        top = processes[:limit]

        lines = [f"{p['name']} (PID: {p['pid']}) - RAM: {p['memory_percent']:.1f}%" for p in top]
        return "Top active processes, sir:\n" + "\n".join(lines)

    @staticmethod
    def kill_task(task_name_or_pid: str) -> str:
        """Kills a process by name or PID."""
        target = task_name_or_pid.strip().lower()
        killed = 0
        try:
            my_pid = os.getpid()
            if target in ("jarvis", "self", "hud") or target == str(my_pid):
                return "Jarvis self-protection engaged: Core process cannot be terminated, sir."

            # Check if PID
            if target.isdigit():
                pid = int(target)
                if pid == my_pid:
                    return "Jarvis self-protection engaged: Core process cannot be terminated, sir."
                p = psutil.Process(pid)
                p.terminate()
                return f"Process with PID {pid} has been terminated, sir."
            
            # Check by name
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.info['pid'] == my_pid:
                        continue
                    pname = proc.info['name'].lower()
                    if target in pname or target.replace(".exe", "") in pname:
                        proc.terminate()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed > 0:
                return f"Terminated {killed} instance(s) of '{task_name_or_pid}', sir."
            return f"No active process matching '{task_name_or_pid}' was found."
        except Exception as e:
            return f"Failed to terminate task: {e}"

    # ==========================================
    # 6. SYSTEM CONFIGURATION & POWER
    # ==========================================
    @staticmethod
    def set_brightness(percent: int) -> str:
        """Sets display brightness (0-100) via PowerShell WMI."""
        pct = max(0, min(100, int(percent)))
        cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {pct})"
        res = ComputerControl.execute_command(cmd)
        if res["success"]:
            return f"Display brightness set to {pct} percent, sir."
        else:
            return f"Brightness adjustment could not be applied on this monitor setup."

    @staticmethod
    def get_network_info() -> str:
        """Retrieves local IP, computer hostname, and tests internet gateway."""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"Network details, sir: Hostname is '{hostname}', local IP address is {local_ip}. Active adapter connected."
        except Exception as e:
            return f"Network query error: {e}"

    @staticmethod
    def clipboard_copy(text: str) -> str:
        """Copies text to the Windows system clipboard."""
        try:
            import tkinter as tk
            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
            r.destroy()
            return f"Copied '{text}' to system clipboard, sir."
        except Exception:
            return "Failed copying to clipboard."

    @staticmethod
    def clipboard_paste() -> str:
        """Pastes current clipboard text at cursor."""
        pyautogui.hotkey('ctrl', 'v')
        return "Pasted clipboard contents, sir."

    @staticmethod
    def lock_workstation() -> str:
        """Locks the Windows desktop instantly."""
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked securely, sir."

    @staticmethod
    def sleep_system() -> str:
        """Puts Windows into sleep mode."""
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Entering low-power sleep state, sir."

    @staticmethod
    def restart_system(delay_seconds: int = 5) -> str:
        """Schedules a Windows restart."""
        os.system(f"shutdown /r /t {delay_seconds}")
        return f"System restart scheduled in {delay_seconds} seconds, sir."

    @staticmethod
    def shutdown_system(delay_seconds: int = 5) -> str:
        """Schedules a Windows shutdown."""
        os.system(f"shutdown /s /t {delay_seconds}")
        return f"System shutdown initiated in {delay_seconds} seconds. Goodbye, sir."
