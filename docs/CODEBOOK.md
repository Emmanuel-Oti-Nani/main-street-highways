# Codebook: Main Street Highways v1.0.0

*Plain-language note: this file explains every column in the three data tables. Open it when you want to know what a column means or where it came from.*

Sources: FARS 2015–2024 (NHTSA); HPMS 2024 (FHWA); TIGER/Line 2024 places, county subdivisions (New England) and Vintage 2024 population estimates (Census Bureau); 2020 Census urban areas; Overture Maps places, release 2026-10-21.0.

## segments.csv (map lines in segments_geo.parquet, joined on segment_id)

One row per **town × route × zone**.

| Column | Meaning | Source / how computed |
|---|---|---|
| segment_id | Unique ID: town GEOID + route label + zone | built |
| GEOID | Town code. 7 digits (state + place) for incorporated places; 10 digits (state + county + county subdivision) for New England towns | TIGER 2024 |
| town_rule | How town limits were drawn: "incorporated place" (legal limits); "new england town, village limits" (villages and Census village areas inside the town); "new england town, no village (center only)" (the center circle stands in for town limits, so no TOWN zone) | built |
| NAME | Town name | TIGER 2024 |
| STATEFP | State FIPS code | TIGER 2024 |
| region | Census region (Northeast, Midwest, South, West) | built from STATEFP |
| pop2024 | Town population, July 1, 2024 estimate | Census Vintage 2024 |
| size_band | under 500 / 500 to 2,499 / 2,500 to 9,999 | from pop2024 |
| route_label | Readable route name, e.g. US-63, SR-61 BUS, BL-44, FM-576, SR-B | HPMS route signing, number, name, qualifier; Texas parsed from route ID |
| route_ids | State route IDs (HPMS route_id) making up the row | HPMS |
| zone | CENTER = inside the town-center circle (¼ mile around the densest cluster of everyday destinations, clipped to town limits); TOWN = inside town limits, outside the center; APPROACH = same route outside every incorporated place, within 5 miles of this town's limits, assigned to the nearest town | built; see 03_centers.py and 04_segments.py |
| f_system | Most common HPMS functional class on the row (2 freeway/expressway, 3 other principal arterial, 4 minor arterial, 5 major collector, 6 minor collector) | HPMS |
| us_signed | True if any part is signed as a U.S. route | HPMS routesigning = 3 |
| length_mi | Centerline length, miles (inventory direction only) | sum of 50 m pieces |
| aadt | Length-weighted average annual daily traffic, 2024 | HPMS aadt, over the length that has a count |
| share_len_with_aadt | Share of length with a traffic count | HPMS |
| vmt_10yr | Vehicle miles traveled over 10 years = aadt × length_mi × 365.25 × 10 | built; 2024 AADT applied to every year |
| speed_limit_mph | Length-weighted posted speed limit, where reported | HPMS (not reported everywhere) |
| through_lanes | Length-weighted through lanes | HPMS |
| share_onstreet_parking | Share of length with peak-period on-street parking reported | HPMS peak_parking > 0 |
| fatal_crashes | Fatal crashes 2015–2024 placed on this row | FARS accident file |
| fatalities | People killed in those crashes | FARS FATALS |
| ped_fatalities | Pedestrians killed (person type 5, fatal injury) | FARS person file |
| bike_fatalities | Bicyclists and other cyclists killed (person types 6, 7) | FARS person file |
| night_crashes | Crashes from 6:00 pm to 5:59 am | FARS HOUR |
| known_hour_crashes | Crashes with a known hour (denominator for night share) | FARS HOUR ≠ 99 |
| in_rate_base | True if f_system 2–5 and share_len_with_aadt ≥ 0.9; only these rows enter crash-rate calculations | built |

## crashes_matched.csv

One row per fatal crash placed on a segment. FARS columns keep their FARS names and codes (see the FARS Analytical User's Manual).

| Column | Meaning |
|---|---|
| crash_id | YEAR_ST_CASE, unique |
| YEAR, MONTH, DAY, HOUR, MINUTE, STATE, COUNTY, ST_CASE | FARS crash identifiers and time |
| LATITUDE, LONGITUD | FARS crash location |
| ROUTE, TWAY_ID, RUR_URB, FUNC_SYS, RD_OWNER | FARS road fields, kept for checking |
| FATALS, ped_fatals, bike_fatals | Deaths in the crash: all, pedestrians, cyclists |
| night | True if 6 pm–6 am; blank if hour unknown |
| GEOID, zone, route_id, route_label, f_system, segment_id | The segment the crash was placed on |
| snap_m | Distance in meters from the FARS location to the road (≤ 50) |
| name_match | True if the number in FARS TWAY_ID equals the number in route_label |

**Matching rule.** A crash is placed on a study road if it is within 50 m of it, and FARS records it as on a U.S. or state highway (ROUTE 2 or 3), or on a state-agency road (RD_OWNER 1), or with a road name whose number matches the route. Interstate crashes are never kept. When several roads are within 50 m, a road-name match wins; otherwise the nearest road wins.

## towns.csv

One row per small town (15,195). Outside New England: incorporated places, lower 48 + DC, under 10,000 people in 2024. In New England: towns and cities (county subdivisions, Census class T1 or C5) under 10,000. All: not more than half of the town's land inside a 2020 urban area of 50,000+.

| Column | Meaning |
|---|---|
| GEOID, STATEFP, PLACEFP, NAME, NAMELSAD, CLASSFP | Census identifiers (PLACEFP holds the county subdivision code for New England towns) |
| town_rule | as above |
| pop2020, pop2024 | 2020 estimates base and 2024 estimate |
| size_band | as above |
| big_ua_share | Share of town land inside a 50,000+ urban area |
| dest_in_town | Everyday destinations inside the town (whole town area in New England) (Overture; shopping, food, services, government, education, health, lodging, arts, lifestyle, cultural; confidence ≥ 0.5; not closed) |
| dest_in_center | Destinations inside the ¼-mile center circle |
| has_center | True if dest_in_center ≥ 10 |
| center_lat, center_lon | Center point |
