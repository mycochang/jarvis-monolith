import pytest
import numpy as np
from core.ports import STTProvider, AudioProvider, ActionProvider, FeedbackProvider
from core.domain import JarvisCore

def test_jarvis_core_start_recording(mocker):
    mock_audio = mocker.Mock(spec=AudioProvider)
    mock_stt = mocker.Mock(spec=STTProvider)
    mock_action = mocker.Mock(spec=ActionProvider)
    
    core = JarvisCore(mock_audio, mock_stt, mock_action)
    core.start_recording()
    
    mock_audio.start_recording.assert_called_once()
    assert core.is_recording is True

def test_jarvis_core_stop_and_transcribe(mocker, capsys):
    mock_audio = mocker.Mock(spec=AudioProvider)
    mock_stt = mocker.Mock(spec=STTProvider)
    mock_action = mocker.Mock(spec=ActionProvider)
    
    dummy_audio = np.zeros(16000, dtype=np.float32)
    mock_audio.stop_recording.return_value = dummy_audio
    mock_stt.transcribe.return_value = "hello world"
    
    core = JarvisCore(mock_audio, mock_stt, mock_action)
    core.is_recording = True
    
    core.stop_and_transcribe()
    
    # Wait for the background thread to finish
    import time
    time.sleep(0.1)
    
    mock_audio.stop_recording.assert_called_once()
    mock_stt.transcribe.assert_called_once_with(dummy_audio, core.sample_rate)
    mock_action.type_text.assert_called_once_with("hello world")
    captured = capsys.readouterr()
    assert "hello world" not in captured.out
    assert "Result: [Transcribed 11 characters]" in captured.out
    assert core.is_recording is False
