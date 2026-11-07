#!/usr/bin/env python3
"""02b_crashes.py - one row per fatal crash, 2015-2024, with location and victim counts.

Plain-language note: reads the ten yearly federal crash files and makes one clean
table: where and when each deadly crash happened, which kind of road FARS says it
was on, how many people died, and how many of them were walking or biking.
Output: data/processed/crashes_all.parquet. You do not need to open this file.
"""
import io
import json
import os
import zipfile

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "fars")
OUT = os.path.join(ROOT, "data", "processed")
YEARS = range(2015, 2025)

ACC = ["STATE", "ST_CASE", "COUNTY", "CITY", "YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "DAY_WEEK",
       "ROUTE", "TWAY_ID", "RUR_URB", "FUNC_SYS", "RD_OWNER", "LATITUDE", "LONGITUD",
       "LGT_COND", "PEDS", "FATALS"]


def read(z, stem, cols):
    name = next(n for n in z.namelist() if n.lower().endswith(f"/{stem}.csv") or n.lower() == f"{stem}.csv")
    df = pd.read_csv(io.BytesIO(z.read(name)), encoding="latin-1", low_memory=False)
    df.columns = [c.upper() for c in df.columns]
    return df[[c for c in cols if c in df.columns]]


def main():
    frames, qa = [], {}
    for y in YEARS:
        z = zipfile.ZipFile(os.path.join(RAW, f"FARS{y}NationalCSV.zip"))
        a = read(z, "accident", ACC)
        p = read(z, "person", ["ST_CASE", "PER_TYP", "INJ_SEV"])
        died = p[p.INJ_SEV == 4]
        g = died.groupby("ST_CASE").PER_TYP
        a["ped_fatals"] = a.ST_CASE.map(g.apply(lambda s: (s == 5).sum())).fillna(0).astype(int)
        a["bike_fatals"] = a.ST_CASE.map(g.apply(lambda s: s.isin([6, 7]).sum())).fillna(0).astype(int)
        a["YEAR"] = y
        qa[y] = {"crashes": len(a), "fatalities": int(a.FATALS.sum()),
                 "ped_fatalities": int(a.ped_fatals.sum()),
                 "deaths_in_person_file": int(len(died))}
        frames.append(a)
    c = pd.concat(frames, ignore_index=True)
    c["crash_id"] = c.YEAR.astype(str) + "_" + c.ST_CASE.astype(str)
    ok = c.LATITUDE.between(18, 72) & c.LONGITUD.between(-180, -60)
    c["has_coords"] = ok
    night = (c.HOUR.between(18, 23) | c.HOUR.between(0, 5)).astype("boolean")
    night[c.HOUR > 23] = pd.NA  # 99 = unknown hour
    c["night"] = night
    c.to_parquet(os.path.join(OUT, "crashes_all.parquet"), index=False)
    qa["total"] = {"crashes": len(c), "with_valid_coords": int(ok.sum()),
                   "fatalities": int(c.FATALS.sum())}
    json.dump(qa, open(os.path.join(OUT, "qa_crashes.json"), "w"), indent=2)
    print(json.dumps(qa, indent=1))


if __name__ == "__main__":
    main()
