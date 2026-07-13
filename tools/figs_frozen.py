"""Concept figure for The Frozen Tapestry (LoRA wing, obsidian palette).

The low-rank bet: freeze W, learn only the thin factors B and A.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_frozen.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import palace_fig as P

WING = "obsidian"
ACC = P.WING[WING]["accent"]   # teal glow
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]

D = 1000
R = 8
FULL = D * D            # 1,000,000
LOW = 2 * D * R         # 16,000


def bar_labels(ax, bars, texts, dy=0.0, color=P.INK, size=13):
    for b, t in zip(bars, texts):
        h = b.get_height()
        ax.annotate(t, (b.get_x() + b.get_width() / 2, h),
                    xytext=(0, 5 + dy), textcoords="offset points",
                    ha="center", va="bottom", color=color, fontsize=size,
                    fontweight="bold")


def fig_savings():
    f = plt.figure(figsize=(17, 7.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 3, width_ratios=[1.35, 0.95, 1.05],
                        wspace=0.30, left=0.045, right=0.975,
                        top=0.80, bottom=0.13)

    P.suptitle(f, "The Low-Rank Bet  —  freeze W, learn only the thin factors B and A")
    f.text(0.5, 0.885,
           "A weight update DeltaW (d x d) is approximated by B . A with inner rank r << d.   "
           "d = 1000,  r = 8.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ------------------------------------------------------------------ (a)
    # shape schematic — DeltaW square vs the thin B . A product
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(P.GRID)
    ax.set_title("(a)  The shapes: a square vs. a thin waist", color=P.INK,
                 fontsize=14, pad=10)

    side = 4.2                       # the full d x d square
    y0 = 2.9
    # DeltaW (frozen-shape, full square)
    ax.add_patch(Rectangle((0.4, y0), side, side, facecolor="#1b2735",
                           edgecolor=COOL, lw=2.0))
    ax.text(0.4 + side / 2, y0 + side / 2, "DeltaW\nd x d",
            ha="center", va="center", color=P.INK, fontsize=14, fontweight="bold")
    ax.text(0.4 + side / 2, y0 - 0.55, "1,000,000 numbers", ha="center",
            va="top", color=WARM, fontsize=12.5, fontweight="bold")
    ax.text(0.4 - 0.15, y0 + side / 2, "d", ha="right", va="center",
            color=P.MUTED, fontsize=13)
    ax.text(0.4 + side / 2, y0 + side + 0.25, "d", ha="center", va="bottom",
            color=P.MUTED, fontsize=13)

    ax.text(5.15, y0 + side / 2, "~", ha="center", va="center",
            color=P.INK, fontsize=26, fontweight="bold")

    # B  (d x r)  — tall, thin
    rw = side * R / 120.0            # exaggerated thin waist (true r/d = 0.008)
    rw = max(rw, 0.42)
    bx = 5.9
    ax.add_patch(Rectangle((bx, y0), rw, side, facecolor=ACC,
                           edgecolor=P.INK, lw=1.5, alpha=0.92))
    ax.text(bx + rw / 2, y0 + side / 2, "B", ha="center", va="center",
            color=P.BG, fontsize=15, fontweight="bold", rotation=0)
    ax.text(bx + rw / 2, y0 - 0.55, "d x r", ha="center", va="top",
            color=P.INK, fontsize=12)
    ax.text(bx + rw / 2, y0 + side + 0.25, "r", ha="center", va="bottom",
            color=ACC, fontsize=13, fontweight="bold")

    ax.text(bx + rw + 0.5, y0 + side / 2, ".", ha="center", va="center",
            color=P.INK, fontsize=22, fontweight="bold")

    # A  (r x d) — wide, thin
    ax.plot([], [])
    ax_y = y0 + side / 2 - rw / 2
    axx = bx + rw + 1.0
    ax.add_patch(Rectangle((axx, ax_y), side, rw, facecolor=ACC,
                           edgecolor=P.INK, lw=1.5, alpha=0.92))
    ax.text(axx + side / 2, ax_y + rw / 2, "A", ha="center", va="center",
            color=P.BG, fontsize=15, fontweight="bold")
    ax.text(axx + side / 2, ax_y - 0.35, "r x d", ha="center", va="top",
            color=P.INK, fontsize=12)
    ax.text(axx + side + 0.15, ax_y + rw / 2, "r", ha="left", va="center",
            color=ACC, fontsize=13, fontweight="bold")
    ax.text(axx + side / 2, ax_y + rw + 0.25, "d", ha="center", va="bottom",
            color=P.MUTED, fontsize=13)

    ax.text(bx + rw / 2 + 1.6, y0 - 1.55,
            "B . A = 16,000 numbers  (rank at most r)",
            ha="center", va="top", color=WARM, fontsize=12.5, fontweight="bold")

    # ------------------------------------------------------------------ (b)
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    ax.set_yscale("log")
    bars = ax.bar([0, 1], [FULL, LOW], width=0.6,
                  color=[COOL, ACC], edgecolor=P.GRID, lw=1.2)
    bar_labels(ax, [bars[0]], ["1,000,000"], color=P.INK, size=13.5)
    bar_labels(ax, [bars[1]], ["16,000"], color=ACC, size=13.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["full DeltaW\n(d x d)", "B . A\n(d x r)+(r x d)"],
                       fontsize=12.5)
    ax.set_ylim(5e3, 3e6)
    ax.set_ylabel("parameters to learn  (log scale)", fontsize=12.5)
    ax.set_title("(b)  62x fewer parameters", color=P.INK, fontsize=14, pad=10)
    # 62x arrow annotation
    ax.annotate("", xy=(1, LOW * 1.7), xytext=(1, FULL * 0.6),
                arrowprops=dict(arrowstyle="<->", color=WARM, lw=2.0))
    ax.text(1.05, np.sqrt(FULL * LOW), "62x\nfewer", ha="left", va="center",
            color=WARM, fontsize=15, fontweight="bold")

    # ------------------------------------------------------------------ (c)
    ax = f.add_subplot(gs[0, 2]); P.style_ax(ax, WING)
    rs = np.array([1, 2, 4, 8, 16, 32])
    low = 2 * D * rs
    ax.axhline(FULL, color=COOL, lw=2.2, ls="--")
    ax.text(32, FULL * 1.12, "full fine-tune: 1,000,000 (flat, rank d)",
            ha="right", va="bottom", color=COOL, fontsize=11.5,
            fontweight="bold")
    ax.plot(rs, low, "-o", color=ACC, lw=2.4, ms=8, mec=P.BG, mew=1.2,
            label="B . A  =  2 d r")
    # highlight r = 8
    ax.plot([8], [2 * D * 8], "o", color=WARM, ms=13, mec=P.BG, mew=1.4,
            zorder=5)
    ax.annotate("r = 8 -> 16,000", xy=(8, 2 * D * 8),
                xytext=(9.5, 2 * D * 8 * 0.30),
                color=WARM, fontsize=12.5, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=WARM, lw=1.8))
    ax.set_yscale("log")
    ax.set_xscale("log", base=2)
    ax.set_xticks(rs)
    ax.set_xticklabels([str(r) for r in rs], fontsize=11.5)
    ax.set_xlim(0.9, 40)
    ax.set_ylim(1.2e3, 3e6)
    ax.set_xlabel("rank  r", fontsize=12.5)
    ax.set_ylabel("parameters to learn  (log)", fontsize=12.5)
    ax.set_title("(c)  Tiny r stays far below full", color=P.INK,
                 fontsize=14, pad=10)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=12, loc="lower right")

    return P.save(f, "lora-parameter-savings.png")


if __name__ == "__main__":
    print("wrote", fig_savings())
