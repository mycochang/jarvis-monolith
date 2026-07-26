import pytest
import numpy as np
from core.ports import STTProvider, AudioProvider, ActionProvider, FeedbackProvider, MediaProvider
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


def test_media_paused_on_start_and_resumed_on_stop(mocker):
    """Media that was playing gets paused at start and resumed at stop."""
    mock_audio = mocker.Mock(spec=AudioProvider)
    mock_stt = mocker.Mock(spec=STTProvider)
    mock_action = mocker.Mock(spec=ActionProvider)
    mock_media = mocker.Mock(spec=MediaProvider)
    mock_media.pause.return_value = True  # was playing

    dummy_audio = np.zeros(16000, dtype=np.float32)
    mock_audio.stop_recording.return_value = dummy_audio
    mock_stt.transcribe.return_value = "test"

    core = JarvisCore(mock_audio, mock_stt, mock_action, media_provider=mock_media)
    core.start_recording()
    mock_media.pause.assert_called_once()
    assert core._media_was_playing is True

    core.stop_and_transcribe()
    mock_media.resume.assert_called_once()
    assert core._media_was_playing is False


def test_media_not_resumed_when_was_already_paused(mocker):
    """If nothing was playing before recording, resume must not be called."""
    mock_audio = mocker.Mock(spec=AudioProvider)
    mock_stt = mocker.Mock(spec=STTProvider)
    mock_action = mocker.Mock(spec=ActionProvider)
    mock_media = mocker.Mock(spec=MediaProvider)
    mock_media.pause.return_value = False  # nothing was playing

    dummy_audio = np.zeros(16000, dtype=np.float32)
    mock_audio.stop_recording.return_value = dummy_audio
    mock_stt.transcribe.return_value = "test"

    core = JarvisCore(mock_audio, mock_stt, mock_action, media_provider=mock_media)
    core.start_recording()
    assert core._media_was_playing is False

    core.stop_and_transcribe()
    mock_media.resume.assert_not_called()


def test_no_media_provider_does_not_break_recording(mocker):
    """When no media_provider is wired, recording still works normally."""
    mock_audio = mocker.Mock(spec=AudioProvider)
    mock_stt = mocker.Mock(spec=STTProvider)
    mock_action = mocker.Mock(spec=ActionProvider)

    dummy_audio = np.zeros(16000, dtype=np.float32)
    mock_audio.stop_recording.return_value = dummy_audio
    mock_stt.transcribe.return_value = "test"

    core = JarvisCore(mock_audio, mock_stt, mock_action)
    core.start_recording()
    assert core.is_recording is True
    core.stop_and_transcribe()
    assert core.is_recording is False
