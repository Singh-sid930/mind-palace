"""Mathematical music lab — audition clips for the palace's procedural score.

Every sound is synthesized from an explicit formula (no samples, no assets),
exactly as the WebAudio engine version would compute it. Run with:

    ~/anaconda3/envs/lrm/bin/python tools/music_lab.py

Writes WAV clips + graph sheets to docs/media/raw/music/ (gitignored).
"""
import numpy as np
from pathlib import Path
import wave

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from palace_fig import BG, PANEL, INK, MUTED, GRID, HOT, WING

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "docs" / "media" / "raw" / "music"
PHI = (1 + 5 ** 0.5) / 2

def t_axis(dur):
    return np.arange(int(dur * SR)) / SR

def fade(x, ms=60):
    n = int(SR * ms / 1000)
    env = np.ones_like(x)
    env[:n] = np.linspace(0, 1, n)
    env[-n:] = np.linspace(1, 0, n)
    return x * env

def save(name, x, peak=0.7):
    x = fade(x / (np.abs(x).max() + 1e-9) * peak)
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    return OUT / name

def save_stereo(name, left, right, peak=0.7):
    n = min(len(left), len(right))
    left, right = fade(left[:n]), fade(right[:n])
    m = max(np.abs(left).max(), np.abs(right).max()) + 1e-9
    inter = np.empty(n * 2)
    inter[0::2] = left / m * peak
    inter[1::2] = right / m * peak
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((inter * 32767).astype(np.int16).tobytes())
    return OUT / name

# --- Binaural layer: two tones, one per ear; the DIFFERENCE is the "beat" -----
# EEG-band targets: calm = theta ~6 Hz, relaxed focus = alpha ~10 Hz,
# alertness = beta ~16 Hz. States rotate in an ascending-arousal ramp, gliding
# smoothly between holds (real cadence: ~10 min/state; here time-compressed).
STATES = [("calm", 6.0), ("relaxed focus", 10.0), ("alertness", 16.0)]

def beat_schedule(dur, hold, glide):
    """A smooth beat-rate curve cycling calm->focus->alert->(wrap), in Hz."""
    t = t_axis(dur)
    seq = [s[1] for s in STATES]
    period = hold + glide
    out = np.empty_like(t)
    for i, ti in enumerate(t):
        cyc = ti % (period * len(seq))
        k = int(cyc // period)               # which state
        into = cyc - k * period
        a = seq[k]
        b = seq[(k + 1) % len(seq)]
        if into < hold:
            out[i] = a
        else:
            u = (into - hold) / glide        # glide a->b
            out[i] = a + (b - a) * (0.5 - 0.5 * np.cos(np.pi * u))
    return out

def binaural_over_pink(dur=54, carrier=120.0, hold=12.0, glide=6.0):
    t = t_axis(dur)
    beat = beat_schedule(dur, hold, glide)
    # Left ear = carrier; right ear = carrier + beat(t). Phase via cumulative sum.
    # The binaural tones and the broadband bed sit LOW — they work on phase and
    # masking, not loudness — so the theatrical bells can ride prominently on top.
    phase_l = 2 * np.pi * carrier * t
    phase_r = 2 * np.pi * np.cumsum(carrier + beat) / SR
    tone_l = 0.17 * np.sin(phase_l)           # subliminal binaural (was 0.32)
    tone_r = 0.17 * np.sin(phase_r)
    bed = 0.5 * pink(dur)                      # quiet broadband base (was 0.9)
    drn = 0.34 * drone(dur)                    # quiet low body (was 0.5)
    blz = 0.56 * distant_bells(dur)            # distant bells, theatrical
    n = min(len(bed), len(drn), len(blz), len(t))
    base = bed[:n] + drn[:n] + blz[:n]         # shared (mono) content, both ears
    return base + tone_l[:n], base + tone_r[:n], beat[:n]

# --- 1. Drone: harmonic series, breathing incommensurately ------------------
def drone(dur=24, f0=55.0):
    t = t_axis(dur)
    rates = [0.050, 0.050 / PHI, 0.050 / np.sqrt(2), 0.050 / np.pi, 0.033, 0.041]
    x = np.zeros_like(t)
    for n in range(1, 7):
        am = 0.62 + 0.38 * np.sin(2 * np.pi * rates[n - 1] * t + n)
        x += (1.0 / n) * am * np.sin(2 * np.pi * n * f0 * t + 0.7 * n)
    return x

# --- 2. Bells: FM with golden inharmonicity, struck on {k·phi mod 1} --------
PENTA = np.array([220.0, 261.63, 293.66, 329.63, 392.0, 440.0])  # A minor penta
def fm_bell(f_c, dur=3.5, I0=2.2):
    t = t_axis(dur)
    I = I0 * np.exp(-t / 0.55)
    amp = np.exp(-t / 1.1)
    return amp * np.sin(2 * np.pi * f_c * t + I * np.sin(2 * np.pi * f_c * PHI * t))

def bells(dur=24, density=9):
    x = np.zeros(int(dur * SR))
    for k in range(density):
        when = ((k * PHI) % 1.0) * (dur - 4)          # equidistributed strike times
        note = PENTA[int((k * PHI * PHI * len(PENTA)) % len(PENTA))]
        b = fm_bell(note) * (0.5 + 0.5 * ((k * 7) % 3) / 2)
        i = int(when * SR)
        x[i:i + len(b)] += b[: len(x) - i]
    return x

# --- distance colouring: air-absorption low-pass + a reverb tail ------------
def fftconv(x, h):
    n = len(x) + len(h) - 1
    N = 1 << int(np.ceil(np.log2(n)))
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(h, N), N)[:n]

def lowpass(x, fc, order=2):
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1.0 / np.sqrt(1 + (f / fc) ** (2 * order))   # Butterworth magnitude
    return np.fft.irfft(np.fft.rfft(x) * H, len(x))

def highpass(x, fc, order=2):
    f = np.fft.rfftfreq(len(x), 1 / SR); f[0] = 1e-6
    H = 1.0 / np.sqrt(1 + (fc / f) ** (2 * order))
    return np.fft.irfft(np.fft.rfft(x) * H, len(x))

def bandpass(x, lo, hi):
    return highpass(lowpass(x, hi), lo)

def place(dst, src, at):
    """Add src into dst starting at time `at` seconds (clipped to bounds)."""
    i = int(at * SR)
    dst[i:i + len(src)] += src[: len(dst) - i]

def reverb(x, decay=2.0, wet=0.45, predelay=0.03):
    ir_len = int(decay * 3 * SR)
    tt = np.arange(ir_len) / SR
    ir = np.random.default_rng(11).standard_normal(ir_len) * np.exp(-tt / decay)
    ir[: int(predelay * SR)] = 0                      # small gap = room size
    wetsig = fftconv(x, ir)[: len(x)]
    wetsig *= np.abs(x).max() / (np.abs(wetsig).max() + 1e-9)
    return (1 - wet) * x + wet * wetsig

def distant(x, cut=1500, decay=1.9, wet=0.5):
    """The shared 'heard across the castle' colouring: air-absorption low-pass
    plus a wet reverb tail. Every event sting is passed through this so the
    creatures sound like they inhabit the same stone halls as the bells."""
    return reverb(lowpass(x, cut), decay=decay, wet=wet)

def distant_bells(dur=24, density=9):
    """Bells heard from across the castle: dulled by air, trailing in reverb."""
    b = lowpass(bells(dur, density), 1200)           # lower cutoff = duller, further
    b = reverb(b, decay=2.3, wet=0.58)               # longer, wetter tail = faded
    return b[: len(t_axis(dur))]

# --- 3. Air: 1/f pink noise with a slow wandering bandpass ------------------
def pink(dur=20):
    n = int(dur * SR)
    spec = np.fft.rfft(np.random.default_rng(7).standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR); f[0] = 1
    x = np.fft.irfft(spec / np.sqrt(f), n)
    t = t_axis(dur)
    sweep = 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t)   # slow LFO on brightness
    return x * sweep

# --- 4. Shepard–Risset glissando: the endless staircase ---------------------
def shepard(dur=14, octaves=7, f_base=32.7, rate=1 / 10, descend=False):
    t = t_axis(dur)
    x = np.zeros_like(t)
    r = -rate if descend else rate
    for i in range(octaves):
        pos = (i + r * t) % octaves                        # octave position, wraps
        f = f_base * 2 ** pos
        w = np.exp(-0.5 * ((pos - octaves / 2) / 1.35) ** 2)  # log-f Gaussian window
        phase = 2 * np.pi * np.cumsum(f) / SR
        x += w * np.sin(phase)
    return x

# --- 5. Sting: dementor — descending cluster + subharmonic + cold noise -----
def dementor(dur=7):
    t = t_axis(dur)
    swell = np.exp(-0.5 * ((t - 2.6) / 1.5) ** 2)
    x = np.zeros_like(t)
    for df in [1.0, 1.06, 0.94]:                      # a minor-second cluster
        f = 190.0 * df * 2 ** (-t / 8)                # slow downward glissando
        x += 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    f_sub = 95.0 * 2 ** (-t / 8)
    x += 0.7 * np.sin(2 * np.pi * np.cumsum(f_sub) / SR)
    n = int(dur * SR)
    spec = np.fft.rfft(np.random.default_rng(3).standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR); fr[0] = 1
    x += 0.8 * np.fft.irfft(spec / fr, n) * swell     # brown-ish cold wind
    return x * (0.35 + 0.65 * swell)

# --- 6. Sting: patronus — just-intonation arpeggio, shimmering ---------------
def patronus(dur=5):
    ratios = [1, 5 / 4, 3 / 2, 2, 5 / 2, 3]           # 4:5:6 stacked (just major)
    x = np.zeros(int(dur * SR))
    for k, r in enumerate(ratios):
        t = t_axis(dur - k * 0.22)
        f = 523.25 * r
        pair = (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * 1.003 * t)) / 2
        note = pair * np.exp(-t / 1.6) * (1 - np.exp(-t / 0.01))
        i = int(k * 0.22 * SR)
        x[i:i + len(note)] += 0.6 * note
    return x

# --- headphone check: does your rig deliver true L/R separation? ------------
def headphone_check():
    """Three segments. 1) tone LEFT only, 2) tone RIGHT only — confirms each ear
    is fed independently. 3) the binaural pair (200 L / 210 R): on real stereo
    headphones each ear hears a STEADY tone and the beat is subtle/central; on a
    mono-summed output you'll instead hear an obvious out-loud throbbing (a
    physical 10 Hz tremolo) — which means binaural entrainment won't work."""
    seg, gap = 3.0, 0.6
    L = np.concatenate([
        0.5 * np.sin(2 * np.pi * 440 * t_axis(seg)), np.zeros(int(gap * SR)),
        np.zeros(int(seg * SR)),                       np.zeros(int(gap * SR)),
        0.42 * np.sin(2 * np.pi * 200 * t_axis(6.0)),
    ])
    R = np.concatenate([
        np.zeros(int(seg * SR)),                       np.zeros(int(gap * SR)),
        0.5 * np.sin(2 * np.pi * 440 * t_axis(seg)),   np.zeros(int(gap * SR)),
        0.42 * np.sin(2 * np.pi * 210 * t_axis(6.0)),
    ])
    return L, R

# --- Event stings: one formula per actor, all sent through distant() ---------
def st_rat(dur=1.3):
    """Tiny high skittering — rapid decaying noise grains, high-passed."""
    x = np.zeros(int(dur * SR)); rng = np.random.default_rng(21)
    for k in range(13):
        gt = t_axis(0.045)
        grain = rng.standard_normal(len(gt)) * np.exp(-gt / 0.012)
        place(x, grain, rng.uniform(0, dur - 0.1))
    return distant(highpass(x, 2600) * 0.7, cut=4000, decay=1.2, wet=0.35)

def st_ghost(dur=4.5):
    """A dark ethereal whoosh — low band-passed noise + a low shimmer, slow swell."""
    t = t_axis(dur); swell = np.exp(-0.5 * ((t - 2.25) / 1.5) ** 2)   # wider = slower
    air = bandpass(np.random.default_rng(5).standard_normal(len(t)), 300, 1600)  # darker
    fsh = 460 + 30 * np.sin(2 * np.pi * 0.35 * t)                     # lower, slower bend
    shimmer = 0.18 * np.sin(2 * np.pi * np.cumsum(fsh) / SR)
    return distant((air + shimmer) * swell, cut=1400, decay=2.6, wet=0.6)

def st_cat(dur=1.8):
    """Mrs Norris — a low wary purr: 25 Hz amplitude modulation on a low tone."""
    t = t_axis(dur); am = 0.5 + 0.5 * np.sin(2 * np.pi * 25 * t)
    env = np.exp(-0.5 * ((t - 0.9) / 0.6) ** 2)
    x = (np.sin(2 * np.pi * 55 * t) + 0.4 * np.sin(2 * np.pi * 110 * t)) * am * env
    return distant(x, cut=1400, decay=1.6, wet=0.4)

def st_owl(dur=2.4):
    """A distant dark 'hoo — hoo': two SHORT low hoots with a clear gap between."""
    x = np.zeros(int(dur * SR))
    for start in (0.25, 1.05):
        ht = t_axis(0.4)                                 # short pulse, not a drone
        f = 300 - 32 * ht / 0.4                          # low + downward glide = dark
        warble = 1 + 0.12 * np.sin(2 * np.pi * 6 * ht)   # a natural hoot wavers
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * warble
        breath = 0.2 * lowpass(np.random.default_rng(int(start * 99)).standard_normal(len(ht)), 800)
        env = np.exp(-ht / 0.14) * (1 - np.exp(-ht / 0.03))
        place(x, (tone + breath) * env, start)
    # Drier reverb: a long wet tail smeared the two hoots into one continuous sound.
    return distant(x, cut=850, decay=1.5, wet=0.32)

def st_snitch(dur=1.6):
    """Golden snitch — a bright metallic flutter darting on a lissajous path."""
    t = t_axis(dur)
    flutter = 0.5 + 0.5 * np.sin(2 * np.pi * 45 * t)        # wingbeat
    fc = 2600 + 600 * np.sin(2 * np.pi * 1.3 * t) + 300 * np.sin(2 * np.pi * 2.1 * t)
    tone = np.sin(2 * np.pi * np.cumsum(fc) / SR)
    env = np.exp(-0.5 * ((t - dur / 2) / (dur / 2.6)) ** 2)
    return distant(tone * flutter * env * 0.5, cut=5000, decay=1.4, wet=0.4)

def st_boggart(dur=2.3):
    """A wooden rattle, a sharp crack, then a low thump as the lid drops."""
    x = np.zeros(int(dur * SR)); rng = np.random.default_rng(31)
    for k in range(8):                                      # rattle
        kt = t_axis(0.05)
        place(x, 0.6 * bandpass(rng.standard_normal(len(kt)), 200, 900) * np.exp(-kt / 0.015),
              rng.uniform(0, 1.1))
    ct = t_axis(0.4)                                        # crack
    place(x, bandpass(np.random.default_rng(7).standard_normal(len(ct)), 300, 3000) * np.exp(-ct / 0.03), 1.3)
    tt = t_axis(0.6)                                        # thump
    place(x, 0.7 * np.sin(2 * np.pi * 70 * tt) * np.exp(-tt / 0.15), 1.35)
    return distant(x, cut=1800, decay=1.8, wet=0.45)

def st_draft(dur=3.0):
    """A low corridor wind — low-passed noise swelling and fading."""
    t = t_axis(dur); swell = np.exp(-0.5 * ((t - 1.5) / 1.0) ** 2)
    wind = lowpass(np.random.default_rng(9).standard_normal(len(t)), 600)
    return distant(wind * swell, cut=900, decay=2.0, wet=0.5)

def st_rumble(dur=4.0):
    """The staircases moving — deep sub tones under grinding stone, swelling."""
    t = t_axis(dur); swell = np.exp(-0.5 * ((t - 2.0) / 1.3) ** 2)
    low = 0.6 * np.sin(2 * np.pi * 32 * t) + 0.4 * np.sin(2 * np.pi * 45 * t)
    grind = lowpass(np.random.default_rng(4).standard_normal(len(t)), 200)
    return distant((low + 0.8 * grind) * swell, cut=1200, decay=2.6, wet=0.55)

def st_noise_veil(dur=3.5):
    """Diffusion made audible — broadband hiss GATHERS into a pure tone, then
    disperses back to noise (the forward/reverse process, as sound)."""
    t = t_axis(dur)
    center = np.exp(-0.5 * ((t - dur / 2) / (dur / 5)) ** 2)   # 1 at the middle
    nz = bandpass(np.random.default_rng(13).standard_normal(len(t)), 300, 4000)
    tone = np.sin(2 * np.pi * 330 * t)
    return distant(nz * (1 - center) * 0.6 + tone * center * 0.5, cut=2600, decay=2.2, wet=0.55)

def st_time_glint(dur=2.6):
    """Time-turner — a bell run BACKWARD (swelling into its strike) + a sparkle."""
    b = fm_bell(523.25, dur=1.5, I0=2.0)[::-1]             # reversed envelope
    x = np.zeros(int(dur * SR)); x[: len(b)] += b
    st = t_axis(1.0)
    place(x, 0.3 * np.sin(2 * np.pi * 1046.5 * st) * np.exp(-st / 0.4), len(b) / SR)
    return distant(x, cut=2200, decay=2.3, wet=0.55)

def st_peeves(dur=2.0):
    """Peeves — pages riffling, then two comedic descending 'book-drop' blips."""
    x = np.zeros(int(dur * SR)); rng = np.random.default_rng(41)
    for k in range(20):                                    # riffle
        rt = t_axis(0.02)
        place(x, 0.4 * highpass(rng.standard_normal(len(rt)), 3000) * np.exp(-rt / 0.006),
              rng.uniform(0, 1.5))
    for start, f0 in ((0.6, 400), (1.2, 300)):             # book drops
        bt = t_axis(0.3); f = f0 * 2 ** (-bt / 0.15)
        place(x, 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-bt / 0.1), start)
    return distant(x, cut=2600, decay=1.6, wet=0.4)

# Re-colour the two existing stings through the same castle reverb.
def st_dementor(dur=7): return distant(dementor(dur), cut=1400, decay=2.6, wet=0.5)
def st_patronus(dur=5): return distant(patronus(dur), cut=1700, decay=2.4, wet=0.55)  # muddier

STINGS = {
    "fx_rat.wav":        (st_rat,        "rat — high decaying noise grains, {irregular} skitter"),
    "fx_ghost.wav":      (st_ghost,      "ghost — band-passed noise swell + bending shimmer"),
    "fx_cat.wav":        (st_cat,        "cat — 25 Hz AM purr on a 55 Hz tone"),
    "fx_owl.wav":        (st_owl,        "owl — two low 320→275 Hz gliding hoots, dark + far"),
    "fx_snitch.wav":     (st_snitch,     "snitch — 45 Hz flutter on a lissajous-darting tone"),
    "fx_boggart.wav":    (st_boggart,    "boggart — wooden rattle · crack · low thump"),
    "fx_draft.wav":      (st_draft,      "draft — low-passed wind, swelling"),
    "fx_rumble.wav":     (st_rumble,     "rumble — 32+45 Hz subs under grinding stone"),
    "fx_noise_veil.wav": (st_noise_veil, "noise-veil — hiss gathers to a tone, then disperses"),
    "fx_time_glint.wav": (st_time_glint, "time-glint — a bell reversed into its strike + sparkle"),
    "fx_peeves.wav":     (st_peeves,     "peeves — page riffle + two descending book-drops"),
    "fx_dementor.wav":   (st_dementor,   "dementor — descending cluster + sub + cold swell"),
    "fx_patronus.wav":   (st_patronus,   "patronus — just-intonation 1:5/4:3/2:2:5/2:3 arpeggio"),
}

# --- render all -------------------------------------------------------------
CLIPS = {
    "drone_harmonics.wav":  (drone,    "drone — Σ (1/n)·sin(2πnf₀t), AM at φ, √2, π rates"),
    "bells_phi.wav":        (bells,    "bells — FM sin(2πf_ct + I·sin(2πφf_ct)), struck at {kφ mod 1}"),
    "air_pink.wav":         (pink,     "air — 1/f pink noise, brightness on a 0.07 Hz LFO"),
    "stairs_shepard.wav":   (shepard,  "stairs — Shepard–Risset: octave partials under a log-f window"),
    "sting_dementor.wav":   (dementor, "dementor — descending cluster ·2^(−t/8) + subharmonic + 1/f² swell"),
    "sting_patronus.wav":   (patronus, "patronus — just intonation 1 : 5/4 : 3/2 : 2 : 5/2 : 3"),
}

def mix_preview():
    # Bells forward for theatrical effect (now distant); drone + air a quiet bed.
    d, b, a = drone(30), distant_bells(30), pink(30)
    n = min(len(d), len(b), len(a))
    return 0.55 * d[:n] + 0.56 * b[:n] + 0.10 * a[:n]

def sheet(rows, fname, title):
    fig, axes = plt.subplots(len(rows), 3, figsize=(14, 3.1 * len(rows)))
    fig.patch.set_facecolor(BG)
    for r, (name, x, label) in enumerate(rows):
        ax0, ax1, ax2 = axes[r] if len(rows) > 1 else axes
        for ax in (ax0, ax1, ax2):
            ax.set_facecolor(PANEL)
            for s in ax.spines.values(): s.set_color(GRID)
            ax.tick_params(colors=MUTED, labelsize=8)
        i0 = len(x) // 3
        zoom = x[i0:i0 + int(0.05 * SR)]
        ax0.plot(np.arange(len(zoom)) / SR * 1000, zoom, color=WING["verdigris"]["accent"], lw=0.7)
        ax0.set_title("waveform (50 ms)", color=MUTED, fontsize=9)
        step = max(1, len(x) // 4000)
        env = np.abs(x[::step])
        ax1.fill_between(np.arange(len(env)) * step / SR, env, -env,
                         color=WING["verdigris"]["warm"], alpha=0.8, lw=0)
        ax1.set_title("envelope (full clip)", color=MUTED, fontsize=9)
        ax2.specgram(x, NFFT=2048, Fs=SR, noverlap=1024, cmap="magma", vmin=-110)
        ax2.set_ylim(0, 4200)
        ax2.set_title("spectrogram", color=MUTED, fontsize=9)
        ax0.set_ylabel(f"{name}\n{label}", color=INK, fontsize=9.5, rotation=0,
                       ha="right", va="center", labelpad=8)
    fig.suptitle(title, color=INK, fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0.02, 0, 1, 0.96])
    p = OUT / fname
    fig.savefig(p, facecolor=BG, dpi=110)
    plt.close(fig)
    return p

if __name__ == "__main__":
    rendered = {}
    for name, (fn, label) in CLIPS.items():
        x = fn()
        save(name, x)
        rendered[name] = (x, label)
        print("wav:", OUT / name)
    mixed = mix_preview()
    save("ambient_mix_preview.wav", mixed)
    print("wav:", OUT / "ambient_mix_preview.wav")

    # Stereo binaural rotation over the pink+drone bed (HEADPHONES ONLY).
    bl, br, beat = binaural_over_pink()
    save_stereo("binaural_rotation.wav", bl, br)
    print("wav:", OUT / "binaural_rotation.wav", "(STEREO — use headphones)")

    hl, hr = headphone_check()
    save_stereo("headphone_check.wav", hl, hr, peak=0.6)
    print("wav:", OUT / "headphone_check.wav", "(STEREO — L-only, R-only, then binaural)")

    # Event stings — one per actor, all through the shared castle reverb.
    # Per-sting peak target = relative loudness in the mix (also the engine's
    # per-event gains). 0.7 is the default "fine" level; lower = quieter.
    STING_PEAK = {"fx_ghost.wav": 0.42, "fx_noise_veil.wav": 0.38, "fx_patronus.wav": 0.5}
    strows = {}
    for name, (fn, label) in STINGS.items():
        x = fn(); save(name, x, peak=STING_PEAK.get(name, 0.7)); strows[name] = (x, label)
        print("wav:", OUT / name)
    order1 = ["fx_rat.wav", "fx_cat.wav", "fx_owl.wav", "fx_snitch.wav",
              "fx_ghost.wav", "fx_peeves.wav", "fx_boggart.wav"]
    order2 = ["fx_draft.wav", "fx_rumble.wav", "fx_noise_veil.wav",
              "fx_time_glint.wav", "fx_dementor.wav", "fx_patronus.wav"]
    print(sheet([(n[3:-4], *strows[n]) for n in order1],
                "sheet-fx-creatures.png", "Event stings — the creatures"))
    print(sheet([(n[3:-4], *strows[n]) for n in order2],
                "sheet-fx-forces.png", "Event stings — the forces & set-pieces"))

    # Graph the beat-rate schedule so the rotation is visible, not just audible.
    tt = t_axis(len(beat) / SR)
    figb, axb = plt.subplots(figsize=(12, 3.2))
    figb.patch.set_facecolor(BG); axb.set_facecolor(PANEL)
    for s in axb.spines.values(): s.set_color(GRID)
    axb.tick_params(colors=MUTED)
    axb.plot(tt, beat, color=WING["verdigris"]["accent"], lw=2)
    for name, hz in STATES:
        axb.axhline(hz, color=MUTED, lw=0.6, ls=":")
        axb.text(0.2, hz + 0.3, f"{name}  ({hz:.0f} Hz)", color=INK, fontsize=9)
    axb.set_xlabel("time (s) — time-compressed; real hold ≈ 10 min/state", color=INK)
    axb.set_ylabel("binaural beat (Hz)", color=INK)
    axb.set_title("The rotation: calm → relaxed focus → alertness → (wrap)",
                  color=INK, fontsize=13, fontweight="bold")
    figb.tight_layout()
    figb.savefig(OUT / "sheet-binaural.png", facecolor=BG, dpi=110)
    plt.close(figb)
    print(OUT / "sheet-binaural.png")

    print(sheet([(n.replace('.wav',''), *rendered[n]) for n in
                 ["drone_harmonics.wav", "bells_phi.wav", "air_pink.wav"]],
                "sheet-ambient.png", "The ambient layer — formulas, envelopes, spectra"))
    print(sheet([(n.replace('.wav',''), *rendered[n]) for n in
                 ["stairs_shepard.wav", "sting_dementor.wav", "sting_patronus.wav"]],
                "sheet-setpieces.png", "Set pieces — the endless stair and the stingers"))
