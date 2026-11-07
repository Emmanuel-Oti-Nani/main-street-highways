#!/usr/bin/env python3
"""01_fetch.py - download every raw input and log where it came from.

Plain-language note: this script downloads the public files the project uses
(federal fatal crash files, Census town boundaries and populations, the federal
road inventory) and writes a line for each into data/raw/PROVENANCE.txt saying
exactly where it came from, when, and a fingerprint (SHA-256) of the file.
You do not need to open this file; run it with `python code/01_fetch.py`.

Usage:
  python code/01_fetch.py fars            # FARS national CSV zips, 2015-2024
  python code/01_fetch.py census          # TIGER 2024 places (all states) + population estimates
  python code/01_fetch.py hpms MO [MO ...]# HPMS 2024 US/state signed routes, per state
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
LOG = os.path.join(RAW, "PROVENANCE.txt")
PROV = os.path.join(ROOT, "tools", "provenance.py")

FARS_YEARS = range(2015, 2025)
NEW_ENGLAND = ["CT", "ME", "MA", "NH", "RI", "VT"]
HPMS_YEAR = 2024
PAGE_WORKERS = int(os.environ.get("PAGE_WORKERS", "6"))
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10",
    "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
    "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35",
    "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56",
}


def log(path, url, note=None):
    cmd = [sys.executable, PROV, path, url, "--log", LOG]
    if note:
        cmd += ["--note", note]
    subprocess.run(cmd, check=True, capture_output=True)


def get(url, dest, note=None, tries=4):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for i in range(tries):
        try:
            tmp = dest + ".part"
            with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            os.replace(tmp, dest)
            log(dest, url, note)
            return dest
        except Exception as e:  # noqa: BLE001
            print(f"  retry {i+1} {url}: {e}", file=sys.stderr)
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"failed: {url}")


def fetch_fars():
    for y in FARS_YEARS:
        url = f"https://static.nhtsa.gov/nhtsa/downloads/FARS/{y}/National/FARS{y}NationalCSV.zip"
        get(url, os.path.join(RAW, "fars", f"FARS{y}NationalCSV.zip"))
        print("fars", y, "ok", flush=True)


def fetch_census():
    for st, fips in STATE_FIPS.items():
        url = f"https://www2.census.gov/geo/tiger/TIGER2024/PLACE/tl_2024_{fips}_place.zip"
        get(url, os.path.join(RAW, "census", "place", f"tl_2024_{fips}_place.zip"))
    for st in NEW_ENGLAND:  # New England towns are county subdivisions, not places
        fips = STATE_FIPS[st]
        url = f"https://www2.census.gov/geo/tiger/TIGER2024/COUSUB/tl_2024_{fips}_cousub.zip"
        get(url, os.path.join(RAW, "census", "cousub", f"tl_2024_{fips}_cousub.zip"))
    url = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024.csv"
    get(url, os.path.join(RAW, "census", "sub-est2024.csv"))
    print("census ok", flush=True)


HPMS_FIELDS = ("objectid,data_year,state_id,route_id,begin_point,end_point,f_system,routenumber,"
               "routename,routesigning,routequalifier,urban_id,facility_type,ownership,county_id,"
               "through_lanes,peak_parking,number_signals,stop_signs,aadt,access_control,"
               "speed_limit,sectionlength")


# US- or state-signed routes, plus any state-owned (ownership 1) non-Interstate, non-local
# road; ramps (facility_type 4) and Interstates (f_system 1, routesigning 2) excluded.
# Route signing alone misses states that leave it blank (e.g. Tennessee).
HPMS_WHERE = ("(routesigning IN (3,4) OR (ownership = 1 AND f_system IN (2,3,4,5,6))) "
              "AND f_system <> 1 AND (routesigning IS NULL OR routesigning <> 2) "
              "AND (facility_type IS NULL OR facility_type <> 4)")


def fetch_hpms(st):
    """Page through the FHWA ArcGIS service for US- and state-signed routes (routesigning 3 or 4)."""
    svc = f"https://geo.dot.gov/server/rest/services/Hosted/HPMS_FULL_{st}_{HPMS_YEAR}/FeatureServer/0/query"
    dest = os.path.join(RAW, "hpms", f"hpms_{st}_{HPMS_YEAR}.geojson")
    if os.path.exists(dest):
        return
    where = HPMS_WHERE
    for t in range(8):
        try:
            n = json.load(urllib.request.urlopen(svc + "?" + urllib.parse.urlencode(
                {"where": where, "returnCountOnly": "true", "f": "json"}), timeout=300))["count"]
            break
        except Exception as e:  # noqa: BLE001
            print("  retry count", st, e, file=sys.stderr, flush=True)
            time.sleep(5 * (t + 1))
    else:
        raise RuntimeError(f"hpms {st} count")
    def page(off):
        q = {"where": where, "outFields": HPMS_FIELDS, "outSR": "4326", "geometryPrecision": "5",
             "orderByFields": "objectid", "resultOffset": off, "resultRecordCount": 2000, "f": "geojson"}
        for t in range(8):
            try:
                return json.load(urllib.request.urlopen(svc + "?" + urllib.parse.urlencode(q),
                                                        timeout=300))["features"]
            except Exception as e:  # noqa: BLE001
                print("  retry", st, off, e, file=sys.stderr, flush=True)
                time.sleep(5 * (t + 1))
        raise RuntimeError(f"hpms {st} offset {off}")

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(PAGE_WORKERS) as ex:
        feats = [f for chunk in ex.map(page, range(0, n, 2000)) for f in chunk]
    if len(feats) != n:
        print(f"  WARNING {st}: expected {n} got {len(feats)}", file=sys.stderr, flush=True)
    tmp = dest + ".part"
    with open(tmp, "w") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f)
    os.replace(tmp, dest)
    log(dest, svc, note=f"ArcGIS REST paged query where={where}; outFields={HPMS_FIELDS}; outSR=4326; "
        f"geometryPrecision=5; orderBy objectid; {len(feats)} of {n} features")
    print("hpms", st, len(feats), "of", n, flush=True)


def safe(st):
    try:
        fetch_hpms(st)
    except Exception as e:  # noqa: BLE001
        print("FAILED", st, e, file=sys.stderr, flush=True)


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "fars":
        fetch_fars()
    elif what == "census":
        fetch_census()
    elif what == "hpms":
        from concurrent.futures import ThreadPoolExecutor
        states = sys.argv[2:] or list(STATE_FIPS)
        with ThreadPoolExecutor(int(os.environ.get('STATE_WORKERS', '2'))) as ex:
            for st, r in zip(states, ex.map(lambda x: (safe(x), x), states)):
                pass
