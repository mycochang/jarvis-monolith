# GPU acceleration: test plan

Status: **not merged, not enabled.** Default stays CPU. See PR #4.

GPU is worth pursuing — measured 7–9x faster (`small.en` float16: ~380ms vs ~3500ms
CPU per 25s chunk, ~367 MiB VRAM). The blocker is not performance, it's display risk.

## The risk

On a hybrid NVIDIA + AMD laptop, earlier GPU attempts killed the display. Before
enabling CUDA anywhere, establish which device the compositor actually uses.

PR #4's body claims the compositor holds no handle to the NVIDIA render node. **That
claim is wrong** and must be corrected before merge. Verify yourself:

```bash
# map render nodes to drivers
for n in 128 129; do
  echo "renderD$n -> $(basename $(readlink -f /sys/class/drm/renderD$n/device/driver))"
done

# what the compositor has open -- REQUIRES ROOT
sudo ls -l /proc/$(pgrep -x kwin_wayland)/fd | grep -o '/dev/dri/[a-z0-9]*' | sort -u

# who is on the NVIDIA card
nvidia-smi
```

The trap: reading `/proc/<pid>/fd` **without root returns empty**, which reads as "no
handle" but means "permission denied." That misread is how PR #4 reached a false
conclusion. Always use `sudo` here.

Current finding on the dev laptop: the compositor *does* hold the NVIDIA render node,
but as a ~2 MiB graphics client — Optimus offload plumbing, not desktop compositing.
Two monitors cannot run on 2 MiB. So the card is not driving the display, but a fault
on it is not fully decoupled from the compositor either. Treat as low-probability,
high-cost.

Reassuring datapoint: CUDA inference has already run on this hardware with no NVIDIA
Xid faults and no compositor crashes. Confirm before testing:

```bash
sudo dmesg | grep -iE 'xid|nvrm'      # expect nothing
nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader
```

## Fix required before merge

`_ensure_cuda_libs_on_path()` in the faster-whisper adapter calls `os.execve` to
re-exec the process with a patched `LD_LIBRARY_PATH`. A daemon replacing itself
mid-load is a bad failure mode regardless of GPU. Set the path in the systemd unit
instead:

```ini
[Service]
Environment="LD_LIBRARY_PATH=<venv>/lib/python3.13/site-packages/nvidia/cublas/lib:<venv>/lib/python3.13/site-packages/nvidia/cudnn/lib"
```

Then delete the re-exec helper and its call sites.

## Test procedure

Four guardrails, in order. Do not skip ahead.

**1. Drive it over SSH, not the desktop session.** If the compositor dies, the shell
survives and the logs are still readable. Confirm `sshd` is active and you can reach
the box from another device *before* starting.

**2. Keep a TTY escape open.** `Ctrl+Alt+F3` to a free VT. Verify tty2–tty6 exist.

**3. Subprocess first, service never.** `bench/test_cuda_subprocess.py` exists for
this — a crash takes the child, not your dictation daemon. Do not set
`JARVIS_DEVICE=cuda` on the live unit until the subprocess path is clean.

**4. Arm a watchdog before the first CUDA call.** So an unattended crash self-heals:

```bash
systemd-run --user --on-active=120 --unit=jarvis-gpu-revert \
  bash -c 'rm -f ~/.config/systemd/user/jarvis.service.d/gpu.conf &&
           systemctl --user daemon-reload && systemctl --user restart jarvis'
```

Cancel it once the test passes: `systemctl --user stop jarvis-gpu-revert.timer`

## VRAM discipline

- `small.en` float16 only. ~367 MiB of 8192 — generous headroom.
- **Never** load `distil-large` on GPU.
- Watch during inference: `nvidia-smi --query-gpu=memory.used --format=csv -l 1`

## Revert

GPU is opt-in via `JARVIS_DEVICE`, so reverting is removing the drop-in:

```bash
rm ~/.config/systemd/user/jarvis.service.d/gpu.conf
systemctl --user daemon-reload && systemctl --user restart jarvis
```

Nothing in the CPU path changes, so this is always available.

## Deferred

VRAM-pressure eviction, analogous to the existing `MemAvailable` watcher: if another
CUDA workload needs the card, drop the weights. Not built — the idle timeout covers the
common case. Revisit if GPU becomes the default.
