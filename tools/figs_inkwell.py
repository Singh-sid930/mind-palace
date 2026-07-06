"""Concept figure for The Inkwell (diffusion wing) — the forward noising march.

A structured distribution melts, step by step, into a standard Gaussian, while
its total spread stays pinned at 1 (variance preservation).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_inkwell.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import palace_fig as P

WING = "amber"
ACC = P.WING[WING]["accent"]   # warm amber
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]
FIRE = P.cmap("fire")


def gauss(x, mu, var):
    return np.exp(-0.5 * (x - mu) ** 2 / var) / np.sqrt(2 * np.pi * var)


def mix_density(x, abar, m, s2):
    """Density of x_t = sqrt(abar)*x0 + sqrt(1-abar)*eps for a symmetric
    two-mode x0 (means +-m, component var s2). Total variance stays 1."""
    v = abar * s2 + (1 - abar)
    return 0.5 * gauss(x, +np.sqrt(abar) * m, v) + 0.5 * gauss(x, -np.sqrt(abar) * m, v)


def main():
    # --- forward schedule (linear beta, DDPM) ----------------------------
    T = 1000
    betas = np.linspace(1e-4, 0.02, T)
    abar = np.cumprod(1 - betas)
    t_axis = np.arange(1, T + 1)

    # a two-mode data distribution engineered to have variance exactly 1
    m, s2 = 0.95, 0.0975            # m^2 + s2 = 1.0
    x = np.linspace(-4, 4, 600)

    # snapshot timesteps chosen where abar hits a staged set of values
    targets = [1.0, 0.6, 0.3, 0.10, 0.02]
    snap_idx = [0] + [int(np.argmin(np.abs(abar - g))) for g in targets[1:]]
    snap_abar = [1.0] + [abar[i] for i in snap_idx[1:]]
    snap_t = [0] + [t_axis[i] for i in snap_idx[1:]]

    # ---------------------------------------------------------------------
    f = plt.figure(figsize=(16.5, 10.2))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 5, height_ratios=[1.05, 0.98],
                        hspace=0.42, wspace=0.30,
                        left=0.055, right=0.975, top=0.855, bottom=0.085)

    P.suptitle(f, "The Inkwell  —  The Forward March: a Droplet Dissolves into the Grey")
    f.text(0.5, 0.912,
           "x_t = √ᾱ_t · x₀ + √(1−ᾱ_t) · ε      —      structure melts, "
           "but the spread never leaves Var = 1  (variance-preserving)",
           ha="center", color=P.MUTED, fontsize=14)

    # --- top row: density snapshots melting to N(0,1) --------------------
    cols = [FIRE(v) for v in np.linspace(0.86, 0.30, 5)]
    ref = gauss(x, 0.0, 1.0)
    for k in range(5):
        ax = f.add_subplot(gs[0, k]); P.style_ax(ax, WING)
        d = mix_density(x, snap_abar[k], m, s2)
        ax.plot(x, ref, color=P.MUTED, ls=(0, (4, 3)), lw=1.4, alpha=0.8)
        ax.plot(x, d, color=cols[k], lw=2.6)
        ax.fill_between(x, d, color=cols[k], alpha=0.28)
        ax.set_ylim(0, 0.74)
        ax.set_xlim(-4, 4)
        ax.set_xticks([-3, 0, 3])
        if k == 0:
            ax.set_ylabel("density", fontsize=12.5)
        else:
            ax.set_yticklabels([])
        stage = "clean data  x₀" if k == 0 else (
            "pure noise  N(0,1)" if k == 4 else "mixing…")
        ax.set_title(f"t = {snap_t[k]}\nᾱ = {snap_abar[k]:.2f}",
                     color=P.INK, fontsize=13)
        ax.text(0.5, 0.965, stage, transform=ax.transAxes, ha="center",
                va="top", color=cols[k] if k != 4 else P.MUTED,
                fontsize=11.5, fontweight="bold")
        ax.text(0.035, 0.90, "Var = 1.00", transform=ax.transAxes, ha="left",
                va="top", color=P.HOT, fontsize=10.5)
        if k == 0:
            ax.text(0.035, 0.80, "dashed = N(0,1)\nendpoint", transform=ax.transAxes,
                    ha="left", va="top", color=P.MUTED, fontsize=9.5, style="italic")

    # --- bottom-left: variance preserved vs naive additive explosion -----
    ax = f.add_subplot(gs[1, 0:2]); P.style_ax(ax, WING)
    naive = 1 + 0.010 * t_axis          # naive: pile on independent noise
    ax.plot(t_axis, naive, color=COOL, lw=2.6, label="naïve add-noise:  Var grows without bound")
    ax.axhline(1.0, color=WARM, lw=3.0, label="DDPM forward:  Var pinned at 1")
    ax.fill_between(t_axis, 0.0, 1.0, color=WARM, alpha=0.10)
    ax.set_ylim(0, 11)
    ax.set_xlim(0, T)
    ax.set_xlabel("timestep  t", fontsize=12.5)
    ax.set_ylabel("Var(x_t)", fontsize=12.5)
    ax.set_title("(a)  Why the √ coefficients: the ink never explodes nor fades",
                 color=P.INK, fontsize=13.5)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11.5, loc="upper left")
    ax.annotate("(1−βₜ)·Var + βₜ  =  1", xy=(T * 0.62, 1.0),
                xytext=(T * 0.42, 3.4), color=WARM, fontsize=12.5,
                fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.8))

    # --- bottom-right: the droplet forgotten — mode centers collapse -----
    ax = f.add_subplot(gs[1, 2:5]); P.style_ax(ax, WING)
    center = np.sqrt(abar) * m
    ax.fill_between(t_axis, center - 1, center + 1, color=COOL, alpha=0.14,
                    label="spread  ±1 std (constant)")
    ax.fill_between(t_axis, -center - 1, -center + 1, color=COOL, alpha=0.14)
    ax.plot(t_axis, center, color=WARM, lw=2.6)
    ax.plot(t_axis, -center, color=WARM, lw=2.6, label="mode centre  ±√ᾱ_t·m")
    ax.axhline(0, color=P.MUTED, ls=":", lw=1.2)
    ax.set_xlim(0, T)
    ax.set_ylim(-2.6, 2.6)
    ax.set_xlabel("timestep  t", fontsize=12.5)
    ax.set_ylabel("value", fontsize=12.5)
    ax.set_title("(b)  The droplet is forgotten: signal centres slide to 0, spread holds",
                 color=P.INK, fontsize=13.5)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=11.5, loc="lower left")
    ax.annotate("√ᾱ_t → 0 : the two modes\nmerge into one N(0,1) cloud",
                xy=(T * 0.93, 0.0), xytext=(T * 0.58, 1.75),
                color=P.INK, fontsize=11.5, ha="center",
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.8))

    return P.save(f, "inkwell-forward-march.png")


if __name__ == "__main__":
    print("wrote", main())
