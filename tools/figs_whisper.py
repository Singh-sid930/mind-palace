"""Concept figure for The Parallel Whisper (LoRA wing, obsidian palette).

The parallel branch and its rank-r bottleneck: y = W.x + B.A.x.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_whisper.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch
import palace_fig as P

WING = "obsidian"
ACC = P.WING[WING]["accent"]   # teal glow
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]

D = 1000
R = 8


def node(ax, cx, cy, w, h, label, sub, face, edge, txtcol=None):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.10",
                                facecolor=face, edgecolor=edge, lw=1.8))
    tc = txtcol if txtcol else P.INK
    ax.text(cx, cy + (0.10 if sub else 0), label, ha="center", va="center",
            color=tc, fontsize=13.5, fontweight="bold")
    if sub:
        ax.text(cx, cy - 0.34, sub, ha="center", va="center",
                color=tc, fontsize=11, alpha=0.9)


def arrow(ax, x0, y0, x1, y1, color=ACC, lw=2.2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                 mutation_scale=18, color=color, lw=lw,
                                 shrinkA=2, shrinkB=2))


def fig_branch():
    f = plt.figure(figsize=(16.5, 8.4))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.16,
                        left=0.03, right=0.975, top=0.80, bottom=0.10)

    P.suptitle(f, "The Parallel Whisper, y = W.x + B.A.x,  one input, two paths")
    f.text(0.5, 0.885,
           "The LoRA branch runs BESIDE the frozen W on the same input x, "
           "not after it.   d = 1000,  r = 8.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ------------------------------------------------------------------ (a)
    # dataflow, node widths encode dimension (wide d, narrow r)
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 12); ax.set_ylim(0, 10)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(P.GRID)
    ax.set_title("(a)  One input x fans into two parallel paths",
                 color=P.INK, fontsize=14, pad=10)

    WIDE = 2.2      # width for a d-dimensional node
    NARROW = 0.85   # width for an r-dimensional node
    h = 1.15

    yc = 5.0        # center line
    ytop = 7.6      # frozen path
    ybot = 2.4      # lora branch

    # input x (d)
    node(ax, 1.3, yc, WIDE, h, "x", "(d,)", "#1b2735", P.INK)

    # frozen path:  x -> W.x
    node(ax, 5.6, ytop, WIDE, h, "W . x", "(d,) frozen", "#22303f", COOL,
         txtcol=COOL)
    # lora branch: A -> A.x (bottleneck) -> B -> B.A.x
    node(ax, 4.0, ybot, NARROW + 0.5, h, "A", "r x d", "#243b3a", ACC,
         txtcol=ACC)
    node(ax, 6.15, ybot, NARROW, h * 0.92, "A.x", "(r,)", ACC, P.BG,
         txtcol=P.BG)
    node(ax, 8.3, ybot, NARROW + 0.5, h, "B", "d x r", "#243b3a", ACC,
         txtcol=ACC)
    node(ax, 10.5, ybot, WIDE, h, "B.A.x", "(d,)", "#22303f", ACC,
         txtcol=ACC)

    # sum node
    sx, sy = 10.5, ytop
    ax.add_patch(plt.Circle((sx, sy), 0.42, facecolor=WARM, edgecolor=P.BG,
                            lw=1.6, zorder=4))
    ax.text(sx, sy, "+", ha="center", va="center", color=P.BG,
            fontsize=20, fontweight="bold", zorder=5)
    # output y
    ax.text(11.55, (ytop + ybot) / 2, "y", ha="center", va="center",
            color=P.INK, fontsize=15, fontweight="bold")
    ax.text(11.55, (ytop + ybot) / 2 - 0.5, "(d,)", ha="center", va="center",
            color=P.MUTED, fontsize=11)

    # arrows
    arrow(ax, 1.3, yc + 0.35, 5.6 - WIDE / 2, ytop - 0.35, color=COOL)   # x->W
    arrow(ax, 1.3, yc - 0.35, 4.0 - (NARROW + 0.5) / 2, ybot + 0.35)     # x->A
    arrow(ax, 4.0 + (NARROW + 0.5) / 2, ybot, 6.15 - NARROW / 2, ybot)   # A->Ax
    arrow(ax, 6.15 + NARROW / 2, ybot, 8.3 - (NARROW + 0.5) / 2, ybot)   # Ax->B
    arrow(ax, 8.3 + (NARROW + 0.5) / 2, ybot, 10.5 - WIDE / 2, ybot)     # B->BAx
    arrow(ax, 5.6 + WIDE / 2, ytop, sx - 0.45, sy, color=COOL)           # Wx->+
    arrow(ax, 10.5, ybot + h / 2, sx - 0.30, sy - 0.42)                  # BAx->+
    arrow(ax, sx + 0.42, sy, 11.35, (ytop + ybot) / 2, color=WARM)       # +->y

    # bottleneck call-out under A.x
    ax.annotate("BOTTLENECK\nsqueeze to r = 8", xy=(6.15, ybot - h * 0.46),
                xytext=(6.15, 0.55), ha="center", va="bottom",
                color=WARM, fontsize=11.5, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=WARM, lw=1.6))
    ax.text(6.0, 9.15, "wide = d,   narrow = r  (widths drawn to dimension)",
            ha="center", va="center", color=P.MUTED, fontsize=11.5,
            style="italic")

    # ------------------------------------------------------------------ (b)
    # shape trace bars along the branch
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    stages = ["x", "A . x", "B . A . x"]
    widths = [D, R, D]
    cols = [COOL, WARM, ACC]
    xpos = np.arange(3)
    bars = ax.bar(xpos, widths, width=0.62, color=cols, edgecolor=P.GRID,
                  lw=1.2)
    ax.set_yscale("log")
    for b, w, dim in zip(bars, widths, ["(d,)", "(r,)", "(d,)"]):
        ax.annotate(f"{w}\n{dim}", (b.get_x() + b.get_width() / 2, w),
                    xytext=(0, 6), textcoords="offset points", ha="center",
                    va="bottom", color=P.INK, fontsize=13, fontweight="bold")
    ax.set_xticks(xpos)
    ax.set_xticklabels(stages, fontsize=13)
    ax.set_ylim(3, 3000)
    ax.set_ylabel("width  (numbers carried), log scale", fontsize=12.5)
    ax.set_title("(b)  The shape trace: squeeze to r, expand to d",
                 color=P.INK, fontsize=14, pad=10)
    # highlight the bottleneck bar
    ax.annotate("squeeze to r\nforces low rank", xy=(0.72, R * 1.15),
                xytext=(0.55, 220), ha="center", va="center",
                color=WARM, fontsize=12.5, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=WARM, lw=1.8))
    ax.text(0.0, 1500, "in", ha="center", color=COOL, fontsize=11)
    ax.text(2.0, 1500, "out", ha="center", color=ACC, fontsize=11)

    return P.save(f, "lora-parallel-branch.png")


if __name__ == "__main__":
    print("wrote", fig_branch())
