"""Concept figure for The Guidance Forge (diffusion wing).

Classifier-free guidance as vector arithmetic: strike the coal twice, subtract
to isolate the prompt direction, and EXTRAPOLATE beyond the conditioned
prediction. The concrete striking uses the room's own numbers
(eps_uncond = 0.20, eps_cond = 0.30, w = 7.5 -> 0.95).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_guidance.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import palace_fig as P

WING = "amber"
ACC = P.WING[WING]["accent"]   # warm gold
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]

UNC = "#8fb0d8"    # unconditioned flame, cool
CON = "#ffc46b"    # conditioned flame, warm gold
GUI = "#ff9a5a"    # guided / extrapolated, hot ember


def fig_guidance():
    f = plt.figure(figsize=(16.5, 10.2))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 2, height_ratios=[1.06, 0.82],
                        hspace=0.40, wspace=0.20,
                        left=0.06, right=0.96, top=0.85, bottom=0.075)

    P.suptitle(f, "The Guidance Forge, Two Flames, Then Extrapolate Past the Prompt")
    f.text(0.5, 0.905,
           "ε_guided = ε_uncond + w · (ε_cond − ε_uncond).   The subtraction isolates the prompt direction; "
           "w sets how far past ε_cond we sprint.  w > 1 is EXTRAPOLATION, not a blend.",
           ha="center", color=P.MUTED, fontsize=13.2)

    # numbers straight from the room
    e_unc, e_con = 0.20, 0.30
    dirn = e_con - e_unc              # 0.10
    ws = [0, 1, 3, 7.5]
    e_g = {w: e_unc + w * dirn for w in ws}   # 0.20, 0.30, 0.50, 0.95

    # ======================================================================
    # (a) vector arithmetic in a 2D image-space sketch
    # ======================================================================
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=True)
    ax.set_title("(a)  In noise-prediction space: subtract, then extrapolate",
                 color=P.INK, fontsize=15)
    ax.set_xlim(-0.3, 6.6); ax.set_ylim(-0.3, 6.6)
    ax.set_aspect("equal")
    ax.set_xlabel("noise-prediction axis 1", fontsize=11)
    ax.set_ylabel("noise-prediction axis 2", fontsize=11)

    O = np.array([0.0, 0.0])
    U = np.array([2.2, 1.4])           # eps_uncond
    d = np.array([0.45, 0.55])         # (eps_cond - eps_uncond), the prompt direction
    C = U + d                          # eps_cond  (w = 1)
    pts = {w: U + w * d for w in ws}

    # the two flames as arrows from a common tail (x_t), both point "toward
    # less noise", so they are nearly collinear; their DIFFERENCE is the prompt.
    ax.add_artist(FancyArrowPatch(O, U, arrowstyle="-|>", mutation_scale=20,
                                  color=UNC, lw=2.6, zorder=4))
    ax.add_artist(FancyArrowPatch(O, C, arrowstyle="-|>", mutation_scale=20,
                                  color=CON, lw=2.6, zorder=4))
    ax.text(0.05, -0.05, "x_t  (current estimate)", ha="left", va="top",
            color=P.MUTED, fontsize=10.5)
    # ε_uncond label pushed into empty lower-right
    ax.annotate("ε_uncond\n(toward a generic image)", xy=(1.15, 0.73),
                xytext=(2.7, 0.35), color=UNC, fontsize=11.5, fontweight="bold",
                ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=UNC, lw=1.3))
    # ε_cond label pushed into empty upper-left
    ax.annotate("ε_cond\n(toward the prompt)", xy=(1.42, 1.02),
                xytext=(0.35, 4.05), color=CON, fontsize=11.5, fontweight="bold",
                ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=CON, lw=1.3))

    # the guidance ray from U outward through the w-points
    far = pts[7.5]
    ax.plot([U[0], far[0]], [U[1], far[1]], color=GUI, lw=2.0, ls=(0, (5, 3)),
            zorder=3, alpha=0.9)
    ax.add_artist(FancyArrowPatch(pts[3], far, arrowstyle="-|>", mutation_scale=22,
                                  color=GUI, lw=2.6, zorder=5))

    # prompt-direction vector U->C highlighted, label to the empty left
    ax.annotate("", xy=C, xytext=U,
                arrowprops=dict(arrowstyle="-|>", color=P.INK, lw=2.8))
    mid = (U + C) / 2
    ax.annotate("ε_cond − ε_uncond\n= prompt direction", xy=(mid[0], mid[1]),
                xytext=(0.30, 1.55), color=P.INK, fontsize=11, ha="left",
                va="center", fontstyle="italic",
                arrowprops=dict(arrowstyle="-", color=P.MUTED, lw=1.2))

    # w markers along the ray with just the guidance scale (ε values live in (b))
    tagoff = {0: (0.26, -0.28), 1: (0.30, 0.05), 3: (0.28, -0.05), 7.5: (0.28, 0.0)}
    for w in ws:
        p = pts[w]
        col = {0: UNC, 1: CON, 3: GUI, 7.5: GUI}[w]
        ax.scatter(*p, s=100, color=col, edgecolor=P.BG, zorder=6, linewidth=1.6)
        ox, oy = tagoff[w]
        ax.text(p[0] + ox, p[1] + oy, f"w={w:g}", color=col, fontsize=11.5,
                fontweight="bold", ha="left", va="center", zorder=7)

    # extrapolation note in the empty region right of the lower ray
    ax.annotate("EXTRAPOLATION  (w > 1)\nfar past where the\nmodel was trained to land",
                xy=(pts[3][0] + 0.05, pts[3][1] - 0.05), xytext=(4.15, 2.35),
                color=GUI, fontsize=11, fontweight="bold", ha="left", va="center",
                arrowprops=dict(arrowstyle="-|>", color=GUI, lw=1.6,
                                connectionstyle="arc3,rad=0.28"))

    # ======================================================================
    # (b) the scalar striking: eps_guided grows linearly with w
    # ======================================================================
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING, grid=True)
    ax.set_title("(b)  One coal, struck twice: ε_guided = 0.20 + w·0.10",
                 color=P.INK, fontsize=15)
    wgrid = np.linspace(0, 9, 200)
    ax.plot(wgrid, e_unc + wgrid * dirn, color=GUI, lw=3, zorder=4)
    # reference levels
    ax.axhline(e_unc, color=UNC, ls=":", lw=1.6)
    ax.axhline(e_con, color=CON, ls=":", lw=1.6)
    ax.text(9.02, e_unc, "ε_uncond = 0.20", color=UNC, fontsize=11, va="center",
            fontweight="bold")
    ax.text(9.02, e_con, "ε_cond = 0.30", color=CON, fontsize=11, va="center",
            fontweight="bold")
    # interpolation vs extrapolation bands
    ax.axvspan(0, 1, color=UNC, alpha=0.10)
    ax.axvspan(1, 9, color=GUI, alpha=0.10)
    ax.text(0.5, 0.9, "blend\n0≤w≤1", color=UNC, fontsize=10.5, ha="center",
            fontweight="bold")
    ax.text(5.0, 0.28, "EXTRAPOLATION  (w > 1)", color=GUI, fontsize=11.5,
            ha="center", fontweight="bold")
    # the four worked points
    for w in ws:
        ax.scatter(w, e_g[w], s=90, color=GUI, edgecolor=P.BG, zorder=6, linewidth=1.5)
        ax.annotate(f"w={w:g} → {e_g[w]:.2f}", (w, e_g[w]),
                    xytext=(w + 0.15, e_g[w] + 0.055), color=P.INK, fontsize=11,
                    fontweight="bold")
    ax.scatter(7.5, 0.95, s=150, facecolor="none", edgecolor=GUI, lw=2.2, zorder=6)
    ax.set_xlim(0, 11.2); ax.set_ylim(0.0, 1.08)
    ax.set_xlabel("guidance scale  w", fontsize=12)
    ax.set_ylabel("ε_guided", fontsize=12)
    ax.annotate("typical setting", xy=(7.5, 0.95), xytext=(8.7, 0.72),
                color=GUI, fontsize=11, ha="center", fontstyle="italic",
                fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=GUI, lw=1.5))

    # ======================================================================
    # (c) the price of pushing too hard, schematic tradeoff
    # ======================================================================
    ax = f.add_subplot(gs[1,:]); P.style_ax(ax, WING, grid=True)
    ax.set_title("(c)  The price of burning twice: adherence rises, but too much w overcooks",
                 color=P.INK, fontsize=15)
    w = np.linspace(0, 20, 300)
    adherence = 1 - np.exp(-w / 2.4)                 # prompt fit: rises, saturates
    naturalness = 1 / (1 + np.exp((w - 9.5) / 2.2))  # diversity/realism: falls at high w
    ax.plot(w, adherence, color=CON, lw=3, label="prompt adherence  (↑ good)")
    ax.plot(w, naturalness, color=UNC, lw=3, label="diversity / naturalness  (↓ overcooked)")
    # sweet-spot band around 7.5
    ax.axvspan(6.0, 9.0, color=GUI, alpha=0.14)
    ax.axvline(7.5, color=GUI, lw=2.0, ls="--")
    ax.text(7.5, 1.06, "usual balance  w ≈ 7.5", color=GUI, fontsize=12,
            ha="center", fontweight="bold")
    # overcook zone
    ax.axvspan(13, 20, color=GUI, alpha=0.08)
    ax.text(16.5, 0.5, "over-saturated colours,\nblown contrast,\nlost diversity",
            color=GUI, fontsize=11, ha="center", va="center", fontstyle="italic",
            fontweight="bold")
    # w=0 and w=1 markers on the adherence curve
    ax.scatter([0, 1], [1 - np.exp(-0/2.4), 1 - np.exp(-1/2.4)], s=70,
               color=CON, edgecolor=P.BG, zorder=6, linewidth=1.3)
    ax.text(0.15, 0.02, "w=0: prompt ignored", color=UNC, fontsize=10.5, va="bottom")
    ax.text(1.15, 1 - np.exp(-1/2.4) - 0.02, "w=1: plain conditioning", color=CON,
            fontsize=10.5, va="top")
    ax.set_xlim(0, 20); ax.set_ylim(0, 1.16)
    ax.set_xlabel("guidance scale  w", fontsize=12)
    ax.set_ylabel("quality (schematic)", fontsize=12)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK, fontsize=12,
              loc="center left", bbox_to_anchor=(0.02, 0.42))

    f.text(0.5, 0.018,
           "cost: 2× inference, two forward passes every step, one conditioned and one unconditioned (null), "
           "the target of much distillation work",
           ha="center", color=P.MUTED, fontsize=11.2, fontstyle="italic")

    return P.save(f, "guidance-forge-cfg.png")


if __name__ == "__main__":
    print("wrote", fig_guidance())
