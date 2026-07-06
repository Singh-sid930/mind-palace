"""Concept figures for The Wheel of Frequencies (Wing of Arithmancy, violet).

Pure mathematics only: a ladder of sinusoids at geometrically spaced
frequencies, and a unit-circle panel showing that rotation preserves length
and that rotating by θ then φ equals rotating by θ+φ.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_wheel.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "violet"
ACC = P.WING[WING]["accent"]
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]


def fig_sinusoids_and_rotation():
    f = plt.figure(figsize=(16.8, 8.4))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.25, 1.0],
                        wspace=0.16, left=0.05, right=0.975,
                        top=0.82, bottom=0.11)

    P.suptitle(f, "Sinusoids & Rotation:   a ladder of frequencies, and angles that add")
    f.text(0.5, 0.895,
           "Fast and slow hands together fix a unique position; a rotation "
           "keeps length, and rotating by θ then φ equals rotating by θ+φ.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- panel (a): ladder of sinusoids, slow to fast --------------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    t = np.linspace(0, 4 * np.pi, 1000)
    # geometrically spaced frequencies: 1/10000^(2i/d) style ladder
    freqs = [0.25, 0.5, 1.0, 2.0, 4.0]
    names = ["slowest hand", "", "", "", "fastest hand"]
    offset = 0.0
    step = 2.6
    marker_t = 3.1   # one shared index n to read every hand at
    for i, fr in enumerate(freqs):
        col = tuple(np.array(_hex(WARM)) * (1 - i / (len(freqs) - 1)) +
                    np.array(_hex(COOL)) * (i / (len(freqs) - 1)))
        y = offset - i * step
        ax.axhline(y, color=P.GRID, lw=0.7, alpha=0.5)
        ax.plot(t, y + np.sin(fr * t), color=col, lw=2.4)
        ax.text(-0.35, y, f"freq {fr:g}", color=col, fontsize=11.5,
                ha="right", va="center", fontweight="bold")
        if names[i]:
            ax.text(-0.35, y - 0.9, names[i], color=P.MUTED, fontsize=9.5,
                    ha="right", va="center")
        # read this hand at the shared index
        ax.plot(marker_t, y + np.sin(fr * marker_t), "o", color=ACC,
                ms=7, zorder=6)
    ax.axvline(marker_t, color=ACC, ls="--", lw=1.6, zorder=5)
    ax.annotate("one index n, read on\nevery hand → a unique\nfingerprint of n",
                xy=(marker_t, offset + 0.9), xytext=(6.2, 1.55),
                color=ACC, fontsize=12, va="center", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.5))
    ax.set_xlim(-2.6, 4 * np.pi)
    ax.set_ylim(-len(freqs) * step + 0.4, 2.0)
    ax.set_yticks([])
    ax.set_xlabel("index / position  →", fontsize=12.5)
    ax.set_title("(a)  a ladder of sinusoids: slow hands to fast hands",
                 color=P.INK)

    # ---- panel (b): rotation on the unit circle, angles add --------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING, grid=False)
    th = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(th), np.sin(th), color=P.GRID, lw=1.4)
    ax.axhline(0, color=P.GRID, lw=0.7)
    ax.axvline(0, color=P.GRID, lw=0.7)

    a0 = np.radians(20)     # starting vector
    thA = np.radians(45)    # rotate by θ
    phi = np.radians(55)    # then by φ
    def vec(ang):
        return np.array([np.cos(ang), np.sin(ang)])

    v0 = vec(a0)
    v1 = vec(a0 + thA)
    v2 = vec(a0 + thA + phi)
    for v, col, lab in [(v0, P.INK, "start"),
                        (v1, WARM, "after +θ"),
                        (v2, ACC, "after +θ+φ")]:
        ax.annotate("", xy=v, xytext=(0, 0),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.8))
        ax.text(v[0] * 1.13, v[1] * 1.13, lab, color=col, fontsize=11.5,
                ha="center", va="center", fontweight="bold")

    # arcs for the two rotations
    arcA = np.linspace(a0, a0 + thA, 40)
    ax.plot(0.45 * np.cos(arcA), 0.45 * np.sin(arcA), color=WARM, lw=2.0)
    ax.text(0.55 * np.cos(a0 + thA / 2), 0.55 * np.sin(a0 + thA / 2), "θ",
            color=WARM, fontsize=14, ha="center", fontweight="bold")
    arcB = np.linspace(a0 + thA, a0 + thA + phi, 40)
    ax.plot(0.72 * np.cos(arcB), 0.72 * np.sin(arcB), color=ACC, lw=2.0)
    ax.text(0.85 * np.cos(a0 + thA + phi / 2), 0.85 * np.sin(a0 + thA + phi / 2),
            "φ", color=ACC, fontsize=14, ha="center", fontweight="bold")

    ax.text(0, -1.32, "length stays 1  ·  θ then φ  =  θ + φ",
            ha="center", color=P.INK, fontsize=13, fontweight="bold")
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.5, 1.45)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(b)  rotation preserves length; angles add", color=P.INK)

    return P.save(f, "sinusoids-rotation.png")


def _hex(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


if __name__ == "__main__":
    print("wrote", fig_sinusoids_and_rotation())
