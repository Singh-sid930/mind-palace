"""Concept figure for The Stitcher's Table (video wing).

Wan length extension: autoregressive chunking with overlap, the drift that
accumulates chunk over chunk, and how overlap-conditioning compares with a
naive cut (with the three extension approaches noted).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_stitch.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import palace_fig as P

WING = "silver"
ACC = P.WING[WING]["accent"]   # cool silver
WARM = P.WING[WING]["warm"]    # muted gold
COOL = P.WING[WING]["cool"]    # moonlit blue
BAD = "#d98a7a"                # warm rust for drift / seams


def fig_chunk_extension():
    f = plt.figure(figsize=(16.0, 7.8))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.25, 1.0],
                        wspace=0.20, left=0.06, right=0.975,
                        top=0.80, bottom=0.135)

    P.suptitle(f, "The Stitcher's Table, chunk-and-overlap extension, and the drift it inherits", wing=WING)
    f.text(0.5, 0.885,
           "Wan is trained for ~81 frames (~5s).  Longer video = short chunks stitched, each conditioned on the "
           "OVERLAP TAIL of the one before, and drift compounds down the chain.",
           ha="center", color=P.MUTED, fontsize=12.5)

    # (a) autoregressive chunk timeline with overlap and growing drift -----------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    L = 81            # trained chunk length (frames)
    ov = 11           # overlap tail
    stride = L - ov   # 70
    n = 4
    ys = [4, 3, 2, 1]
    starts = [1 + k * stride for k in range(n)]   # 1, 71, 141, 211
    h = 0.6

    for k in range(n):
        s0 = starts[k]
        y = ys[k]
        # the chunk body
        ax.add_patch(Rectangle((s0, y - h / 2), L, h, linewidth=1.4,
                     edgecolor=P.GRID, facecolor=COOL, alpha=0.85))
        ax.text(s0 + L / 2 - ov / 2, y, f"chunk {k+1}\n{s0}, {s0+L-1}",
                ha="center", va="center", color=P.BG, fontsize=11.5,
                fontweight="bold")

        # overlap tail shared with the next chunk
        if k < n - 1:
            ax.add_patch(Rectangle((s0 + L - ov, y - h / 2), ov, h, linewidth=0,
                         facecolor=WARM, alpha=0.95))
            # arrow: tail conditions the next chunk
            arr = FancyArrowPatch((s0 + L - ov / 2, y - h / 2 - 0.02),
                                  (starts[k + 1] + ov / 2, ys[k + 1] + h / 2 + 0.02),
                                  arrowstyle="-|>", mutation_scale=16,
                                  color=WARM, lw=1.8,
                                  connectionstyle="arc3,rad=-0.15")
            ax.add_patch(arr)

        # drift whisker at the trailing edge, grows chunk over chunk
        drift = 0.06 + 0.14 * k
        ax.errorbar(s0 + L, y, yerr=drift, color=BAD, elinewidth=3.2,
                    capsize=5, capthick=2.2, zorder=5)

    # labels placed in the open upper-right quadrant
    ax.annotate("overlap tail\n(shared frames)", xy=(starts[0] + L - ov / 2, ys[0]),
                xytext=(118, 4.55), color=WARM, fontsize=11, ha="left",
                va="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=WARM, lw=1.4))
    ax.annotate("each new chunk conditioned\non the previous tail",
                xy=(starts[1] + ov / 2, ys[1] + h / 2), xytext=(200, 4.0),
                color=P.INK, fontsize=11, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=P.MUTED, lw=1.3))
    ax.annotate("drift band grows\nchunk over chunk", xy=(starts[3] + L, ys[3]),
                xytext=(150, 1.35), color=BAD, fontsize=11, ha="left",
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=BAD, lw=1.4))

    ax.axvspan(1, L, ymin=0.02, ymax=0.98, color=COOL, alpha=0.06)
    ax.text(L / 2 - ov / 2, 4.6, "within T_max", color=ACC, fontsize=10.5,
            ha="center")

    ax.set_xlim(-10, starts[-1] + L + 20)
    ax.set_ylim(0.3, 5.0)
    ax.set_yticks([])
    ax.set_xlabel("frame index  (video timeline)", fontsize=12.5)
    ax.set_title("(a)  Autoregressive chunking with overlap", color=P.INK)
    for sp in ("left", "right", "top"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(P.GRID)
    ax.tick_params(colors=P.MUTED, labelsize=11)

    # (b) drift vs number of chunks: overlap-conditioning vs naive cut -----------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    chunks = np.arange(1, 9)
    # overlap-conditioning: smooth, sub-linear compounding
    drift_ov = 0.10 * (chunks - 1) ** 1.15
    # naive cut (no overlap): steeper, with a seam jump at every join
    drift_cut = 0.30 * (chunks - 1) + 0.22 * (chunks - 1) ** 1.2

    ax.plot(chunks, drift_ov, "-o", color=ACC, lw=2.6, markersize=6,
            label="overlap-conditioning (chunk-and-overlap)")
    ax.plot(chunks, drift_cut, "-s", color=BAD, lw=2.6, markersize=6,
            label="naive cut (no overlap), visible seams")
    ax.fill_between(chunks, drift_ov, drift_cut, color=BAD, alpha=0.08)

    ax.axhline(1.0, color=P.MUTED, ls=":", lw=1.2)
    ax.text(1.1, 1.03, "coherence breaks (~10s)", color=P.MUTED, fontsize=10,
            va="bottom")

    ax.set_xlim(0.7, 8.3)
    ax.set_ylim(0, max(drift_cut) * 1.08)
    ax.set_xlabel("number of stitched chunks", fontsize=12.5)
    ax.set_ylabel("accumulated drift  (representative)", fontsize=12.5)
    ax.set_title("(b)  Overlap-conditioning drifts slower than a naive cut", color=P.INK)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=10.5, loc="upper left")
    ax.text(0.5, -0.205,
            "Also: fine-tuned continuation models train the handover in;  "
            "sliding-window overlap blurs on DYNAMIC motion.",
            transform=ax.transAxes, ha="center", color=ACC, fontsize=11,
            fontweight="bold")

    return P.save(f, "video-chunk-extension.png")


if __name__ == "__main__":
    print("wrote", fig_chunk_extension())
