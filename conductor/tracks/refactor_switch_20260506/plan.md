# Implementation Plan: Refactor architecture for switchable STT engines

## Phase 1: Define Interfaces (Ports) [checkpoint: 642c483]
- [x] Task: Define `STTProvider` interface outlining methods for model loading and transcription. [dfa4908]
- [x] Task: Define `AudioProvider` interface outlining methods for capturing audio arrays. [842eb9e]
- [x] Task: Define `ActionProvider` interface outlining methods for text injection. [079eb8f]
- [x] Task: Define `FeedbackProvider` interface outlining methods for user notifications. [d0f562d]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Define Interfaces (Ports)' (Protocol in workflow.md)

## Phase 2: Implement Adapters for Current Stack
- [x] Task: Implement `FasterWhisperAdapter` conforming to `STTProvider`. [5111793]
- [ ] Task: Implement `SoundDeviceAdapter` conforming to `AudioProvider`.
- [ ] Task: Implement `YdotoolAdapter` conforming to `ActionProvider`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implement Adapters for Current Stack' (Protocol in workflow.md)

## Phase 3: Core Domain Refactoring
- [ ] Task: Extract state machine and coordination logic from `jarvis.py` into a `JarvisCore` class.
- [ ] Task: Refactor `JarvisCore` to accept Ports via constructor injection.
- [ ] Task: Update the main entry point to instantiate adapters and inject them into `JarvisCore`.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Core Domain Refactoring' (Protocol in workflow.md)

## Phase 4: Testing & Validation
- [ ] Task: Verify `faster-whisper` transcription works identically to the previous version.
- [ ] Task: Verify hotkey detection and `ydotool` injection work seamlessly.
- [ ] Task: Verify latency metrics have not regressed.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Testing & Validation' (Protocol in workflow.md)
