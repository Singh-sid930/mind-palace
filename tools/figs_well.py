"""Concept figures for The Well of Chance (Wing of Arithmancy, violet).

Pure mathematics only: the Gaussian bell, and the sum of two independent
Gaussians. No machine-learning vocabulary.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_well.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "violet"
ACC = P.WING[WING]["accent"]   # soft violet
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]    # muted violet


def gauss(x, mu=0.0, sig=1.0):
    return np.exp(-0.5 * ((x - mu) / sig) ** 2) / (sig * np.sqrt(2 * np.pi))


def fig_bell_and_sum():
    f = plt.figure(figsize=(16.5, 8.2))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.05, 1.0],
                        wspace=0.20, left=0.055, right=0.975,
                        top=0.83, bottom=0.115)

    P.suptitle(f, "The Bell:  anatomy of N(0, 1)  and  the sum of two independent Gaussians")
    f.text(0.5, 0.90,
           "Every draw clusters around a center μ and spreads by a typical "
           "amount σ; add two independent bells and the spreads add in "
           "quadrature.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- panel (a): anatomy of the standard bell -------------------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    x = np.linspace(-4.2, 4.2, 800)
    y = gauss(x)
    ax.plot(x, y, color=ACC, lw=2.6, zorder=6)

    # nested sigma bands, palest outermost
    bands = [
        (3, "#2a2140", "99.7%"),
        (2, "#3a2f57", "95.4%"),
        (1, "#514279", "68.2%"),
    ]
    for k, col, pct in bands:
        m = np.abs(x) <= k
        ax.fill_between(x[m], 0, y[m], color=col, zorder=2 + (3 - k))

    # sigma boundary lines
    for k in (1, 2, 3):
        for s in (-1, 1):
            xv = s * k
            ax.plot([xv, xv], [0, gauss(xv)], color=P.MUTED, ls=":",
                    lw=1.1, zorder=5)
    ax.axvline(0, color=WARM, lw=1.8, ls="--", zorder=5)
    ax.text(0.0, gauss(0) + 0.010, "mean μ = 0", color=WARM, fontsize=12.5,
            ha="center", fontweight="bold")

    # percentage labels inside the bands
    ax.text(0.0, 0.150, "68.2%", ha="center", color=P.INK, fontsize=13,
            fontweight="bold", zorder=7)
    ax.annotate("95.4%", xy=(1.5, 0.052), color=P.INK, fontsize=11.5,
                ha="center", fontweight="bold", zorder=7)
    ax.annotate("99.7%", xy=(2.5, 0.017), color=P.INK, fontsize=10.5,
                ha="center", fontweight="bold", zorder=7)

    # sigma tick annotations
    ax.set_xticks([-3, -2, -1, 0, 1, 2, 3])
    ax.set_xticklabels(["−3σ", "−2σ", "−σ", "0", "+σ", "+2σ", "+3σ"],
                       fontsize=12)
    ax.set_ylim(0, 0.47)
    ax.set_xlim(-4.2, 4.2)
    ax.set_ylabel("probability density", fontsize=12.5)
    ax.set_title("(a)  one standard bell — where the draws land", color=P.INK)
    ax.annotate("σ = spread\n(std. deviation)", xy=(1, gauss(1)),
                xytext=(2.35, 0.30), color=COOL, fontsize=11.5, ha="center",
                arrowprops=dict(arrowstyle="-|>", color=COOL, lw=1.6))

    # ---- panel (b): sum of two independent Gaussians ---------------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    sA, sB = 0.6, 0.8
    sSum = np.sqrt(sA**2 + sB**2)   # = 1.0 exactly
    xx = np.linspace(-3.6, 3.6, 800)
    ax.fill_between(xx, 0, gauss(xx, 0, sA), color=WARM, alpha=0.22, zorder=2)
    ax.fill_between(xx, 0, gauss(xx, 0, sB), color=COOL, alpha=0.22, zorder=2)
    ax.plot(xx, gauss(xx, 0, sA), color=WARM, lw=2.4, zorder=5,
            label=f"A ~ N(0, 0.6²)   Var = {sA**2:.2f}")
    ax.plot(xx, gauss(xx, 0, sB), color=COOL, lw=2.4, zorder=5,
            label=f"B ~ N(0, 0.8²)   Var = {sB**2:.2f}")
    ax.plot(xx, gauss(xx, 0, sSum), color=ACC, lw=3.0, zorder=6,
            label=f"A + B ~ N(0, 1.0²)   Var = {sSum**2:.2f}")

    ax.set_ylim(0, 0.72)
    ax.set_xlim(-3.6, 3.6)
    ax.set_xlabel("value", fontsize=12.5)
    ax.set_ylabel("probability density", fontsize=12.5)
    ax.set_title("(b)  add two independent bells → one wider bell", color=P.INK)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11.5, loc="upper right")

    ax.text(-2.05, 0.545,
            "0.6²  +  0.8²  =  1.0²\nvariances add",
            ha="center", color=P.INK, fontsize=14, fontweight="bold",
            zorder=8,
            bbox=dict(boxstyle="round,pad=0.4", fc=P.PANEL, ec=ACC, lw=1.4))

    return P.save(f, "gaussian-anatomy.png")


if __name__ == "__main__":
    print("wrote", fig_bell_and_sum())
