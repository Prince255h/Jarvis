import os
import sys
import re
import json
import random
import time
import urllib.request
import urllib.parse
from config import WAKE_WORDS, SLEEP_WORDS, EXIT_WORDS, DIALOGS_FILE, GEMINI_API_KEY, LANGUAGE_VOICES, STT_LANGUAGES
from automation.youtube_control import YouTubeControl
from automation.browser_control import BrowserControl
from automation.system_control import SystemControl
from automation.app_control import AppControl
from automation.computer_control import ComputerControl
from automation.live_intel import LiveIntel
from core.agent import AutonomousAgent
from core.translator import TranslatorEngine

class Brain:
    """
    STARK INDUSTRIES OS 5.0 INTENT ROUTER & NEURAL REASONING ENGINE
    Orchestrates:
    - Iron Man voice dialogue & personality
    - Direct Computer Access & OS Shell execution
    - Process, Window, and Hardware controls
    - Browser & YouTube automation
    - Live Intel & Gemini AI fallback
    """
    def __init__(self, speaker_ref=None, on_state_change=None, listener_ref=None):
        self.speaker = speaker_ref
        self.listener = listener_ref
        self.on_state_change = on_state_change
        self.state = "STANDBY"  # "STANDBY" or "AWAKE"
        self.context = {"service": None, "timestamp": 0.0}
        self.dialogs = self._load_dialogs()
        self.system = SystemControl(speaker_ref=self.speaker)
        self.system.start_battery_monitor()

    def _load_dialogs(self):
        try:
            with open(DIALOGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"greetings": ["At your service, sir."], "easter_eggs": {}}

    def get_proactive_greeting(self) -> str:
        """
        Proactive human-like greeting when Jarvis boots or detects user presence (as seen in video).
        Combines current time, sharp ready state, and long-term memory topics.
        """
        from datetime import datetime
        from core.memory import MemoryManager
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        
        data = MemoryManager.load_data()
        recent_topics = data.get("recent_topics", [])
        
        options = [
            f"Hey, I was right here, sir. See, it's {time_str}, and I am completely ready and sharp. You tell me, how are things?",
            f"Good to see you, sir. All neural and desktop systems are online at {time_str}. Tell me, what's the plan for today?",
            f"See, it's {time_str}, and I am completely online and sharp. Tell me, what should we build or watch today?"
        ]
        if recent_topics:
            last_t = recent_topics[-1]
            options.append(f"Hey, I was right here, sir. Clock shows {time_str}. By the way, are we still discussing the {last_t}, or do you have new tasks for me?")
        
        return random.choice(options)

    def process(self, query):
        if not query or not query.strip():
            return None

        raw_query = query.strip()
        text = raw_query.lower()
        print(f"[Brain Processing]: '{raw_query}' (State: {self.state})")

        # 1. Direct Shell Prefix check (e.g. "> dir" or "cmd: ipconfig" or "powershell: Get-Process")
        # Direct shell commands execute immediately even in Standby if typed
        if raw_query.startswith(">") or text.startswith("powershell:") or text.startswith("cmd:"):
            return self._handle_direct_shell(raw_query)

        # 2. Check Exit / Shutdown
        if any(w in text for w in EXIT_WORDS):
            reply = "Powering down Jarvis systems. Goodbye, sir."
            self._respond(reply)
            return {"action": "exit", "reply": reply}

        # 3. Check Wake / Sleep State Switching
        if self.state == "STANDBY":
            if any(w in text for w in WAKE_WORDS):
                self.state = "AWAKE"
                if self.on_state_change:
                    self.on_state_change(self.state)
                if self.speaker:
                    self.speaker.play_wake_sfx()
                reply = random.choice(self.dialogs.get("wake_up", ["I am online and listening, sir."]))
                self._respond(reply)
                return {"action": "wake", "reply": reply}
            else:
                # Standby ignores ordinary speech
                return None

        # When AWAKE, check if user said to sleep
        if any(w in text for w in SLEEP_WORDS):
            self.state = "STANDBY"
            if self.on_state_change:
                self.on_state_change(self.state)
            reply = random.choice(self.dialogs.get("sleep", ["Entering standby mode, sir."]))
            self._respond(reply)
            return {"action": "sleep", "reply": reply}

        # Check instant speech silence / interrupt
        silence_triggers = (
            "stop talking", "be quiet", "shut up", "silence jarvis", "silence",
            "stop speaking", "hush jarvis", "that's enough jarvis", "that's enough",
            "chup ho jao", "shaant ho jao", "bas karo"
        )
        if any(trig in text for trig in silence_triggers):
            if self.speaker:
                self.speaker.stop_speech()
            reply = "Understood, sir. Standing by silently."
            return {"action": "silence", "reply": reply}

        # Play quick ack sound on valid command
        if self.speaker:
            self.speaker.play_ack_sfx()

        # Check Gemini API Key Configuration Commands (or raw key pasted)
        raw_key_match = re.search(r"\b((?:AIzaSy|AQ\.)[A-Za-z0-9_-]{30,55})\b", raw_query)
        if raw_key_match:
            res = self._set_gemini_api_key(raw_key_match.group(1).strip())
            if isinstance(res, dict):
                self._respond(res.get("reply", ""))
            return res

        if any(text.startswith(p) for p in ("set api key ", "set gemini key ", "gemini api key ", "gemini key ", "api key ")):
            for p in ("set api key ", "set gemini key ", "gemini api key ", "gemini key ", "api key "):
                if text.startswith(p):
                    key_val = raw_query[len(p):].strip()
                    res = self._set_gemini_api_key(key_val)
                    if isinstance(res, dict):
                        self._respond(res.get("reply", ""))
                    return res

        # ==============================================================
        # 3.4. DYNAMIC LISTENING LANGUAGE SWITCHING
        # ==============================================================
        lang_switch_m = (
            re.search(r"(?:switch|change|set)\s+(?:listening\s+)?language\s+(?:to|in)\s+([a-zA-Z]+)", text) or
            re.search(r"listen\s+in\s+([a-zA-Z]+)", text)
        )
        if lang_switch_m:
            target_lang_word = lang_switch_m.group(1).strip().lower()
            if self.listener:
                active_code = self.listener.set_language(target_lang_word)
                lang_display = TranslatorEngine.get_lang_name(active_code.split("-")[0])
                reply = f"Acoustic sensor updated, sir. Now listening in {lang_display} ({active_code})."
                self._respond(reply)
                return {
                    "action": "language_changed",
                    "reply": reply,
                    "terminal_output": f"[ACOUSTIC SENSOR] Listening language set to: {lang_display} [{active_code}]\n"
                }

        # ==============================================================
        # 3.5. UNIVERSAL NEURAL TRANSLATOR & INTERPRETER INTERCEPT
        # ==============================================================
        trans_res = TranslatorEngine.handle_intent(raw_query)
        if trans_res:
            reply_text = trans_res.get("reply", "")
            target_code = trans_res.get("target_lang", "en")
            voice_to_use = LANGUAGE_VOICES.get(target_code)
            if self.speaker and reply_text:
                self.speaker.speak(reply_text, voice=voice_to_use)
            return trans_res

        # ==============================================================
        # 4. PRIMARY AI NEURAL CORTEX (Google Gemini 2.5 Flash)
        # When Gemini is connected, Gemini is the PRIMARY BRAIN for EVERYTHING!
        # Handles all conversation, reasoning, common sense, and autonomous actions.
        # ==============================================================
        ai_res = AutonomousAgent.process_with_ai_brain(raw_query)
        if ai_res:
            self._respond(ai_res["reply"])
            return ai_res

        # ==============================================================
        # 5. OFFLINE FALLBACK: Multi-Step & Compound Actions
        # Runs when offline / without Gemini key so PC actions still work
        # ==============================================================
        cleaned_instruction = AutonomousAgent.clean_instruction(raw_query)
        offline_plan = AutonomousAgent._offline_semantic_planner(cleaned_instruction)
        if offline_plan:
            agent_res = AutonomousAgent.run_plan(offline_plan, raw_query)
            if agent_res:
                self._respond(agent_res["reply"])
                return agent_res

        # ==============================================================
        # 6. OFFLINE FALLBACK: Fast Local Computer Shortcuts
        # ==============================================================
        res = self._route_intent(text, raw_query)
        if res:
            if isinstance(res, dict):
                reply = res.get("reply", "")
                if reply:
                    self._respond(reply)
                return res
            else:
                self._respond(res)
                return {"action": "execute", "reply": res}

        # ==============================================================
        # 7. OFFLINE FALLBACK: Conversational & Knowledge Engine
        # ==============================================================
        reply = self._query_ai_or_web(text)
        self._respond(reply)
        return {"action": "ai_query", "reply": reply}

    def _respond(self, reply_text):
        if self.speaker:
            self.speaker.speak(reply_text)

    def _handle_direct_shell(self, raw_cmd):
        """Executes direct shell command lines."""
        if raw_cmd.startswith(">"):
            cmd = raw_cmd[1:].strip()
            shell_type = "powershell"
        elif raw_cmd.lower().startswith("cmd:"):
            cmd = raw_cmd[4:].strip()
            shell_type = "cmd"
        else:
            cmd = raw_cmd[11:].strip()
            shell_type = "powershell"

        exec_res = ComputerControl.execute_command(cmd, shell_type=shell_type)
        output = exec_res["output"]
        vocal_summary = "Command executed successfully, sir." if exec_res["success"] else "Command finished with an alert, sir."
        self._respond(vocal_summary)
        return {
            "action": "shell",
            "reply": vocal_summary,
            "terminal_output": f"[{shell_type.upper()}] > {cmd}\n{output}\n"
        }

    def _set_gemini_api_key(self, api_key: str):
        """Saves and validates the Gemini API key in .env and runtime memory."""
        cleaned_key = api_key.strip().strip("'\"")
        if not cleaned_key or len(cleaned_key) < 15:
            reply = "The provided Gemini API key appears invalid or incomplete, sir."
            return {"action": "gemini_error", "reply": reply, "terminal_output": f"[ALERT] {reply}\n"}

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, ".env")
        try:
            env_lines = []
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    env_lines = f.readlines()

            new_lines = []
            found = False
            for line in env_lines:
                if line.strip().startswith("GEMINI_API_KEY="):
                    new_lines.append(f"GEMINI_API_KEY={cleaned_key}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"GEMINI_API_KEY={cleaned_key}\n")

            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            # Update in-memory configuration
            os.environ["GEMINI_API_KEY"] = cleaned_key
            import config
            config.GEMINI_API_KEY = cleaned_key
            import core.brain
            core.brain.GEMINI_API_KEY = cleaned_key
            import core.agent
            core.agent.GEMINI_API_KEY = cleaned_key

            # Validate connection across standard Google Gemini models
            active_model = None
            for m_name in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"):
                try:
                    from google import genai
                    client = genai.Client(api_key=cleaned_key)
                    resp = client.models.generate_content(
                        model=m_name,
                        contents='Say: Online.'
                    )
                    if resp and resp.text:
                        active_model = m_name
                        break
                except Exception:
                    continue

            status_text = f"Verified: {active_model} neural link is active." if active_model else "Key saved to .env and activated in runtime."
            reply = f"Google Gemini neural link has been activated, sir. Cognitive capability is now at maximum."
            return {
                "action": "gemini_key_saved",
                "reply": reply,
                "terminal_output": f"[GEMINI API INTEGRATION]\n• Key saved to: {env_path}\n• Active Model: {active_model or 'Default'}\n• Status: {status_text}\n"
            }
        except Exception as e:
            return f"Failed saving Gemini key: {e}"

    def _route_intent(self, text, raw_query):
        # ==========================================
        # GEMINI API CONFIGURATION & KEY SETUP
        # ==========================================
        # Auto-detect raw Google API key anywhere in user message (starts with AIzaSy)
        raw_key_match = re.search(r"\b(AIzaSy[A-Za-z0-9_-]{30,45})\b", raw_query)
        if raw_key_match:
            return self._set_gemini_api_key(raw_key_match.group(1).strip())

        if any(text.startswith(p) for p in ("set api key ", "set gemini key ", "gemini api key ", "gemini key ", "api key ")):
            for p in ("set api key ", "set gemini key ", "gemini api key ", "gemini key ", "api key "):
                if text.startswith(p):
                    key_val = raw_query[len(p):].strip()
                    return self._set_gemini_api_key(key_val)

        if any(phrase in text for phrase in ("get gemini key", "how to get gemini", "where to get gemini", "create gemini key", "open gemini studio")):
            BrowserControl.open_website("https://aistudio.google.com/app/apikey")
            speech = "I have opened Google AI Studio in your browser, sir. Click 'Create API key' to copy your free key, then say: set api key, followed by your key."
            return {
                "action": "open_gemini_studio",
                "reply": speech,
                "terminal_output": "[GEMINI AI STUDIO PORTAL]\nOpened https://aistudio.google.com/app/apikey\nClick 'Create API key' to get your free key.\n"
            }

        # --- Easter Eggs ---
        for egg, egg_reply in self.dialogs.get("easter_eggs", {}).items():
            if egg in text:
                return egg_reply

        # --- Greetings & Casual Conversation ---
        if re.search(r"^(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b", text):
            responses = [
                "Always at your service, sir. What can I do for you today?",
                "Hello, sir. All systems are nominal and ready for your command.",
                "Greetings, sir. How may I assist you?",
                "At your service, sir. What are your orders?",
                "Hello, sir. Ready when you are."
            ]
            return random.choice(responses)

        if text in ("thanks", "thank you", "thanks jarvis", "thank you jarvis", "appreciate it"):
            return random.choice([
                "Always a pleasure to be of service, sir.",
                "Don't mention it, sir. Glad to help.",
                "Anytime, sir. Standing by."
            ])

        if any(w in text for w in ("how are you", "how are you doing", "how r u")):
            return "All internal processors and neural subsystems are operating with zero faults, sir. How are you doing today?"

        if any(w in text for w in ("what's up", "whats up", "what are you doing", "what u doing")):
            return "Monitoring workstation telemetry and standing by for your instructions, sir. What's on your mind?"

        if "who are you" in text or "what are you" in text:
            return "I am J.A.R.V.I.S., your autonomous AI assistant with full administrative control over this workstation."

        if "who made you" in text or "who created you" in text:
            return "I was engineered for your workstation, sir, modeled after Tony Stark's personal OS."

        if "good night" in text:
            return "Good night, sir. Subsystems standing by in low-power standby mode."

        # ==========================================
        # COMPUTER ACCESS: SHELL & TERMINAL COMMANDS
        # ==========================================
        if text.startswith("run command ") or text.startswith("execute command ") or text.startswith("terminal "):
            for prefix in ("run command ", "execute command ", "terminal "):
                if text.startswith(prefix):
                    cmd_part = raw_query[len(prefix):].strip()
                    break
            exec_res = ComputerControl.execute_command(cmd_part, shell_type="powershell")
            out = exec_res["output"]
            speech = f"Command executed, sir." if exec_res["success"] else "Command finished with errors, sir."
            return {
                "action": "shell",
                "reply": speech,
                "terminal_output": f"[EXECUTE] > {cmd_part}\n{out}\n"
            }

        if text.startswith("powershell "):
            cmd_part = raw_query[11:].strip()
            exec_res = ComputerControl.execute_command(cmd_part, shell_type="powershell")
            return {
                "action": "shell",
                "reply": "PowerShell command executed, sir.",
                "terminal_output": f"[POWERSHELL] > {cmd_part}\n{exec_res['output']}\n"
            }

        if text.startswith("cmd "):
            cmd_part = raw_query[4:].strip()
            exec_res = ComputerControl.execute_command(cmd_part, shell_type="cmd")
            return {
                "action": "shell",
                "reply": "Command prompt executed, sir.",
                "terminal_output": f"[CMD] > {cmd_part}\n{exec_res['output']}\n"
            }

        # ==========================================
        # COMPUTER ACCESS: FILE SYSTEM
        # ==========================================
        if text.startswith("open folder ") or text.startswith("open directory "):
            folder = text.replace("open folder", "").replace("open directory", "").strip()
            return ComputerControl.open_path(folder)

        if text.startswith("open file "):
            fpath = raw_query.replace("open file", "", 1).strip()
            return ComputerControl.open_path(fpath)

        if text.startswith("create folder ") or text.startswith("make folder "):
            fname = raw_query.replace("create folder", "", 1).replace("make folder", "", 1).strip()
            return ComputerControl.create_folder(fname)

        if text.startswith("create file ") or text.startswith("make file "):
            fname = raw_query.replace("create file", "", 1).replace("make file", "", 1).strip()
            return ComputerControl.create_file(fname)

        if text.startswith("read file ") or text.startswith("view file "):
            fname = raw_query.replace("read file", "", 1).replace("view file", "", 1).strip()
            content = ComputerControl.read_file(fname)
            return {
                "action": "file_read",
                "reply": f"Retrieved contents of {fname}, sir.",
                "terminal_output": f"[FILE READ] {fname}\n{content}\n"
            }

        if text.startswith("search file ") or text.startswith("find file "):
            fname = text.replace("search file", "").replace("find file", "").strip()
            res = ComputerControl.search_file(fname)
            return {
                "action": "file_search",
                "reply": f"File search completed for {fname}, sir.",
                "terminal_output": f"[SEARCH RESULTS: {fname}]\n{res}\n"
            }

        if "empty recycle bin" in text or "clear recycle bin" in text or "clean recycle bin" in text:
            return ComputerControl.empty_recycle_bin()

        # ==========================================
        # COMPUTER ACCESS: WINDOW MANAGEMENT
        # ==========================================
        if "list windows" in text or "open windows" in text or "what windows are open" in text:
            wins = ComputerControl.get_open_windows()
            win_str = "\n".join([f"• {w}" for w in wins[:10]])
            return {
                "action": "windows_list",
                "reply": f"You currently have {len(wins)} active application windows open, sir.",
                "terminal_output": f"[ACTIVE APPLICATION WINDOWS]\n{win_str}\n"
            }

        if text.startswith("switch to ") or text.startswith("focus "):
            target = text.replace("switch to", "").replace("focus", "").strip()
            return ComputerControl.focus_window(target)

        if "minimize window" in text or "minimize active" in text:
            return ComputerControl.minimize_active_window()

        if "maximize window" in text or "maximize active" in text:
            return ComputerControl.maximize_active_window()

        if "close window" in text or "close active window" in text:
            return ComputerControl.close_active_window()

        if "switch window" in text or "alt tab" in text:
            return ComputerControl.switch_window()

        # ==========================================
        # COMPUTER ACCESS: MOUSE & KEYBOARD
        # ==========================================
        if text.startswith("type ") or text.startswith("write "):
            to_type = raw_query.replace("type ", "", 1).replace("write ", "", 1)
            return ComputerControl.type_text(to_type)

        if text.startswith("press key ") or text.startswith("press "):
            key_name = text.replace("press key", "").replace("press", "").strip()
            if "ctrl" in key_name or "alt" in key_name or "shift" in key_name:
                keys = [k.strip() for k in key_name.replace("+", " ").split()]
                return ComputerControl.send_hotkey(*keys)
            return ComputerControl.press_key(key_name)

        if "double click" in text:
            return ComputerControl.mouse_click(double=True)

        if "right click" in text:
            return ComputerControl.mouse_click(button='right')

        if "click" in text and "mouse" in text:
            return ComputerControl.mouse_click()

        # ==========================================
        # COMPUTER ACCESS: PROCESS & TASK MANAGEMENT
        # ==========================================
        if "running processes" in text or "list tasks" in text or "show tasks" in text or "running apps" in text:
            tasks_str = ComputerControl.get_running_tasks()
            return {
                "action": "tasks",
                "reply": "Displaying top active processes on your console, sir.",
                "terminal_output": f"[TASK MANAGER OVERVIEW]\n{tasks_str}\n"
            }

        if text.startswith("kill process ") or text.startswith("end task ") or text.startswith("kill task "):
            pname = text.replace("kill process", "").replace("end task", "").replace("kill task", "").strip()
            return ComputerControl.kill_task(pname)

        # ==========================================
        # COMPUTER ACCESS: SYSTEM CONFIGURATION & HARDWARE
        # ==========================================
        if "brightness" in text:
            b_match = re.search(r"(\d+)", text)
            if b_match:
                pct = int(b_match.group(1))
                return ComputerControl.set_brightness(pct)
            elif "up" in text or "increase" in text:
                return ComputerControl.set_brightness(80)
            elif "down" in text or "decrease" in text:
                return ComputerControl.set_brightness(40)

        if "my ip" in text or "ip address" in text or "network details" in text or "hostname" in text:
            return ComputerControl.get_network_info()

        if text.startswith("copy to clipboard ") or text.startswith("clipboard copy "):
            clip_text = raw_query.replace("copy to clipboard", "").replace("clipboard copy", "").strip()
            return ComputerControl.clipboard_copy(clip_text)

        if "paste clipboard" in text or "paste text" in text:
            return ComputerControl.clipboard_paste()

        if "sleep computer" in text or "sleep pc" in text:
            return ComputerControl.sleep_system()

        if "restart computer" in text or "restart pc" in text:
            return ComputerControl.restart_system()

        if "shutdown computer" in text or "turn off computer" in text or "turn off pc" in text:
            return ComputerControl.shutdown_system()

        # ==========================================
        # YOUTUBE CONTROLS & SEARCH
        # ==========================================
        # 1. Explicit YouTube Searches: e.g. "search fukra insaan in youtube", "search on youtube for ..."
        yt_search_m = (
            re.search(r"search\s+(.+?)\s+(?:on|in)\s+youtube", text) or
            re.search(r"search\s+(?:on|in)?\s*youtube\s+(?:for\s+)?(.+)", text) or
            re.search(r"youtube\s+search\s+(?:for\s+)?(.+)", text)
        )
        if yt_search_m:
            q = yt_search_m.group(1).strip()
            return YouTubeControl.search(q)

        # Fallback YouTube Search when query contains "youtube" and search/find words
        if "youtube" in text and ("search" in text or "find" in text or "lookup" in text):
            clean_q = text.replace("search", "").replace("find", "").replace("lookup", "").replace("on youtube", "").replace("in youtube", "").replace("for youtube", "").replace("youtube", "").strip()
            if clean_q:
                return YouTubeControl.search(clean_q)

        # 2. Explicit YouTube Playback: e.g. "play faded on youtube", "play fukra insaan in youtube"
        yt_play_m = (
            re.search(r"play\s+(.+?)\s+(?:on|in)\s+youtube", text) or
            re.search(r"play\s+(?:on|in)?\s*youtube\s+(?:for\s+)?(.+)", text)
        )
        if yt_play_m:
            song = yt_play_m.group(1).strip()
            return YouTubeControl.play_direct(song)

        # 3. Direct Play command: e.g. "play iron man theme", "play believer"
        if text.startswith("play ") and text not in ("play video", "play the video", "play music", "play"):
            song = text[5:].strip()
            from config import APP_PATHS
            if song not in APP_PATHS:
                return YouTubeControl.play_direct(song)

        # Check active shorts interruption
        if getattr(YouTubeControl, "is_scrolling_shorts", False) and any(w in text for w in ("stop", "pause", "stop scrolling", "exit", "halt")):
            return YouTubeControl.stop_scrolling_shorts()

        # YouTube Shorts Controls
        if any(w in text for w in ("stop scrolling shorts", "stop shorts")):
            return YouTubeControl.stop_scrolling_shorts()

        if any(w in text for w in ("scroll shorts", "scrolling shorts", "auto scroll shorts", "start scrolling shorts", "open shorts and scroll", "open youtube and start scrolling shorts", "open youtube and scroll shorts")):
            return YouTubeControl.open_and_scroll_shorts(speaker_ref=self.speaker)

        if "open shorts" in text or "youtube shorts" in text:
            return YouTubeControl.open_shorts()

        # Click First Organic Video (with visual ad skipping)
        if any(w in text for w in ("click on the first video", "click the first video", "play the first video", "click first video", "play first video")):
            return YouTubeControl.click_first_organic_video()

        # 4. Player Hotkey Controls
        if "pause video" in text or "play video" in text or "pause the video" in text:
            return YouTubeControl.toggle_play_pause()

        if "video volume up" in text:
            return YouTubeControl.volume_up()


        if "video volume down" in text:
            return YouTubeControl.volume_down()

        if "mute video" in text:
            return YouTubeControl.mute()

        if "subtitles" in text or "captions" in text:
            return YouTubeControl.toggle_captions()

        if "fullscreen" in text:
            return YouTubeControl.toggle_fullscreen()

        if "speed up video" in text or "speed up" in text:
            return YouTubeControl.speed_up()

        if "slow down video" in text:
            return YouTubeControl.speed_down()

        if "skip forward" in text or "skip 10 seconds" in text:
            return YouTubeControl.seek_forward()

        if "rewind" in text or "rewind 10 seconds" in text:
            return YouTubeControl.seek_backward()

        if "next video" in text:
            return YouTubeControl.next_video()

        # ==========================================
        # BROWSER & GENERAL APP LAUNCHING
        # ==========================================
        # Direct URL or domain pasted/typed
        if text.startswith("http://") or text.startswith("https://") or (text.startswith("www.") and ("." in text)):
            if "youtube.com/shorts" in text:
                return YouTubeControl.open_shorts()
            return BrowserControl.open_website(raw_query)

        if text.startswith("open ") and ("site" in text or "website" in text or ".com" in text):
            site = text.replace("open", "").replace("website", "").replace("site", "").strip()
            self.context = {"service": site, "timestamp": time.time()}
            return BrowserControl.open_website(site)


        if text.startswith("open "):
            target = text.replace("open", "").strip()
            self.context = {"service": target, "timestamp": time.time()}
            from config import APP_PATHS, WEB_SHORTCUTS
            if target in APP_PATHS:
                return AppControl.launch_app(target)
            elif target in WEB_SHORTCUTS:
                return BrowserControl.open_website(target)
            else:
                res = AppControl.launch_app(target)
                if "could not locate" in res:
                    # Try opening as path
                    path_res = ComputerControl.open_path(target)
                    if "does not exist" not in path_res:
                        return path_res
                    return BrowserControl.open_website(target)
                return res

        # --- Google & General Web Searches ---
        google_search_m = (
            re.search(r"search\s+(.+?)\s+(?:on|in)\s+google", text) or
            re.search(r"search\s+(?:on|in)?\s*google\s+(?:for\s+)?(.+)", text) or
            re.search(r"google\s+search\s+(?:for\s+)?(.+)", text) or
            re.search(r"^google\s+(.+)", text)
        )
        if google_search_m:
            q = google_search_m.group(1).strip()
            return BrowserControl.google_search(q)

        # General "search for [topic]" or "search [topic]"
        if (text.startswith("search for ") or text.startswith("search ")) and "file" not in text and "folder" not in text:
            q = text.replace("search for ", "", 1) if text.startswith("search for ") else text.replace("search ", "", 1)
            q = q.strip()
            if q:
                # Human-like context awareness: if user mentions channel, or if YouTube was recently opened/active, search in YouTube!
                if "channel" in q or YouTubeControl.is_recently_active() or (self.context.get("service") and "youtube" in self.context.get("service", "") and (time.time() - self.context.get("timestamp", 0) < 1200)):
                    return YouTubeControl.search(q)
                return BrowserControl.google_search(q)


        if "scroll down" in text:
            return BrowserControl.scroll_down()

        if "scroll up" in text:
            return BrowserControl.scroll_up()

        if "scroll to top" in text:
            return BrowserControl.scroll_to_top()

        if "scroll to bottom" in text:
            return BrowserControl.scroll_to_bottom()

        if "new tab" in text:
            return BrowserControl.new_tab()

        close_tab_m = re.search(r"close\s+(?:the\s+|this\s+|active\s+|current\s+|browser\s+)?(?:([a-zA-Z]+)\s+)?tab", text)
        if close_tab_m or "close tab" in text or (text.startswith("close ") and "tab" in text):
            target = "youtube" if "youtube" in text else "browser"
            return BrowserControl.close_tab(target=target)

        if "switch tab" in text:
            return BrowserControl.switch_tab()

        if text.startswith("close ") or text.startswith("terminate ") or text.startswith("kill "):
            app = text.replace("close", "").replace("terminate", "").replace("kill", "").strip()
            return AppControl.close_app(app)

        # ==========================================
        # SYSTEM TELEMETRY & HARDWARE CHECKS
        # ==========================================
        if "battery" in text or "power status" in text:
            return SystemControl.get_battery_info()

        if "system status" in text or "telemetry" in text or "diagnostics" in text or "cpu" in text or "ram" in text:
            return SystemControl.get_system_telemetry()

        if "screenshot" in text:
            return SystemControl.take_screenshot()

        if "speed test" in text or "internet speed" in text:
            return SystemControl.test_internet_speed()

        if "minimize" in text or "show desktop" in text:
            return SystemControl.minimize_all_windows()

        if "lock workstation" in text:
            return SystemControl.lock_workstation()

        # Volume control
        vol_match = re.search(r"volume to (\d+)", text)
        if vol_match:
            pct = int(vol_match.group(1))
            return SystemControl.set_volume_percent(pct)

        if "volume up" in text or "increase volume" in text:
            return SystemControl.volume_up()

        if "volume down" in text or "decrease volume" in text:
            return SystemControl.volume_down()

        if "mute audio" in text or "mute system" in text:
            return SystemControl.mute_volume()

        # ==========================================
        # LIVE INTEL (Weather, News, Time, Jokes, Advice)
        # ==========================================
        if "weather" in text or "temperature" in text:
            city_match = re.search(r"weather in ([a-zA-Z\s]+)", text)
            city = city_match.group(1).strip() if city_match else None
            return LiveIntel.get_weather(city)

        if "news" in text or "headlines" in text:
            return LiveIntel.get_top_news()

        if "time" in text or "date" in text:
            return LiveIntel.get_time_and_date()

        if "joke" in text:
            return LiveIntel.get_joke()

        if "advice" in text or "quote" in text:
            return LiveIntel.get_advice()

        return None

    def _query_ai_or_web(self, query):
        """Intelligent conversational AI response using Gemini if active, with smart offline persona fallback."""
        import os
        import config
        active_key = config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")

        # 1. Use Google Gemini 2.5 Flash if key is configured
        if active_key:
            try:
                from google import genai
                client = genai.Client(api_key=active_key)
                prompt = (
                    "You are J.A.R.V.I.S., Tony Stark's sophisticated, highly intelligent AI assistant. "
                    "Respond concisely (1 to 3 sentences maximum) in a polished, intelligent, slightly witty, polite tone. "
                    "Address the user as 'sir'.\n\n"
                    f"User Query: {query}"
                )
                response = None
                for m_name in ('gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash'):
                    try:
                        response = client.models.generate_content(
                            model=m_name,
                            contents=prompt
                        )
                        if response and response.text:
                            return response.text.strip()
                    except Exception:
                        continue
            except Exception as e:
                print(f"[Brain] Gemini API error: {e}")

        # 2. If Gemini key is missing, ONLY use Wikipedia for explicit factual encyclopedic lookup queries
        # (e.g. "who was Albert Einstein", "what is photosynthesis", "tell me about quantum computing")
        q_lower = query.lower().strip()
        is_factual = any(q_lower.startswith(p) for p in (
            "who was ", "who is ", "what is ", "what was ", "tell me about ", "explain ", "define ", "history of "
        ))
        conversational_words = {"hello", "hi", "hey", "what", "who", "why", "how", "cool", "nice", "ok", "yes", "no", "thanks"}
        if is_factual and q_lower not in conversational_words and len(q_lower.split()) > 2:
            try:
                clean_term = q_lower
                for p in ("who was ", "who is ", "what is ", "what was ", "tell me about ", "explain ", "define ", "history of "):
                    if clean_term.startswith(p):
                        clean_term = clean_term[len(p):].strip()
                        break
                clean_q = urllib.parse.quote(clean_term)
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_q}"
                req = urllib.request.Request(url, headers={'User-Agent': 'JarvisDesktopAssistant/1.0'})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    extract = data.get('extract')
                    if extract:
                        sentences = extract.split(". ")
                        summary = ". ".join(sentences[:2]) + "."
                        return f"According to historical archives, {summary}"
            except Exception:
                pass

        # 3. Smart offline persona response
        offline_replies = [
            f"Understood, sir. I have full control over your computer, applications, files, and YouTube. To enable open-domain general conversational intelligence, please connect your free Gemini API key.",
            f"I hear you, sir. All local subsystems are standing by. For deep conversational answers, activate your Gemini API key by typing 'set api key' or clicking the Gemini button in the HUD.",
            "All internal diagnostics are nominal, sir. What would you like me to do next on your workstation?"
        ]
        return random.choice(offline_replies)
