import numpy as np
import pytest
from core.ports import STTProvider

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
