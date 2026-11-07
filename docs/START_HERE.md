# Start Here: Main Street Highways

*Read this first. It explains your project in plain language. Words in bold are explained in [GLOSSARY.md](GLOSSARY.md).*

## What you are building

A free, public table of every stretch of U.S. or state highway that runs through the middle of a small American town, showing how many people died in crashes there and who they were.

## Why it matters

In thousands of small towns, the main street is also a state or U.S. highway. Trucks and through traffic arrive at highway speed and meet people walking to the post office, the school, and the café. When someone dies on that street, it is counted in national crash data, but nobody has pulled those streets out as their own group. This project does. It lets a town, a state transportation department, or a researcher see how deadly their downtown highway is, and compare it with the same road just outside town.

Think of it like a report card for every small-town main street that is also a highway.

## Where the information comes from

All sources are free and public. Nothing here needs special permission.

| Source | In plain terms | What one row looks like | Link |
|---|---|---|---|
| FARS (Fatality Analysis Reporting System) | The federal list of every crash in the U.S. where someone died, with the map location | One fatal crash: date, time, location, road, number killed | https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars |
| HPMS (Highway Performance Monitoring System) | The federal inventory of public roads, sent in by every state | One stretch of road: route number, who owns it, speed limit, daily traffic, lanes, on-street parking | https://www.fhwa.dot.gov/policyinformation/hpms.cfm |
| Census TIGER places | The official boundary of every town and city | One town: name, outline on the map | https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html |
| Census population estimates | How many people live in each town | One town: population each year 2020 to 2024 | https://www.census.gov/programs-surveys/popest.html |
| Overture Maps (built partly from OpenStreetMap) | A free world map of businesses and land use | One shop, school, or land-use area with its location | https://overturemaps.org |

## What you will have at the end

- [x] **A public project page** on GitHub where anyone can see and reuse your work: https://github.com/Emmanuel-Oti-Nani/main-street-highways
- [ ] **A permanent citation number (DOI)** from Zenodo for the Main Street Highways segment dataset (added to the README after release)
- [ ] **A paper submitted to the TRB 2028 Annual Meeting** (Transportation Research Board), for presentation and journal review (target August 2027)
- [ ] A short sample check of town centers against aerial photos, documented so others can see it was done

## How it connects to your work

Your published study found that roadside trading along a national highway was tied to congestion, poor sanitation, and road accidents, with 21.8 percent of reported accident cases involving roadside traders. This project asks the same question in U.S. small towns, where shops line the highway instead of traders. It also builds directly on your Rural Road Fatality County Panel: same crash data, same years, now down to the street level.

## What you need to do

| Your task | When | Time |
|---|---|---|
| Accounts (ORCID, GitHub, Zenodo) | Already done | 0 min |
| Answer five setup questions | Now | 10 min |
| Check 30 sample town centers on aerial photos | After checkpoint 3 | 1 to 2 hours |
| Check the results using the checklist | When the draft is ready | 1 to 2 hours |
| Approve publishing | After checking | 5 min |
| Submit the TRB paper yourself, using the guide | Summer 2027 (TRB call opens) | 20 min |

Everything else is built for you.

## The steps ahead

1. **Data collected.** We download the crash, road, and town files and record where each came from.
2. **Town centers found.** We mark the downtown part of each small town, using your definition.
3. **Highways cut into segments.** Each highway is split into "town center", "rest of town", and "outside town" pieces, and crashes are placed on them.
4. **Quality checks and your aerial-photo sample.** We count, compare, and you check a sample of town centers on aerial photos.
5. **Figures and draft paper.** Every number in the paper comes straight from the data.
6. **Ready for your check.** You verify, then we publish.

*You are here: step 6 (verified by the author on Nov 7, 2026; publishing)*
