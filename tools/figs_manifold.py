"""Concept figure for The Curved Ground (Wing of Continuous Motion, bronze).

PURE geometry only: curved surfaces, tangent patches, turns as points on a
surface, and the counting of degrees of freedom. No machines, no bearings.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_manifold.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import palace_fig as P

WING = "bronze"
ACC = P.WING[WING]["accent"]   # warm brass
WARM = P.WING[WING]["warm"]    # burnt orange
COOL = P.WING[WING]["cool"]    # sage


def fig_manifold():
    f = plt.figure(figsize=(16.5, 9.0))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 2, width_ratios=[1.05, 1.0],
                        height_ratios=[1.0, 1.0],
                        hspace=0.30, wspace=0.16,
                        left=0.02, right=0.975, top=0.865, bottom=0.06)

    P.suptitle(f, "The Curved Ground  —  globally curved, locally flat; "
                  "the turns as a surface")

    # =====================================================================
    # (a)  a sphere with a flat tangent patch, and a magnifier
    # =====================================================================
    ax = f.add_subplot(gs[:, 0], projection="3d")
    ax.set_facecolor(P.BG)

    # the curved ground: a globe drawn as a soft wireframe
    u = np.linspace(0, 2 * np.pi, 48)
    v = np.linspace(0, np.pi, 30)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(xs, ys, zs, rstride=2, cstride=2, color="#1b2735",
                    edgecolor=P.GRID, linewidth=0.35, alpha=0.85, shade=True)

    # touch point (you are here) chosen to FACE the camera, so its tangent
    # patch reads as a flat square rather than an edge-on sliver
    n = np.array([0.40, -0.74, 0.54]); n /= np.linalg.norm(n)
    p = n                                        # point lies on the unit globe
    # two orthonormal tangent directions at p
    t1 = np.cross(n, [0, 0, 1]); t1 /= np.linalg.norm(t1)
    t2 = np.cross(n, t1); t2 /= np.linalg.norm(t2)

    s = 0.34                                       # half-size of the flat patch
    corners = [p + a * s * t1 + b * s * t2
               for a, b in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
    patch = Poly3DCollection([corners], facecolor=ACC, edgecolor=P.INK,
                             alpha=0.45, linewidth=1.6)
    ax.add_collection3d(patch)
    # a small grid on the flat patch to signal "ordinary plane"
    for t in np.linspace(-1, 1, 5):
        a0 = p + t * s * t1 - s * t2
        a1 = p + t * s * t1 + s * t2
        ax.plot(*zip(a0, a1), color=P.INK, lw=0.5, alpha=0.5)
        b0 = p - s * t1 + t * s * t2
        b1 = p + s * t1 + t * s * t2
        ax.plot(*zip(b0, b1), color=P.INK, lw=0.5, alpha=0.5)

    ax.scatter(*p, color=WARM, s=70, depthshade=False, zorder=6,
               edgecolor=P.INK, linewidth=1.0)
    ax.text(p[0] - 0.05, p[1] - 0.05, p[2] + 0.78,
            "you are here:\na small flat tangent patch",
            color=WARM, fontsize=12.5, fontweight="bold", ha="center")

    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=18, azim=-58)
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    ax.set_axis_off()
    ax.set_title("(a)  Globally curved, locally flat",
                 color=P.INK, fontsize=15, pad=-2)

    # magnifier inset: the patch, up close, is an ordinary flat plane
    axm = f.add_axes([0.055, 0.085, 0.175, 0.235])
    axm.set_facecolor(P.PANEL)
    for g in np.linspace(0, 1, 6):
        axm.axhline(g, color=P.GRID, lw=0.8)
        axm.axvline(g, color=P.GRID, lw=0.8)
    axm.plot([0, 1], [0, 1], color=COOL, lw=1.6)       # a straight walk
    axm.scatter([0.5], [0.5], color=WARM, s=55, zorder=5,
                edgecolor=P.INK, linewidth=0.8)
    axm.set_xlim(0, 1); axm.set_ylim(0, 1)
    axm.set_xticks([]); axm.set_yticks([])
    for sp in axm.spines.values():
        sp.set_color(ACC); sp.set_linewidth(1.6)
    axm.set_title("up close: an ordinary flat plane", color=P.INK,
                  fontsize=11.5, pad=4)
    # connective "magnify" arrow from the inset up toward the patch
    f.add_artist(FancyArrowPatch((0.235, 0.31), (0.315, 0.46),
                                 transform=f.transFigure, arrowstyle="-|>",
                                 mutation_scale=18, color=ACC, lw=2.0,
                                 connectionstyle="arc3,rad=-0.25"))
    f.text(0.20, 0.375, "magnify", color=ACC, fontsize=11.5,
           fontweight="bold", ha="right")
    f.text(0.28, 0.075,
           "the whole surface curves and closes;\nonly far-apart patches disagree",
           color=P.MUTED, fontsize=11, ha="center", va="center")

    # =====================================================================
    # (b top)  2D turns = a circle, one degree of freedom
    # =====================================================================
    axc = f.add_subplot(gs[0, 1]); P.style_ax(axc, WING, grid=False)
    th = np.linspace(0, 2 * np.pi, 400)
    axc.plot(np.cos(th), np.sin(th), color=ACC, lw=2.4)
    marks = [0, 45, 90, 135, 180, 270]
    for d in marks:
        a = np.deg2rad(d)
        x, y = np.cos(a), np.sin(a)
        axc.plot([0, x], [0, y], color=P.GRID, lw=0.9, ls=":")
        axc.scatter([x], [y], color=WARM, s=48, zorder=5,
                    edgecolor=P.INK, linewidth=0.7)
        axc.text(1.16 * x, 1.16 * y, f"{d}°", color=P.INK, fontsize=11.5,
                 ha="center", va="center")
    # a small arc arrow showing the sweep of the angle
    arc = FancyArrowPatch(posA=(0.34, 0.0), posB=(0.24, 0.24),
                          connectionstyle="arc3,rad=0.5",
                          arrowstyle="-|>", mutation_scale=16,
                          color=WARM, lw=2.0)
    axc.add_patch(arc)
    axc.text(0.40, 0.14, "θ", color=WARM, fontsize=15, fontweight="bold")
    axc.set_xlim(-1.5, 1.5); axc.set_ylim(-1.62, 1.35)
    axc.set_aspect("equal")
    axc.set_xticks([]); axc.set_yticks([])
    axc.set_title("(b)  2D turns form a circle  —  1 degree of freedom",
                  color=P.INK, fontsize=14)
    axc.text(0, -1.52, "one number θ, and it wraps: sweep a full turn and "
             "you return to the start", color=P.MUTED, fontsize=11,
             ha="center")

    # =====================================================================
    # (b bottom)  3D turns: 9 numbers written, only 3 free
    # =====================================================================
    axg = f.add_subplot(gs[1, 1]); axg.set_facecolor(P.BG)
    axg.set_xlim(0, 10); axg.set_ylim(0, 10)
    axg.set_xticks([]); axg.set_yticks([])
    for sp in axg.spines.values():
        sp.set_color(P.GRID)
    axg.set_title("A 3×3 turn: 9 numbers written, only 3 truly free",
                  color=P.INK, fontsize=14, pad=8)

    # --- left: the 3x3 grid of "written numbers" + its constraints ---------
    gx, gy, cell = 0.55, 4.35, 1.05
    for i in range(3):
        for j in range(3):
            axg.add_patch(Rectangle((gx + j * cell, gy + (2 - i) * cell),
                                    cell, cell, facecolor=PANEL_FILL(i, j),
                                    edgecolor=P.INK, linewidth=1.2))
    axg.text(gx + 1.5 * cell, gy + 3 * cell + 0.32,
             "9 written numbers", color=WARM, fontsize=12.5,
             fontweight="bold", ha="center")
    axg.text(gx + 1.5 * cell, gy - 0.55,
             "columns must stay unit-length\nand mutually square  →  6 constraints",
             color=P.MUTED, fontsize=10.5, ha="center", va="top")
    axg.text(gx + 1.5 * cell, 1.15,
             "9 − 6 = 3 free", color=ACC, fontsize=15,
             fontweight="bold", ha="center")

    # --- right: loose 9-D space holding the thin 3-D surface of valid turns -
    bx0, bx1, by0, by1 = 5.35, 9.7, 2.5, 8.5
    box = FancyBboxPatch((bx0, by0), bx1 - bx0, by1 - by0,
                         boxstyle="round,pad=0.06,rounding_size=0.25",
                         facecolor="#161f2b", edgecolor=P.GRID, linewidth=1.3)
    axg.add_patch(box)
    axg.text((bx0 + bx1) / 2, by1 - 0.55, "the loose space of all 9-number grids",
             color=P.MUTED, fontsize=10.5, ha="center", va="center")
    # a thin curved ribbon = the surface of valid turns
    xx = np.linspace(bx0 + 0.5, bx1 - 0.5, 200)
    yy = 4.35 + 0.75 * np.sin((xx - bx0) * 1.5)
    axg.plot(xx, yy, color=ACC, lw=3.4, solid_capstyle="round")
    px = bx0 + 1.15
    py = 4.35 + 0.75 * np.sin((px - bx0) * 1.5)
    axg.scatter([px], [py], color=WARM, s=60, zorder=6,
                edgecolor=P.INK, linewidth=0.8)
    axg.text((bx0 + bx1) / 2, 3.05, "valid turns: a 3-D surface",
             color=ACC, fontsize=11.5, ha="center", fontweight="bold")
    # nudge-off arrow, pointing up into the empty loose space
    axg.add_patch(FancyArrowPatch((px, py), (px + 0.55, py + 1.7),
                                  arrowstyle="-|>", mutation_scale=16,
                                  color=WARM, lw=2.0))
    axg.text(px + 0.75, py + 2.15, "nudge one entry →\nslide off into nonsense",
             color=WARM, fontsize=10.5, ha="left", va="center")

    return P.save(f, "lie-manifold.png")


# alternate a subtle checker so the 3x3 grid reads as a filled matrix
def PANEL_FILL(i, j):
    return "#1d2836" if (i + j) % 2 == 0 else "#223143"


if __name__ == "__main__":
    print("wrote", fig_manifold())
