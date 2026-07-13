"""Concept figure for The Singular Prism (Wing of Arithmancy, violet).

PURE mathematics: matrices as motions, singular values, low-rank approximation.
No downstream ML jargon.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_singular.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import palace_fig as P

WING = "violet"
ACC = P.WING[WING]["accent"]   # violet
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]    # muted violet


def bar_labels(ax, bars, fmt="{:.2f}", dy=0.0, color=P.INK, size=12):
    for b in bars:
        h = b.get_height()
        ax.annotate(fmt.format(h), (b.get_x() + b.get_width() / 2, h),
                    xytext=(0, 4 + dy), textcoords="offset points",
                    ha="center", va="bottom", color=color, fontsize=size,
                    fontweight="bold")


def fig_singular_prism():
    # --- the room's own matrix -------------------------------------------
    M = np.array([[2.0, 1.0], [1.0, 2.0]])
    U, S, Vt = np.linalg.svd(M)          # S = [3, 1]; U cols = [1,1]/√2, [1,-1]/√2
    s1, s2 = S

    # the room's own spectrum
    spec = np.array([8.2, 5.1, 3.7, 0.9, 0.3, 0.08])
    energy = spec ** 2
    total_e = energy.sum()
    cum_frac = np.cumsum(energy) / total_e            # energy captured keeping top-k
    # relative reconstruction error (Eckart-Young): sqrt(discarded energy / total)
    r_vals = np.arange(0, len(spec) + 1)
    rel_err = np.array([np.sqrt(max(total_e - energy[:r].sum(), 0) / total_e)
                        for r in r_vals])

    f = plt.figure(figsize=(17.4, 7.7))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 3, width_ratios=[1.05, 1.0, 1.0],
                        left=0.045, right=0.985, top=0.83, bottom=0.11,
                        wspace=0.28)

    P.suptitle(f, "The Singular Prism  —  rotate, stretch, rotate, "
                  "and the best few directions")
    f.text(0.5, 0.895,
           "M = U · Σ · V$^{\\mathrm{T}}$    every matrix is a motion: split it into "
           "three simpler motions, then keep only the directions that carry the weight.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # =====================================================================
    # (a) unit circle -> ellipse
    # =====================================================================
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    ax.set_aspect("equal")

    t = np.linspace(0, 2 * np.pi, 400)
    circ = np.vstack([np.cos(t), np.sin(t)])
    ell = M @ circ

    # unit circle (input)
    ax.plot(circ[0], circ[1], color=P.MUTED, lw=1.8, ls="--",
            label="unit circle (input)")
    # image ellipse (output)
    ax.plot(ell[0], ell[1], color=ACC, lw=2.6, label="image ellipse  M·(circle)")
    ax.fill(ell[0], ell[1], color=ACC, alpha=0.08)

    # principal directions: U columns scaled by singular values
    u1 = U[:, 0] * s1
    u2 = U[:, 1] * s2
    for vec, sig, name, col in [(u1, s1, "σ₁ = 3", WARM),
                                (u2, s2, "σ₂ = 1", COOL)]:
        ax.add_patch(FancyArrowPatch((0, 0), (vec[0], vec[1]),
                     arrowstyle="-|>", mutation_scale=22, color=col, lw=3.0,
                     zorder=5))
        lx, ly = vec * 1.14
        ax.text(lx, ly, name, color=col, fontsize=14, fontweight="bold",
                ha="center", va="center", zorder=6)

    # the semi-axis directions on the input circle (the V columns), thin ticks
    for vec, col in [(Vt[0], WARM), (Vt[1], COOL)]:
        ax.plot([0, vec[0]], [0, vec[1]], color=col, lw=1.2, ls=":", alpha=0.7)

    ax.axhline(0, color=P.GRID, lw=0.8)
    ax.axvline(0, color=P.GRID, lw=0.8)
    lim = 3.4
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    ax.set_title("(a)  a matrix carries a circle to an ellipse", color=P.INK)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=10.5, loc="lower right")
    ax.text(0.5, 0.965,
            "V$^{\\mathrm{T}}$ rotate  →  Σ stretch by σ  →  U rotate",
            transform=ax.transAxes, ha="center", va="top", color=WARM,
            fontsize=12.5, fontweight="bold")
    ax.text(0.5, -0.145,
            "M = [[2,1],[1,2]].  The stretch alone breaks roundness;\n"
            "the semi-axes σ₁=3, σ₂=1 along [1,1]/√2 and [1,−1]/√2 are the character of M.",
            transform=ax.transAxes, ha="center", va="top", color=P.MUTED,
            fontsize=10.3)

    # =====================================================================
    # (b) singular-value spectrum + cumulative energy
    # =====================================================================
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    x = np.arange(1, len(spec) + 1)
    bars = ax.bar(x, spec, 0.62, color=ACC, edgecolor=P.GRID, zorder=3)
    bar_labels(ax, bars, "{:.2f}", size=11.5)
    ax.set_xticks(x)
    ax.set_xticklabels(["σ%d" % k for k in x], fontsize=12)
    ax.set_ylim(0, 9.6)
    ax.set_ylabel("singular value  σ", fontsize=12.5)
    ax.set_title("(b)  the spectrum decays fast — an elbow", color=P.INK)

    # elbow marker after the 3rd value
    ax.axvline(3.5, color=WARM, ls="--", lw=1.6, alpha=0.9, zorder=2)
    ax.text(3.6, 8.7, "elbow", color=WARM, fontsize=12.5, fontweight="bold",
            ha="left", va="top")
    ax.annotate("substance\nabove", (2, 5.1), (1.4, 7.4), color=P.INK,
                fontsize=10.5, ha="center",
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.3))
    ax.annotate("a fading tail\nbelow", (5, 0.3), (5.1, 3.6), color=P.MUTED,
                fontsize=10.5, ha="center",
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.3))

    # cumulative energy on a twin axis
    ax2 = ax.twinx()
    ax2.plot(x, cum_frac * 100, color=WARM, lw=2.4, marker="o",
             markersize=6, zorder=4)
    ax2.set_ylim(0, 108)
    ax2.set_ylabel("cumulative energy captured (%)", color=WARM, fontsize=12)
    ax2.tick_params(colors=WARM, labelsize=10.5)
    for s in ax2.spines.values():
        s.set_color(P.GRID)
    ax2.annotate("top 3 σ hold 99.2%\nof the energy",
                 (3, cum_frac[2] * 100), (3.15, 55), color=WARM,
                 fontsize=11, fontweight="bold", ha="left",
                 arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.4))

    # =====================================================================
    # (c) rank-r truncation quality (Eckart-Young)
    # =====================================================================
    ax = f.add_subplot(gs[0, 2]); P.style_ax(ax, WING)
    ax.plot(r_vals, rel_err * 100, color=ACC, lw=2.6, marker="o",
            markersize=7, zorder=4)
    for r in [1, 2, 3]:
        ax.annotate("{:.1f}%".format(rel_err[r] * 100),
                    (r, rel_err[r] * 100), xytext=(0, 12),
                    textcoords="offset points", ha="center", color=P.INK,
                    fontsize=11.5, fontweight="bold")

    ax.axvline(3, color=WARM, ls="--", lw=1.6, alpha=0.9)
    ax.text(3.08, 82, "cut at the elbow:\nrank 3 → 9.2% error",
            color=WARM, fontsize=11.5, fontweight="bold", ha="left", va="top")

    # shade the "small r suffices" region
    ax.axvspan(3, len(spec), color=COOL, alpha=0.08)
    ax.text(4.5, 40, "flat: extra\ndirections\nbuy almost\nnothing",
            color=P.MUTED, fontsize=10.5, ha="center", va="center")

    ax.set_xticks(r_vals)
    ax.set_xlim(-0.15, len(spec) + 0.15)
    ax.set_ylim(-4, 108)
    ax.set_xlabel("rank r  (directions kept)", fontsize=12.5)
    ax.set_ylabel("reconstruction error  ‖M − M$_r$‖ / ‖M‖  (%)", fontsize=12)
    ax.set_title("(c)  best rank-r approximation (Eckart–Young)", color=P.INK)
    ax.text(0.5, -0.145,
            "Truncated SVD is provably the closest rank-r matrix; the error is\n"
            "set exactly by the discarded σ. Fast decay ⇒ a small r suffices.",
            transform=ax.transAxes, ha="center", va="top", color=P.MUTED,
            fontsize=10.3)

    return P.save(f, "svd-prism.png")


if __name__ == "__main__":
    p = fig_singular_prism()
    print("wrote", p)
