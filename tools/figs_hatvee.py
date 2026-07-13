"""Concept figure for 'The Hat and the Vee' (Wing of Continuous Motion, bronze).

The hat operator as a picture (2D scalar -> 2x2 skew frame; 3D vector -> 3x3
skew frame with the antisymmetry made visible), and the three-space relay
ℝⁿ --hat--> matrix --exp--> surface --log--> matrix --vee--> ℝⁿ.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_hatvee.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import palace_fig as P

WING = "bronze"
ACC = P.WING[WING]["accent"]   # brass gold
WARM = P.WING[WING]["warm"]    # burnt orange
COOL = P.WING[WING]["cool"]    # olive


def cell_text(v):
    if v == 0:
        return "0"
    s = "−" if v < 0 else ""
    a = abs(v)
    return s + a


def draw_matrix(ax, entries, xy, cell=1.0, title="", labels=None,
                accent=ACC, fontsize=17):
    """entries: list of rows of strings. Draw a boxed grid at xy (top-left)."""
    x0, y0 = xy
    nr = len(entries)
    nc = len(entries[0])
    for i in range(nr):
        for j in range(nc):
            cx = x0 + j * cell
            cy = y0 - i * cell
            txt = entries[i][j]
            # colour zero diagonal grey; off-diagonal negatives warm, pos accent
            if txt == "0":
                col = P.MUTED
            elif txt.startswith("−"):
                col = WARM
            else:
                col = accent
            ax.text(cx, cy, txt, ha="center", va="center", color=col,
                    fontsize=fontsize, fontweight="bold")
    # bracket outlines
    left = x0 - cell * 0.55
    right = x0 + (nc - 1) * cell + cell * 0.55
    top = y0 + cell * 0.55
    bot = y0 - (nr - 1) * cell - cell * 0.55
    tick = cell * 0.16
    for bx, d in [(left, 1), (right, -1)]:
        ax.plot([bx, bx], [bot, top], color=P.INK, lw=2.0)
        ax.plot([bx, bx + d * tick], [top, top], color=P.INK, lw=2.0)
        ax.plot([bx, bx + d * tick], [bot, bot], color=P.INK, lw=2.0)
    if title:
        ax.text((left + right) / 2, top + cell * 0.55, title, ha="center",
                va="bottom", color=P.INK, fontsize=13.5, fontweight="bold")


def fig_hat_vee():
    f = plt.figure(figsize=(14.2, 8.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 2, height_ratios=[1.0, 0.86],
                        hspace=0.30, wspace=0.16,
                        left=0.04, right=0.97, top=0.87, bottom=0.055)
    P.suptitle(f, "The Hat and the Vee  —  lift a list of numbers into a skew frame, and read it back")
    f.text(0.5, 0.905,
           "hat (∧) lifts a coordinate vector up into its skew-symmetric matrix; "
           "vee (∨) reads the matrix back down to the vector.  Aᵀ = −A: zero "
           "diagonal, mirror entries negated.",
           ha="center", color=P.MUTED, fontsize=12.5)

    # --------------------------------------------------------------- (a) 2D
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.2)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(a)  the 2D hat:  one number → a 2×2 skew frame", color=P.INK,
                 fontsize=14)
    # scalar a
    ax.text(1.15, 3.1, "a", ha="center", va="center", color=ACC,
            fontsize=30, fontweight="bold")
    ax.text(1.15, 1.9, "one number\n(amount of turn)", ha="center", va="top",
            color=P.MUTED, fontsize=11)
    # hat arrow
    ax.add_patch(FancyArrowPatch((2.1, 3.1), (4.0, 3.1), arrowstyle="-|>",
                                 mutation_scale=22, color=COOL, lw=2.6))
    ax.text(3.05, 3.55, "hat  ∧", ha="center", color=COOL, fontsize=14,
            fontweight="bold")
    # vee arrow back
    ax.add_patch(FancyArrowPatch((4.0, 2.4), (2.1, 2.4), arrowstyle="-|>",
                                 mutation_scale=22, color=WARM, lw=2.6))
    ax.text(3.05, 1.62, "vee  ∨", ha="center", color=WARM, fontsize=14,
            fontweight="bold")
    # 2x2 matrix
    draw_matrix(ax, [["0", "−a"], ["a", "0"]], (5.9, 3.9), cell=1.35,
                fontsize=22)
    ax.text(6.55, 0.85, "diagonal = 0,  off-diagonal = a and −a", ha="center",
            va="center", color=P.INK, fontsize=11.5)

    # --------------------------------------------------------------- (b) 3D
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.2)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(b)  the 3D hat:  a vector → a 3×3 skew frame", color=P.INK,
                 fontsize=14)
    # vector [x,y,z]
    draw_matrix(ax, [["x"], ["y"], ["z"]], (1.15, 4.2), cell=1.1, fontsize=19)
    ax.text(1.15, 0.95, "coordinate\nvector in R³", ha="center", va="top",
            color=P.MUTED, fontsize=11)
    # hat / vee arrows
    ax.add_patch(FancyArrowPatch((2.15, 3.3), (3.7, 3.3), arrowstyle="-|>",
                                 mutation_scale=20, color=COOL, lw=2.4))
    ax.text(2.95, 3.72, "hat ∧", ha="center", color=COOL, fontsize=13,
            fontweight="bold")
    ax.add_patch(FancyArrowPatch((3.7, 2.6), (2.15, 2.6), arrowstyle="-|>",
                                 mutation_scale=20, color=WARM, lw=2.4))
    ax.text(2.95, 1.95, "vee ∨", ha="center", color=WARM, fontsize=13,
            fontweight="bold")
    # 3x3 skew matrix
    M = [["0", "−z", "y"],
         ["z", "0", "−x"],
         ["−y", "x", "0"]]
    draw_matrix(ax, M, (5.7, 4.5), cell=1.25, fontsize=18)
    # highlight the zero diagonal with a faint band
    ax.text(6.95, 0.75, "Aᵀ = −A  (mirror across the diagonal negates)",
            ha="center", va="center", color=P.INK, fontsize=11)

    # --------------------------------------------------------------- (c) relay
    ax = f.add_subplot(gs[1, :]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.6)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(c)  the three-space relay:  two bridges among three spaces",
                 color=P.INK, fontsize=14)

    def box(x, y, label, col, w=2.3, h=1.2):
        b = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                           boxstyle="round,pad=0.06,rounding_size=0.14",
                           linewidth=2.2, edgecolor=col,
                           facecolor=P.PANEL, zorder=3)
        ax.add_patch(b)
        ax.text(x, y, label, ha="center", va="center", color=P.INK,
                fontsize=13, fontweight="bold", zorder=4)

    # triangle: Rⁿ bottom-left, matrix top-centre, surface bottom-right
    Rn = np.array([2.6, 1.55])
    Mx = np.array([6.0, 3.85])
    Sf = np.array([9.4, 1.55])
    box(*Rn, "Rⁿ  coordinates\n(arithmetic lives here)", COOL, w=3.0)
    box(*Mx, "skew-symmetric\nmatrix", ACC, w=2.9)
    box(*Sf, "curved surface\n(valid states)", WARM, w=3.0)

    def edge(A, B, label, col, side=1, pad=1.35, sep=0.45, lab=0.62):
        """One arrow A->B, offset perpendicular to the segment by `side`."""
        d = B - A
        u = d / np.linalg.norm(d)
        perp = np.array([-u[1], u[0]]) * side
        a = A + u * pad + perp * sep
        b = B - u * pad + perp * sep
        ax.add_patch(FancyArrowPatch(tuple(a), tuple(b), arrowstyle="-|>",
                                     mutation_scale=20, color=col, lw=2.6,
                                     zorder=2))
        m = (a + b) / 2 + perp * lab
        ax.text(m[0], m[1], label, ha="center", va="center", color=col,
                fontsize=13.5, fontweight="bold")

    # left bridge: hat up (Rⁿ→matrix), vee down (matrix→Rⁿ)
    edge(Rn, Mx, "hat ∧", COOL, side=+1)
    edge(Mx, Rn, "vee ∨", WARM, side=+1)
    # right bridge: exp down-out (matrix→surface), log up-back (surface→matrix)
    edge(Mx, Sf, "exp", ACC, side=+1)
    edge(Sf, Mx, "log", WARM, side=+1)

    ax.text(6.0, 0.42,
            "hat then exp climbs to a valid point on the surface;  "
            "log then vee brings it back down to numbers you can add and average.",
            ha="center", va="center", color=P.MUTED, fontsize=12)

    return P.save(f, "lie-hat-vee.png")


if __name__ == "__main__":
    print("wrote", fig_hat_vee())
