"""Cut the recording, mix narration, burn captions (white text, black outline).

    python compose.py admin|owner [--lang ar] [--dest ../../frontend/public/videos]

Reads out/<video>/{raw.webm,marks.json,durations.json,audio/*.mp3}; writes
tutorial-<video>-<lang>.mp4 / .vtt / .jpg. Needs rsvg-convert (brew install librsvg)
to render the captions with proper Arabic shaping.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

from scenes_ar import VIDEOS

OUT = Path(__file__).parent / "out"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
LEAD = 0.35
W, H = 1280, 720
CAP_W, CAP_H = 1180, 140
LINE_CHARS, MAX_LINES = 40, 2


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-2500:])


# ── timeline ───────────────────────────────────────────────────────────────
def segments(t0, t1, fast):
    """Split [t0, t1] into (a, b, speed) pieces."""
    pts, out, cur = sorted(fast), [], t0
    for a, b, s in pts:
        a, b = max(a, t0), min(b, t1)
        if b <= cur:
            continue
        if a > cur:
            out.append((cur, a, 1.0))
        out.append((max(a, cur), b, s))
        cur = b
    if cur < t1:
        out.append((cur, t1, 1.0))
    return out


def mapper(segs):
    def m(t):
        acc = 0.0
        for a, b, s in segs:
            if t <= a:
                return acc
            if t < b:
                return acc + (t - a) / s
            acc += (b - a) / s
        return acc
    return m


# ── captions ───────────────────────────────────────────────────────────────
def chunks(text):
    """Split narration into caption pieces of <= MAX_LINES lines."""
    text = text.replace("عِمارة.كوم", "عِمارة§كوم")  # keep the brand name's dot from ending a sentence
    sentences = [s.strip() for s in re.findall(r"[^.!؟?]+[.!؟?]?", text) if s.strip()]
    pieces = []
    for s in sentences:
        words, cur = s.split(), ""
        for w in words:
            if len((cur + " " + w).strip()) > LINE_CHARS * MAX_LINES:
                pieces.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            pieces.append(cur)
    # merge tiny pieces into the previous one
    merged = []
    for p in pieces:
        if merged and len(p) < 14 and len(merged[-1] + " " + p) <= LINE_CHARS * MAX_LINES:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return [p.replace("§", ".") for p in merged]


def wrap(text):
    lines, cur = [], ""
    for w in text.split():
        if len((cur + " " + w).strip()) > LINE_CHARS and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    # balance two lines
    if len(lines) == 2 and len(lines[0]) > len(lines[1]) + 12:
        ws = (lines[0] + " " + lines[1]).split()
        best = min(range(1, len(ws)), key=lambda i: abs(len(" ".join(ws[:i])) - len(" ".join(ws[i:]))))
        lines = [" ".join(ws[:best]), " ".join(ws[best:])]
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def render_caption(lines, path):
    n = len(lines)
    ys = [CAP_H / 2 + 14] if n == 1 else [CAP_H / 2 - 20, CAP_H / 2 + 32]
    texts = ""
    for pass_, attrs in (("stroke", 'fill="#000" stroke="#000" stroke-width="8" stroke-linejoin="round"'), ("fill", 'fill="#fff"')):
        for y, line in zip(ys, lines):
            texts += (
                f'<text x="{CAP_W/2}" y="{y}" text-anchor="middle" direction="rtl" font-family="Cairo, Tajawal, sans-serif" '
                f'font-weight="800" font-size="40" {attrs}>{esc(line)}</text>'
            )
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{CAP_W}" height="{CAP_H}" viewBox="0 0 {CAP_W} {CAP_H}">{texts}</svg>'
    tmp = path.with_suffix(".svg")
    tmp.write_text(svg)
    run(["rsvg-convert", "-o", str(path), str(tmp)])
    tmp.unlink()


def vtt_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


# ── main ───────────────────────────────────────────────────────────────────
def main(video, lang="ar", dest=None):
    out = OUT / video
    marks = json.loads((out / "marks.json").read_text())
    scenes, fast = marks["scenes"], marks["fast"]
    durs = json.loads((out / "durations.json").read_text())
    texts = dict(VIDEOS[video])
    order = [sid for sid, _ in VIDEOS[video] if sid in scenes]

    t0 = scenes[order[0]]["start"]
    t1 = scenes[order[-1]]["end"]
    segs = segments(t0, t1, fast)
    m = mapper(segs)
    total = m(t1)

    caps_dir = out / "caps"
    shutil.rmtree(caps_dir, ignore_errors=True)
    caps_dir.mkdir(parents=True)
    cues, audio = [], []
    for sid in order:
        pos = m(scenes[sid]["start"]) + LEAD
        audio.append((out / "audio" / f"{sid}.mp3", pos))
        parts = chunks(texts[sid])
        weights = [max(len(p), 1) for p in parts]
        span, acc = durs[sid], 0.0
        for p, wgt in zip(parts, weights):
            a = pos + span * acc / sum(weights)
            acc += wgt
            b = pos + span * acc / sum(weights)
            cues.append((a, b, wrap(p)))

    for i, (a, b, lines) in enumerate(cues):
        render_caption(lines, caps_dir / f"c{i:03d}.png")

    # inputs: 0 = video, then audio, then captions
    cmd = [FFMPEG, "-y", "-i", str(out / "raw.webm")]
    for f, _ in audio:
        cmd += ["-i", str(f)]
    for i in range(len(cues)):
        cmd += ["-i", str(caps_dir / f"c{i:03d}.png")]

    fc = []
    for k, (a, b, s) in enumerate(segs):
        fc.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=(PTS-STARTPTS)/{s},fps=25,scale={W}:{H}[s{k}]")
    fc.append("".join(f"[s{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[base]")
    prev = "base"
    n_audio = len(audio)
    for i, (a, b, _) in enumerate(cues):
        idx = 1 + n_audio + i
        fc.append(
            f"[{prev}][{idx}:v]overlay=x=(W-w)/2:y=H-h-22:enable='between(t,{a:.3f},{b:.3f})'[o{i}]"
        )
        prev = f"o{i}"
    for k, (_, pos) in enumerate(audio):
        ms = int(pos * 1000)
        fc.append(f"[{1 + k}:a]adelay={ms}|{ms}[a{k}]")
    fc.append("".join(f"[a{k}]" for k in range(n_audio)) + f"amix=inputs={n_audio}:normalize=0:duration=longest[aout]")

    name = f"tutorial-{video}-{lang}"
    mp4 = out / f"{name}.mp4"
    cmd += [
        "-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-map", "[aout]",
        "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "24", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(mp4),
    ]
    run(cmd)

    vtt = ["WEBVTT", ""]
    for i, (a, b, lines) in enumerate(cues, 1):
        vtt += [str(i), f"{vtt_time(a)} --> {vtt_time(b)}", "\n".join(lines), ""]
    (out / f"{name}.vtt").write_text("\n".join(vtt), encoding="utf-8")
    # poster from the raw recording so it carries no caption
    run([FFMPEG, "-y", "-ss", f"{t0 + 1.0:.2f}", "-i", str(out / "raw.webm"), "-frames:v", "1",
         "-vf", f"scale={W}:{H}", "-q:v", "4", str(out / f"{name}.jpg")])

    if dest:
        dest = Path(dest)
        dest.mkdir(parents=True, exist_ok=True)
        for ext in ("mp4", "vtt", "jpg"):
            shutil.copy(out / f"{name}.{ext}", dest / f"{name}.{ext}")
    print(f"{name}: {total:.1f}s, {len(cues)} captions, {mp4.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    args = sys.argv[1:]
    dest = args[args.index("--dest") + 1] if "--dest" in args else None
    lang = args[args.index("--lang") + 1] if "--lang" in args else "ar"
    main(args[0], lang, dest)
