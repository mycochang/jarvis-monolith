import ctypes
import os
import threading
import time

import numpy as np
from faster_whisper import WhisperModel

from core.ports import STTProvider

_libc = ctypes.CDLL("libc.so.6")


def _mem_available_mb() -> int:
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    return 1 << 30


def _ensure_cuda_libs_on_path() -> None:
    """Re-exec with LD_LIBRARY_PATH patched so pip-installed cuBLAS/cuDNN are findable."""
    _PATCHED = "_JARVIS_LD_PATCHED"
    if os.environ.get(_PATCHED):
        return
    import site
    dirs = []
    for sp in site.getsitepackages():
        nvidia_root = os.path.join(sp, "nvidia")
        if os.path.isdir(nvidia_root):
            for pkg in sorted(os.listdir(nvidia_root)):
                lib = os.path.join(nvidia_root, pkg, "lib")
                if os.path.isdir(lib):
                    dirs.append(lib)
    if not dirs:
        return
    existing = os.environ.get("LD_LIBRARY_PATH", "")
    parts = dirs + ([existing] if existing else [])
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ":".join(parts)
    env[_PATCHED] = "1"
    import sys
    os.execve(sys.executable, [sys.executable] + sys.argv, env)


class FasterWhisperAdapter(STTProvider):
    """Keeps CTranslate2 weights resident, but evicts them when idle or when the box
    needs the RAM back. Eviction calls ct2's unload_model() rather than dropping the
    WhisperModel, so tokenizer/feature-extractor stay built and a reload is ~0.7s off
    page cache instead of a cold re-init."""

    def __init__(
        self,
        model_size: str,
        device: str,
        compute_type: str,
        cpu_threads: int,
        idle_unload_s: float = 300.0,
        min_available_mb: int = 4096,
        poll_s: float = 5.0,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads
        self.idle_unload_s = idle_unload_s
        self.min_available_mb = min_available_mb
        self.poll_s = poll_s

        self.model: WhisperModel | None = None
        self._lock = threading.RLock()
        self._last_used = 0.0

    def load_model(self) -> None:
        with self._lock:
            if self.device == "cuda":
                _ensure_cuda_libs_on_path()
                try:
                    self.model = WhisperModel(
                        model_size_or_path=self.model_size,
                        device=self.device,
                        compute_type=self.compute_type,
                        cpu_threads=self.cpu_threads,
                        download_root="models",
                    )
                except Exception as e:
                    print(f"[!] CUDA init failed ({e}), falling back to CPU/int8.", flush=True)
                    self.device = "cpu"
                    self.compute_type = "int8"
                    self.model = WhisperModel(
                        model_size_or_path=self.model_size,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=self.cpu_threads,
                        download_root="models",
                    )
            else:
                self.model = WhisperModel(
                    model_size_or_path=self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=self.cpu_threads,
                    download_root="models",
                )
            self._last_used = time.monotonic()

        if self.idle_unload_s > 0 or self.min_available_mb > 0:
            threading.Thread(target=self._watch, daemon=True).start()

    @property
    def resident(self) -> bool:
        return self.model is not None and self.model.model.model_is_loaded

    def unload(self, reason: str = "manual") -> None:
        with self._lock:
            if not self.resident:
                return
            self.model.model.unload_model()
            # ct2 hands the arenas back to glibc, not the kernel; trim does the rest.
            _libc.malloc_trim(0)
            print(f"[*] Weights evicted ({reason}).", flush=True)

    def ensure_resident(self) -> None:
        with self._lock:
            if self.model is None:
                raise RuntimeError("Model not loaded. Call load_model() first.")
            if not self.resident:
                t0 = time.monotonic()
                self.model.model.load_model()
                print(f"[*] Weights reloaded in {time.monotonic() - t0:.2f}s.", flush=True)

    def _watch(self) -> None:
        while True:
            time.sleep(self.poll_s)
            with self._lock:
                if not self.resident:
                    continue
                idle = time.monotonic() - self._last_used
                if self.idle_unload_s > 0 and idle > self.idle_unload_s:
                    self.unload(f"idle {idle:.0f}s")
                elif self.min_available_mb > 0:
                    avail = _mem_available_mb()
                    if avail < self.min_available_mb:
                        self.unload(f"MemAvailable {avail}MB")

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        with self._lock:
            self.ensure_resident()
            self._last_used = time.monotonic()
            segments, _ = self.model.transcribe(
                audio=audio_data,
                beam_size=1,
                language="en",
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            text = "".join(segment.text for segment in segments)
            # Segments are lazy: only now are the weights actually done being read.
            self._last_used = time.monotonic()
        return text.strip()


def demo() -> None:
    def rss_mb() -> int:
        return int(open(f"/proc/{os.getpid()}/statm").read().split()[1]) * 4096 // 1048576

    adapter = FasterWhisperAdapter(
        model_size=os.environ.get("JARVIS_MODEL", "Systran/faster-whisper-small.en"),
        device="cpu",
        compute_type="int8",
        cpu_threads=8,
        idle_unload_s=0,
        min_available_mb=0,
    )
    adapter.load_model()
    audio = (np.random.randn(16000 * 4) * 0.02).astype(np.float32)

    adapter.transcribe(audio, 16000)
    assert adapter.resident
    hot = rss_mb()

    adapter.unload("demo")
    assert not adapter.resident
    cold = rss_mb()
    assert cold < hot - 100, f"eviction reclaimed only {hot - cold}MB"

    t0 = time.monotonic()
    adapter.transcribe(audio, 16000)
    assert adapter.resident, "transcribe must self-heal after eviction"
    print(f"OK cpu hot={hot}MB evicted={cold}MB reload+infer={time.monotonic() - t0:.2f}s")

    # CUDA path (opt-in, skip gracefully if unavailable)
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() < 1:
            print("SKIP: no CUDA device")
            return
    except Exception:
        print("SKIP: ctranslate2 unavailable")
        return

    _ensure_cuda_libs_on_path()
    cuda_adapter = FasterWhisperAdapter(
        model_size=os.environ.get("JARVIS_MODEL", "Systran/faster-whisper-small.en"),
        device="cuda",
        compute_type="float16",
        cpu_threads=8,
        idle_unload_s=0,
        min_available_mb=0,
    )
    cuda_adapter.load_model()
    # After load_model(), device may have fallen back to cpu if CUDA init failed.
    effective = cuda_adapter.device
    t0 = time.monotonic()
    cuda_adapter.transcribe(audio, 16000)
    print(f"OK cuda({effective}) infer={time.monotonic() - t0:.2f}s")


if __name__ == "__main__":
    demo()
