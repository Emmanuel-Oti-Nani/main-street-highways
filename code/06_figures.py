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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
OUT = os.path.join(ROOT, "paper", "figures")
FINAL = "--final" in sys.argv
ZONES = ["CENTER", "TOWN", "APPROACH"]
ZLAB = {"CENTER": "Town center", "TOWN": "Rest of town", "APPROACH": "Outside town\n(0-5 mi)"}
COL = {"CENTER": "#2a78d6", "TOWN": "#eb6834", "APPROACH": "#1baf7a"}  # validated, light mode
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
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
        ax.text(i, r[hi] * 1.02, fmt.format(r[val]), ha="center", va="bottom", color=INK, fontsize=10)
    ax.set_xticks(list(x), [ZLAB[r["zone"]] for r in rows])
    ax.set_title(title, loc="left", color=INK, fontsize=11)
    ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.set_ylim(0, max(r[hi] for r in rows) * 1.18)


def fig1():
    rows = [next(r for r in S["rates_pooled"] if r["zone"] == z) for z in ZONES]
    fig, (a, b) = plt.subplots(1, 2, figsize=(9, 3.9))
    bars(a, rows, "crash_rate", "crash_rate_lo", "crash_rate_hi", "A. Fatal crashes per 100 million vehicle miles")
    bars(b, rows, "ped_rate", "ped_rate_lo", "ped_rate_hi", "B. Pedestrian deaths per 100 million vehicle miles",
         fmt="{:.3f}")
    fig.text(0.01, -0.04, f"State and U.S. highways in and near {S['n_towns_with_segment']:,} U.S. towns under 10,000 people, lower 48 "
             f"states, {S['years']}. FARS crashes; HPMS {S['hpms_year']} traffic. Whiskers: 95% Poisson intervals.",
             fontsize=8, color=INK2)
    fig.tight_layout()
    stamp(fig)
    fig.savefig(os.path.join(OUT, "fig1_rates_by_zone.png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig1_rates_by_zone.svg"), bbox_inches="tight")


def fig2():
    sizes = ["under 500", "500 to 2,499", "2,500 to 9,999"]
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.6), sharey=True)
    for ax, sz in zip(axes, sizes):
        rows = [next(r for r in S["rates_by_size"] if r["size_band"] == sz and r["zone"] == z) for z in ZONES]
        bars(ax, rows, "ped_rate", "ped_rate_lo", "ped_rate_hi", f"Towns of {sz}", fmt="{:.3f}")
        ax.set_xticklabels([ZLAB[z].split("\n")[0] for z in ZONES], fontsize=8.5)
    top = max(r["ped_rate_hi"] for r in S["rates_by_size"]) * 1.18
    for ax in axes:
        ax.set_ylim(0, top)
    fig.suptitle("Pedestrian deaths per 100 million vehicle miles, by town size", x=0.01, ha="left",
                 color=INK, fontsize=11)
    fig.tight_layout()
    stamp(fig)
    fig.savefig(os.path.join(OUT, "fig2_ped_rate_by_size.png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig2_ped_rate_by_size.svg"), bbox_inches="tight")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fig1()
    fig2()
    print("figures written", "(final)" if FINAL else "(draft)")
