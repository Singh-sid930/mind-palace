"""Figures for the Riverworks (flow matching) and Embodied Motion floors.

Run with:  ~/anaconda3/envs/lrm/bin/python tools/fig_flow_matching.py
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from palace_fig import (fig, save, suptitle, style_ax, WING, INK, MUTED,
                        GRID, PANEL, HOT, BG)

COB = WING["cobalt"]["accent"]
EMB = WING["ember"]["accent"]


# --- 1. straight vs curved: why the step count collapses --------------------
def straight_vs_curved():
    f, axes = fig(13.0, 4.6, wing="cobalt", n=3)
    a, b, c = axes

    # (a) the path itself, with the interpolation table
    t = np.linspace(0, 1, 200)
    x0, x1 = 1.0, 5.0
    a.plot(t, (1 - t) * x0 + t * x1, color=COB, lw=2.6, zorder=3)
    ts = np.array([0, .25, .5, .75, 1.0])
    xs = (1 - ts) * x0 + ts * x1
    a.scatter(ts, xs, s=70, color=HOT, zorder=4, edgecolor=BG, linewidth=1.2)
    for tt, xx in zip(ts, xs):
        a.annotate(f"{xx:.1f}", (tt, xx), textcoords="offset points",
                   xytext=(-4, 11), color=INK, fontsize=10, ha="center")
    # a curved, schedule-shaped path between the SAME two endpoints
    s = (1 - np.cos(np.pi * t)) / 2
    a.plot(t, x0 + (x1 - x0) * s, color=MUTED, lw=2.0, ls="--", alpha=0.85)
    a.text(0.46, 1.55, "diffusion: curved,\nschedule-determined",
           color=MUTED, fontsize=10, style="italic")
    a.text(0.04, 4.75, "flow matching:\nstraight line", color=COB, fontsize=11,
           fontweight="bold")
    a.set_title("(a)  the path", fontsize=13)
    a.set_xlabel("t     (0 = noise, 1 = data)")
    a.set_ylabel("x")
    a.set_ylim(0.3, 5.7)

    # (b) the velocity: constant vs schedule-dependent
    b.axhline(4.0, color=COB, lw=2.8, zorder=3)
    b.text(0.13, 4.24, "v = x₁ − x₀ = 4.0   (constant)", color=COB,
           fontsize=11.5, fontweight="bold")
    b.plot(t, (x1 - x0) * (np.pi / 2) * np.sin(np.pi * t),
           color=MUTED, lw=2.0, ls="--")
    b.text(0.16, 1.05, "the curved path's speed:\nchanges the whole way along",
           color=MUTED, fontsize=10, style="italic")
    b.set_title("(b)  the velocity it implies", fontsize=13)
    b.set_xlabel("t")
    b.set_ylabel("dx/dt")
    b.set_ylim(-0.5, 7.4)

    # (c) four Euler steps: exact on a line, corner-cutting on a curve
    c.plot(t, (1 - t) * x0 + t * x1, color=COB, lw=2.0, alpha=0.5, zorder=2)
    c.scatter(ts, xs, s=64, color=COB, zorder=5, edgecolor=BG, linewidth=1.1)
    for i in range(4):
        c.add_patch(FancyArrowPatch((ts[i], xs[i]), (ts[i + 1], xs[i + 1]),
                    arrowstyle="-|>", mutation_scale=13, color=COB, lw=1.8,
                    zorder=4))
    c.plot(t, x0 + (x1 - x0) * s, color=MUTED, lw=2.0, alpha=0.6, ls="--",
           zorder=2)
    # Euler on the curve: step along the LOCAL tangent, accumulating error
    ex, ey = [0.0], [x0]
    for i in range(4):
        tt = i / 4
        slope = (x1 - x0) * (np.pi / 2) * np.sin(np.pi * tt)
        ey.append(ey[-1] + slope * 0.25)
        ex.append(tt + 0.25)
    c.plot(ex, ey, color=EMB, lw=1.9, zorder=4)
    c.scatter(ex, ey, s=56, color=EMB, zorder=5, edgecolor=BG, linewidth=1.1)
    c.annotate("same 4 steps on the curve:\neach cuts the corner, so it\nmisses the target",
               xy=(1.0, ey[-1]), xytext=(0.10, 5.55), color=EMB, fontsize=9.8,
               arrowprops=dict(arrowstyle="->", color=EMB, lw=1.3))
    c.text(0.44, 1.35, "4 steps,\nexact arrival", color=COB, fontsize=10.5,
           fontweight="bold")
    c.set_title("(c)  the same four Euler steps", fontsize=13)
    c.set_xlabel("t")
    c.set_ylabel("x")
    c.set_ylim(0.3, 6.3)

    suptitle(f, "A straight path forgives large steps — and that is the whole saving")
    f.tight_layout(rect=[0, 0, 1, 0.93])
    return save(f, "flow-straight-path.png")


# --- 2. the bimodal experiment: commit, or average into the wall -----------
def bimodal_commit():
    f, axes = fig(12.4, 4.8, wing="ember", n=2)
    a, b = axes

    # (a) the two demonstrated modes, the sampled paths, and the mean path
    u = np.linspace(0, 1, 120)
    for sign, lbl in [(1, None), (-1, None)]:
        a.plot(u, sign * 0.55 * np.sin(u * np.pi / 2), color=HOT, lw=2.4,
               alpha=0.85, zorder=3)
    rng = np.random.default_rng(4)
    for i in range(10):                      # ~45/55 split, as measured
        s = 1 if i % 2 == 0 else -1
        jit = rng.normal(0, 0.035)
        a.plot(u, s * 0.55 * np.sin(u * np.pi / 2) + jit * u,
               color=EMB, lw=1.0, alpha=0.55, zorder=2)
    a.plot(u, 0 * u, color="#8f8f8f", lw=2.6, zorder=4)
    a.add_patch(Rectangle((0.63, -0.17), 0.12, 0.34, facecolor="#d06a5a",
                          alpha=0.85, zorder=5))
    a.text(0.695, 0.235, "obstacle", color="#e0907f", fontsize=10.5,
           ha="center", fontweight="bold")
    a.text(0.03, 0.60, "demonstrations: sometimes LEFT, sometimes RIGHT",
           color=HOT, fontsize=10.5, fontweight="bold")
    a.text(0.03, -0.66, "regression answers with the MEAN of both modes",
           color="#b9b9b9", fontsize=10.5, fontweight="bold")
    a.set_title("(a)  one observation, two valid answers", fontsize=13)
    a.set_xlabel("progress along the chunk")
    a.set_ylabel("lateral action")
    a.set_ylim(-0.78, 0.78)

    # (b) measured end-magnitude (target = 1.0)
    steps = [1, 2, 5, 10, 50]
    vals = [0.243, 0.833, 0.964, 0.988, 0.998]
    xs = np.arange(len(steps))
    b.bar(xs, vals, width=0.62, color=EMB, alpha=0.9, zorder=3)
    b.bar([len(steps) + 0.6], [0.418], width=0.62, color="#8f8f8f",
          alpha=0.9, zorder=3)
    b.axhline(1.0, color=HOT, ls="--", lw=1.5, alpha=0.9, zorder=2)
    b.text(len(steps) + 0.62, 1.035, "target 1.0", color=HOT, fontsize=10,
           ha="right")
    for x, v in zip(xs, vals):
        b.text(x, v + 0.03, f"{v:.3f}", color=INK, fontsize=10, ha="center")
    b.text(len(steps) + 0.6, 0.448, "0.418", color=INK, fontsize=10, ha="center")
    b.text(len(steps) + 0.6, 0.20, "COLLAPSED\nto the middle", color="#d0d0d0",
           fontsize=9.5, ha="center", style="italic")
    b.set_xticks(list(xs) + [len(steps) + 0.6])
    b.set_xticklabels([f"{s} step" + ("s" if s > 1 else "") for s in steps]
                      + ["regression"], fontsize=10)
    b.set_ylim(0, 1.16)
    b.set_ylabel("|end of action| (1.0 = committed)")
    b.set_title("(b)  flow matching commits; the average does not", fontsize=13)

    suptitle(f, "Why the action head must be generative", wing="ember")
    f.tight_layout(rect=[0, 0, 1, 0.93])
    return save(f, "vla-bimodal-commit.png")


# --- 3. pi0: two experts, one transformer ----------------------------------
def two_experts():
    f, ax = plt.subplots(figsize=(11.6, 5.6))
    f.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.4)
    ax.axis("off")

    def token(x, y, w, label, color, sub=""):
        ax.add_patch(Rectangle((x, y), w, 0.62, facecolor=PANEL,
                               edgecolor=color, lw=1.7, zorder=3))
        ax.text(x + w / 2, y + 0.38, label, ha="center", color=INK,
                fontsize=10.5, zorder=4)
        if sub:
            ax.text(x + w / 2, y + 0.14, sub, ha="center", color=MUTED,
                    fontsize=8.4, zorder=4)

    VLM, ACT = WING["verdigris"]["accent"], EMB
    ax.text(0.2, 5.85, "ONE transformer · the token's TYPE selects which weights it uses",
            color=INK, fontsize=13, fontweight="bold")

    y = 4.55
    token(0.4, y, 2.0, "image tokens", VLM, "PaliGemma 3B")
    token(2.6, y, 1.9, "text tokens", VLM, "PaliGemma 3B")
    token(4.7, y, 1.7, "state token", ACT, "action expert")
    token(6.6, y, 4.9, "noisy action chunk  x_τ  (50 tokens)", ACT,
          "action expert 300M   ·   an INPUT, not an output")

    ax.text(0.4, y - 0.42, "frozen-ish VLM weights", color=VLM, fontsize=9.5)
    ax.text(6.6, y - 0.42, "separate weight set — but inside the same stack",
            color=ACT, fontsize=9.5)

    # joint attention band
    ax.add_patch(Rectangle((0.4, 2.75), 11.1, 0.95, facecolor="#1b2735",
                           edgecolor=HOT, lw=1.8, zorder=3))
    ax.text(5.95, 3.42, "JOINT SELF-ATTENTION  —  every token attends to every token",
            ha="center", color=HOT, fontsize=11.5, fontweight="bold", zorder=4)
    ax.text(5.95, 3.02,
            "each token computes Q,K,V with ITS OWN expert's weights, then all attend together",
            ha="center", color=MUTED, fontsize=9.6, zorder=4)
    for x in (1.4, 3.55, 5.55, 9.0):
        ax.add_patch(FancyArrowPatch((x, y - 0.02), (x, 3.72),
                     arrowstyle="-|>", mutation_scale=11, color=MUTED,
                     lw=1.2, alpha=0.8, zorder=2))

    # separate MLPs
    ax.add_patch(Rectangle((0.4, 1.62), 6.0, 0.72, facecolor=PANEL,
                           edgecolor=VLM, lw=1.6, zorder=3))
    ax.text(3.4, 1.94, "VLM MLP", ha="center", color=INK, fontsize=10.5, zorder=4)
    ax.add_patch(Rectangle((6.6, 1.62), 4.9, 0.72, facecolor=PANEL,
                           edgecolor=ACT, lw=1.6, zorder=3))
    ax.text(9.05, 1.94, "action-expert MLP", ha="center", color=INK,
            fontsize=10.5, zorder=4)
    ax.text(5.95, 1.28, "attention MIXES;  the MLPs stay specialised",
            ha="center", color=MUTED, fontsize=9.8, style="italic")

    ax.add_patch(FancyArrowPatch((9.05, 1.58), (9.05, 0.92),
                 arrowstyle="-|>", mutation_scale=13, color=ACT, lw=1.8))
    ax.text(9.05, 0.60, "velocity for the chunk   (50, action_dim)",
            ha="center", color=ACT, fontsize=11, fontweight="bold")
    ax.text(0.4, 0.60,
            "image & text K,V do not depend on τ → cached across all 10 steps\n"
            "cost = one 3B pass + ten 300M passes,  NOT ten 3.3B passes",
            color=MUTED, fontsize=9.8, va="center")

    from palace_fig import ASSETS
    f.savefig(ASSETS / "vla-two-experts.png", facecolor=BG,
              bbox_inches="tight", pad_inches=0.3, dpi=150)
    plt.close(f)
    return "world/assets/vla-two-experts.png"


if __name__ == "__main__":
    for fn in (straight_vs_curved, bimodal_commit, two_experts):
        print(fn())
