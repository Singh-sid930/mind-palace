"""Concept figure for The Loom Across Time (video wing, silver).

Panel (a): the (T frames) x (h.w positions) grid. SPATIAL attention is one
           highlighted ROW (all positions within one frame attend), TEMPORAL
           attention is one highlighted COLUMN (one position across all frames).
Panel (b): cost bars, full joint 3D O((T.h.w)^2) towering over factorized
           O((h.w)^2)+O(T^2), representative T=21, h.w=1024, log scale.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_temporal.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import palace_fig as P

WING = "silver"
ACC = P.WING[WING]["accent"]    # cool silver
WARM = P.WING[WING]["warm"]     # gold  -> SPATIAL
COOL = "#8fb8e6"                # moonlit blue -> TEMPORAL
SPAT = WARM
TEMP = COOL


def main():
    f = plt.figure(figsize=(16.0, 8.0))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.32, 1.0], wspace=0.22,
                        left=0.045, right=0.975, top=0.80, bottom=0.145)

    P.suptitle(f, "Factorized Attention, space along a row, time down a column",
               WING)
    f.text(0.5, 0.865,
           "Two cheap axes of attention replace one impossible joint 3D "
           "attention.", ha="center", color=P.MUTED, fontsize=14)

    # =====================================================================
    # (a) the T x (h.w) grid with a highlighted row and column
    # =====================================================================
    ax = f.add_subplot(gs[0]); P.style_ax(ax, WING, grid=False)
    NR, NC = 5, 8                 # T frames (rows) x h.w positions (cols)
    spat_row = 2                  # 0-indexed from TOP -> frame 3
    temp_col = 5
    ax.set_xlim(-2.5, NC + 2.9)
    ax.set_ylim(-2.05, NR + 0.85)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(a)  One grid, two axes of attention", color=P.INK,
                 fontsize=15.5, pad=10)

    for r in range(NR):            # r=0 is top row (frame 1)
        yframe = NR - 1 - r        # y of cell bottom
        for c in range(NC):
            in_row = (r == spat_row)
            in_col = (c == temp_col)
            if in_row and in_col:
                fc = "#c8b8a0"     # the shared cell
            elif in_row:
                fc = SPAT
            elif in_col:
                fc = TEMP
            else:
                fc = "#1b2836"
            ax.add_patch(Rectangle((c + 0.08, yframe + 0.08), 0.84, 0.84,
                                   facecolor=fc, edgecolor=P.GRID, lw=1.2,
                                   zorder=3,
                                   alpha=1.0 if (in_row or in_col) else 0.9))

    # frame (row) labels on the left
    for r in range(NR):
        yc = NR - 1 - r + 0.5
        lbl = f"frame {r+1}"
        col = SPAT if r == spat_row else P.MUTED
        ax.text(-0.15, yc, lbl, ha="right", va="center", color=col,
                fontsize=12, fontweight="bold" if r == spat_row else "normal")

    # position (column) labels along the top
    for c in range(NC):
        col = TEMP if c == temp_col else P.MUTED
        ax.text(c + 0.5, NR + 0.12, f"p{c+1}", ha="center", va="bottom",
                color=col, fontsize=11,
                fontweight="bold" if c == temp_col else "normal")

    # axis meaning labels
    ax.text(NC / 2.0, NR + 0.62, "h·w spatial positions (one flattened frame)",
            ha="center", va="bottom", color=P.INK, fontsize=12.5,
            fontweight="bold")
    ax.text(-2.05, NR / 2.0, "T frames", ha="center", va="center",
            color=P.INK, fontsize=12.5, fontweight="bold", rotation=90)

    # SPATIAL callout (the row)
    yrow = NR - 1 - spat_row + 0.5
    ax.annotate("", xy=(NC + 0.5, yrow), xytext=(NC + 0.02, yrow),
                arrowprops=dict(arrowstyle="-|>", color=SPAT, lw=2.2))
    ax.text(NC + 0.62, yrow, "SPATIAL\nattention", ha="left", va="center",
            color=SPAT, fontsize=12.5, fontweight="bold", linespacing=1.2)

    # TEMPORAL callout (the column)
    ax.annotate("", xy=(temp_col + 0.5, -0.60), xytext=(temp_col + 0.5, -0.05),
                arrowprops=dict(arrowstyle="-|>", color=TEMP, lw=2.2))
    ax.text(temp_col + 0.5, -0.72, "TEMPORAL\nattention", ha="center",
            va="top", color=TEMP, fontsize=12.5, fontweight="bold",
            linespacing=1.2)

    # one-line meanings, centred safely below everything
    ax.text(NC / 2.0, -1.55,
            "row  =  all h·w positions within ONE frame attend to each other",
            ha="center", va="center", color=SPAT, fontsize=11.5)
    ax.text(NC / 2.0, -1.90,
            "column  =  ONE fixed position attends across ALL T frames",
            ha="center", va="center", color=TEMP, fontsize=11.5)

    # =====================================================================
    # (b) cost bars, log scale
    # =====================================================================
    ax2 = f.add_subplot(gs[1]); P.style_ax(ax2, WING, grid=True)
    T, HW = 21, 1024
    full = (T * HW) ** 2
    spatial = HW ** 2             # run T times, but one attention's length^2
    temporal = T ** 2
    fact = spatial + temporal

    labels = ["full joint 3D\nO((T·h·w)²)",
              "factorized\nO((h·w)²)+O(T²)"]
    vals = [full, fact]
    colors = ["#d98a8a", ACC]     # red = expensive, silver = cheap
    x = np.arange(2)
    bars = ax2.bar(x, vals, 0.56, color=colors, edgecolor=P.GRID, lw=1.4,
                   zorder=3)
    ax2.set_yscale("log")
    ax2.set_ylim(1e2, 3e9)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=12.5, color=P.INK)
    ax2.set_ylabel("attention pair-count  (log scale)", fontsize=12.5)
    ax2.set_title("(b)  Cost of one attention op   (T=21, h·w=1024)",
                  color=P.INK, fontsize=15.5, pad=10)

    val_txt = [f"{full:,.0f}\n≈ 4.6 × 10⁸", f"{fact:,.0f}\n≈ 1.05 × 10⁶"]
    for b, t in zip(bars, val_txt):
        ax2.annotate(t, (b.get_x() + b.get_width() / 2, b.get_height()),
                     xytext=(0, 6), textcoords="offset points", ha="center",
                     va="bottom", color=P.INK, fontsize=12, fontweight="bold")

    # the saving factor, drawn between the bar tops
    ratio = full / fact
    ax2.annotate("", xy=(1, fact * 1.25), xytext=(0, full * 0.9),
                 arrowprops=dict(arrowstyle="-|>", color=WARM, lw=2.0,
                                 connectionstyle="arc3,rad=-0.25"))
    ax2.text(0.5, 2.0e7, f"≈ {ratio:,.0f}×\ncheaper", ha="center", va="center",
             color=WARM, fontsize=14, fontweight="bold", linespacing=1.2)

    f.text(0.5, 0.032,
           "Full 3D attends over all T·h·w tokens at once, quadratic in their "
           "product;  factorizing pays only (h·w)² + T² instead, the same "
           "anti-quadratic escape seen across the palace.",
           ha="center", va="bottom", color=P.MUTED, fontsize=11.5)

    return f


if __name__ == "__main__":
    f = main()
    print(P.save(f, "video-factorized-attention.png"))
