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
- [x] **A permanent citation number (DOI)** from Zenodo: https://doi.org/10.5281/zenodo.24030310 (all versions); v1.0.0 is https://doi.org/10.5281/zenodo.24030311
- [ ] **A paper submitted to the TRB 2028 Annual Meeting** (Transportation Research Board), for presentation and journal review (target August 2027)
- [x] A documented check of 45 sample town centers against aerial imagery and each town's post office, town hall or courthouse (all 45 within a quarter mile)

## How it connects to your work

Your published study found that informal economic activities along a national highway in Ghana were tied to road accidents, traffic congestion, and poor sanitation, with 21.8 percent of reported accident cases involving informal economic actors. This project asks the same question in U.S. small towns, where shops and services line the highway. It also builds directly on your Rural Road Fatality County Panel: same crash data, same years, now down to the street level.

## What you need to do

| Your task | When | Time |
|---|---|---|
| Accounts (ORCID, GitHub, Zenodo) | Done | 0 min |
| Answer five setup questions | Done (Nov 6, 2026) | 10 min |
| Town-center check of 45 sample towns | Done (Nov 7, 2026) | 1 to 2 hours |
| Check the results using the checklist | Done (Nov 7, 2026) | 1 to 2 hours |
| Approve publishing | Done (Nov 7, 2026) | 5 min |
| Post the preprint (after checking TRB's preprint policy) | When you choose | 20 min |
| Submit the TRB paper yourself, using the guide | Summer 2027 (TRB call opens) | 20 min |

Everything else is built for you.

## The steps ahead

1. **Data collected.** We download the crash, road, and town files and record where each came from.
2. **Town centers found.** We mark the downtown part of each small town, using your definition.
3. **Highways cut into segments.** Each highway is split into "town center", "rest of town", and "outside town" pieces, and crashes are placed on them.
4. **Quality checks and your aerial-photo sample.** We count, compare, and you check a sample of town centers on aerial photos.
5. **Figures and draft paper.** Every number in the paper comes straight from the data.
6. **Ready for your check.** You verify, then we publish.

*You are here: published on November 7, 2026 (GitHub and Zenodo DOI 10.5281/zenodo.24030310); the TRB paper and preprint are ready for your submission.*
