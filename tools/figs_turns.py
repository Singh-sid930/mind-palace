"""Concept figure for The Sphere of Turns (Lie / bronze cellar).

Two groups of turns, worked: SO(2) the circle, and SO(3) the surface of
spatial turns, hat a few bare numbers into a skew matrix, exponentiate,
and land on the turn.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_turns.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc
import palace_fig as P

WING = "bronze"
ACC = P.WING[WING]["accent"]   # warm brass
WARM = P.WING[WING]["warm"]    # copper
COOL = P.WING[WING]["cool"]    # patina green


# --- the two matrix exponentials, by their closed forms --------------------
def R2(theta):
    """exp([[0,-t],[t,0]]) = the planar turn."""
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s], [s, c]])


def hat3(w):
    """axis-angle vector -> 3x3 skew (the hat map)."""
    wx, wy, wz = w
    return np.array([[0, -wz, wy], [wz, 0, -wx], [-wy, wx, 0]])


def rodrigues(axis, theta):
    """R = I + sin t . K + (1 - cos t) . K^2, K = hat(unit axis)."""
    K = hat3(axis / np.linalg.norm(axis))
    return np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)


def fig_turns():
    f = plt.figure(figsize=(15.5, 8.2))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.05],
                        left=0.045, right=0.975, top=0.83, bottom=0.10,
                        wspace=0.26)

    P.suptitle(f, "Two Groups of Turns, Worked, hat the numbers, "
                  "exponentiate, get the turn")
    f.text(0.5, 0.895,
           "vector of freedoms  →(hat)→  skew matrix  "
           "→(exp)→  rotation",
           ha="center", color=WARM, fontsize=14.5, fontweight="bold")

    # =====================================================================
    # (a) SO(2): the unit circle, a vector turned by several angles
    # =====================================================================
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    tt = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(tt), np.sin(tt), color=COOL, lw=2.0, alpha=0.9)

    angles = [0, np.pi / 6, np.pi / 3, np.pi / 2, 2 * np.pi / 3]
    labs = [r"$0$", r"$\pi/6$", r"$\pi/3$", r"$\pi/2$", r"$2\pi/3$"]
    v0 = np.array([1.0, 0.0])
    cols = [P.MUTED, COOL, COOL, ACC, WARM]
    lws = [2.0, 2.0, 2.0, 3.2, 2.0]
    for th, lab, c, lw in zip(angles, labs, cols, lws):
        v = R2(th) @ v0
        ax.add_patch(FancyArrowPatch((0, 0), (v[0], v[1]),
                     arrowstyle="-|>", mutation_scale=17, color=c, lw=lw,
                     zorder=5))
        r = 1.16
        ax.text(r * np.cos(th), r * np.sin(th), lab, color=c, fontsize=13,
                ha="center", va="center", fontweight="bold")
    # sweep arc from 0 to pi/2
    ax.add_patch(Arc((0, 0), 0.66, 0.66, angle=0, theta1=0, theta2=90,
                     color=ACC, lw=1.8))
    ax.text(0.30, 0.30, r"$\theta$", color=ACC, fontsize=15, fontweight="bold")

    ax.set_xlim(-1.35, 1.55); ax.set_ylim(-1.35, 1.45)
    ax.set_aspect("equal")
    ax.axhline(0, color=P.GRID, lw=0.8); ax.axvline(0, color=P.GRID, lw=0.8)
    ax.set_title("(a)  SO(2): the circle of planar turns", color=P.INK,
                 fontsize=14)
    ax.text(0.5, -1.58,
            "R(θ) =  ⎡ cos θ   −sin θ ⎤\n"
            "           ⎣ sin θ    cos θ ⎦",
            color=P.INK, fontsize=13, ha="center", va="top",
            family="monospace")
    ax.text(0.5, -2.14,
            "worked  θ = π/2 :   ⎡ 0  −1 ⎤\n"
            "                          ⎣ 1   0 ⎦",
            color=WARM, fontsize=13, ha="center", va="top",
            family="monospace")
    ax.text(0.5, -2.74,
            "hat the angle, exponentiate, get the turn:\n"
            "exp ⎡ 0  −θ ⎤⎣ θ   0 ⎦ = R(θ)",
            color=ACC, fontsize=12.5, ha="center", va="top",
            family="monospace", fontweight="bold")

    # =====================================================================
    # (b) exp wraps the flat tangent line onto SO(2)
    # =====================================================================
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING, grid=False)
    ax.plot(np.cos(tt), np.sin(tt), color=COOL, lw=2.0, alpha=0.9)
    # the tangent line (the Lie algebra so(2)) at the identity point (1,0)
    ys = np.linspace(-1.55, 1.75, 200)
    ax.plot(np.ones_like(ys), ys, color=WARM, lw=2.2, ls="--", alpha=0.95)
    ax.text(-1.28, -0.45, "flat tangent line = so(2):\n"
            "the skew ⎡0 −θ⎤⎣θ  0⎦",
            color=WARM, fontsize=11, ha="left", va="top",
            family="monospace")
    # mark equal step-lengths theta on the line, wrap each onto the circle
    steps = [np.pi / 6, np.pi / 3, np.pi / 2]
    slab = [r"$\pi/6$", r"$\pi/3$", r"$\pi/2$"]
    ax.scatter([1], [0], color=P.INK, s=40, zorder=6)
    ax.text(1.05, -0.02, "identity", color=P.INK, fontsize=10.5, va="top")
    for th, lb in zip(steps, slab):
        # point up the tangent line at arc-length theta
        pl = np.array([1.0, th])
        # its image on the circle: exp wraps arc-length theta round
        pc = R2(th) @ np.array([1.0, 0.0])
        ax.scatter([pl[0]], [pl[1]], color=WARM, s=28, zorder=6)
        ax.scatter([pc[0]], [pc[1]], color=ACC, s=34, zorder=6)
        arr = FancyArrowPatch(pl, pc, connectionstyle="arc3,rad=0.32",
                              arrowstyle="-|>", mutation_scale=13,
                              color=ACC, lw=1.5, alpha=0.9, zorder=4)
        ax.add_patch(arr)
        ax.text(pl[0] + 0.07, pl[1], lb, color=WARM, fontsize=11,
                va="center", ha="left")
    ax.set_xlim(-1.35, 1.95); ax.set_ylim(-1.65, 1.95)
    ax.set_aspect("equal")
    ax.axhline(0, color=P.GRID, lw=0.8); ax.axvline(0, color=P.GRID, lw=0.8)
    ax.set_title("(b)  exp wraps the flat line onto the circle", color=P.INK,
                 fontsize=14)
    ax.text(0.3, -2.02,
            "Walk arc-length θ up the flat algebra; exp lays it round the\n"
            "curved group. The tangent line is straight and additive, \n"
            "the circle is where the turns actually live.",
            color=P.MUTED, fontsize=11.5, ha="center", va="top")

    # =====================================================================
    # (c) SO(3): an axis-angle turn on the sphere proxy
    # =====================================================================
    ax = f.add_subplot(gs[0, 2], projection="3d")
    ax.set_facecolor(P.BG)
    ax.set_box_aspect((1, 1, 1))
    # faint wireframe sphere (a PROXY for SO(3), not SO(3) itself)
    u = np.linspace(0, 2 * np.pi, 26)
    v = np.linspace(0, np.pi, 14)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_wireframe(xs, ys, zs, color=P.GRID, linewidth=0.5, alpha=0.55)

    axis = np.array([0.35, 0.35, 1.0]); axis = axis / np.linalg.norm(axis)
    theta = np.deg2rad(120)
    # a probe vector off the axis, and its rotation
    p = np.array([1.0, -0.2, 0.15]); p = p / np.linalg.norm(p)
    Rp = rodrigues(axis, theta) @ p

    # rotation axis (both directions)
    ax.quiver(0, 0, 0, axis[0] * 1.35, axis[1] * 1.35, axis[2] * 1.35,
              color=WARM, lw=2.6, arrow_length_ratio=0.12)
    ax.quiver(0, 0, 0, -axis[0] * 0.55, -axis[1] * 0.55, -axis[2] * 0.55,
              color=WARM, lw=1.4, arrow_length_ratio=0.0, alpha=0.6)
    ax.text(axis[0] * 1.15, axis[1] * 1.15, axis[2] * 1.15 + 0.14,
            "axis ω/|ω|", color=WARM, fontsize=12, fontweight="bold",
            ha="right")
    # probe and turned probe
    ax.quiver(0, 0, 0, p[0], p[1], p[2], color=COOL, lw=2.4,
              arrow_length_ratio=0.13)
    ax.quiver(0, 0, 0, Rp[0], Rp[1], Rp[2], color=ACC, lw=2.8,
              arrow_length_ratio=0.13)
    ax.text(p[0] * 1.12, p[1] * 1.12, p[2] * 1.12 - 0.12, "v", color=COOL,
            fontsize=13, fontweight="bold")
    ax.text(Rp[0] * 1.14, Rp[1] * 1.14, Rp[2] * 1.14, "Rv", color=ACC,
            fontsize=13, fontweight="bold")
    # the arc of the turn from v to Rv (a small circle about the axis)
    n = p - np.dot(p, axis) * axis
    n = n / np.linalg.norm(n)
    m = np.cross(axis, n)
    rad = np.linalg.norm(p - np.dot(p, axis) * axis)
    cen = np.dot(p, axis) * axis
    aa = np.linspace(0, theta, 60)
    arc = (cen[:, None] + rad * (np.cos(aa) * n[:, None]
                                 + np.sin(aa) * m[:, None]))
    ax.plot(arc[0], arc[1], arc[2], color=ACC, lw=1.8, ls=":")
    ax.text(arc[0, 30] * 1.05, arc[1, 30] * 1.05, arc[2, 30] * 1.05 + 0.08,
            r"$\theta$", color=ACC, fontsize=14, fontweight="bold")

    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
    ax.xaxis.pane.set_visible(False)
    ax.yaxis.pane.set_visible(False)
    ax.zaxis.pane.set_visible(False)
    ax.grid(False)
    try:
        ax.view_init(elev=18, azim=-58)
    except Exception:
        pass
    ax.set_title("(c)  SO(3): axis + angle, one spatial turn", color=P.INK,
                 fontsize=14, y=1.04)

    # captions under panel (c) in figure coords (3D axes crowd their own space)
    f.text(0.815, 0.205,
           "axis-angle  ω ∈ R³   →(hat)→   skew [ω]×   →(exp)→   R",
           color=ACC, fontsize=12, ha="center", fontweight="bold")
    f.text(0.815, 0.16,
           r"Rodrigues:  $R = I + \sin\theta\,K + (1-\cos\theta)\,K^2$",
           color=P.INK, fontsize=12.5, ha="center")
    f.text(0.815, 0.093,
           "SO(3) is a genuine 3-dimensional surface; so(3) is the 3×3\n"
           "skew matrices. The drawn sphere is only a PROXY, the true\n"
           "shape of SO(3) cannot be drawn.",
           color=P.MUTED, fontsize=11, ha="center", va="top")

    return P.save(f, "lie-so2-so3.png")


if __name__ == "__main__":
    print("wrote", fig_turns())
