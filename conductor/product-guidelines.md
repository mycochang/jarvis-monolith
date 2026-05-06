# Product Guidelines: Jarvis Monolith

## 1. UX Principles
- **Invisible but Present:** The tool must operate entirely in the background. It should only make its presence known through immediate, accurate text injection upon user command.
- **Zero Friction:** Dictation must feel like an extension of the keyboard. No loading screens, no "listening..." popups, and no waiting.
- **System Harmony:** The daemon must respect the host operating system. It should never hog resources while idle or crash the desktop environment (e.g., by aggressively claiming GPU VRAM).

## 2. Architecture & Design Philosophy
- **Monolith over Microservices:** Keep the architecture simple and self-contained within a single runnable script or tightly coupled module to ease deployment and debugging.
- **RAM First:** Prioritize memory-mapped operations and RAM-based buffers over disk I/O to shave off every possible millisecond of latency.
- **Air-Gapped by Default:** Models and dependencies must be capable of running entirely offline. The application should never phone home or rely on external cloud APIs for transcription.

## 3. Code Style & Maintainability
- **Hexagonal / Ports & Adapters:** For any feature involving multiple backends (e.g., switching STT engines from Whisper to Moonshine), strictly decouple the core domain logic from external dependencies using interfaces.
- **Pythonic Precision:** Use modern Python features (type hinting, context managers for resource cleanup) to ensure stability in a long-running daemon.
- **Clear Logging:** Because the application runs headlessly, ensure errors and state changes are clearly logged to `stdout`/`stderr` so they can be captured by `journalctl`.

## 4. Platform Specifics
- **Wayland First:** Always test input injection using `ydotool` on Wayland environments, as X11 fallback tools (like `xdotool`) are deprecated on modern Linux desktops.
- **Dependency Isolation:** Use `uv` (or a strict virtual environment) to tightly lock dependencies (especially C++ bound libraries like `onnxruntime` or `faster-whisper`) to prevent system updates from breaking the daemon.
