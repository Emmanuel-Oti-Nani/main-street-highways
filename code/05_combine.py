#!/usr/bin/env python3
"""05_combine.py - join the state files into the national dataset, write the quality
report and the statistics file.

Plain-language note: stitches the 48 state results into the final tables
(data/processed/segments.csv, segments.gpkg, crashes_matched.csv), then writes
data/processed/qa_report.txt (the quality report: counts, losses, checks) and
paper/stats.json (every number the paper quotes). Open qa_report.txt; you do not
need to open this script.
"""
import glob
import json
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import chi2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
BY = os.path.join(PROC, "by_state")
REGION = {  # Census regions by state FIPS
    "Northeast": ["09", "23", "25", "33", "44", "50", "34", "36", "42"],
    "Midwest": ["17", "18", "26", "39", "55", "19", "20", "27", "29", "31", "38", "46"],
    "South": ["10", "11", "12", "13", "24", "37", "45", "51", "54", "01", "21", "28", "47", "05", "22",
              "40", "48"],
    "West": ["04", "08", "16", "30", "32", "35", "49", "56", "06", "41", "53"],
}
ST_REGION = {f: r for r, fs in REGION.items() for f in fs}
ZONES = ["CENTER", "TOWN", "APPROACH"]
NE = ["09", "23", "25", "33", "44", "50"]


def pois_ci(k, a=0.05):
    lo = chi2.ppf(a / 2, 2 * k) / 2 if k > 0 else 0.0
    hi = chi2.ppf(1 - a / 2, 2 * (k + 1)) / 2
    return lo, hi


def rate_table(df, by=None):
    keys = ([by] if by else []) + ["zone"]
    a = df.groupby(keys)[["length_mi", "vmt_10yr", "fatal_crashes", "fatalities", "ped_fatalities",
                          "bike_fatalities", "night_crashes", "known_hour_crashes"]].sum()
    out = []
    for idx, r in a.iterrows():
        k, kp, v = r.fatal_crashes, r.ped_fatalities, r.vmt_10yr / 1e8
        lo, hi = pois_ci(k)
        plo, phi = pois_ci(kp)
        out.append({**dict(zip(keys, idx if isinstance(idx, tuple) else (idx,))),
                    "miles": round(r.length_mi, 1), "vmt_100m": round(v, 2),
                    "fatal_crashes": int(k), "fatalities": int(r.fatalities),
                    "ped_fatalities": int(kp), "bike_fatalities": int(r.bike_fatalities),
                    "crash_rate": round(k / v, 3), "crash_rate_lo": round(lo / v, 3),
                    "crash_rate_hi": round(hi / v, 3),
                    "ped_rate": round(kp / v, 3), "ped_rate_lo": round(plo / v, 3), "ped_rate_hi": round(phi / v, 3),
                    "ped_share": round(kp / r.fatalities, 5) if r.fatalities else None,
                    "night_share": round(r.night_crashes / r.known_hour_crashes, 5) if r.known_hour_crashes else None})
    return out


def main():
    segs = pd.concat([pd.read_csv(f, dtype={"GEOID": str, "route_ids": str})
                      for f in sorted(glob.glob(f"{BY}/segments_*.csv"))], ignore_index=True)
    segs["STATEFP"] = segs.GEOID.str[:2]
    segs["region"] = segs.STATEFP.map(ST_REGION)
    crashes = pd.concat([pd.read_csv(f, dtype={"GEOID": str}) for f in sorted(glob.glob(f"{BY}/crashes_*.csv"))],
                        ignore_index=True)
    qas = [json.load(open(f)) for f in sorted(glob.glob(f"{BY}/qa_*.json"))]
    towns = pd.read_csv(f"{PROC}/towns.csv", dtype={"GEOID": str, "STATEFP": str})
    assert segs.segment_id.is_unique, "duplicate segment ids"
    assert crashes.crash_id.is_unique, "a crash was assigned twice"
    assert crashes.segment_id.isin(segs.segment_id).all(), "crash on unknown segment"

    segs.to_csv(f"{PROC}/segments.csv", index=False)
    crashes.to_csv(f"{PROC}/crashes_matched.csv", index=False)
    geo = pd.concat([gpd.read_file(f) for f in sorted(glob.glob(f"{BY}/segments_*.gpkg"))], ignore_index=True)
    geo = gpd.GeoDataFrame(geo.merge(segs, on=["segment_id"], suffixes=("_g", "")), crs=4326)
    geo = geo[[c for c in geo.columns if not c.endswith("_g")]]
    geo.to_file(f"{PROC}/segments.gpkg", driver="GPKG")

    base = segs[segs.in_rate_base]
    center_towns = segs[segs.zone == "CENTER"].GEOID.unique()
    allc = pd.read_parquet(f"{PROC}/crashes_all.parquet")
    lower48 = allc[~allc.STATE.isin([2, 15])]
    stats = {
        "years": "2015-2024", "hpms_year": 2024,
        "n_states": len(qas),
        "n_towns": int(len(towns)), "n_towns_with_center": int(towns.has_center.sum()),
        "n_towns_with_segment": int(segs.GEOID.nunique()),
        "n_main_street_towns": int(len(center_towns)),
        "n_segments": int(len(segs)),
        "miles_by_zone": segs.groupby("zone").length_mi.sum().round(1).to_dict(),
        "crashes_by_zone": segs.groupby("zone").fatal_crashes.sum().astype(int).to_dict(),
        "fatalities_by_zone": segs.groupby("zone").fatalities.sum().astype(int).to_dict(),
        "n_crashes_matched": int(len(crashes)),
        "n_crashes_lower48": int(len(lower48)),
        "share_of_us_fatal_crashes": round(len(crashes) / len(lower48), 4),
        "name_match_share": round(float(crashes.name_match.mean()), 3),
        "rate_base_share_of_crashes": round(base.fatal_crashes.sum() / segs.fatal_crashes.sum(), 3),
        "rates_pooled": rate_table(base),
        "rates_pooled_excl_new_england": rate_table(base[~base.STATEFP.isin(NE)]),
        "rates_new_england_only": rate_table(base[base.STATEFP.isin(NE)]),
        "n_new_england_towns_with_segment": int(segs[segs.STATEFP.isin(NE)].GEOID.nunique()),
        "rates_by_size": rate_table(base, "size_band"),
        "rates_by_region": rate_table(base, "region"),
        "rates_by_us_signed": rate_table(base.assign(route_type=np.where(base.us_signed, "US", "State")),
                                         "route_type"),
        "speed_limit_by_zone": (base.assign(w=base.speed_limit_mph * base.length_mi)
                                .groupby("zone").apply(lambda d: d.w.sum() / d.loc[d.speed_limit_mph.notna(),
                                                                                    "length_mi"].sum())
                                .round(3).to_dict()),
        "crashes_by_hour": {z: {int(h): int(n) for h, n in grp.items()} for z, grp in
                            pd.crosstab(crashes[crashes.HOUR <= 23].zone,
                                        crashes[crashes.HOUR <= 23].HOUR).iterrows()},
    }
    pc = crashes[(crashes.ped_fatals > 0) & crashes.night.notna()]
    stats["ped_crash_night_share_by_zone"] = pc.groupby("zone").night.apply(
        lambda x: round(float(x.astype(bool).mean()), 5)).to_dict()
    stats["ped_crashes_by_zone"] = crashes[crashes.ped_fatals > 0].groupby("zone").size().astype(int).to_dict()
    stats["n_regions_center_higher_ped"] = sum(
        1 for reg in REGION if next(r["ped_rate"] for r in stats["rates_by_region"]
                                    if r["region"] == reg and r["zone"] == "CENTER") >
        next(r["ped_rate"] for r in stats["rates_by_region"] if r["region"] == reg and r["zone"] == "APPROACH"))
    stats["towns_by_rule"] = json.load(open(f"{PROC}/qa_towns.json"))["towns_by_rule"]
    stats["n_ne_towns_total"] = int(sum(v for k, v in stats["towns_by_rule"].items() if "new england" in k))
    stats["ped_rate_ratio_center_vs_approach"] = round(
        next(r["ped_rate"] for r in stats["rates_pooled"] if r["zone"] == "CENTER") /
        next(r["ped_rate"] for r in stats["rates_pooled"] if r["zone"] == "APPROACH"), 2)
    os.makedirs(os.path.join(ROOT, "paper"), exist_ok=True)
    json.dump(stats, open(os.path.join(ROOT, "paper", "stats.json"), "w"), indent=1, default=str)

    # quality report
    import sys
    L = ["MAIN STREET HIGHWAYS - QUALITY REPORT" + ("" if "--final" in sys.argv else " (DRAFT)"), "=" * 60, ""]
    tq = json.load(open(f"{PROC}/qa_towns.json"))
    cq = json.load(open(f"{PROC}/qa_centers.json"))
    L += ["1. TOWNS", f"   Census places, all states: {tq['places_all_states']:,}",
          f"   Incorporated places, lower 48 + DC outside New England: {tq['incorporated_lower48_dc']:,}",
          f"   Under 10,000 (2024 est.), incl. New England towns: {tq['under_pop_max']:,}",
          f"   Dropped as suburbs (>50% inside urban area 50k+): {tq['dropped_as_suburbs']:,}",
          f"   New England towns (county subdivisions) under 10,000: {tq['ne_towns_under_pop_max']:,}",
          f"   Small towns kept: {tq['towns']:,}  by size: {tq['towns_by_size']}",
          f"   By rule: {tq['towns_by_rule']}",
          f"   Towns with an identifiable center (>=10 destinations in 1/4 mi): {cq['towns_with_center']:,}",
          f"   Share with center by size: {cq['share_with_center_by_size']}", ""]
    L += ["2. ROADS AND SEGMENTS (per state)"]
    hdr = f"   {'st':3}{'sections':>10}{'kept':>10}{'center mi':>10}{'town mi':>9}{'appr mi':>9}{'crashes':>8}{'dropped':>8}"
    L.append(hdr)
    for q in qas:
        mz = q["miles_by_zone"]
        L.append(f"   {q['state']:3}{q['hpms_sections']:>10,}{q['sections_after_dropping_dup_direction_and_local']:>10,}"
                 f"{mz.get('CENTER', 0):>10,.0f}{mz.get('TOWN', 0):>9,.0f}{mz.get('APPROACH', 0):>9,.0f}"
                 f"{q['crashes_kept']:>8,}{q['crashes_dropped_fars_not_highway']:>8,}")
    L += ["", "3. CRASH MATCHING",
          f"   Fatal crashes, lower 48 + DC, 2015-2024: {len(lower48):,}",
          f"   Within 50 m of a study road: {sum(q['crashes_within_snap'] for q in qas):,}",
          f"   Dropped because FARS records a non-highway or Interstate road: "
          f"{sum(q['crashes_dropped_fars_not_highway'] for q in qas):,}",
          f"   Kept: {len(crashes):,}  (CENTER {stats['crashes_by_zone'].get('CENTER', 0):,}, "
          f"TOWN {stats['crashes_by_zone'].get('TOWN', 0):,}, APPROACH {stats['crashes_by_zone'].get('APPROACH', 0):,})",
          f"   Snap distance median {crashes.snap_m.median():.1f} m, 95th pct {crashes.snap_m.quantile(.95):.1f} m",
          f"   FARS ROUTE code of kept crashes: {crashes.ROUTE.value_counts().to_dict()}",
          f"   FARS road name number matches the assigned route: {crashes.name_match.mean():.1%} of kept crashes",
          f"   Kept only because of that name match (FARS route/owner codes blank or 'other'): "
          f"{sum(q.get('kept_by_name_match_only', 0) for q in qas):,}",
          "   Integrity: every crash on exactly one segment; segment ids unique (asserted).", ""]
    L += ["4. RATE BASE",
          "   Rates use segments on principal arterials, minor arterials and major collectors",
          "   (HPMS f_system 2-5) with traffic counts on >=90% of length.",
          f"   Share of matched crashes inside the rate base: {stats['rate_base_share_of_crashes']:.1%}",
          f"   AADT is the 2024 snapshot applied to all ten years (see LIMITATIONS).", ""]
    L += ["5. POOLED RESULTS (rate base)"]
    for r in stats["rates_pooled"]:
        L.append(f"   {r['zone']:9} miles {r['miles']:>9,.0f}  crashes {r['fatal_crashes']:>6,}  "
                 f"rate {r['crash_rate']:.3f} [{r['crash_rate_lo']:.3f}-{r['crash_rate_hi']:.3f}]  "
                 f"ped rate {r['ped_rate']:.3f} [{r['ped_rate_lo']:.3f}-{r['ped_rate_hi']:.3f}]  "
                 f"ped share {r['ped_share']:.1%}  night {r['night_share']:.1%}")
    L += ["", "5b. ROBUSTNESS: WITHOUT NEW ENGLAND (towns from county subdivisions, village limits)"]
    for r in stats["rates_pooled_excl_new_england"]:
        L.append(f"   {r['zone']:9} crashes {r['fatal_crashes']:>6,}  rate {r['crash_rate']:.3f}  "
                 f"ped rate {r['ped_rate']:.3f}  ped share {r['ped_share']:.1%}")
    L += ["   New England only:"]
    for r in stats["rates_new_england_only"]:
        L.append(f"   {r['zone']:9} crashes {r['fatal_crashes']:>6,}  rate {r['crash_rate']:.3f}  "
                 f"ped rate {r['ped_rate']:.3f}  ped share {(r['ped_share'] or 0):.1%}")
    L += ["", "6. SPOT CHECKS (look these up in FARS: year, state, ST_CASE)"]
    rng = np.random.default_rng(7)
    picks = []
    for z in ZONES:
        sub = crashes[crashes.zone == z]
        picks += sub.iloc[rng.choice(len(sub), size=min(2, len(sub)), replace=False)].to_dict("records")
    big = crashes.sort_values("FATALS", ascending=False).iloc[0].to_dict()
    picks.append(big)
    for p in picks:
        L.append(f"   {p['crash_id']}: state {p['STATE']}, ST_CASE {p['ST_CASE']}, {p['YEAR']}-{p['MONTH']:02d}-"
                 f"{p['DAY']:02d} hour {p['HOUR']}, {p['FATALS']} killed, ped {p['ped_fatals']}, "
                 f"FARS road '{p['TWAY_ID']}', our route {p['route_label']}, zone {p['zone']}, "
                 f"lat {p['LATITUDE']:.5f} lon {p['LONGITUD']:.5f}")
    open(f"{PROC}/qa_report.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
