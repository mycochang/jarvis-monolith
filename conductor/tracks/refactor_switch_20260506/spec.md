# Specification: Refactor architecture for switchable STT engines

## Overview
The goal of this track is to refactor the current `jarvis-monolith` codebase into a Hexagonal Architecture (Ports and Adapters). This will allow the application to dynamically switch between different Speech-to-Text (STT) engines, starting with support for the existing `faster-whisper` and the new `Moonshine` engine, without altering the core domain logic.

## Scope
- **Core Domain Isolation:** Separate the state machine and audio buffering logic from hardware/external dependencies.
- **Port Definitions:** Define clear interfaces for Audio Input, STT Processing, Action Injection, and User Feedback.
- **Adapter Implementations:** Implement adapters for `sounddevice` (Audio), `faster-whisper` (STT), `ydotool` (Action), and `notify-send`/`aplay` (Feedback).
- **Dependency Injection:** Modify the main application entry point to inject dependencies based on environment configuration (`JARVIS_ENGINE`).

## Constraints
- **Zero Latency Target:** The refactored architecture must not introduce any noticeable latency overhead.
- **Backwards Compatibility:** The default configuration must behave exactly as the current monolith does, using `faster-whisper` (`base.en`).

## Deliverables
- A refactored `jarvis.py` (or a set of modules) implementing the Hexagonal Architecture.
- Functional adapters for the existing tech stack.
- Updated documentation reflecting the new architecture.
