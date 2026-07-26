"""Latency + accuracy benchmark for STT configs.

    python bench/bench.py corpus add "<youtube-url>" --at 20:00 --for 3:00
    python bench/bench.py run --configs base.en:1,small.en:1,small.en:5
    python bench/bench.py run --repeat 5          # noise-aware timing

Two lessons are baked in, both learned by getting them wrong:

1. Pin the CPU. Unpinned on a busy box, identical work measured 2620-6839ms --
   a 5x spread that swamped the ~5% effect being measured. Always `taskset`, and
   trust `min` over `mean`: min is the closest thing to uncontended truth.

2. The reference must be a DIFFERENT ASR family. Scoring small Whisper against
   large Whisper hides their shared failure modes and flatters both. YouTube's
   captions are independent, so disagreement is informative. They are still not
   ground truth -- absolute WER overstates error. Rank configs; don't quote WER
   as truth. Only a human transcript earns that.
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wavfile

CORPUS = Path(__file__).parent / "corpus"
MODELS = Path(__file__).parent.parent / "models"
ALIASES = {
    "base.en": "Systran/faster-whisper-base.en",
    "small.en": "Systran/faster-whisper-small.en",
    "medium.en": "Systran/faster-whisper-medium.en",
    "distil-large": "distil-whisper/distil-large-v3.5-ct2",
}


def hhmmss(s: str) -> int:
    parts = [int(p) for p in s.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)

    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def norm(t: str) -> str:
    """Strip what we don't want WER to punish: casing, punctuation, fillers,
    caption artifacts (>> speaker turns, [Music])."""
    t = t.lower().replace(">>", " ")
    t = re.sub(r"\[.*?\]", " ", t)
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    t = re.sub(r"\b(uh|um|mm|hmm|ah|er|yeah|like)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def wer(ref: str, hyp: str) -> float:
    r, h = norm(ref).split(), norm(hyp).split()
    if not r:
        return float("nan")
    prev = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        cur = [i] + [0] * len(h)
        for j in range(1, len(h) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
        prev = cur
    return prev[len(h)] / len(r)


def corpus_add(url: str, at: str, dur: str, name: str | None = None) -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    start, length = hhmmss(at), hhmmss(dur)
    end = start + length
    meta = json.loads(subprocess.run(
        ["yt-dlp", "--no-update", "-J", url], capture_output=True, text=True, check=True).stdout)
    vid = meta["id"]
    slug = name or f"{vid}_{start}"
    if meta.get("subtitles"):
        print(f"[!] {slug}: HUMAN subtitles exist -- prefer those over auto-captions")

    def ts(sec):
        return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"

    subprocess.run([
        "yt-dlp", "--no-update", "-f", "bestaudio",
        "--download-sections", f"*{ts(start)}-{ts(end)}",
        "-x", "--audio-format", "wav",
        "--postprocessor-args", "-ar 16000 -ac 1",
        "-o", str(CORPUS / f"{slug}.%(ext)s"), url,
    ], check=True)

    subprocess.run([
        "yt-dlp", "--no-update", "--write-auto-subs", "--sub-langs", "en",
        "--sub-format", "json3", "--skip-download",
        "-o", str(CORPUS / f"{slug}_subs"), url,
    ], check=True)

    sub_file = CORPUS / f"{slug}_subs.en.json3"
    events = json.loads(sub_file.read_text())["events"]
    words = [
        seg["utf8"].strip()
        for e in events
        if start * 1000 <= e.get("tStartMs", 0) < end * 1000
        for seg in e.get("segs", [])
        if seg.get("utf8", "").strip() not in ("", "\n")
    ]
    ref = " ".join(words)
    (CORPUS / f"{slug}.ref.txt").write_text(ref)
    sub_file.unlink()
    (CORPUS / f"{slug}.meta.json").write_text(json.dumps({
        "url": url, "video_id": vid, "title": meta.get("title"),
        "start_s": start, "duration_s": length,
        "reference": "youtube-auto-captions",
        "reference_is_ground_truth": False,
    }, indent=2))
    print(f"[+] {slug}: {length}s audio, {len(ref.split())} reference words")


def load_clips():
    out = []
    for wav in sorted(CORPUS.glob("*.wav")):
        ref = wav.with_suffix("").with_suffix(".ref.txt")
        if not ref.exists():
            ref = CORPUS / f"{wav.stem}.ref.txt"
        if ref.exists():
            out.append((wav.stem, wav, ref.read_text()))
    return out


def run(configs, repeat, window_s):
    from faster_whisper import WhisperModel

    clips = load_clips()
    if not clips:
        sys.exit(f"No clips in {CORPUS}. Add one:\n"
                 f"  python bench/bench.py corpus add <url> --at 20:00 --for 3:00")

    print(f"corpus: {len(clips)} clip(s), window={window_s}s, repeat={repeat}")
    print("WER is vs YouTube auto-captions -- ranking signal, NOT ground truth.")
    print("Timing: trust min (least contended). Run under taskset.\n")
    print(f"{'config':22s} {'WER':>7s} {'min':>8s} {'median':>8s} {'spread':>7s}")

    cache, rows = {}, []
    for spec in configs:
        alias, _, beam = spec.partition(":")
        beam = int(beam or 1)
        name = ALIASES.get(alias, alias)
        if name not in cache:
            cache[name] = WhisperModel(name, device="cpu", compute_type="int8",
                                       cpu_threads=8, download_root=str(MODELS))
        model = cache[name]

        times, wers = [], []
        for _, wav_path, ref in clips:
            sr, data = wavfile.read(wav_path)
            audio = data.astype(np.float32) / 32768.0
            chunks = [audio[i:i + window_s * sr] for i in range(0, len(audio), window_s * sr)]
            chunks = [c for c in chunks if len(c) >= sr * 4]
            model.transcribe(chunks[0], beam_size=beam)  # warm

            best_text = ""
            for _ in range(repeat):
                parts, t0 = [], time.monotonic()
                for c in chunks:
                    segs, _ = model.transcribe(c, beam_size=beam)
                    parts.append(" ".join(s.text.strip() for s in segs))
                # per-chunk latency, which is what a dictation press actually costs
                times.append((time.monotonic() - t0) * 1000 / len(chunks))
                best_text = " ".join(parts)
            wers.append(wer(ref, best_text))

        row = (spec, statistics.mean(wers), min(times),
               statistics.median(times), max(times) - min(times))
        rows.append(row)
        print(f"{row[0]:22s} {row[1]:6.1%} {row[2]:7.0f}ms {row[3]:7.0f}ms {row[4]:6.0f}ms")

    if rows:
        best = min(rows, key=lambda r: r[1])
        fast = min(rows, key=lambda r: r[2])
        print(f"\nmost accurate: {best[0]} ({best[1]:.1%})")
        print(f"fastest:       {fast[0]} ({fast[2]:.0f}ms)")
        if max(r[2] for r in rows) - min(r[2] for r in rows) < max(r[4] for r in rows):
            print("[!] latency spread between configs < noise within a config: "
                  "differences are not real. Pin CPU or raise --repeat.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("corpus").add_subparsers(dest="sub", required=True)
    add = c.add_parser("add")
    add.add_argument("url")
    add.add_argument("--at", default="0:00", help="start, mm:ss or hh:mm:ss")
    add.add_argument("--for", dest="dur", default="3:00", help="duration")
    add.add_argument("--name")
    c.add_parser("list")

    r = sub.add_parser("run")
    r.add_argument("--configs", default="base.en:1,base.en:5,small.en:1,small.en:5")
    r.add_argument("--repeat", type=int, default=3)
    r.add_argument("--window", type=int, default=25, help="chunk seconds")

    a = ap.parse_args()
    if a.cmd == "corpus" and a.sub == "add":
        corpus_add(a.url, a.at, a.dur, a.name)
    elif a.cmd == "corpus":
        for slug, wav, ref in load_clips():
            sr, d = wavfile.read(wav)
            print(f"{slug:28s} {len(d)/sr:6.0f}s  {len(ref.split()):5d} ref words")
    else:
        run([c.strip() for c in a.configs.split(",")], a.repeat, a.window)


if __name__ == "__main__":
    main()
