"""Concept figure for The Flat Window (Wing of Continuous Motion, bronze).

PURE geometry only: a curve, a straight tangent line, the gap between a flat
step and the true curve, and the tangent-at-the-identity as a flat vector
space isomorphic to Rn. No machines, no estimation, no jargon.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_tangent.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import palace_fig as P

WING = "bronze"
ACC = P.WING[WING]["accent"]   # warm brass
WARM = P.WING[WING]["warm"]    # burnt orange
COOL = P.WING[WING]["cool"]    # sage


def fig_tangent():
    f = plt.figure(figsize=(16.5, 9.0))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 2, width_ratios=[1.08, 1.0],
                        height_ratios=[1.0, 0.82],
                        hspace=0.42, wspace=0.20,
                        left=0.055, right=0.965, top=0.86, bottom=0.085)

    P.suptitle(f, "The Flat Window, a straight tangent stands in for the "
                  "curve, and at the identity it is the Lie algebra")

    # =====================================================================
    # (a)  circle + straight tangent line; the gap near vs far
    # =====================================================================
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color=ACC, lw=2.4, label="the true curve")

    # touch at the top; tangent is the horizontal line y = 1
    ax.plot([-0.1, 1.55], [1, 1], color=WARM, lw=2.2, ls="-",
            label="the flat tangent")
    ax.scatter([0], [1], color=P.INK, s=70, zorder=6,
               edgecolor=WARM, linewidth=1.4)
    ax.text(0, 1.12, "touch point", color=P.INK, fontsize=12,
            ha="center", fontweight="bold")

    # straight steps along the tangent vs the matching arc-length point
    for d in [0.35, 0.7, 1.05, 1.4]:
        tp = np.array([d, 1.0])                       # step along flat tangent
        cp = np.array([np.sin(d), np.cos(d)])         # same arc length on curve
        ax.plot([tp[0], cp[0]], [tp[1], cp[1]], color=P.MUTED, ls="--",
                lw=1.3, alpha=0.9)
        ax.scatter(*tp, color=WARM, s=34, zorder=5)
        ax.scatter(*cp, color=ACC, s=34, zorder=5)
    ax.annotate("near the touch:\nnearly identical", xy=(0.34, 0.96),
                xytext=(-0.98, 0.5), color=P.INK, fontsize=11.5,
                ha="center",
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.4))
    ax.annotate("far away:\nthe gap grows", xy=(1.3, 0.6),
                xytext=(1.18, -0.32), color=WARM, fontsize=11.5, ha="center",
                fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.4))

    ax.set_xlim(-1.3, 1.75); ax.set_ylim(-1.3, 1.4)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(a)  A straight step is a good LOCAL stand-in for the curve",
                 color=P.INK, fontsize=14)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11, loc="lower left")

    # =====================================================================
    # (a, lower)  the gap grows with distance from the touch point
    # =====================================================================
    axg = f.add_subplot(gs[1, 0]); P.style_ax(axg, WING)
    d = np.linspace(0, 1.5, 200)
    gap = np.sqrt((d - np.sin(d)) ** 2 + (1 - np.cos(d)) ** 2)
    axg.plot(d, gap, color=WARM, lw=2.6)
    axg.fill_between(d, 0, gap, color=WARM, alpha=0.12)
    axg.axvspan(0, 0.4, color=COOL, alpha=0.16)
    axg.text(0.2, axg.get_ylim()[1] * 0.82, "near:\ngap ≈ 0", color=COOL,
             fontsize=11, ha="center")
    axg.set_xlim(0, 1.5)
    axg.set_xlabel("distance walked from the touch point", fontsize=12)
    axg.set_ylabel("gap: flat step vs curve", fontsize=12)
    axg.set_title("The gap starts at zero and grows with distance",
                  color=P.INK, fontsize=13)

    # =====================================================================
    # (b, upper)  tangent at the identity = the Lie algebra, isomorphic R^1
    # =====================================================================
    axb = f.add_subplot(gs[0, 1]); P.style_ax(axb, WING, grid=False)
    axb.plot(np.cos(th), np.sin(th), color=ACC, lw=2.4)
    # identity = the do-nothing turn, at angle 0 -> point (1,0); tangent vertical
    axb.plot([1, 1], [-1.35, 1.35], color=WARM, lw=2.2)
    for t in [-1, -0.5, 0.5, 1]:
        axb.plot([0.94, 1.06], [t, t], color=WARM, lw=1.6)
        axb.text(1.13, t, f"{t:g}", color=P.MUTED, fontsize=10, va="center")
    axb.scatter([1], [0], color=P.INK, s=80, zorder=6,
                edgecolor=WARM, linewidth=1.5)
    axb.text(0.92, 0.16, "identity\n(do-nothing turn)", color=P.INK,
             fontsize=11.5, ha="right", fontweight="bold")
    axb.annotate("the tangent line here\n= the Lie algebra  $\\cong\\ \\mathbb{R}^{1}$",
                 xy=(1.0, -0.7), xytext=(-0.35, -1.02), color=ACC,
                 fontsize=12.5, ha="center", fontweight="bold",
                 arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.6))
    axb.set_xlim(-1.5, 1.7); axb.set_ylim(-1.5, 1.5)
    axb.set_aspect("equal")
    axb.set_xticks([]); axb.set_yticks([])
    axb.set_title("(b)  A circle's tangent at the identity is a flat "
                  "$\\mathbb{R}^{1}$  (1 dof)", color=P.INK, fontsize=14)

    # =====================================================================
    # (b, lower)  the surface of 3D turns has a 3-dimensional tangent, R^3
    # =====================================================================
    axr = f.add_subplot(gs[1, 1]); axr.set_facecolor(P.BG)
    axr.set_xlim(-1.6, 1.9); axr.set_ylim(-1.25, 1.25)
    axr.set_aspect("equal")
    axr.set_xticks([]); axr.set_yticks([])
    for sp in axr.spines.values():
        sp.set_color(P.GRID)
    axr.set_title("The surface of 3D turns has a 3-dimensional flat tangent  "
                  "$\\cong\\ \\mathbb{R}^{3}$", color=P.INK, fontsize=13, pad=8)
    # a small orthonormal frame drawn in a light isometric projection
    O = np.array([-0.15, 0.05])
    axes3 = {"e₁": np.array([1.05, 0.0]),
             "e₂": np.array([0.0, 0.95]),
             "e₃": np.array([-0.66, -0.48])}
    for name, vec in axes3.items():
        axr.add_patch(FancyArrowPatch(O, O + vec, arrowstyle="-|>",
                                      mutation_scale=18, color=ACC, lw=2.4))
        tip = O + vec * 1.14
        axr.text(tip[0], tip[1], name, color=P.INK, fontsize=13,
                 ha="center", va="center", fontweight="bold")
    axr.text(1.42, 0.62, "three independent\ndirections you may\nfreely combine",
             color=P.MUTED, fontsize=11, ha="center", va="center")
    axr.text(0.15, -1.08, "n = degrees of freedom  →  tangent at identity "
             "$\\cong\\,\\mathbb{R}^{n}$", color=WARM, fontsize=11.5,
             ha="center", fontweight="bold")

    return P.save(f, "lie-tangent.png")


if __name__ == "__main__":
    print("wrote", fig_tangent())
