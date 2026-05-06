import pytest
import numpy as np
from adapters.faster_whisper_adapter import FasterWhisperAdapter

def test_faster_whisper_adapter_instantiation():
    # Should instantiate without errors if it implements STTProvider
    adapter = FasterWhisperAdapter(model_size="tiny.en", device="cpu", compute_type="int8", cpu_threads=1)
    assert adapter is not None

def test_faster_whisper_adapter_transcribe(mocker):
    adapter = FasterWhisperAdapter(model_size="tiny.en", device="cpu", compute_type="int8", cpu_threads=1)
    
    # Mock the actual model to avoid downloading/running inference during unit tests
    mock_model = mocker.Mock()
    mock_segment = mocker.Mock()
    mock_segment.text = " Hello world."
    mock_model.transcribe.return_value = ([mock_segment], None)
    
    adapter.model = mock_model
    
    dummy_audio = np.zeros(16000, dtype=np.float32)
    result = adapter.transcribe(dummy_audio, 16000)
    
    assert result == "Hello world."
    mock_model.transcribe.assert_called_once()
