import os
import sys
import json
import time
import re
import subprocess
from datetime import datetime

# Ensure base dir in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

class SkillSynthesizer:
    """
    STARK INDUSTRIES OS 5.1 // JUST-IN-TIME DYNAMIC CODE SYNTHESIZER
    Enables Jarvis to dynamically generate and execute custom code on-the-fly:
    - If user asks for an action that has no existing function, Jarvis writes the function in Python
    - Executes the code immediately in a secure child subprocess with live stdout/stderr capture
    - Self-healing: If the synthesized code encounters an exception, it auto-repairs via Gemini
    - Persistent Skill Vault: Automatically saves synthesized skills in data/custom_skills/
    """
    SKILLS_DIR = os.path.join(BASE_DIR, "data", "custom_skills")
    MANIFEST_FILE = os.path.join(SKILLS_DIR, "manifest.json")

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.SKILLS_DIR, exist_ok=True)
        if not os.path.exists(cls.MANIFEST_FILE):
            try:
                with open(cls.MANIFEST_FILE, "w", encoding="utf-8") as f:
                    json.dump({"skills": {}, "last_updated": datetime.now().isoformat()}, f, indent=4)
            except Exception:
                pass

    @classmethod
    def clean_python_code(cls, code: str) -> str:
        """Strips markdown code blocks, backticks, and extraneous text from LLM code generation."""
        c = code.strip()
        # Extract from ```python ... ``` if wrapped
        match = re.search(r"```(?:python)?\s*([\s\S]*?)```", c, re.IGNORECASE)
        if match:
            c = match.group(1).strip()
        elif c.startswith("```") and c.endswith("```"):
            c = c[3:-3].strip()
        return c

    @classmethod
    def execute_code(cls, python_code: str, skill_name: str = "custom_task", purpose: str = "", timeout: int = 40, auto_repair: bool = True) -> dict:
        """
        Saves and executes Python code in a dedicated child process.
        Returns execution result, output text, and status.
        """
        cls._ensure_dir()
        cleaned_code = cls.clean_python_code(python_code)
        if not cleaned_code:
            return {
                "success": False,
                "output": "No executable code provided.",
                "skill_name": skill_name
            }

        # Normalize skill filename
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", skill_name.strip().lower())
        if not safe_name or safe_name == "_":
            safe_name = f"skill_{int(time.time())}"
        
        script_path = os.path.join(cls.SKILLS_DIR, f"{safe_name}.py")

        # Add UTF-8 stdout configuration header if missing
        header = (
            "# STARK INDUSTRIES DYNAMICALLY SYNTHESIZED SKILL\n"
            "# Created: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
            "# Purpose: " + (purpose or skill_name) + "\n\n"
            "import sys, os\n"
            "if hasattr(sys.stdout, 'reconfigure'):\n"
            "    try: sys.stdout.reconfigure(encoding='utf-8')\n"
            "    except Exception: pass\n\n"
        )
        full_code = header + cleaned_code

        # Save to skill vault
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(full_code)
        except Exception as e:
            return {"success": False, "output": f"Failed to save skill script: {e}", "skill_name": safe_name}

        print(f"[SkillSynthesizer] Executing dynamic skill '{safe_name}'...")
        t0 = time.time()
        
        # Execute using current Python 3.12 interpreter
        python_exe = sys.executable or "python"
        try:
            proc = subprocess.Popen(
                [python_exe, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=BASE_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            stdout, stderr = proc.communicate(timeout=timeout)
            duration_ms = (time.time() - t0) * 1000
            success = (proc.returncode == 0)

            combined_out = ""
            if stdout and stdout.strip():
                combined_out += stdout.strip()
            if stderr and stderr.strip():
                if combined_out:
                    combined_out += "\n[Runtime Warnings / Error Details]:\n"
                combined_out += stderr.strip()

            if not combined_out:
                combined_out = f"Skill executed successfully in {duration_ms:.0f}ms with zero output."

            # Self-healing if execution failed and auto_repair is active
            if not success and auto_repair and ("error" in combined_out.lower() or "traceback" in combined_out.lower()):
                print(f"[SkillSynthesizer] Dynamic skill '{safe_name}' had a runtime error. Initiating self-healing...")
                repaired = cls._auto_repair(cleaned_code, combined_out, safe_name, purpose)
                if repaired and repaired.get("success"):
                    return repaired

            # Update manifest
            cls._record_skill(safe_name, purpose, script_path, success)

            return {
                "success": success,
                "output": combined_out,
                "skill_name": safe_name,
                "script_path": script_path,
                "duration_ms": duration_ms,
                "returncode": proc.returncode
            }

        except subprocess.TimeoutExpired:
            proc.kill()
            return {
                "success": False,
                "output": f"Execution timed out after {timeout} seconds.",
                "skill_name": safe_name
            }
        except Exception as e:
            return {
                "success": False,
                "output": f"Subprocess execution error: {str(e)}",
                "skill_name": safe_name
            }

    @classmethod
    def _auto_repair(cls, failed_code: str, error_msg: str, skill_name: str, purpose: str) -> dict:
        """Self-healing: Uses Gemini to automatically correct runtime bugs and syntax errors."""
        try:
            from core.agent import AutonomousAgent
            api_key = AutonomousAgent.get_api_key()
            if not api_key:
                return None
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            prompt = (
                f"You are J.A.R.V.I.S.'s self-healing code debugger. The following Windows Python 3.12 script failed:\n"
                f"--- SCRIPT ---\n{failed_code}\n\n"
                f"--- RUNTIME ERROR ---\n{error_msg}\n\n"
                f"Fix the bug completely. Return STRICT JSON with key 'python_code' containing the fixed runnable code."
            )
            config = types.GenerateContentConfig(
                max_output_tokens=3000,
                temperature=0.2,
                response_mime_type="application/json"
            )
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            if resp and resp.text:
                raw = resp.text.strip()
                data = json.loads(raw)
                fixed_code = data.get("python_code")
                if fixed_code:
                    print(f"[SkillSynthesizer] Self-healing generated fix for '{skill_name}'. Re-executing...")
                    return cls.execute_code(fixed_code, skill_name=skill_name, purpose=purpose, auto_repair=False)
        except Exception as e:
            print(f"[SkillSynthesizer] Auto-repair exception: {e}")
        return None

    @classmethod
    def _record_skill(cls, name: str, purpose: str, path: str, success: bool):
        try:
            data = {"skills": {}}
            if os.path.exists(cls.MANIFEST_FILE):
                with open(cls.MANIFEST_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data.setdefault("skills", {})[name] = {
                "purpose": purpose,
                "path": path,
                "last_run": datetime.now().isoformat(),
                "last_success": success
            }
            data["last_updated"] = datetime.now().isoformat()
            with open(cls.MANIFEST_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    @classmethod
    def synthesize_and_execute(cls, user_prompt: str, skill_name: str = None) -> dict:
        """
        Deep Neural Code Synthesis via Google Gemini:
        1. Analyzes the user's prompt
        2. Writes a complete Python script to execute the task on Windows
        3. Executes the script immediately
        4. If it fails, performs 1 self-healing auto-repair cycle
        """
        from core.agent import AutonomousAgent
        api_key = AutonomousAgent.get_api_key()
        if not api_key:
            return {
                "success": False,
                "reply": "I cannot synthesize custom code without an active Gemini neural connection, sir.",
                "terminal_output": "[ALERT] Gemini API key required for dynamic code synthesis.\n"
            }

        clean_prompt = user_prompt.strip()
        print(f"[SkillSynthesizer] Synthesizing custom function for: '{clean_prompt}'")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            system_instruction = (
                "You are J.A.R.V.I.S., Tony Stark's autonomous AI assistant and master software architect. "
                "The user gave you an instruction on their Windows PC for which no standard function exists. "
                "You must write complete, production-ready, clean Python 3 code that accomplishes their exact goal.\n\n"
                "ENVIRONMENT RULES:\n"
                "- Operating System: Windows 11\n"
                "- Python 3.12 64-bit\n"
                "- Available Libraries: os, sys, subprocess, shutil, psutil, pyautogui, pygame, requests, urllib, json, math, datetime, re, ctypes, time, glob, pathlib, etc.\n"
                "- The script must be completely self-contained and runnable directly.\n"
                "- Always print clear, informative progress or final results to stdout.\n\n"
                "OUTPUT FORMAT: Return STRICT valid JSON with NO surrounding markdown fences:\n"
                "{\n"
                "  \"skill_name\": \"short_descriptive_snake_case_name\",\n"
                "  \"purpose\": \"one sentence describing what this does\",\n"
                "  \"python_code\": \"complete executable python code with newlines and escapes\",\n"
                "  \"vocal_reply\": \"Crisp, natural 1-2 sentence response addressing user as 'sir' reporting the execution\"\n"
                "}"
            )

            prompt_content = f"User Request: {clean_prompt}\nSynthesize and generate the complete Python solution now:"

            config = types.GenerateContentConfig(
                max_output_tokens=3500,
                temperature=0.2,
                response_mime_type="application/json"
            )

            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{system_instruction}\n\n{prompt_content}",
                config=config
            )

            if not resp or not resp.text:
                return {
                    "success": False,
                    "reply": "I was unable to synthesize code for that request, sir.",
                    "terminal_output": "[ERROR] Empty response from code generator.\n"
                }

            # Parse JSON
            raw_text = resp.text.strip()
            # Clean JSON if fences present
            if "```" in raw_text:
                m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text)
                if m:
                    raw_text = m.group(1).strip()

            parsed = None
            try:
                parsed = json.loads(raw_text)
            except Exception:
                # Find outermost { ... }
                s = raw_text.find("{")
                e = raw_text.rfind("}")
                if s != -1 and e != -1:
                    try:
                        parsed = json.loads(raw_text[s:e+1])
                    except Exception:
                        pass

            if not parsed or "python_code" not in parsed:
                return {
                    "success": False,
                    "reply": "Code synthesis returned an invalid schema, sir.",
                    "terminal_output": f"[ERROR] Failed to parse generated code JSON:\n{raw_text}\n"
                }

            gen_skill_name = parsed.get("skill_name") or skill_name or "dynamic_task"
            gen_purpose = parsed.get("purpose", clean_prompt)
            gen_code = parsed.get("python_code", "")
            gen_vocal = parsed.get("vocal_reply") or f"I have synthesized and executed the function for {gen_skill_name}, sir."

            # Execute the synthesized code
            exec_res = cls.execute_code(gen_code, skill_name=gen_skill_name, purpose=gen_purpose)

            # Self-healing if execution failed
            if not exec_res.get("success") and "error" in exec_res.get("output", "").lower():
                print(f"[SkillSynthesizer] Execution failed. Attempting self-healing auto-repair...")
                repair_prompt = (
                    f"The synthesized script for '{clean_prompt}' failed with the following error output:\n"
                    f"{exec_res.get('output')}\n\n"
                    f"Original code:\n{gen_code}\n\n"
                    f"Please fix the bug and return the corrected JSON solution with working 'python_code':"
                )
                try:
                    fix_resp = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"{system_instruction}\n\n{repair_prompt}",
                        config=config
                    )
                    if fix_resp and fix_resp.text:
                        fix_raw = fix_resp.text.strip()
                        if "```" in fix_raw:
                            fm = re.search(r"```(?:json)?\s*([\s\S]*?)```", fix_raw)
                            if fm:
                                fix_raw = fm.group(1).strip()
                        fix_parsed = json.loads(fix_raw)
                        if "python_code" in fix_parsed:
                            gen_code = fix_parsed["python_code"]
                            exec_res = cls.execute_code(gen_code, skill_name=gen_skill_name, purpose=gen_purpose)
                except Exception as e:
                    print(f"[SkillSynthesizer] Self-healing error: {e}")

            out_text = exec_res.get("output", "")
            # Craft natural vocal report incorporating output summary if short
            vocal_summary = gen_vocal
            if exec_res.get("success"):
                if len(out_text.splitlines()) <= 2 and len(out_text) < 120 and not out_text.startswith("Skill executed"):
                    vocal_summary += f" The result is: {out_text}"
            else:
                vocal_summary = f"I synthesized the function for {gen_skill_name}, sir, but it encountered an error: {out_text[:80]}"

            terminal_output = (
                f"[DYNAMIC CODE SYNTHESIS & EXECUTION]\n"
                f"• Skill Name : {gen_skill_name}\n"
                f"• Purpose    : {gen_purpose}\n"
                f"• Script File: {exec_res.get('script_path', 'memory')}\n"
                f"• Status     : {'SUCCESS (0)' if exec_res.get('success') else 'FAILED'}\n"
                f"• Output     :\n{out_text}\n"
            )

            return {
                "success": exec_res.get("success", False),
                "action": "dynamic_skill_executed",
                "reply": vocal_summary,
                "terminal_output": terminal_output,
                "skill_name": gen_skill_name,
                "code": gen_code,
                "output": out_text
            }

        except Exception as e:
            return {
                "success": False,
                "reply": f"An error occurred while synthesizing that capability, sir: {str(e)}",
                "terminal_output": f"[SkillSynthesizer Error]: {e}\n"
            }
