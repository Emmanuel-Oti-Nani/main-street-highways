# Build spec: Main Street Highways

*Plain-language note: this is the one-page plan the whole build follows. Each field has a plain explanation under it. If the project changes shape, this file is updated first.*

```
PROJECT:   Main Street Highways. Archetypes: open dataset (1) + analysis paper (TRB 2028).

QUESTION:  On U.S. and state highways that serve as the main street of a small town
           (under 10,000 people), how do fatal crashes, pedestrian deaths, and time of
           day compare with the same routes outside town?

SOURCES:   FARS 2015-2024 national CSV (NHTSA), accident + person files.
             https://static.nhtsa.gov/nhtsa/downloads/FARS/{year}/National/
           HPMS 2024 full spatial submission per state (FHWA, geo.dot.gov ArcGIS REST),
             US-signed and state-signed routes only (routesigning 3, 4).
           Census TIGER/Line 2024 places, all 50 states + DC.
           Census Vintage 2024 subcounty population estimates (sub-est2024.csv).
           Overture Maps places + land_use themes, release 2026-10-21.0 (S3, open license;
             land_use derived from OpenStreetMap, ODbL). Substitutes for direct
             OpenStreetMap download, which is not reachable from the build environment.
           All public; access dates in data/raw/PROVENANCE.txt.

UNIT:      Route-zone segment: one town x one signed route x one zone.
           Zones: CENTER (town center), TOWN (inside town limits, outside center),
           APPROACH (same route, 0 to 5 miles outside town limits, not inside any other place).
           Also a crash-level file (one row per fatal crash matched to a segment).

MEASURES:  length_mi; AADT (length-weighted); VMT_10yr = AADT x length x 365.25 x 10 days
           fatal_crashes, fatalities, ped_fatalities (PER_TYP 5), bike_fatalities (6, 7)
           fatal_crash_rate per 100 million VMT; night_share (crashes 6pm-6am);
           speed_limit, through_lanes, on-street parking (HPMS context)
           Comparison: CENTER vs TOWN vs APPROACH, pooled and by route type and region.

OUTPUTS:   data/processed/segments.csv, segments_geo.parquet, centers_geo.parquet,
           crashes_matched.csv, towns.csv, qa_report.txt
           docs/CODEBOOK.md, LIMITATIONS.md, VERIFY_CHECKLIST.md (verification record)
           paper/stats.json, paper/figures/*, paper/manuscript_TRB2028.docx (TRB format,
           7,500-word limit incl. tables), paper/preprint/ (two-column preprint)

VENUES:    GitHub (public repo) -> Zenodo DOI (published Nov 7, 2026: 10.5281/zenodo.24030310)
           -> TRB 2028 Annual Meeting paper (submission window ~Aug 1, 2027)

VERIFY POINTS (author rules on each):
  V1 Town center definition (see Question 1)
  V2 Town population cutoff and which places count as towns (incorporated vs CDP)
  V3 Width of the APPROACH comparison zone (5 miles default)
  V4 Crash-to-road snapping distance (crashes more than 50 m from a signed route dropped)
  V5 Town-center sample: 45 random towns (30 MO, 15 New England), aerial imagery plus civic anchors

LICENSE:   Code MIT. Data and documents CC BY 4.0, with attribution to NHTSA, FHWA,
           Census Bureau, and Overture Maps / OpenStreetMap contributors (ODbL notice
           kept with any file containing Overture land-use attributes).

BUILD DECISIONS MADE DURING THE BUILD (logged in qa_report.txt):
  - Road filter: US/state-signed OR state-owned, functional class 2-6; Interstates, ramps,
    local roads (class 7) and the second direction of divided highways (facility 6) dropped.
    Route signing alone missed states that leave it blank (Tennessee).
  - Crash keep rule: within 50 m AND (FARS route 2/3 OR state-owned OR FARS road-name number
    matches the route); never Interstates. Needed for Texas FM/RM roads, which FARS codes
    as "other" with owner not reported.
  - Rates only on class 2-5 rows with traffic counts on >=90% of length (97% of crashes).
  - New England (author decision, Nov 6, 2026): towns = county subdivisions (T1, C5) under
    10,000; town limits = villages and Census village areas inside the town; towns with no
    village get a center zone only. Results reported with and without New England.

ASSUMPTIONS (author confirmed defaults, Nov 6, 2026):
  - Years 2015-2024, same as the county panel; HPMS 2024 road snapshot.
  - Interstates excluded (no Interstate is a main street).
  - Pilot state Missouri first, then all states.
```

## What each line means for you

- **Question:** the one thing the paper answers. Is your town's highway main street more dangerous than the same road just outside town?
- **Sources:** five free government and open-map datasets. Every download is logged.
- **Unit:** every row in the final table is one piece of highway in one town, labeled center, rest of town, or just outside town.
- **Measures:** for each piece: how long it is, how much traffic, how many deadly crashes and deaths, how many were people walking or biking, and how many happened at night.
- **Outputs:** the table (spreadsheet and map file), the documentation, and the paper.
- **Verify points:** five decisions that need your planning judgment. The build uses a default for each until you rule.
- **License:** anyone can reuse it if they credit you and the original sources.
