"""Concept figures for The Compass and the Clock (positional encoding).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_compass.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import palace_fig as P


def freqs(d):
    """freq_i = 1 / 10000^(2i/d) for pair index i = 0..d/2-1."""
    i = np.arange(d // 2)
    return 1.0 / (10000.0 ** (2.0 * i / d))


# ---------------------------------------------------------------------------
# FIGURE 1 — Sinusoidal positional encoding
# ---------------------------------------------------------------------------
def fig_sinusoidal():
    d = 64
    L = 64
    pos = np.arange(L)
    fr = freqs(d)  # length d/2

    # PE[pos, 2i] = sin(pos*freq_i); PE[pos, 2i+1] = cos(pos*freq_i)
    PE = np.zeros((L, d))
    ang = np.outer(pos, fr)            # (L, d/2)
    PE[:, 0::2] = np.sin(ang)
    PE[:, 1::2] = np.cos(ang)

    f, (axA, axB) = P.fig(13.5, 6.2, wing="sapphire", ncols=2,
                          gridspec_kw={"width_ratios": [1.15, 1.0],
                                       "wspace": 0.28})
    P.suptitle(f, "Sinusoidal Positional Encoding  —  a clock of many hands")

    # (a) heatmap: x = position, y = dimension
    im = axA.imshow(PE.T, aspect="auto", origin="lower",
                    cmap=P.cmap("heat"), vmin=-1, vmax=1,
                    extent=[0, L - 1, 0, d - 1])
    axA.set_title("(a) PE[pos, dim]   ADDED to token embeddings", fontsize=14)
    axA.set_xlabel("position  (0 … 63)", fontsize=13)
    axA.set_ylabel("embedding dimension  (0 … 63)", fontsize=13)
    axA.grid(False)
    cb = f.colorbar(im, ax=axA, fraction=0.046, pad=0.02)
    cb.set_label("value", color=P.INK, fontsize=11)
    cb.ax.yaxis.set_tick_params(color=P.MUTED, labelsize=10)
    cb.ax.yaxis.set_tick_params(labelcolor=P.MUTED)
    cb.outline.set_edgecolor(P.GRID)

    # (b) a few dimension curves vs position: fast (low dim) vs slow (high dim)
    sel = [(0, "dim 0  sin, freq 1.00  — fast 'second-hand'", P.WING["sapphire"]["accent"]),
           (8, "dim 8  sin, freq 0.10  — minute-hand", P.HOT),
           (40, "dim 40 sin, freq 0.0006 — slow 'hour-hand'", P.WING["sapphire"]["cool"])]
    fine = np.linspace(0, L - 1, 600)
    for dim, lab, c in sel:
        pair = dim // 2
        y = np.sin(fine * fr[pair])
        axB.plot(fine, y, color=c, lw=2.4, label=lab)
    axB.set_title("(b) one frequency per dimension pair", fontsize=14)
    axB.set_xlabel("position", fontsize=13)
    axB.set_ylabel("sin(pos · freq)", fontsize=13)
    axB.set_xlim(0, L - 1)
    axB.set_ylim(-1.18, 1.18)
    leg = axB.legend(loc="lower center", fontsize=10.0, facecolor=P.PANEL,
                     edgecolor=P.GRID, framealpha=0.95, ncol=1)
    for t in leg.get_texts():
        t.set_color(P.INK)
    axB.text(0.5, -0.30,
             "freq_i = 1 / 10000^(2i/d)   ·   encodes ABSOLUTE position",
             transform=axB.transAxes, ha="center", va="top",
             fontsize=11.5, color=P.MUTED, style="italic")

    return P.save(f, "sinusoidal-pe.png")


# ---------------------------------------------------------------------------
# FIGURE 2 — RoPE: rotation carries relative distance
# ---------------------------------------------------------------------------
def fig_rope():
    f, (axA, axB) = P.fig(13.5, 6.2, wing="sapphire", ncols=2,
                          gridspec_kw={"wspace": 0.30})
    P.suptitle(f, "RoPE  —  rotation encodes RELATIVE distance")

    # (a) a query vector rotated by m*theta at several positions m
    q = np.array([3.0, 1.0])
    theta = np.deg2rad(35.0)         # angle per position step
    axA.set_title("(a) rotate q by m·θ   (length preserved)", fontsize=14)
    R = np.hypot(*q)
    # draw the circle the tip travels on
    tt = np.linspace(0, 2 * np.pi, 400)
    axA.plot(R * np.cos(tt), R * np.sin(tt), color=P.GRID, lw=1.0, alpha=0.8)

    cols = [P.WING["sapphire"]["accent"], P.HOT,
            P.WING["sapphire"]["cool"], "#e08a9a"]
    for k, m in enumerate([0, 1, 2, 3]):
        a = m * theta
        Rm = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        v = Rm @ q
        c = cols[k]
        axA.annotate("", xy=(v[0], v[1]), xytext=(0, 0),
                     arrowprops=dict(arrowstyle="-|>", color=c, lw=2.6))
        axA.text(v[0] * 1.12, v[1] * 1.12, f"m={m}", color=c,
                 fontsize=12.5, ha="center", va="center", fontweight="bold")
    axA.set_xlim(-R * 1.35, R * 1.35)
    axA.set_ylim(-R * 1.35, R * 1.35)
    axA.set_aspect("equal")
    axA.axhline(0, color=P.GRID, lw=0.8)
    axA.axvline(0, color=P.GRID, lw=0.8)
    axA.set_xlabel("dim 0", fontsize=13)
    axA.set_ylabel("dim 1", fontsize=13)
    axA.text(0.5, -0.20, "|q| constant  ·  applied AFTER projection, to Q and K only",
             transform=axA.transAxes, ha="center", va="top",
             fontsize=11.5, color=P.MUTED, style="italic")

    # (b) dot product of q@m and k@n depends only on (m-n)
    # q.k after rotation = |q||k| cos(angle(q,k) + (m-n)theta)
    # Take q=k same direction so it's a clean cosine of relative offset.
    qv = np.array([3.0, 1.0])
    kv = np.array([3.0, 1.0])
    base = np.dot(qv, kv)            # |q||k| cos(0) for aligned vectors
    rel = np.linspace(-12, 12, 600)
    dp = base * np.cos(rel * theta)
    axB.plot(rel, dp, color=P.WING["sapphire"]["accent"], lw=2.6)
    axB.axhline(0, color=P.GRID, lw=0.8)
    axB.axvline(0, color=P.GRID, lw=0.8)

    # mark integer relative offsets
    rint = np.arange(-12, 13)
    axB.scatter(rint, base * np.cos(rint * theta), s=22,
                color=P.HOT, zorder=5)
    axB.set_title("(b) score q·k depends only on (m − n)", fontsize=14)
    axB.set_xlabel("relative distance   m − n", fontsize=13)
    axB.set_ylabel("q·k  (rotated)", fontsize=13)
    axB.set_xlim(-12, 12)
    axB.text(0.5, -0.20,
             "cos A cos B + sin A sin B = cos(A−B)  →  absolute m, n cancel",
             transform=axB.transAxes, ha="center", va="top",
             fontsize=11.5, color=P.MUTED, style="italic")

    return P.save(f, "rope-rotation.png")


if __name__ == "__main__":
    print(fig_sinusoidal())
    print(fig_rope())
