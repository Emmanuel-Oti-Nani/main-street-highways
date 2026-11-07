#!/usr/bin/env python3
"""03_centers.py - find each small town's center.

Plain-language note: for every town, this script takes the shops, restaurants,
offices, schools, churches, clinics and other everyday destinations inside town
limits, finds the spot where the most of them sit within a quarter mile, and
calls the quarter-mile circle around that spot the town center. A town needs at
least 10 destinations inside that circle to get a center. Gas stations, car
dealers and other travel businesses are left out so a highway strip at the edge
of town is not mistaken for downtown.
Output: data/processed/centers.gpkg (one circle per town) and towns.csv.
"""
import json
import os

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
OVT = os.path.join(ROOT, "data", "raw", "overture", "places_us48_2026-10-21.0.parquet")
CRS = "EPSG:5070"

CONFIG = {  # V1: town center definition
    "radius_m": 402.3,          # one quarter mile
    "min_destinations": 10,
    "min_confidence": 0.5,
    "categories": ["shopping", "food_and_drink", "services_and_business", "community_and_government",
                   "education", "health_care", "lodging", "arts_and_entertainment",
                   "lifestyle_services", "cultural_and_historic"],
    # excluded on purpose: travel_and_transportation (fuel, auto), geographic_entities,
    # sports_and_recreation (parks, fields often at town edge), uncategorized
}


def main():
    towns = gpd.read_file(f"{PROC}/towns_base.gpkg")  # from 02; towns.gpkg written below
    search = gpd.read_file(f"{PROC}/towns_search.gpkg").set_index("GEOID").geometry  # whole town area
    cats = ",".join(f"'{c}'" for c in CONFIG["categories"])
    r = CONFIG["radius_m"]
    rows, n_poi, n_in = [], 0, 0
    for st, tw in towns.groupby("STATEFP"):          # one state at a time keeps memory low
        tws = gpd.GeoDataFrame(tw[["GEOID"]], geometry=search.loc[tw.GEOID].values, crs=CRS)
        xmin, ymin, xmax, ymax = tws.to_crs(4326).total_bounds
        poi = duckdb.sql(f"""
            SELECT id, lon, lat, tax_top FROM '{OVT}'
            WHERE tax_top IN ({cats}) AND confidence >= {CONFIG['min_confidence']}
              AND coalesce(operating_status, 'open') NOT IN ('permanently_closed', 'temporarily_closed')
              AND lon BETWEEN {xmin} AND {xmax} AND lat BETWEEN {ymin} AND {ymax}""").df()
        n_poi += len(poi)
        poi = gpd.GeoDataFrame(poi, geometry=gpd.points_from_xy(poi.lon, poi.lat), crs=4326).to_crs(CRS)
        poi = gpd.sjoin(poi, tws, predicate="within", how="inner")
        n_in += len(poi)
        for geoid, g in poi.groupby("GEOID"):
            xy = np.column_stack([g.geometry.x.values, g.geometry.y.values])
            if len(xy) < CONFIG["min_destinations"]:
                rows.append((geoid, len(xy), 0, np.nan, np.nan))
                continue
            t = cKDTree(xy)
            counts = np.array([len(n) for n in t.query_ball_point(xy, r)])
            peak = xy[counts.argmax()]
            c = xy[t.query_ball_point(peak, r)].mean(axis=0)  # one step toward the cluster middle
            n_c = len(t.query_ball_point(c, r))
            if n_c < counts.max():                            # keep whichever holds more destinations
                c, n_c = peak, counts.max()
            rows.append((geoid, len(xy), int(n_c), c[0], c[1]))
    cen = pd.DataFrame(rows, columns=["GEOID", "dest_in_town", "dest_in_center", "cen_x", "cen_y"])
    towns = towns.merge(cen, on="GEOID", how="left")
    towns["dest_in_town"] = towns.dest_in_town.fillna(0).astype(int)
    towns["dest_in_center"] = towns.dest_in_center.fillna(0).astype(int)
    towns["has_center"] = towns.dest_in_center >= CONFIG["min_destinations"]
    c = towns[towns.has_center].copy()
    circ = gpd.GeoSeries(gpd.points_from_xy(c["cen_x"], c["cen_y"]), crs=CRS).buffer(r, 64).values
    c["geometry"] = gpd.GeoSeries(circ, index=c.index, crs=CRS).intersection(
        gpd.GeoSeries(search.loc[c.GEOID].values, index=c.index, crs=CRS))
    c = gpd.GeoDataFrame(c, geometry="geometry", crs=CRS)
    c.to_file(f"{PROC}/centers.gpkg", driver="GPKG")
    # New England towns with no village: the center circle stands in for town limits
    nov = towns.town_rule.str.contains("no village")
    cg = c.set_index("GEOID").geometry
    towns["geometry"] = [cg[g] if (nv and g in cg.index) else geom
                         for g, nv, geom in zip(towns.GEOID, nov, towns.geometry)]
    towns = gpd.GeoDataFrame(towns, geometry="geometry", crs=CRS)
    towns[towns.geometry.notna()].drop(columns=["cen_x", "cen_y", "dest_in_town", "dest_in_center",
                                                "has_center"]).to_file(f"{PROC}/towns.gpkg", driver="GPKG")
    pts = gpd.GeoSeries(gpd.points_from_xy(towns["cen_x"], towns["cen_y"]), crs=CRS).to_crs(4326)
    towns["center_lat"], towns["center_lon"] = pts.y.round(6), pts.x.round(6)
    towns.drop(columns=["geometry", "cen_x", "cen_y"]).to_csv(f"{PROC}/towns.csv", index=False)
    qa = {"destinations_in_state_boxes": n_poi, "destinations_in_towns": n_in, "towns": len(towns),
          "towns_with_center": int(towns.has_center.sum()),
          "share_with_center_by_size": towns.groupby("size_band").has_center.mean().round(3).to_dict(),
          "towns_with_center_by_rule": towns.groupby("town_rule").has_center.mean().round(3).to_dict(),
          "median_dest_in_center": float(towns.loc[towns.has_center, "dest_in_center"].median()),
          "config": CONFIG}
    json.dump(qa, open(f"{PROC}/qa_centers.json", "w"), indent=2)
    print(json.dumps(qa, indent=2))


if __name__ == "__main__":
    main()
