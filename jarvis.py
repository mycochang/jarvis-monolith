import os
import sys
import evdev
import selectors
from evdev import ecodes

from core.domain import JarvisCore
from adapters.faster_whisper_adapter import FasterWhisperAdapter
from adapters.sound_device_adapter import SoundDeviceAdapter
from adapters.ydotool_adapter import YdotoolAdapter

# --- Configuration ---
# Allow switching engine via environment variable, default to faster-whisper.
ENGINE = os.environ.get("JARVIS_ENGINE", "faster-whisper")
MODEL_SIZE = os.environ.get("JARVIS_MODEL", "Systran/faster-whisper-base.en")
DEVICE = "cpu"
COMPUTE_TYPE = "int8"
CPU_THREADS = int(os.environ.get("JARVIS_THREADS", 4))
SAMPLE_RATE = 16000
TRIGGER_KEY = ecodes.KEY_SPACE
MODIFIER_KEY = ecodes.KEY_LEFTCTRL

def main():
    print(f"[*] Starting Jarvis Monolith (Engine: {ENGINE})", flush=True)

    # 1. Initialize the correct Adapters
    audio_adapter = SoundDeviceAdapter(sample_rate=SAMPLE_RATE)
    action_adapter = YdotoolAdapter()
    
    if ENGINE == "faster-whisper":
        stt_adapter = FasterWhisperAdapter(
            model_size=MODEL_SIZE, 
            device=DEVICE, 
            compute_type=COMPUTE_TYPE, 
            cpu_threads=CPU_THREADS
        )
    elif ENGINE == "moonshine":
        from adapters.moonshine_adapter import MoonshineAdapter
        # Default to the highly accurate, lightweight "base" model for CPU streaming
        moonshine_size = os.environ.get("JARVIS_MODEL", "base")
        stt_adapter = MoonshineAdapter(model_size=moonshine_size)
    else:
        raise ValueError(f"Unknown engine: {ENGINE}")

    # 2. Inject Adapters into the Core Domain
    core = JarvisCore(
        audio_provider=audio_adapter,
        stt_provider=stt_adapter,
        action_provider=action_adapter,
        sample_rate=SAMPLE_RATE
    )
    
    # 3. Load model weights
    core.initialize()

    # 4. Start Event Listener Loop (Primary Driving Adapter logic)
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    keyboard_devices = [d for d in devices if ecodes.EV_KEY in d.capabilities()]

    if not keyboard_devices:
        print("Error: No keyboards found. Run with sudo or check 'input' group.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Listening on {len(keyboard_devices)} keyboards. Hold Ctrl + Space to dictate.")

    selector = selectors.DefaultSelector()
    for dev in keyboard_devices:
        selector.register(dev, selectors.EVENT_READ)

    modifiers_active = set()
    try:
        while True:
            for key, _ in selector.select():
                device = key.fileobj
                for event in device.read():
                    if event.type == ecodes.EV_KEY:
                        key_event = evdev.categorize(event)
                        
                        # Track modifiers
                        if key_event.scancode == MODIFIER_KEY:
                            if key_event.keystate == key_event.key_down:
                                modifiers_active.add(MODIFIER_KEY)
                            elif key_event.keystate == key_event.key_up:
                                modifiers_active.discard(MODIFIER_KEY)
                                
                        # Handle Trigger
                        if key_event.scancode == TRIGGER_KEY and MODIFIER_KEY in modifiers_active:
                            if key_event.keystate == key_event.key_down:
                                core.start_recording()
                            elif key_event.keystate == key_event.key_up:
                                core.stop_and_transcribe()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")

if __name__ == "__main__":
    main()
