"""Concept figure for The Two Gazes: the SHAPE of the attention score matrix
in self- vs cross-attention, drawn to scale side by side.

Run with: ~/anaconda3/envs/lrm/bin/python tools/figs_gazes.py
"""
import sys
sys.path.insert(0, "tools")
import palace_fig as P
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

WING = "sapphire"
AC = P.WING[WING]["accent"]   # cool blue accent
WARM = P.WING[WING]["warm"]   # warm gold

# Common cell geometry so both matrices are drawn at the SAME cell size,
# making square-vs-rectangle unmistakable and to scale.
CELL = 1.0


def draw_matrix(ax, n_rows, n_cols, x0, y0, fill, edge, label_rows, label_cols):
    """Draw an n_rows x n_cols grid of unit cells with lower-left at (x0,y0)."""
    for r in range(n_rows):
        for c in range(n_cols):
            ax.add_patch(Rectangle(
                (x0 + c * CELL, y0 + r * CELL), CELL, CELL,
                facecolor=fill, edgecolor=edge, linewidth=1.6))
    # outer frame for emphasis
    ax.add_patch(Rectangle((x0, y0), n_cols * CELL, n_rows * CELL,
                           facecolor="none", edgecolor=edge, linewidth=3.0))
    return x0, y0, n_cols * CELL, n_rows * CELL


def main():
    f, axes = P.fig(13.5, 7.4, wing=WING, ncols=2)
    f.suptitle(r"The Shape of the Score Matrix  (Q$\cdot$K$^{\mathsf{T}}$)",
               color=P.INK, fontsize=19, fontweight="bold", y=0.99)

    # ---------- LEFT: self-attention, 6x6 square --------------------------
    axL = axes[0]
    axL.set_title("Self-attention", color=P.INK, pad=14)
    n = 6
    bx, by, bw, bh = draw_matrix(axL, n, n, 0, 0,
                                 fill="#1f3a5f", edge=AC,
                                 label_rows=True, label_cols=True)
    cx = bx + bw / 2
    # axis labels
    axL.text(cx, by + bh + 0.55, "keys  (n)", ha="center", va="bottom",
             color=AC, fontsize=13, fontweight="bold")
    axL.text(bx - 0.55, by + bh / 2, "queries  (n)", ha="right", va="center",
             color=AC, fontsize=13, fontweight="bold", rotation=90)
    axL.text(cx, by - 0.95,
             "Q, K, V from the SAME tokens",
             ha="center", va="top", color=P.INK, fontsize=13)
    axL.text(cx, by - 1.75,
             "→  (n, n). SQUARE",
             ha="center", va="top", color=WARM, fontsize=14.5,
             fontweight="bold")
    # symmetric horizontal margins so the square sits centered in the panel
    axL.set_xlim(-2.8, n + 2.8)
    axL.set_ylim(-3.4, n + 2.2)

    # ---------- RIGHT: cross-attention, 5x4 rectangle ---------------------
    axR = axes[1]
    axR.set_title("Cross-attention", color=P.INK, pad=14)
    nt, npatch = 5, 4   # 5 text rows, 4 image-patch columns
    bx2, by2, bw2, bh2 = draw_matrix(axR, nt, npatch, 0, 0,
                                     fill="#5c3a1a", edge=WARM,
                                     label_rows=True, label_cols=True)
    cx2 = bx2 + bw2 / 2
    axR.text(cx2, by2 + bh2 + 0.55, "keys  (n_patches)", ha="center",
             va="bottom", color=WARM, fontsize=13, fontweight="bold")
    axR.text(bx2 - 0.55, by2 + bh2 / 2, "queries  (n_text)", ha="right",
             va="center", color=WARM, fontsize=13, fontweight="bold",
             rotation=90)
    axR.text(cx2, by2 - 0.95,
             "Q from text  •  K, V from image",
             ha="center", va="top", color=P.INK, fontsize=13)
    axR.text(cx2, by2 - 1.75,
             "→  (n_text, n_patches). NOT SQUARE",
             ha="center", va="top", color=AC, fontsize=14.5,
             fontweight="bold")
    # SAME total x/y span (and aspect='equal') as left so cells are the same
    # physical size; center the 4-wide rectangle in that span.
    span = (n + 2.8) - (-2.8)           # left panel's x width
    pad = (span - npatch) / 2.0
    axR.set_xlim(-pad, npatch + pad)
    axR.set_ylim(-3.4, n + 2.2)

    for ax in (axL, axR):
        ax.set_aspect("equal")
        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)

    # ---------- unifying rule banner across the bottom --------------------
    f.text(0.5, 0.045,
           "The unifying rule:  K and V always come from whatever you look INTO.",
           ha="center", va="center", color=P.HOT, fontsize=15,
           fontweight="bold", style="italic")

    f.subplots_adjust(left=0.06, right=0.97, top=0.88, bottom=0.13,
                      wspace=0.28)
    out = P.save(f, "attention-shapes.png")
    print("wrote", out)


if __name__ == "__main__":
    main()
