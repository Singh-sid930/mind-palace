"""Concept figure for The Backward Walk (diffusion wing) — reverse sampling.

A 2D point cloud walked backward from pure Gaussian noise (x_T) to a structured
shape (two moons) across denoise snapshots t = T … 0, with the flow direction
and the fresh-noise kick annotated.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_backward.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import palace_fig as P

WING = "amber"
ACC = P.WING[WING]["accent"]
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]
FIRE = P.cmap("fire")


def two_moons(n, rng, noise=0.06):
    k = n // 2
    t1 = np.linspace(0, np.pi, k)
    t2 = np.linspace(0, np.pi, n - k)
    m1 = np.c_[np.cos(t1), np.sin(t1)]
    m2 = np.c_[1 - np.cos(t2), 0.5 - np.sin(t2)]
    X = np.vstack([m1, m2])
    X += rng.normal(0, noise, X.shape)
    X -= X.mean(0)
    X /= X.std(0)                 # normalize to ~unit variance per axis
    return X


def main():
    rng = np.random.default_rng(3)
    n = 900
    target = two_moons(n, rng)
    eps = rng.standard_normal((n, 2))

    # snapshots from pure noise (abar≈0, left) to clean (abar=1, right)
    T = 1000
    abar_snap = [0.0, 0.15, 0.45, 0.80, 1.0]
    t_snap = [1000, 700, 400, 150, 0]

    # shared point colour = distance from origin at the CLEAN target,
    # so the two moons are legible even inside the noise
    hue = (target[:, 0] - target[:, 0].min())
    hue = hue / hue.max()

    f = plt.figure(figsize=(17.5, 8.2))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 5, wspace=0.14,
                        left=0.03, right=0.985, top=0.74, bottom=0.15)

    P.suptitle(f, "The Backward Walk  —  From Pure Noise, an Image is Un-Mixed")
    f.text(0.5, 0.87,
           "Generation runs the arrow of time backward:  x_T ~ N(0,1)  →  "
           "x_{T-1}  →  …  →  x₀      predict ε̂, rearrange to x₀_est, step one rung down",
           ha="center", color=P.MUTED, fontsize=13.5)

    lims = 3.0
    for k in range(5):
        ax = f.add_subplot(gs[0, k]); P.style_ax(ax, WING, grid=False)
        a = abar_snap[k]
        pts = np.sqrt(a) * target + np.sqrt(1 - a) * eps
        ax.scatter(pts[:, 0], pts[:, 1], c=hue, cmap=FIRE, s=9,
                   alpha=0.85, edgecolors="none")
        ax.set_xlim(-lims, lims); ax.set_ylim(-lims, lims)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_aspect("equal")
        for s in ax.spines.values():
            s.set_color(P.GRID); s.set_linewidth(1.4)
        stage = ("x_T : pure N(0,1)" if k == 0 else
                 "x₀ : clean sample" if k == 4 else "denoising…")
        ax.set_title(f"t = {t_snap[k]}\nᾱ = {a:.2f}", color=P.INK, fontsize=13)
        col = COOL if k == 0 else (WARM if k == 4 else P.MUTED)
        ax.text(0.5, -0.075, stage, transform=ax.transAxes, ha="center",
                va="top", color=col, fontsize=12, fontweight="bold")

    # big directional arrow beneath the row (walk backward T → 0)
    y = 0.085
    arr = FancyArrowPatch((0.10, y), (0.90, y), transform=f.transFigure,
                          arrowstyle="-|>", mutation_scale=28, color=ACC,
                          lw=2.6, clip_on=False)
    f.add_artist(arr)
    f.text(0.5, y + 0.028,
           "each rung: predict ε̂ → estimate x₀ → re-noise to t−1  +  a small "
           "fresh N(0,1) kick  (dropped only at the final step to x₀)",
           ha="center", color=P.INK, fontsize=12.5)
    f.text(0.5, y - 0.035, "reverse walk  (T → 0)", ha="center", color=ACC,
           fontsize=12, fontweight="bold")

    return P.save(f, "backward-walk-moons.png")


if __name__ == "__main__":
    print("wrote", main())
