#!/usr/bin/env python3
"""04_segments.py - cut highways into town-center, rest-of-town and outside-town pieces,
then place each fatal crash on its piece.

Plain-language note: every state or U.S. highway near a small town is chopped into
50-meter pieces. Each piece is labeled CENTER (inside the quarter-mile town center),
TOWN (inside town limits but not the center) or APPROACH (the same road, outside town,
up to 5 miles from the town line, not inside any other town or city). Each fatal crash
within 50 meters of one of these roads, that FARS also records as on a U.S. or state
highway or a state-owned road, is attached to the nearest piece. Pieces are then added
up into one row per town, route and zone. You do not need to open this file.

Usage: python code/04_segments.py MO [IA ...]   (no argument = every state with road data)
Outputs per state in data/processed/by_state/, combined by 05_combine.py.
"""
import glob
import json
import os
import re
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import LineString

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(PROC, "by_state")
CRS = "EPSG:5070"
NE = ["09", "23", "25", "33", "44", "50"]  # New England state FIPS
FIPS = {"AL": "01", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10", "DC": "11",
        "FL": "12", "GA": "13", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
        "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
        "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37",
        "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
        "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
        "WY": "56"}

CONFIG = {
    "piece_m": 50.0,             # piece length
    "approach_m": 8046.7,        # V3: 5 miles
    "snap_m": 50.0,              # V4: crash-to-road distance
    "fars_route_keep": [2, 3],   # FARS ROUTE: 2 U.S. highway, 3 state highway
    "fars_owner_keep": [1],      # FARS RD_OWNER: 1 state highway agency
    "years": 10,                 # 2015-2024 exposure window
}


def pieces(gdf, step):
    """Split every line into ~step-meter pieces, carrying attributes."""
    out_geom, out_idx = [], []
    for idx, geom in zip(gdf.index, gdf.geometry.values):
        for line in getattr(geom, "geoms", [geom]):
            L = line.length
            if L == 0:
                continue
            n = max(1, int(round(L / step)))
            d = np.linspace(0, L, n + 1)
            pts = [line.interpolate(x) for x in d]
            for a, b in zip(pts[:-1], pts[1:]):
                out_geom.append(LineString([a, b]))
                out_idx.append(idx)
    p = gdf.loc[out_idx].drop(columns="geometry").reset_index(names="sec_idx")
    return gpd.GeoDataFrame(p, geometry=out_geom, crs=gdf.crs)


SIGN = {3: "US", 4: "SR", 5: "BL"}          # HPMS routesigning: U.S., state, off-Interstate business
QUAL = {2: " ALT", 3: " BUS", 4: " BYP", 5: " SPUR", 6: " LOOP", 9: " TRUCK"}  # routequalifier


# Texas (and similar) route ids such as US0075-KG, FM0576-KG, SL0008-KG
TXRE = re.compile(r"^([A-Z]{2})0*(\d+)")
TXPFX = {"US": "US-{}", "SH": "SR-{}", "FM": "FM-{}", "RM": "RM-{}", "SL": "LOOP-{}", "SS": "SPUR-{}",
         "BU": "US-{} BUS", "BS": "SR-{} BUS", "BF": "FM-{} BUS", "BI": "BL-{}", "PR": "PARK-RD-{}",
         "UA": "US-{} ALT", "UP": "US-{} SPUR", "SA": "SR-{} ALT", "RE": "REC-RD-{}"}
NUMRE = re.compile(r"(\d+)")


def first_number(x):
    """Route number used to compare with the FARS road name; unnumbered labels never match."""
    if pd.isna(x) or str(x).startswith(("UNNUMBERED", "STATE-ROUTE-ID")):
        return -1
    m = NUMRE.search(str(x))
    return int(m.group(1)) if m else -1


# state-specific route_id codes that carry the route number (checked against rows that have both)
STATE_ID_RE = {
    "23": re.compile(r"^0*(\d+)[A-Z]{1,2}$"),        # Maine: 0172X -> 172
    "50": re.compile(r"^V0*(\d+)"),                  # Vermont: V012, V289-ES009A -> 12, 289
    "09": re.compile(r"^A0*(\d+)[A-Z]?$"),           # Connecticut: A015 -> 15
}
INVENTORY_NAME = re.compile(r"^(RD INV|NSH-)")       # Maine road-inventory / Vermont section codes


def route_key(df, fips=None):
    """Human-readable route identity, e.g. 'US-63', 'SR-61 BUS', 'BL-44', 'FM-576', 'SR-B'.
    Order: HPMS route number; route name (unless it is an inventory code); route number decoded from
    the state's route_id; otherwise 'UNNUMBERED <id>' (kept as a road, never used for name matching)."""
    labs = []
    sre = STATE_ID_RE.get(fips)
    for sg, nm, nme, q, rid in zip(df.routesigning, df.routenumber, df.routename, df.routequalifier,
                                   df.route_id):
        sign = SIGN.get(int(sg), "") if pd.notna(sg) else "SR"   # other codes: label by street name
        qual = QUAL.get(int(q), "") if pd.notna(q) else ""
        ident = str(int(nm)) if pd.notna(nm) else ""
        if not ident and pd.notna(nme) and str(nme).strip() and not INVENTORY_NAME.match(str(nme)):
            ident = str(nme).strip()
        if ident:
            labs.append(f"{sign}-{ident}{qual}" if sign else f"{ident}{qual}")
            continue
        rid = str(rid).strip()
        tx = TXRE.match(rid)
        st = sre.match(rid) if sre else None
        if tx:
            labs.append(TXPFX.get(tx.group(1), tx.group(1) + "-{}").format(int(tx.group(2))))
        elif st:
            labs.append(f"{sign or 'SR'}-{int(st.group(1))}")
        else:
            labs.append(f"UNNUMBERED {rid}")
    return df.route_id.astype(str), pd.Series(labs, index=df.index, dtype=object)


def run_state(st):
    fips = FIPS[st]
    hp = glob.glob(f"{RAW}/hpms/hpms_{st}_*.geojson")
    if not hp:
        print(st, "no road file yet")
        return
    towns = gpd.read_file(f"{PROC}/towns.gpkg")
    towns = towns[(towns.STATEFP == fips) & towns.geometry.notna() & ~towns.geometry.is_empty]
    towns = towns[["GEOID", "NAME", "pop2024", "size_band", "town_rule", "geometry"]]
    centers = gpd.read_file(f"{PROC}/centers.gpkg")
    centers = centers[centers.STATEFP == fips][["GEOID", "geometry"]]
    allplaces = gpd.read_file(f"zip://{RAW}/census/place/tl_2024_{fips}_place.zip").to_crs(CRS)
    if fips in NE:   # New England: villages and Census-drawn village areas also count as "in a town"
        allplaces = allplaces[allplaces.CLASSFP.str[0].isin(["C", "U"])]
    else:
        allplaces = allplaces[allplaces.CLASSFP.str.startswith("C")]  # every incorporated place, any size

    roads = gpd.read_file(hp[0]).to_crs(CRS)
    n_sec = len(roads)
    roads = roads[(roads.facility_type.fillna(2) != 6)   # 6 = second direction of a divided road
                  & (roads.f_system != 7)]               # 7 = local roads (no traffic counts)
    n_kept_sec = len(roads)
    roads["route_id"], roads["route_label"] = route_key(roads, fips)
    near = towns.buffer(CONFIG["approach_m"]).union_all()
    roads = roads[roads.intersects(near)]
    pc = pieces(roads, CONFIG["piece_m"])
    pc["len_m"] = pc.geometry.length
    mid = pc.copy()
    mid["geometry"] = pc.geometry.interpolate(0.5, normalized=True)

    # zone 1: center; zone 2: town; zone 3: approach (outside every incorporated place)
    z_c = gpd.sjoin(mid[["geometry"]], centers, predicate="within", how="inner")
    z_t = gpd.sjoin(mid[["geometry"]], towns[["GEOID", "geometry"]], predicate="within", how="inner")
    pc["GEOID"], pc["zone"] = None, None
    pc.loc[z_t.index, "GEOID"] = z_t.GEOID.values
    pc.loc[z_t.index, "zone"] = "TOWN"
    pc.loc[z_c.index, "GEOID"] = z_c.GEOID.values
    pc.loc[z_c.index, "zone"] = "CENTER"
    in_any = gpd.sjoin(mid[["geometry"]], allplaces[["geometry"]], predicate="within", how="inner").index
    outside = mid.index.difference(in_any.unique())
    outside = outside.difference(pc.index[pc.zone.notna()])  # never relabel a center or town piece
    # approach: nearest town on the same route, within 5 miles of the town line
    routes_in_town = pc.loc[pc.GEOID.notna(), ["route_label", "GEOID"]].drop_duplicates()
    cand = gpd.sjoin(mid.loc[outside, ["route_label", "geometry"]], gpd.GeoDataFrame(
        towns[["GEOID"]], geometry=towns.buffer(CONFIG["approach_m"]), crs=CRS),
        predicate="within", how="inner").reset_index(names="pid")
    cand = cand.merge(routes_in_town, on=["route_label", "GEOID"])  # route must enter that town
    tg = towns.set_index("GEOID").geometry
    cand["d"] = [mid.geometry[p].distance(tg[g]) for p, g in zip(cand.pid, cand.GEOID)]
    cand = cand.sort_values("d").drop_duplicates("pid")
    pc.loc[cand.pid, "GEOID"] = cand.GEOID.values
    pc.loc[cand.pid, "zone"] = "APPROACH"
    pc = pc[pc.zone.notna()].copy()

    # crashes
    cr = pd.read_parquet(f"{PROC}/crashes_all.parquet")
    cr = cr[(cr.STATE == int(fips)) & cr.has_coords]
    cr = gpd.GeoDataFrame(cr, geometry=gpd.points_from_xy(cr.LONGITUD, cr.LATITUDE), crs=4326).to_crs(CRS)
    cand = gpd.sjoin(cr, pc[["GEOID", "zone", "route_id", "route_label", "f_system", "geometry"]],
                     predicate="dwithin", distance=CONFIG["snap_m"], how="inner")
    cand["snap_m"] = shapely.distance(cand.geometry.values, pc.geometry.loc[cand.index_right.values].values)
    cand["name_match"] = [first_number(t) == first_number(r) and first_number(t) >= 0
                          for t, r in zip(cand.TWAY_ID, cand.route_label)]
    m = cand.sort_values(["name_match", "snap_m"], ascending=[False, True]).drop_duplicates("crash_id")
    interstate = (m.ROUTE == 1) | m.TWAY_ID.astype(str).str.match(r"^(I|IH)[- ]?\d")
    fars_hwy = ((m.ROUTE.isin(CONFIG["fars_route_keep"]) | m.RD_OWNER.isin(CONFIG["fars_owner_keep"])
                 | m.name_match) & ~interstate)  # never an Interstate crash (cross-street interchanges)
    m["fars_says_highway"] = fars_hwy
    keep = m[fars_hwy].copy()

    # aggregate pieces to town x route x zone
    w = pc.len_m
    pc["aadt_w"] = pc.aadt * w
    pc["has_aadt_m"] = np.where(pc.aadt.notna(), w, 0)
    pc["spd_w"] = pc.speed_limit * w
    pc["has_spd_m"] = np.where(pc.speed_limit.notna(), w, 0)
    pc["park_m"] = np.where(pc.peak_parking.fillna(0) > 0, w, 0)
    pc["lanes_w"] = pc.through_lanes * w
    pc["has_lanes_m"] = np.where(pc.through_lanes.notna(), w, 0)
    key = ["GEOID", "route_label", "zone"]
    g = pc.groupby(key).agg(route_ids=("route_id", lambda x: " ".join(sorted(set(x)))), len_m=("len_m", "sum"),
                            aadt_w=("aadt_w", "sum"), has_aadt_m=("has_aadt_m", "sum"),
                            spd_w=("spd_w", "sum"), has_spd_m=("has_spd_m", "sum"),
                            park_m=("park_m", "sum"), lanes_w=("lanes_w", "sum"),
                            has_lanes_m=("has_lanes_m", "sum"),
                            f_system=("f_system", lambda s: int(s.mode().iloc[0])),
                            us_signed=("routesigning", lambda s: bool((s == 3).any()))).reset_index()
    g["length_mi"] = g.len_m / 1609.344
    g["aadt"] = (g.aadt_w / g.has_aadt_m.replace(0, np.nan)).round(0)
    g["speed_limit_mph"] = (g.spd_w / g.has_spd_m.replace(0, np.nan)).round(1)
    g["through_lanes"] = (g.lanes_w / g.has_lanes_m.replace(0, np.nan)).round(2)
    g["share_onstreet_parking"] = (g.park_m / g.len_m).round(3)
    g["share_len_with_aadt"] = (g.has_aadt_m / g.len_m).round(3)
    g["vmt_10yr"] = g.aadt * g.length_mi * 365.25 * CONFIG["years"]
    c = keep.groupby(key).agg(fatal_crashes=("crash_id", "size"), fatalities=("FATALS", "sum"),
                              ped_fatalities=("ped_fatals", "sum"), bike_fatalities=("bike_fatals", "sum"),
                              night_crashes=("night", lambda s: int(s.fillna(False).sum())),
                              known_hour_crashes=("night", lambda s: int(s.notna().sum()))).reset_index()
    g = g.merge(c, on=key, how="left")
    for col in ["fatal_crashes", "fatalities", "ped_fatalities", "bike_fatalities", "night_crashes",
                "known_hour_crashes"]:
        g[col] = g[col].fillna(0).astype(int)
    g = g.merge(towns.drop(columns="geometry"), on="GEOID", how="left")
    g.insert(0, "segment_id", g.GEOID + "_" + g.route_label.str.replace(r"\W", "", regex=True) + "_" + g.zone)
    g["in_rate_base"] = g.f_system.between(2, 5) & (g.share_len_with_aadt >= 0.9)
    g = g.drop(columns=["aadt_w", "has_aadt_m", "spd_w", "has_spd_m", "park_m", "lanes_w", "has_lanes_m",
                        "len_m"])
    os.makedirs(OUT, exist_ok=True)
    g.to_csv(f"{OUT}/segments_{st}.csv", index=False)
    geo = pc.dissolve(by=key, as_index=False)[key + ["geometry"]]
    geo = geo.merge(g[key + ["segment_id"]], on=key).to_crs(4326)
    geo.to_file(f"{OUT}/segments_{st}.gpkg", driver="GPKG")
    keep_cols = ["crash_id", "YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "STATE", "COUNTY", "ST_CASE",
                 "LATITUDE", "LONGITUD", "ROUTE", "TWAY_ID", "RUR_URB", "FUNC_SYS", "RD_OWNER",
                 "FATALS", "ped_fatals", "bike_fatals", "night", "GEOID", "zone", "route_id",
                 "route_label", "f_system", "snap_m", "name_match"]
    keep["segment_id"] = keep.GEOID + "_" + keep.route_label.str.replace(r"\W", "", regex=True) + "_" + keep.zone
    keep[keep_cols + ["segment_id"]].to_csv(f"{OUT}/crashes_{st}.csv", index=False)
    qa = {"state": st, "hpms_sections": n_sec, "sections_after_dropping_dup_direction_and_local": n_kept_sec, "pieces_in_zones": len(pc),
          "crashes_in_state_with_coords": len(cr), "crashes_within_snap": len(m),
          "crashes_dropped_fars_not_highway": int((~fars_hwy).sum()),
          "dropped_fars_route_codes": m.loc[~fars_hwy, "ROUTE"].value_counts().to_dict(),
          "crashes_kept": len(keep), "kept_by_name_match_only": int((keep.name_match & ~keep.ROUTE.isin([2, 3])
                                                                     & (keep.RD_OWNER != 1)).sum()),
          "kept_with_name_match": int(keep.name_match.sum()), "segments": len(g),
          "miles_by_zone": g.groupby("zone").length_mi.sum().round(1).to_dict(),
          "crashes_by_zone": g.groupby("zone").fatal_crashes.sum().to_dict(),
          "towns_with_any_segment": int(g.GEOID.nunique()), "towns_in_state": len(towns)}
    json.dump(qa, open(f"{OUT}/qa_{st}.json", "w"), indent=2, default=int)
    print(json.dumps(qa, default=int))


if __name__ == "__main__":
    for s in sys.argv[1:] or sorted(FIPS):
        run_state(s)
