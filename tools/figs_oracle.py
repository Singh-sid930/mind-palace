"""Concept figure for The Noise Oracle (diffusion wing) — one training step.

Pick a t, mix a clean rune with known noise ε, the network predicts ε̂, and the
loss is ‖ε − ε̂‖². Shown as a row of panels over a simple 16×16 rune.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_oracle.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch
import palace_fig as P

WING = "amber"
ACC = P.WING[WING]["accent"]
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]
FIRE = P.cmap("fire")
# signed diverging map for the noise fields: cool → dark → warm
DIV = LinearSegmentedColormap.from_list(
    "amberdiv", ["#7fa8e0", "#3a5675", "#141c27", "#7a4a24", "#ffb04a"])


def make_rune(n=16):
    """A simple angular rune drawn on an n×n grid, values in [0,1]."""
    g = np.zeros((n, n))
    def line(r0, c0, r1, c1, w=1.2):
        for a in np.linspace(0, 1, 200):
            r = r0 + a * (r1 - r0)
            c = c0 + a * (c1 - c0)
            rr = np.arange(n)[:, None]
            cc = np.arange(n)[None, :]
            g[:] = np.maximum(g, np.exp(-((rr - r) ** 2 + (cc - c) ** 2) / (2 * w ** 2)))
    # a rune: vertical stave + two diagonal arms
    line(2, 8, 13, 8)          # stave
    line(2, 8, 6, 3)           # upper-left arm
    line(7, 8, 12, 13)         # lower-right arm
    line(2, 8, 5, 13)          # upper-right arm
    g = g / g.max()
    return g * 2 - 1           # center to [-1, 1] like normalized data


def main():
    rng = np.random.default_rng(7)
    n = 16
    x0 = make_rune(n)

    # --- one training step ------------------------------------------------
    t = 400
    abar = 0.45                       # ᾱ_t at this timestep (illustrative)
    sa, sn = np.sqrt(abar), np.sqrt(1 - abar)
    eps = rng.standard_normal((n, n))            # the TRUE noise (the label)
    xt = sa * x0 + sn * eps                      # corrupted sample

    # a plausible network prediction: close to eps but imperfect
    smooth = (eps + np.roll(eps, 1, 0) + np.roll(eps, 1, 1)) / 3
    eps_hat = 0.82 * eps + 0.18 * smooth + 0.12 * rng.standard_normal((n, n))
    err = (eps - eps_hat) ** 2
    mse = err.mean()

    f = plt.figure(figsize=(17.5, 7.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 5, wspace=0.30,
                        left=0.035, right=0.985, top=0.72, bottom=0.135)

    P.suptitle(f, "The Noise Oracle  —  One Turn of the Globe (a single training step)")
    f.text(0.5, 0.855,
           f"Draw t = {t}  ·  ᾱ_t = {abar:.2f}  →  build  x_t = √ᾱ_t·x₀ + "
           f"√(1−ᾱ_t)·ε   ·   the Oracle sees only (x_t, t) and names the noise",
           ha="center", color=P.MUTED, fontsize=13.5)

    def panel(k, M, title, cmap, sub, vlim=None):
        ax = f.add_subplot(gs[0, k]); P.style_ax(ax, WING, grid=False)
        if vlim is None:
            vlim = np.max(np.abs(M))
        if cmap is FIRE:
            im = ax.imshow(M, cmap=cmap, vmin=-1, vmax=1)
        else:
            im = ax.imshow(M, cmap=cmap, vmin=-vlim, vmax=vlim)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(P.GRID); s.set_linewidth(1.4)
        ax.set_title(title, color=P.INK, fontsize=13.5, pad=8)
        ax.text(0.5, -0.10, sub, transform=ax.transAxes, ha="center",
                va="top", color=P.MUTED, fontsize=11.5)
        return ax

    a0 = panel(0, x0, "clean rune  x₀", FIRE, "a datum from the dataset")
    a1 = panel(1, xt, "noised  x_t", FIRE, f"√ᾱ·x₀ + √(1−ᾱ)·ε   (t={t})")
    vl = max(np.max(np.abs(eps)), np.max(np.abs(eps_hat)))
    a2 = panel(2, eps, "TRUE noise  ε", DIV, "the very ε used to corrupt →\nis the free label", vlim=vl)
    a3 = panel(3, eps_hat, "predicted  ε̂ = net(x_t, t)", DIV, "the Oracle's guess", vlim=vl)
    a4 = panel(4, err, "squared error  (ε − ε̂)²", P.cmap("heat"), "The Scales of Error")

    # big MSE readout under the last panel
    a4.text(0.5, 1.14, f"Loss = ‖ε − ε̂‖²  =  {mse:.3f}", transform=a4.transAxes,
            ha="center", va="bottom", color=P.HOT, fontsize=14, fontweight="bold")

    # flow arrows between panels
    def arrow(a, b, label=None):
        x0f = a.get_position().x1
        x1f = b.get_position().x0
        ym = (a.get_position().y0 + a.get_position().y1) / 2
        arr = FancyArrowPatch((x0f + 0.004, ym), (x1f - 0.004, ym),
                              transform=f.transFigure, arrowstyle="-|>",
                              mutation_scale=22, color=ACC, lw=2.2, clip_on=False)
        f.add_artist(arr)
        if label:
            f.text((x0f + x1f) / 2, ym + 0.045, label, ha="center",
                   color=ACC, fontsize=11, fontweight="bold")

    arrow(a0, a1, "mix ε")
    arrow(a2, a3, "learn")

    # brace the true/pred pair as "compared"
    f.text((a2.get_position().x0 + a3.get_position().x1) / 2, 0.045,
           "The corruption hands over its own answer key: the ε that noised the "
           "rune IS the target. Backprop nudges every weight a hair toward ε.",
           ha="center", color=P.INK, fontsize=12.5)

    return P.save(f, "oracle-training-step.png")


if __name__ == "__main__":
    print("wrote", main())
