"""Concept figure for 'The Two Maps' (Wing of Continuous Motion, bronze).

The exponential and logarithm maps as pure geometry: a straight step in the
flat tangent line becomes a geodesic arc of equal length on the circle, and
the logarithm unwraps it back. Worked concretely on SO(2) — the unit circle.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_explog.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc
import palace_fig as P

WING = "bronze"
ACC = P.WING[WING]["accent"]   # brass gold
WARM = P.WING[WING]["warm"]    # burnt orange
COOL = P.WING[WING]["cool"]    # olive


def circle(ax, r=1.0, **kw):
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(r * np.cos(t), r * np.sin(t), **kw)


def fig_exp_log():
    theta = 1.0                       # the worked tangent value / arc length
    p = np.array([1.0, 0.0])
    q = np.array([np.cos(theta), np.sin(theta)])

    f, axes = P.fig(13.6, 7.2, wing=WING, ncols=2)
    f.subplots_adjust(left=0.045, right=0.975, top=0.80, bottom=0.16, wspace=0.16)
    P.suptitle(f, "The Two Maps  —  a straight step, wrapped onto the curve and unwrapped back")
    f.text(0.5, 0.885,
           "On the unit circle (SO(2)): the tangent value θ maps to the point "
           "at angle θ.  A flat step of length θ travels an arc of length θ.",
           ha="center", color=P.MUTED, fontsize=13)

    # ------------------------------------------------------------------ (a)
    ax = axes[0]
    ax.grid(False)
    ax.set_aspect("equal")
    circle(ax, 1.0, color=P.GRID, lw=1.4)
    # faint radius to q, marking the angle theta at the centre
    ax.plot([0, q[0]], [0, q[1]], color=P.MUTED, lw=1.0, ls=":")
    ax.plot([0, 1], [0, 0], color=P.MUTED, lw=1.0, ls=":")
    arc_ang = Arc((0, 0), 0.5, 0.5, angle=0, theta1=0,
                  theta2=np.degrees(theta), color=P.MUTED, lw=1.2)
    ax.add_patch(arc_ang)
    ax.text(0.32, 0.14, "θ = 1.0 rad", color=P.MUTED, fontsize=12,
            ha="left", va="center")

    # tangent line at p (vertical, since p is the rightmost point)
    ax.plot([1, 1], [-0.35, 1.45], color=COOL, lw=1.3, ls="--", alpha=0.9)
    ax.text(1.05, 1.45, "flat tangent line at p", color=COOL, fontsize=11.5,
            ha="left", va="bottom")

    # the straight tangent step: vertical arrow of length theta
    ax.add_patch(FancyArrowPatch((1, 0), (1, theta), arrowstyle="-|>",
                                 mutation_scale=20, color=WARM, lw=3.0))
    ax.text(1.10, theta / 2 - 0.05, "straight step\nof length s = θ",
            color=WARM, fontsize=12.5, ha="left", va="center",
            fontweight="bold")

    # the geodesic arc of the SAME length, wrapped onto the circle (exp image)
    arc_geo = Arc((0, 0), 2, 2, angle=0, theta1=0, theta2=np.degrees(theta),
                  color=ACC, lw=4.0)
    ax.add_patch(arc_geo)
    ax.text(-0.02, 1.18, "geodesic arc\nof length s = θ", color=ACC,
            fontsize=12.5, ha="left", va="bottom", fontweight="bold")

    # points
    ax.plot(*p, "o", color=P.INK, ms=9, zorder=5)
    ax.text(p[0] + 0.05, p[1] - 0.12, "p", color=P.INK, fontsize=15,
            fontweight="bold")
    ax.plot(*q, "o", color=ACC, ms=9, zorder=5)
    ax.text(q[0] - 0.14, q[1] - 0.18, "q = exp(θ)", color=ACC, fontsize=12.5,
            fontweight="bold", ha="right")

    # exp arrow: from the tangent tip curving onto q
    ax.add_patch(FancyArrowPatch((1.0, theta), tuple(q + [0.02, 0.03]),
                                 arrowstyle="-|>", mutation_scale=18,
                                 color=P.INK, lw=1.6,
                                 connectionstyle="arc3,rad=0.28"))
    ax.text(0.86, 1.05, "exp", color=P.INK, fontsize=13, fontweight="bold",
            ha="center")

    ax.set_xlim(-1.35, 2.15)
    ax.set_ylim(-1.3, 1.7)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(a)  exp preserves length, trades straightness", color=P.INK,
                 fontsize=14)

    # ------------------------------------------------------------------ (b)
    ax = axes[1]
    ax.grid(False)
    ax.set_aspect("equal")
    circle(ax, 1.0, color=P.GRID, lw=1.4)

    # tangent step out
    ax.plot([1, 1], [-0.2, 1.25], color=COOL, lw=1.2, ls="--", alpha=0.8)
    ax.add_patch(FancyArrowPatch((1, 0), (1, theta), arrowstyle="-|>",
                                 mutation_scale=18, color=WARM, lw=2.6))
    ax.text(1.08, theta / 2, "v = 1.0 rad", color=WARM, fontsize=12.5,
            ha="left", va="center", fontweight="bold")

    arc_geo = Arc((0, 0), 2, 2, angle=0, theta1=0, theta2=np.degrees(theta),
                  color=ACC, lw=3.4)
    ax.add_patch(arc_geo)

    ax.plot(*p, "o", color=P.INK, ms=8, zorder=5)
    ax.text(p[0] + 0.05, p[1] - 0.13, "p", color=P.INK, fontsize=14,
            fontweight="bold")
    ax.plot(*q, "o", color=ACC, ms=9, zorder=5)
    ax.text(q[0] - 0.06, q[1] + 0.10,
            "q = (cos 1, sin 1)\n   ≈ (0.540, 0.841)", color=ACC,
            fontsize=11.5, fontweight="bold", ha="right", va="bottom")

    # exp (out) and log (back) curved arrows
    ax.add_patch(FancyArrowPatch((1.0, theta), tuple(q + [0.02, 0.02]),
                                 arrowstyle="-|>", mutation_scale=17,
                                 color=COOL, lw=2.2,
                                 connectionstyle="arc3,rad=0.32"))
    ax.text(1.02, 1.18, "exp →", color=COOL, fontsize=13,
            fontweight="bold", ha="left")
    ax.add_patch(FancyArrowPatch(tuple(q - [0.02, 0.0]), (1.0, theta - 0.03),
                                 arrowstyle="-|>", mutation_scale=17,
                                 color=WARM, lw=2.2,
                                 connectionstyle="arc3,rad=0.32"))
    ax.text(0.24, 0.63, "← log", color=WARM, fontsize=13,
            fontweight="bold", ha="left")

    ax.set_xlim(-1.25, 1.7)
    ax.set_ylim(-1.25, 1.6)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(b)  the round trip: v → q → v", color=P.INK, fontsize=14)

    f.text(0.5, 0.045,
           "v = 1.0 rad  —exp→  q on the circle  —log→  v = 1.0 rad.   "
           "log is exp run backwards: out to the flat, and exactly back again.",
           ha="center", color=P.INK, fontsize=12.5)

    return P.save(f, "lie-exp-log.png")


if __name__ == "__main__":
    print("wrote", fig_exp_log())
