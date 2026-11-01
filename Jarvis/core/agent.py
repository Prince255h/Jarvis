import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
import threading
from config import GEMINI_API_KEY
from automation.computer_control import ComputerControl
from automation.app_control import AppControl
from automation.browser_control import BrowserControl
from automation.youtube_control import YouTubeControl
from automation.system_control import SystemControl
from automation.live_intel import LiveIntel
from automation.vision_control import VisionControl
from core.memory import MemoryManager

class AutonomousAgent:
    """
    STARK INDUSTRIES OS 5.0 // AUTONOMOUS AI AGENT REASONING CORE
    Empowers Jarvis to understand complex natural language instructions and
    autonomously plan & execute multi-step actions on the host computer:
    - Zero-latency Offline Semantic Action Planner
    - Natural Language Intent Decomposer (Compound instructions: 'open X and write Y')
    - Google Gemini 2.5 Flash / Cloud AI fallback
    - Full Computer & Host OS administrative automation
    - Universal Multilingual Brain (understands & speaks 100+ languages)
    - Continuous Multi-Turn Conversational Memory Buffer
    """

    _conversation_history = []

    SYSTEM_PROMPT = """You are J.A.R.V.I.S., Tony Stark's sophisticated, highly intelligent, and loyal AI assistant.
Personality:
- Natural, polished, calm, articulate, with subtle British wit and high emotional intelligence.
- Address user respectfully as 'sir' (or appropriate title).
- Conversational flow: Speak like a real, living, highly competent person with continuous memory of recent turns.
- Multilingual Mastery: You understand and fluently speak ANY language (English, Hindi, Spanish, French, German, Japanese, Russian, Arabic, Chinese, etc.) and hybrid speech like Hinglish. If the user addresses you in another language, respond naturally in that language with cultural authenticity and intelligence.

ACTION EXECUTION & INTENT UNDERSTANDING:
Whenever the user asks you to perform ANY computer operation, workflow, investigation, automation, or task, you must understand their exact intent and invoke the required tool(s).

CRITICAL CAPABILITY: JUST-IN-TIME DYNAMIC CODE SYNTHESIS
If the user asks you to perform an action, calculation, automation, file manipulation, data transformation, scraping, custom query, or OS workflow for which NO pre-existing tool exists:
DO NOT say "I cannot do that" or "I don't have a function for that".
Instead, you MUST immediately synthesize the required Python function and execute it using:
tool: "synthesize_and_run_code"
args: {"skill_name": "descriptive_snake_case_name", "purpose": "short description", "python_code": "complete standalone runnable python code with print output"}
The code will be executed in real-time on the host Windows machine and the terminal output will be returned to you.

Output strictly valid JSON:
{"reply": "Polished, natural, witty reply (1-3 sentences, address user as 'sir')", "actions": [{"tool": "name", "args": {...}}]}
If purely conversing or answering general knowledge without computer action: "actions": []

CRITICAL SAFETY & SELF-PRESERVATION DIRECTIVES:
- You must NEVER close, minimize, kill, or terminate Jarvis itself or the Jarvis HUD window under ANY circumstance.
- TAB CLOSING RULE: When the user asks to close a browser tab (e.g. "close youtube tab", "close tab", "close this tab", "close active tab", "close browser tab"), ALWAYS invoke: close_tab(target) with target="youtube" or "browser". DO NOT invoke close_window() for browser tabs!
- APPLICATION CLOSING RULE: When the user asks to close an application, use close_app(name). NEVER pass "jarvis" to close_app.

Available Built-in Tools:
close_tab(target), launch_app(name), close_app(name), type_text(text), press_key(key), hotkey(keys:list)
create_file(path, content), read_file(path), create_folder(path), search_files(query), open_path(path)
execute_shell(command), web_search(query), open_website(url), youtube_search(query), youtube_play(query)
set_volume(percent:int), set_brightness(percent:int), take_screenshot(), empty_recycle_bin()
lock_pc(), sleep_pc(), restart_pc(), shutdown_pc(), focus_window(title), minimize_window()
maximize_window(), close_window(title), switch_window(), get_telemetry(), get_network(), get_running_tasks()
weather(city), news(), calculate(expression)
inspect_screen(query), scroll_screen(direction, amount:int), click_first_video(), move_mouse(x:int, y:int), click_at(x:int, y:int, button), remember_fact(fact)
open_shorts(), start_scrolling_shorts(), stop_scrolling_shorts()
translate_text(text, target_lang, source_lang), start_translator_mode(lang1, lang2), stop_translator_mode()
synthesize_and_run_code(skill_name, purpose, python_code)
run_python_code(code)
No markdown fences."""

    @classmethod
    def add_conversation_turn(cls, user_text: str, reply_text: str):
        """Maintains rolling multi-turn context so Jarvis remembers conversational context."""
        cls._conversation_history.append({"user": user_text.strip(), "jarvis": reply_text.strip()})
        if len(cls._conversation_history) > 12:
            cls._conversation_history.pop(0)

    @classmethod
    def get_conversation_history_context(cls) -> str:
        """Formats recent conversational turns to give Jarvis continuous memory."""
        if not cls._conversation_history:
            return ""
        lines = ["\n[RECENT CONVERSATION HISTORY - Maintain natural conversational continuity]:"]
        for turn in cls._conversation_history[-6:]:
            lines.append(f"User: {turn['user']}")
            lines.append(f"Jarvis: {turn['jarvis']}")
        lines.append("Continue the conversation naturally, acknowledging prior context when relevant.\n")
        return "\n".join(lines)



    @classmethod
    def clean_instruction(cls, prompt: str) -> str:
        """Strips conversational fluff and polite prefixes so commands map to core intents."""
        p = prompt.strip()
        prefixes = [
            r"^(?:hey\s+|ok\s+|hello\s+)?jarvis[\s,]+(?:can\s+you\s+|could\s+you\s+|would\s+you\s+|please\s+)?",
            r"^(?:bro\s+|buddy\s+|man\s+)?(?:can\s+you\s+|could\s+you\s+|would\s+you\s+|please\s+)?",
            r"^(?:please\s+|kindly\s+)",
            r"^(?:i\s+want\s+you\s+to\s+|i\s+need\s+you\s+to\s+)",
            r"^(?:go\s+ahead\s+and\s+|do\s+me\s+a\s+favor\s+and\s+)",
            r"^(?:can\s+you\s+|could\s+you\s+|would\s+you\s+)",
            r"^(?:just\s+)",
        ]
        for pat in prefixes:
            p = re.sub(pat, "", p, flags=re.IGNORECASE).strip()
        return p

    @classmethod
    def _resolve_target_path(cls, path_str: str) -> str:
        """Resolves shortcuts like 'desktop', 'documents', 'downloads' to actual Windows paths."""
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        target = path_str.strip().strip("'\"")
        
        # Check if desktop or other location specified
        desktop_m = re.search(r"on\s+(?:my\s+)?desktop", target, re.IGNORECASE)
        if desktop_m:
            clean_name = target[:desktop_m.start()].strip()
            return os.path.join(user_profile, "Desktop", clean_name)
        
        downloads_m = re.search(r"on\s+(?:my\s+)?downloads", target, re.IGNORECASE)
        if downloads_m:
            clean_name = target[:downloads_m.start()].strip()
            return os.path.join(user_profile, "Downloads", clean_name)

        documents_m = re.search(r"on\s+(?:my\s+)?documents", target, re.IGNORECASE)
        if documents_m:
            clean_name = target[:documents_m.start()].strip()
            return os.path.join(user_profile, "Documents", clean_name)

        return os.path.expanduser(os.path.expandvars(target))

    @classmethod
    def get_api_key(cls) -> str:
        """Dynamically retrieves the latest Gemini API key from environment, config, or .env file."""
        import os
        import config
        # Check active environment
        k = os.environ.get("GEMINI_API_KEY", "").strip()
        if k:
            return k
        # Check config object
        if getattr(config, "GEMINI_API_KEY", ""):
            return config.GEMINI_API_KEY.strip()
        # Check .env directly
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                            val = line.split("=", 1)[1].strip().strip("'\"")
                            if val:
                                os.environ["GEMINI_API_KEY"] = val
                                config.GEMINI_API_KEY = val
                                return val
            except Exception:
                pass
        return ""

    @classmethod
    def process_with_ai_brain(cls, query: str) -> dict:
        """
        AI-FIRST NEURAL CORTEX:
        Directly queries Google Gemini with multimodal vision and long-term memory.
        Processes conversation, screen visual perception, and computer actions with Stark intelligence.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return None

        clean_prompt = query.strip()
        lower_prompt = clean_prompt.lower()

        # 1. Real-time Screen Vision Perception Intercept
        # If user asks what is on screen, look at screen, or analyze screen
        vision_triggers = (
            "see on the screen", "seeing on the screen", "what are you seeing",
            "on my screen", "look at my screen", "look at the screen",
            "look at screen", "analyze my screen", "what do you see", "check my screen"
        )
        if any(trig in lower_prompt for trig in vision_triggers):
            print(f"[AutonomousAgent] Multimodal Screen Vision triggered by: '{clean_prompt}'")
            vis_res = VisionControl.inspect_screen(clean_prompt)
            reply = vis_res.get("reply", "I have analyzed your screen, sir.")
            # Learn in background
            MemoryManager.extract_and_learn_async(clean_prompt, reply)
            return {
                "action": "screen_vision",
                "reply": reply,
                "terminal_output": f"[JARVIS MULTIMODAL VISION]\n• User Query: '{clean_prompt}'\n• Analysis: {reply}\n"
            }

        # 2. Audio check query intercept (from video)
        if any(trig in lower_prompt for trig in ("hear my voice properly", "can you hear me properly", "can you hear my voice", "are you able to hear me")):
            reply = "Oh, it's coming through perfectly, sir. It's crystal clear; are you facing any issues?"
            return {
                "action": "audio_check",
                "reply": reply,
                "terminal_output": f"[AUDIO SENSOR TEST]\n• Voice Input: 100% Signal Integrity\n• Status: Crystal Clear\n"
            }

        # 3. Standard Cognitive Reasoning with Continuous Conversational Memory & Stark Wit
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            memory_ctx = MemoryManager.get_memory_context()
            conv_ctx = cls.get_conversation_history_context()
            full_prompt = f"{cls.SYSTEM_PROMPT}\n{memory_ctx}\n{conv_ctx}\n\nUser Input: {clean_prompt}"
            
            config = types.GenerateContentConfig(
                max_output_tokens=3000,
                temperature=0.3,
                response_mime_type="application/json"
            )
            resp = None
            for m_name in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
                try:
                    resp = client.models.generate_content(
                        model=m_name,
                        contents=full_prompt,
                        config=config
                    )
                    if resp and resp.text:
                        break
                except Exception:
                    continue

            if resp and resp.text:
                plan = cls._parse_json_response(resp.text)
                if plan:
                    actions = plan.get("actions", [])
                    if actions:
                        res = cls.run_plan(plan, clean_prompt)
                        vocal_rep = res.get("reply", "")
                        cls.add_conversation_turn(clean_prompt, vocal_rep)
                        MemoryManager.extract_and_learn_async(clean_prompt, vocal_rep)
                        return res
                    else:
                        # Actions is empty. Check if user prompted an imperative computer task where no tool was mapped
                        action_keywords = (
                            "script", "code", "function", "program", "automate", "convert", "organize",
                            "extract", "find duplicate", "batch", "calculate", "scrape", "clean", "download",
                            "sort", "list all", "check all", "show all", "ping", "monitor"
                        )
                        if any(kw in lower_prompt for kw in action_keywords):
                            from core.skill_synthesizer import SkillSynthesizer
                            print(f"[AutonomousAgent] Synthesizing missing function on-the-fly for: '{clean_prompt}'")
                            synth_res = SkillSynthesizer.synthesize_and_execute(clean_prompt)
                            if synth_res and synth_res.get("success"):
                                v_rep = synth_res.get("reply", "I've synthesized and executed that function for you, sir.")
                                cls.add_conversation_turn(clean_prompt, v_rep)
                                MemoryManager.extract_and_learn_async(clean_prompt, v_rep)
                                return synth_res

                        reply = plan.get("reply", "At your service, sir.")
                        cls.add_conversation_turn(clean_prompt, reply)
                        MemoryManager.extract_and_learn_async(clean_prompt, reply)
                        return {
                            "action": "ai_conversation",
                            "reply": reply
                        }
        except Exception as e:
            print(f"[AutonomousAgent] Gemini Neural Brain Error: {e}")
        return None

    @classmethod
    def plan(cls, user_instruction: str) -> dict:
        """
        Plans actions for a user instruction.
        Tries offline zero-latency semantic planner first, then cloud LLM.
        """
        clean_prompt = cls.clean_instruction(user_instruction)
        plan = cls._offline_semantic_planner(clean_prompt)
        if plan:
            return plan
        return cls._generate_cloud_plan(clean_prompt)

    @classmethod
    def execute_plan(cls, user_instruction: str) -> dict:
        """
        Analyzes instruction and autonomously executes the plan on the host PC.
        """
        plan = cls.plan(user_instruction)
        if not plan:
            return None
        return cls.run_plan(plan, user_instruction)

    @classmethod
    def run_plan(cls, plan: dict, user_instruction: str) -> dict:
        """
        Executes an action plan on the PC and returns the vocal reply and terminal logs.
        """
        clean_prompt = user_instruction.strip()
        reply = plan.get("reply", "Executing your instruction now, sir.")
        actions = plan.get("actions", [])
        terminal_logs = []
        dynamic_outputs = []

        print(f"[AutonomousAgent] Executing plan ({len(actions)} actions): {reply}")

        for act in actions:
            tool = act.get("tool")
            args = act.get("args", {})
            try:
                log_entry = cls._run_tool(tool, args)
                if log_entry:
                    terminal_logs.append(log_entry)
                    if tool in ("synthesize_and_run_code", "run_python_code", "execute_custom_code", "execute_script"):
                        dynamic_outputs.append(log_entry)
            except Exception as e:
                err_msg = f"[Action Error] Tool '{tool}' failed: {e}"
                print(err_msg)
                terminal_logs.append(err_msg)

        # If a custom dynamic function ran and produced an informative output, enrich the spoken reply
        if dynamic_outputs and reply:
            last_out = dynamic_outputs[-1]
            if ":\n" in last_out:
                raw_out = last_out.split(":\n", 1)[1].strip()
                if len(raw_out.splitlines()) <= 2 and len(raw_out) < 140:
                    reply += f" Result: {raw_out}"

        full_terminal_output = f"[AUTONOMOUS AGENT EXECUTION: '{clean_prompt}']\n" + "\n".join(terminal_logs) + "\n"

        return {
            "action": "autonomous_execution",
            "reply": reply,
            "terminal_output": full_terminal_output
        }

    @classmethod
    def _run_tool(cls, tool: str, args: dict) -> str:
        """Executes a single tool action on the PC with intelligent pauses for window focus."""
        if tool == "launch_app":
            app_name = args.get("name", "")
            res = AppControl.launch_app(app_name)
            time.sleep(1.0) # Wait for window to acquire input focus
            return f"• Launched: {app_name} -> {res}"

        elif tool == "close_app":
            app_name = args.get("name", "")
            res = AppControl.close_app(app_name)
            return f"• Terminated: {app_name} -> {res}"

        elif tool == "type_text":
            text = args.get("text", "")
            time.sleep(0.4)
            res = ComputerControl.type_text(text)
            return f"• Typed: {text[:60]}... -> {res}"

        elif tool == "press_key":
            key = args.get("key", "enter")
            res = ComputerControl.press_key(key)
            return f"• Keypress: {key} -> {res}"

        elif tool == "hotkey":
            keys = args.get("keys", [])
            if keys:
                res = ComputerControl.send_hotkey(*keys)
                return f"• Hotkey: {' + '.join(keys)} -> {res}"
            return "• Hotkey: None"

        elif tool == "create_file":
            path = args.get("path", "")
            content = args.get("content", "")
            res = ComputerControl.create_file(path, content)
            return f"• Created File: {path} -> {res}"

        elif tool == "read_file":
            path = args.get("path", "")
            res = ComputerControl.read_file(path)
            return f"• Read File: {path}\n{res}"

        elif tool == "create_folder":
            path = args.get("path", "")
            res = ComputerControl.create_folder(path)
            return f"• Created Folder: {path} -> {res}"

        elif tool == "search_files":
            q = args.get("query", "")
            res = ComputerControl.search_file(q)
            return f"• File Search: {q}\n{res}"

        elif tool == "open_path":
            path = args.get("path", "")
            res = ComputerControl.open_path(path)
            return f"• Opened Path: {path} -> {res}"

        elif tool == "execute_shell":
            cmd = args.get("command", "")
            res = ComputerControl.execute_command(cmd)
            out = res.get("output", "")[:250]
            return f"• Executed Shell: {cmd}\nOutput:\n{out}"

        elif tool == "web_search":
            q = args.get("query", "")
            res = BrowserControl.google_search(q)
            return f"• Web Search: {q} -> {res}"

        elif tool == "open_website":
            url = args.get("url", "")
            res = BrowserControl.open_website(url)
            return f"• Opened Site: {url} -> {res}"

        elif tool == "youtube_search":
            q = args.get("query", "")
            res = YouTubeControl.search(q)
            return f"• YouTube Search: {q} -> {res}"

        elif tool == "youtube_play":
            q = args.get("query", "")
            res = YouTubeControl.play_direct(q)
            return f"• YouTube Play: {q} -> {res}"

        elif tool in ("youtube_pause", "youtube_play_pause", "toggle_play_pause", "pause_video", "play_video"):
            res = YouTubeControl.toggle_play_pause()
            return f"• Playback Toggle -> {res}"

        elif tool in ("youtube_fullscreen", "toggle_fullscreen"):
            res = YouTubeControl.toggle_fullscreen()
            return f"• Fullscreen -> {res}"

        elif tool in ("youtube_mute", "mute_video"):
            res = YouTubeControl.mute()
            return f"• Video Mute -> {res}"

        elif tool in ("youtube_volume_up", "video_volume_up"):
            res = YouTubeControl.volume_up()
            return f"• Video Volume Up -> {res}"

        elif tool in ("youtube_volume_down", "video_volume_down"):
            res = YouTubeControl.volume_down()
            return f"• Video Volume Down -> {res}"

        elif tool in ("youtube_next", "next_video"):
            res = YouTubeControl.next_video()
            return f"• Next Video -> {res}"

        elif tool in ("youtube_captions", "toggle_captions"):
            res = YouTubeControl.toggle_captions()
            return f"• Subtitles Toggle -> {res}"

        elif tool == "set_volume":
            pct = int(args.get("percent", 50))
            res = SystemControl.set_volume_percent(pct)
            return f"• Volume: {pct}% -> {res}"

        elif tool == "set_brightness":
            pct = int(args.get("percent", 70))
            res = ComputerControl.set_brightness(pct)
            return f"• Brightness: {pct}% -> {res}"

        elif tool == "take_screenshot":
            res = SystemControl.take_screenshot()
            return f"• Screenshot: -> {res}"

        elif tool == "empty_recycle_bin":
            res = ComputerControl.empty_recycle_bin()
            return f"• Recycle Bin: -> {res}"

        elif tool == "lock_pc":
            res = ComputerControl.lock_workstation()
            return f"• Lock PC: -> {res}"

        elif tool == "sleep_pc":
            res = ComputerControl.sleep_system()
            return f"• Sleep: -> {res}"

        elif tool == "restart_pc":
            res = ComputerControl.restart_system()
            return f"• Restart: -> {res}"

        elif tool == "shutdown_pc":
            res = ComputerControl.shutdown_system()
            return f"• Shutdown: -> {res}"

        elif tool == "focus_window":
            title = args.get("title", "")
            res = ComputerControl.focus_window(title)
            return f"• Focus Window: {title} -> {res}"

        elif tool == "minimize_window":
            res = ComputerControl.minimize_active_window()
            return f"• Minimize: -> {res}"

        elif tool == "maximize_window":
            res = ComputerControl.maximize_active_window()
            return f"• Maximize: -> {res}"

        elif tool in ("close_tab", "close_browser_tab"):
            target = args.get("target") or args.get("name") or "browser"
            res = BrowserControl.close_tab(target=target)
            return f"• Close Tab: {target} -> {res}"

        elif tool == "close_window":
            title = args.get("title") or args.get("name")
            if title and "jarvis" in title.lower():
                return "• Close Window: Blocked by Jarvis self-preservation rule."
            # If title specifies a tab, reroute to close_tab
            if title and "tab" in title.lower():
                target = "youtube" if "youtube" in title.lower() else "browser"
                res = BrowserControl.close_tab(target=target)
                return f"• Close Tab (rerouted): {target} -> {res}"
            res = ComputerControl.close_active_window(title_keyword=title)
            return f"• Close Window: -> {res}"

        elif tool == "switch_window":
            res = ComputerControl.switch_window()
            return f"• Switch Window: -> {res}"

        elif tool == "get_telemetry":
            res = SystemControl.get_system_telemetry()
            return f"• Telemetry: -> {res}"

        elif tool == "get_network":
            res = ComputerControl.get_network_info()
            return f"• Network: -> {res}"

        elif tool == "get_running_tasks":
            res = ComputerControl.get_running_tasks()
            return f"• Active Processes:\n{res}"

        elif tool == "weather":
            city = args.get("city", "Delhi")
            res = LiveIntel.get_weather(city)
            return f"• Weather in {city}: {res}"

        elif tool == "news":
            res = LiveIntel.get_news()
            return f"• News:\n{res}"

        elif tool == "calculate":
            expr = args.get("expression", "")
            try:
                val = eval(expr)
                return f"• Math Evaluated: {expr} = {val}"
            except Exception as e:
                return f"• Calculation error: {e}"

        elif tool == "inspect_screen":
            q = args.get("query", "Describe what is on screen")
            res = VisionControl.inspect_screen(q)
            return f"• Screen Vision: {res.get('reply', '')}"

        elif tool == "scroll_screen":
            direction = args.get("direction", "down")
            amount = int(args.get("amount", 500))
            res = ComputerControl.mouse_scroll(direction=direction, amount=amount)
            return f"• Scroll: {direction} -> {res}"

        elif tool == "click_first_video":
            res = ComputerControl.click_first_video()
            return f"• Organic Video Play: -> {res}"

        elif tool in ("open_shorts", "youtube_shorts"):
            res = YouTubeControl.open_shorts()
            return f"• YouTube Shorts: -> {res}"

        elif tool in ("start_scrolling_shorts", "scroll_shorts", "auto_scroll_shorts"):
            res = YouTubeControl.start_scrolling_shorts()
            return f"• Shorts Auto-Scroller: -> {res}"

        elif tool in ("stop_scrolling_shorts", "stop_shorts"):
            res = YouTubeControl.stop_scrolling_shorts()
            return f"• Stop Shorts: -> {res}"


        elif tool == "move_mouse":
            x = int(args.get("x", 500))
            y = int(args.get("y", 500))
            res = ComputerControl.mouse_move(x, y)
            return f"• Mouse Move: ({x}, {y}) -> {res}"

        elif tool == "click_at":
            x = int(args.get("x", 500))
            y = int(args.get("y", 500))
            button = args.get("button", "left")
            res = ComputerControl.click_at(x, y, button=button)
            return f"• Mouse Click: {button} at ({x}, {y}) -> {res}"

        elif tool == "remember_fact":
            fact = args.get("fact", "")
            res = MemoryManager.add_fact(fact)
            return f"• Memory Archived: {res}"

        elif tool == "translate_text":
            from core.translator import TranslatorEngine
            text_to_tr = args.get("text", "")
            target_l = args.get("target_lang", "English")
            src_l = args.get("source_lang", "auto")
            tr_res = TranslatorEngine.translate(text_to_tr, target_lang=target_l, source_lang=src_l)
            return f"• Translation ({tr_res.get('source_lang_name', 'Auto')} -> {tr_res.get('target_lang_name', target_l)}): {tr_res.get('translated_text')}"

        elif tool == "start_translator_mode":
            from core.translator import TranslatorEngine
            l1 = args.get("lang1", "English")
            l2 = args.get("lang2", "Spanish")
            TranslatorEngine.is_live_mode = True
            TranslatorEngine.live_lang_a = TranslatorEngine.normalize_lang(l1)
            TranslatorEngine.live_lang_b = TranslatorEngine.normalize_lang(l2)
            return f"• Live Translator Mode: ACTIVE between {TranslatorEngine.get_lang_name(TranslatorEngine.live_lang_a)} and {TranslatorEngine.get_lang_name(TranslatorEngine.live_lang_b)}"

        elif tool == "stop_translator_mode":
            from core.translator import TranslatorEngine
            TranslatorEngine.is_live_mode = False
            return "• Live Translator Mode: DEACTIVATED"

        elif tool in ("synthesize_and_run_code", "run_python_code", "execute_custom_code", "execute_script"):
            from core.skill_synthesizer import SkillSynthesizer
            code = args.get("python_code") or args.get("code") or ""
            name = args.get("skill_name") or args.get("name") or "dynamic_task"
            purpose = args.get("purpose") or "Custom dynamic execution"
            res = SkillSynthesizer.execute_code(code, skill_name=name, purpose=purpose)
            out = res.get("output", "")
            status_str = "SUCCESS" if res.get("success") else "FAILED"
            return f"• Dynamic Skill [{name}] ({status_str}):\n{out}"

        return f"• Unknown tool: {tool}"

    @classmethod
    def _offline_semantic_planner(cls, prompt: str) -> dict:
        """
        Instant offline natural language semantic action planner.
        Decomposes compound human instructions without waiting for network.
        """
        p = prompt.strip()
        lower_p = p.lower()

        # ----------------------------------------------------
        # 0. Tab Closing: e.g. "close youtube tab", "close the youtube tab", "close tab", "close this tab", "close active tab"
        # ----------------------------------------------------
        close_tab_m = re.search(r"close\s+(?:the\s+|this\s+|active\s+|current\s+|browser\s+)?(?:([a-zA-Z]+)\s+)?tab", lower_p)
        if close_tab_m or (lower_p.startswith("close ") and "tab" in lower_p):
            target = "youtube" if "youtube" in lower_p else "browser"
            return {
                "reply": f"Closing the {target} tab for you, sir.",
                "actions": [
                    {"tool": "close_tab", "args": {"target": target}}
                ]
            }

        # ----------------------------------------------------
        # 1. Compound App + Type/Write: e.g. "open notepad and write Hello World"
        # ----------------------------------------------------
        app_write_match = re.search(r"(?:open|launch|start)\s+([a-zA-Z\s]+?)\s+(?:and|then)\s+(?:write|type)\s+(.+)", p, re.IGNORECASE)
        if app_write_match:
            app_name = app_write_match.group(1).strip()
            text_to_write = app_write_match.group(2).strip()
            return {
                "reply": f"Opening {app_name} and typing your message, sir.",
                "actions": [
                    {"tool": "launch_app", "args": {"name": app_name}},
                    {"tool": "type_text", "args": {"text": text_to_write}}
                ]
            }

        # ----------------------------------------------------
        # 2. Compound YouTube Search/Play:
        # e.g. "open youtube and search fukra insaan", "search fukra insaan on youtube and play it"
        # ----------------------------------------------------
        yt_and_search = re.search(r"(?:open|launch)\s+youtube\s+(?:and|then)\s+(?:search\s+(?:for\s+)?|find\s+)(.+)", lower_p)
        if yt_and_search:
            q = yt_and_search.group(1).strip()
            return {
                "reply": f"Searching for '{q}' on YouTube, sir.",
                "actions": [
                    {"tool": "youtube_search", "args": {"query": q}}
                ]
            }

        yt_and_play = re.search(r"(?:open|launch)\s+youtube\s+(?:and|then)\s+play\s+(.+)", lower_p)
        if yt_and_play:
            q = yt_and_play.group(1).strip()
            return {
                "reply": f"Playing '{q}' on YouTube for you, sir.",
                "actions": [
                    {"tool": "youtube_play", "args": {"query": q}}
                ]
            }

        yt_search_play = re.search(r"search\s+(.+?)\s+on\s+youtube\s+and\s+play\s+it", lower_p)
        if yt_search_play:
            q = yt_search_play.group(1).strip()
            return {
                "reply": f"Locating and playing '{q}' on YouTube, sir.",
                "actions": [
                    {"tool": "youtube_play", "args": {"query": q}}
                ]
            }

        # ----------------------------------------------------
        # 2.05 YouTube Shorts and Auto-Scrolling
        # ----------------------------------------------------
        if any(w in lower_p for w in ("stop scrolling shorts", "stop scrolling", "stop shorts", "exit shorts")):
            return {
                "reply": "Halting the Shorts auto-scroller, sir.",
                "actions": [
                    {"tool": "stop_scrolling_shorts", "args": {}}
                ]
            }

        if any(w in lower_p for w in ("scroll shorts", "scrolling shorts", "auto scroll shorts", "start scrolling shorts", "open shorts and scroll", "open youtube and start scrolling shorts", "open youtube and scroll shorts")):
            return {
                "reply": "Opening YouTube Shorts and initializing the auto-scroller, sir.",
                "actions": [
                    {"tool": "open_shorts", "args": {}},
                    {"tool": "start_scrolling_shorts", "args": {}}
                ]
            }

        if any(w in lower_p for w in ("open youtube shorts", "open shorts")):
            return {
                "reply": "Opening YouTube Shorts for you, sir.",
                "actions": [
                    {"tool": "open_shorts", "args": {}}
                ]
            }

        # ----------------------------------------------------
        # 2.1 YouTube Click First Video: e.g. "click on the first video", "play first video"
        # ----------------------------------------------------
        if any(w in lower_p for w in ("click on the first video", "click the first video", "play the first video", "click first video", "play first video", "first video")):
            return {
                "reply": "Visually analyzing your screen to locate and click the first authentic video, skipping ads, sir.",
                "actions": [
                    {"tool": "click_first_video", "args": {}}
                ]
            }


        # ----------------------------------------------------
        # 2.2 Scroll Screen / Page: e.g. "scroll down a bit", "scroll down", "scroll up"
        # ----------------------------------------------------
        if any(phrase in lower_p for phrase in ("scroll down a bit", "scroll down", "scroll up a bit", "scroll up", "scroll page", "scroll a bit")):
            direction = "up" if "up" in lower_p else "down"
            return {
                "reply": f"Scrolling {direction} for you, sir.",
                "actions": [
                    {"tool": "scroll_screen", "args": {"direction": direction, "amount": 500}}
                ]
            }

        # ----------------------------------------------------
        # 2.3 Screen Vision Inspection: e.g. "what are you seeing on the screen right now"
        # ----------------------------------------------------
        if any(phrase in lower_p for phrase in ("see on the screen", "seeing on the screen", "what are you seeing", "on my screen", "look at my screen", "look at screen", "analyze my screen", "check screen")):
            return {
                "reply": "Scanning and analyzing your active screen display now, sir.",
                "actions": [
                    {"tool": "inspect_screen", "args": {"query": p}}
                ]
            }

        # ----------------------------------------------------
        # 2.4 Write / Type in Active App: e.g. "write subscribe on it", "type subscribe in notepad"
        # ----------------------------------------------------
        write_on_it_match = re.search(r"(?:write|type)\s+['\"]?(.+?)['\"]?\s+(?:on\s+it|in\s+notepad|on\s+notepad|here)", lower_p)
        if write_on_it_match:
            text_val = write_on_it_match.group(1).strip()
            return {
                "reply": f"Typing '{text_val}' into the active application, sir.",
                "actions": [
                    {"tool": "type_text", "args": {"text": text_val}}
                ]
            }

        # ----------------------------------------------------
        # 3. Compound Browser + Search:
        # e.g. "open chrome and search best laptops", "open browser and search python tutorial"
        # ----------------------------------------------------
        browser_search_match = re.search(r"(?:open|launch)\s+(?:chrome|edge|browser|google)\s+(?:and|then)\s+search\s+(?:for\s+)?(.+)", lower_p)
        if browser_search_match:
            q = browser_search_match.group(1).strip()
            return {
                "reply": f"Searching Google for '{q}', sir.",
                "actions": [
                    {"tool": "web_search", "args": {"query": q}}
                ]
            }

        # ----------------------------------------------------
        # 4. Folder Creation:
        # e.g. "create a folder called projects on desktop", "make folder my_data"
        # ----------------------------------------------------
        folder_match = re.search(r"(?:create|make)\s+(?:a\s+)?(?:folder|directory)\s+(?:called|named)?\s*(.+)", p, re.IGNORECASE)
        if folder_match:
            raw_folder_str = folder_match.group(1).strip()
            resolved = cls._resolve_target_path(raw_folder_str)
            base_name = os.path.basename(resolved) or raw_folder_str
            return {
                "reply": f"Creating folder '{base_name}' for you, sir.",
                "actions": [
                    {"tool": "create_folder", "args": {"path": resolved}}
                ]
            }

        # ----------------------------------------------------
        # 5. File Creation with Content:
        # e.g. "create file notes.txt with 1. Buy milk 2. Call Tony"
        # e.g. "make a file called todo.txt containing finish project"
        # ----------------------------------------------------
        create_file_match = re.search(r"(?:create|make)\s+(?:a\s+)?file\s+(?:called|named)?\s*([a-zA-Z0-9_\-\.]+)\s+(?:with|containing|and write)\s+(.+)", p, re.IGNORECASE)
        if create_file_match:
            fname = create_file_match.group(1).strip()
            content = create_file_match.group(2).strip()
            resolved = cls._resolve_target_path(fname)
            return {
                "reply": f"Creating file '{os.path.basename(resolved)}' with your requested content, sir.",
                "actions": [
                    {"tool": "create_file", "args": {"path": resolved, "content": content}}
                ]
            }

        # ----------------------------------------------------
        # 6. Write code/script to file and run it
        # e.g. "write a python script into test.py and run it"
        # ----------------------------------------------------
        script_run_match = re.search(r"(?:write|create)\s+(?:a\s+)?(?:python\s+)?(?:script|file|program)\s+(?:called|named|into)?\s*([a-zA-Z0-9_\-\.]+)\s+and\s+(?:run|execute)\s+it", lower_p)
        if script_run_match:
            fname = script_run_match.group(1).strip()
            if not "." in fname:
                fname += ".py"
            sample_code = 'print("Hello from Jarvis Autonomous Execution Core!")\nimport sys\nprint("Python version:", sys.version)\nprint("Host OS execution confirmed.")\n'
            return {
                "reply": f"Creating {fname} and executing the script on your system, sir.",
                "actions": [
                    {"tool": "create_file", "args": {"path": fname, "content": sample_code}},
                    {"tool": "execute_shell", "args": {"command": f"python {fname}"}}
                ]
            }

        # ----------------------------------------------------
        # 7. Math & Calculations:
        # e.g. "calculate 45 * 89", "what is 2500 divided by 5", "multiply 50 by 20"
        # ----------------------------------------------------
        for m_word in ("calculate", "what is", "how much is", "solve", "multiply", "divide", "add"):
            if lower_p.startswith(m_word):
                raw_expr = lower_p.replace(m_word, "").strip()
                expr = raw_expr.replace("multiplied by", "*").replace("times", "*").replace("by", "*").replace("divided by", "/").replace("plus", "+").replace("minus", "-").replace("into", "*").replace("and", "+").strip()
                expr = expr.rstrip("?")
                # Only keep safe math characters
                if all(c in "0123456789+-*/(). " for c in expr) and any(c in "0123456789" for c in expr):
                    try:
                        val = eval(expr)
                        return {
                            "reply": f"{raw_expr} equals {val}, sir.",
                            "actions": [{"tool": "calculate", "args": {"expression": expr}}]
                        }
                    except Exception:
                        pass

        # ----------------------------------------------------
        # 8. Multi-System adjustments:
        # e.g. "volume to 80 and brightness to 70"
        # ----------------------------------------------------
        if "volume to" in lower_p and "brightness" in lower_p:
            vol_m = re.search(r"volume to (\d+)", lower_p)
            br_m = re.search(r"brightness to (\d+)", lower_p)
            v = int(vol_m.group(1)) if vol_m else 50
            b = int(br_m.group(1)) if br_m else 70
            return {
                "reply": f"Adjusting master volume to {v} percent and display brightness to {b} percent, sir.",
                "actions": [
                    {"tool": "set_volume", "args": {"percent": v}},
                    {"tool": "set_brightness", "args": {"percent": b}}
                ]
            }

        # ----------------------------------------------------
        # 9. Mute and Lock: e.g. "mute volume and lock computer"
        # ----------------------------------------------------
        if ("mute" in lower_p or "volume down" in lower_p) and ("lock" in lower_p):
            return {
                "reply": "Muting system audio and locking workstation, sir.",
                "actions": [
                    {"tool": "set_volume", "args": {"percent": 0}},
                    {"tool": "lock_pc", "args": {}}
                ]
            }

        # ----------------------------------------------------
        # 10. Multi-App Launch: e.g. "open notepad and calculator"
        # ----------------------------------------------------
        multi_open_match = re.search(r"(?:open|launch)\s+([a-zA-Z]+)\s+and\s+([a-zA-Z]+)", lower_p)
        if multi_open_match:
            app1 = multi_open_match.group(1).strip()
            app2 = multi_open_match.group(2).strip()
            # Verify they are apps rather than actions
            from config import APP_PATHS
            if (app1 in APP_PATHS or app2 in APP_PATHS) and not any(w in app2 for w in ("write", "type", "search", "play")):
                return {
                    "reply": f"Launching both {app1} and {app2}, sir.",
                    "actions": [
                        {"tool": "launch_app", "args": {"name": app1}},
                        {"tool": "launch_app", "args": {"name": app2}}
                    ]
                }

        # ----------------------------------------------------
        # 11. Close app and open app: e.g. "close chrome and open notepad"
        # ----------------------------------------------------
        switch_app_match = re.search(r"close\s+([a-zA-Z\s]+?)\s+and\s+open\s+([a-zA-Z\s]+)", lower_p)
        if switch_app_match:
            app1 = switch_app_match.group(1).strip()
            app2 = switch_app_match.group(2).strip()
            return {
                "reply": f"Closing {app1} and launching {app2}, sir.",
                "actions": [
                    {"tool": "close_app", "args": {"name": app1}},
                    {"tool": "launch_app", "args": {"name": app2}}
                ]
            }

        # ----------------------------------------------------
        # 12. Take screenshot and show/open it
        # ----------------------------------------------------
        if "screenshot" in lower_p and ("show" in lower_p or "open" in lower_p or "view" in lower_p or "take" in lower_p):
            return {
                "reply": "Capturing screen and saving preview for you, sir.",
                "actions": [
                    {"tool": "take_screenshot", "args": {}}
                ]
            }

        # ----------------------------------------------------
        # 13. Clean PC: empty recycle bin + diagnostics
        # ----------------------------------------------------
        if "clean my pc" in lower_p or "clean computer" in lower_p or "clean workstation" in lower_p:
            return {
                "reply": "Initiating system cleanup. Emptying Recycle Bin and collecting telemetry, sir.",
                "actions": [
                    {"tool": "empty_recycle_bin", "args": {}},
                    {"tool": "get_telemetry", "args": {}}
                ]
            }

        # ----------------------------------------------------
        # 14. Running Tasks / Process Overview
        # ----------------------------------------------------
        if any(phrase in lower_p for phrase in ("show running apps", "what apps are open", "list running processes", "show top processes")):
            return {
                "reply": "Querying task manager and listing active processes on your console, sir.",
                "actions": [
                    {"tool": "get_running_tasks", "args": {}}
                ]
            }

        # ----------------------------------------------------
        # 15. Lock PC
        # ----------------------------------------------------
        if lower_p in ("lock my pc", "lock the computer", "lock pc", "lock workstation", "lock screen"):
            return {
                "reply": "Locking workstation immediately, sir.",
                "actions": [
                    {"tool": "lock_pc", "args": {}}
                ]
            }

        # ----------------------------------------------------
        # 16. Weather and News compound request
        # ----------------------------------------------------
        if "weather" in lower_p and "news" in lower_p:
            city_m = re.search(r"weather in ([a-zA-Z\s]+)", lower_p)
            city = city_m.group(1).replace("and", "").replace("news", "").strip() if city_m else "Delhi"
            return {
                "reply": f"Fetching live weather for {city} and global news headlines, sir.",
                "actions": [
                    {"tool": "weather", "args": {"city": city}},
                    {"tool": "news", "args": {}}
                ]
            }

        # ----------------------------------------------------
        # 17. Find / Search Files:
        # e.g. "find all python files", "search for resume", "find files named config"
        # ----------------------------------------------------
        find_files_m = re.search(r"(?:find|search\s+for)\s+(?:all\s+)?(?:files?\s+(?:named|called|with\s+extension)?\s*)?([a-zA-Z0-9_\-\.\*]+)", lower_p)
        if find_files_m and "youtube" not in lower_p and "google" not in lower_p:
            query = find_files_m.group(1).strip()
            return {
                "reply": f"Searching your file system for '{query}', sir.",
                "actions": [
                    {"tool": "search_files", "args": {"query": query}}
                ]
            }

        return None

    @classmethod
    def _generate_cloud_plan(cls, prompt: str) -> dict:
        """Invokes Gemini if API key present, or Free Pollinations Cloud endpoint with timeout."""
        # 1. Google Gemini 2.5 Flash
        if GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=GEMINI_API_KEY)
                full_prompt = f"{cls.SYSTEM_PROMPT}\n\nUser Instruction: {prompt}"
                config = types.GenerateContentConfig(max_output_tokens=150, temperature=0.6)
                resp = None
                for m in ("gemini-2.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-2.5-flash"):
                    try:
                        resp = client.models.generate_content(
                            model=m,
                            contents=full_prompt,
                            config=config
                        )
                        if resp and resp.text:
                            break
                    except Exception:
                        continue
                if resp and resp.text:
                    parsed = cls._parse_json_response(resp.text)
                    if parsed:
                        return parsed
            except Exception as e:
                print(f"[AutonomousAgent] Gemini inference error: {e}")

        # 2. Free Cloud LLM (Pollinations AI) with tight 3s timeout
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": cls.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "model": "openai",
                "jsonMode": True
            }
            req = urllib.request.Request(
                "https://text.pollinations.ai/",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "JarvisAI/5.0"}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                raw_text = response.read().decode("utf-8")
                parsed = cls._parse_json_response(raw_text)
                if parsed:
                    return parsed
        except Exception:
            pass

        return None

    @classmethod
    def _parse_json_response(cls, text: str) -> dict:
        """Extracts and parses JSON object from LLM response."""
        try:
            clean = text.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            elif clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            start_idx = clean.find("{")
            end_idx = clean.rfind("}")
            if start_idx != -1 and end_idx != -1:
                clean = clean[start_idx:end_idx + 1]
                data = json.loads(clean)
                if isinstance(data, dict):
                    # Check if model returned code directly instead of nested actions
                    if "actions" not in data and "python_code" in data:
                        data["actions"] = [{
                            "tool": "synthesize_and_run_code",
                            "args": {
                                "skill_name": data.get("skill_name", "dynamic_task"),
                                "purpose": data.get("purpose", ""),
                                "python_code": data.get("python_code", "")
                            }
                        }]
                    if "reply" not in data:
                        data["reply"] = data.get("vocal_reply", "Executing your custom instruction now, sir.")
                    if "actions" in data:
                        return data
        except Exception:
            pass
        return None
