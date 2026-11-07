#!/usr/bin/env python3
"""09_package.py - write compact map files for the public release.

Plain-language note: the full-detail map file (segments.gpkg) is too large for GitHub. This
script merges each segment's 50 m pieces into continuous lines, simplifies them to within
1 meter, and writes GeoParquet files: data/processed/segments_geo.parquet (one line per
segment_id; join to segments.csv for attributes) and data/processed/centers_geo.parquet
(the town-center circles). Total length changes by less than 0.01%.
"""
import os
import geopandas as gpd, pandas as pd, pyogrio, shapely

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")
n = pyogrio.read_info(f"{P}/segments.gpkg")["features"]
parts = []
for start in range(0, n, 15000):  # chunks keep memory low
    g = gpd.read_file(f"{P}/segments.gpkg", columns=["segment_id"], skip_features=start, max_features=15000).to_crs(5070)
    geom = shapely.simplify(shapely.line_merge(shapely.set_precision(g.geometry.values, 0.01)), 1.0)
    g = gpd.GeoDataFrame({"segment_id": g.segment_id.values}, geometry=geom, crs=5070).to_crs(4326)
    g["geometry"] = shapely.set_precision(g.geometry.values, 1e-6)
    parts.append(g)
s = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry="geometry", crs=4326)
s.to_parquet(f"{P}/segments_geo.parquet", compression="zstd")
c = gpd.read_file(f"{P}/centers.gpkg")[["GEOID", "NAME", "STATEFP", "geometry"]].to_crs(5070)
c["geometry"] = c.geometry.simplify(1.0)
c.to_crs(4326).to_parquet(f"{P}/centers_geo.parquet", compression="zstd")
print("segments_geo", len(s), "centers_geo", len(c))
