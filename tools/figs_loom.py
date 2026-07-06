"""Concept figures for The Loom of Similarity (Wing of Arithmancy, violet).

Pure mathematics only: the dot product u·v = |u||v|cosθ as a similarity score,
and softmax turning scores into weights (with a sharpness/temperature knob).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_loom.py
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


def softmax(s):
    e = np.exp(np.array(s, float) - np.max(s))
    return e / e.sum()


def fig_dot_and_softmax():
    f = plt.figure(figsize=(16.8, 8.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.0, 1.12],
                        wspace=0.17, left=0.045, right=0.975,
                        top=0.82, bottom=0.10)

    P.suptitle(f, "Alignment → Weights:   u · v = |u||v|cos θ,   then softmax")
    f.text(0.5, 0.895,
           "The dot product scores how nearly two arrows agree; softmax turns "
           "a row of scores into positive weights that sum to 1.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- panel (a): geometry of the dot product --------------------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    u = np.array([2.7, 0.0])          # fixed reference arrow, |u| = 2.7
    # (angle, colour, label offset in points)
    specs = [(25, WARM, (14, -6), "left"),
             (70, ACC, (10, 12), "left"),
             (145, COOL, (-12, 10), "right")]
    vlen = 2.4
    ax.axhline(0, color=P.GRID, lw=0.8)
    ax.axvline(0, color=P.GRID, lw=0.8)
    ax.annotate("", xy=u, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=P.INK, lw=3.4))
    ax.annotate("u", u, xytext=(6, -16), textcoords="offset points",
                color=P.INK, fontsize=16, fontweight="bold")
    for th_deg, col, off, ha in specs:
        th = np.radians(th_deg)
        v = vlen * np.array([np.cos(th), np.sin(th)])
        dot = float(u @ v)
        ax.annotate("", xy=v, xytext=(0, 0),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.9))
        # arc marking the angle
        arc = np.linspace(0, th, 40)
        r = 0.55
        ax.plot(r * np.cos(arc), r * np.sin(arc), color=col, lw=1.4)
        ax.annotate(f"v   (θ = {th_deg}°)\nu·v = {dot:+.2f}", v,
                    xytext=off, textcoords="offset points", color=col,
                    fontsize=12, fontweight="bold", va="center", ha=ha)
    ax.text(0.5, -1.72,
            "same direction → large +      perpendicular → 0      opposed → −",
            transform=ax.transData, ha="center", color=P.MUTED, fontsize=11.5)
    ax.set_xlim(-3.0, 3.3)
    ax.set_ylim(-2.0, 2.7)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(a)  the dot product measures alignment", color=P.INK)

    # ---- panel (b): softmax + temperature sharpening ---------------------
    gb = gs[0, 1].subgridspec(2, 1, height_ratios=[1.0, 1.0], hspace=0.42)

    scores = np.array([2.0, 1.0, 0.0, -0.5])
    labels = ["s₁=2.0", "s₂=1.0", "s₃=0.0", "s₄=−0.5"]
    x = np.arange(len(scores))

    # (b1) scores -> weights
    ax1 = f.add_subplot(gb[0, 0]); P.style_ax(ax1, WING)
    w = softmax(scores)
    bb = ax1.bar(x, w, 0.6, color=ACC, edgecolor=P.GRID)
    for b, val in zip(bb, w):
        ax1.annotate(f"{val:.2f}", (b.get_x() + b.get_width() / 2,
                     b.get_height()), xytext=(0, 4), textcoords="offset points",
                     ha="center", color=P.INK, fontsize=12, fontweight="bold")
    ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=12)
    ax1.set_ylim(0, 0.78)
    ax1.set_ylabel("weight", fontsize=12)
    ax1.set_title("(b)  softmax: raw scores → weights that sum to 1",
                  color=P.INK)
    ax1.text(0.98, 0.72, "Σ weights = 1.00", transform=ax1.transAxes,
             ha="right", va="top", color=P.MUTED, fontsize=11)

    # (b2) temperature sweep
    ax2 = f.add_subplot(gb[1, 0]); P.style_ax(ax2, WING)
    temps = [(0.5, WARM, "τ = 0.5  (sharper)"),
             (1.0, ACC, "τ = 1.0"),
             (2.5, COOL, "τ = 2.5  (flatter)")]
    ww = 0.24
    for i, (t, col, lab) in enumerate(temps):
        wt = softmax(scores / t)
        ax2.bar(x + (i - 1) * ww, wt, ww, color=col, edgecolor=P.GRID,
                label=lab)
    ax2.axhline(0.25, color=P.MUTED, ls=":", lw=1.1)
    ax2.text(3.35, 0.25, "uniform\n(0.25)", color=P.MUTED, fontsize=10,
             va="center")
    ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=12)
    ax2.set_ylim(0, 0.92)
    ax2.set_ylabel("weight", fontsize=12)
    ax2.set_title("(c)  temperature tunes the sharpness (same scores)",
                  color=P.INK)
    ax2.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
               fontsize=10.5, loc="upper right", ncol=1)

    return P.save(f, "dot-product-softmax.png")


if __name__ == "__main__":
    print("wrote", fig_dot_and_softmax())
