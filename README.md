# Main Street Highways

**Status:** Released. Version 1.0.0, built from FARS 2015-2024 and HPMS 2024.

In thousands of small American towns, the main street is also a state or U.S. highway. This project is an open dataset of
those roads. It covers every state and U.S. highway that runs through or near a town of under 10,000 people in the lower
48 states. Each road is split into three parts: the town center, the rest of town, and the same road just outside town.
Every fatal crash from 2015-2024 is placed on its part.
In New England, where towns are large areas that include farmland and forest, town limits are the town's villages;
results are reported with and without New England (678 towns).

**What it shows.** Across 8,995 towns where a highway runs through the town center, fatal crashes
per mile driven are lower in the center (0.97 per 100 million vehicle miles) than just outside
town (1.27). Pedestrian deaths per mile driven are 3.0
times higher in the center (0.276 versus 0.093). In town centers,
26% of the people killed were walking, compared with 6% outside town.

## Contents

| File | What it is |
|---|---|
| `data/processed/segments.csv` | 72,301 rows: one per town, route and zone, with length, traffic, crashes and deaths |
| `data/processed/segments_geo.parquet` | Map lines for every segment (GeoParquet, WGS84; join on `segment_id`) |
| `data/processed/centers_geo.parquet` | Town-center circles (GeoParquet) |
| `data/processed/crashes_matched.csv` | 39,300 fatal crashes, each placed on one segment |
| `data/processed/towns.csv` | 15,195 small towns with their center location |
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

- NHTSA Fatality Analysis Reporting System (FARS), national CSV files 2015-2024.
- FHWA Highway Performance Monitoring System (HPMS), 2024 spatial data, via geo.dot.gov.
- U.S. Census Bureau TIGER/Line 2024 places; Vintage 2024 population estimates; 2020 urban areas.
- Overture Maps Foundation places, release 2026-10-21.0 (includes data from OpenStreetMap contributors, ODbL).

## License and citation

Code: MIT. Data and documents: CC BY 4.0, with credit to the sources above.
Cite as: Emmanuel Oti Nani (2027). *Main Street Highways: fatal crashes on state and U.S. highways through small-town centers*
(Version 1.0.0) [Data set]. Zenodo.

Maintainer: Emmanuel Oti Nani, Independent Researcher, Springfield, Missouri, USA. ORCID 0009-0009-4175-8962.
