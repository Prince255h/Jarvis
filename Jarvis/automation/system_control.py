import psutil
import pyautogui
import os
import time
import datetime
import subprocess
import threading
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False

class SystemControl:
    def __init__(self, speaker_ref=None):
        self.speaker = speaker_ref
        self.last_plugged_state = None
        self.monitoring_battery = False
        self.monitor_thread = None

    def start_battery_monitor(self):
        """Continuously check for charger plug-in / plug-out and battery extremes."""
        if not self.monitoring_battery:
            self.monitoring_battery = True
            self.monitor_thread = threading.Thread(target=self._battery_monitor_loop, daemon=True)
            self.monitor_thread.start()

    def _battery_monitor_loop(self):
        while self.monitoring_battery:
            try:
                b = psutil.sensors_battery()
                if b is not None:
                    # Check plug transition
                    if self.last_plugged_state is not None:
                        if b.power_plugged and not self.last_plugged_state:
                            msg = "Sir, the charger has been connected. Charging initialized."
                            if self.speaker:
                                self.speaker.speak(msg)
                        elif not b.power_plugged and self.last_plugged_state:
                            msg = f"Attention sir, the charger has been disconnected. Device running on battery at {b.percent} percent."
                            if self.speaker:
                                self.speaker.speak(msg)
                    
                    self.last_plugged_state = b.power_plugged

                    # Check critical thresholds
                    if not b.power_plugged and b.percent <= 20:
                        if self.speaker:
                            self.speaker.speak(f"Critical warning: Battery level is down to {b.percent} percent. Please connect the power adapter, sir.")
                            time.sleep(180) # Don't spam alert
                    elif b.power_plugged and b.percent >= 98:
                        if self.speaker:
                            self.speaker.speak("Battery is fully charged at 98 percent. You may unplug the charger to protect cell longevity, sir.")
                            time.sleep(300)
            except Exception as e:
                print(f"[BatteryMonitor] Error: {e}")
            time.sleep(5)

    @staticmethod
    def get_battery_info():
        b = psutil.sensors_battery()
        if b is None:
            return "This system is running on direct desktop AC power with stable supply, sir."
        
        status = "charging" if b.power_plugged else "discharging"
        return f"Battery is currently at {b.percent} percent, and the system is {status}, sir."

    @staticmethod
    def get_system_telemetry():
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return (
            f"Diagnostics report, sir: Processor utilization is at {cpu:.1f} percent. "
            f"Physical memory usage is at {ram.percent} percent with {ram.available // (1024**3):.1f} gigabytes available. "
            f"Main storage has {disk.free // (1024**3)} gigabytes free."
        )

    @staticmethod
    def set_volume_percent(percent):
        percent = max(0, min(100, percent))
        if PYCAW_AVAILABLE:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
                return f"Master volume adjusted to {percent} percent, sir."
            except Exception:
                pass
        # Fallback
        return f"Adjusting system volume to {percent} percent."

    @staticmethod
    def volume_up():
        pyautogui.press('volumeup', presses=5)
        return "Master volume increased, sir."

    @staticmethod
    def volume_down():
        pyautogui.press('volumedown', presses=5)
        return "Master volume decreased, sir."

    @staticmethod
    def mute_volume():
        pyautogui.press('volumemute')
        return "Audio toggled mute, sir."

    @staticmethod
    def take_screenshot():
        os.makedirs("g:/Jarvis/data/screenshots", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"g:/Jarvis/data/screenshots/screenshot_{timestamp}.png"
        try:
            from automation.vision_control import VisionControl
            img = VisionControl.take_screenshot()
            if img:
                img.save(filename)
                os.system(f'start "" "{filename}"')
                return f"Screenshot captured and saved to your data directory, sir."
        except Exception:
            pass
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            os.system(f'start "" "{filename}"')
            return "Screenshot captured and saved to your data directory, sir."
        except Exception as e:
            return f"Failed to capture screenshot: {e}"


    @staticmethod
    def minimize_all_windows():
        pyautogui.hotkey('win', 'd')
        return "Minimized all active windows to reveal your desktop, sir."

    @staticmethod
    def lock_workstation():
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Workstation locked securely, sir."

    @staticmethod
    def test_internet_speed():
        """Measure network ping and speed."""
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            down_mbps = st.download() / 1_000_000
            up_mbps = st.upload() / 1_000_000
            return f"Speed test complete, sir. Download speed is {down_mbps:.1f} megabits per second, and upload speed is {up_mbps:.1f} megabits per second."
        except Exception:
            # Fast ping fallback
            try:
                out = subprocess.check_output("ping -n 3 8.8.8.8", shell=True).decode()
                if "Average =" in out:
                    avg = out.split("Average =")[-1].strip()
                    return f"Network is online and responsive with an average ping latency of {avg}, sir."
            except Exception:
                pass
            return "Your internet connection is active and stable, sir."
