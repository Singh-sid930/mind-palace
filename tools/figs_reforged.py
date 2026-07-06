"""Concept figure for The Reforged Transformer (DiT wing) — DiT scaling.

Stylized / representative numbers: the SHAPE is the lesson, not the exact FID.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_reforged.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "crimson"
ACC = P.WING[WING]["accent"]   # coral
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]    # rose


def fig_scaling():
    f = plt.figure(figsize=(16.5, 8.4))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.12, 1.0],
                        wspace=0.19, left=0.06, right=0.975,
                        top=0.82, bottom=0.145)

    P.suptitle(f, "The Reforged Transformer  —  quality follows compute")
    f.text(0.5, 0.885,
           "Reforge the U-Net into a transformer and the language-model scaling "
           "law carries over: pour in compute, FID falls on a smooth frontier.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # === (a) FID vs model compute — the descending frontier ================
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    # stylized DiT model sizes: (name, Gflops/forward, FID)
    names = ["DiT-S/2", "DiT-B/2", "DiT-L/2", "DiT-XL/2"]
    gflops = np.array([6.0, 23.0, 80.0, 119.0])
    fid = np.array([68.0, 43.0, 23.3, 19.5])
    sizes = [130, 240, 400, 620]

    # smooth frontier line through the four sizes (in log-x)
    lg = np.log10(gflops)
    xx = np.linspace(lg[0], lg[-1], 200)
    yy = np.interp(xx, lg, fid)
    ax.plot(10 ** xx, yy, color=ACC, lw=2.6, alpha=0.55, zorder=2)
    ax.fill_between(10 ** xx, yy, 75, color=ACC, alpha=0.05, zorder=1)

    for n, g, y, s in zip(names, gflops, fid, sizes):
        ax.scatter([g], [y], s=s, color=ACC, edgecolor=P.BG, lw=1.5, zorder=4)
    # labels, nudged to avoid the markers
    ax.annotate("DiT-S/2", (gflops[0], fid[0]), xytext=(9, 66),
                color=P.INK, fontsize=11.5, fontweight="bold")
    ax.annotate("DiT-B/2", (gflops[1], fid[1]), xytext=(30, 45),
                color=P.INK, fontsize=11.5, fontweight="bold")
    ax.annotate("DiT-L/2", (gflops[2], fid[2]), xytext=(44, 26.5),
                color=P.INK, fontsize=11.5, fontweight="bold")
    ax.annotate("DiT-XL/2\non the frontier", (gflops[3], fid[3]),
                xytext=(150, 24.5), color=ACC, fontsize=12.5, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.8),
                ha="left")

    # U-Net-era baselines: flat-ish reference points, off the clean line
    ax.scatter([90], [26.5], s=180, marker="s", color=P.MUTED,
               edgecolor=P.BG, lw=1.3, zorder=3)
    ax.scatter([700], [22.0], s=180, marker="s", color=P.MUTED,
               edgecolor=P.BG, lw=1.3, zorder=3)
    ax.annotate("LDM (U-Net)", (90, 26.5), xytext=(60, 33),
                color=P.MUTED, fontsize=11)
    ax.annotate("ADM (U-Net)\nmuch more compute", (700, 22.0), xytext=(220, 34),
                color=P.MUTED, fontsize=11,
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.4))

    ax.set_xscale("log")
    ax.set_xlim(4.5, 1400); ax.set_ylim(8, 75)
    ax.invert_yaxis()
    ax.set_xlabel("model compute  —  transformer Gflops / forward  (log)",
                  fontsize=12.5)
    ax.set_ylabel("FID   (lower = better samples)", fontsize=12.5)
    ax.set_title("(a)  bigger DiT → lower FID, on a clean frontier",
                 color=P.INK, fontsize=13.5)
    ax.text(5.2, 12.5, "quality\nfollows\ncompute →", color=ACC, fontsize=12,
            fontweight="bold", va="center")

    # === (b) FID vs training compute — scaling law carries over ============
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    steps = np.logspace(np.log10(50e3), np.log10(7e6), 200)  # 50k → 7M
    r = steps / 50e3
    # DiT-XL/2: smooth power-law descent toward ~10
    dit = 8.0 + 65.0 * r ** (-0.70)
    # U-Net: improves then plateaus around ~16
    unet = 16.0 + 60.0 * r ** (-0.90)
    ax.plot(steps, dit, color=ACC, lw=3.0, label="DiT-XL/2 (transformer)")
    ax.plot(steps, unet, color=P.MUTED, lw=2.6, ls="--",
            label="U-Net baseline")

    ax.scatter([7e6], [dit[-1]], s=160, color=ACC, edgecolor=P.BG, lw=1.5, zorder=5)
    ax.annotate("keeps falling —\nforecastable", (7e6, dit[-1]),
                xytext=(2.2e6, 13.8), color=ACC, fontsize=12, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.7), ha="center")
    ax.annotate("U-Net plateaus", (3.2e6, 16.6), xytext=(2.4e5, 22.5),
                color=P.MUTED, fontsize=11.5, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.5))

    ax.set_xscale("log")
    ax.set_xlim(50e3, 7e6); ax.set_ylim(6, 46)
    ax.invert_yaxis()
    ax.set_xlabel("training compute  —  steps  (log)", fontsize=12.5)
    ax.set_ylabel("FID   (lower = better)", fontsize=12.5)
    ax.set_title("(b)  the scaling law carries over from language",
                 color=P.INK, fontsize=13.5)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11.5, loc="lower right")

    f.text(0.5, 0.038,
           "Stylized, representative values — the SHAPE is the lesson. A hand-tuned "
           "U-Net sputters; a DiT keeps improving along a smooth curve, which is why "
           "SORA, Stable Diffusion 3 and PixArt build on it.",
           ha="center", color=P.INK, fontsize=12.5)

    return P.save(f, "dit-scaling.png")


if __name__ == "__main__":
    print("wrote", fig_scaling())
