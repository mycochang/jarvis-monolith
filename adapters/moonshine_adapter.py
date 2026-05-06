import numpy as np
from core.ports import STTProvider

class MoonshineAdapter(STTProvider):
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.transcriber = None

    def load_model(self) -> None:
        # Import lazily so the main app doesn't crash if the library isn't installed 
        # when running in faster-whisper mode.
        from moonshine_voice import Transcriber, get_model_for_language
        
        # Download/cache the ONNX weights
        model_path, model_arch = get_model_for_language("en")
        
        # Initialize the ONNX runtime session in RAM
        self.transcriber = Transcriber(model_path=model_path, model_arch=model_arch)

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        if not self.transcriber:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        # Moonshine expects a python list of floats, not a raw numpy array.
        audio_list = audio_data.tolist()
        
        result = self.transcriber.transcribe_without_streaming(
            audio_list, 
            sample_rate=sample_rate
        )
        
        # Moonshine returns a Transcript object which contains segments/lines.
        if result and hasattr(result, 'text'):
            return result.text.strip()
        elif result and hasattr(result, 'lines'):
             return " ".join([line.text for line in result.lines]).strip()
        elif isinstance(result, str):
            return result.strip()
        return ""
