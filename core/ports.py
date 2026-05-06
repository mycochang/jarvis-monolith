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
        
        Returns:
            str: The transcribed text.
        """
        pass

class AudioProvider(ABC):
    """
    Interface for capturing audio data.
    """

    @abstractmethod
    def start_recording(self) -> None:
        """
        Start capturing audio into a buffer.
        """
        pass

    @abstractmethod
    def stop_recording(self) -> np.ndarray:
        """
        Stop capturing audio and return the buffer.
        
        Returns:
            np.ndarray: The captured audio data as a NumPy array.
        """
        pass

class ActionProvider(ABC):
    """
    Interface for injecting or typing text into the system.
    """

    @abstractmethod
    def type_text(self, text: str) -> None:
        """
        Simulate typing the provided text.
        
        Args:
            text (str): The text to be typed.
        """
        pass

class FeedbackProvider(ABC):
    """
    Interface for providing feedback to the user.
    """

    @abstractmethod
    def notify(self, message: str) -> None:
        """
        Send a desktop notification.
        
        Args:
            message (str): The message to display.
        """
        pass

    @abstractmethod
    def play_sound(self, sound_name: str) -> None:
        """
        Play an audio cue.
        
        Args:
            sound_name (str): Identifier for the sound to play.
        """
        pass
