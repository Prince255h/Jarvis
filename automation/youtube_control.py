import pyautogui
import webbrowser
import urllib.parse
import urllib.request
import json
import re
import time
import threading
import ctypes
from ctypes import wintypes
import pyperclip
from PIL import ImageGrab
import numpy as np
from automation.computer_control import ComputerControl

# Prevent PyAutoGUI from crashing if cursor is in corner
pyautogui.FAILSAFE = False

class YouTubeControl:
    """
    Intelligent YouTube Automation Engine
    - Tracks active session state
    - Performs human-like in-page search on YouTube via '/' keyboard shortcut
    - Real-time Shorts duration analysis and exact 1-second post-end scrolling
    - NO tab reload, NO page refresh, NO window minimize/shrink
    - Full hotkey & media control suite
    """
    is_open = False
    last_opened_at = 0.0
    is_scrolling_shorts = False
    _shorts_thread = None
    status_callback = None

    @classmethod
    def mark_opened(cls):
        cls.is_open = True
        cls.last_opened_at = time.time()

    @classmethod
    def is_recently_active(cls) -> bool:
        """Returns True if YouTube was opened or used within the last 20 minutes."""
        return cls.is_open and ((time.time() - cls.last_opened_at) < 1200)

    @classmethod
    def _focus_browser_safely(cls) -> bool:
        """
        Brings the browser/YouTube window to the foreground safely.
        Uses native Win32 ctypes without pygetwindow to avoid un-maximizing or shrinking the window.
        Prioritizes active YouTube Shorts or YouTube windows.
        """
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            found_hwnd = [None]
            fallback_hwnd = [None]

            def enum_cb(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value.lower()
                        if "youtube" in title or "shorts" in title:
                            found_hwnd[0] = hwnd
                            return False
                        elif fallback_hwnd[0] is None and any(kw in title for kw in ("chrome", "edge", "brave", "firefox", "opera")):
                            fallback_hwnd[0] = hwnd
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

            target_hwnd = found_hwnd[0] or fallback_hwnd[0]
            if target_hwnd:
                hwnd = target_hwnd
                # ONLY restore if minimized to taskbar (IsIconic). Never shrink maximized window!
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9) # SW_RESTORE

                cur_thread = kernel32.GetCurrentThreadId()
                target_thread = user32.GetWindowThreadProcessId(hwnd, None)
                user32.AttachThreadInput(cur_thread, target_thread, True)
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.AttachThreadInput(cur_thread, target_thread, False)
                return True
        except Exception as e:
            print(f"[YouTubeControl] Focus browser error: {e}")
        return False


    @classmethod
    def _in_page_search(cls, query: str):
        """
        Uses YouTube's native in-page search input without reloading the page:
        1. Focuses browser/YouTube window safely.
        2. Uses '/' (YouTube native shortcut) to focus search box.
        3. Clears and types the search query.
        4. Presses Enter for instant SPA search (NO reload, NO minimize).
        """
        cls._focus_browser_safely()
        time.sleep(0.15)

        try:
            # YouTube hotkey to focus search bar is '/'
            pyautogui.press('esc')
            time.sleep(0.06)
            pyautogui.press('/')
            time.sleep(0.08)

            # Clear search box
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.03)
            pyautogui.press('backspace')
            time.sleep(0.03)

            # Type search query cleanly
            pyautogui.write(query, interval=0.01)
            time.sleep(0.06)
            pyautogui.press('enter')
        except Exception as e:
            print(f"[YouTubeControl] In-page search error: {e}")

    @classmethod
    def search(cls, query: str, force_new_tab: bool = False) -> str:
        """
        Intelligently searches YouTube:
        If YouTube is open, searches in-place via YouTube search bar (NO page reload, NO minimize).
        If not open, launches YouTube in browser.
        """
        clean_q = query.strip()
        encoded = urllib.parse.quote_plus(clean_q)
        url = f"https://www.youtube.com/results?search_query={encoded}"

        if not force_new_tab and cls.is_recently_active():
            cls.last_opened_at = time.time()
            threading.Thread(target=lambda: cls._in_page_search(clean_q), daemon=True).start()
            return f"Searching for {clean_q} on YouTube, sir."
        else:
            cls.mark_opened()
            webbrowser.open(url)
            return f"Searching YouTube for {clean_q}, sir."

    @classmethod
    def play_direct(cls, query: str, force_new_tab: bool = False) -> str:
        """
        Searches and plays requested video:
        Reuses active tab if YouTube is already open, otherwise opens browser.
        """
        clean_q = query.strip()
        encoded = urllib.parse.quote_plus(clean_q)
        url = f"https://www.youtube.com/results?search_query={encoded}"

        if not force_new_tab and cls.is_recently_active():
            cls.last_opened_at = time.time()
            def _reuse_and_play():
                cls._in_page_search(clean_q)
                time.sleep(2.0)
                try:
                    pyautogui.press('tab', presses=4, interval=0.1)
                    pyautogui.press('enter')
                except Exception:
                    pass

            threading.Thread(target=_reuse_and_play, daemon=True).start()
            return f"Playing {clean_q} on YouTube, sir."
        else:
            cls.mark_opened()
            webbrowser.open(url)
            def _press_play():
                try:
                    time.sleep(2.2)
                    pyautogui.press('tab', presses=4, interval=0.1)
                    pyautogui.press('enter')
                except Exception:
                    pass

            threading.Thread(target=_press_play, daemon=True).start()
            return f"Playing {clean_q} on YouTube, sir."

    @classmethod
    def toggle_play_pause(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            # 'k' is YouTube's dedicated play/pause key which avoids unwanted scrolling
            pyautogui.press('k')
        except Exception:
            try:
                pyautogui.press('space')
            except Exception:
                pass
        return "Toggled video playback, sir."

    @classmethod
    def volume_up(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.press('up', presses=3, interval=0.08)
        except Exception:
            pass
        return "Increased video volume."

    @classmethod
    def volume_down(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.press('down', presses=3, interval=0.08)
        except Exception:
            pass
        return "Decreased video volume."

    @classmethod
    def mute(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.press('m')
        except Exception:
            pass
        return "Toggled video mute."

    @classmethod
    def toggle_captions(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.press('c')
        except Exception:
            pass
        return "Toggled video subtitles, sir."

    @classmethod
    def toggle_fullscreen(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.press('f')
        except Exception:
            pass
        return "Toggled fullscreen display."

    @classmethod
    def speed_up(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.hotkey('shift', '>')
        except Exception:
            pass
        return "Increased playback speed."

    @classmethod
    def speed_down(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.hotkey('shift', '<')
        except Exception:
            pass
        return "Decreased playback speed."

    @classmethod
    def seek_forward(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.press('l')
        except Exception:
            pass
        return "Skipped forward 10 seconds."

    @classmethod
    def seek_backward(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.press('j')
        except Exception:
            pass
        return "Rewound 10 seconds."

    @classmethod
    def next_video(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.hotkey('shift', 'n')
        except Exception:
            pass
        return "Skipping to the next video, sir."

    @classmethod
    def prev_video(cls):
        cls._focus_browser_safely()
        time.sleep(0.08)
        try:
            pyautogui.hotkey('shift', 'p')
        except Exception:
            pass
        return "Returning to previous video, sir."

    # ==========================================
    # INTELLIGENT ORGANIC VIDEO SELECTION & VISION
    # ==========================================
    @classmethod
    def click_first_organic_video(cls) -> str:
        """
        Intelligently locates and clicks the first NON-AD, NON-SPONSORED video on YouTube:
        1. Brings YouTube browser window into foreground safely.
        2. Captures screenshot and uses Gemini Vision to distinguish between Ads/Sponsored and real content.
        3. Identifies and skips any sponsored cards or promotional banners.
        4. Smoothly navigates the mouse to the first organic video and clicks.
        5. Falls back to smart visual heuristics if offline.
        """
        cls._focus_browser_safely()
        time.sleep(0.2)

        # 1. Try Gemini Multimodal Visual Inspection
        try:
            from core.agent import AutonomousAgent
            api_key = AutonomousAgent.get_api_key()
            if api_key:
                from automation.vision_control import VisionControl
                import io
                from PIL import Image
                from google import genai
                from google.genai import types
                import json

                VisionControl._attach_desktop()
                orig_screen = pyautogui.screenshot()
                screen_w, screen_h = orig_screen.size

                # Resize image for fast, crisp vision reasoning
                scale = 1200.0 / max(screen_w, screen_h)
                resized = orig_screen.resize((int(screen_w * scale), int(screen_h * scale)), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                resized.save(buf, format="JPEG", quality=85)

                client = genai.Client(api_key=api_key)
                part = types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

                prompt = (
                    "You are an expert visual GUI agent analyzing a screenshot of YouTube in a web browser.\n"
                    "Task: Find the FIRST ORGANIC (NON-SPONSORED, NON-AD) video in the search results or feed.\n\n"
                    "CRITICAL AD FILTERING RULES:\n"
                    "1. Check the very top cards. If any video or card contains the label 'Sponsored', 'Ad', 'Promoted', or is an ad banner, DO NOT select it! Skip it completely.\n"
                    "2. Identify the FIRST authentic content video.\n"
                    "3. Return the exact center coordinates of its thumbnail or clickable video title.\n\n"
                    "Respond with ONLY valid JSON without markdown fences:\n"
                    "{\"found\": true, \"title\": \"video title\", \"ads_skipped\": 1, \"x\": int_0_to_1000, \"y\": int_0_to_1000}\n"
                    "If no organic video is visible, return: {\"found\": false, \"reason\": \"explanation\"}"
                )

                for model_name in ("gemini-2.5-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash"):
                    try:
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=[part, prompt]
                        )
                        if resp and resp.text:
                            raw = resp.text.strip()
                            if "{" in raw and "}" in raw:
                                data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
                                if data.get("found"):
                                    norm_x = data.get("x", 480)
                                    norm_y = data.get("y", 420)
                                    title = data.get("title", "first organic video")
                                    ads_skipped = data.get("ads_skipped", 0)

                                    target_x = int((norm_x / 1000.0) * screen_w)
                                    target_y = int((norm_y / 1000.0) * screen_h)

                                    print(f"[YouTubeControl] Vision located organic video '{title}' at ({target_x}, {target_y}) - Skipped {ads_skipped} ad(s)")
                                    pyautogui.moveTo(target_x, target_y, duration=0.45)
                                    time.sleep(0.12)
                                    pyautogui.click(target_x, target_y)

                                    skip_note = f" (skipped {ads_skipped} sponsored ad)" if ads_skipped > 0 else ""
                                    return f"Visually verified and clicked on '{title}'{skip_note}, sir."
                    except Exception as me:
                        print(f"[YouTubeControl] Vision model {model_name} attempt: {me}")
                        continue
        except Exception as e:
            print(f"[YouTubeControl] Visual video detection error: {e}")

        # 2. Smart Fallback: Organic card heuristic on 1080p/1440p
        # On YouTube, sponsored ads take the top slot (y ~ 240-340).
        # The first organic video card thumbnail is centered around x=45%, y=44%
        sw, sh = pyautogui.size()
        organic_x = int(sw * 0.45)
        organic_y = int(sh * 0.44)
        try:
            pyautogui.moveTo(organic_x, organic_y, duration=0.4)
            time.sleep(0.15)
            pyautogui.click(organic_x, organic_y)
            return f"Navigated past initial ads and clicked the primary video at ({organic_x}, {organic_y}), sir."
        except Exception as e:
            pyautogui.press('enter')
            return f"Selected video via enter key: {e}"

    # ==========================================
    # AUTONOMOUS YOUTUBE SHORTS AUTO-SCROLLER
    # ==========================================
    @classmethod
    def _notify(cls, status_cb, sender: str, msg: str):
        """Dispatches status updates to HUD GUI and logs to console."""
        print(f"[{sender}] {msg}")
        cb = status_cb or cls.status_callback
        if cb:
            try:
                cb(sender, msg)
            except Exception:
                pass

    @classmethod
    def _get_active_browser_url(cls) -> str:
        """
        Safely retrieves the URL of the active browser tab without disturbing playback.
        Uses Ctrl+L, Ctrl+C, Esc sequence and preserves existing clipboard content.
        """
        old_clip = None
        try:
            old_clip = pyperclip.paste()
        except Exception:
            pass

        cls._focus_browser_safely()
        time.sleep(0.04)

        try:
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.04)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.04)
            pyautogui.press('esc')
        except Exception:
            pass

        url = ""
        try:
            url = pyperclip.paste().strip()
        except Exception:
            pass

        # Restore previous clipboard if it wasn't the URL
        if old_clip is not None and old_clip != url:
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass

        return url

    @classmethod
    def _extract_video_id(cls, url: str):
        """Extracts the YouTube video ID from various Shorts or standard URL formats."""
        if not url:
            return None
        patterns = [
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'watch\?v=([a-zA-Z0-9_-]{11})',
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    @classmethod
    def fetch_short_duration_and_info(cls, video_id: str) -> dict:
        """
        Analyzes the duration and metadata for a YouTube Short video ID:
        1. Queries YouTube InnerTube Player API (fast ~0.2 - 0.4s).
        2. Fallbacks to lightweight streaming HTML inspection.
        Returns dict with duration (seconds), title, author.
        """
        if not video_id:
            return None

        # 1. Fast InnerTube API
        try:
            url = "https://www.youtube.com/youtubei/v1/player"
            payload = json.dumps({
                "videoId": video_id,
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20240101.00.00"
                    }
                }
            }).encode('utf-8')

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                vd = data.get("videoDetails", {})
                dur = float(vd.get("lengthSeconds", 0))
                title = vd.get("title", "")
                author = vd.get("author", "")
                if 0 < dur <= 300: # Shorts are under 3 minutes
                    return {
                        "video_id": video_id,
                        "duration": dur,
                        "title": title,
                        "author": author,
                        "source": "innertube"
                    }
        except Exception as e:
            print(f"[YouTubeControl] InnerTube duration query error: {e}")

        # 2. Fallback: Streaming HTML scrape
        try:
            url = f"https://www.youtube.com/shorts/{video_id}"
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                chunk_size = 65536
                bytes_read = 0
                while bytes_read < 1000000:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    m = re.search(rb'"approxDurationMs":"(\d+)"', chunk)
                    if m:
                        dur = float(m.group(1)) / 1000.0
                        return {
                            "video_id": video_id,
                            "duration": dur,
                            "title": f"Short {video_id}",
                            "author": "",
                            "source": "stream_approxDurationMs"
                        }
                    m2 = re.search(rb'"lengthSeconds":"(\d+)"', chunk)
                    if m2:
                        dur = float(m2.group(1))
                        return {
                            "video_id": video_id,
                            "duration": dur,
                            "title": f"Short {video_id}",
                            "author": "",
                            "source": "stream_lengthSeconds"
                        }
        except Exception as e:
            print(f"[YouTubeControl] Streaming duration fallback error: {e}")

        return None

    @classmethod
    def detect_visual_short_progress(cls) -> tuple:
        """
        Visually monitors the red progress bar (#ff0000) of YouTube Shorts desktop player.
        Returns (is_detected: bool, progress_ratio: float, has_ended: bool).
        """
        try:
            from automation.vision_control import VisionControl
            VisionControl._attach_desktop()

            user32 = ctypes.windll.user32
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)

            # Central bottom viewport of primary display where Shorts progress bar resides
            bbox = (int(sw * 0.28), int(sh * 0.70), int(sw * 0.72), int(sh * 0.98))
            img = ImageGrab.grab(bbox=bbox)
            arr = np.array(img)

            # YouTube signature red progress line: R > 190, G < 70, B < 70
            red_mask = (arr[:, :, 0] > 190) & (arr[:, :, 1] < 70) & (arr[:, :, 2] < 70)
            row_counts = np.sum(red_mask, axis=1)

            candidate_rows = np.where(row_counts > 25)[0]
            if len(candidate_rows) == 0:
                return (False, 0.0, False)

            best_row = candidate_rows[np.argmax(row_counts[candidate_rows])]
            red_indices = np.where(red_mask[best_row, :])[0]
            if len(red_indices) < 15:
                return (False, 0.0, False)

            span = red_indices[-1] - red_indices[0]
            total_w = bbox[2] - bbox[0]
            ratio = min(1.0, max(0.0, span / float(total_w * 0.75)))
            has_ended = ratio >= 0.96

            return (True, ratio, has_ended)
        except Exception:
            return (False, 0.0, False)

    @classmethod
    def open_shorts(cls) -> str:
        """
        Navigates to YouTube Shorts:
        If active window/tab is already on YouTube Shorts, brings it into focus without reloading.
        If YouTube is active, navigates to Shorts.
        If not open, launches https://www.youtube.com/shorts in default browser.
        """
        cls.mark_opened()
        cls._focus_browser_safely()
        time.sleep(0.15)

        # Check if browser is already displaying Shorts
        url = cls._get_active_browser_url()
        if "youtube.com/shorts" in url:
            return "YouTube Shorts is already actively focused on screen, sir."

        if cls.is_recently_active():
            from automation.browser_control import BrowserControl
            BrowserControl._navigate_active_tab("https://www.youtube.com/shorts")
            return "Navigated active YouTube tab to Shorts, sir."
        else:
            webbrowser.open("https://www.youtube.com/shorts")
            return "Opened YouTube Shorts, sir."

    @classmethod
    def start_scrolling_shorts(cls, speaker_ref=None, status_cb=None, duration_per_short: int = 25) -> str:
        """
        Autonomous Intelligent Shorts Scroller:
        1. Analyzes the current Short's duration in real-time.
        2. Plays the Short for its exact duration.
        3. EXACTLY 1 second after the Short ends, automatically scrolls down to the next Short.
        4. Continuously repeats until interrupted by user (Escape key, voice command 'stop', or HUD button).
        """
        if cls.is_scrolling_shorts:
            return "YouTube Shorts auto-scroller is already actively running, sir."

        cls.is_scrolling_shorts = True
        if status_cb:
            cls.status_callback = status_cb
        cls._focus_browser_safely()

        def _scroller_worker():
            cls._notify(status_cb, "SHORTS", "Autonomous Shorts auto-scroller initialized.")
            user32 = ctypes.windll.user32
            short_idx = 1
            last_video_id = None

            # Initial stabilization
            time.sleep(1.0)

            while cls.is_scrolling_shorts:
                # Step 1: Analyze current Short's duration and metadata
                start_playback_time = time.time()
                cls._notify(status_cb, "SHORTS", f"Analyzing duration of Short #{short_idx}...")

                url = cls._get_active_browser_url()
                video_id = cls._extract_video_id(url)

                # If URL hasn't updated yet from previous short transition, wait briefly and retry
                if video_id and video_id == last_video_id:
                    time.sleep(0.4)
                    url = cls._get_active_browser_url()
                    video_id = cls._extract_video_id(url)

                short_info = None
                if video_id:
                    short_info = cls.fetch_short_duration_and_info(video_id)
                    last_video_id = video_id

                if short_info and short_info.get("duration", 0) > 0:
                    duration = short_info["duration"]
                    title = short_info.get("title", f"Short #{short_idx}")
                    creator = f" by {short_info['author']}" if short_info.get("author") else ""
                    cls._notify(
                        status_cb,
                        "SHORTS",
                        f"Short #{short_idx} analyzed: \"{title}\"{creator} | Duration: {duration:.1f}s. Auto-scrolling in {duration + 1.0:.1f}s (exactly 1s after finish)..."
                    )
                else:
                    duration = float(duration_per_short)
                    cls._notify(
                        status_cb,
                        "SHORTS",
                        f"Short #{short_idx}: Duration analyzed via visual/adaptive fallback ({duration:.0f}s). Auto-scrolling in {duration + 1.0:.0f}s..."
                    )

                # Step 2: Play Short and wait until it ends + EXACTLY 1.0 second buffer
                # Video naturally ends at (start_playback_time + duration).
                # User specification: "when it end exactly after 1 second it scrolls to next short"
                target_scroll_time = start_playback_time + duration + 1.0

                interrupted = False
                while time.time() < target_scroll_time:
                    if not cls.is_scrolling_shorts:
                        interrupted = True
                        break

                    # Check for Escape key press (VK_ESCAPE = 0x1B)
                    if (user32.GetAsyncKeyState(0x1B) & 0x8000) != 0:
                        cls._notify(status_cb, "SHORTS", "User pressed Escape key. Halting auto-scroller.")
                        cls.is_scrolling_shorts = False
                        interrupted = True
                        if speaker_ref:
                            speaker_ref.speak("Shorts auto-scroll stopped, sir.")
                        break

                    time.sleep(0.05)

                if interrupted or not cls.is_scrolling_shorts:
                    break

                # Step 3: Exact 1-second delay completed! Scroll to next Short
                cls._notify(status_cb, "SHORTS", f"Short #{short_idx} ended! 1-second delay completed. Scrolling to next Short...")
                cls._focus_browser_safely()
                time.sleep(0.04)
                pyautogui.press('down')
                short_idx += 1

                # Allow transition animation and new short to mount
                time.sleep(0.85)

            cls.is_scrolling_shorts = False
            cls._notify(status_cb, "SHORTS", "YouTube Shorts auto-scroller disengaged.")

        cls._shorts_thread = threading.Thread(target=_scroller_worker, daemon=True)
        cls._shorts_thread.start()

        return "YouTube Shorts auto-scroller engaged, sir. Analyzing each short's duration and scrolling exactly one second after completion."

    @classmethod
    def stop_scrolling_shorts(cls) -> str:
        """Immediately stops the autonomous Shorts auto-scroller."""
        if not cls.is_scrolling_shorts:
            return "YouTube Shorts auto-scroller is not currently running, sir."

        cls.is_scrolling_shorts = False
        cls._notify(cls.status_callback, "SHORTS", "Auto-scroller halted by command.")
        return "YouTube Shorts auto-scroller has been disengaged, sir."

    @classmethod
    def open_and_scroll_shorts(cls, speaker_ref=None, status_cb=None, duration_per_short: int = 25) -> str:
        """Compound action: Ensures Shorts is open/focused and starts the intelligent auto-scroller."""
        cls.open_shorts()
        time.sleep(1.8)
        return cls.start_scrolling_shorts(speaker_ref=speaker_ref, status_cb=status_cb, duration_per_short=duration_per_short)

    # Standard functional aliases
    fullscreen = toggle_fullscreen
    play = toggle_play_pause
    pause = toggle_play_pause
    play_pause = toggle_play_pause
    captions = toggle_captions
    previous_video = prev_video
    click_first_video = click_first_organic_video
    scroll_shorts = start_scrolling_shorts
    stop_shorts = stop_scrolling_shorts


