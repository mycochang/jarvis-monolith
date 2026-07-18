# Jarvis Monolith

A zero-latency, CPU-only voice dictation tool designed specifically for Linux (Wayland/X11).
It keeps a local STT model in RAM, records straight from your microphone to memory, and uses `ydotool` to inject text instantly. No cloud. No transcript logs.

## Installation

1. **Permissions:** Ensure your user is in the `input` group to read keyboard events:
   ```bash
   sudo usermod -aG input $USER
   ```
2. **Setup Environment:** Use `uv` to pull dependencies safely:
   ```bash
   uv sync
   ```
3. **Daemonize `ydotool`:** Required for typing into Wayland windows:
    ```bash
    sudo pacman -S ydotool
    systemctl --user enable --now ydotool.service
    ```
4. **Auto-Start (Optional):**
   ```bash
   cp systemd/jarvis.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now jarvis.service
   ```

## Usage
Hold the **Compose/Menu** key, speak, and release to type.

`Ctrl+Space` is intentionally not used: if Ctrl is still physically held when `ydotool` starts typing, the transcript can turn into desktop shortcuts.

## Runtime Notes

- Default engine: `moonshine`; override with `JARVIS_ENGINE=faster-whisper`.
- Default audio device: `pulse`; override with `JARVIS_AUDIO_DEVICE` if hardware routing needs tuning.
- Text injection uses `ydotool type -d 1 -H 1`; zero-delay events can be dropped by Wayland/KWin.
- The systemd service logs status and character counts only, never raw dictated text.
- Local discoveries live in [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md).

## Architecture & Replicability
This repo is entirely self-contained. The AI models are saved directly into the `models/` directory, so you can back up this entire folder to an external drive and run it air-gapped on any Linux machine.

## Architecture

```text
========================================================================
                      JARVIS MONOLITH ARCHITECTURE                      
========================================================================

[ Physical Keyboard(s) ]
       | (Hardware Events: Compose/Menu)
       v
+----------------------------------------------------------------------+
|                         jarvis.py (Python)                           |
|                                                                      |
|  1. [evdev Listener]  <-- Detects Compose/Menu across connected boards|
|           |                                                          |
|           v (Trigger)                                                |
|  2. [sounddevice]     <-- Records Mic directly to RAM (NumPy array)  |
|           |                                                          |
|           v (Float32 Array)                                          |
|  3. [STT Engine]      <-- Moonshine or faster-whisper in RAM          |
|           |               (CPU-only, local inference)                 |
|           v (Text string)                                            |
|  4. [ydotool]         <-- Spawns subprocess to type text directly    |
+----------------------------------------------------------------------+
       | (CLI Command: ydotool type -d 1 -H 1 "text")
       v
[ Virtual Keyboard (ydotoold) ]
       |
       v
[ Active Wayland/X11 Window ]
```
