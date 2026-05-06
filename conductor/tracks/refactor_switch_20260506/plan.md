# Implementation Plan: Refactor architecture for switchable STT engines

## Phase 1: Define Interfaces (Ports) [checkpoint: 642c483]
- [x] Task: Define `STTProvider` interface outlining methods for model loading and transcription. [dfa4908]
- [x] Task: Define `AudioProvider` interface outlining methods for capturing audio arrays. [842eb9e]
- [x] Task: Define `ActionProvider` interface outlining methods for text injection. [079eb8f]
- [x] Task: Define `FeedbackProvider` interface outlining methods for user notifications. [d0f562d]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Define Interfaces (Ports)' (Protocol in workflow.md)

## Phase 2: Implement Adapters for Current Stack [checkpoint: a26cab8]
- [x] Task: Implement `FasterWhisperAdapter` conforming to `STTProvider`. [5111793]
- [x] Task: Implement `SoundDeviceAdapter` conforming to `AudioProvider`. [023e7d5]
- [x] Task: Implement `YdotoolAdapter` conforming to `ActionProvider`. [9306528]
- [x] Task: Conductor - User Manual Verification 'Phase 2: Implement Adapters for Current Stack' (Protocol in workflow.md)

## Phase 3: Core Domain Refactoring
- [x] Task: Extract state machine and coordination logic from `jarvis.py` into a `JarvisCore` class. [3f0062f]
- [x] Task: Refactor `JarvisCore` to accept Ports via constructor injection. [3f0062f]
- [x] Task: Update the main entry point to instantiate adapters and inject them into `JarvisCore`. [ec36d3d]
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Core Domain Refactoring' (Protocol in workflow.md)

## Phase 3.5: Moonshine Adapter Implementation [checkpoint: 4686c8d]
- [x] Task: Implement `MoonshineAdapter` strictly adhering to the `STTProvider` interface. [4686c8d]
- [x] Task: Ensure the adapter targets CPU-only inference using the bundled `onnxruntime`. [4686c8d]

## Phase 5: Polish & Feedback Adjustments
- [x] Task: Update `DesktopNotifierAdapter.play_sound` to use the original `aplay` logic pointing to `~/.local/share/voice_assistant/mic_on.wav` and `mic_off.wav`.
