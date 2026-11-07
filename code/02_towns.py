#!/usr/bin/env python3
"""02_towns.py - build the list of small towns.

Plain-language note: this script makes the list of towns the project studies.
A town is kept if it is an incorporated place (a real city, town or village with
its own government), had fewer than 10,000 people in the 2024 Census estimate,
and is not mostly inside a big urban area of 50,000 or more (that would make it
a suburb). Output: data/processed/towns.gpkg and towns.csv. You do not need to
open this file.

Rule settings live in the CONFIG block so the author can change them in one place.
"""
import glob
import json
import os

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "census")
OUT = os.path.join(ROOT, "data", "processed")
CRS = "EPSG:5070"  # USA Contiguous Albers Equal Area, meters (AK/HI handled in their own pass if added)

CONFIG = {
    "pop_max": 10000,              # V2: small-town cutoff (2024 estimate, exclusive)
    "incorporated_only": True,     # V2: drop Census Designated Places
    "big_ua_pop": 50000,           # V2: urban area size that makes a place a suburb
    "big_ua_share": 0.5,           # V2: share of place land inside a big urban area to drop it
    "exclude_states": ["02", "15"],  # Alaska, Hawaii: different road system, handled later if wanted
    # New England: towns are county subdivisions (T1 towns, C5 cities). Their land runs far beyond the
    # settled village, so "town limits" for the zones is the village: incorporated villages/boroughs and
    # Census Designated Places inside the town. The whole town is still searched for its center.
    "new_england": ["09", "23", "25", "33", "44", "50"],
    "ne_town_classes": ["T1", "C5"],
    "ne_village_classes": ["C1", "C2", "C5", "C7", "C8", "C9", "U1", "U2"],
}


def main():
    os.makedirs(OUT, exist_ok=True)
    places = pd.concat([gpd.read_file(f"zip://{p}") for p in sorted(glob.glob(f"{RAW}/place/*.zip"))])
    n_all = len(places)
    places_ne_all = places[places.STATEFP.isin(CONFIG["new_england"])]
    places = places[~places.STATEFP.isin(CONFIG["exclude_states"] + CONFIG["new_england"])]
    if CONFIG["incorporated_only"]:
        places = places[places.CLASSFP.str.startswith("C") & (places.FUNCSTAT == "A")]
    n_inc = len(places)

    pop0 = pd.read_csv(f"{RAW}/sub-est2024.csv", dtype=str, encoding="latin-1")
    pop = pop0[pop0.SUMLEV == "162"].copy()
    pop["GEOID"] = pop.STATE + pop.PLACE
    pop["pop2020"] = pop.ESTIMATESBASE2020.astype(int)
    pop["pop2024"] = pop.POPESTIMATE2024.astype(int)
    places = places.merge(pop[["GEOID", "pop2020", "pop2024"]], on="GEOID", how="left")
    n_nopop = int(places.pop2024.isna().sum())
    places = places[places.pop2024.notna() & (places.pop2024 < CONFIG["pop_max"])].copy()
    n_small = len(places)

    places = places.to_crs(CRS)
    places["town_rule"] = "incorporated place"
    places["search_geom"] = places.geometry

    # New England towns
    cs = pd.concat([gpd.read_file(f"zip://{p}") for p in sorted(glob.glob(f"{RAW}/cousub/*.zip"))]).to_crs(CRS)
    n_ne_all = len(cs)
    cs = cs[cs.CLASSFP.isin(CONFIG["ne_town_classes"])].reset_index(drop=True)
    mcd = pop0[pop0.SUMLEV == "061"].copy()
    mcd["GEOID"] = mcd.STATE + mcd.COUNTY + mcd.COUSUB
    mcd["pop2020"] = mcd.ESTIMATESBASE2020.astype(int)
    mcd["pop2024"] = mcd.POPESTIMATE2024.astype(int)
    cs = cs.merge(mcd[["GEOID", "pop2020", "pop2024"]].drop_duplicates("GEOID"), on="GEOID", how="left")
    n_ne_nopop = int(cs.pop2024.isna().sum())
    cs = cs[cs.pop2024.notna() & (cs.pop2024 < CONFIG["pop_max"])].copy()
    vil = places_ne_all[places_ne_all.CLASSFP.isin(CONFIG["ne_village_classes"])].to_crs(CRS).reset_index(drop=True)
    vpt = vil.copy()
    vpt["geometry"] = vil.geometry.representative_point()
    hit = gpd.sjoin(vpt[["geometry"]], cs[["GEOID", "geometry"]], predicate="within", how="inner")
    vil = vil.loc[hit.index].assign(TOWN=hit.GEOID.values)
    vgeom = vil.dissolve(by="TOWN").geometry
    cs["search_geom"] = cs.geometry
    cs["geometry"] = [vgeom[g].intersection(sg) if g in vgeom.index else None
                      for g, sg in zip(cs.GEOID, cs.search_geom)]
    cs["town_rule"] = np.where(cs.geometry.notna(), "new england town, village limits",
                               "new england town, no village (center only)")
    cs["PLACEFP"] = cs.COUSUBFP
    ne = gpd.GeoDataFrame(cs[["GEOID", "STATEFP", "PLACEFP", "NAME", "NAMELSAD", "CLASSFP", "pop2020",
                              "pop2024", "town_rule", "search_geom", "geometry"]], geometry="geometry", crs=CRS)
    n_ne_small = len(ne)
    places = pd.concat([places[ne.columns], ne], ignore_index=True)
    places = gpd.GeoDataFrame(places, geometry="geometry", crs=CRS)
    n_small += n_ne_small

    ua = gpd.read_file(f"zip://{RAW}/tl_2024_us_uac20.zip").to_crs(CRS)
    uapop = pd.read_excel(f"{RAW}/2020_Census_ua_list_all.xlsx", dtype={"UACE": str})
    uapop["UACE"] = uapop.UACE.str.zfill(5)
    ua = ua.merge(uapop[["UACE", "POP"]], left_on="UACE20", right_on="UACE", how="left")
    big = ua[ua.POP >= CONFIG["big_ua_pop"]][["geometry"]]
    sg = gpd.GeoDataFrame(places[["GEOID"]], geometry=gpd.GeoSeries(places.search_geom, crs=CRS), crs=CRS)
    places["area_m2"] = sg.geometry.area
    inter = gpd.overlay(sg, big, how="intersection", keep_geom_type=True)
    inter["a"] = inter.geometry.area
    share = inter.groupby("GEOID").a.sum()
    places["big_ua_share"] = places.GEOID.map(share).fillna(0) / places.area_m2
    suburbs = places[places.big_ua_share > CONFIG["big_ua_share"]]
    towns = places[places.big_ua_share <= CONFIG["big_ua_share"]].copy()

    towns["size_band"] = pd.cut(towns.pop2024, [-1, 499, 2499, 9999],
                                labels=["under 500", "500 to 2,499", "2,500 to 9,999"]).astype(str)
    cols = ["GEOID", "STATEFP", "PLACEFP", "NAME", "NAMELSAD", "CLASSFP", "pop2020", "pop2024",
            "size_band", "town_rule", "big_ua_share", "geometry"]
    search = gpd.GeoDataFrame(towns[["GEOID"]], geometry=gpd.GeoSeries(towns.search_geom, crs=CRS), crs=CRS)
    search.to_file(f"{OUT}/towns_search.gpkg", driver="GPKG")
    towns = towns[cols]
    towns.to_file(f"{OUT}/towns_base.gpkg", driver="GPKG")
    towns.drop(columns="geometry").to_csv(f"{OUT}/towns_all.csv", index=False)
    qa = {"places_all_states": n_all, "incorporated_lower48_dc": n_inc, "no_population_match": n_nopop,
          "under_pop_max": n_small, "ne_cousubs_all": n_ne_all, "ne_no_population_match": n_ne_nopop,
          "ne_towns_under_pop_max": n_ne_small,
          "towns_by_rule": towns.town_rule.value_counts().to_dict(), "dropped_as_suburbs": len(suburbs), "towns": len(towns),
          "towns_by_size": towns.size_band.value_counts().to_dict(), "config": CONFIG}
    json.dump(qa, open(f"{OUT}/qa_towns.json", "w"), indent=2)
    print(json.dumps(qa, indent=2))


if __name__ == "__main__":
    main()
