"""Concept figures for the Council of Heads room (multi-head attention).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_council.py
"""
import sys
sys.path.insert(0, "tools")
import palace_fig as P
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

ACC = P.WING["sapphire"]["accent"]
COOL = P.WING["sapphire"]["cool"]
WARM = P.WING["sapphire"]["warm"]


# ---------------------------------------------------------------------------
# Figure 1: kv-sharing.png  —  MHA -> GQA -> MQA
# ---------------------------------------------------------------------------
def fig_kv_sharing():
    f = plt.figure(figsize=(13.5, 7.4))
    f.patch.set_facecolor(P.BG)
    P.suptitle(f, "Shared Libraries:  MHA → GQA → MQA   (d_k = 64, h = 8)")

    # --- left: bar chart of KV-cache values per token --------------------
    axb = f.add_axes([0.07, 0.10, 0.40, 0.74])
    P.style_ax(axb, "sapphire")

    labels = ["MHA\n(g=8)", "GQA\n(g=4)", "GQA\n(g=2)", "MQA\n(g=1)"]
    vals = [1024, 512, 256, 128]
    colors = [ACC, COOL, "#6f93c4", WARM]
    x = np.arange(len(vals))
    bars = axb.bar(x, vals, width=0.62, color=colors, edgecolor=P.GRID, linewidth=1.0)
    for xi, v in zip(x, vals):
        axb.text(xi, v + 22, f"{v}", ha="center", va="bottom",
                 color=P.INK, fontsize=14, fontweight="bold")
    axb.set_xticks(x)
    axb.set_xticklabels(labels, fontsize=12, color=P.INK)
    axb.set_ylabel("KV-cache values stored per token", fontsize=13)
    axb.set_ylim(0, 1180)
    axb.set_title("Memory per token  (= g × 2 × d_k)", fontsize=14, pad=10)
    axb.grid(True, axis="y", color=P.GRID, linewidth=0.6, alpha=0.6)
    axb.set_axisbelow(True)

    # --- right: schematic of Q heads grouped onto KV pairs ---------------
    axs = f.add_axes([0.53, 0.10, 0.43, 0.74])
    axs.set_facecolor(P.PANEL)
    for s in axs.spines.values():
        s.set_color(P.GRID)
    axs.set_xlim(0, 10)
    axs.set_ylim(0, 10)
    axs.set_xticks([])
    axs.set_yticks([])
    axs.set_title("How query heads share K/V", fontsize=14, pad=10, color=P.INK)

    def qbox(ax, cx, cy, w, h, label, fc):
        b = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                           boxstyle="round,pad=0.015,rounding_size=0.10",
                           fc=fc, ec=P.GRID, lw=0.8)
        ax.add_patch(b)
        ax.text(cx, cy, label, ha="center", va="center",
                color="#0e131b", fontsize=8.5, fontweight="bold")

    def kvbox(ax, cx, cy, w, h, label, fc):
        b = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                           boxstyle="round,pad=0.015,rounding_size=0.10",
                           fc=fc, ec=ACC, lw=1.3)
        ax.add_patch(b)
        ax.text(cx, cy, label, ha="center", va="center",
                color=P.INK, fontsize=9, fontweight="bold")

    # 8 query heads across the top
    qx = np.linspace(0.85, 9.15, 8)
    qw = 0.92
    # three rows: MHA (top), GQA g=2 (mid), MQA (bottom)
    rows = [
        (8.4, "MHA: 8 K/V", [0, 1, 2, 3, 4, 5, 6, 7]),   # each Q its own KV
        (5.0, "GQA g=2: 2 K/V groups", [0, 0, 0, 0, 1, 1, 1, 1]),
        (1.6, "MQA: 1 shared K/V", [0, 0, 0, 0, 0, 0, 0, 0]),
    ]
    kvpal = [ACC, COOL, "#6f93c4", WARM]

    for ry, rlabel, groups in rows:
        ax = axs
        ax.text(0.15, ry + 1.05, rlabel, ha="left", va="center",
                color=P.INK, fontsize=10.5, fontweight="bold")
        # query heads
        for i, cx in enumerate(qx):
            qbox(ax, cx, ry + 0.62, qw, 0.55, f"Q{i+1}", "#cbd9ec")
        # kv groups: one box centered on its group's queries
        uniq = sorted(set(groups))
        for gi in uniq:
            members = [qx[i] for i in range(8) if groups[i] == gi]
            cx = float(np.mean(members))
            fc = kvpal[gi % len(kvpal)]
            kvbox(ax, cx, ry - 0.62, max(1.0, (max(members) - min(members)) + 1.0),
                  0.5, "K,V", fc)
            for i in range(8):
                if groups[i] == gi:
                    ax.add_patch(FancyArrowPatch(
                        (qx[i], ry + 0.34), (cx, ry - 0.37),
                        arrowstyle="-", color=fc, lw=1.0, alpha=0.85,
                        shrinkA=0, shrinkB=0))

    # annotation
    axs.text(5.0, -0.55,
             "Architecture chosen BEFORE training; trained with shared KV from day one.\n"
             "LLaMA 2 70B uses g=8 (MHA), the rare exception.",
             ha="center", va="top", color=P.MUTED, fontsize=9.5, style="italic")

    return P.save(f, "kv-sharing.png")


# ---------------------------------------------------------------------------
# Figure 2: multihead-flow.png  —  split / attend / concat / project
# ---------------------------------------------------------------------------
def fig_multihead_flow():
    f = plt.figure(figsize=(13.5, 7.6))
    f.patch.set_facecolor(P.BG)
    P.suptitle(f, "Multi-Head Attention:  Split · Attend · Concat · Project")

    ax = f.add_axes([0.04, 0.05, 0.92, 0.84])
    ax.set_facecolor(P.PANEL)
    for s in ax.spines.values():
        s.set_color(P.GRID)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.set_xticks([])
    ax.set_yticks([])

    def box(cx, cy, w, h, lines, fc, ec=P.GRID, fs=10, tc="#0e131b", lw=1.0):
        b = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                           boxstyle="round,pad=0.02,rounding_size=0.12",
                           fc=fc, ec=ec, lw=lw)
        ax.add_patch(b)
        ax.text(cx, cy, lines, ha="center", va="center",
                color=tc, fontsize=fs, fontweight="bold", linespacing=1.3)

    def arrow(p0, p1, color=ACC, lw=1.6):
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>",
                     mutation_scale=14, color=color, lw=lw,
                     shrinkA=2, shrinkB=2))

    # 1) token embedding (d_model)
    box(2.0, 5.0, 2.2, 1.5, "token\nembedding\n(d_model)", "#cbd9ec", fs=10)

    # 2) split into h heads
    box(5.0, 5.0, 1.7, 4.6, "split\ninto\nh heads", ACC, fs=10)
    arrow((3.1, 5.0), (4.15, 5.0))

    # 3) three head lanes (head 1, head 2, head h)
    head_ys = [8.0, 5.0, 2.0]
    head_labels = ["head 1", "head 2", "head h"]
    for hy, hl in zip(head_ys, head_labels):
        arrow((5.85, 5.0), (6.7, hy), color=COOL)
        # own Wq,Wk,Wv
        box(7.9, hy, 2.0, 1.15, f"{hl}\nown Wq,Wk,Wv", "#9fb6d6", fs=9.0)
        # scaled dot-product attention in d_k subspace
        box(10.7, hy, 2.4, 1.15, "scaled dot-product\nattn  (d_k = d_model/h)",
            COOL, fs=8.6)
        arrow((8.9, hy), (9.5, hy), color=COOL)
    # dotted continuation between head 2 and head h
    ax.text(7.9, 3.5, ".\n.\n.", ha="center", va="center", color=P.MUTED,
            fontsize=13, linespacing=0.6)

    # 4) concat back to d_model
    box(13.5, 5.0, 1.5, 4.6, "concat\n→ d_model", WARM, fs=9.5)
    for hy in head_ys:
        arrow((11.95, hy), (12.7, 5.0 + (hy - 5.0) * 0.55), color=COOL)

    # 5) Wo mixing
    box(15.2, 5.0, 1.3, 2.0, "· Wo\nmix all\nheads", ACC, fs=9.5)
    arrow((14.3, 5.0), (14.5, 5.0))

    # output label below Wo
    ax.text(15.2, 3.5, "output\nn × d_model", ha="center", va="top",
            color=P.INK, fontsize=9.5, fontweight="bold", linespacing=1.2)

    # notes
    ax.text(8.0, 0.55,
            "Each head attends in its own d_k subspace, in parallel.  Concatenation stacks them; "
            "Wo lets dimensions that were separate interact.",
            ha="center", va="center", color=P.MUTED, fontsize=10, style="italic")
    ax.text(8.0, 9.5,
            "Constraint:  d_model must be divisible by h   (h × d_k must rebuild d_model exactly)",
            ha="center", va="center", color=P.HOT, fontsize=10.5, fontweight="bold")

    return P.save(f, "multihead-flow.png")


if __name__ == "__main__":
    print(fig_kv_sharing())
    print(fig_multihead_flow())
