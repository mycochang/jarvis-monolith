import os
import subprocess
from core.ports import FeedbackProvider

class DesktopNotifierAdapter(FeedbackProvider):
    def notify(self, message: str) -> None:
        try:
            # -t 1500 makes the notification disappear quickly (1.5 seconds)
            # -h string:x-canonical-private-synchronous:jarvis replaces the old notification 
            # instead of stacking them up on the screen.
            subprocess.Popen([
                "notify-send", 
                "-t", "1500", 
                "-h", "string:x-canonical-private-synchronous:jarvis",
                "🎙️ Jarvis", 
                message
            ])
        except Exception:
            pass # Fail silently if notify-send is missing

    def play_sound(self, sound_name: str) -> None:
        try:
            sound_type = "on" if sound_name == "start" else "off"
            sound_file = f"{os.environ.get('HOME')}/.local/share/voice_assistant/mic_{sound_type}.wav"
            
            if os.path.exists(sound_file):
                subprocess.Popen(["aplay", "-q", sound_file], stderr=subprocess.DEVNULL)
        except Exception:
            pass
