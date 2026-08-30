"""Concept figure for the basement room `the-sliding-kernel` (Arithmancy, violet).

PURE MATH, convolution as a window of weights slid across a signal.
No downstream jargon: only signals, kernels, windows, grids, volumes, dot products.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_kernel.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import palace_fig as P

WING = "violet"
ACC = P.WING[WING]["accent"]   # violet
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]

MINUS = "−"   # true minus sign


def cell(ax, x, y, w, h, text="", fc=P.PANEL, ec=P.GRID, tc=P.INK,
         fs=15, bold=True, alpha=1.0, lw=1.6):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                           lw=lw, alpha=alpha, zorder=2))
    if text != "":
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                color=tc, fontsize=fs, fontweight="bold" if bold else "normal",
                zorder=3)


def fig_kernel():
    signal = [1, 1, 1, 2, 3, 4]
    kernel = [1, 0, -1]
    outs = [signal[t] * 1 + signal[t + 1] * 0 + signal[t + 2] * (-1)
            for t in range(len(signal) - len(kernel) + 1)]   # [0, -1, -2, -2]

    f = plt.figure(figsize=(14.0, 15.0))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(3, 1, height_ratios=[1.32, 0.60, 0.86],
                        hspace=0.16, left=0.045, right=0.975,
                        top=0.935, bottom=0.035)

    P.suptitle(f, "The Sliding Kernel, a window of weights, "
                  "slid across a signal, multiply-and-sum at every stop")
    f.text(0.5, 0.955,
           "signal = [1, 1, 1, 2, 3, 4]        kernel = [1, 0, "
           f"{MINUS}1]        each output = kernel · local window",
           ha="center", color=P.MUTED, fontsize=14)

    # =====================================================================
    # (a)  1-D convolution WORKED, the window slid across the signal
    # =====================================================================
    ax = f.add_subplot(gs[0]); ax.axis("off")
    ax.set_xlim(-0.6, 13.6); ax.set_ylim(0.0, 10.4)
    ax.text(-0.4, 9.95, "(a)  Slide, multiply, sum. Every stop is a "
            "dot product", color=P.INK, fontsize=16, fontweight="bold",
            ha="left", va="center")

    tops = [7.95, 6.45, 4.95, 3.45]     # cell-bottom y for each stop
    ch = 1.0                            # cell height
    wlab = ["×1", "×0", f"×{MINUS}1"]
    for t, yb in enumerate(tops):
        a, b, c = signal[t], signal[t + 1], signal[t + 2]
        # the six signal cells; window t..t+2 highlighted
        for i, v in enumerate(signal):
            inwin = t <= i <= t + 2
            cell(ax, i, yb, 1.0, ch, str(v),
                 fc=ACC if inwin else P.PANEL,
                 tc=P.BG if inwin else P.MUTED,
                 fs=17, alpha=1.0 if inwin else 0.55)
        # weight tags above the three covered cells
        for j, i in enumerate((t, t + 1, t + 2)):
            ax.text(i + 0.5, yb + ch + 0.18, wlab[j], ha="center", va="bottom",
                    color=WARM, fontsize=12.5, fontweight="bold")
        # arithmetic + result cell
        eqn = (f"1·{a} + 0·{b} + ({MINUS}1)·{c}  =")
        ax.text(6.7, yb + ch / 2, eqn, ha="left", va="center",
                color=P.INK, fontsize=15)
        cell(ax, 12.1, yb, 1.15, ch, f"{outs[t]}" if outs[t] >= 0 else f"{MINUS}{abs(outs[t])}",
             fc=P.PANEL, ec=WARM, tc=WARM, fs=17, lw=2.0)
        ax.text(0 + 3.0, yb + ch / 2, "", )  # noop spacing
    # "stop" labels on the left
    for t, yb in enumerate(tops):
        ax.text(-0.42, yb + ch / 2, f"stop {t+1}", ha="right", va="center",
                color=P.MUTED, fontsize=11.5, rotation=0)
    # slide arrows between successive stops (window steps right by one)
    for t in range(len(tops) - 1):
        y0 = tops[t]; y1 = tops[t + 1] + ch
        xw = (t + 1) + 0.5   # roughly the moving edge
        ax.annotate("", xy=(xw + 1.0, y1), xytext=(xw, y0),
                    arrowprops=dict(arrowstyle="-|>", color=COOL, lw=1.8,
                                    alpha=0.9))
    ax.text(3.9, (tops[0] + tops[1]) / 2 + 0.15, "slide  +1",
            color=COOL, fontsize=11, rotation=-32, ha="center", va="center")

    # assembled output signal (aligned under window centres)
    yo = 1.55
    ax.text(0.5, yo + ch / 2, "output", ha="center", va="center",
            color=P.INK, fontsize=13.5, fontweight="bold")
    for t, v in enumerate(outs):
        cx = t + 1                       # window t centre = t+1.5 -> cell [t+1,t+2]
        cell(ax, cx + 1.0, yo, 1.0, ch,
             f"{v}" if v >= 0 else f"{MINUS}{abs(v)}",
             fc=WARM, tc=P.BG, fs=17)
    ax.text(7.6, yo + ch / 2, f"output signal  =  [0, {MINUS}1, {MINUS}2, "
            f"{MINUS}2]", ha="left", va="center", color=WARM, fontsize=14,
            fontweight="bold")
    ax.text(7.6, yo - 0.55, f"flat run → 0 (no change) · rising ramp "
            f"→ {MINUS}2 (steady change)",
            ha="left", va="center", color=P.MUTED, fontsize=11.5)

    # =====================================================================
    # (b)  LOCAL WINDOW (receptive field) + WEIGHT SHARING
    # =====================================================================
    ax = f.add_subplot(gs[1]); ax.axis("off")
    ax.set_xlim(-0.6, 13.6); ax.set_ylim(-1.15, 5.05)
    ax.text(-0.4, 4.75, "(b)  One output sees only a local window  ·  the "
            "same weights are reused everywhere",
            color=P.INK, fontsize=16, fontweight="bold", ha="left", va="center")

    # --- receptive field (left) -----------------------------------------
    ysig = 3.1
    for i, v in enumerate(signal):
        inwin = 2 <= i <= 4
        cell(ax, i, ysig, 1.0, 0.95, str(v),
             fc=ACC if inwin else P.PANEL,
             tc=P.BG if inwin else P.MUTED,
             fs=16, alpha=1.0 if inwin else 0.5)
    # bracket under the window
    ax.plot([2.05, 2.05, 4.95, 4.95], [ysig - 0.15, ysig - 0.4, ysig - 0.4,
            ysig - 0.15], color=ACC, lw=2.0)
    ax.text(3.5, ysig - 0.7, f"receptive field  ·  k = 3 inputs",
            ha="center", va="center", color=ACC, fontsize=12.5,
            fontweight="bold")
    # the single output it feeds (arrow starts below the label, so no crossing)
    cell(ax, 3.0, 0.4, 1.0, 0.95, f"{MINUS}2", fc=WARM, tc=P.BG, fs=16)
    ax.annotate("", xy=(3.5, 1.4), xytext=(3.5, ysig - 1.02),
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=2.0))
    ax.text(4.35, 0.9, "one output depends on\nNOTHING outside its window",
            ha="left", va="center", color=P.MUTED, fontsize=11.5)

    # --- weight sharing (right) -----------------------------------------
    xk = 8.9
    ax.text(xk + 1.5, 3.95, "WEIGHT SHARING", ha="center", va="center",
            color=WARM, fontsize=13, fontweight="bold")
    for row, yb in enumerate((2.75, 1.55)):
        for j, kv in enumerate(kernel):
            txt = str(kv) if kv >= 0 else f"{MINUS}{abs(kv)}"
            cell(ax, xk + j, yb, 1.0, 0.95, txt, fc=P.PANEL, ec=WARM,
                 tc=WARM, fs=16, lw=1.8)
        ax.text(xk + 3.3, yb + 0.48, f"stop {row+1}", ha="left", va="center",
                color=P.MUTED, fontsize=11.5)
    ax.text(xk + 1.5, 0.6, f"the SAME [1, 0, {MINUS}1] at every stop, "
            "k weights\nfor any signal length, not one rule per position",
            ha="center", va="center", color=P.MUTED, fontsize=11.5)

    # =====================================================================
    # (c)  1-D → 2-D → 3-D, same operation, more axes
    # =====================================================================
    gc = gs[2].subgridspec(2, 3, height_ratios=[0.16, 1.0], wspace=0.14,
                           hspace=0.02)
    axh = f.add_subplot(gc[0,:]); axh.axis("off")
    axh.text(0.0, 0.85, "(c)  One axis or three, it is the same enchantment: "
             "a local window of shared weights, slid everywhere",
             color=P.INK, fontsize=16, fontweight="bold", ha="left",
             va="top", transform=axh.transAxes)

    # --- 1-D: strip on a line -------------------------------------------
    axc = f.add_subplot(gc[1, 0]); axc.axis("off")
    axc.set_xlim(-0.5, 8.5); axc.set_ylim(-2.2, 3.2)
    axc.set_aspect("equal")
    axc.text(0.5, 0.94, "1-D  ·  line", transform=axc.transAxes,
             ha="center", va="top", color=P.INK, fontsize=14,
             fontweight="bold")
    for i in range(8):
        inwin = 2 <= i <= 4
        cell(axc, i, 0.5, 1.0, 1.0, "",
             fc=ACC if inwin else P.PANEL, tc=P.BG,
             alpha=1.0 if inwin else 0.5)
    axc.annotate("", xy=(6.4, 1.0), xytext=(4.2, 1.0),
                 arrowprops=dict(arrowstyle="-|>", color=COOL, lw=2.2))
    axc.text(4.0, -1.1, "strip of 3 weights\nslides along ONE axis",
             ha="center", va="center", color=P.MUTED, fontsize=12)

    # --- 2-D: square patch over a grid ----------------------------------
    axc = f.add_subplot(gc[1, 1]); axc.axis("off")
    axc.set_xlim(-0.5, 6.5); axc.set_ylim(-2.0, 7.4)
    axc.set_aspect("equal")
    axc.text(0.5, 0.98, "2-D  ·  grid", transform=axc.transAxes,
             ha="center", va="top", color=P.INK, fontsize=14,
             fontweight="bold")
    n = 6
    for r in range(n):
        for cix in range(n):
            inwin = (1 <= cix <= 3) and (2 <= r <= 4)
            cell(axc, cix, r, 1.0, 1.0, "",
                 fc=ACC if inwin else P.PANEL, ec=P.GRID,
                 alpha=1.0 if inwin else 0.5, lw=1.2)
    axc.annotate("", xy=(4.4, 3.5), xytext=(3.5, 3.5),
                 arrowprops=dict(arrowstyle="-|>", color=COOL, lw=2.0))
    axc.annotate("", xy=(2.5, 1.4), xytext=(2.5, 2.3),
                 arrowprops=dict(arrowstyle="-|>", color=COOL, lw=2.0))
    axc.text(3.0, -1.0, "3×3 square patch slides\nover rows AND columns",
             ha="center", va="center", color=P.MUTED, fontsize=12)

    # --- 3-D: small box within a volume (isometric voxels) --------------
    axc = f.add_subplot(gc[1, 2], projection="3d")
    axc.text2D(0.5, 0.99, "3-D  ·  volume", transform=axc.transAxes,
               ha="center", va="top", color=P.INK, fontsize=14,
               fontweight="bold")
    N = 5
    filled = np.zeros((N, N, N), bool)
    filled[:] = True
    hi = np.zeros((N, N, N), bool)
    hi[0:3, 0:3, 0:3] = True
    fc = np.empty(filled.shape, dtype=object)
    ec = np.empty(filled.shape, dtype=object)
    for idx in np.ndindex(filled.shape):
        if hi[idx]:
            fc[idx] = (0.82, 0.66, 1.0, 0.9)      # violet accent
            ec[idx] = (1, 1, 1, 0.28)
        else:
            fc[idx] = (0.42, 0.5, 0.62, 0.06)     # faint volume
            ec[idx] = (0.6, 0.68, 0.8, 0.10)
    axc.voxels(filled, facecolors=fc, edgecolors=ec, linewidth=0.5)
    axc.set_facecolor(P.BG)
    axc.set_axis_off()
    axc.view_init(elev=22, azim=-52)
    try:
        axc.set_box_aspect((1, 1, 1))
    except Exception:
        pass
    axc.text2D(0.5, -0.04, "3×3×3 box slides through\nthe volume "
               "(three axes)", transform=axc.transAxes, ha="center",
               va="center", color=P.MUTED, fontsize=12)

    return P.save(f, "convolution-kernel.png")


if __name__ == "__main__":
    print("wrote", fig_kernel())
