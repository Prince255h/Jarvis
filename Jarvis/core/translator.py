import re
import os
import json
import time
import urllib.request
import urllib.parse
from config import GEMINI_API_KEY, LANGUAGE_VOICES

class TranslatorEngine:
    """
    STARK INDUSTRIES // UNIVERSAL NEURAL TRANSLATION & INTERPRETATION ENGINE
    Empowers J.A.R.V.I.S. to:
    - Automatically detect and understand 100+ global languages natively
    - Perform context-aware, idiomatic, human-like real-time translation
    - Provide phonetic transliteration & pronunciation guides for non-Latin scripts
    - Act as a live simultaneous interpreter between any two languages
    - Translate clipboard, documents, and natural voice dialogue
    """

    # Language name to code mapping
    LANGUAGE_CODES = {
        "english": "en", "en": "en",
        "hindi": "hi", "hi": "hi",
        "spanish": "es", "es": "es",
        "french": "fr", "fr": "fr",
        "german": "de", "de": "de",
        "japanese": "ja", "ja": "ja",
        "italian": "it", "it": "it",
        "russian": "ru", "ru": "ru",
        "chinese": "zh", "mandarin": "zh", "zh": "zh",
        "arabic": "ar", "ar": "ar",
        "portuguese": "pt", "pt": "pt",
        "korean": "ko", "ko": "ko",
        "bengali": "bn", "bn": "bn",
        "telugu": "te", "te": "te",
        "tamil": "ta", "ta": "ta",
        "marathi": "mr", "mr": "mr",
        "gujarati": "gu", "gu": "gu",
        "urdu": "ur", "ur": "ur",
        "turkish": "tr", "tr": "tr",
        "dutch": "nl", "nl": "nl",
        "greek": "el", "el": "el",
        "latin": "la", "la": "la",
        "vietnamese": "vi", "vi": "vi",
        "thai": "th", "th": "th",
        "indonesian": "id", "id": "id",
        "hebrew": "he", "he": "he",
        "polish": "pl", "pl": "pl",
        "swedish": "sv", "sv": "sv"
    }

    LANGUAGE_NAMES = {
        "en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French",
        "de": "German", "ja": "Japanese", "it": "Italian", "ru": "Russian",
        "zh": "Chinese", "ar": "Arabic", "pt": "Portuguese", "ko": "Korean",
        "bn": "Bengali", "te": "Telugu", "ta": "Tamil", "mr": "Marathi",
        "gu": "Gujarati", "ur": "Urdu", "tr": "Turkish", "nl": "Dutch",
        "el": "Greek", "la": "Latin", "vi": "Vietnamese", "th": "Thai",
        "id": "Indonesian", "he": "Hebrew", "pl": "Polish", "sv": "Swedish"
    }

    # Live bilateral translation session state
    is_live_mode = False
    live_lang_a = "en"
    live_lang_b = "es"

    @classmethod
    def normalize_lang(cls, lang_input: str) -> str:
        """Resolves language name or abbreviation to standardized ISO code."""
        if not lang_input:
            return "en"
        cleaned = lang_input.strip().lower()
        return cls.LANGUAGE_CODES.get(cleaned, cleaned[:2])

    @classmethod
    def get_lang_name(cls, code: str) -> str:
        return cls.LANGUAGE_NAMES.get(code.lower(), code.capitalize())

    @classmethod
    def detect_script(cls, text: str) -> str:
        """Fast offline heuristic script detection."""
        for char in text:
            cp = ord(char)
            if 0x0900 <= cp <= 0x097F:
                return "hi"  # Devanagari (Hindi/Marathi)
            elif 0x3040 <= cp <= 0x30FF or 0x4E00 <= cp <= 0x9FFF:
                return "ja"  # Japanese / Kanji
            elif 0x0400 <= cp <= 0x04FF:
                return "ru"  # Cyrillic
            elif 0x0600 <= cp <= 0x06FF:
                return "ar"  # Arabic / Urdu
            elif 0xAC00 <= cp <= 0xD7AF:
                return "ko"  # Hangul (Korean)
            elif 0x0980 <= cp <= 0x09FF:
                return "bn"  # Bengali
            elif 0x0C00 <= cp <= 0x0C7F:
                return "te"  # Telugu
            elif 0x0B80 <= cp <= 0x0BFF:
                return "ta"  # Tamil
            elif 0x0A80 <= cp <= 0x0AFF:
                return "gu"  # Gujarati
        return "en"

    @classmethod
    def translate(cls, text: str, target_lang: str = "en", source_lang: str = "auto") -> dict:
        """
        Universal Translation Pipeline:
        1. Queries Gemini 2.5 Flash for nuanced, human-level idiomatic translation.
        2. Generates phonetic romanization for non-Latin target scripts.
        3. Falls back to free neural web API / local phrasebook if offline.
        """
        if not text or not text.strip():
            return {
                "success": False,
                "translated_text": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "reply": "No text provided for translation, sir."
            }

        text = text.strip()
        target_code = cls.normalize_lang(target_lang)
        source_code = cls.normalize_lang(source_lang) if source_lang != "auto" else "auto"
        target_name = cls.get_lang_name(target_code)

        # 1. Primary Neural Translation via Google Gemini
        gemini_result = cls._translate_with_gemini(text, target_code, target_name, source_code)
        if gemini_result:
            return gemini_result

        # 2. Secondary Neural Web Fallback (MyMemory / LibreTranslate REST API)
        web_result = cls._translate_with_web_api(text, target_code, source_code)
        if web_result:
            return web_result

        # 3. Offline Dictionary Phrasebook Fallback
        return cls._translate_offline_phrasebook(text, target_code)

    @classmethod
    def _translate_with_gemini(cls, text: str, target_code: str, target_name: str, source_code: str) -> dict:
        """High-precision translation using Google Gemini with cultural nuance and phonetics."""
        import os
        import config
        from core.agent import AutonomousAgent
        api_key = AutonomousAgent.get_api_key()
        if not api_key:
            return None

        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)

            prompt = f"""You are J.A.R.V.I.S.'s high-precision neural translation module.
Translate the following text into {target_name} ({target_code}).
Source language: {source_code if source_code != 'auto' else 'Auto-detect'}.

Requirements:
1. Provide a natural, fluent, human translation maintaining the exact tone, nuance, and emotion.
2. If the target language uses non-Latin script (like Hindi, Japanese, Russian, Arabic, Chinese, Korean), provide an accurate Romanized/phonetic pronunciation in English characters.
3. Identify the detected source language name.

Output STRICT JSON:
{{
  "detected_source": "Language Name",
  "detected_source_code": "two-letter-code",
  "translated_text": "The exact translated text in target script",
  "phonetic": "Romanized pronunciation guide (or empty if target uses Latin alphabet)",
  "cultural_note": "Brief nuance tip if relevant (optional)"
}}
Do NOT output markdown fences.

Text to translate:
\"\"\"{text}\"\"\""""

            config_gen = types.GenerateContentConfig(
                max_output_tokens=350,
                temperature=0.2
            )

            resp = None
            for m_name in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
                try:
                    resp = client.models.generate_content(
                        model=m_name,
                        contents=prompt,
                        config=config_gen
                    )
                    if resp and resp.text:
                        break
                except Exception:
                    continue

            if resp and resp.text:
                clean = resp.text.strip()
                if clean.startswith("```json"):
                    clean = clean[7:]
                elif clean.startswith("```"):
                    clean = clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()

                start_idx = clean.find("{")
                end_idx = clean.rfind("}")
                data = {}
                if start_idx != -1 and end_idx != -1:
                    json_str = clean[start_idx:end_idx + 1]
                    try:
                        data = json.loads(json_str)
                    except Exception:
                        tr_m = re.search(r'"translated_text"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', json_str)
                        src_m = re.search(r'"detected_source"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', json_str)
                        code_m = re.search(r'"detected_source_code"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', json_str)
                        pho_m = re.search(r'"phonetic"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', json_str)
                        data = {
                            "translated_text": tr_m.group(1) if tr_m else "",
                            "detected_source": src_m.group(1) if src_m else "Auto-detected",
                            "detected_source_code": code_m.group(1) if code_m else "auto",
                            "phonetic": pho_m.group(1) if pho_m else ""
                        }

                translated = data.get("translated_text", "").strip()
                if not translated:
                    # If empty, return None to trigger web/offline fallback
                    return None

                detected_src = data.get("detected_source", "Auto-detected")
                detected_code = data.get("detected_source_code", "auto")
                phonetic = data.get("phonetic", "").strip()

                reply_voice = f"In {target_name}: {phonetic if phonetic and target_code in ('hi', 'ja', 'zh', 'ru', 'ar', 'ko') else translated}"

                term_out = (
                    f"[◈ UNIVERSAL NEURAL TRANSLATOR // STARK OS 5.0]\n"
                    f"• Source [{detected_src}]: {text}\n"
                    f"• Target [{target_name}]: {translated}\n"
                )
                if phonetic:
                    term_out += f"• Phonetic / Pronunciation: {phonetic}\n"

                return {
                    "success": True,
                    "original_text": text,
                    "translated_text": translated,
                    "phonetic": phonetic,
                    "source_lang": detected_code,
                    "source_lang_name": detected_src,
                    "target_lang": target_code,
                    "target_lang_name": target_name,
                    "reply": reply_voice,
                    "terminal_output": term_out
                }
        except Exception as e:
            print(f"[TranslatorEngine] Gemini translation error: {e}")
            return None

    @classmethod
    def _translate_with_web_api(cls, text: str, target_code: str, source_code: str) -> dict:
        """Fast public REST translation fallback."""
        try:
            s_code = source_code if source_code != "auto" else cls.detect_script(text)
            encoded_q = urllib.parse.quote(text)
            url = f"https://api.mymemory.translated.net/get?q={encoded_q}&langpair={s_code}|{target_code}"
            req = urllib.request.Request(url, headers={'User-Agent': 'JarvisAssistant/1.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                res_data = data.get("responseData", {})
                translated = res_data.get("translatedText", "")
                if translated and translated.lower() != text.lower():
                    target_name = cls.get_lang_name(target_code)
                    source_name = cls.get_lang_name(s_code)
                    return {
                        "success": True,
                        "original_text": text,
                        "translated_text": translated,
                        "phonetic": "",
                        "source_lang": s_code,
                        "source_lang_name": source_name,
                        "target_lang": target_code,
                        "target_lang_name": target_name,
                        "reply": f"In {target_name}: {translated}",
                        "terminal_output": f"[TRANSLATOR FALLBACK]\n• From ({source_name}): {text}\n• To ({target_name}): {translated}\n"
                    }
        except Exception as e:
            print(f"[TranslatorEngine] Web API translation error: {e}")
        return None

    @classmethod
    def _translate_offline_phrasebook(cls, text: str, target_code: str) -> dict:
        """Zero-latency offline phrasebook for common conversational expressions."""
        t_lower = text.lower().strip()
        target_name = cls.get_lang_name(target_code)
        
        phrasebook = {
            "hello": {"hi": "नमस्ते (Namaste)", "es": "Hola", "fr": "Bonjour", "de": "Hallo", "ja": "こんにちは (Konnichiwa)", "ru": "Привет (Privet)", "it": "Ciao"},
            "how are you": {"hi": "आप कैसे हैं? (Aap kaise hain?)", "es": "¿Cómo estás?", "fr": "Comment allez-vous?", "de": "Wie geht es Ihnen?", "ja": "お元気ですか (Ogenki desu ka)", "ru": "Как дела? (Kak dela?)", "it": "Come stai?"},
            "thank you": {"hi": "धन्यवाद (Dhanyawad)", "es": "Gracias", "fr": "Merci", "de": "Danke", "ja": "ありがとう (Arigatou)", "ru": "Спасибо (Spasibo)", "it": "Grazie"},
            "good morning": {"hi": "सुप्रभात (Suprabhat)", "es": "Buenos días", "fr": "Bonjour", "de": "Guten Morgen", "ja": "おはようございます (Ohayou gozaimasu)", "ru": "Доброе утро (Dobroye utro)", "it": "Buongiorno"},
            "good night": {"hi": "शुभ रात्रि (Shubh Ratri)", "es": "Buenas noches", "fr": "Bonne nuit", "de": "Gute Nacht", "ja": "おやすみなさい (Oyasuminasai)", "ru": "Спокойной ночи (Spokoynoy nochi)", "it": "Buonanotte"},
            "yes": {"hi": "हाँ (Haan)", "es": "Sí", "fr": "Oui", "de": "Ja", "ja": "はい (Hai)", "ru": "Да (Da)", "it": "Sì"},
            "no": {"hi": "नहीं (Nahi)", "es": "No", "fr": "Non", "de": "Nein", "ja": "いいえ (Iie)", "ru": "Нет (Net)", "it": "No"},
            "i love you": {"hi": "मैं तुमसे प्यार करता हूँ (Main tumse pyar karta hoon)", "es": "Te amo", "fr": "Je t'aime", "de": "Ich liebe dich", "ja": "愛してる (Aishiteru)", "ru": "Я тебя люблю (Ya tebya lyublyu)", "it": "Ti amo"}
        }

        matched = phrasebook.get(t_lower, {}).get(target_code)
        if matched:
            return {
                "success": True,
                "original_text": text,
                "translated_text": matched,
                "phonetic": "",
                "source_lang": "en",
                "source_lang_name": "English",
                "target_lang": target_code,
                "target_lang_name": target_name,
                "reply": f"In {target_name}, '{text}' is: {matched}",
                "terminal_output": f"[OFFLINE PHRASEBOOK]\n• English: {text}\n• {target_name}: {matched}\n"
            }

        return {
            "success": False,
            "original_text": text,
            "translated_text": text,
            "phonetic": "",
            "source_lang": "auto",
            "source_lang_name": "Auto",
            "target_lang": target_code,
            "target_lang_name": target_name,
            "reply": f"To translate '{text}' to {target_name} with full vocabulary, please connect your Gemini API key, sir.",
            "terminal_output": f"[TRANSLATION ALERT] Offline dictionary could not find translation for '{text}'. Activate Gemini key for 100+ language support.\n"
        }

    @classmethod
    def handle_intent(cls, query: str) -> dict:
        """
        Detects if user is asking for a translation or interpreter protocol.
        Examples:
        - "Jarvis translate I am happy into Spanish"
        - "Translate this into Hindi: Where is the nearest train station?"
        - "How do you say good morning in Japanese?"
        - "What does bonjour mean in English?"
        - "Translate clipboard to French"
        - "Be my translator between English and Spanish"
        - "Start live translator mode"
        - "Stop translator mode"
        """
        raw = query.strip()
        lower = raw.lower()

        # 1. Stop Live Translator
        if cls.is_live_mode and any(w in lower for w in ("stop translation", "stop translator", "exit translator", "end translation", "stop translating")):
            cls.is_live_mode = False
            reply = "Live translation mode deactivated, sir. Normal Jarvis operating protocol restored."
            return {
                "action": "translator_mode_stop",
                "reply": reply,
                "terminal_output": "[LIVE TRANSLATOR] Deactivated. Subsystems returning to standard command mode.\n"
            }

        # 2. Start Live Interpreter / Translator Mode
        live_match = (
            re.search(r"(?:be\s+my\s+translator|start\s+(?:live\s+)?translator(?:\s+mode)?)\s+(?:between\s+)?([a-zA-Z]+)\s+and\s+([a-zA-Z]+)", lower) or
            re.search(r"translate\s+between\s+([a-zA-Z]+)\s+and\s+([a-zA-Z]+)", lower)
        )
        if live_match:
            lang_1 = live_match.group(1).strip()
            lang_2 = live_match.group(2).strip()
            cls.is_live_mode = True
            cls.live_lang_a = cls.normalize_lang(lang_1)
            cls.live_lang_b = cls.normalize_lang(lang_2)
            name_a = cls.get_lang_name(cls.live_lang_a)
            name_b = cls.get_lang_name(cls.live_lang_b)
            reply = f"Live bilateral translation active between {name_a} and {name_b}, sir. Speak naturally, and I shall translate both ways in real time."
            return {
                "action": "translator_mode_start",
                "reply": reply,
                "terminal_output": f"[LIVE SIMULTANEOUS INTERPRETER]\n• Language A: {name_a} ({cls.live_lang_a})\n• Language B: {name_b} ({cls.live_lang_b})\n• Status: ACTIVE\n"
            }

        # If already in live mode, intercept everything as translation!
        if cls.is_live_mode:
            # Detect script or language of input to route to opposite language
            detected = cls.detect_script(raw)
            target = cls.live_lang_b if detected == cls.live_lang_a or detected == "en" else cls.live_lang_a
            res = cls.translate(raw, target_lang=target, source_lang="auto")
            res["action"] = "live_translation"
            return res

        # 3. Clipboard Translation
        if "translate clipboard" in lower or "translate my clipboard" in lower:
            target_lang = "en"
            m = re.search(r"(?:to|in|into)\s+([a-zA-Z]+)", lower)
            if m:
                target_lang = m.group(1).strip()
            from automation.computer_control import ComputerControl
            clip_text = ComputerControl.clipboard_paste()
            if not clip_text or not clip_text.strip():
                reply = "Your clipboard is currently empty, sir."
                return {"action": "translate_clip_empty", "reply": reply}
            res = cls.translate(clip_text.strip(), target_lang=target_lang)
            res["action"] = "translate_clipboard"
            return res

        # 4. Pattern: "How do you say [phrase] in [target]" or "what is [phrase] in [target]"
        say_m = (
            re.search(r"how\s+(?:do\s+you\s+)?say\s+[\"']?(.+?)[\"']?\s+(?:in|into)\s+([a-zA-Z]+)\b", lower) or
            re.search(r"what\s+(?:is|does)\s+[\"']?(.+?)[\"']?\s+(?:mean\s+)?(?:in|into)\s+([a-zA-Z]+)\b", lower)
        )
        if say_m:
            phrase = say_m.group(1).strip()
            target = say_m.group(2).strip()
            res = cls.translate(phrase, target_lang=target)
            res["action"] = "translate_phrase"
            return res

        # 5. Pattern: "Translate [phrase] to/into [target]" or "Translate into [target]: [phrase]"
        trans_m1 = re.search(r"translate\s+[\"']?(.+?)[\"']?\s+(?:to|in|into)\s+([a-zA-Z]+)\b", lower)
        if trans_m1:
            phrase = trans_m1.group(1).strip()
            target = trans_m1.group(2).strip()
            # Handle possible reversed match if user said "translate into spanish: hello"
            if phrase.startswith("into ") or phrase.startswith("to "):
                parts = phrase.split(maxsplit=2)
                if len(parts) >= 2:
                    target = parts[1]
                    phrase = parts[2] if len(parts) > 2 else ""
            res = cls.translate(phrase, target_lang=target)
            res["action"] = "translate_text"
            return res

        trans_m2 = re.search(r"translate\s+(?:to|into|in)\s+([a-zA-Z]+)[\s:,]+(.+)", lower)
        if trans_m2:
            target = trans_m2.group(1).strip()
            phrase = trans_m2.group(2).strip()
            res = cls.translate(phrase, target_lang=target)
            res["action"] = "translate_text"
            return res

        # 6. Direct meaning check: "What does [phrase] mean" (defaults to English target)
        mean_m = re.search(r"what\s+does\s+[\"']?(.+?)[\"']?\s+mean(?:\s+in\s+english)?\b", lower)
        if mean_m:
            phrase = mean_m.group(1).strip()
            res = cls.translate(phrase, target_lang="en")
            res["action"] = "translate_meaning"
            return res

        return None
