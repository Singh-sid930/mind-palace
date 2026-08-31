"""Music bed for the promo film, rendered from the palace's own formulas.

The engine synthesizes its score in WebAudio, which a headless recording
cannot capture, so the identical voices are re-rendered offline here and
muxed onto the video. Nothing is sampled: it is the same mathematics.

Run with:  ~/anaconda3/envs/lrm/bin/python tools/promo_audio.py [seconds]
"""
import sys
from pathlib import Path

import numpy as np

import music_lab as M

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "media" / "raw" / "promo_music.wav"


def build(dur, dementor_at, patronus_at):
    left, right, _ = M.binaural_over_pink(dur=dur, hold=18.0, glide=8.0)
    left, right = left.copy(), right.copy()

    # The two event stings, placed on the beats where they happen on screen.
    dem = M.distant(M.dementor(6.5), cut=900, decay=2.6, wet=0.6) * 0.7
    pat = M.distant(M.patronus(5.0), cut=1700, decay=2.2, wet=0.55) * 0.5
    for track in (left, right):
        M.place(track, dem, dementor_at)
        M.place(track, pat, patronus_at)

    # Lift the last few seconds so the end card does not feel like a dropout.
    t = M.t_axis(min(len(left), len(right)) / M.SR)
    swell = 1.0 + 0.25 * np.clip((t - (dur - 8)) / 6.0, 0, 1)
    n = min(len(left), len(right), len(swell))
    return left[:n] * swell[:n], right[:n] * swell[:n]


if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 48.0
    dem_at = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    pat_at = float(sys.argv[3]) if len(sys.argv) > 3 else 34.0
    l, r = build(dur, dem_at, pat_at)
    import wave
    peak = max(np.abs(l).max(), np.abs(r).max())
    l, r = l / peak * 0.82, r / peak * 0.82
    inter = np.empty(len(l) * 2, dtype=np.int16)
    inter[0::2] = (l * 32767).astype(np.int16)
    inter[1::2] = (r * 32767).astype(np.int16)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(M.SR)
        w.writeframes(inter.tobytes())
    print(OUT, f"{len(l)/M.SR:.1f}s")
