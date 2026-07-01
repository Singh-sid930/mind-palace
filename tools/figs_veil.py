"""Figures for The Veil of the Future (causal masking; encoder vs decoder).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_veil.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "sapphire"
ACCENT = P.WING[WING]["accent"]
WARM = P.WING[WING]["warm"]


def _cells(ax, M, mask=None, fmt="{:.0f}", text_thresh=0.55,
           vmin=None, vmax=None, cmap=None, blank="−∞"):
    """Render matrix M as a heatmap with per-cell text labels.

    mask: boolean array, True where the cell is forbidden (drawn dark + `blank`).
    """
    n = M.shape[0]
    if cmap is None:
        cmap = P.cmap("heat")
    disp = np.array(M, dtype=float)
    if mask is not None:
        disp = np.where(mask, np.nan, disp)
    if vmin is None:
        vmin = np.nanmin(disp)
    if vmax is None:
        vmax = np.nanmax(disp)
    cmap.set_bad(P.BG)
    ax.imshow(disp, cmap=cmap, vmin=vmin, vmax=vmax, aspect="equal")
    rng = (vmax - vmin) or 1.0
    for i in range(n):
        for j in range(n):
            if mask is not None and mask[i, j]:
                ax.text(j, i, blank, ha="center", va="center",
                        color=P.MUTED, fontsize=13, fontweight="bold")
                continue
            v = M[i, j]
            norm = (v - vmin) / rng
            col = P.BG if norm > text_thresh else P.INK
            ax.text(j, i, fmt.format(v), ha="center", va="center",
                    color=col, fontsize=13)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    for sp in ax.spines.values():
        sp.set_color(P.GRID)
    ax.tick_params(length=0, colors=P.MUTED, labelsize=12)
    ax.set_xticks(np.arange(-.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-.5, n, 1), minor=True)
    ax.grid(which="minor", color=P.BG, linewidth=2.5)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)


# ---------------------------------------------------------------------------
# Figure 1: the causal mask in three stages
# ---------------------------------------------------------------------------
def causal_mask():
    f, axes = P.fig(15.5, 6.4, wing=WING, ncols=3)
    P.suptitle(f, "The Causal Mask: how a decoder forgets the future", wing=WING)

    # (a) raw 4x4 scores Q·Kᵀ (illustrative integers)
    raw = np.array([
        [3, 1, 0, 2],
        [1, 4, 2, 1],
        [2, 1, 3, 0],
        [1, 2, 1, 4],
    ], dtype=float)
    qk = ["q1", "q2", "q3", "q4"]
    kk = ["k1", "k2", "k3", "k4"]

    ax = axes[0]
    _cells(ax, raw, fmt="{:.0f}", vmin=0, vmax=4, cmap=P.cmap("heat"))
    ax.set_xticklabels(kk)
    ax.set_yticklabels(qk)
    ax.set_title("(a)  raw scores  Q·Kᵗ", color=P.INK, fontsize=15, pad=10)
    ax.set_xlabel("keys (what is looked at)", color=P.MUTED, fontsize=12)
    ax.set_ylabel("queries (the token asking)", color=P.MUTED, fontsize=12)

    # (b) mask the strict upper triangle → −∞
    mask = np.triu(np.ones((4, 4), dtype=bool), k=1)
    ax = axes[1]
    _cells(ax, raw, mask=mask, fmt="{:.0f}", vmin=0, vmax=4,
           cmap=P.cmap("heat"), blank="−∞")
    ax.set_xticklabels(kk)
    ax.set_yticklabels(qk)
    ax.set_title("(b)  upper triangle → −∞", color=P.INK, fontsize=15, pad=10)
    ax.text(0.5, -0.16, "the future is forbidden",
            transform=ax.transAxes, ha="center", color=WARM, fontsize=12,
            style="italic")

    # (c) softmaxed lower-triangular weights — room's EXACT values
    W = np.array([
        [1.000, 0.000, 0.000, 0.000],
        [0.047, 0.953, 0.000, 0.000],
        [0.665, 0.090, 0.245, 0.000],
        [0.083, 0.224, 0.083, 0.610],
    ])
    zero_mask = np.triu(np.ones((4, 4), dtype=bool), k=1)
    ax = axes[2]
    _cells(ax, W, mask=zero_mask, fmt="{:.3f}", vmin=0, vmax=1,
           cmap=P.cmap("heat"), blank="0", text_thresh=0.62)
    ax.set_xticklabels(kk)
    ax.set_yticklabels(qk)
    ax.set_title("(c)  softmax weights  (rows sum to 1)",
                 color=P.INK, fontsize=15, pad=10)
    ax.text(0.5, -0.16, "e^(−∞) = 0  →  each token attends only to itself & the past",
            transform=ax.transAxes, ha="center", color=ACCENT, fontsize=12)

    f.subplots_adjust(left=0.05, right=0.985, top=0.84, bottom=0.14, wspace=0.32)
    return P.save(f, "causal-mask.png")


# ---------------------------------------------------------------------------
# Figure 2: encoder (bidirectional) vs decoder (causal)
# ---------------------------------------------------------------------------
def encoder_vs_decoder():
    toks = ["The", "cat", "sat", "on", "the", "mat"]
    n = len(toks)
    f, axes = P.fig(15.0, 7.4, wing=WING, ncols=2)
    P.suptitle(f, "One Mask Apart: encoder vs decoder attention",
               wing=WING)

    def draw(ax, allowed, title, sub, accent):
        grid = np.where(allowed, 1.0, 0.0)
        cmap = P.cmap("heat")
        cmap.set_bad(P.BG)
        ax.imshow(np.where(allowed, 0.78, np.nan), cmap=cmap,
                  vmin=0, vmax=1, aspect="equal")
        for i in range(n):
            for j in range(n):
                if allowed[i, j]:
                    ax.add_patch(plt.Circle((j, i), 0.18, color=P.BG, zorder=3))
                else:
                    ax.text(j, i, "×", ha="center", va="center",
                            color=P.GRID, fontsize=15)
        ax.set_xticks(range(n)); ax.set_yticks(range(n))
        ax.set_xticklabels(toks, fontsize=12.5)
        ax.set_yticklabels(toks, fontsize=12.5)
        ax.tick_params(length=0, colors=P.MUTED)
        ax.set_xticks(np.arange(-.5, n, 1), minor=True)
        ax.set_yticks(np.arange(-.5, n, 1), minor=True)
        ax.grid(which="minor", color=P.BG, linewidth=2.5)
        ax.grid(which="major", visible=False)
        ax.tick_params(which="minor", length=0)
        for sp in ax.spines.values():
            sp.set_color(P.GRID)
        ax.set_title(title, color=accent, fontsize=16, pad=12, fontweight="bold")
        ax.set_xlabel("key  (token attended to)", color=P.MUTED, fontsize=12)
        ax.set_ylabel("query  (token attending)", color=P.MUTED, fontsize=12)
        ax.text(0.5, -0.165, sub, transform=ax.transAxes, ha="center",
                color=P.INK, fontsize=12.5, style="italic")

    full = np.ones((n, n), dtype=bool)
    causal = np.tril(np.ones((n, n), dtype=bool))

    draw(axes[0], full, "ENCODER  —  bidirectional",
         "every token sees every token  (BERT)", ACCENT)
    draw(axes[1], causal, "DECODER  —  causal",
         "only the past & itself: lower triangle  (GPT, LLaMA, Claude)", WARM)

    f.subplots_adjust(left=0.07, right=0.97, top=0.86, bottom=0.15, wspace=0.30)
    return P.save(f, "encoder-vs-decoder.png")


if __name__ == "__main__":
    print(causal_mask())
    print(encoder_vs_decoder())
