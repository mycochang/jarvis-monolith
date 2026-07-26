import sys
import threading
from core.ports import STTProvider, AudioProvider, ActionProvider, FeedbackProvider, MediaProvider

class JarvisCore:
    def __init__(self,
                 audio_provider: AudioProvider,
                 stt_provider: STTProvider,
                 action_provider: ActionProvider,
                 feedback_provider: FeedbackProvider = None,
                 media_provider: MediaProvider = None,
                 sample_rate: int = 16000):
        self.audio = audio_provider
        self.stt = stt_provider
        self.action = action_provider
        self.feedback = feedback_provider
        self.media = media_provider
        self.sample_rate = sample_rate
        self.is_recording = False
        self._media_was_playing = False

    def initialize(self):
        print("[*] Initializing STT Model. This may take a moment...", flush=True)
        self.stt.load_model()
        print("[*] Model loaded. Ready.", flush=True)

    def start_recording(self):
        if not self.is_recording:
            self.is_recording = True
            if self.media:
                self._media_was_playing = self.media.pause()
            print("[Start Recording]", flush=True)
            if self.feedback:
                self.feedback.play_sound("start")
                self.feedback.notify("Recording... (Speak now)")
            self.audio.start_recording()

    def stop_and_transcribe(self):
        if self.is_recording:
            self.is_recording = False
            if self.media and self._media_was_playing:
                self.media.resume()
                self._media_was_playing = False
            print("[Stop Recording. Transcribing...]", flush=True)
            if self.feedback:
                self.feedback.play_sound("stop")
                self.feedback.notify("Transcribing...")
            
            audio_data = self.audio.stop_recording()
            
            if len(audio_data) == 0:
                print("[-] No audio recorded.", flush=True)
                return

            def _transcribe_and_type():
                try:
                    text = self.stt.transcribe(audio_data, self.sample_rate)
                    if text:
                        print(f"Result: [Transcribed {len(text)} characters]", flush=True)
                        self.action.type_text(text)
                except Exception as e:
                    print(f"Transcription error: {e}", file=sys.stderr, flush=True)

            # Fire off the transcription in a background thread so we don't 
            # block the evdev listener loop.
            t = threading.Thread(target=_transcribe_and_type)
            t.daemon = True
            t.start()
