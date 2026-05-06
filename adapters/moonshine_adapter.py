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
        model_path, model_arch = get_model_for_language(
            "en", 
            model_name=f"moonshine/{self.model_size}"
        )
        
        # Initialize the ONNX runtime session in RAM
        self.transcriber = Transcriber(model_path=model_path, model_arch=model_arch)

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        if not self.transcriber:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        # Moonshine expects a python list of floats, not a raw numpy array.
        audio_list = audio_data.tolist()
        
        text = self.transcriber.transcribe_without_streaming(
            audio_list, 
            sample_rate=sample_rate
        )
        
        return text.strip() if text else ""
