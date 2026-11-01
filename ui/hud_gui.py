import customtkinter as ctk
import tkinter as tk
import time
import datetime
import psutil
import socket
import threading
import subprocess
from ui.arc_reactor import ArcReactor, VoiceVisualizer
from automation.computer_control import ComputerControl

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class JarvisHUD(ctk.CTk):
    """
    STARK INDUSTRIES // J.A.R.V.I.S. OS 5.0 ADVANCED CYBER HUD
    Featuring:
    - Multi-layer vector animated Palladium Arc Reactor
    - 28-band Spectral Audio Frequency Visualizer
    - Unified Main Neural Chat & Cyber Console (Live Streams, Voice, Cognition, Shell)
    - Direct Shell & PowerShell Command Execution Console
    - Real-time Hardware Telemetry (CPU, RAM, Disk, Power, Network IP)
    - Full Computer Access Quick Protocol Deck
    """
    def __init__(self, brain_ref=None, listener_ref=None, speaker_ref=None, clapper_ref=None):
        super().__init__()

        self.brain = brain_ref
        self.listener = listener_ref
        self.speaker = speaker_ref
        self.clapper = clapper_ref

        # Start time for uptime calculation
        self.start_time = time.time()

        # Window Setup
        self.title("J.A.R.V.I.S. // STARK INDUSTRIES OS 5.0 PRO [COMPUTER ACCESS: GRANTED]")
        self.geometry("1180x740")
        self.minsize(1040, 680)
        self.configure(fg_color="#070a13")

        # Configure Grid Layout
        self.grid_columnconfigure(0, weight=3) # Left (Arc Reactor & Audio Visualizer)
        self.grid_columnconfigure(1, weight=6) # Center (Neural Console & System Terminal)
        self.grid_columnconfigure(2, weight=3) # Right (Hardware Telemetry & Quick Protocols)
        self.grid_rowconfigure(1, weight=1)

        # Build Panels
        self._build_header()
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()

        # Keyboard Shortcut: F12 Stealth Top Command Bar Toggle
        self.is_compact_mode = False
        self.bind("<F12>", self.toggle_compact_mode)

        # Telemetry & Uptime loop
        self.telemetry_active = True
        self._update_telemetry_loop()

        # Proactive Human-like greeting (as seen in video)
        self.after(1500, self._boot_proactive_greeting)

    # ==========================================
    # HEADER: HOLOGRAPHIC STATUS BAR
    # ==========================================
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="#0d1322", corner_radius=0, height=58)
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=(0, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Left Title
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        title_label = ctk.CTkLabel(
            title_box,
            text="◈ J.A.R.V.I.S. // STARK INDUSTRIES OS 5.0 PRO",
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            text_color="#00f3ff"
        )
        title_label.pack(side="left")

        # Computer Access Granted Badge
        access_badge = ctk.CTkLabel(
            title_box,
            text="● ACCESS: GRANTED",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#10b981",
            fg_color="#064e3b",
            corner_radius=6,
            padx=8,
            pady=2
        )
        access_badge.pack(side="left", padx=12)

        # Center: Clock & Uptime
        info_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        info_box.grid(row=0, column=1, padx=10, pady=10)

        self.clock_label = ctk.CTkLabel(
            info_box,
            text="00:00:00 PM",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color="#f8fafc"
        )
        self.clock_label.pack(side="left", padx=8)

        self.uptime_label = ctk.CTkLabel(
            info_box,
            text="UPTIME: 00:00:00",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#94a3b8"
        )
        self.uptime_label.pack(side="left", padx=8)

        # Right: Gemini Status, F12 Compact Bar Toggle & System State Badge
        right_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_box.grid(row=0, column=2, padx=15, pady=10, sticky="e")

        # F12 Compact Top Bar Button
        self.compact_btn = ctk.CTkButton(
            right_box,
            text="🗕 F12 TOP BAR",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#1e293b",
            text_color="#38bdf8",
            hover_color="#334155",
            corner_radius=6,
            height=28,
            command=self.toggle_compact_mode
        )
        self.compact_btn.pack(side="left", padx=(0, 10))

        import os
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        gemini_text = "🟢 GEMINI ACTIVE" if gemini_key else "⚡ GEMINI: CONNECT"
        gemini_fg = "#064e3b" if gemini_key else "#451a03"
        gemini_color = "#10b981" if gemini_key else "#f59e0b"

        self.gemini_btn = ctk.CTkButton(
            right_box,
            text=gemini_text,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color=gemini_fg,
            text_color=gemini_color,
            hover_color="#065f46" if gemini_key else "#78350f",
            corner_radius=6,
            height=28,
            command=self._show_gemini_dialog
        )
        self.gemini_btn.pack(side="left", padx=(0, 10))

        # Neural Voice Mode Toggle
        is_neural = getattr(self.speaker, "use_neural", True) if self.speaker else True
        self.voice_btn = ctk.CTkButton(
            right_box,
            text="🗣 NEURAL VOICE: ON" if is_neural else "🗣 LOCAL VOICE",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#064e3b" if is_neural else "#1e293b",
            text_color="#10b981" if is_neural else "#94a3b8",
            hover_color="#065f46" if is_neural else "#334155",
            corner_radius=6,
            height=28,
            command=self._toggle_neural_voice
        )
        self.voice_btn.pack(side="left", padx=(0, 10))

        self.status_badge = ctk.CTkLabel(
            right_box,
            text="[ STANDBY ]",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#00f3ff",
            fg_color="#062e3d",
            corner_radius=6,
            padx=14,
            pady=4
        )
        self.status_badge.pack(side="left")

    # ==========================================
    # LEFT PANEL: ARC REACTOR & VOICE ENGINE
    # ==========================================
    def _build_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, fg_color="#0d1322", corner_radius=12, border_color="#1e293b", border_width=1)
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(15, 8), pady=(0, 15))
        self.left_frame.grid_columnconfigure(0, weight=1)
        left_frame = self.left_frame

        # Header
        lbl = ctk.CTkLabel(
            left_frame, text="PALLADIUM ARC REACTOR CORE",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#38bdf8"
        )
        lbl.pack(pady=(12, 4))

        # Animated Arc Reactor
        self.reactor = ArcReactor(left_frame, size=235, bg="#0d1322")
        self.reactor.pack(pady=4)

        # Spectral Audio Frequency Visualizer
        vis_lbl = ctk.CTkLabel(
            left_frame, text="NEURAL AUDIO EQUALIZER",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#64748b"
        )
        vis_lbl.pack(pady=(4, 2))

        self.visualizer = VoiceVisualizer(left_frame, width=235, height=45, bg="#0d1322")
        self.visualizer.pack(pady=(0, 6))

        # Audio / State Details Box
        desc_box = ctk.CTkFrame(left_frame, fg_color="#070a13", corner_radius=8)
        desc_box.pack(fill="x", padx=16, pady=4)
        
        self.state_desc = ctk.CTkLabel(
            desc_box,
            text="Awaiting Wake Word\nSay: 'Wake up Jarvis'",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#94a3b8",
            justify="center",
            pady=6
        )
        self.state_desc.pack()

        # Action Buttons Dock
        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=6)

        # Mic Toggle Button
        self.mic_btn = ctk.CTkButton(
            btn_frame,
            text="🎤 Mic: Listening",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            corner_radius=8,
            height=32,
            command=self._toggle_mic
        )
        self.mic_btn.pack(pady=3, fill="x")

        # Clap Trigger Button
        self.clap_btn = ctk.CTkButton(
            btn_frame,
            text="👏 Clap Trigger: OFF",
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1e293b",
            hover_color="#334155",
            corner_radius=8,
            height=32,
            command=self._toggle_clapper
        )
        self.clap_btn.pack(pady=3, fill="x")

        # Wake Up Now Button
        self.wake_btn = ctk.CTkButton(
            btn_frame,
            text="⚡ Wake Up Jarvis",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#047857",
            hover_color="#065f46",
            corner_radius=8,
            height=32,
            command=self._manual_wake
        )
        self.wake_btn.pack(pady=3, fill="x")

        # YouTube Shorts Auto-Scroller Button
        self.shorts_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Auto-Scroll Shorts",
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1e293b",
            hover_color="#334155",
            corner_radius=8,
            height=32,
            command=self._toggle_shorts_scroller
        )
        self.shorts_btn.pack(pady=3, fill="x")


    # ==========================================
    # CENTER PANEL: UNIFIED MAIN CHAT CONSOLE
    # ==========================================
    def _build_center_panel(self):
        self.center_frame = ctk.CTkFrame(self, fg_color="#0d1322", corner_radius=12, border_color="#1e293b", border_width=1)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=8, pady=(0, 15))
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)

        # Build Single Unified Main Chat Console
        self._setup_main_chat_console()

        # Bottom Input Bar (Directly beneath main chat)
        self._build_input_bar(self.center_frame)

    def _setup_main_chat_console(self):
        self.chat_container = ctk.CTkFrame(
            self.center_frame,
            fg_color="#090e1a",
            corner_radius=10,
            border_color="#1e293b",
            border_width=1
        )
        self.chat_container.grid(row=0, column=0, sticky="nsew", padx=12, pady=(8, 6))
        self.chat_container.grid_rowconfigure(1, weight=1)
        self.chat_container.grid_columnconfigure(0, weight=1)

        # Console Header Toolbar
        toolbar = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))

        # Title & Status Indicator
        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        title_lbl = ctk.CTkLabel(
            title_box,
            text="💬 J.A.R.V.I.S. MAIN NEURAL CHAT",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#38bdf8"
        )
        title_lbl.pack(side="left")

        live_badge = ctk.CTkLabel(
            title_box,
            text="● UNIFIED STREAM",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#10b981"
        )
        live_badge.pack(side="left", padx=(10, 0))

        # Right Actions: Copy, Clear
        btn_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_box.pack(side="right")

        copy_btn = ctk.CTkButton(
            btn_box,
            text="Copy All",
            width=65,
            height=24,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#1e293b",
            hover_color="#334155",
            command=self._copy_chat
        )
        copy_btn.pack(side="right", padx=(4, 0))

        clear_btn = ctk.CTkButton(
            btn_box,
            text="Clear",
            width=55,
            height=24,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#1e293b",
            hover_color="#ef4444",
            command=self._clear_chat
        )
        clear_btn.pack(side="right", padx=(4, 0))

        # Unified Main Chat Textbox
        self.chat_terminal = ctk.CTkTextbox(
            self.chat_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#03060d",
            text_color="#e2e8f0",
            corner_radius=8,
            wrap="word",
            border_color="#0e3a53",
            border_width=1
        )
        self.chat_terminal.grid(row=1, column=0, sticky="nsew", padx=8, pady=(2, 8))

        # Set sys_terminal to point to the unified chat for backward compatibility
        self.sys_terminal = self.chat_terminal

        # Backward compatibility shim for tabview
        class _TabCompat:
            def set(self, *args, **kwargs):
                pass
            def grid_remove(self):
                pass
            def grid(self, *args, **kwargs):
                pass
        self.tabview = _TabCompat()

        # Initial Welcome Messages
        self.log_message("SYSTEM", "STARK INDUSTRIES // J.A.R.V.I.S. Core OS 5.0 Online.")
        self.log_message("SYSTEM", "Main Unified Chat Active: All conversations, voice commands, and system responses appear here.")
        self.log_message("SYSTEM", "Say 'Wake up Jarvis' or type below (use '>' for direct shell execution).")

    def _clear_chat(self):
        self.chat_terminal.delete("1.0", "end")
        self.log_message("SYSTEM", "Main Chat Cleared. Ready for input.")

    def _copy_chat(self):
        try:
            content = self.chat_terminal.get("1.0", "end").strip()
            if content:
                self.clipboard_clear()
                self.clipboard_append(content)
                self.log_message("SYSTEM", "Chat history copied to clipboard.")
        except Exception:
            pass

    def _toggle_neural_voice(self):
        if hasattr(self, 'speaker') and self.speaker:
            is_active = self.speaker.toggle_neural()
            if is_active:
                self.voice_btn.configure(text="🗣 NEURAL VOICE: ON", fg_color="#064e3b", text_color="#10b981")
                self.log_message("SYSTEM", "Studio-grade neural voice (edge-tts) enabled.")
            else:
                self.voice_btn.configure(text="🗣 LOCAL VOICE", fg_color="#1e293b", text_color="#94a3b8")
                self.log_message("SYSTEM", "Offline local voice (pyttsx3) enabled.")

    def _build_input_bar(self, parent):
        self.input_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 12))
        self.input_frame.grid_columnconfigure(0, weight=1)
        input_frame = self.input_frame

        self.cmd_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter command or prefix with '>' for direct shell (e.g. '> ipconfig', 'play iron man')...",
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#070a13",
            border_color="#38bdf8",
            corner_radius=8,
            height=40
        )
        self.cmd_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.cmd_entry.bind("<Return>", lambda event: self._send_typed_command())
        self.cmd_entry.bind("<F12>", self.toggle_compact_mode)

        send_btn = ctk.CTkButton(
            input_frame,
            text="Send ↵",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#00f3ff",
            text_color="#000000",
            hover_color="#38bdf8",
            width=75,
            height=40,
            corner_radius=8,
            command=self._send_typed_command
        )
        send_btn.grid(row=0, column=1, padx=(0, 6))

        shell_btn = ctk.CTkButton(
            input_frame,
            text="Run Shell ⚡",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            width=88,
            height=40,
            corner_radius=8,
            command=self._send_as_shell
        )
        shell_btn.grid(row=0, column=2)

        self.bar_f12_btn = ctk.CTkButton(
            input_frame,
            text="🗕 F12",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#1e293b",
            text_color="#38bdf8",
            hover_color="#334155",
            width=58,
            height=40,
            corner_radius=8,
            command=self.toggle_compact_mode
        )
        self.bar_f12_btn.grid(row=0, column=3, padx=(6, 0))

    # ==========================================
    # RIGHT PANEL: HARDWARE TELEMETRY & PROTOCOLS
    # ==========================================
    def _build_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, fg_color="#0d1322", corner_radius=12, border_color="#1e293b", border_width=1)
        self.right_frame.grid(row=1, column=2, sticky="nsew", padx=(8, 15), pady=(0, 15))
        self.right_frame.grid_columnconfigure(0, weight=1)
        right_frame = self.right_frame

        # Header
        lbl = ctk.CTkLabel(
            right_frame, text="HARDWARE TELEMETRY",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#38bdf8"
        )
        lbl.pack(pady=(12, 8))

        # CPU Metric
        self.cpu_label = ctk.CTkLabel(right_frame, text="CPU: 0%", font=ctk.CTkFont(family="Consolas", size=11), text_color="#cbd5e1")
        self.cpu_label.pack(anchor="w", padx=16, pady=(2, 0))
        self.cpu_bar = ctk.CTkProgressBar(right_frame, progress_color="#00f3ff", fg_color="#1e293b", height=10)
        self.cpu_bar.set(0.0)
        self.cpu_bar.pack(fill="x", padx=16, pady=(2, 8))

        # RAM Metric
        self.ram_label = ctk.CTkLabel(right_frame, text="RAM: 0%", font=ctk.CTkFont(family="Consolas", size=11), text_color="#cbd5e1")
        self.ram_label.pack(anchor="w", padx=16, pady=(2, 0))
        self.ram_bar = ctk.CTkProgressBar(right_frame, progress_color="#10b981", fg_color="#1e293b", height=10)
        self.ram_bar.set(0.0)
        self.ram_bar.pack(fill="x", padx=16, pady=(2, 8))

        # Disk Storage Metric
        self.disk_label = ctk.CTkLabel(right_frame, text="STORAGE: Free -- GB", font=ctk.CTkFont(family="Consolas", size=11), text_color="#cbd5e1")
        self.disk_label.pack(anchor="w", padx=16, pady=(2, 0))
        self.disk_bar = ctk.CTkProgressBar(right_frame, progress_color="#8b5cf6", fg_color="#1e293b", height=10)
        self.disk_bar.set(0.0)
        self.disk_bar.pack(fill="x", padx=16, pady=(2, 8))

        # Battery / Power Line
        self.power_label = ctk.CTkLabel(
            right_frame, text="POWER: Desktop AC Supply",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#94a3b8"
        )
        self.power_label.pack(anchor="w", padx=16, pady=(2, 4))

        # Network IP & Ping
        self.network_label = ctk.CTkLabel(
            right_frame, text="IP: 127.0.0.1 // ONLINE",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#38bdf8"
        )
        self.network_label.pack(anchor="w", padx=16, pady=(2, 10))

        # Divider
        div = ctk.CTkFrame(right_frame, fg_color="#1e293b", height=1)
        div.pack(fill="x", padx=16, pady=4)

        # Quick Actions Header
        lbl_act = ctk.CTkLabel(
            right_frame, text="QUICK PROTOCOLS",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#38bdf8"
        )
        lbl_act.pack(pady=(6, 4))

        actions = [
            ("🌐 Universal Translator", "tab_translator"),
            ("🌤 Live Weather", "weather"),
            ("📰 Global News Feed", "news"),
            ("📊 Full Diagnostics", "system status"),
            ("⚡ Internet Speed Test", "speed test"),
            ("🌐 Check IP & Network", "my ip"),
            ("🧹 Clean Recycle Bin", "empty recycle bin")
        ]

        for text, cmd in actions:
            btn = ctk.CTkButton(
                right_frame,
                text=text,
                font=ctk.CTkFont(family="Consolas", size=11),
                fg_color="#1e293b",
                hover_color="#334155",
                corner_radius=6,
                height=30,
                command=lambda c=cmd: self._run_quick_cmd(c)
            )
            btn.pack(fill="x", padx=16, pady=3)

    # ==========================================
    # LOGGING & CONSOLE OUTPUT
    # ==========================================
    def log_message(self, sender, text):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] "
        if sender == "USER":
            formatted = f"{prefix}USER: {text}\n"
        elif sender == "JARVIS":
            formatted = f"{prefix}JARVIS: {text}\n\n"
        else:
            formatted = f"{prefix}[{sender}]: {text}\n"

        self.chat_terminal.insert("end", formatted)
        self.chat_terminal.see("end")

    def log_terminal(self, text):
        """Append raw command output to the unified main chat console."""
        if not text:
            return
        self.chat_terminal.insert("end", f"{text}\n")
        self.chat_terminal.see("end")

    def _clear_terminal(self):
        self._clear_chat()

    def _boot_proactive_greeting(self):
        """Speaks and logs proactive human-like greeting upon booting (as seen in video)."""
        if hasattr(self, 'brain') and self.brain and hasattr(self.brain, 'get_proactive_greeting'):
            greeting = self.brain.get_proactive_greeting()
            if hasattr(self, 'speaker') and self.speaker and self.brain.state != "MUTED":
                self.speaker.speak(greeting)
            else:
                self.log_message("JARVIS", greeting)

    def toggle_compact_mode(self, event=None):
        """
        F12 Hotkey Toggle:
        Switches between Full Holographic Stark HUD and Stealth Top Floating Command Bar.
        In Compact Mode:
        - The entire upper body (header, holographic panels, Arc Reactor, equalizer, logs) disappears.
        - The input bar floats at the very top of the screen (always on top).
        - The desktop is 100% visible and unobstructed so Jarvis can control apps, browsers, and mouse efficiently!
        """
        self.is_compact_mode = not getattr(self, "is_compact_mode", False)

        if self.is_compact_mode:
            # Save normal window size and location
            self._normal_geometry = self.geometry()
            
            # Allow window to shrink down to a sleek top bar
            self.minsize(400, 52)

            # Hide upper body
            self.header_frame.grid_remove()
            self.left_frame.grid_remove()
            self.right_frame.grid_remove()
            self.chat_container.grid_remove()

            # Re-grid center frame & input frame to fill top window
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=0)
            self.center_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=0, pady=0)
            self.center_frame.configure(corner_radius=0, border_width=0, fg_color="#070a13")
            self.input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=6)

            # Resize window to top floating bar
            screen_w = self.winfo_screenwidth()
            bar_w = min(1050, max(750, int(screen_w * 0.72)))
            bar_h = 54
            bar_x = (screen_w - bar_w) // 2
            bar_y = 10

            self.geometry(f"{bar_w}x{bar_h}+{bar_x}+{bar_y}")
            self.attributes("-topmost", True)

            if hasattr(self, 'compact_btn'):
                self.compact_btn.configure(text="🗖 F12 FULL HUD", fg_color="#0284c7")
            if hasattr(self, 'bar_f12_btn'):
                self.bar_f12_btn.configure(text="🗖 F12", fg_color="#0284c7")

            self.cmd_entry.configure(placeholder_text="[F12 to Expand HUD] Command Jarvis (e.g. 'open youtube', 'scroll down', 'type in notepad')...")
            self.cmd_entry.focus_set()
            print("[HUD] Stealth Top Command Bar Active (F12). Upper body hidden for PC control.")
        else:
            # Restore normal Stark HUD
            self.attributes("-topmost", False)

            # Reset minsize
            self.minsize(1040, 680)

            # Re-attach components
            self.grid_rowconfigure(0, weight=0)
            self.grid_rowconfigure(1, weight=1)
            self.center_frame.configure(corner_radius=12, border_width=1, fg_color="#0d1322")
            self.input_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 12))
            self.chat_container.grid(row=0, column=0, sticky="nsew", padx=12, pady=(8, 6))

            self.center_frame.grid(row=1, column=1, sticky="nsew", padx=8, pady=(0, 15))
            self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=(0, 10))
            self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(15, 8), pady=(0, 15))
            self.right_frame.grid(row=1, column=2, sticky="nsew", padx=(8, 15), pady=(0, 15))

            norm_geo = getattr(self, "_normal_geometry", "1280x760")
            self.geometry(norm_geo)

            if hasattr(self, 'compact_btn'):
                self.compact_btn.configure(text="🗕 F12 TOP BAR", fg_color="#1e293b")
            if hasattr(self, 'bar_f12_btn'):
                self.bar_f12_btn.configure(text="🗕 F12", fg_color="#1e293b")

            self.cmd_entry.configure(placeholder_text="Enter command or prefix with '>' for direct shell (e.g. '> ipconfig', 'play iron man')...")
            self.cmd_entry.focus_set()
            print("[HUD] Restored Full Holographic Stark HUD.")
        return "break"

    # ==========================================
    # STATUS & ANIMATION UPDATES
    # ==========================================
    def set_status(self, status):
        """Update HUD status badge, Arc Reactor, and Equalizer."""
        self.status_badge.configure(text=f"[ {status} ]")
        
        if hasattr(self, 'reactor'):
            self.reactor.set_state(status)
        if hasattr(self, 'visualizer'):
            self.visualizer.set_state(status)

        if status == "STANDBY":
            self.status_badge.configure(text_color="#00f3ff", fg_color="#062e3d")
            self.state_desc.configure(text="Awaiting Wake Word\nSay: 'Wake up Jarvis'")
        elif status == "LISTENING":
            self.status_badge.configure(text_color="#10b981", fg_color="#064e3b")
            self.state_desc.configure(text="Listening...\nSpeak your command, sir.")
        elif status == "PROCESSING":
            self.status_badge.configure(text_color="#f59e0b", fg_color="#451a03")
            self.state_desc.configure(text="Processing request...")
        elif status == "SPEAKING":
            self.status_badge.configure(text_color="#38bdf8", fg_color="#0c4a6e")
            self.state_desc.configure(text="Jarvis is responding...")
        elif status == "MUTED":
            self.status_badge.configure(text_color="#ef4444", fg_color="#450a0a")
            self.state_desc.configure(text="Microphone Muted\nUse typed input or unmute.")

    # ==========================================
    # INPUT & EXECUTION DISPATCHERS
    # ==========================================
    def _toggle_mic(self):
        if self.listener:
            is_muted = self.listener.toggle_mute()
            if is_muted:
                self.mic_btn.configure(text="🔇 Mic: MUTED", fg_color="#ef4444")
                self.set_status("MUTED")
            else:
                self.mic_btn.configure(text="🎤 Mic: Listening", fg_color="#0284c7")
                self.set_status("STANDBY")

    def _toggle_clapper(self):
        if self.clapper:
            is_active = self.clapper.toggle()
            if is_active:
                self.clap_btn.configure(text="👏 Clap Trigger: ON", fg_color="#059669")
                self.log_message("SYSTEM", "Clap detection activated. Double-clap to trigger music.")
            else:
                self.clap_btn.configure(text="👏 Clap Trigger: OFF", fg_color="#1e293b")
                self.log_message("SYSTEM", "Clap detection deactivated.")

    def _manual_wake(self):
        if self.brain:
            self.brain.process("wake up jarvis")

    def _toggle_shorts_scroller(self):
        from automation.youtube_control import YouTubeControl
        import threading
        if getattr(YouTubeControl, "is_scrolling_shorts", False):
            YouTubeControl.stop_scrolling_shorts()
            self.shorts_btn.configure(text="▶ Auto-Scroll Shorts", fg_color="#1e293b")
            self.log_message("SYSTEM", "YouTube Shorts auto-scroller stopped.")
        else:
            self.shorts_btn.configure(text="⏹ Stop Shorts Scroller", fg_color="#ef4444")
            self.log_message("SYSTEM", "Starting YouTube Shorts auto-scroller...")
            threading.Thread(target=lambda: YouTubeControl.open_and_scroll_shorts(speaker_ref=self.speaker, status_cb=self.log_message), daemon=True).start()


    def _send_typed_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        self.cmd_entry.delete(0, "end")
        self.log_message("USER", cmd)

        # Force wake for manual typed commands if in standby
        if self.brain and self.brain.state == "STANDBY":
            self.brain.state = "AWAKE"
            self.set_status("AWAKE")

        def _exec():
            if self.brain:
                res = self.brain.process(cmd)
                if res:
                    if "reply" in res and not (self.speaker and getattr(self.speaker, "on_speech_start", None)):
                        self.after(0, lambda: self.log_message("JARVIS", res["reply"]))
                    if "terminal_output" in res:
                        self.after(0, lambda: self.log_terminal(res["terminal_output"]))
        threading.Thread(target=_exec, daemon=True).start()

    def _send_as_shell(self):
        """Forces the current input to run as direct shell command."""
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        if not cmd.startswith(">"):
            cmd = "> " + cmd
        self.cmd_entry.delete(0, "end")
        self.cmd_entry.insert(0, cmd)
        self._send_typed_command()

    def _run_quick_cmd(self, cmd):
        if cmd == "tab_translator":
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.insert(0, "translate to hindi: Hello Jarvis, how are you today?")
            self.cmd_entry.focus_set()
            return
        self.cmd_entry.delete(0, "end")
        self.cmd_entry.insert(0, cmd)
        self._send_typed_command()

    # ==========================================
    # TELEMETRY & HARDWARE REFRESH LOOP
    # ==========================================
    def _update_telemetry_loop(self):
        if not self.telemetry_active:
            return

        # Clock & Uptime
        now_str = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.clock_label.configure(text=now_str)

        elapsed = int(time.time() - self.start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        self.uptime_label.configure(text=f"UPTIME: {hrs:02d}:{mins:02d}:{secs:02d}")

        # CPU & RAM & Storage
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            self.cpu_label.configure(text=f"CPU: {cpu:.1f}%")
            self.cpu_bar.set(cpu / 100.0)
            if cpu > 80:
                self.cpu_bar.configure(progress_color="#ef4444")
            elif cpu > 50:
                self.cpu_bar.configure(progress_color="#f59e0b")
            else:
                self.cpu_bar.configure(progress_color="#00f3ff")

            self.ram_label.configure(text=f"RAM: {ram.percent:.1f}% ({ram.used // (1024**3):.1f}/{ram.total // (1024**3):.1f} GB)")
            self.ram_bar.set(ram.percent / 100.0)

            disk_free_gb = disk.free // (1024**3)
            self.disk_label.configure(text=f"STORAGE: {disk.percent:.1f}% (Free {disk_free_gb} GB)")
            self.disk_bar.set(disk.percent / 100.0)

            # Battery
            b = psutil.sensors_battery()
            if b is not None:
                p_text = f"POWER: Battery {b.percent}% ({'Charging' if b.power_plugged else 'Discharging'})"
            else:
                p_text = "POWER: Desktop AC Supply (Stable)"
            self.power_label.configure(text=p_text)

            # Shorts Auto-Scroller button dynamic state
            try:
                from automation.youtube_control import YouTubeControl
                if hasattr(self, 'shorts_btn'):
                    if getattr(YouTubeControl, "is_scrolling_shorts", False):
                        self.shorts_btn.configure(text="⏹ Stop Shorts Scroller", fg_color="#ef4444")
                    else:
                        self.shorts_btn.configure(text="▶ Auto-Scroll Shorts", fg_color="#1e293b")
            except Exception:
                pass

            # Network IP

            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                self.network_label.configure(text=f"IP: {ip} // ONLINE")
            except Exception:
                pass
        except Exception:
            pass

        self.after(1000, self._update_telemetry_loop)

    def _show_gemini_dialog(self):
        """Displays dialog for connecting Google Gemini API Key."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("◈ CONNECT GOOGLE GEMINI NEURAL CORTEX")
        dialog.geometry("540x390")
        dialog.configure(fg_color="#070a13")
        dialog.transient(self)

        lbl_title = ctk.CTkLabel(
            dialog,
            text="GOOGLE GEMINI NEURAL AI INTEGRATION",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#38bdf8"
        )
        lbl_title.pack(pady=(16, 6))

        lbl_desc = ctk.CTkLabel(
            dialog,
            text=(
                "Empowers Jarvis with true human common sense, conversational reasoning,\n"
                "and autonomous multi-step computer actions.\n"
                "1-click free key from Google AI Studio (zero credit card needed)."
            ),
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#94a3b8",
            justify="center"
        )
        lbl_desc.pack(pady=4)

        btn_portal = ctk.CTkButton(
            dialog,
            text="🌐 1. Open Google AI Studio (Get Free Key)",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            corner_radius=6,
            height=32,
            command=lambda: ComputerControl.open_path("https://aistudio.google.com/app/apikey")
        )
        btn_portal.pack(pady=(6, 12))

        entry_row = ctk.CTkFrame(dialog, fg_color="transparent")
        entry_row.pack(pady=4)

        key_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="Paste your Gemini API key (AIzaSy...)",
            font=ctk.CTkFont(family="Consolas", size=12),
            width=360,
            height=36,
            fg_color="#0d1322",
            border_color="#1e293b"
        )
        key_entry.pack(in_=entry_row, side="left", padx=(0, 6))

        status_lbl = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(family="Consolas", size=11), text_color="#38bdf8")

        def _paste_clip():
            try:
                clip = dialog.clipboard_get().strip()
                if clip:
                    key_entry.delete(0, "end")
                    key_entry.insert(0, clip)
                    status_lbl.configure(text="Pasted API key from clipboard!", text_color="#10b981")
            except Exception as e:
                status_lbl.configure(text="Clipboard is empty or inaccessible.", text_color="#f59e0b")

        paste_btn = ctk.CTkButton(
            dialog,
            text="📋 Paste",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            width=80,
            height=36,
            command=_paste_clip
        )
        paste_btn.pack(in_=entry_row, side="left")

        # Auto-detect if clipboard already has Gemini key
        try:
            curr_clip = dialog.clipboard_get().strip()
            if curr_clip.startswith("AIzaSy"):
                key_entry.insert(0, curr_clip)
                status_lbl.configure(text="Auto-detected Gemini key from clipboard! Click Activate.", text_color="#10b981")
        except Exception:
            pass

        status_lbl.pack(pady=6)

        def _save():
            val = key_entry.get().strip()
            if not val:
                status_lbl.configure(text="Please paste your API key above first.", text_color="#ef4444")
                return
            status_lbl.configure(text="Testing neural connection with Google...", text_color="#f59e0b")
            dialog.update()

            if self.brain:
                res = self.brain._set_gemini_api_key(val)
                if isinstance(res, dict) and res.get("action") == "gemini_key_saved":
                    self.gemini_btn.configure(
                        text="🟢 GEMINI ACTIVE",
                        fg_color="#064e3b",
                        text_color="#10b981",
                        hover_color="#065f46"
                    )
                    self.log_message("SYSTEM", "Google Gemini neural link is online and active.")
                    status_lbl.configure(text="Neural link established successfully!", text_color="#10b981")
                    self.after(1000, dialog.destroy)
                else:
                    err_msg = res.get("reply") if isinstance(res, dict) else str(res)
                    status_lbl.configure(text=f"{err_msg}", text_color="#ef4444")

        btn_box = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_box.pack(pady=10)

        save_btn = ctk.CTkButton(
            btn_box,
            text="2. Activate Gemini Key",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            width=180,
            height=34,
            command=_save
        )
        save_btn.pack(side="left", padx=8)

        cancel_btn = ctk.CTkButton(
            btn_box,
            text="Close",
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#334155",
            hover_color="#475569",
            width=90,
            height=34,
            command=dialog.destroy
        )
        cancel_btn.pack(side="left", padx=8)

    def destroy(self):
        self.telemetry_active = False
        super().destroy()
