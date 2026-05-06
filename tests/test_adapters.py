import pytest
import numpy as np
from adapters.faster_whisper_adapter import FasterWhisperAdapter
from adapters.sound_device_adapter import SoundDeviceAdapter
from adapters.ydotool_adapter import YdotoolAdapter

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

def test_ydotool_adapter_type_text(mocker):
    mock_run = mocker.patch("subprocess.run")
    adapter = YdotoolAdapter()
    
    adapter.type_text("test input")
    
    mock_run.assert_called_once_with(
        ["ydotool", "type", "-d", "1", "-H", "1", "test input "],
        check=True
    )

from adapters.moonshine_adapter import MoonshineAdapter

def test_moonshine_adapter_instantiation():
    adapter = MoonshineAdapter(model_size="base")
    assert adapter is not None

def test_moonshine_adapter_transcribe(mocker):
    adapter = MoonshineAdapter(model_size="base")
    
    mock_transcriber = mocker.Mock()
    mock_transcriber.transcribe_without_streaming.return_value = "Hello moonshine."
    
    adapter.transcriber = mock_transcriber
    
    dummy_audio = np.zeros(16000, dtype=np.float32)
    result = adapter.transcribe(dummy_audio, 16000)
    
    assert result == "Hello moonshine."
    # The adapter should convert the numpy array to a list as required by Moonshine
    mock_transcriber.transcribe_without_streaming.assert_called_once()
    args, kwargs = mock_transcriber.transcribe_without_streaming.call_args
    assert isinstance(args[0], list)
    assert kwargs["sample_rate"] == 16000
