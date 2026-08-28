# Jarvis Monolith

A zero-latency, CPU-only voice dictation tool designed specifically for Linux (Wayland/X11).
It keeps a local STT model in RAM, records straight from your microphone to memory, and uses `ydotool` to inject text instantly. No cloud. No transcript logs.

## Installation

1. **Permissions:** Ensure your user is in the `input` group to read keyboard events:
   ```bash
   sudo usermod -aG input $USER
   ```
2. **Setup Environment:** Use `uv` to pull dependencies safely:
   ```bash
   uv sync
   ```
3. **Daemonize `ydotool`:** Required for typing into Wayland windows:
    ```bash
    sudo pacman -S ydotool
    systemctl --user enable --now ydotool.service
    ```
4. **Auto-Start (Optional):**
   ```bash
   cp systemd/jarvis.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now jarvis.service
   ```

## Usage
Hold the **Compose/Menu** key, speak, and release to type.

`Ctrl+Space` is intentionally not used: if Ctrl is still physically held when `ydotool` starts typing, the transcript can turn into desktop shortcuts.

## Runtime Notes

- Default engine: `moonshine`; override with `JARVIS_ENGINE=faster-whisper`.
- Default audio device: `pulse`; override with `JARVIS_AUDIO_DEVICE` if hardware routing needs tuning.
- Text injection uses `ydotool type -d 1 -H 1`; zero-delay events can be dropped by Wayland/KWin.
- The systemd service logs status and character counts only, never raw dictated text.
- Local discoveries live in [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md).

## RAM residency (`faster-whisper` engine)

Weights stay resident for instant dictation, but the adapter evicts them when idle or
when the machine gets tight, and transparently reloads on the next keypress. Reload is
~0.6s because eviction drops only the CTranslate2 weights (`unload_model()`), leaving
tokenizer and feature extractor built; the weights come back off page cache.

| Variable | Default | Meaning |
|---|---|---|
| `JARVIS_MODEL` | `Systran/faster-whisper-base.en` | Any faster-whisper / CT2 repo id |
| `JARVIS_IDLE_UNLOAD_S` | `300` | Evict after this many idle seconds; `0` = never |
| `JARVIS_MIN_AVAILABLE_MB` | `4096` | Evict when `MemAvailable` drops below this; `0` = never |
| `JARVIS_THREADS` | `4` | CT2 CPU threads |
| `JARVIS_DEVICE` / `JARVIS_COMPUTE_TYPE` | `cpu` / `int8` | `cuda` + `float16` for GPU; requires NVIDIA with cuBLAS+cuDNN pip packages. Default is CPU — GPU is opt-in. |

Measured on this box, `int8` on CPU, 8 threads:

| Model | Resident | Warm load |
|---|---|---|
| `base.en` | ~260 MB | 0.6s |
| `small.en` | ~440 MB | 0.7s |
| `distil-large-v3.5-ct2` | ~1.900 GB | 1.6s |

Eviction is cheap, so residency is a RAM question. Model choice is not: it costs real
latency — see [`bench/`](bench/) for the accuracy/latency numbers.

To force eviction before a heavy job, restart the unit — or set a high
`JARVIS_MIN_AVAILABLE_MB` so the watcher yields automatically under pressure.

## GPU acceleration (opt-in)

**How to enable:**
```bash
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
JARVIS_DEVICE=cuda JARVIS_COMPUTE_TYPE=float16 systemctl --user restart jarvis
```

**Display-safety — verify before enabling on your machine.**
Prior GPU attempts crashed the compositor. Investigation on this machine found:

- `renderD128` = NVIDIA RTX 3070 Mobile (driver: `nvidia`)
- `renderD129` = AMD Radeon Vega iGPU (driver: `amdgpu`)
- KWin/Wayland compositor uses the AMD card via KMS (`card2`) — confirmed by
  checking open file descriptors: `kwin_wayland` holds NO fd to either render node.
- NVIDIA VRAM at test time: 85 MiB / 8192 MiB used — essentially idle.
- **CUDA allocation on the NVIDIA GPU is safe on this machine because the display
  compositor runs entirely on the AMD card.**

This is hardware-specific. On Optimus laptops where the compositor IS on the NVIDIA
GPU, a large CUDA alloc exhausting VRAM can crash the desktop. Always check:
```bash
# which /dev/dri/card* does kwin_wayland have open?
ls -la /proc/$(pgrep kwin_wayland)/fd | grep card
# which render node is that card?
ls -la /dev/dri/
```

**Measured numbers** (190s podcast audio, 25s chunks, taskset -c 8-15):

| Config | WER vs captions | Min | Median |
|---|---|---|---|
| `base.en` beam1 CPU int8 | 21.8% | 2603ms | 2804ms |
| `base.en` beam1 CUDA float16 | 23.9% | 485ms | 494ms |
| `small.en` beam1 CPU int8 | 20.4% | 3500ms | 3508ms |
| `small.en` beam1 CUDA float16 | 20.0% | 382ms | 383ms |

GPU is **7–9x faster** than CPU. `small.en` on CUDA is both the most accurate and the
fastest config — it costs 382ms median vs 3508ms on CPU.

**VRAM usage** (base.en float16):
- Before model load: 88 MiB used
- After model load: 455 MiB used (~367 MiB allocated)
- After inference: 473 MiB used

**Fallback behavior:** if `JARVIS_DEVICE=cuda` is set but CUDA initialization fails
(missing libs, no GPU, OOM), the adapter logs a warning and falls back to CPU/int8
automatically — the dictation service keeps running.

## Benchmarking

`bench/` measures latency and accuracy for STT configs against real speech.

```bash
python bench/bench.py corpus add "<youtube-url>" --at 20:00 --for 3:00
taskset -c 8-15 python bench/bench.py run --configs base.en:1,small.en:1,small.en:5
```

Two traps this suite exists to avoid, both hit the hard way:

- **Pin the CPU.** Unpinned on a loaded box, identical work measured 2620–6839ms. That
  5x spread swamps the ~5% differences you're trying to measure. Trust `min`, not `mean`,
  and the runner warns when between-config spread is smaller than within-config noise.
- **The reference must be a different ASR family.** Scoring small Whisper against large
  Whisper hides their shared failure modes and flatters both. YouTube auto-captions are
  independent, so disagreement is informative — but they carry their own errors, so
  absolute WER overstates. Rank configs with it; only a human transcript is ground truth.

Findings so far, on 190s of multi-speaker podcast audio (crosstalk — harder than solo
dictation, so treat these as rankings, not absolutes):

| Config | Device | WER vs captions | Min | Median |
|---|---|---|---|---|
| `base.en` beam1 | CPU int8 | 21.8% | 2603ms | 2804ms |
| `base.en` beam1 | CUDA float16 | 23.9% | 485ms | 494ms |
| `small.en` beam1 | CPU int8 | 20.4% | 3500ms | 3508ms |
| `small.en` beam1 | CUDA float16 | **20.0%** | **382ms** | **383ms** |
| `distil-large` beam1 | CPU int8 | 19.0% | — | 15490ms |

GPU configs run with `taskset -c 8-15 python bench/bench.py run --configs "base.en:1:cuda:float16,small.en:1:cuda:float16"`

**`beam_size` is not worth paying for.** Beam 3 and 5 measured no better than beam 1 at
either model size (and slightly worse, within noise) while costing up to 1.6x the time.
Whisper's encoder processes a fixed 30-second window regardless of clip length, so
latency is dominated by that floor, not by decode width — 12s of pure *silence* still
costs ~1.4s. This is also why speeding audio up with `ffmpeg atempo` fails: 1.5x tempo
bought 7% latency for 62% WER. Fewer samples, same padded window, mangled words.

## Architecture & Replicability
This repo is entirely self-contained. The AI models are saved directly into the `models/` directory, so you can back up this entire folder to an external drive and run it air-gapped on any Linux machine.

## Architecture

```text
========================================================================
                      JARVIS MONOLITH ARCHITECTURE                      
========================================================================

[ Physical Keyboard(s) ]
       | (Hardware Events: Compose/Menu)
       v
+----------------------------------------------------------------------+
|                         jarvis.py (Python)                           |
|                                                                      |
|  1. [evdev Listener]  <-- Detects Compose/Menu across connected boards|
|           |                                                          |
|           v (Trigger)                                                |
|  2. [sounddevice]     <-- Records Mic directly to RAM (NumPy array)  |
|           |                                                          |
|           v (Float32 Array)                                          |
|  3. [STT Engine]      <-- Moonshine or faster-whisper in RAM          |
|           |               (CPU-only, local inference)                 |
|           v (Text string)                                            |
|  4. [ydotool]         <-- Spawns subprocess to type text directly    |
+----------------------------------------------------------------------+
       | (CLI Command: ydotool type -d 1 -H 1 "text")
       v
[ Virtual Keyboard (ydotoold) ]
       |
       v
[ Active Wayland/X11 Window ]
```
