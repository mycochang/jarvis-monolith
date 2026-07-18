import queue
import numpy as np
import sounddevice as sd
from core.ports import AudioProvider

class SoundDeviceAdapter(AudioProvider):
    def __init__(self, sample_rate: int = 16000, device: str = "pulse"):
        self.sample_rate = sample_rate
        self.device = device
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None

    def _audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if self.is_recording:
            self.audio_queue.put(indata.copy())

    def start_recording(self) -> None:
        self.is_recording = True
        # Clear any old data
        while not self.audio_queue.empty():
            self.audio_queue.get()
            
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            device=self.device,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop_recording(self) -> np.ndarray:
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
            
        if not audio_data:
            return np.zeros(0, dtype=np.float32)
            
        # Concatenate and flatten to 1D array
        return np.concatenate(audio_data, axis=0).flatten()
