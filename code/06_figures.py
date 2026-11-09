#!/usr/bin/env python3
"""06_figures.py - paper figures, built only from paper/stats.json.

Plain-language note: draws the charts for the paper from the statistics file, so a
chart can never disagree with the numbers. Every chart carries a DRAFT stamp until
the author has checked the data; run with --final after that to remove it.

Figure 1: fatal crash rate and pedestrian death rate by zone (two panels, one scale each).
Figure 2: pedestrian death rate by zone and town size.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

for _f in ["regular", "bold", "italic"]:
    _p = f"/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-{_f}.otf"
    if os.path.exists(_p):
        font_manager.fontManager.addfont(_p)
FONT = "TeX Gyre Pagella" if any("Pagella" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Serif"
if os.environ.get("FIGFONT") == "termes":  # Times-style font for the EarthArXiv spatial-analysis version
    for _f in ["regular", "bold", "italic"]:
        font_manager.fontManager.addfont(f"/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-{_f}.otf")
    FONT = "TeX Gyre Termes"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
OUT = os.environ.get("FIGOUT", os.path.join(ROOT, "paper", "figures"))
FINAL = "--final" in sys.argv
ZONES = ["CENTER", "TOWN", "APPROACH"]
ZLAB = {"CENTER": "Town center", "TOWN": "Rest of town", "APPROACH": "Outside town\n(0-5 mi)"}
# IBM Design Library color-blind-safe palette (magenta, orange, blue); validated: CVD and normal-vision
# separation pass, values are labeled on every bar so identity never rests on color alone
COL = {"CENTER": "#DC267F", "TOWN": "#FE6100", "APPROACH": "#648FFF"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"  # white for print
plt.rcParams.update({"font.family": FONT, "font.size": 9, "pdf.fonttype": 42, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF})


def stamp(fig):
    if not FINAL:
        fig.text(0.99, 0.99, "DRAFT - not verified", ha="right", va="top", color="#e34948",
                 fontsize=9, fontweight="bold")


def bars(ax, rows, val, lo, hi, title, fmt="{:.2f}"):
    x = range(len(rows))
    for i, r in zip(x, rows):
        ax.bar(i, r[val], width=0.6, color=COL[r["zone"]], zorder=2)
        ax.plot([i, i], [r[lo], r[hi]], color=INK2, lw=1.2, zorder=3)
        ax.text(i, r[hi] * 1.02, fmt.format(r[val]), ha="center", va="bottom", color=INK, fontsize=8.5)
    ax.set_xticks(list(x), [ZLAB[r["zone"]] for r in rows])
    ax.set_title(title, loc="left", color=INK, fontsize=9.5)
    ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.set_ylim(0, max(r[hi] for r in rows) * 1.18)


def fig1():
    rows = [next(r for r in S["rates_pooled"] if r["zone"] == z) for z in ZONES]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.0))
    bars(a, rows, "crash_rate", "crash_rate_lo", "crash_rate_hi", "(a) Fatal crashes per 100 million VMT")
    bars(b, rows, "ped_rate", "ped_rate_lo", "ped_rate_hi", "(b) Pedestrian deaths per 100 million VMT",
         fmt="{:.3f}")
    # source and interval notes live in the figure caption
    fig.tight_layout()
    stamp(fig)
    fig.savefig(os.path.join(OUT, "fig1_rates_by_zone.png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig1_rates_by_zone.svg"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig1_rates_by_zone.pdf"), bbox_inches="tight")


def fig2():
    sizes = ["under 500", "500 to 2,499", "2,500 to 9,999"]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.8), sharey=True)
    for ax, sz in zip(axes, sizes):
        rows = [next(r for r in S["rates_by_size"] if r["size_band"] == sz and r["zone"] == z) for z in ZONES]
        bars(ax, rows, "ped_rate", "ped_rate_lo", "ped_rate_hi", f"Towns of {sz}", fmt="{:.3f}")
        ax.set_xticklabels([ZLAB[z].split("\n")[0] for z in ZONES], fontsize=7.5)
    top = max(r["ped_rate_hi"] for r in S["rates_by_size"]) * 1.18
    for ax in axes:
        ax.set_ylim(0, top)
    # title lives in the figure caption
    fig.tight_layout()
    stamp(fig)
    fig.savefig(os.path.join(OUT, "fig2_ped_rate_by_size.png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig2_ped_rate_by_size.svg"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig2_ped_rate_by_size.pdf"), bbox_inches="tight")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fig1()
    fig2()
    print("figures written", "(final)" if FINAL else "(draft)")
