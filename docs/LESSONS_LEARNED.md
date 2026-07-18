# Lessons Learned

## Wayland Input
- Use a single dedicated trigger key (`KEY_COMPOSE` / Menu). `Ctrl+Space` can collide with typed output if Ctrl is still held when `ydotool` starts injecting text.
- Keep `ydotool type -d 1 -H 1`. Zero-delay key events can be dropped by Wayland/KWin as glitches.
- Never listen to virtual keyboards named `ydotool`, or injected text can feed back into the listener.

## Audio
- Default to `sounddevice` device `pulse` so PipeWire/PulseAudio can track USB mic changes. Override with `JARVIS_AUDIO_DEVICE` if hardware routing needs tuning.

## Logging
- Do not print raw dictated text from the systemd service. It lands in the user journal. Log character counts or status only.

## Service
- This machine currently runs `~/.config/systemd/user/jarvis.service` from a linked worktree. The repo unit preserves the required runtime settings (`LD_PRELOAD`, `PYTHONUNBUFFERED`) but points at `%h/repos/jarvis-monolith`.
