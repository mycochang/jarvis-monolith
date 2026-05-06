from abc import ABC, abstractmethod
import numpy as np

class STTProvider(ABC):
    """
    Interface for Speech-to-Text engines.
    """

    @abstractmethod
    def load_model(self) -> None:
        """
        Load the model into memory.
        """
        pass

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe the provided audio data into text.
        
        Args:
            audio_data (np.ndarray): The audio array to transcribe.
            sample_rate (int): The sample rate of the audio data.
            
        Returns:
            str: The transcribed text.
        """
        pass
