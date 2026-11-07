# Verification record: Main Street Highways v1.0.0

*Plain-language note: what was checked before release, how, and what was found. Approved for release by the author on November 7, 2026.*

## A. Headline numbers are consistent

The quality report (section 5), README and statistics file (`paper/stats.json`) all come from one pipeline run and were cross-checked by script: town-center pedestrian death rate 0.276 per 100 million vehicle miles, outside-town 0.093 (3.0 times), town-center fatal crash rate 0.97, and 39,300 matched crashes.

## B. Crashes compared with NHTSA's live records

Ten crashes (Vandalia, Holden and Lake Ozark, MO; Schoharie, NY; and six random spot checks from the quality report) were looked up in NHTSA's FARS API (https://crashapi.nhtsa.dot.gov). All ten match on date, hour, road name, number killed, pedestrians killed, and location. Evidence: `data/verify/fars_api_check.csv`.

Three name a different route in FARS than the assigned route; all three are real shared roads (US-19/US-276 in Maggie Valley, NC; SR-30A/SR-30 in Schoharie, NY; SR-12E/SR-12 in Chaumont, NY).

To repeat a check, open for example https://crashapi.nhtsa.dot.gov/crashes/GetCaseDetails?stateCase=290356&caseYear=2016&state=29&format=json (Vandalia, MO: May 21, 2016, hour 21, US-54, one pedestrian killed).

## C. Town-center rows

Checked rows (Excel row numbers in `data/processed/segments.csv`): 30,883 Marshfield, MO, SR-38 (0.6 mi, AADT 9,021); 32,672 Willow Springs, MO, Business 63 (0.52 mi, AADT 4,233); 68,229 Woodstock, VT, US-4 (0.51 mi, AADT 4,851, 25 mph).

## D. Town-center review: every sampled center against the town's recognized center

A random sample of 45 towns (30 Missouri, 15 New England) was reviewed two ways.

1. **Aerial imagery.** Each center was drawn with its quarter-mile circle and the study highways on Esri World Imagery (images not redistributed because of imagery terms; rebuild with `tools/aerial_sheets.py`). A visual pass in Google Earth Pro covered the first four Missouri towns and agreed.
2. **Recognized-center anchors, all 45 towns.** For each town, the post office, town or city hall, county courthouse and official place point were taken from the USGS Geographic Names Information System (2021 archive) and distances measured to our center (`tools/center_anchor_check.py`). Where the name match missed a village post office or a town office, the nearest civic site was taken from the Overture places data or the Census geocoder.

**Result: all 45 centers lie within a quarter mile (402 m) of at least one civic anchor**: the town's post office, town or city hall or offices, or county courthouse. Median distance to the nearest civic anchor: 187 m; largest: 371 m. Details: `data/verify/center_anchor_check.csv`.

Three carry a caveat:

| Town | Caveat |
|---|---|
| Doolittle, MO | Civic center (city hall 212 m) of a post-1940s Route 66 town; no traditional downtown |
| Duenweg, MO | Civic center along old Route 66 (post office 2 m); highway-strip form |
| Granby, MA | Present-day post office (186 m) and town offices (539 m) on a US-202 commercial strip; the historic town common and Kellogg Hall are about 3 km east |

Village towns in New England matched through their village post offices or town offices: East Haddam (Moodus Post Office, 332 m), Deerfield (town offices in South Deerfield, 207 m), Weathersfield (Ascutney Post Office, 89 m). The nine towns that needed follow-up can be opened in Google Earth with `docs/verify/town_center_check.kml`.

The review also found one coding error, fixed before release: in New England, town-center highway lying outside village limits had been labeled "outside town". The fix raised New England's town-center crash count from 34 to 66 and left every other state unchanged.

## E. Rulings

All defaults kept: quarter-mile centers with 10+ destinations; towns under 10,000 with suburbs dropped; 0 to 5 mile outside-town zone; 50 m crash matching with highway, ownership or route-number agreement; rates on main road classes with traffic counts; New England towns with village limits.

## F. Citations

Nani et al. (2025), *Transportation in Developing Economies*, Vol. 11, No. 1, Article 5, confirmed on the publisher's page; the 21.8% figure refers to "informal economic actors". "How Rural Is Rural?" confirmed on EarthArXiv, DOI 10.31223/X5RV4C.
