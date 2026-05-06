import numpy as np
import pytest
from core.ports import STTProvider, AudioProvider, ActionProvider, FeedbackProvider

class DummySTTAdapter(STTProvider):
    pass

def test_stt_provider_interface():
    # Attempting to instantiate an abstract base class without implementing
    # its abstract methods should raise a TypeError.
    with pytest.raises(TypeError):
        adapter = DummySTTAdapter()

def test_stt_provider_implemented():
    class ValidSTTAdapter(STTProvider):
        def load_model(self) -> None:
            pass

        def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
            return "test"

    adapter = ValidSTTAdapter()
    assert adapter.transcribe(np.zeros(16000, dtype=np.float32), 16000) == "test"

class DummyAudioAdapter(AudioProvider):
    pass

def test_audio_provider_interface():
    with pytest.raises(TypeError):
        adapter = DummyAudioAdapter()

def test_audio_provider_implemented():
    class ValidAudioAdapter(AudioProvider):
        def start_recording(self) -> None:
            pass
            
        def stop_recording(self) -> np.ndarray:
            return np.zeros(16000, dtype=np.float32)

class DummyActionAdapter(ActionProvider):
    pass

def test_action_provider_interface():
    with pytest.raises(TypeError):
        adapter = DummyActionAdapter()

def test_action_provider_implemented():
    class ValidActionAdapter(ActionProvider):
        def type_text(self, text: str) -> None:
            pass

class DummyFeedbackAdapter(FeedbackProvider):
    pass

def test_feedback_provider_interface():
    with pytest.raises(TypeError):
        adapter = DummyFeedbackAdapter()

def test_feedback_provider_implemented():
    class ValidFeedbackAdapter(FeedbackProvider):
        def notify(self, message: str) -> None:
            pass
        def play_sound(self, sound_name: str) -> None:
            pass

    adapter = ValidFeedbackAdapter()
    adapter.notify("test")
    adapter.play_sound("test")
