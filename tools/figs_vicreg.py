"""Concept figures for the Corridor of the Three Vows (VICReg).

VICReg, Variance-Invariance-Covariance Regularization
(Bardes, Ponce & LeCun, ICLR 2022).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_vicreg.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle
import palace_fig as P

rng = np.random.default_rng(7)
WARM = P.WING["emerald"]["warm"]
COOL = P.WING["emerald"]["cool"]
ACC = P.WING["emerald"]["accent"]


# ===========================================================================
# FIGURE 1, the three terms
# ===========================================================================
def fig_three_terms():
    f, axes = P.fig(15.0, 5.4, wing="emerald", ncols=3)
    a_inv, a_var, a_cov = axes
    P.suptitle(f, "VICReg, The Three Vows over a Batch of Embeddings")

    # ---- (1) Invariance ----------------------------------------------------
    a_inv.set_title("Invariance", color=ACC, pad=12)
    a_inv.set_xlim(0, 10)
    a_inv.set_ylim(0, 10)
    a_inv.set_xticks([])
    a_inv.set_yticks([])
    a_inv.grid(False)

    # two augmented views (small chips) and their embeddings converging
    pA = np.array([2.2, 7.6])
    pB = np.array([2.2, 2.4])
    zA = np.array([6.4, 6.0])
    zB = np.array([6.4, 4.0])
    target = np.array([8.4, 5.0])

    for (px, py, lbl) in [(pA[0], pA[1], "view 1"), (pB[0], pB[1], "view 2")]:
        a_inv.add_patch(FancyBboxPatch((px - 0.9, py - 0.9), 1.8, 1.8,
                        boxstyle="round,pad=0.05,rounding_size=0.25",
                        fc=P.PANEL, ec=COOL, lw=1.8))
        a_inv.text(px, py, lbl, ha="center", va="center",
                   color=P.INK, fontsize=11)

    # encoder arrows view -> embedding
    for p, z in [(pA, zA), (pB, zB)]:
        a_inv.add_patch(FancyArrowPatch((p[0] + 1.0, p[1]), (z[0] - 0.55, z[1]),
                        arrowstyle="-|>", mutation_scale=16,
                        color=P.MUTED, lw=1.6))
    a_inv.text(4.3, 8.4, "encoder\n+ expander", ha="center", va="center",
               color=P.MUTED, fontsize=9.5, style="italic")

    # embedding points
    a_inv.scatter(*zA, s=260, color=WARM, zorder=5, edgecolor=P.BG, lw=1.5)
    a_inv.scatter(*zB, s=260, color=WARM, zorder=5, edgecolor=P.BG, lw=1.5)
    a_inv.text(zA[0], zA[1] + 0.7, "z", ha="center", color=P.INK, fontsize=12)
    a_inv.text(zB[0], zB[1] - 0.9, "z'", ha="center", color=P.INK, fontsize=12)

    # convergence arrows pulling the pair together toward a midpoint
    a_inv.add_patch(FancyArrowPatch((zA[0] + 0.2, zA[1] - 0.4),
                    (target[0] - 0.3, target[1] + 0.35),
                    arrowstyle="-|>", mutation_scale=18, color=ACC, lw=2.4,
                    connectionstyle="arc3,rad=-0.25"))
    a_inv.add_patch(FancyArrowPatch((zB[0] + 0.2, zB[1] + 0.4),
                    (target[0] - 0.3, target[1] - 0.35),
                    arrowstyle="-|>", mutation_scale=18, color=ACC, lw=2.4,
                    connectionstyle="arc3,rad=0.25"))
    a_inv.scatter(*target, s=120, color=ACC, marker="*", zorder=6)
    a_inv.text(target[0] + 0.15, target[1], "pull\ntogether", ha="left",
               va="center", color=ACC, fontsize=10.5)

    a_inv.text(5.0, 0.9, r"$s(z,z') = \frac{1}{n}\sum \|z_i - z'_i\|_2^2$  (MSE)",
               ha="center", va="center", color=P.INK, fontsize=12.5)

    # ---- (2) Variance ------------------------------------------------------
    a_var.set_title("Variance", color=ACC, pad=12)
    d = 10
    std = np.array([1.42, 0.34, 1.15, 0.62, 1.30, 0.18, 0.95, 1.20, 0.48, 1.05])
    x = np.arange(d)
    below = std < 1.0
    colors = [WARM if b else COOL for b in below]
    a_var.bar(x, std, color=colors, edgecolor=P.BG, lw=0.8, width=0.74, zorder=3)

    a_var.axhline(1.0, color=ACC, lw=2.0, ls="--", zorder=4)
    a_var.text(d - 0.4, 1.06, "hinge target = 1.0", ha="right", va="bottom",
               color=ACC, fontsize=10.5)

    # arrows pushing the short bars up to the threshold
    for xi, s, b in zip(x, std, below):
        if b:
            a_var.add_patch(FancyArrowPatch((xi, s + 0.04), (xi, 0.97),
                            arrowstyle="-|>", mutation_scale=11,
                            color=WARM, lw=1.6, zorder=5))

    a_var.set_xticks(x)
    a_var.set_xticklabels([f"{i+1}" for i in range(d)], fontsize=9.5)
    a_var.set_xlabel("embedding dimension", fontsize=12)
    a_var.set_ylabel("std. deviation across batch", fontsize=12)
    a_var.set_ylim(0, 1.6)
    a_var.text(0.05, 1.50,
               r"penalty $= \max(0,\ 1 - \mathrm{std})$  per dim",
               ha="left", va="top", color=P.INK, fontsize=11.5,
               transform=a_var.transData)

    # ---- (3) Covariance ----------------------------------------------------
    a_cov.set_title("Covariance", color=ACC, pad=12)
    a_cov.set_xticks([])
    a_cov.set_yticks([])
    a_cov.grid(False)
    a_cov.set_facecolor(P.BG)
    for s in a_cov.spines.values():
        s.set_visible(False)

    # two correlation matrices: before (off-diagonal energy) -> after (clean)
    k = 6
    base = np.eye(k)
    off = rng.uniform(-0.65, 0.65, (k, k))
    off = (off + off.T) / 2
    np.fill_diagonal(off, 0)
    before = base + off
    after = base + off * 0.06  # off-diagonals driven toward 0

    cm = P.cmap("fire")
    ax_b = a_cov.inset_axes([0.01, 0.24, 0.35, 0.58])
    ax_a = a_cov.inset_axes([0.64, 0.24, 0.35, 0.58])
    for ax, M, ttl in [(ax_b, before, "before"), (ax_a, after, "after")]:
        ax.imshow(M, cmap=cm, vmin=-1, vmax=1, aspect="equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(ttl, color=P.INK, fontsize=12.5, pad=6)
        for sp in ax.spines.values():
            sp.set_color(P.GRID)

    # arrow between the two
    a_cov.add_patch(FancyArrowPatch((0.41, 0.50), (0.59, 0.50),
                    transform=a_cov.transAxes,
                    arrowstyle="-|>", mutation_scale=18, color=ACC, lw=2.4))
    a_cov.text(0.50, 0.60, "decorrelate", transform=a_cov.transAxes,
               ha="center", va="bottom", color=ACC, fontsize=10.5)

    a_cov.text(0.5, 0.08,
               "off-diagonals " + r"$\rightarrow 0$" + ";  diagonal kept by Variance",
               transform=a_cov.transAxes, ha="center", va="center",
               color=P.INK, fontsize=11.5)
    a_cov.text(0.5, 0.93, "embedding covariance matrix",
               transform=a_cov.transAxes, ha="center", va="center",
               color=P.MUTED, fontsize=10, style="italic")

    f.subplots_adjust(left=0.05, right=0.97, top=0.86, bottom=0.12, wspace=0.28)
    return P.save(f, "vicreg-three-terms.png")


# ===========================================================================
# FIGURE 2, the expander schematic
# ===========================================================================
def fig_expander():
    f, ax = P.fig(13.5, 6.4, wing="emerald")
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_facecolor(P.BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("The Expander  hϕ. A discardable buffer that takes the loss",
                 color=P.INK, fontsize=18, pad=14)

    def box(x, y, w, h, label, ec, sub=None, fc=P.PANEL, lw=2.0):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                     boxstyle="round,pad=0.04,rounding_size=0.18",
                     fc=fc, ec=ec, lw=lw, zorder=3))
        ax.text(x + w / 2, y + h / 2 + (0.35 if sub else 0), label,
                ha="center", va="center", color=P.INK, fontsize=13.5,
                fontweight="bold", zorder=4)
        if sub:
            ax.text(x + w / 2, y + h / 2 - 0.45, sub, ha="center", va="center",
                    color=P.MUTED, fontsize=10.5, zorder=4)

    yc = 5.0
    # image -> encoder -> representation -> expander -> embedding -> loss
    box(0.4, yc - 0.9, 2.0, 1.8, "image\nview", COOL)
    box(3.1, yc - 0.9, 2.2, 1.8, "Encoder", WARM, sub=r"$f_\theta$")
    box(6.0, yc - 0.9, 2.3, 1.8, "Expander", ACC, sub=r"$h_\phi$",
        fc="#14241c")
    box(9.0, yc - 0.9, 2.0, 1.8, "Loss", WARM,
        sub="Inv + Var + Cov")

    # arrows w/ dimension annotations
    def arrow(x0, x1, y, txt=None, col=P.MUTED):
        ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>",
                     mutation_scale=18, color=col, lw=2.0, zorder=2))
        if txt:
            ax.text((x0 + x1) / 2, y + 0.45, txt, ha="center", va="bottom",
                    color=P.INK, fontsize=11)

    arrow(2.4, 3.1, yc)
    arrow(5.3, 6.0, yc, r"$y \in \mathbb{R}^{d}$  (kept rich)", col=WARM)
    arrow(8.3, 9.0, yc, r"$z \in \mathbb{R}^{D},\ D \gg d$", col=ACC)

    # "kept" vs "discarded" banners
    ax.add_patch(FancyBboxPatch((3.0, 2.2), 2.4, 0.7,
                 boxstyle="round,pad=0.04,rounding_size=0.15",
                 fc="#14241c", ec=WARM, lw=1.4, zorder=3))
    ax.text(4.2, 2.55, "KEPT after training", ha="center", va="center",
            color=WARM, fontsize=10.5, fontweight="bold")
    ax.add_patch(FancyArrowPatch((4.2, 4.1), (4.2, 2.95), arrowstyle="-",
                 color=WARM, lw=1.3, ls=":", zorder=2))

    ax.add_patch(FancyBboxPatch((5.9, 2.2), 2.5, 0.7,
                 boxstyle="round,pad=0.04,rounding_size=0.15",
                 fc=P.PANEL, ec=P.MUTED, lw=1.4, ls="--", zorder=3))
    ax.text(7.15, 2.55, "DISCARDED", ha="center", va="center",
            color=P.MUTED, fontsize=10.5, fontweight="bold")
    ax.add_patch(FancyArrowPatch((7.15, 4.1), (7.15, 2.95), arrowstyle="-",
                 color=P.MUTED, lw=1.3, ls=":", zorder=2))

    # explanatory note panel on the right
    note = (
        "Why expand, then throw it away?\n\n"
        "1.  The expander absorbs the invariance\n"
        "     pressure, so the encoder's output $y$\n"
        "     stays rich. It need not forget what\n"
        "     differs between two views of an image.\n\n"
        "2.  Raising the dimension turns nonlinear\n"
        "     correlations into linear ones, which the\n"
        "     covariance term can then remove.\n\n"
        "After training, $h_\\phi$ is dropped; only the\n"
        "encoder $f_\\theta$ walks onward."
    )
    ax.add_patch(FancyBboxPatch((11.25, 0.5), 2.55, 7.0,
                 boxstyle="round,pad=0.06,rounding_size=0.2",
                 fc=P.PANEL, ec=P.GRID, lw=1.4, zorder=1))
    ax.text(11.45, 7.1, note, ha="left", va="top", color=P.INK,
            fontsize=10.6, linespacing=1.45, zorder=4)

    f.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.04)
    return P.save(f, "vicreg-expander.png")


if __name__ == "__main__":
    print(fig_three_terms())
    print(fig_expander())
