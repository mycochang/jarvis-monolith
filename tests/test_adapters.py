import pytest
import numpy as np
from adapters.faster_whisper_adapter import FasterWhisperAdapter
from adapters.sound_device_adapter import SoundDeviceAdapter

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

def test_sound_device_adapter_flow(mocker):
    adapter = SoundDeviceAdapter(sample_rate=16000)
    
    # Mock the sounddevice InputStream to avoid actual hardware capture
    mock_stream = mocker.patch("sounddevice.InputStream")
    
    adapter.start_recording()
    assert adapter.is_recording is True
    assert adapter.stream is not None
    
    # Simulate the callback adding some data
    dummy_data = np.zeros((100, 1), dtype=np.float32)
    adapter._audio_callback(dummy_data, 100, None, None)
    
    result = adapter.stop_recording()
    
    assert adapter.is_recording is False
    assert isinstance(result, np.ndarray)
    assert len(result) == 100
