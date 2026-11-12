#!/usr/bin/env python3
"""07_readme.py - write README.md with every number taken from paper/stats.json.

Plain-language note: rebuilds the project's front page so its numbers always match the data.
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
A = json.load(open(os.path.join(ROOT, "AUTHORS.json")))["authors"][0]
FINAL = "--final" in sys.argv
R = {r["zone"]: r for r in S["rates_pooled"]}
status = "Released" if FINAL else "DRAFT, not yet verified by the author"
VERSION = "1.0.0"
CONCEPT_DOI = "10.5281/zenodo.24030310"  # all versions
VERSION_DOI = "10.5281/zenodo.24030311"  # v1.0.0
txt = f"""# Main Street Highways

[![DOI](https://zenodo.org/badge/DOI/{CONCEPT_DOI}.svg)](https://doi.org/{CONCEPT_DOI})

**Status:** {status}. Version {VERSION}, built from FARS {S['years']} and HPMS {S['hpms_year']}.

In thousands of small American towns, the main street is also a state or U.S. highway. This project is an open dataset of
those roads. It covers every state and U.S. highway that runs through or near a town of under 10,000 people in the lower
48 states. Each road is split into three parts: the town center, the rest of town, and the same road just outside town.
Every fatal crash from {S['years']} is placed on its part.
In New England, where towns are large areas that include farmland and forest, town limits are the town's villages;
results are reported with and without New England ({S['n_new_england_towns_with_segment']:,} towns).

**What it shows.** Across {S['n_main_street_towns']:,} towns where a highway runs through the town center, fatal crashes
per mile driven are lower in the center ({R['CENTER']['crash_rate']:.2f} per 100 million vehicle miles) than just outside
town ({R['APPROACH']['crash_rate']:.2f}). Pedestrian deaths per mile driven are {S['ped_rate_ratio_center_vs_approach']:.1f}
times higher in the center ({R['CENTER']['ped_rate']:.3f} versus {R['APPROACH']['ped_rate']:.3f}). In town centers,
{R['CENTER']['ped_share']:.0%} of the people killed were walking, compared with {R['APPROACH']['ped_share']:.0%} outside town.

## Contents

| File | What it is |
|---|---|
| `data/processed/segments.csv` | {S['n_segments']:,} rows: one per town, route and zone, with length, traffic, crashes and deaths |
| `data/processed/segments_geo.parquet` | Map lines for every segment (GeoParquet, WGS84; join on `segment_id`) |
| `data/processed/centers_geo.parquet` | Town-center circles (GeoParquet) |
| `data/processed/crashes_matched.csv` | {S['n_crashes_matched']:,} fatal crashes, each placed on one segment |
| `data/processed/towns.csv` | {S['n_towns']:,} small towns with their center location |
| `data/processed/qa_report.txt` | Quality report: counts, losses, checks, spot checks |
| `docs/CODEBOOK.md` | Every column defined |
| `docs/LIMITATIONS.md` | What the data cannot tell you |
| `paper/` | Statistics file (`stats.json`) and figures |
| `docs/verify/` | Verification records: aerial-imagery review of 45 sampled town centers |
| `data/verify/fars_api_check.csv` | Spot-check crashes compared with NHTSA's live FARS records |

## How to rebuild

Python 3.11 or newer with geopandas, duckdb, scipy, pyarrow, openpyxl and matplotlib.

```
python code/01_fetch.py fars
python code/01_fetch.py census
python code/01_fetch.py hpms            # all states, about 1 hour
python code/01b_fetch_overture.py
python code/02_towns.py
python code/02b_crashes.py
python code/03_centers.py
python code/04_segments.py              # all states, about 45 minutes
python code/05_combine.py
python code/06_figures.py
python code/07_readme.py
python code/09_package.py              # compact map files for release
```

Every download is logged with its source address, date and SHA-256 fingerprint in `data/raw/PROVENANCE.txt`.

## Sources

- NHTSA Fatality Analysis Reporting System (FARS), national CSV files {S['years']}.
- FHWA Highway Performance Monitoring System (HPMS), {S['hpms_year']} spatial data, via geo.dot.gov.
- U.S. Census Bureau TIGER/Line 2024 places; Vintage 2024 population estimates; 2020 urban areas.
- Overture Maps Foundation places, release 2026-10-21.0 (includes data from OpenStreetMap contributors, ODbL).

## License and citation

Code: MIT. Data and documents: CC BY 4.0, with credit to the sources above.
Cite as: {A['name']} (2026). *Main Street Highways: fatal crashes on state and U.S. highways through small-town centers*
(Version {VERSION}) [Data set]. Zenodo. https://doi.org/{CONCEPT_DOI}
(all versions; this version: https://doi.org/{VERSION_DOI})

Paper describing the dataset: {A['name']} (2026). *Main Street Highways: Fatal Crashes on State and U.S. Highways Through
Small-Town Centers in the United States, 2015–2024*. engrXiv preprint. https://doi.org/10.31224/8795

Maintainer: {A['name']}, {A['affiliation']}. ORCID {A['orcid']}.
"""
open(os.path.join(ROOT, "README.md"), "w").write(txt)
print("README written")
