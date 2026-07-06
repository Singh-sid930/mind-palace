"""Concept figure for The Adaptive Sanctum (DiT wing) — adaLN-Zero.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_sanctum.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import palace_fig as P

WING = "crimson"
ACC = P.WING[WING]["accent"]   # coral
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]    # rose


def box(ax, x, y, w, h, text, fc, tc=None, fs=11.5, lw=1.6, ec=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.06",
                 facecolor=fc, edgecolor=ec or P.GRID, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tc or P.BG, fontsize=fs, fontweight="bold")


def fig_adaln():
    f = plt.figure(figsize=(16.5, 9.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 2, height_ratios=[0.92, 1.0],
                        width_ratios=[1.02, 1.0],
                        hspace=0.40, wspace=0.20,
                        left=0.055, right=0.972, top=0.85, bottom=0.115)

    P.suptitle(f, "The Adaptive Sanctum  —  adaLN-Zero pours the block's dials from (t, c)")
    f.text(0.5, 0.905,
           "One conditioning vector cond = t_embed + c_embed is spun by an MLP "
           "into per-block (γ, β, α). The α gate starts at ZERO.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # --- (a) conditioning fan-out schematic --------------------------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.set_title("(a)  one signal → MLP → the block's adaptive dials",
                 color=P.INK, fontsize=13.5, loc="left")

    box(ax, 0.1, 4.05, 1.85, 0.62, "timestep t", WARM, fs=10.5)
    box(ax, 0.1, 2.72, 1.85, 0.72, "class / text c\n(or null)", COOL, fs=9.5)
    ax.text(2.4, 3.82, "+", color=P.INK, fontsize=20, ha="center", va="center",
            fontweight="bold")
    box(ax, 2.7, 3.28, 2.35, 0.95, "cond = t_embed\n+ c_embed", ACC, tc=P.BG, fs=10.5)
    box(ax, 5.55, 3.42, 1.25, 0.66, "small\nMLP", P.INK, tc=P.BG, fs=10.5)
    ax.annotate("", xy=(2.65, 3.92), xytext=(1.95, 4.36),
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.8))
    ax.annotate("", xy=(2.65, 3.58), xytext=(1.95, 3.08),
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.8))
    ax.annotate("", xy=(5.5, 3.75), xytext=(5.05, 3.75),
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=2.2))

    # the six outputs, grouped by sub-layer
    box(ax, 7.15, 4.5, 2.7, 1.0, "attention sub-layer\nγ₁    β₁    α₁", WARM,
        tc=P.BG, fs=10.5)
    box(ax, 7.15, 2.3, 2.7, 1.0, "MLP sub-layer\nγ₂    β₂    α₂", COOL,
        tc=P.BG, fs=10.5)
    ax.annotate("", xy=(7.1, 5.0), xytext=(6.82, 3.9),
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=2.0))
    ax.annotate("", xy=(7.1, 2.8), xytext=(6.82, 3.6),
                arrowprops=dict(arrowstyle="-|>", color=COOL, lw=2.0))
    ax.text(5.0, 1.35, "γ scales · β shifts · α gates the residual — "
            "regenerated fresh for every (t, c)",
            ha="center", color=P.INK, fontsize=11.5, fontstyle="italic")

    # --- (b) γ scale + β shift on the token distribution -------------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    xs = np.linspace(-5, 6, 500)

    def gauss(x, mu, sd):
        return np.exp(-0.5 * ((x - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi))

    g, b = 1.7, 1.6
    ax.plot(xs, gauss(xs, 0, 1), color=P.MUTED, lw=2.4,
            label="normalize(x):  mean 0, std 1")
    ax.fill_between(xs, gauss(xs, 0, 1), color=P.MUTED, alpha=0.12)
    ax.plot(xs, gauss(xs, b, g), color=ACC, lw=2.8,
            label=f"adaLN = γ·normalize(x) + β\n(γ={g}, β={b})")
    ax.fill_between(xs, gauss(xs, b, g), color=ACC, alpha=0.18)
    ax.axvline(0, color=P.MUTED, ls=":", lw=1.1)
    ax.axvline(b, color=ACC, ls=":", lw=1.4)
    ax.annotate("β shifts the center", xy=(b, 0.05), xytext=(3.0, 0.14),
                color=ACC, fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.6))
    ax.annotate("γ widens the spread", xy=(b + g, 0.10), xytext=(2.4, 0.28),
                color=WARM, fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.6))
    ax.set_ylim(0, 0.46)
    ax.set_xlabel("feature value", fontsize=12)
    ax.set_ylabel("density", fontsize=12)
    ax.set_title("(b)  same LN formula — but γ, β poured from (t, c)",
                 color=P.INK, fontsize=13.5)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=10.5, loc="upper left")

    # --- (c) α fades in from zero over training ----------------------------
    ax = f.add_subplot(gs[1, :]); P.style_ax(ax, WING)
    steps = np.linspace(0, 100, 400)
    taus = [16, 30, 52, 80]
    labels = ["block 4 (shallow)", "block 12", "block 20",
              "block 28 (deep) — opens last"]
    cols = [ACC, WARM, COOL, "#c98fb0"]
    for tau, lab, col in zip(taus, labels, cols):
        alpha = 1 - np.exp(-steps / tau)
        ax.plot(steps, alpha, color=col, lw=2.8, label=lab)
    ax.scatter([0], [0], s=90, color=P.INK, zorder=6)
    ax.annotate("α = 0 at init\n→ branch ×0 → block is pure identity (x → x)",
                xy=(0, 0), xytext=(9, 0.30), color=P.INK, fontsize=12,
                fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=P.INK, lw=1.8))
    ax.axhline(0, color=P.MUTED, ls=":", lw=1.0)
    ax.text(99, 0.02, "residual silenced", color=P.MUTED, fontsize=10,
            ha="right", va="bottom")
    ax.text(70, 0.55, "training turns each block on\nby learning α upward from 0",
            color=P.INK, fontsize=12.5, ha="left", fontstyle="italic")
    ax.set_xlim(0, 100); ax.set_ylim(-0.03, 1.02)
    ax.set_xlabel("training step  (stylized)", fontsize=12.5)
    ax.set_ylabel("α  =  residual-branch gate", fontsize=12.5)
    ax.set_title("(c)  the 'Zero': every gate starts shut, so a newborn "
                 "deep DiT is a stable pass-through", color=P.INK, fontsize=13.5)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11, loc="lower right", ncol=2)

    f.text(0.5, 0.022,
           "output = x + α · branch(adaLN(x)).  At α=0 the block writes nothing "
           "onto the residual highway; gradients flow straight down. Depth is "
           "earned, not fought from the first step.",
           ha="center", color=P.INK, fontsize=12.5)

    return P.save(f, "dit-adaln-zero.png")


if __name__ == "__main__":
    print("wrote", fig_adaln())
