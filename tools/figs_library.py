"""Concept figures for the Library of Keys (KV cache + Flash attention).

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_library.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import palace_fig as P

WARM = P.WING["sapphire"]["warm"]
COOL = P.WING["sapphire"]["cool"]
ACC = P.WING["sapphire"]["accent"]


def rbox(ax, x, y, w, h, fc, ec, lw=1.6, rad=0.04, alpha=1.0):
    b = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rad}",
                       fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=3)
    ax.add_patch(b)
    return b


def arrow(ax, p0, p1, color=P.MUTED, lw=2.0, ls="-", rad=0.0):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=16,
                        color=color, lw=lw, linestyle=ls,
                        connectionstyle=f"arc3,rad={rad}", zorder=2)
    ax.add_patch(a)


# ===========================================================================
# FIGURE 1 — KV cache growth
# ===========================================================================
def fig_kv_cache():
    f, (axL, axR) = P.fig(15.5, 7.4, wing="sapphire", ncols=2,
                          gridspec_kw={"width_ratios": [1.0, 1.32], "wspace": 0.22})
    P.suptitle(f, "The KV Cache at Inference — the library only grows")

    # ---- (a) staircase plot --------------------------------------------
    tokens = ["The", "cat", "sat", "on", "the", "mat"]
    # prefill processes "The cat" together (2 cached), then decode 1/step
    n = len(tokens)
    steps = np.arange(n + 1)            # 0..6 (x = tokens processed)
    cache = np.arange(n + 1)            # cache size == tokens seen
    axL.step(steps, cache, where="post", color=ACC, lw=3.0, zorder=4)
    axL.plot(steps[:-1], cache[:-1], "o", color=WARM, ms=9,
             mec=P.BG, mew=1.5, zorder=5)

    # prefill shading: first 2 tokens processed at once
    axL.axvspan(0, 2, color=COOL, alpha=0.12, zorder=0)
    axL.axvspan(2, n, color=WARM, alpha=0.08, zorder=0)
    axL.text(1.0, 5.55, "PREFILL\n(prompt at once)", color=COOL, fontsize=11.5,
             ha="center", va="top", fontweight="bold")
    axL.text(4.0, 5.55, "DECODE\n(+1 K,V per step)", color=WARM, fontsize=11.5,
             ha="center", va="top", fontweight="bold")

    for i, t in enumerate(tokens):
        axL.annotate(t, (i + 0.5, cache[i] + 0.02), color=P.MUTED,
                     fontsize=11, ha="center", va="bottom", style="italic")

    axL.set_xlim(0, n)
    axL.set_ylim(0, 6.3)
    axL.set_xticks(range(n + 1))
    axL.set_yticks(range(0, 7))
    axL.set_xlabel("tokens processed", fontsize=13)
    axL.set_ylabel("cached (K, V) vectors", fontsize=13)
    axL.set_title("(a)  cache size grows by exactly 1 per decode step",
                  fontsize=14, loc="left", color=P.INK)

    # ---- (b) prefill -> decode schematic -------------------------------
    axR.set_xlim(0, 12)
    axR.set_ylim(0, 10)
    axR.axis("off")
    axR.set_title("(b)  prefill once, then decode one token at a time",
                  fontsize=14, loc="left", color=P.INK)
    axR.grid(False)

    def cell(x, y, label, fc, ec, w=0.92, h=0.7, fs=11):
        rbox(axR, x, y, w, h, fc, ec, lw=1.4, rad=0.05)
        axR.text(x + w / 2, y + h / 2, label, color=P.INK, fontsize=fs,
                 ha="center", va="center")

    # ---- KV cache rows (top), growing ----------------------------------
    y_k = 8.55
    y_v = 7.55
    axR.text(0.2, y_k + 0.35, "K_cache", color=ACC, fontsize=12.5,
             fontweight="bold", va="center")
    axR.text(0.2, y_v + 0.35, "V_cache", color=ACC, fontsize=12.5,
             fontweight="bold", va="center")

    keys = ["k_The", "k_cat", "k_sat"]
    vals = ["v_The", "v_cat", "v_sat"]
    x0 = 2.1
    dx = 1.1
    for i in range(3):
        fc = (COOL if i < 2 else WARM)
        cell(x0 + i * dx, y_k, keys[i], "#1a2738", fc, w=0.95, h=0.7, fs=10.5)
        cell(x0 + i * dx, y_v, vals[i], "#1a2738", fc, w=0.95, h=0.7, fs=10.5)
    axR.annotate("grows  ->", (x0 + 3 * dx + 0.15, y_v + 0.7),
                 color=WARM, fontsize=12, fontweight="bold", va="center")
    axR.text(x0 + 1.05, y_k + 1.0, "the new k_sat, v_sat are shelved forever",
             color=COOL, fontsize=10, ha="left", style="italic")

    # ---- Decode step box -----------------------------------------------
    bx, by, bw, bh = 0.5, 0.5, 11.0, 6.05
    rbox(axR, bx, by, bw, bh, "#121b27", P.GRID, lw=1.5, rad=0.03)
    axR.text(bx + 0.3, by + bh - 0.42, "DECODE STEP   ·   produce “sat”",
             color=WARM, fontsize=12.5, fontweight="bold", va="center")

    cy = by + 2.75   # vertical centre of the pipeline row

    # new token
    cell(0.95, cy, "new token", "#19222f", P.MUTED, w=1.5, h=0.7, fs=10.5)
    axR.text(1.7, cy - 0.45, "“sat”", color=P.MUTED, fontsize=9.5,
             ha="center", va="top", style="italic")

    # q,k,v fresh
    qx = 3.15
    cell(qx, cy + 0.45, "q_sat", "#2a2118", WARM, w=0.95, h=0.6, fs=10.5)
    cell(qx, cy - 0.25, "k_sat", "#19222f", ACC, w=0.95, h=0.6, fs=10.5)
    cell(qx, cy - 0.95, "v_sat", "#19222f", ACC, w=0.95, h=0.6, fs=10.5)
    arrow(axR, (2.5, cy + 0.3), (qx - 0.02, cy + 0.4), color=P.MUTED, lw=1.6)
    axR.text(qx + 0.47, cy + 1.45, "computed FRESH\nthis step", color=WARM,
             fontsize=9.8, ha="center", va="center", fontweight="bold")

    # append k,v up to cache
    arrow(axR, (qx + 0.95, cy - 0.4), (x0 + 2 * dx + 0.45, y_v - 0.02),
          color=ACC, lw=1.6, rad=-0.3)
    axR.text(x0 + 2 * dx + 0.45, cy + 1.35, "append k,v ->", color=ACC,
             fontsize=9.5, ha="center", va="center", style="italic")

    # scores
    sx = 5.6
    cell(sx, cy - 0.05, "scores =\nq_sat · K_cacheᵀ", "#23303f", COOL,
         w=1.85, h=1.0, fs=10)
    arrow(axR, (qx + 0.95, cy + 0.7), (sx - 0.02, cy + 0.55), color=WARM, lw=1.7)

    # softmax
    wx = 7.95
    cell(wx, cy - 0.05, "softmax\n[.12 .55 .33]", "#23303f", COOL,
         w=1.7, h=1.0, fs=10)
    arrow(axR, (sx + 1.85, cy + 0.45), (wx - 0.02, cy + 0.45), color=P.MUTED, lw=1.6)

    # blend cached values (dashed up to V_cache)
    arrow(axR, (wx + 0.85, cy + 1.0), (wx + 0.5, y_v - 0.02),
          color=COOL, lw=1.6, ls=(0, (4, 3)), rad=-0.15)
    axR.text(wx + 1.95, cy + 0.45, "blend\nV_cache", color=COOL, fontsize=9.5,
             ha="left", va="center", style="italic")

    # blended vector -> MLP -> ... bar
    barx, bary, barw, barh = 1.2, by + 0.55, 9.6, 0.78
    rbox(axR, barx, bary, barw, barh, "#161f2b", P.GRID, lw=1.3, rad=0.05)
    axR.text(barx + barw / 2, bary + barh / 2,
             "blended vector  ->  MLP  ->  lm_head  ->  next token",
             color=P.INK, fontsize=11, ha="center", va="center")
    arrow(axR, (wx + 0.85, cy - 0.6), (barx + barw / 2, bary + barh),
          color=WARM, lw=1.6, rad=0.12)

    # Q-not-cached note (between pipeline and bar, clear band)
    axR.text(bx + bw / 2, by + 1.68,
             "Q is discarded — the asker asks once;  K and V stay and only grow.",
             color=WARM, fontsize=10.5, ha="center", va="center",
             fontweight="bold", style="italic")

    return P.save(f, "kv-cache-growth.png")


# ===========================================================================
# FIGURE 2 — Flash attention
# ===========================================================================
def fig_flash():
    f, (axL, axR) = P.fig(15.5, 7.2, wing="sapphire", ncols=2,
                          gridspec_kw={"width_ratios": [1.05, 1.15], "wspace": 0.24})
    P.suptitle(f, "Flash Attention — same answer, O(n) memory")

    # ---- (a) memory vs sequence length (log y) -------------------------
    n = np.array([1e3, 2e3, 4e3, 8e3, 16e3, 32e3, 64e3, 128e3])
    bytes_per = 2          # fp16 score
    heads = 1
    eager = n ** 2 * bytes_per / 1e9        # GB for (n,n) fp16, one head
    flash = n * 4 * bytes_per / 1e9 + 0.02  # O(n): a few running buffers

    axL.plot(n, eager, "-o", color=WARM, lw=3.0, ms=7, mec=P.BG, mew=1.2,
             label="eager: store (n,n)  →  O(n²)", zorder=5)
    axL.plot(n, flash, "-o", color=ACC, lw=3.0, ms=7, mec=P.BG, mew=1.2,
             label="Flash: tiled, never stored  →  O(n)", zorder=5)
    axL.set_yscale("log")
    axL.set_xscale("log")
    axL.set_xlabel("sequence length  n", fontsize=13)
    axL.set_ylabel("attention-matrix memory  (GB, one head)", fontsize=13)
    axL.set_title("(a)  memory vs sequence length", fontsize=14, loc="left",
                  color=P.INK)
    axL.legend(loc="lower right", facecolor=P.PANEL, edgecolor=P.GRID,
               labelcolor=P.INK, fontsize=11, framealpha=0.97)

    # annotate ~32 GB at 128K
    axL.annotate("~32 GB for one head\nat n = 128K  (eager)",
                 xy=(128e3, eager[-1]), xytext=(9e3, 6e3),
                 color=WARM, fontsize=11.5, fontweight="bold", ha="center",
                 arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.8))
    axL.set_ylim(1e-2, 4e4)

    # ---- (b) tiling schematic ------------------------------------------
    axR.set_xlim(0, 12)
    axR.set_ylim(0, 10)
    axR.axis("off")
    axR.grid(False)
    axR.set_title("(b)  tiling + running softmax  (the (n,n) matrix is never stored)",
                  fontsize=13.5, loc="left", color=P.INK)

    # SRAM region box
    rbox(axR, 0.5, 4.5, 11.0, 4.9, "#101a16", "#2f5d44", lw=1.6, rad=0.03)
    axR.text(0.8, 9.05, "on-chip SRAM  (~20 MB, fast)", color="#9fe8b9",
             fontsize=12, fontweight="bold", va="center")

    # Q tiles (rows) and K tiles (cols) loaded as blocks
    # Q blocks on the left
    for i in range(2):
        rbox(axR, 1.0, 6.7 - i * 1.35, 1.15, 1.1, "#2a2118", WARM, lw=1.5, rad=0.05)
        axR.text(1.575, 7.25 - i * 1.35, f"Q\nblock {i+1}", color=WARM,
                 fontsize=10.5, ha="center", va="center", fontweight="bold")
    # K/V blocks across the top
    for j in range(3):
        rbox(axR, 3.1 + j * 1.4, 7.9, 1.2, 1.0, "#19222f", ACC, lw=1.5, rad=0.05)
        axR.text(3.7 + j * 1.4, 8.4, f"K,V\nblock {j+1}", color=ACC,
                 fontsize=10, ha="center", va="center", fontweight="bold")

    # partial score tile being computed (one Q block x one K block)
    rbox(axR, 3.1, 5.05, 4.2, 2.3, "#16202c", P.GRID, lw=1.3, rad=0.03)
    axR.text(5.2, 7.05, "partial S = QKᵀ for this tile\n(computed, used, discarded)",
             color=P.MUTED, fontsize=10, ha="center", va="center", style="italic")
    # mini grid of one tile
    for r in range(2):
        for c in range(3):
            sh = 0.35 + 0.55 * ((r + c) % 2)
            axR.add_patch(Rectangle((3.55 + c * 0.62, 5.55 + r * 0.55), 0.5, 0.45,
                          fc=P.cmap("heat")(sh), ec=P.BG, lw=0.8, zorder=4))
    arrow(axR, (2.15, 6.6), (3.45, 6.4), color=WARM, lw=1.5)
    arrow(axR, (4.5, 7.85), (4.7, 7.4), color=ACC, lw=1.5)

    # running softmax accumulator box (right)
    rbox(axR, 7.7, 5.05, 3.55, 2.85, "#23303f", COOL, lw=1.6, rad=0.04)
    axR.text(9.475, 7.55, "running softmax", color=ACC, fontsize=12,
             fontweight="bold", ha="center", va="center")
    axR.text(9.475, 6.55,
             "running max  m\nrunning sum  l\noutput  O",
             color=P.INK, fontsize=11, ha="center", va="center", linespacing=1.5)
    axR.text(9.475, 5.45, "rescale old by  e^(m_old−m_new)",
             color=WARM, fontsize=9.8, ha="center", va="center", style="italic")
    arrow(axR, (7.3, 6.3), (7.66, 6.4), color=COOL, lw=1.7)

    # bottom: HBM contrast + identical-output guarantee
    rbox(axR, 0.5, 2.55, 11.0, 1.45, "#1c1411", "#7a4a2a", lw=1.5, rad=0.03)
    axR.text(0.8, 3.55, "slow HBM:  eager writes the full (n,n) matrix here  (×)",
             color="#e0a060", fontsize=11.5, va="center", fontweight="bold")
    axR.text(0.8, 2.95,
             "Flash keeps only the tiny m, l, O buffers  →  O(n) memory, never the (n,n) matrix",
             color=P.INK, fontsize=11, va="center")

    axR.text(6.0, 1.4,
             "Output is IDENTICAL to eager attention — exact, not approximate.",
             color="#9fe8b9", fontsize=12, ha="center", va="center",
             fontweight="bold")
    axR.text(6.0, 0.7,
             "If Flash and eager ever disagree, it is a bug, not a feature.",
             color=P.MUTED, fontsize=10.5, ha="center", va="center", style="italic")

    return P.save(f, "flash-attention.png")


if __name__ == "__main__":
    p1 = fig_kv_cache()
    p2 = fig_flash()
    print("WROTE", p1)
    print("WROTE", p2)
