"""Concept figure for The Hall of Directions (LoRA wing, obsidian palette).

The SVD connection: energy of a fine-tuning update lives in a few singular
directions (so rank-r suffices), and the two roads to a rank-r update.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_directions.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import palace_fig as P

WING = "obsidian"
ACC = P.WING[WING]["accent"]   # teal glow
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]    # muted teal


def box(ax, xy, w, h, text, fc=P.PANEL, ec=None, tc=P.INK, fs=12.5,
        fw="normal", round_pad=0.02):
    ec = ec or P.GRID
    x, y = xy
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad={round_pad},rounding_size=0.03",
                       linewidth=1.6, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tc, fontsize=fs, fontweight=fw, zorder=4, wrap=True)
    return (x + w / 2, y, x + w / 2, y + h)  # (cx, ybot, cx, ytop)


def arrow(ax, p0, p1, color=ACC, lw=2.2, style="-|>", ls="-", mut=16):
    a = FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=mut,
                        linewidth=lw, color=color, linestyle=ls,
                        shrinkA=3, shrinkB=3, zorder=2)
    ax.add_patch(a)


def fig_svd_connection():
    sig = np.array([8.2, 5.1, 3.7, 0.9, 0.3, 0.08, 0.03, 0.012, 0.005, 0.002])
    n = len(sig)
    idx = np.arange(1, n + 1)
    energy = np.cumsum(sig) / sig.sum() * 100.0
    r_star = 3  # elbow after the third singular value

    f = plt.figure(figsize=(16.5, 8.4))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.06, 1.0],
                        left=0.065, right=0.975, top=0.83, bottom=0.11,
                        wspace=0.22)

    P.suptitle(f, "The Spectrum Read  —  a fine-tuning update spends its energy "
                  "on a few directions")
    f.text(0.5, 0.895,
           "singular values of an update ΔW, sorted large → small "
           "(representative values — the SHAPE is the lesson)",
           ha="center", color=P.MUTED, fontsize=13)

    # -- (a) spectrum bars + cumulative energy -------------------------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    bars = ax.bar(idx, sig, width=0.62, color=COOL, edgecolor=ACC,
                  linewidth=1.2, zorder=3)
    for b in bars[:r_star]:
        b.set_color(ACC); b.set_edgecolor(P.INK)
    for b, s in zip(bars, sig):
        if s >= 0.05:
            ax.annotate(f"{s:.2g}", (b.get_x() + b.get_width() / 2, s),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", color=P.INK,
                        fontsize=11.5, fontweight="bold")
    # elbow marker
    ax.axvline(r_star + 0.5, color=WARM, ls="--", lw=1.8, zorder=2)
    ax.annotate("the elbow —\nσ drops to ≈ 0 here",
                xy=(r_star + 0.5, 6.4), xytext=(r_star + 1.6, 7.6),
                color=WARM, fontsize=12.5, fontweight="bold", ha="left",
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.8))
    ax.set_xticks(idx)
    ax.set_xlim(0.4, n + 0.6)
    ax.set_ylim(0, 9.1)
    ax.set_xlabel("singular-value index  i", fontsize=13)
    ax.set_ylabel("singular value  σᵢ  (bars)", fontsize=13, color=ACC)
    ax.set_title("(a)  Fast decay — a few bright directions, a long dim tail",
                 color=P.INK, fontsize=14.5, pad=10)

    # cumulative energy on twin axis
    ax2 = ax.twinx()
    ax2.plot(idx, energy, color=WARM, lw=2.4, marker="o", ms=6,
             markerfacecolor=P.BG, markeredgecolor=WARM, zorder=5)
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("cumulative energy  (%, line)", fontsize=13, color=WARM)
    ax2.tick_params(colors=WARM, labelsize=11)
    for s in ax2.spines.values():
        s.set_color(P.GRID)
    ax2.axhline(100, color=P.GRID, ls=":", lw=1.0)
    ax2.annotate(f"top {r_star}: {energy[r_star-1]:.0f}% of energy",
                 xy=(r_star, energy[r_star - 1]),
                 xytext=(r_star + 1.3, 55),
                 color=WARM, fontsize=12, fontweight="bold", ha="left",
                 arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.6))
    ax.text(0.5, -0.145,
            "energy lives in a few directions → a rank-r truncation keeps "
            "almost all of ΔW",
            transform=ax.transAxes, ha="center", color=ACC, fontsize=12.5,
            fontweight="bold")

    # -- (b) two roads schematic ---------------------------------------------
    ax = f.add_subplot(gs[0, 1]); ax.set_facecolor(P.PANEL)
    for s in ax.spines.values():
        s.set_color(P.GRID)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(b)  Two roads to the same rank-r update  B·A",
                 color=P.INK, fontsize=14.5, pad=10)

    # column headers
    ax.text(2.5, 9.45, "SVD truncation", ha="center", color=WARM,
            fontsize=13.5, fontweight="bold")
    ax.text(2.5, 9.0, "THEORY — not a pipeline step", ha="center",
            color=P.MUTED, fontsize=10.5, style="italic")
    ax.text(7.5, 9.45, "LoRA", ha="center", color=ACC,
            fontsize=13.5, fontweight="bold")
    ax.text(7.5, 9.0, "PRACTICE — what actually runs", ha="center",
            color=P.MUTED, fontsize=10.5, style="italic")

    # left road (SVD)
    t1 = box(ax, (0.7, 7.4), 3.6, 1.1,
             "a GIVEN full update\nΔW  (d × k)", ec=WARM, tc=WARM)
    t2 = box(ax, (0.7, 5.4), 3.6, 1.1,
             "factor exactly:\nΔW = U Σ Vᵀ")
    t3 = box(ax, (0.7, 3.4), 3.6, 1.1,
             "keep top r  (Eckart–Young):\nUᵣ Σᵣ Vᵣᵀ  — best rank-r")
    arrow(ax, (t1[0], t1[1]), (t2[0], t2[3]), color=WARM)
    arrow(ax, (t2[0], t2[1]), (t3[0], t3[3]), color=WARM)
    ax.text(2.5, 2.72, "minimizes RECONSTRUCTION\n(closest matrix to a given ΔW)",
            ha="center", va="center", color=WARM, fontsize=10.5, style="italic")

    # right road (LoRA)
    s1 = box(ax, (5.7, 7.4), 3.6, 1.1,
             "a TASK + its loss\n(no ΔW ever formed)", ec=ACC, tc=ACC)
    s2 = box(ax, (5.7, 5.4), 3.6, 1.1,
             "parameterize thin\nB (d×r),  A (r×k)")
    s3 = box(ax, (5.7, 3.4), 3.6, 1.1,
             "learn B, A by gradient\ndescent on the loss")
    arrow(ax, (s1[0], s1[1]), (s2[0], s2[3]), color=ACC)
    arrow(ax, (s2[0], s2[1]), (s3[0], s3[3]), color=ACC)
    ax.text(7.5, 2.72, "minimizes TASK LOSS\n(update is discovered, not copied)",
            ha="center", va="center", color=ACC, fontsize=10.5, style="italic")

    # converge to shared rank-r update
    conv = box(ax, (2.5, 0.5), 5.0, 1.25,
               "rank-r update   ΔW ≈ B·A\n(d×r) · (r×k),  waist width r",
               ec=P.INK, tc=P.INK, fs=12.5, fw="bold")
    arrow(ax, (t3[0], 3.4), (conv[0] - 0.7, conv[3]), color=WARM, ls="--")
    arrow(ax, (s3[0], 3.4), (conv[0] + 0.7, conv[3]), color=ACC)

    ax.text(5.0, 0.18,
            "same low-rank SHAPE  ·  different objectives  ·  LoRA never walks "
            "the left road",
            ha="center", va="center", color=P.MUTED, fontsize=11,
            fontweight="bold")

    return f


if __name__ == "__main__":
    f = fig_svd_connection()
    print(P.save(f, "lora-svd-connection.png"))
