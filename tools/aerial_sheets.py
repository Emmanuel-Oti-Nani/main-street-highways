#!/usr/bin/env python3
"""Aerial review images for the town-center sample.

Plain-language note: for each sampled town, downloads a satellite image of the center (Esri World
Imagery, for review only, not redistributed) and draws the quarter-mile center circle (white), town
limits (yellow dashed) and the study highways by zone (blue = center, orange = rest of town,
green = outside town). Writes one image per town plus contact sheets of nine.
"""
import io, os, sys, urllib.request
import geopandas as gpd, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

OUT = "docs/verify/aerial"; os.makedirs(OUT, exist_ok=True)
HALF = 750  # meters each side of the center
COL = {"CENTER": "#2a78d6", "TOWN": "#eb6834", "APPROACH": "#1baf7a"}
towns = gpd.read_file("data/processed/towns.gpkg").to_crs(3857).set_index("GEOID")
cents = gpd.read_file("data/processed/centers.gpkg").to_crs(3857).set_index("GEOID")
t = pd.read_csv("data/processed/towns.csv", dtype={"GEOID": str}).set_index("GEOID")
files = []
for sample in sys.argv[1:]:
    s = pd.read_csv(sample)
    for _, r in s.iterrows():
        cand = t[(t.NAME == r.town) & t.center_lat.notna()]
        g = ((cand.center_lat - r.center_lat) ** 2 + (cand.center_lon - r.center_lon) ** 2).idxmin()
        cx, cy = gpd.GeoSeries(gpd.points_from_xy([r.center_lon], [r.center_lat]), crs=4326).to_crs(3857).iloc[0].coords[0]
        bb = (cx - HALF, cy - HALF, cx + HALF, cy + HALF)
        url = ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?"
               f"bbox={bb[0]},{bb[1]},{bb[2]},{bb[3]}&bboxSR=3857&imageSR=3857&size=700,700&format=jpg&f=image")
        img = Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=60).read()))
        segs = gpd.read_file("data/processed/segments.gpkg", bbox=tuple(gpd.GeoSeries(
            gpd.points_from_xy([bb[0], bb[2]], [bb[1], bb[3]]), crs=3857).to_crs(4326).total_bounds)).to_crs(3857)
        fig, ax = plt.subplots(figsize=(5, 5.35), dpi=110)
        ax.imshow(img, extent=(bb[0], bb[2], bb[1], bb[3]))
        for z, c in COL.items():
            sz = segs[segs.zone == z]
            if len(sz): sz.plot(ax=ax, color=c, linewidth=3.2, alpha=0.95)
        if g in towns.index and towns.geometry[g] is not None:
            gpd.GeoSeries([towns.geometry[g].boundary], crs=3857).plot(ax=ax, color="#ffd400", linewidth=1.2, linestyle="--")
        if g in cents.index:
            gpd.GeoSeries([cents.geometry[g].boundary], crs=3857).plot(ax=ax, color="white", linewidth=1.6)
        ax.set_xlim(bb[0], bb[2]); ax.set_ylim(bb[1], bb[3]); ax.set_axis_off()
        ax.set_title(f"{r.town}, {r.state} (pop {int(r.population_2024):,})", fontsize=10, loc="left")
        fig.text(0.01, 0.005, "Imagery: Esri, Maxar, Earthstar Geographics | white = center, blue/orange/green = study highway by zone",
                 fontsize=5.5, color="#333")
        fn = f"{OUT}/{r.state}_{r.town.replace(' ', '_')}.png"
        fig.savefig(fn, bbox_inches="tight"); plt.close(fig); files.append(fn)
        print("ok", fn, flush=True)
# contact sheets, 9 per sheet
ims = [Image.open(f).convert("RGB") for f in files]
w, h = max(i.size[0] for i in ims), max(i.size[1] for i in ims)
for k in range(0, len(ims), 9):
    sheet = Image.new("RGB", (w * 3, h * 3), "white")
    for j, im in enumerate(ims[k:k + 9]):
        sheet.paste(im, ((j % 3) * w, (j // 3) * h))
    sheet.save(f"{OUT}/sheet_{k // 9 + 1}.jpg", quality=85)
print("sheets", (len(ims) + 8) // 9)
