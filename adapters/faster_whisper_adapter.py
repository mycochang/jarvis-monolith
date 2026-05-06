import numpy as np
from faster_whisper import WhisperModel
from core.ports import STTProvider

class FasterWhisperAdapter(STTProvider):
    def __init__(self, model_size: str, device: str, compute_type: str, cpu_threads: int):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads
        self.model = None

    def load_model(self) -> None:
        self.model = WhisperModel(
            model_size_or_path=self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=self.cpu_threads,
            download_root="models"
        )

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        segments, _ = self.model.transcribe(
            audio=audio_data,
            beam_size=1,
            language="en",
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Combine segments
        text = "".join(segment.text for segment in segments)
        return text.strip()
