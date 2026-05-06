# Jarvis Monolith Product Guide

## Initial Concept
A zero-latency, CPU-only voice dictation tool designed specifically for Linux (Wayland/X11).

## Target Audience
- Linux desktop users (especially Wayland users).
- Developers or writers who require instant, friction-free voice-to-text dictation.
- Privacy-conscious individuals needing a completely local, air-gapped solution with no cloud dependency.

## Core Problems Solved
- **Latency:** Eliminates the delays found in cloud-based STT or disk-reliant local setups by keeping models in RAM and streaming audio arrays directly to memory.
- **Wayland Compatibility:** Overcomes the limitations of traditional X11 macro tools by utilizing `ydotool` to simulate hardware keyboard events, ensuring text injection works seamlessly across any active Wayland or X11 application.
- **Privacy & Portability:** Everything runs locally. Models are stored in the project directory, making the entire setup air-gappable and portable.

## Key Features
- **Global Hotkey Trigger:** Uses `evdev` to listen for a global `Ctrl+Space` shortcut across all connected input devices.
- **Interactive HUD:** Provides immediate visual (`notify-send`) and audio (`aplay`) feedback when recording starts and stops to prevent state confusion.
- **In-Memory Audio Processing:** Captures microphone input directly into a NumPy array using `sounddevice` (no temporary `.wav` files).
- **Switchable STT Engines:** Built on a Hexagonal Architecture, allowing seamless switching between `faster-whisper` and `Moonshine` engines via environment variables (`JARVIS_ENGINE`).
- **Universal Text Injection:** Spawns a `ydotool` subprocess to instantly type the transcribed text into the currently focused window.
- **Background Daemon:** Designed to run silently as a `systemd` user service.

## Success Metrics
- **Transcription Latency:** Time from releasing the hotkey to text appearing on screen should be consistently under 0.5 seconds for short phrases.
- **Resource Efficiency:** Minimal idle CPU and RAM usage to prevent interference with other desktop applications (especially avoiding GPU VRAM contention).
- **Reliability:** The daemon should remain stable and responsive without crashing or leaking memory during prolonged desktop sessions.
