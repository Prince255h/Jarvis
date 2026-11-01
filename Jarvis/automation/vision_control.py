import io
import os
import sys
import ctypes
from PIL import Image
import pyautogui

class VisionControl:
    """
    STARK INDUSTRIES OS 5.0 // MULTIMODAL REAL-TIME SCREEN PERCEPTION
    Enables Jarvis to visually inspect the host computer's display:
    - Captures desktop screenshot with OpenInputDesktop session attachment
    - Multimodal visual reasoning via Google Gemini Vision
    - Visual element grounding (locating buttons/links/videos on screen)
    - Offline fallback window detection
    """

    @staticmethod
    def _attach_desktop():
        """Attaches current thread to active input desktop to ensure screenshots work in all sessions."""
        try:
            user32 = ctypes.windll.user32
            hDesk = user32.OpenInputDesktop(0, False, 0x01FF)
            if hDesk:
                user32.SetThreadDesktop(hDesk)
        except Exception:
            pass

    @classmethod
    def capture_screen_image(cls, max_dimension: int = 960) -> Image.Image:
        """Captures a screenshot of the primary display and optimizes dimensions for fast transmission."""
        screenshot = None
        try:
            screenshot = pyautogui.screenshot()
        except Exception:
            try:
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
            except Exception:
                screenshot = None

        if not screenshot:
            # Fallback canvas if display is temporarily locked or in headless subshell
            screenshot = Image.new("RGB", (960, 540), color="#080c16")

        w, h = screenshot.size
        if max(w, h) > max_dimension:
            scale = max_dimension / max(w, h)
            screenshot = screenshot.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        return screenshot

    @classmethod
    def capture_screen_bytes(cls, max_dimension: int = 960, quality: int = 70) -> bytes:
        """Captures screen and returns optimized low-token JPEG bytes."""
        img = cls.capture_screen_image(max_dimension=max_dimension)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()

    @classmethod
    def inspect_screen(cls, user_prompt: str = "") -> dict:
        """
        Visually analyzes the user's screen using Gemini Multimodal Vision.
        Answers questions like:
        - "What are you seeing on the screen right now?"
        - "What's on my screen?"
        - "What video is playing?"
        - "Explain this error on screen"
        """
        from core.agent import AutonomousAgent
        api_key = AutonomousAgent.get_api_key()

        # Capture live screen
        try:
            img_bytes = cls.capture_screen_bytes()
        except Exception as e:
            return {
                "success": False,
                "reply": f"I was unable to capture your display, sir: {e}",
                "description": ""
            }

        if api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)
                part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

                query = user_prompt.strip() if user_prompt.strip() else "What is currently visible on my screen?"
                vision_instruction = (
                    "You are J.A.R.V.I.S., Tony Stark's autonomous AI assistant. "
                    "Analyze this live screenshot of the user's computer screen and answer their question with "
                    "sharp intelligence, accuracy, and subtle British wit. Address the user as 'sir'. "
                    "Keep your answer to 2-3 concise, informative sentences. Do not use markdown backticks.\n\n"
                    f"User question: {query}"
                )

                config = types.GenerateContentConfig(
                    max_output_tokens=150,
                    temperature=0.6
                )

                for model_name in ("gemini-2.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-2.5-flash"):
                    try:
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=[part, vision_instruction],
                            config=config
                        )
                        if resp and resp.text:
                            reply_text = resp.text.strip()
                            return {
                                "success": True,
                                "reply": reply_text,
                                "description": reply_text,
                                "model": model_name
                            }
                    except Exception:
                        continue
            except Exception as e:
                print(f"[VisionControl] Gemini vision error: {e}")

        # Offline fallback: enumerate visible windows & active application
        offline_summary = cls.offline_screen_summary()
        return {
            "success": True,
            "reply": f"Based on active desktop telemetry, sir, your screen currently displays: {offline_summary}.",
            "description": offline_summary,
            "model": "offline_telemetry"
        }

    @classmethod
    def locate_element_on_screen(cls, target_description: str) -> tuple:
        """
        Uses Gemini Vision to estimate normalized (x, y) coordinates of a target element on screen.
        Returns (screen_x, screen_y) or None.
        """
        from core.agent import AutonomousAgent
        api_key = AutonomousAgent.get_api_key()
        if not api_key:
            return None

        try:
            cls._attach_desktop()
            orig_screen = pyautogui.screenshot()
            screen_w, screen_h = orig_screen.size

            # Scale for prompt
            w, h = orig_screen.size
            scale = 1000.0 / max(w, h)
            resized = orig_screen.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="JPEG", quality=80)

            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            part = types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

            prompt = (
                f"Analyze this computer screen. Find the exact center coordinates of: '{target_description}'. "
                "Respond in ONLY valid JSON format with normalized integer coordinates between 0 and 1000: "
                "{\"found\": true, \"x\": int_0_to_1000, \"y\": int_0_to_1000}"
            )

            for model_name in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=[part, prompt]
                    )
                    if resp and resp.text:
                        import json
                        raw = resp.text.strip()
                        if "{" in raw and "}" in raw:
                            data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
                            if data.get("found"):
                                norm_x = data.get("x", 500)
                                norm_y = data.get("y", 500)
                                actual_x = int((norm_x / 1000.0) * screen_w)
                                actual_y = int((norm_y / 1000.0) * screen_h)
                                return (actual_x, actual_y)
                except Exception:
                    continue
        except Exception as e:
            print(f"[VisionControl] Coordinate localization failed: {e}")
        return None

    @classmethod
    def offline_screen_summary(cls) -> str:
        """Inspects foreground and visible window titles via Win32 user32."""
        try:
            user32 = ctypes.windll.user32
            # Get foreground window
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            fg_title = buff.value.strip()

            if fg_title:
                return f"Active window: '{fg_title}'"
            return "Windows Desktop and taskbar"
        except Exception:
            return "Active Windows workspace"
