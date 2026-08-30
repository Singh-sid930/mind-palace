"""Concept figure for The Shortcut Shrine (diffusion wing), the ᾱ shortcut.

β_t (small, rising), α_t = 1−β_t, and the cumulative product ᾱ_t collapsing
toward 0; plus the signal fraction √ᾱ vs noise fraction √(1−ᾱ) seesaw.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_shortcut.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "amber"
ACC = P.WING[WING]["accent"]
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]


def main():
    T = 1000
    betas = np.linspace(1e-4, 0.02, T)     # real DDPM linear schedule
    alphas = 1 - betas
    abar = np.cumprod(alphas)
    t = np.arange(1, T + 1)

    sig = np.sqrt(abar)          # signal fraction  √ᾱ
    noi = np.sqrt(1 - abar)      # noise  fraction  √(1−ᾱ)
    cross = int(np.argmin(np.abs(sig - noi)))   # 50/50 crossover

    f = plt.figure(figsize=(17.0, 8.4))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 3, wspace=0.52,
                        left=0.05, right=0.965, top=0.79, bottom=0.155)

    P.suptitle(f, "The Shortcut Shrine, One Leap Instead of a Thousand Steps")
    f.text(0.5, 0.895,
           "x_t = √ᾱ_t · x₀  +  √(1−ᾱ_t) · ε        with   αₜ = 1−βₜ   and   "
           "ᾱₜ = α₁·α₂·…·αₜ",
           ha="center", color=P.HOT, fontsize=15, fontweight="bold")

    # --- (a) the schedule: β rises, α = 1-β stays near 1 -----------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    ax.plot(t, betas, color=WARM, lw=2.8, label="βₜ  (noise budget)")
    ax.fill_between(t, 0, betas, color=WARM, alpha=0.20)
    ax.set_xlim(0, T)
    ax.set_ylim(0, 0.022)
    ax.set_xlabel("timestep  t", fontsize=12.5)
    ax.set_ylabel("βₜ", fontsize=13, color=WARM)
    ax.tick_params(axis="y", colors=WARM)
    ax.set_title("(a)  βₜ: a schedule, not a number", color=P.INK, fontsize=14)
    ax.annotate("0.0001  →  0.02\n(gentle first, harder later)",
                xy=(T * 0.5, betas[T // 2]), xytext=(T * 0.06, 0.0175),
                color=P.INK, fontsize=11.5,
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.6))

    axb = ax.twinx()
    axb.plot(t, alphas, color=COOL, lw=2.4, ls="--", label="αₜ = 1−βₜ")
    axb.set_ylim(0.97, 1.001)
    axb.set_ylabel("αₜ  (signal kept)", fontsize=11.5, color=COOL)
    axb.tick_params(axis="y", colors=COOL, labelsize=11)
    for s in axb.spines.values():
        s.set_color(P.GRID)
    l1, la1 = ax.get_legend_handles_labels()
    l2, la2 = axb.get_legend_handles_labels()
    ax.legend(l1 + l2, la1 + la2, facecolor=P.PANEL, edgecolor=P.GRID,
              labelcolor=P.INK, fontsize=11, loc="lower right")

    # --- (b) ᾱ_t collapses toward 0 (linear + log twin) ------------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    ax.plot(t, abar, color=ACC, lw=3.0)
    ax.fill_between(t, 0, abar, color=ACC, alpha=0.20)
    ax.set_xlim(0, T)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("timestep  t", fontsize=12.5)
    ax.set_ylabel("ᾱₜ  (linear)", fontsize=13, color=ACC)
    ax.tick_params(axis="y", colors=ACC)
    ax.set_title("(b)  ᾱₜ = running product → collapses to 0",
                 color=P.INK, fontsize=14)
    ax.annotate(f"ᾱ₁₀₀₀ ≈ {abar[-1]:.1e}\n(x₀ all but forgotten)",
                xy=(T, abar[-1]), xytext=(T * 0.34, 0.30),
                color=P.INK, fontsize=11.5,
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.6))

    axl = ax.twinx()
    axl.semilogy(t, abar, color=P.MUTED, lw=1.6, ls=":")
    axl.set_ylabel("ᾱₜ  (log)", fontsize=11.5, color=P.MUTED)
    axl.tick_params(axis="y", colors=P.MUTED, labelsize=10)
    for s in axl.spines.values():
        s.set_color(P.GRID)

    # --- (c) signal vs noise seesaw --------------------------------------
    ax = f.add_subplot(gs[0, 2]); P.style_ax(ax, WING)
    ax.plot(t, sig, color=WARM, lw=3.0, label="signal fraction  √ᾱₜ")
    ax.plot(t, noi, color=COOL, lw=3.0, label="noise  fraction  √(1−ᾱₜ)")
    ax.fill_between(t, 0, sig, color=WARM, alpha=0.16)
    ax.fill_between(t, sig, 1, color=COOL, alpha=0.16)
    ax.axvline(cross, color=P.MUTED, ls=":", lw=1.3)
    ax.plot(cross, sig[cross], "o", color=P.HOT, ms=8, zorder=5)
    ax.set_xlim(0, T)
    ax.set_ylim(0, 1.03)
    ax.set_xlabel("timestep  t", fontsize=12.5)
    ax.set_ylabel("fraction", fontsize=12.5)
    ax.set_title("(c)  The seesaw: √ᾱₜ² + √(1−ᾱₜ)² = 1",
                 color=P.INK, fontsize=14)
    ax.annotate(f"50 / 50  at  t ≈ {t[cross]}", xy=(cross, sig[cross]),
                xytext=(cross - 40, 0.62), color=P.HOT, fontsize=11.5,
                fontweight="bold", ha="right",
                arrowprops=dict(arrowstyle="-|>", color=P.HOT, lw=1.6))
    ax.text(0.03, 0.06, "all signal", transform=ax.transAxes, color=WARM,
            fontsize=11, fontweight="bold")
    ax.text(0.97, 0.94, "all noise", transform=ax.transAxes, color=COOL,
            fontsize=11, fontweight="bold", ha="right", va="top")
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11, loc="center left")

    f.text(0.5, 0.045,
           "Precompute the whole schedule once; then jumping to ANY step t is two "
           "lookups (√ᾱₜ, √(1−ᾱₜ)) and a single draw of ε, no thousand-step chain.",
           ha="center", color=P.INK, fontsize=12.5)

    return P.save(f, "shortcut-alpha-bar.png")


if __name__ == "__main__":
    print("wrote", main())
