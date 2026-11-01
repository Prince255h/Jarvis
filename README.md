# ◈ J.A.R.V.I.S. // STARK INDUSTRIES OS 4.1 ADVANCED

An ultra-fast, multi-threaded AI Desktop Assistant for Windows inspired by Iron Man's J.A.R.V.I.S. and modeled from Anubhav Chaturvedi's master tutorial (`https://youtu.be/99i4BF0To4Y`), heavily enhanced with modern asynchronous architecture, zero-latency local TTS, animated vector Arc Reactor HUD GUI, and comprehensive Windows automation.

---

## ⚡ Key Highlights & Architecture Upgrades

| Feature | Original Video Implementation | **Your Advanced Upgrade** |
| :--- | :--- | :--- |
| **TTS / Speech Output** | Selenium browser scrape / Edge-TTS (prone to timeouts, browser lag, blocking) | **Zero-Latency Dual Engine**: Dedicated COM-threaded `pyttsx3` (David/Zira) + SFX Chimes with non-blocking queue |
| **Voice Activation** | Basic string matching with false positives | **Dual-State Engine (STANDBY / AWAKE)**: Strict wake-word triggers (`Wake up Jarvis`), echo-cancellation (Jarvis never listens to itself) |
| **User Interface** | Basic static window / GIF | **CustomTkinter Cyber HUD**: Vector-animated rotating palladium Arc Reactor with pulsing glow, real-time CPU/RAM gauges, live conversation log, and dual voice/text command inputs |
| **System Telemetry** | Crashed on desktop PCs with `psutil.sensors_battery() is None` | **Hardware Adaptive**: Detects laptop batteries (charging status, alerts at <20% and >98%) and desktop AC line power |
| **Media Control** | Manual keystroke delays | **Comprehensive YouTube Automation**: Play, pause, volume, mute, captions, speed adjustment, seek ±10s, next/previous video |
| **Intelligence** | Brittle regex / slow scrape | **Instant Regex Intent Router + Free Live Intel** (wttr.in weather, Google News RSS, jokes, advice) + Optional Gemini 2.5 Flash |
| **Clap Trigger** | Triggered on ordinary speech/lip movement | **Transient Peak Detection**: Filters RMS energy decay so only real claps trigger music |

---

## 🚀 Quick Start (1-Click Launch)

Simply double-click the included batch launcher:
```bat
g:\Jarvis\run_jarvis.bat
```
To run the automated hardware, audio, and neural diagnostics self-check:
```bat
g:\Jarvis\run_diagnostics.bat
```
Or start via terminal:
```bash
cd g:\Jarvis
python main.py
```

---

## 🎙️ Voice & Text Command Cheatsheet

### 1. Wake, Standby & Physical Summon Protocols
- **`Ctrl + Alt + J`** ➔ **Universal Global Hotkey** (Instantly summons Jarvis to the foreground from any app/game or interrupts speech).
- `"Wake up Jarvis"` / `"Hey Jarvis"` / `"Hello Jarvis"` ➔ Wakes Jarvis into AWAKE mode.
- `"Go to sleep"` / `"Sleep Jarvis"` / `"Goodbye Jarvis"` ➔ Puts Jarvis into low-power STANDBY mode.
- `"Stop talking"` / `"Silence"` / `"Be quiet"` / `"That's enough Jarvis"` ➔ Instantly cuts speech audio output.
- `"Exit Jarvis"` / `"Shutdown Jarvis"` ➔ Safely closes the assistant.

### 2. YouTube & Media Control
- `"Play [song name] on YouTube"` ➔ Opens and directly plays your requested music/video.
- `"Search [topic] on YouTube"` ➔ Searches YouTube.
- `"Pause video"` / `"Play video"` ➔ Toggles playback.
- `"Video volume up"` / `"Video volume down"` / `"Mute video"` ➔ Adjusts YouTube player volume.
- `"Subtitles"` / `"Captions"` ➔ Toggles closed captions (`c`).
- `"Fullscreen"` ➔ Toggles fullscreen (`f`).
- `"Speed up video"` / `"Slow down video"` ➔ Changes video playback speed (`shift+>` / `shift+<`).
- `"Skip forward"` / `"Rewind"` ➔ Skips forward or rewinds 10 seconds.
- `"Next video"` ➔ Skips to the next video in playlist.

### 3. Browser & Navigation
- `"Open Google"` / `"Open YouTube"` / `"Open GitHub"` / `"Open ChatGPT"` / `"Open WhatsApp"` / `"Open Instagram"`
- `"Search on Google [query]"` ➔ Launches instant Google search.
- `"Scroll down"` / `"Scroll up"` / `"Scroll to top"` / `"Scroll to bottom"` ➔ Page navigation.
- `"New tab"` / `"Close tab"` / `"Switch tab"` ➔ Tab management.

### 4. Windows App Management
- `"Open Notepad"`, `"Open Calculator"`, `"Open Chrome"`, `"Open VS Code"`, `"Open Terminal"`
- `"Close Notepad"`, `"Close Chrome"`, `"Terminate Calculator"` ➔ Process killer.

### 5. System Health & Hardware Telemetry
- `"Check battery"` / `"Power status"` ➔ Reports battery % or AC desktop line status.
- `"System status"` / `"Diagnostics"` ➔ Vocal report of CPU utilization, RAM usage, and free hard disk space.
- `"Check internet speed"` / `"Speed test"` ➔ Measures network speed and latency.
- `"Take a screenshot"` ➔ Captures full screen, saves to `data/screenshots/`, and opens preview.
- `"Volume to [0-100] percent"` / `"Volume up"` / `"Volume down"` / `"Mute audio"` ➔ Windows master volume control.
- `"Show desktop"` / `"Minimize windows"` ➔ Minimizes all windows.
- `"Lock workstation"` ➔ Securely locks Windows.

### 6. Real-Time Intel & Lifestyle
- `"Check weather"` / `"Weather in [City]"` ➔ Live temperature, humidity, wind, and forecast.
- `"Top news"` / `"Headlines"` ➔ Top 3 breaking news stories.
- `"What time is it"` / `"What is today's date"` ➔ Time & date briefing.
- `"Tell me a joke"` ➔ Fresh programming/general humor.
- `"Give me advice"` ➔ Inspirational wisdom slip.

### 7. Iron Man Easter Eggs
- `"Suit up"`
- `"House party protocol"`
- `"Protocol clean slate"`
- `"I am Iron Man"`

### 8. 🧠 Autonomous Natural Language Agent (NEW in OS 5.0)
Jarvis now understands free-form, multi-step natural language instructions and executes them by himself on your computer:
- **Compound App & Writing Actions**:
  - `"Open notepad and write my shopping list"` ➔ Launches Notepad, waits for window focus, and automatically types your text.
  - `"Open word and type project meeting minutes"`
- **Autonomous Media & YouTube Actions**:
  - `"Open YouTube and search Fukra Insaan"` ➔ Searches in active session using YouTube's in-page shortcut without page reloads or window resizing.
  - `"Search Believer on YouTube and play it"` ➔ Finds and starts video playback directly.
- **Autonomous Web & Research Actions**:
  - `"Open Chrome and search best laptops under 70000"` ➔ Launches browser and executes Google search.
- **Autonomous Filesystem Operations**:
  - `"Create a folder called stark_tech on desktop"` ➔ Creates `Desktop\stark_tech` folder.
  - `"Create file todo.txt with 1. Upgrade suit 2. Test thrusters"` ➔ Creates file with requested content.
- **Autonomous Script Generation & Execution**:
  - `"Write a python script into test.py and run it"` ➔ Generates script file and executes `python test.py` in shell.
- **Multi-System Adjustments & Calculations**:
  - `"Volume to 80 and brightness to 70"` ➔ Adjusts volume and display brightness in one command.
  - `"Mute volume and lock computer"` ➔ Mutes audio and locks Windows workstation.
  - `"Calculate 450 * 12"` ➔ Evaluates math expression.
  - `"Clean my PC"` ➔ Empties Windows Recycle Bin and displays telemetry diagnostics.
- **Conversational Prefix Tolerance**:
- **⚡ Just-In-Time Dynamic Code Synthesis & Self-Healing Execution (OS 5.1)**:
  - If you ask for ANY custom task, calculation, automation, or query for which **no built-in function exists**:
    - Jarvis **dynamically writes the required Python function** specifically for your prompt.
    - Runs the synthesized function in a dedicated child process.
    - **Self-Healing Auto-Repair**: If a runtime exception occurs, Jarvis's neural debugger automatically fixes the code and retries execution.
    - **Persistent Skill Vault**: Stores new abilities in `data/custom_skills/` and tracks them in `manifest.json`.
    - *Examples*:
      - `"Jarvis, count how many python files are in this folder and print the line count"`
      - `"Jarvis, calculate the MD5 hash of README.md"`
      - `"Jarvis, list all active network adapters and IP addresses"`
      - `"Jarvis, find how much space __pycache__ folders occupy"`
      - `"Jarvis, find all png images larger than 1MB"`

### 9. 💻 Full Computer Access Protocols (OS 5.0)
- **Shell & PowerShell Execution**:
  - `> [command]` (e.g. `> ipconfig`, `> dir`, `> Get-Process | Select -First 5`)
  - `"Run command [cmd]"` / `"Execute command [cmd]"`
  - `"Powershell [cmd]"` / `"Terminal [cmd]"` / `"Cmd [cmd]"`
- **File & Directory Management**:
  - `"Open folder [path/name]"` (e.g. `"Open folder downloads"`, `"Open folder desktop"`)
  - `"Open file [path]"`
  - `"Create folder [name]"` / `"Create file [filename]"`
  - `"Read file [path]"`
  - `"Search file [name]"` / `"Find file [name]"`
  - `"Empty recycle bin"`
- **Window & Display Control**:
  - `"List windows"` / `"Open windows"` (Lists active application windows)
  - `"Switch to [window name]"` / `"Focus [window name]"`
  - `"Minimize window"` / `"Maximize window"` / `"Close active window"` / `"Switch window"`
  - `"Brightness to [0-100] percent"` / `"Increase brightness"` / `"Decrease brightness"`
- **Mouse & Keyboard Automation**:
  - `"Type [text]"` / `"Write [text]"` (Types directly into active window)
  - `"Press [key]"` (e.g. `"Press enter"`, `"Press escape"`, `"Press tab"`)
  - `"Press [hotkey]"` (e.g. `"Press ctrl c"`, `"Press ctrl v"`, `"Press win r"`)
  - `"Click"`, `"Double click"`, `"Right click"`
- **Process & Task Management**:
  - `"Running processes"` / `"List tasks"` (Top CPU and RAM consuming tasks)
  - `"Kill process [name/PID]"` / `"End task [name]"`
- **Network & System Power**:
  - `"My IP"` / `"IP address"` / `"Network details"`
  - `"Copy to clipboard [text]"` / `"Paste clipboard"`
  - `"Sleep computer"` / `"Restart computer"` / `"Shutdown computer"`

---

## 📁 Project Structure

```
g:/Jarvis/
├── main.py                     # Master launcher & orchestrator
├── config.py                   # Central settings, hotwords, application paths
├── run_jarvis.bat              # 1-Click desktop launcher
├── core/
│   ├── listener.py             # Ambient noise calibrated Speech-to-Text
│   ├── speaker.py              # Asynchronous thread-safe SAPI5 TTS engine + SFX
│   ├── brain.py                # Command routing, regex NLP, shell & computer access
│   └── clapper.py              # Acoustic transient clap detector for music
├── automation/
│   ├── computer_control.py     # OS shell, process, window, filesystem & input automation
│   ├── youtube_control.py      # Full YouTube hotkey suite
│   ├── browser_control.py      # Web navigation and scrolling
│   ├── system_control.py       # Battery alerts, volume, hardware telemetry, screenshot
│   ├── app_control.py          # Windows app launcher and process termination
│   └── live_intel.py           # Live weather, Google News, jokes, advice
├── ui/
│   ├── hud_gui.py              # CustomTkinter OS 5.0 Cyber HUD interface with multi-tabs
│   └── arc_reactor.py          # Vector animated Palladium Arc Reactor & VoiceVisualizer
└── data/
    ├── dialogs.json            # Jarvis dialogues and Stark personality responses
    ├── sfx/                    # Futuristic sound effects (startup, wake, ack)
    ├── music/                  # Local music directory for clap triggers
    └── screenshots/            # Automated screenshot captures
```
