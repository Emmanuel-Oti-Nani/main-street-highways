#!/usr/bin/env python3
"""11_maps.py - map figures for the spatial-analysis version of the paper.

Plain-language note: draws two maps from the processed data.
  Map 1: every small town where a state or U.S. highway runs through the town center,
         with the towns that had a pedestrian death in the center highlighted.
  Map 2: one example town (Stockton, Missouri) showing how a highway is split into
         the town center, the rest of town, and the 5 miles outside town, with the
         everyday destinations used to locate the center and the fatal crashes.
Also redraws the two charts in the paper's Times-style font.

Usage: python3 code/11_maps.py STATES_ZIP OUTDIR
  STATES_ZIP = Census cartographic state boundaries (cb_2024_us_state_20m.zip), used only
               as a background outline.
"""
import os
import sys

import duckdb
import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
OVT = os.path.join(ROOT, "data", "raw", "overture", "places_us48_2026-10-21.0.parquet")
STATES_ZIP, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
CRS = "EPSG:5070"
EXAMPLE = "2970828"  # Stockton, Missouri (in the 45-town verification sample)

for f in ["regular", "bold", "italic"]:
    p = f"/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-{f}.otf"
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
COL = {"CENTER": "#DC267F", "TOWN": "#FE6100", "APPROACH": "#648FFF"}  # IBM color-blind-safe
INK, INK2, LINE = "#0b0b0b", "#52514e", "#bdbcb7"
plt.rcParams.update({"font.family": "TeX Gyre Termes", "font.size": 9, "pdf.fonttype": 42,
                     "figure.facecolor": "white", "axes.facecolor": "white"})


def save(fig, name):
    for ext in ["pdf", "png"]:
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


seg = pd.read_csv(f"{PROC}/segments.csv", dtype={"GEOID": str, "STATEFP": str})
cr = pd.read_csv(f"{PROC}/crashes_matched.csv", dtype={"GEOID": str})
cen = gpd.read_file(f"{PROC}/centers.gpkg")
states = gpd.read_file(f"zip://{STATES_ZIP}")
states = states[~states.STUSPS.isin(["AK", "HI", "PR"])].to_crs(CRS)

# ---------- Map 1: national ----------
ms = seg[seg.zone == "CENTER"].GEOID.unique()                       # main street towns
ped = cr[cr.zone == "CENTER"].groupby("GEOID").ped_fatals.sum()
pts = cen[cen.GEOID.isin(ms)].copy()
pts["geometry"] = gpd.points_from_xy(pts.cen_x, pts.cen_y)
pts["ped"] = pts.GEOID.map(ped).fillna(0)
hit = pts[pts.ped > 0]
fig, ax = plt.subplots(figsize=(7.0, 4.4))
states.boundary.plot(ax=ax, color=LINE, lw=0.45, zorder=1)
pts[pts.ped == 0].plot(ax=ax, color="#9a9994", markersize=0.6, zorder=2, rasterized=True)
hit.sort_values("ped").plot(ax=ax, color=COL["CENTER"], markersize=hit.sort_values("ped").ped * 7,
                            edgecolor="white", linewidth=0.25, zorder=3)
ax.set_axis_off()
ax.legend(handles=[
    Line2D([], [], marker="o", ls="", color="#9a9994", ms=2.5,
           label=f"Town center on a state or U.S. highway, no pedestrian death ({(pts.ped == 0).sum():,})"),
    Line2D([], [], marker="o", ls="", color=COL["CENTER"], ms=4,
           label=f"Pedestrian death(s) in the town center ({len(hit):,}; symbol size = deaths)")],
    loc="lower left", frameon=False, fontsize=8, bbox_to_anchor=(0.0, -0.06))
save(fig, "map1_national")
print("map1", len(pts), "towns;", len(hit), "with center ped deaths;", int(hit.ped.sum()), "deaths")

# ---------- Map 2: example town ----------
towns = gpd.read_file(f"{PROC}/towns.gpkg")
town = towns[towns.GEOID == EXAMPLE]
c = cen[cen.GEOID == EXAMPLE]
sg = gpd.read_parquet(f"{PROC}/segments_geo.parquet")          # stored in WGS 84
sg = sg[sg.segment_id.str.startswith(EXAMPLE + "_")].to_crs(CRS)
sg["zone"] = sg.segment_id.str.rsplit("_", n=1).str[-1]
k = cr[cr.GEOID == EXAMPLE]
k = gpd.GeoDataFrame(k, geometry=gpd.points_from_xy(k.LONGITUD, k.LATITUDE), crs=4326).to_crs(CRS)
x0, y0, x1, y1 = town.to_crs(4326).total_bounds
cats = ("'shopping','food_and_drink','services_and_business','community_and_government','education',"
        "'health_care','lodging','arts_and_entertainment','lifestyle_services','cultural_and_historic'")
d = duckdb.sql(f"""SELECT lon, lat FROM '{OVT}' WHERE tax_top IN ({cats}) AND confidence >= 0.5
    AND coalesce(operating_status,'open') NOT IN ('permanently_closed','temporarily_closed')
    AND lon BETWEEN {x0} AND {x1} AND lat BETWEEN {y0} AND {y1}""").df()
d = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(CRS)
d = d[d.within(town.geometry.iloc[0])]

fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.6), gridspec_kw={"width_ratios": [1.15, 1]})
for ax, zoom in [(a, False), (b, True)]:
    town.plot(ax=ax, facecolor="#f3f2ee", edgecolor="#8f8e89", lw=0.6, zorder=1)
    c.plot(ax=ax, facecolor=COL["CENTER"], alpha=0.12, edgecolor=COL["CENTER"], lw=0.8, zorder=2)
    for z in ["APPROACH", "TOWN", "CENTER"]:
        sz = sg[sg.zone == z]
        if len(sz):
            sz.plot(ax=ax, color=COL[z], lw=2.4 if z == "CENTER" else 1.6, zorder=3)
    if zoom:
        d.plot(ax=ax, color=INK, markersize=3, zorder=4)
    kk = k.copy()
    kk.plot(ax=ax, marker="X", color=INK, markersize=26 if zoom else 18, edgecolor="white",
            linewidth=0.5, zorder=5)
    ax.set_axis_off()
    ax.set_aspect("equal")
cb = c.geometry.iloc[0].buffer(260).bounds
b.set_xlim(cb[0], cb[2])
b.set_ylim(cb[1], cb[3])
tb = town.geometry.iloc[0].buffer(8200).bounds
a.set_xlim(tb[0], tb[2])
a.set_ylim(tb[1], tb[3])
a.add_patch(plt.Rectangle((cb[0], cb[1]), cb[2] - cb[0], cb[3] - cb[1], fill=False, ec=INK2, lw=0.7, zorder=6))
# scale bars
for ax, L, lab in [(a, 1609.34 * 2, "2 mi"), (b, 402.3, "¼ mi")]:
    xa, xb = ax.get_xlim()
    ya, yb = ax.get_ylim()
    sx, sy = xa + 0.06 * (xb - xa), ya + 0.05 * (yb - ya)
    ax.plot([sx, sx + L], [sy, sy], color=INK, lw=1.5, zorder=7)
    ax.text(sx + L / 2, sy + 0.025 * (yb - ya), lab, ha="center", fontsize=8, color=INK)
fig.canvas.draw()
for ax, t in [(a, "(a) Town and 5-mile approaches"), (b, "(b) Town center (quarter-mile circle)")]:
    x = ax.get_position().x0
    fig.text(x, 0.97, t, fontsize=9, color=INK, ha="left", va="bottom")
fig.legend(handles=[
    Line2D([], [], color=COL["CENTER"], lw=2.4, label="Town center"),
    Line2D([], [], color=COL["TOWN"], lw=1.6, label="Rest of town"),
    Line2D([], [], color=COL["APPROACH"], lw=1.6, label="Outside town (0–5 mi)"),
    Patch(facecolor="#f3f2ee", edgecolor="#8f8e89", label="Town limits"),
    Line2D([], [], marker="o", ls="", color=INK, ms=2.5, label="Everyday destination"),
    Line2D([], [], marker="X", ls="", color=INK, ms=6, label="Fatal crash, 2015–2024")],
    loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.08))
save(fig, "map2_example_town")
print("map2", town.NAME.iloc[0], "segments", sg.zone.value_counts().to_dict(), "crashes",
      k.zone.value_counts().to_dict(), "destinations", len(d), "center dest", int(c.dest_in_center.iloc[0]))
