"""Concept figure for The Rank Dial (LoRA wing, obsidian palette).

Choosing r (the plateau) and the alpha/r scaling that decouples update
magnitude from rank.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_rankdial.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "obsidian"
ACC = P.WING[WING]["accent"]   # teal glow
WARM = P.WING[WING]["warm"]    # gold
COOL = P.WING[WING]["cool"]    # muted teal


def fig_rank_alpha():
    ranks = np.array([2, 4, 8, 16, 32, 64])
    xi = np.arange(len(ranks))                 # even spacing, log-like axis
    # validation performance: rises, then plateaus at r ~ 16
    val = np.array([0.60, 0.73, 0.85, 0.905, 0.907, 0.900])
    plateau_i = 3                              # r = 16

    f = plt.figure(figsize=(16.5, 8.0))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.0, 1.0],
                        left=0.065, right=0.955, top=0.83, bottom=0.12,
                        wspace=0.24)

    P.suptitle(f, "The Plateau Found, turn the dial to the smallest r that "
                  "clears the elbow, set α apart")
    f.text(0.5, 0.895,
           "representative sweep, the SHAPE is the lesson: r sets how many "
           "directions, α sets how loud",
           ha="center", color=P.MUTED, fontsize=13)

    # -- (a) rank sweep -> plateau -------------------------------------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    # shaded regions
    ax.axvspan(-0.4, plateau_i - 0.5, color=WARM, alpha=0.10, zorder=0)
    ax.axvspan(plateau_i + 0.5, len(ranks) - 0.6, color=COOL, alpha=0.10, zorder=0)
    ax.text(0.75, 0.635, "UNDERFIT\nr too small, \ncan't capture\nthe update",
            color=WARM, fontsize=11.5, ha="center", va="center",
            fontweight="bold", linespacing=1.4)
    ax.text(4.5, 0.72, "DIMINISHING RETURNS\nr too large, more params,\n"
            "compute, overfit risk;\nno better than full tune",
            color=COOL, fontsize=11.5, ha="center", va="center",
            fontweight="bold", linespacing=1.4)

    ax.plot(xi, val, color=ACC, lw=2.6, marker="o", ms=10,
            markerfacecolor=P.BG, markeredgecolor=ACC, markeredgewidth=2.2,
            zorder=4)
    # plateau marker
    ax.axvline(plateau_i, color=P.INK, ls="--", lw=1.6, zorder=2)
    ax.scatter([plateau_i], [val[plateau_i]], s=200, color=ACC,
               edgecolor=P.INK, linewidth=2, zorder=6)
    ax.annotate("smallest r where\nvalidation PLATEAUS\n→ pick r ≈ 16",
                xy=(plateau_i, val[plateau_i]),
                xytext=(plateau_i - 1.55, 0.80),
                color=P.INK, fontsize=12.5, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="-|>", color=P.INK, lw=1.8),
                bbox=dict(boxstyle="round,pad=0.35", fc=P.PANEL, ec=ACC, lw=1.4))
    # bracket showing flat plateau
    ax.annotate("", xy=(plateau_i, 0.928), xytext=(len(ranks) - 1, 0.928),
                arrowprops=dict(arrowstyle="<->", color=P.MUTED, lw=1.4))
    ax.text((plateau_i + len(ranks) - 1) / 2, 0.945, "flat, no gain",
            color=P.MUTED, fontsize=11, ha="center", style="italic")

    ax.set_xticks(xi)
    ax.set_xticklabels([f"r={r}" for r in ranks], fontsize=12.5)
    ax.set_ylim(0.55, 0.97)
    ax.set_xlim(-0.4, len(ranks) - 0.6)
    ax.set_xlabel("rank  r  (swept, doubling)", fontsize=13)
    ax.set_ylabel("validation performance", fontsize=13)
    ax.set_title("(a)  Sweep r, watch validation, take the smallest on the plateau",
                 color=P.INK, fontsize=13.5, pad=10)

    # -- (b) alpha / r scaling -----------------------------------------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    rr = np.array([2, 4, 8, 16, 32, 64], float)
    xj = np.arange(len(rr))
    # The scaling coefficient (alpha/r) that multiplies B·A. It sets how loudly
    # the adapter speaks; the convention alpha = r (or 2r) holds it STEADY as r
    # changes, while a FIXED alpha (no ÷r tie) lurches with every turn of r.
    eff_alpha_eq_r = np.full_like(rr, 1.0)     # alpha = r   -> alpha/r = 1
    eff_alpha_2r = np.full_like(rr, 2.0)       # alpha = 2r  -> alpha/r = 2
    eff_fixed = 16.0 / rr                       # fixed alpha = 16 -> lurches

    ax.plot(xj, eff_fixed, color=P.MUTED, lw=2.2, ls=":", marker="^", ms=9,
            zorder=3, markerfacecolor=P.BG, markeredgecolor=P.MUTED,
            markeredgewidth=1.8)
    ax.plot(xj, eff_alpha_2r, color=ACC, lw=2.6, marker="o", ms=10, zorder=4,
            markerfacecolor=P.BG, markeredgecolor=ACC, markeredgewidth=2.2)
    ax.plot(xj, eff_alpha_eq_r, color=WARM, lw=2.6, marker="s", ms=9, zorder=4,
            markerfacecolor=P.BG, markeredgecolor=WARM, markeredgewidth=2.2)

    ax.text(xj[-1], 1.0 + 0.35, "α = r   →  α/r = 1  (scale steady)",
            color=WARM, fontsize=12.5, fontweight="bold", ha="right", va="bottom")
    ax.text(xj[-1], 2.0 + 0.35, "α = 2r  →  α/r = 2  (steady, louder)",
            color=ACC, fontsize=12.5, fontweight="bold", ha="right", va="bottom")
    ax.annotate("fixed α (rank NOT tied in):\nα/r LURCHES with every r, \n"
                "raise r and the update\nquietly changes strength",
                xy=(0, eff_fixed[0]), xytext=(1.05, 6.4),
                color=P.MUTED, fontsize=11.5, ha="left", fontweight="bold",
                linespacing=1.4,
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.6))

    ax.set_xticks(xj)
    ax.set_xticklabels([f"r={int(r)}" for r in rr], fontsize=12.5)
    ax.set_ylim(0, 8.6)
    ax.set_xlabel("rank  r  (changing the dial)", fontsize=13)
    ax.set_ylabel("update strength, the (α/r) factor on B·A", fontsize=13)
    ax.set_title("(b)  The α/r factor decouples magnitude from rank",
                 color=P.INK, fontsize=13.5, pad=10)
    ax.text(0.5, -0.165,
            "W_new = W + (α/r)·B·A     ·     α = the ComfyUI strength slider",
            transform=ax.transAxes, ha="center", color=ACC, fontsize=12.5,
            fontweight="bold")

    return f


if __name__ == "__main__":
    f = fig_rank_alpha()
    print(P.save(f, "lora-rank-alpha.png"))
