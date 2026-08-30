"""Concept figures for The Forge of the Query (attention wing).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_forge.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import palace_fig as P

WING = "sapphire"
ACC = P.WING[WING]["accent"]   # cool blue
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]


def softmax(x):
    e = np.exp(np.array(x, float) - np.max(x))
    return e / e.sum()


def bar_labels(ax, bars, fmt="{:.2f}", dy=0.0, color=P.INK, size=12):
    for b in bars:
        h = b.get_height()
        ax.annotate(fmt.format(h), (b.get_x() + b.get_width() / 2, h),
                    xytext=(0, 4 + dy), textcoords="offset points",
                    ha="center", va="bottom", color=color, fontsize=size,
                    fontweight="bold")


# ===========================================================================
# FIGURE 1. The atomic attention unit, worked end to end
# ===========================================================================
def fig_worked_example():
    raw = [1.0, 3.0]
    scaled = [0.5, 1.5]
    weights = softmax(scaled)          # [0.2689, 0.7311]
    out = weights[0] * np.array([10, 0, 0, 0]) + weights[1] * np.array([0, 0, 0, 10])

    f = plt.figure(figsize=(16.5, 9.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 3, height_ratios=[1.0, 0.92],
                        hspace=0.46, wspace=0.32,
                        left=0.06, right=0.975, top=0.86, bottom=0.085)

    P.suptitle(f, "The Atomic Act of Attention, q · k  →  scale  →  softmax  →  blend")
    f.text(0.5, 0.905,
           "q = [1, 0, 2, 1]      k₁ = [1,1,0,0]   k₂ = [0,0,1,1]      "
           "v₁ = [10,0,0,0]   v₂ = [0,0,0,10]",
           ha="center", color=P.MUTED, fontsize=13.5)

    keys = ["k₁", "k₂"]
    x = np.arange(2)

    # (a) raw vs scaled scores ------------------------------------------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    w = 0.36
    b1 = ax.bar(x - w / 2, raw, w, color=WARM, label="raw  q·k", edgecolor=P.GRID)
    b2 = ax.bar(x + w / 2, scaled, w, color=ACC, label="÷ √d_k  (√4=2)",
                edgecolor=P.GRID)
    bar_labels(ax, b1, "{:.0f}")
    bar_labels(ax, b2, "{:.1f}")
    ax.set_xticks(x); ax.set_xticklabels(keys, fontsize=13)
    ax.set_ylim(0, 3.7)
    ax.set_title("(a)  Score, then scale", color=P.INK)
    ax.set_ylabel("dot-product score", fontsize=12)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11, loc="upper left")

    # (b) softmax weights -----------------------------------------------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    cols = [COOL, ACC]
    bb = ax.bar(x, weights, 0.55, color=cols, edgecolor=P.GRID)
    bar_labels(ax, bb, "{:.2f}")
    ax.axhline(0.5, color=P.MUTED, ls=":", lw=1.1)
    ax.text(1.46, 0.5, "0.5\nuniform", color=P.MUTED, fontsize=10,
            va="center", ha="left")
    ax.set_xticks(x); ax.set_xticklabels(keys, fontsize=13)
    ax.set_ylim(0, 1.0)
    ax.set_title("(b)  softmax → attention weights", color=P.INK)
    ax.set_ylabel("weight (sums to 1)", fontsize=12)

    # (c) output vector -------------------------------------------------------
    ax = f.add_subplot(gs[0, 2]); P.style_ax(ax, WING)
    xo = np.arange(4)
    bo = ax.bar(xo, out, 0.6, color=WARM, edgecolor=P.GRID)
    bar_labels(ax, bo, "{:.1f}")
    ax.set_xticks(xo)
    ax.set_xticklabels(["d₀", "d₁", "d₂", "d₃"], fontsize=12)
    ax.set_ylim(0, 8.6)
    ax.set_title("(c)  output = 0.27·v₁ + 0.73·v₂", color=P.INK)
    ax.set_ylabel("value", fontsize=12)
    ax.text(0.5, 8.0, "[2.7, 0, 0, 7.3], mostly v₂", color=ACC,
            fontsize=12.5, ha="left", fontweight="bold")

    # (d) the 3-query matrix form --------------------------------------------
    # one wide row of three heatmaps with arrows between
    gd = gs[1,:].subgridspec(1, 3, wspace=0.55)

    scores = np.array([[1, 3], [1, 1], [2, 1]], float)
    Wt = np.array([[0.27, 0.73], [0.50, 0.50], [0.62, 0.38]])
    O = np.array([[2.7, 0, 0, 7.3], [5.0, 0, 0, 5.0], [6.2, 0, 0, 3.8]])

    def heat(axp, M, title, fmt, cmapname, vmax=None, cols=None):
        ax = f.add_subplot(axp); P.style_ax(ax, WING, grid=False)
        cm = P.cmap(cmapname)
        im = ax.imshow(M, cmap=cm, aspect="auto",
                       vmin=0, vmax=vmax if vmax else M.max())
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M[i, j]
                lc = P.BG if (v / (vmax if vmax else M.max())) > 0.6 else P.INK
                ax.text(j, i, fmt.format(v), ha="center", va="center",
                        color=lc, fontsize=11.5, fontweight="bold")
        ax.set_xticks(range(M.shape[1]))
        ax.set_xticks(range(M.shape[1]))
        if cols:
            ax.set_xticklabels(cols, fontsize=11)
        else:
            ax.set_xticklabels(["d%d" % k for k in range(M.shape[1])], fontsize=10)
        ax.set_yticks(range(3))
        ax.set_yticklabels(["q₁", "q₂", "q₃"], fontsize=12)
        ax.set_title(title, color=P.INK, fontsize=13)
        for s in ax.spines.values():
            s.set_color(P.GRID)
        return ax

    ax1 = heat(gd[0, 0], scores, "Q·Kᵀ  (scores)", "{:.0f}", "fire",
               vmax=3, cols=["k₁", "k₂"])
    ax2 = heat(gd[0, 1], Wt, "softmax per row", "{:.2f}", "heat",
               vmax=1.0, cols=["k₁", "k₂"])
    ax3 = heat(gd[0, 2], O, "·V → output", "{:.1f}", "fire",
               vmax=7.3, cols=["d₀", "d₁", "d₂", "d₃"])

    f.text(0.155, 0.045,
           "(d)  All queries at once: each row is scaled, softmaxed and blended "
           "independently.   Row 1 = the single-query example above.",
           color=P.MUTED, fontsize=12)

    # arrows between the three heatmaps
    for a, b in [(ax1, ax2), (ax2, ax3)]:
        con = FancyArrowPatch(
            (1.06, 0.5), (-0.16, 0.5),
            transform=None, arrowstyle="-|>", mutation_scale=20,
            color=ACC, lw=2,
            connectionstyle="arc3", clip_on=False,
        )
        # place arrow in figure coords between the two axes
        x0 = a.get_position().x1
        x1 = b.get_position().x0
        ym = (a.get_position().y0 + a.get_position().y1) / 2
        arr = FancyArrowPatch((x0 + 0.004, ym), (x1 - 0.004, ym),
                              transform=f.transFigure, arrowstyle="-|>",
                              mutation_scale=22, color=ACC, lw=2.2,
                              clip_on=False)
        f.add_artist(arr)

    return P.save(f, "attention-worked-example.png")


# ===========================================================================
# FIGURE 2, softmax as normalise + sharpen, and √d_k scaling
# ===========================================================================
def fig_softmax_sharpening():
    base = np.array([0.5, 1.5])           # the scaled scores from the room
    factors = [1, 2, 4]                   # ×1, ×2, ×4  →  [.5,1.5] [1,3] [2,6]
    scoresets = [base * k for k in factors]
    labels = ["[0.5, 1.5]\n(scaled, √d_k=2)", "[1, 3]\n(raw, unscaled)",
              "[2, 6]\n(×4: over-sharp)"]
    Ws = [softmax(s) for s in scoresets]

    def entropy(w):
        return -np.sum(w * np.log2(w))

    ents = [entropy(w) for w in Ws]

    f, axes = P.fig(15.5, 7.4, wing=WING, ncols=2)
    f.subplots_adjust(left=0.065, right=0.975, top=0.80, bottom=0.16, wspace=0.24)
    P.suptitle(f, "Softmax = normalise + sharpen, why we divide by √d_k")
    f.text(0.5, 0.885,
           "Same score gap, scaled up: attention slides from near-uniform "
           "toward near one-hot.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # left: grouped bars per scaling --------------------------------------
    ax = axes[0]
    x = np.arange(3)
    w = 0.36
    w1 = [W[0] for W in Ws]
    w2 = [W[1] for W in Ws]
    b1 = ax.bar(x - w / 2, w1, w, color=COOL, edgecolor=P.GRID, label="weight on k₁")
    b2 = ax.bar(x + w / 2, w2, w, color=WARM, edgecolor=P.GRID, label="weight on k₂")
    bar_labels(ax, b1, "{:.2f}", size=11)
    bar_labels(ax, b2, "{:.2f}", size=11)
    ax.axhline(0.5, color=P.MUTED, ls=":", lw=1.1)
    ax.text(2.55, 0.5, "uniform", color=P.MUTED, fontsize=10, va="center")
    ax.text(2.55, 0.98, "one-hot", color=P.MUTED, fontsize=10, va="top")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11.5)
    ax.set_ylim(0, 1.06)
    ax.set_title("(a)  Larger scores → sharper attention", color=P.INK)
    ax.set_ylabel("softmax weight", fontsize=12.5)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11.5, loc="center left")

    # right: entropy decreasing -------------------------------------------
    ax = axes[1]
    be = ax.bar(x, ents, 0.5, color=ACC, edgecolor=P.GRID)
    bar_labels(ax, be, "{:.2f}", size=12)
    ax.axhline(1.0, color=P.MUTED, ls=":", lw=1.1)
    ax.text(2.55, 1.0, "1 bit = max\n(2-way tie)", color=P.MUTED, fontsize=10,
            va="center")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11.5)
    ax.set_ylim(0, 1.12)
    ax.set_title("(b)  Softmax entropy collapses as scores grow", color=P.INK)
    ax.set_ylabel("entropy  (bits)", fontsize=12.5)

    f.text(0.5, 0.035,
           "Dividing by √d_k keeps scores small so softmax stays soft and "
           "differentiable. Skip it and high-dimensional scores explode, "
           "softmax spikes to one-hot, and the gradient dies.",
           ha="center", color=P.INK, fontsize=12.5)

    return P.save(f, "softmax-sharpening.png")


if __name__ == "__main__":
    p1 = fig_worked_example()
    p2 = fig_softmax_sharpening()
    print("wrote", p1)
    print("wrote", p2)
