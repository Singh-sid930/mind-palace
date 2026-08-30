"""Concept figure for The Reel of Lengths (video wing).

Variable-length generation and degradation past the trained horizon, and the
varied-length training that makes variable-length inference possible.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_reel.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "silver"
ACC = P.WING[WING]["accent"]   # cool silver
WARM = P.WING[WING]["warm"]    # muted gold
COOL = P.WING[WING]["cool"]    # moonlit blue


def quality_curve(x, plateau=1.0, drop=0.42, power=1.35):
    """High, flat within the trained horizon (x<=1), gradual drift beyond."""
    over = np.clip(x - 1.0, 0.0, None)
    q = np.where(x <= 1.0, plateau, plateau - drop * over ** power)
    return np.clip(q, 0.0, 1.0)


def fig_length_degradation():
    f = plt.figure(figsize=(15.5, 7.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.15, 1.0],
                        wspace=0.24, left=0.065, right=0.975,
                        top=0.80, bottom=0.135)

    P.suptitle(f, "The Reel of Lengths, variable length, and the drift beyond the horizon", wing=WING)
    f.text(0.5, 0.885,
           "Frame count T is a sequence length, not a fixed weight, so quality holds within the trained span, "
           "then drifts.  The same curve governs an LLM past its context.",
           ha="center", color=P.MUTED, fontsize=13)

    # (a) quality vs length: twin video / LLM curves, shared trained horizon -----
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    x = np.linspace(0.0, 2.9, 400)           # length in multiples of the trained horizon
    q_vid = quality_curve(x, plateau=1.0, drop=0.46, power=1.4)
    q_llm = quality_curve(x, plateau=0.965, drop=0.40, power=1.55)

    ax.axvspan(0, 1.0, color=COOL, alpha=0.09)
    ax.axvline(1.0, color=WARM, ls="--", lw=2.0)
    ax.text(1.02, 1.08, "trained horizon (T_max)", color=WARM, fontsize=12.5,
            fontweight="bold", ha="center")

    ax.plot(x, q_vid, color=ACC, lw=3.0, label="video: quality vs generated length")
    ax.plot(x, q_llm, color=WARM, lw=2.4, ls=(0, (5, 2)),
            label="LLM: quality vs context length")

    ax.text(0.5, 0.5, "within span:\nframes stay\nconsistent", color=P.INK,
            fontsize=11.5, ha="center", va="center")
    ax.annotate("past the horizon:\ndrift, degradation,\na face stops being itself",
                xy=(2.05, quality_curve(np.array([2.05]), drop=0.46, power=1.4)[0]),
                xytext=(1.72, 0.32), color=P.INK, fontsize=11, ha="center",
                arrowprops=dict(arrowstyle="->", color=P.MUTED, lw=1.4))

    ax.set_xlim(0, 2.9); ax.set_ylim(0, 1.14)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["0", "T_max\n(~81 fr / ~5s)", "2 x T_max"], fontsize=11.5)
    ax.set_xlabel("generated length  (multiples of the trained horizon)", fontsize=12.5)
    ax.set_ylabel("temporal coherence  (quality)", fontsize=12.5)
    ax.set_title("(a)  Same-shaped fall: video length = LLM context", color=P.INK)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11, loc="lower left")

    # (b) varied-length training histogram ---------------------------------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    # representative training-clip length distribution: a spike of stills at T=1,
    # then broad coverage of clip lengths up to T_max = 81 frames.
    edges = np.array([1, 9, 17, 25, 33, 41, 49, 57, 65, 73, 81])
    centers = (edges[:-1] + edges[1:]) / 2
    counts = np.array([34, 12, 15, 17, 18, 19, 20, 21, 23, 27], float)  # representative

    bars = ax.bar(centers, counts, width=7.2, color=COOL, edgecolor=P.GRID,
                  align="center")
    bars[0].set_color(WARM)          # highlight the T=1 stills bucket
    ax.annotate("T = 1\nstatic images", xy=(centers[0], counts[0]),
                xytext=(centers[0] + 9, counts[0] + 1.5), color=WARM,
                fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=WARM, lw=1.4))

    ax.axvline(81, color=WARM, ls="--", lw=2.0)
    ax.text(81, counts.max() * 1.06, "T_max = 81 fr", color=WARM,
            fontsize=11.5, fontweight="bold", ha="right")

    ax.set_xlim(-3, 92); ax.set_ylim(0, counts.max() * 1.2)
    ax.set_xlabel("training-clip length T  (frames)", fontsize=12.5)
    ax.set_ylabel("share of training clips  (representative)", fontsize=12.5)
    ax.set_title("(b)  Clips of varied length, T = 1 up to T_max", color=P.INK)
    ax.text(0.5, -0.205,
            "Varied-length training is what enables variable-length inference.",
            transform=ax.transAxes, ha="center", color=ACC, fontsize=12.5,
            fontweight="bold")

    return P.save(f, "video-length-degradation.png")


if __name__ == "__main__":
    print("wrote", fig_length_degradation())
