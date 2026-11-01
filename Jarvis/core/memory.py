import os
import json
import re
import threading
from datetime import datetime

MEMORY_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "user_memory.json")

class MemoryManager:
    """
    STARK INDUSTRIES OS 5.0 // PERSISTENT LONG-TERM MEMORY ENGINE
    Replicates Astra / GPT-6 long-term episodic and semantic memory:
    - Persists user preferences, projects, purchases, and personal facts to disk
    - Recalls relevant facts into Gemini's context window across sessions
    - Autonomous background memory extraction from natural conversation
    """

    _lock = threading.Lock()

    @classmethod
    def _ensure_file(cls):
        os.makedirs(os.path.dirname(MEMORY_FILE_PATH), exist_ok=True)
        if not os.path.exists(MEMORY_FILE_PATH):
            initial_data = {
                "user_name": "Sir",
                "facts": [
                    "User is Tony Stark / creator of this Jarvis AI system.",
                    "User prefers fast, intelligent, zero-friction desktop automation."
                ],
                "preferences": {
                    "browser": "Chrome",
                    "style": "Witty, sharp, loyal Stark assistant"
                },
                "recent_topics": [],
                "last_updated": datetime.now().isoformat()
            }
            with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=4)

    @classmethod
    def load_data(cls) -> dict:
        cls._ensure_file()
        with cls._lock:
            try:
                with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"facts": [], "preferences": {}, "recent_topics": []}

    @classmethod
    def save_data(cls, data: dict):
        cls._ensure_file()
        with cls._lock:
            try:
                data["last_updated"] = datetime.now().isoformat()
                with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"[MemoryManager] Error saving memory: {e}")

    @classmethod
    def add_fact(cls, fact_str: str) -> str:
        """Adds a permanent fact or user note to long-term memory."""
        clean_fact = fact_str.strip()
        if not clean_fact:
            return "No fact provided."

        data = cls.load_data()
        facts = data.get("facts", [])
        # Check if already present
        if not any(clean_fact.lower() in f.lower() for f in facts):
            facts.append(clean_fact)
            data["facts"] = facts[-30:] # keep up to 30 most recent facts
            cls.save_data(data)
            return f"Memorized: '{clean_fact}', sir."
        return f"I already have that in my archives, sir."

    @classmethod
    def record_topic(cls, topic: str):
        """Records recent topic discussed."""
        clean_t = topic.strip()
        if not clean_t:
            return
        data = cls.load_data()
        topics = data.get("recent_topics", [])
        if clean_t not in topics:
            topics.append(clean_t)
            data["recent_topics"] = topics[-10:]
            cls.save_data(data)

    @classmethod
    def get_memory_context(cls) -> str:
        """Formats stored memory into a prompt section for Gemini."""
        data = cls.load_data()
        facts = data.get("facts", [])
        recent_topics = data.get("recent_topics", [])

        if not facts and not recent_topics:
            return ""

        lines = ["\n[USER LONG-TERM MEMORY & PERSISTENT KNOWLEDGE - You remember these facts across conversations]:"]
        for f in facts:
            lines.append(f"• {f}")
        if recent_topics:
            lines.append(f"• Recent discussion topics: {', '.join(recent_topics[-4:])}")
        lines.append("Reference these memories naturally when appropriate (just like a human companion with continuous memory).\n")
        return "\n".join(lines)

    @classmethod
    def extract_and_learn_async(cls, user_text: str, ai_reply: str):
        """Background thread to extract facts, interests, or plans from conversation."""
        threading.Thread(target=cls._extract_worker, args=(user_text, ai_reply), daemon=True).start()

    @classmethod
    def _extract_worker(cls, user_text: str, ai_reply: str):
        """Extracts facts from statements like 'I want to buy a tripod', 'my favorite video is...', etc."""
        text = user_text.lower().strip()
        
        # Check explicit patterns
        patterns = [
            (r"(?:i\s+want\s+to\s+buy|i'm\s+looking\s+for|planning\s+to\s+buy)\s+(?:a\s+|an\s+)?([a-zA-Z0-9\s]+)", "User is looking to buy {}"),
            (r"(?:my\s+favorite|i\s+love|i\s+really\s+like)\s+([a-zA-Z0-9\s]+)", "User likes {}"),
            (r"(?:call\s+me|my\s+name\s+is)\s+([a-zA-Z0-9]+)", "User's name or preferred title is {}"),
            (r"(?:i\s+am\s+working\s+on|i'm\s+building)\s+([a-zA-Z0-9\s]+)", "User is working on {}"),
        ]

        for pat, template in patterns:
            m = re.search(pat, text)
            if m:
                target = m.group(1).strip()
                if len(target) > 2 and len(target) < 60:
                    fact = template.format(target)
                    cls.add_fact(fact)
                    cls.record_topic(target)
                    return

        # If user spoke about a specific subject, record as recent topic
        words = text.split()
        if len(words) > 3:
            # Check for noun phrases like tripod, gaming, coding, fukra insaan
            for kw in ("tripod", "camera", "headphone", "monitor", "setup", "fukra insaan", "youtube channel", "project", "exam"):
                if kw in text:
                    cls.record_topic(kw)
                    cls.add_fact(f"User discussed {kw}.")
                    break
