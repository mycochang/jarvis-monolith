"""Standalone CUDA smoke-test for faster-whisper. No app imports.

Automatically prepends the nvidia pip-package lib dirs to LD_LIBRARY_PATH so
ctranslate2 can find libcublas.so.12 and libcudnn without a system install.
"""
import os
import subprocess
import sys

_PATCHED = "_CUDA_TEST_LD_PATCHED"


def _nvidia_lib_dirs() -> list[str]:
    """Return lib dirs from pip-installed nvidia-* packages in the active venv."""
    try:
        import site
        dirs = []
        for sp in site.getsitepackages():
            nvidia_root = os.path.join(sp, "nvidia")
            if os.path.isdir(nvidia_root):
                for pkg in sorted(os.listdir(nvidia_root)):
                    lib = os.path.join(nvidia_root, pkg, "lib")
                    if os.path.isdir(lib):
                        dirs.append(lib)
        return dirs
    except Exception:
        return []


def _ensure_cuda_libs_on_path() -> None:
    """Re-exec with LD_LIBRARY_PATH patched if not already done."""
    if os.environ.get(_PATCHED):
        return
    extra = _nvidia_lib_dirs()
    if not extra:
        return
    existing = os.environ.get("LD_LIBRARY_PATH", "")
    parts = extra + ([existing] if existing else [])
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ":".join(parts)
    env[_PATCHED] = "1"
    os.execve(sys.executable, [sys.executable] + sys.argv, env)


def vram_used_mib() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except Exception as e:
        return f"(nvidia-smi error: {e})"


def main() -> int:
    _ensure_cuda_libs_on_path()

    import ctranslate2

    if ctranslate2.get_cuda_device_count() < 1:
        print("SKIP: no CUDA")
        return 0

    import numpy as np
    from faster_whisper import WhisperModel

    vram_before = vram_used_mib()
    print(f"VRAM before: {vram_before} MiB")

    try:
        model = WhisperModel(
            "Systran/faster-whisper-base.en",
            device="cuda",
            compute_type="float16",
            download_root="models",
        )
    except Exception as e:
        print(f"FAIL: model load error: {e}", file=sys.stderr)
        return 1

    vram_after = vram_used_mib()
    print(f"VRAM after model load: {vram_after} MiB")

    # 5 seconds of near-silence
    audio = (np.random.randn(16000 * 5) * 0.001).astype(np.float32)

    try:
        segments, _ = model.transcribe(audio, beam_size=1, language="en")
        text = "".join(s.text for s in segments)
        print(f"Transcription (near-silence): '{text.strip()}'")
    except Exception as e:
        print(f"FAIL: transcribe error: {e}", file=sys.stderr)
        return 1

    vram_infer = vram_used_mib()
    print(f"VRAM after inference: {vram_infer} MiB")
    print("OK: CUDA inference succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
