#!/usr/bin/env python3
"""center_anchor_check.py - compare sampled town centers with each town's recognized center.

Plain-language note: for every town in the aerial-review samples, looks up the town's post
office, town or city hall, county courthouse (if any) and official place point in the USGS
Geographic Names Information System (2021 archive), and measures how far each is from our
town-center point. A center is "confirmed" when a civic anchor (post office, town/city hall,
courthouse) lies within a quarter mile (402 m); "place point only" when only the USGS place
point does; otherwise it is flagged for a closer look.

Usage: python -I tools/center_anchor_check.py docs/verify/aerial_sample_MO.csv docs/verify/aerial_sample_NE.csv
Writes data/verify/center_anchor_check.csv
"""
import math
import re
import sys

import pandas as pd

QMI = 402.3
ST = {"MO": "MO", "CT": "CT", "ME": "ME", "MA": "MA", "NH": "NH", "RI": "RI", "VT": "VT"}


def dist(a, b):
    R = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1])
    return 2 * R * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def nearest(df, c, maxd):
    if df.empty:
        return None, None
    d = [dist(c, (la, lo)) for la, lo in zip(df.PRIM_LAT_DEC, df.PRIM_LONG_DEC)]
    i = min(range(len(d)), key=d.__getitem__)
    return (df.iloc[i].FEATURE_NAME, round(d[i])) if d[i] <= maxd else (None, None)


rows = []
gn = {}
for f in sys.argv[1:]:
    s = pd.read_csv(f)
    for _, r in s.iterrows():
        st = r.state
        if st not in gn:
            g = pd.read_csv(f"data/raw/gnis/{st}_Features_20210825.txt", sep="|", dtype=str, encoding="utf-8-sig")
            g = g[g.PRIM_LAT_DEC.astype(float) != 0]
            g["PRIM_LAT_DEC"] = g.PRIM_LAT_DEC.astype(float)
            g["PRIM_LONG_DEC"] = g.PRIM_LONG_DEC.astype(float)
            gn[st] = g
        g = gn[st]
        c = (r.center_lat, r.center_lon)
        t = re.escape(r.town)
        po = g[(g.FEATURE_CLASS == "Post Office") & g.FEATURE_NAME.str.match(rf"^{t}\b.*Post Office", case=False)]
        hall = g[(g.FEATURE_CLASS == "Building") & g.FEATURE_NAME.str.match(
            rf"^{t}\b.*(City|Town|Village|Municipal)\s*(Hall|Building|Offices?)", case=False)]
        court = g[(g.FEATURE_CLASS == "Building") & g.FEATURE_NAME.str.contains("Courthouse", case=False)]
        place = g[(g.FEATURE_CLASS.isin(["Populated Place", "Civil", "Census"])) &
                  (g.FEATURE_NAME.str.replace(r"^(City|Town|Village) of ", "", regex=True).str.lower() == r.town.lower())]
        po_n, po_d = nearest(po, c, 15000)
        h_n, h_d = nearest(hall, c, 15000)
        ct_n, ct_d = nearest(court, c, 3000)
        pl_n, pl_d = nearest(place[place.FEATURE_CLASS == "Populated Place"], c, 15000)
        civic = [d for d in (po_d, h_d, ct_d) if d is not None]
        if civic and min(civic) <= QMI:
            v = "confirmed (civic anchor within 1/4 mi)"
        elif pl_d is not None and pl_d <= QMI:
            v = "place point only within 1/4 mi"
        else:
            v = "flag: no anchor within 1/4 mi"
        rows.append({"town": r.town, "state": st, "post_office": po_n, "post_office_m": po_d, "town_hall": h_n,
                     "town_hall_m": h_d, "courthouse": ct_n, "courthouse_m": ct_d, "usgs_place_point_m": pl_d,
                     "nearest_civic_m": min(civic) if civic else None, "anchor_result": v})
out = pd.DataFrame(rows)
out.to_csv("data/verify/center_anchor_check.csv", index=False)
pd.set_option("display.width", 250)
print(out[["town", "state", "post_office_m", "town_hall_m", "courthouse_m", "usgs_place_point_m", "anchor_result"]].to_string(index=False))
print(out.anchor_result.value_counts().to_dict())
