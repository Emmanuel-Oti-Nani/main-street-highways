#!/usr/bin/env python3
"""Independent check: compare spot-check crashes in crashes_matched.csv with NHTSA's live FARS API.

Plain-language note: for each listed crash, asks NHTSA's own crash-lookup service for the case and
compares date, hour, road name, deaths, pedestrian deaths and location with our table.
Writes data/verify/fars_api_check.csv.
"""
import json, re, sys, time, urllib.request
import pandas as pd

CASES = sys.argv[1:]  # crash_id values like 2016_290356
c = pd.read_csv("data/processed/crashes_matched.csv", dtype={"GEOID": str}).set_index("crash_id")
t = pd.read_csv("data/processed/towns.csv", dtype={"GEOID": str}).set_index("GEOID")
rows = []
for cid in CASES:
    yr, case = cid.split("_"); st = int(case) // 10000
    url = f"https://crashapi.nhtsa.dot.gov/crashes/GetCaseDetails?stateCase={case}&caseYear={yr}&state={st}&format=json"
    d = json.load(urllib.request.urlopen(url, timeout=60))
    res = d["Results"][0][0]["CrashResultSet"]
    persons = [p for v in (res.get("Vehicles") or []) for p in (v.get("Persons") or [])] + (res.get("NParticipants") or res.get("NPersons") or [])
    ped_killed = sum(1 for p in persons if str(p.get("PER_TYP")) == "5" and str(p.get("INJ_SEV")) == "4")
    o = c.loc[cid]
    api = {"date": f"{res['YEAR']}-{int(res['MONTH']):02d}-{int(res['DAY']):02d}", "hour": int(res["HOUR"]),
           "road": res.get("TWAY_ID"), "killed": int(res["FATALS"]), "ped_killed": ped_killed,
           "lat": float(res["LATITUDE"]), "lon": float(res["LONGITUD"])}
    ours = {"date": f"{o.YEAR}-{int(o.MONTH):02d}-{int(o.DAY):02d}", "hour": int(o.HOUR), "road": o.TWAY_ID,
            "killed": int(o.FATALS), "ped_killed": int(o.ped_fatals), "lat": float(o.LATITUDE), "lon": float(o.LONGITUD)}
    same = {k: (abs(api[k] - ours[k]) < 1e-4 if k in ("lat", "lon") else
                (re.sub(r"\s+", " ", str(api[k])).strip() == re.sub(r"\s+", " ", str(ours[k])).strip()))
            for k in api}
    rows.append({"crash_id": cid, "town": t.NAME.get(o.GEOID, ""), "zone": o.zone, "our_route": o.route_label,
                 **{f"api_{k}": v for k, v in api.items()}, **{f"ours_{k}": v for k, v in ours.items()},
                 "all_match": all(same.values()), "mismatches": ",".join(k for k, v in same.items() if not v)})
    time.sleep(0.5)
out = pd.DataFrame(rows)
out.to_csv("data/verify/fars_api_check.csv", index=False)
print(out[["crash_id", "town", "zone", "our_route", "api_date", "api_hour", "api_road", "api_killed", "api_ped_killed", "all_match", "mismatches"]].to_string(index=False))
