"""Concept figure for the Great Hall of the Paris Cauldron (state of the JEPA realm).

Facts drawn verbatim from world/rooms/paris-cauldron.json:
  - V-JEPA 2 (Jun 2025): 65-80% grasping on the Franka arm.
  - V-JEPA 2.1 (Mar 2026): Dense Predictive Loss + Deep Self-Supervision +
    modality-specific tokenizers -> grasping +20 pts, planning 10x faster.
  - Four sizes: ViT-B 80M, ViT-L 300M, ViT-g 1B, ViT-G 2B.
  - The "missing decree": LLMs have the Chinchilla scaling law (~20 tokens
    per parameter); JEPA has no scaling law yet.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_paris.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import palace_fig as P

WARM = P.WING["emerald"]["warm"]
COOL = P.WING["emerald"]["cool"]
ACC = P.WING["emerald"]["accent"]


def fig_realm():
    f = plt.figure(figsize=(15.2, 11.6))
    f.patch.set_facecolor(P.BG)

    gs = f.add_gridspec(2, 2, left=0.065, right=0.965, top=0.855,
                        bottom=0.07, hspace=0.36, wspace=0.24)
    a_grasp = f.add_subplot(gs[0, 0])
    a_plan = f.add_subplot(gs[0, 1])
    a_ladder = f.add_subplot(gs[1, 0])
    a_law = f.add_subplot(gs[1, 1])
    for ax in (a_grasp, a_plan, a_ladder, a_law):
        P.style_ax(ax, "emerald")

    P.suptitle(f, "The Paris Cauldron, State of the JEPA Realm, May 2026")
    f.text(0.5, 0.915,
           "The Mirror learns to act: V-JEPA 2 → 2.1, the model ladder, "
           "and the scaling law the realm still lacks",
           ha="center", va="bottom", color=P.MUTED, fontsize=12.5,
           style="italic")

    # -----------------------------------------------------------------
    # (a) Grasping success: V-JEPA 2 -> 2.1, +20 points
    # -----------------------------------------------------------------
    a_grasp.set_title("Grasping success on the Franka arm", color=ACC, pad=12)
    labels = ["V-JEPA 2\n(Jun 2025)", "V-JEPA 2.1\n(Mar 2026)"]
    # Room: V-JEPA 2 grasps at 65-80%; 2.1 lifts success by +20 pts.
    base_lo, base_hi = 65, 80
    base_mid = (base_lo + base_hi) / 2          # 72.5
    new_mid = base_mid + 20                      # 92.5
    x = np.array([0, 1])
    # draw the 65-80% reported band for V-JEPA 2
    a_grasp.bar(0, base_hi - base_lo, bottom=base_lo, width=0.52,
                color=COOL, edgecolor=P.BG, lw=1.2, zorder=3, alpha=0.92)
    a_grasp.text(0, (base_lo + base_hi) / 2, "65, 80%", ha="center",
                 va="center", color=P.BG, fontsize=14, fontweight="bold",
                 zorder=5)
    # V-JEPA 2.1 as a point estimate (+20 over the midpoint)
    a_grasp.bar(1, new_mid, width=0.52, color=WARM, edgecolor=P.BG, lw=1.2,
                zorder=3)
    a_grasp.text(1, new_mid / 2, "≈ 93%", ha="center", va="center",
                 color=P.BG, fontsize=14, fontweight="bold", zorder=5)

    # arrow showing the +20 lift from the band midpoint
    a_grasp.add_patch(FancyArrowPatch((0.28, base_mid), (0.72, new_mid),
                      arrowstyle="-|>", mutation_scale=20, color=ACC, lw=2.6,
                      connectionstyle="arc3,rad=-0.18", zorder=6))
    a_grasp.text(0.5, base_mid + 14, "+20 points", ha="center", va="bottom",
                 color=ACC, fontsize=12.5, fontweight="bold")

    a_grasp.set_xticks(x)
    a_grasp.set_xticklabels(labels, fontsize=12)
    a_grasp.set_ylabel("grasp success rate (%)", fontsize=13)
    a_grasp.set_ylim(0, 105)
    a_grasp.set_xlim(-0.6, 1.6)
    a_grasp.grid(axis="x", visible=False)
    a_grasp.text(0.02, 0.97,
                 "trained on 1M hrs video,\nthen 62 hrs of robot data",
                 transform=a_grasp.transAxes, ha="left", va="top",
                 color=P.MUTED, fontsize=10.5, style="italic")

    # -----------------------------------------------------------------
    # (b) Planning speed: 10x faster
    # -----------------------------------------------------------------
    a_plan.set_title("Planning speed (relative)", color=ACC, pad=12)
    a_plan.barh(0, 1, height=0.5, color=COOL, edgecolor=P.BG, lw=1.2, zorder=3)
    a_plan.barh(1, 10, height=0.5, color=WARM, edgecolor=P.BG, lw=1.2, zorder=3)
    a_plan.text(1 + 0.25, 0, "1×", ha="left", va="center", color=P.INK,
                fontsize=14, fontweight="bold")
    a_plan.text(10 - 0.3, 1, "10× faster", ha="right", va="center",
                color=P.BG, fontsize=14, fontweight="bold")
    a_plan.set_yticks([0, 1])
    a_plan.set_yticklabels(["V-JEPA 2", "V-JEPA 2.1"], fontsize=12)
    a_plan.set_xlabel("relative planning throughput", fontsize=13)
    a_plan.set_xlim(0, 11.5)
    a_plan.set_ylim(-0.6, 1.6)
    a_plan.grid(axis="y", visible=False)
    a_plan.text(0.97, 0.05,
                "2.1 adds: Dense Predictive Loss ·\nDeep Self-Supervision · "
                "modality\ntokenizers",
                transform=a_plan.transAxes, ha="right", va="bottom",
                color=P.MUTED, fontsize=10.5, style="italic")

    # -----------------------------------------------------------------
    # (c) Model-size ladder: ViT-B 80M -> ViT-G 2B (log scale)
    # -----------------------------------------------------------------
    a_ladder.set_title("V-JEPA 2.1 ships in four sizes", color=ACC, pad=12)
    names = ["ViT-B", "ViT-L", "ViT-g", "ViT-G"]
    params = np.array([80e6, 300e6, 1e9, 2e9])
    plabels = ["80M", "300M", "1B", "2B"]
    roles = ["distilled", "distilled", "colossal", "colossal"]
    cols = [COOL, COOL, WARM, WARM]
    xi = np.arange(4)
    a_ladder.bar(xi, params, width=0.6, color=cols, edgecolor=P.BG, lw=1.2,
                 zorder=3, log=True)
    for i, (p, lab, role) in enumerate(zip(params, plabels, roles)):
        a_ladder.text(i, p * 1.35, lab, ha="center", va="bottom", color=P.INK,
                      fontsize=14, fontweight="bold")
        a_ladder.text(i, p * 0.5, role, ha="center", va="top", color=P.BG,
                      fontsize=10, fontweight="bold")
    a_ladder.set_xticks(xi)
    a_ladder.set_xticklabels(names, fontsize=12)
    a_ladder.set_ylabel("parameters (log scale)", fontsize=13)
    a_ladder.set_ylim(3e7, 6e9)
    a_ladder.set_xlim(-0.6, 3.6)
    a_ladder.grid(axis="x", visible=False)
    # 25x span annotation
    a_ladder.annotate("", xy=(3, 2e9 * 1.9), xytext=(0, 80e6 * 1.9),
                      arrowprops=dict(arrowstyle="-|>", color=ACC, lw=2.0,
                                      connectionstyle="arc3,rad=0.12"))
    a_ladder.text(1.5, 4.4e9, "25× span", ha="center", va="center",
                  color=ACC, fontsize=12, fontweight="bold")

    # -----------------------------------------------------------------
    # (d) The missing decree: Chinchilla line vs JEPA's undefined frontier
    # -----------------------------------------------------------------
    a_law.set_title("The decree the realm still lacks", color=ACC, pad=12)
    # LLM Chinchilla rule: tokens = 20 x parameters -> a clean line in log-log
    pmin, pmax = 1e8, 1e11
    pp = np.logspace(np.log10(pmin), np.log10(pmax), 50)
    tokens = 20 * pp
    a_law.plot(pp, tokens, color=WARM, lw=3.0, zorder=4,
               label="LLMs, Chinchilla: ~20 tokens / parameter")
    # mark a couple of points on the law
    for pv in (1e9, 1e10, 7e10):
        a_law.scatter(pv, 20 * pv, s=70, color=WARM, edgecolor=P.BG, lw=1.3,
                      zorder=5)
    a_law.text(4e10, 20 * 4e10 * 2.3, "optimal-compute frontier",
               ha="center", va="bottom", color=WARM, fontsize=11,
               fontweight="bold", rotation=27, rotation_mode="anchor")

    # JEPA: no known law -> a shaded zone of uncertainty + a big question mark
    a_law.fill_between(pp, 1e8, 4e12, color=COOL, alpha=0.07, zorder=1)
    a_law.text(2.4e9, 5e11, "?", ha="center", va="center", color=COOL,
               fontsize=72, fontweight="bold", zorder=3, alpha=0.85)
    a_law.text(2.4e9, 7e10, "JEPA, \nno scaling law yet", ha="center",
               va="center", color=COOL, fontsize=12, fontweight="bold",
               zorder=3)

    a_law.set_xscale("log")
    a_law.set_yscale("log")
    a_law.set_xlim(pmin, pmax)
    a_law.set_ylim(1e9, 5e12)
    a_law.set_xlabel("model parameters", fontsize=13)
    a_law.set_ylabel("training tokens", fontsize=13)
    leg = a_law.legend(loc="lower right", fontsize=10.5, frameon=True,
                       facecolor=P.PANEL, edgecolor=P.GRID)
    for t in leg.get_texts():
        t.set_color(P.INK)

    return P.save(f, "jepa-realm.png")


if __name__ == "__main__":
    print(fig_realm())
