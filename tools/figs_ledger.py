"""Concept figures for The Ledger of Variance (Wing of Arithmancy, violet).

Pure mathematics only: the variance-preserving mixture y = √(1−β)·x + √β·ε,
whose total variance stays pinned at 1 for every mixing fraction β.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_ledger.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "violet"
ACC = P.WING[WING]["accent"]
WARM = P.WING[WING]["warm"]    # gold  -> signal x
COOL = P.WING[WING]["cool"]    # violet -> noise ε


def fig_variance_budget():
    f = plt.figure(figsize=(16.5, 8.4))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.15, 1.0],
                        wspace=0.19, left=0.06, right=0.975,
                        top=0.82, bottom=0.135)

    P.suptitle(f, "The Variance-Preserving Mixture:   y = √(1−β)·x + √β·ε")
    f.text(0.5, 0.895,
           "x and ε each have variance 1. The squared weights (1−β) and β "
           "are the whole budget, they always sum to 1.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- panel (a): stacked variance budget across a sweep of β ----------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    betas = np.linspace(0, 1, 21)
    sig = 1 - betas    # signal contribution = (√(1−β))² · Var(x)
    noi = betas        # noise  contribution = (√β)²    · Var(ε)
    w = (betas[1] - betas[0]) * 0.9
    ax.bar(betas, sig, width=w, color=WARM, edgecolor=P.BG, lw=0.4,
           label="signal share  (1−β)·Var(x)")
    ax.bar(betas, noi, width=w, bottom=sig, color=COOL, edgecolor=P.BG,
           lw=0.4, label="noise share  β·Var(ε)")
    ax.axhline(1.0, color=ACC, ls="--", lw=2.0, zorder=6)
    ax.text(0.5, 1.035, "total variance = 1  (always)", color=ACC,
            fontsize=13, ha="center", fontweight="bold")
    ax.set_ylim(0, 1.16)
    ax.set_xlim(-0.03, 1.03)
    ax.set_xlabel("mixing knob  β   (0 = all signal → 1 = all noise)",
                  fontsize=12.5)
    ax.set_ylabel("variance budget", fontsize=12.5)
    ax.set_title("(a)  the two shares trade off, the total never drifts",
                 color=P.INK)
    ax.grid(True, axis="y", color=P.GRID, lw=0.6, alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11.5, loc="center", bbox_to_anchor=(0.5, 0.5))

    # ---- panel (b): scatter clouds at a few β, identical spread ----------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING, grid=False)
    rng = np.random.default_rng(7)
    N = 900
    x = rng.standard_normal((N, 2))     # signal cloud,  Var = 1
    e = rng.standard_normal((N, 2))     # noise cloud,   Var = 1
    show = [0.0, 0.25, 0.5, 0.75, 1.0]
    gap = 3.4
    for i, b in enumerate(show):
        cx = i * gap
        y = np.sqrt(1 - b) * x + np.sqrt(b) * e
        # colour blends gold->violet with β
        col = tuple(np.array(_hex(WARM)) * (1 - b) + np.array(_hex(COOL)) * b)
        ax.scatter(y[:, 0] + cx, y[:, 1], s=6, color=col, alpha=0.55,
                   edgecolors="none", zorder=4)
        std = y.std()
        # a circle of radius = measured std to make "same spread" visible
        th = np.linspace(0, 2 * np.pi, 100)
        ax.plot(cx + std * np.cos(th), std * np.sin(th), color=ACC, lw=1.8,
                zorder=6)
        ax.text(cx, 3.65, f"β = {b:.2f}", ha="center", color=P.INK,
                fontsize=12, fontweight="bold")
        ax.text(cx, -3.75, f"std ≈ {std:.2f}", ha="center", color=ACC,
                fontsize=11.5)
    ax.set_xlim(-2.2, (len(show) - 1) * gap + 2.2)
    ax.set_ylim(-4.5, 4.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("(b)  same spread at every mix (rings = measured std ≈ 1)",
                 color=P.INK)

    return P.save(f, "variance-preserving-mixture.png")


def _hex(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


if __name__ == "__main__":
    print("wrote", fig_variance_budget())
