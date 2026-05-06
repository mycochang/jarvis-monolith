import subprocess
from core.ports import ActionProvider

class YdotoolAdapter(ActionProvider):
    def type_text(self, text: str) -> None:
        if not text:
            return
            
        # Add a trailing space to separate transcribed segments nicely
        text = text + " "
        
        # Use -d 1 and -H 1 for minimum delay to prevent Wayland buffering issues
        subprocess.run(
            ["ydotool", "type", "-d", "1", "-H", "1", text],
            check=True
        )
