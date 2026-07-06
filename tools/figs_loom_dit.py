"""Concept figure for The Patchwork Loom (DiT wing) — patchify.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_loom_dit.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch
import palace_fig as P

WING = "crimson"
ACC = P.WING[WING]["accent"]   # warm coral
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]    # dusky rose


def latent_field(n=32, seed=7):
    """A smooth pseudo-latent field just for texture."""
    rng = np.random.default_rng(seed)
    g = rng.standard_normal((n, n))
    # smooth it a little by averaging shifted copies
    for _ in range(3):
        g = (g + np.roll(g, 1, 0) + np.roll(g, -1, 0)
             + np.roll(g, 1, 1) + np.roll(g, -1, 1)) / 5.0
    g = (g - g.min()) / (g.max() - g.min())
    return g


def fig_patchify():
    N, p = 32, 2
    grid = N // p        # 16
    ntok = grid * grid   # 256
    field = latent_field(N)

    f = plt.figure(figsize=(16.5, 9.4))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 3, height_ratios=[1.32, 0.82],
                        width_ratios=[1.15, 0.95, 0.95],
                        hspace=0.42, wspace=0.30,
                        left=0.055, right=0.972, top=0.85, bottom=0.075)

    P.suptitle(f, "The Patchwork Loom  —  cut the latent grid into a thread of tokens")
    f.text(0.5, 0.905,
           "A transformer eats only a SEQUENCE. The loom cuts a 32×32×4 latent "
           "into 2×2 patches → (32/2)² = 256 tokens.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # --- (a) the latent grid with the 2×2 patch mesh -----------------------
    ax = f.add_subplot(gs[:, 0]); P.style_ax(ax, WING, grid=False)
    ax.imshow(field, cmap=P.cmap("fire"), extent=[0, N, N, 0],
              interpolation="bicubic", aspect="equal")
    # patch mesh every p cells
    for k in range(0, N + 1, p):
        ax.plot([k, k], [0, N], color=P.BG, lw=0.8, alpha=0.55)
        ax.plot([0, N], [k, k], color=P.BG, lw=0.8, alpha=0.55)
    # highlight three patches that will become tokens
    hi = [(0, 0), (0, 1), (0, 2)]
    hcolors = [ACC, WARM, COOL]
    for (r, c), col in zip(hi, hcolors):
        ax.add_patch(Rectangle((c * p, r * p), p, p, fill=False,
                               edgecolor=col, lw=3.2, zorder=5))
    ax.set_xlim(0, N); ax.set_ylim(N, 0)
    ax.set_xticks([0, 8, 16, 24, 32]); ax.set_yticks([0, 8, 16, 24, 32])
    ax.tick_params(colors=P.MUTED, labelsize=10)
    ax.set_title("(a)  latent 32×32×4, cut on a 2×2 mesh", color=P.INK, fontsize=13.5)
    ax.set_xlabel("16 patches across", color=P.MUTED, fontsize=11)
    ax.set_ylabel("16 patches down", color=P.MUTED, fontsize=11)
    ax.text(N / 2, -2.4, f"{grid} × {grid} = {ntok} patches",
            ha="center", color=ACC, fontsize=13.5, fontweight="bold")

    # --- (b) one patch → flatten 16 values → project to token --------------
    ax = f.add_subplot(gs[0, 1:]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off")
    ax.set_title("(b)  one patch → flatten (2·2·4 = 16 values) → linear project → 1 token",
                 color=P.INK, fontsize=13.5, loc="left")

    # a single 2×2 patch (4 cells, each with 4 channels implied)
    px0, py0 = 0.3, 1.7
    rng = np.random.default_rng(3)
    cells = rng.uniform(0.25, 0.9, (2, 2))
    for i in range(2):
        for j in range(2):
            ax.add_patch(Rectangle((px0 + j * 0.85, py0 + (1 - i) * 0.85),
                                    0.85, 0.85, facecolor=P.cmap("fire")(cells[i, j]),
                                    edgecolor=ACC, lw=2.0))
    ax.text(px0 + 0.85, py0 + 1.95, "2×2×4\npatch", ha="center", color=P.INK,
            fontsize=11.5, fontweight="bold")

    # flatten strand: 16 little cells
    fx0, fy0 = 3.35, 2.55
    for k in range(16):
        ax.add_patch(Rectangle((fx0 + k * 0.235, fy0), 0.22, 0.5,
                               facecolor=WARM if k % 4 < 2 else COOL,
                               edgecolor=P.GRID, lw=0.6, alpha=0.9))
    ax.text(fx0 + 16 * 0.235 / 2, fy0 + 0.85, "flatten → 16 numbers",
            ha="center", color=P.INK, fontsize=11)
    ax.annotate("", xy=(fx0 - 0.15, fy0 + 0.25), xytext=(px0 + 1.8, fy0 + 0.25),
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=2.0))

    # token vector out
    tx0, ty0 = 3.7, 0.55
    for k in range(9):
        ax.add_patch(Rectangle((tx0 + k * 0.30, ty0), 0.27, 0.55,
                               facecolor=ACC, edgecolor=P.GRID, lw=0.6, alpha=0.85))
    ax.text(tx0 + 9 * 0.30 + 0.55, ty0 + 0.28, "…", color=P.INK, fontsize=16, va="center")
    ax.text(tx0 + 9 * 0.30 / 2, ty0 - 0.42, "one token, dim = d_model",
            ha="center", color=ACC, fontsize=11.5, fontweight="bold")
    ax.annotate("", xy=(tx0 + 1.2, ty0 + 0.9), xytext=(fx0 + 1.4, fy0 - 0.1),
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=2.0))
    ax.text(6.55, 1.65, "shared learned\nW : 16 → d_model", color=WARM,
            fontsize=11, ha="left", fontweight="bold")

    # --- (c) the token ribbon: 256 threads ---------------------------------
    ax = f.add_subplot(gs[1, 1]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis("off")
    ax.set_title("(c)  256 tokens, in row-major order", color=P.INK,
                 fontsize=13, loc="left")
    shown = 11
    for k in range(shown):
        col = ACC if k == 0 else (WARM if k == 1 else (COOL if k == 2 else P.MUTED))
        ax.add_patch(FancyBboxPatch((0.25 + k * 0.83, 1.05), 0.62, 0.95,
                     boxstyle="round,pad=0.02,rounding_size=0.08",
                     facecolor=col, edgecolor=P.GRID, lw=0.8, alpha=0.9))
        ax.text(0.25 + k * 0.83 + 0.31, 1.52, f"{k+1}", ha="center", va="center",
                color=P.BG, fontsize=10, fontweight="bold")
    ax.text(0.25 + shown * 0.83 + 0.35, 1.52, "…  256", color=P.INK,
            fontsize=13, va="center", fontweight="bold")
    ax.text(0.25, 0.55, "patch (0,0)  (0,1)  (0,2)  →  the sequence the transformer reads",
            color=P.MUTED, fontsize=10.5)

    # --- (d) patch size trade-off -----------------------------------------
    ax = f.add_subplot(gs[1, 2]); P.style_ax(ax, WING)
    ps = [2, 4, 8]
    toks = [(N // pp) ** 2 for pp in ps]   # 256, 64, 16
    xb = np.arange(3)
    bars = ax.bar(xb, toks, 0.56, color=[ACC, WARM, COOL], edgecolor=P.GRID)
    for b, t in zip(bars, toks):
        ax.annotate(f"{t}", (b.get_x() + b.get_width() / 2, t),
                    xytext=(0, 4), textcoords="offset points", ha="center",
                    va="bottom", color=P.INK, fontsize=13, fontweight="bold")
    ax.set_yscale("log")
    ax.set_xticks(xb)
    ax.set_xticklabels(["p=2", "p=4", "p=8"], fontsize=12)
    ax.set_ylim(9, 500)
    ax.set_title("(d)  patch size trades detail ↔ length", color=P.INK, fontsize=13)
    ax.set_ylabel("# tokens  (log)", fontsize=11.5)
    ax.text(0.55, 200, "finer\nmore compute", color=ACC, fontsize=9.5, ha="center")
    ax.text(2.0, 190, "coarser\ncheaper", color=COOL, fontsize=9.5, ha="center")

    f.text(0.5, 0.028,
           "Smaller p → more tokens → finer detail but more attention compute; "
           "larger p → shorter sequence, coarser reconstruction. DiT-XL/2 uses p=2.",
           ha="center", color=P.INK, fontsize=12.5)

    return P.save(f, "dit-patchify.png")


if __name__ == "__main__":
    print("wrote", fig_patchify())
