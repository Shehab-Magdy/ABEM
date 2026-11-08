"""Generate one MP3 per scene with edge-tts and record durations.

    python tts.py admin|owner [--rate +8%]
"""
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

import edge_tts
import imageio_ffmpeg

from scenes_ar import SAY_REPLACEMENTS, VIDEOS

VOICE = "ar-EG-ShakirNeural"
OUT = Path(__file__).parent / "out"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def spoken(text: str) -> str:
    for a, b in SAY_REPLACEMENTS:
        text = text.replace(a, b)
    return text


def duration(path: Path) -> float:
    err = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


async def main(video: str, rate: str):
    d = OUT / video / "audio"
    d.mkdir(parents=True, exist_ok=True)
    durs = {}
    for sid, text in VIDEOS[video]:
        f = d / f"{sid}.mp3"
        await edge_tts.Communicate(spoken(text), VOICE, rate=rate).save(str(f))
        durs[sid] = round(duration(f), 3)
        print(sid, durs[sid])
    (OUT / video / "durations.json").write_text(json.dumps(durs, indent=2))


if __name__ == "__main__":
    rate = sys.argv[sys.argv.index("--rate") + 1] if "--rate" in sys.argv else "+8%"
    asyncio.run(main(sys.argv[1], rate))
