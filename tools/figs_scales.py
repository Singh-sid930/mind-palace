"""Concept figures for The Scales of Error (Wing of Arithmancy, violet).

Pure mathematics only: the squared-error parabola with a gradient-descent path
walking downhill (shrinking strides), and a panel contrasting |error| with
error² (why big mistakes dominate).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_scales.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
import palace_fig as P

WING = "violet"
ACC = P.WING[WING]["accent"]
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]


def fig_parabola_and_descent():
    f = plt.figure(figsize=(16.6, 8.2))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.15, 1.0],
                        wspace=0.19, left=0.06, right=0.975,
                        top=0.82, bottom=0.115)

    P.suptitle(f, "Squared Error & the Walk Downhill:   loss = (prediction − target)²")
    f.text(0.5, 0.895,
           "Follow the slope of the parabola downhill in shrinking steps; "
           "squaring makes big mistakes dominate the bill.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- panel (a): parabola + gradient descent path ---------------------
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING)
    # loss(w) = (w - target)^2, target = 0 for clean centering
    w = np.linspace(-3.3, 3.3, 600)
    loss = w ** 2
    ax.plot(w, loss, color=ACC, lw=2.8, zorder=4)
    ax.fill_between(w, 0, loss, color=ACC, alpha=0.07, zorder=2)

    lr = 0.28
    p = 3.0
    xs = [p]
    for _ in range(7):
        grad = 2 * p          # d/dw (w²) = 2w
        p = p - lr * grad
        xs.append(p)
    xs = np.array(xs)
    ys = xs ** 2
    ax.plot(xs, ys, "-", color=WARM, lw=1.6, alpha=0.6, zorder=5)
    ax.scatter(xs, ys, color=WARM, s=70, zorder=6, edgecolors=P.BG, lw=0.8)
    for i in range(len(xs) - 1):
        ax.annotate("", xy=(xs[i + 1], ys[i + 1]), xytext=(xs[i], ys[i]),
                    arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.8,
                                    shrinkA=7, shrinkB=7), zorder=6)
    # label only the first, uncrowded, steps; the rest bunch at the floor
    step_off = {0: (14, -2), 1: (12, 2), 2: (12, 6)}
    for i, (dx, dy) in step_off.items():
        ax.annotate(f"step {i}", (xs[i], ys[i]), xytext=(dx, dy),
                    textcoords="offset points", color=P.INK, fontsize=11.5,
                    fontweight="bold", va="center")
    ax.annotate("steps 3+\n(shrinking)", (xs[4], ys[4]), xytext=(20, 34),
                textcoords="offset points", color=P.MUTED, fontsize=10.5,
                va="center",
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.2))
    ax.scatter([0], [0], color=COOL, s=150, zorder=7, marker="*",
               edgecolors=P.BG, lw=0.8)
    ax.annotate("minimum", (0, 0), xytext=(-42, 22),
                textcoords="offset points", color=COOL, fontsize=12,
                fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=COOL, lw=1.3))

    ax.text(0.035, 0.96,
            "new = old − (rate)·gradient\ngradient = 2·error\nstrides shrink "
            "as the slope flattens",
            transform=ax.transAxes, ha="left", va="top", color=P.MUTED,
            fontsize=11.5,
            bbox=dict(boxstyle="round,pad=0.4", fc=P.PANEL, ec=P.GRID, lw=1.0))
    ax.set_xlim(-3.3, 3.3)
    ax.set_ylim(-0.5, 9.6)
    ax.set_xlabel("adjustable value  (error = value − target)", fontsize=12.5)
    ax.set_ylabel("loss = error²", fontsize=12.5)
    ax.set_title("(a)  walk downhill: each step opposes the slope", color=P.INK)

    # ---- panel (b): |error| vs error² ------------------------------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    e = np.linspace(-4, 4, 600)
    ax.plot(e, np.abs(e), color=COOL, lw=2.6, label="|error|  (raw size)")
    ax.plot(e, e ** 2, color=WARM, lw=2.8, label="error²  (squared)")

    # markers at error = 1 and error = 4 to show 1→1 vs 16, i.e. domination
    for ev, col in [(1, P.INK), (4, P.INK)]:
        ax.plot([ev, ev], [0, ev ** 2], color=P.GRID, ls=":", lw=1.2)
        ax.scatter([ev], [ev], color=COOL, s=55, zorder=6, edgecolors=P.BG)
        ax.scatter([ev], [ev ** 2], color=WARM, s=55, zorder=6,
                   edgecolors=P.BG)
    ax.annotate("error 1 → weighs 1", xy=(1, 1), xytext=(1.4, 3.3),
                color=P.INK, fontsize=11.5,
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.3))
    ax.annotate("error 4 → weighs 16\n(16× heavier, not 4×)", xy=(4, 16),
                xytext=(1.1, 13.0), color=P.INK, fontsize=11.5,
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.3))
    ax.set_xlim(-4, 4)
    ax.set_ylim(0, 17.5)
    ax.set_xlabel("error  (prediction − target)", fontsize=12.5)
    ax.set_ylabel("weight on the scales", fontsize=12.5)
    ax.set_title("(b)  squaring lets big mistakes dominate", color=P.INK)
    ax.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
              fontsize=12, loc="upper center")

    return P.save(f, "squared-error-descent.png")


if __name__ == "__main__":
    print("wrote", fig_parabola_and_descent())
