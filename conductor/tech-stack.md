# Tech Stack: Jarvis Monolith

## Core Language & Environment
- **Language:** Python (>=3.10)
- **Environment Management:** `uv` (for strict dependency locking and fast resolution)

## Core Libraries
- **Audio Capture:** `sounddevice` (captures raw microphone input directly into memory)
- **Data Processing:** `numpy`, `scipy` (handles audio arrays and float32 conversions)
- **Speech-to-Text (STT):** 
  - `faster-whisper` (CTranslate2 engine)
  - `moonshine-voice` (ONNX runtime for ultra-low latency, dynamic-window inference)
- **Input Handling:** 
  - `evdev`: Listens directly to Linux event devices for global hotkey detection.
  - `ydotool`: Injects simulated keypresses into the display server (Wayland/X11).
- **Feedback:** `notify-send` (visual popups) and `aplay` (custom audio cues)

## Deployment & System
- **Operating System:** Linux (Arch/Ubuntu/Debian targeted)
- **Process Management:** `systemd` (runs the script as a background user daemon)
- **Display Server:** Wayland (primary target) / X11 (fallback)
