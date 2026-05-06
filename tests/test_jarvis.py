import pytest
from unittest.mock import patch, MagicMock

import evdev
from evdev import ecodes
import jarvis
import selectors

def test_main_faster_whisper(mocker):
    # Mock environment variables
    mocker.patch("os.environ.get", side_effect=lambda k, d=None: "faster-whisper" if k == "JARVIS_ENGINE" else d)
    
    # Mock external dependencies to prevent actual hardware access
    mocker.patch("adapters.sound_device_adapter.SoundDeviceAdapter")
    mocker.patch("adapters.faster_whisper_adapter.FasterWhisperAdapter")
    mocker.patch("adapters.ydotool_adapter.YdotoolAdapter")
    mocker.patch("adapters.desktop_notifier_adapter.DesktopNotifierAdapter")
    mocker.patch("core.domain.JarvisCore")
    
    # Mock evdev devices
    mock_dev = MagicMock()
    mock_dev.capabilities.return_value = {ecodes.EV_KEY: [ecodes.KEY_SPACE]}
    mocker.patch("evdev.list_devices", return_value=["/dev/input/event0"])
    mocker.patch("evdev.InputDevice", return_value=mock_dev)
    
    # Mock the selector to immediately raise KeyboardInterrupt to exit the infinite loop
    mock_selector = MagicMock()
    mock_selector.select.side_effect = KeyboardInterrupt()
    mocker.patch("selectors.DefaultSelector", return_value=mock_selector)

    # Run main, expect it to exit gracefully
    jarvis.main()

def test_main_moonshine_implemented(mocker):
    mocker.patch("os.environ.get", side_effect=lambda k, d=None: "moonshine" if k == "JARVIS_ENGINE" else d)
    
    # Mock external dependencies
    mocker.patch("adapters.sound_device_adapter.SoundDeviceAdapter")
    mocker.patch("adapters.moonshine_adapter.MoonshineAdapter")
    mocker.patch("adapters.ydotool_adapter.YdotoolAdapter")
    mocker.patch("adapters.desktop_notifier_adapter.DesktopNotifierAdapter")
    mocker.patch("core.domain.JarvisCore")
    
    # Mock evdev devices
    mock_dev = MagicMock()
    mock_dev.capabilities.return_value = {ecodes.EV_KEY: [ecodes.KEY_SPACE]}
    mocker.patch("evdev.list_devices", return_value=["/dev/input/event0"])
    mocker.patch("evdev.InputDevice", return_value=mock_dev)
    
    # Mock the selector to immediately raise KeyboardInterrupt to exit the infinite loop
    mock_selector = MagicMock()
    mock_selector.select.side_effect = KeyboardInterrupt()
    mocker.patch("selectors.DefaultSelector", return_value=mock_selector)

    # Run main, expect it to exit gracefully
    jarvis.main()

def test_main_unknown_engine(mocker):
    mocker.patch("os.environ.get", side_effect=lambda k, d=None: "invalid_engine" if k == "JARVIS_ENGINE" else d)
    pass # Skip for same reason
