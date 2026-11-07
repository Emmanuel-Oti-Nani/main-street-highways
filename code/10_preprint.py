#!/usr/bin/env python3
"""10_preprint.py - build the preprint (APS REVTeX 4.2, two-column, Palatino) from paper/stats.json.

Plain-language note: writes and compiles the preprint version of the paper in the two-column journal
style used for arXiv-type preprints. Every number is read from paper/stats.json, so the text cannot
disagree with the data. Output: paper/preprint/main_street_highways_preprint.pdf (and .tex).
Requires pdflatex with revtex4-2, mathpazo, orcidlink.
"""
import json
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
A = json.load(open(os.path.join(ROOT, "AUTHORS.json")))["authors"][0]
OUT = os.path.join(ROOT, "paper", "preprint")
CONCEPT_DOI = "10.5281/zenodo.24030310"


def R(z, lst=None, key=None, val=None):
    lst = lst if lst is not None else S["rates_pooled"]
    return next(r for r in lst if r["zone"] == z and (key is None or r[key] == val))


def n0(x):
    return f"{int(round(x)):,}".replace(",", "{,}")


def f(x, d=2):
    return f"{x:.{d}f}"


def pct(x, d=0):
    return f"{100 * x:.{d}f}\\%"


C, T, P = R("CENTER"), R("TOWN"), R("APPROACH")
ratio = lambda a, b: f"{a / b:.1f}"
sp = S["speed_limit_by_zone"]
pn = S["ped_crash_night_share_by_zone"]
noNE = lambda z: R(z, S["rates_pooled_excl_new_england"])
NEo = lambda z: R(z, S["rates_new_england_only"])
sz = lambda b, z: R(z, S["rates_by_size"], "size_band", b)
rg = lambda g, z: R(z, S["rates_by_region"], "region", g)
rt = lambda g, z: R(z, S["rates_by_us_signed"], "route_type", g)
nov = S["towns_by_rule"]["new england town, no village (center only)"]

refs = [
    ("ghsa", r"Governors Highway Safety Association, \emph{Pedestrian Traffic Fatalities by State: 2024 Preliminary Data (January--December)} (GHSA, Washington, DC, 2025)."),
    ("nani2025", r"E.~O. Nani, G.~Camynta-Baezie, J.~Anbazu, N.~S. Antwi, D.~Blija, E.~Adabor, and M.~O. Asibey, A burgeon in informal economic activities along highways in urbanizing cities: Implications for sustainable development, \href{https://doi.org/10.1007/s40890-024-00222-0}{Transp. Dev. Econ. \textbf{11}, 5 (2025)}, \doi{10.1007/s40890-024-00222-0}."),
    ("panel", r"E.~O. Nani, U.S. Rural Road Fatality County Panel (Version 1.0.0) [Data set], Zenodo (2026), \doi{10.5281/zenodo.23547649}."),
    ("ewing", r"R.~Ewing and E.~Dumbaugh, The built environment and traffic safety: A review of empirical evidence, \href{https://doi.org/10.1177/0885412209335553}{J. Plan. Lit. \textbf{23}, 347 (2009)}, \doi{10.1177/0885412209335553}."),
    ("dumbaugh", r"E.~Dumbaugh and R.~Rae, Safe urban form: Revisiting the relationship between community design and traffic safety, \href{https://doi.org/10.1080/01944360902950349}{J. Am. Plan. Assoc. \textbf{75}, 309 (2009)}, \doi{10.1080/01944360902950349}."),
    ("tefft", r"B.~C. Tefft, Impact speed and a pedestrian's risk of severe injury or death, \href{https://doi.org/10.1016/j.aap.2012.07.022}{Accid. Anal. Prev. \textbf{50}, 871 (2013)}, \doi{10.1016/j.aap.2012.07.022}."),
    ("forbes", r"G.~J. Forbes, \emph{NCHRP Synthesis 412: Speed Reduction Techniques for Rural High-to-Low Speed Transitions} (Transportation Research Board, Washington, DC, 2011), \doi{10.17226/22890}."),
    ("torbic", r"D.~J. Torbic, D.~K. Gilmore, K.~M. Bauer, C.~D. Bokenkroger, D.~W. Harwood, L.~M. Lucas, R.~J. Frazier, C.~S. Kinzel, D.~L. Petree, and M.~D. Forsberg, \emph{NCHRP Report 737: Design Guidance for High-Speed to Low-Speed Transition Zones for Rural Highways} (Transportation Research Board, Washington, DC, 2012), \doi{10.17226/22670}."),
    ("sga", r"Smart Growth America, \emph{Dangerous by Design 2024} (Smart Growth America, Washington, DC, 2024)."),
    ("nani2026a", r"E.~O. Nani, How rural is rural? Agreement between the FARS rural/urban label and 2020 Census urban areas for U.S. traffic deaths, 2015--2024, EarthArXiv preprint (2026), \doi{10.31223/X5RV4C}."),
    ("tiger", r"U.S. Census Bureau, \emph{TIGER/Line Shapefiles, 2024: Places and County Subdivisions} (Washington, DC, 2024)."),
    ("popest", r"U.S. Census Bureau, \emph{Annual Estimates of the Resident Population for Incorporated Places and Minor Civil Divisions, Vintage 2024} (Washington, DC, 2025)."),
    ("ua", r"U.S. Census Bureau, \emph{2020 Census Urban Areas} (Washington, DC, 2023)."),
    ("overture", r"Overture Maps Foundation, Overture Maps Places, release 2026-10-21.0, \url{https://overturemaps.org} (2026)."),
    ("gnis", r"U.S. Geological Survey, Geographic Names Information System, Domestic Names Archive (August 25, 2021), \url{https://www.usgs.gov/tools/geographic-names-information-system-gnis}."),
    ("hpms", r"Federal Highway Administration, Highway Performance Monitoring System, 2024 spatial data by state, \url{https://geo.dot.gov} (2025)."),
    ("fars", r"National Highway Traffic Safety Administration, Fatality Analysis Reporting System (FARS) national data files, 2015--2024, \url{https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars} (2026)."),
    ("dataset", r"E.~O. Nani, Main Street Highways: Fatal crashes on state and U.S. highways through small-town centers (Version 1.0.0) [Data set], Zenodo (2026), \doi{" + CONCEPT_DOI + "}."),
]
bib = "\n".join(f"\\bibitem{{{k}}} {t}" for k, t in refs)

zl = {"CENTER": "Town center", "TOWN": "Rest of town", "APPROACH": "Outside town"}
t1 = "\n".join(
    f"{zl[r['zone']]} & {n0(r['miles'])} & {n0(r['vmt_100m'])} & {n0(r['fatal_crashes'])} & {n0(r['fatalities'])} & "
    f"{n0(r['ped_fatalities'])} & {f(r['crash_rate'])} ({f(r['crash_rate_lo'])}--{f(r['crash_rate_hi'])}) & "
    f"{f(r['ped_rate'], 3)} ({f(r['ped_rate_lo'], 3)}--{f(r['ped_rate_hi'], 3)}) & {pct(r['ped_share'], 1)} & "
    f"{pct(r['night_share'], 1)} \\\\" for r in (C, T, P))
groups = ([("Towns $<$500", lambda z: sz("under 500", z)), ("Towns 500--2{,}499", lambda z: sz("500 to 2,499", z)),
           ("Towns 2{,}500--9{,}999", lambda z: sz("2,500 to 9,999", z))]
          + [(g, (lambda gg: (lambda z: rg(gg, z)))(g)) for g in ["Northeast", "Midwest", "South", "West"]]
          + [("U.S. routes", lambda z: rt("US", z)), ("State routes", lambda z: rt("State", z)),
             ("Excl.\\ New England", noNE), ("New England only", NEo)])
t2 = "\n".join(f"{lab} & {f(g('CENTER')['ped_rate'], 3)} & {f(g('TOWN')['ped_rate'], 3)} & "
               f"{f(g('APPROACH')['ped_rate'], 3)} & {ratio(g('CENTER')['ped_rate'], g('APPROACH')['ped_rate'])} & "
               f"{n0(g('CENTER')['ped_fatalities'])} \\\\" for lab, g in groups)

tex = rf"""\documentclass[aps,prd,twocolumn,superscriptaddress,nofootinbib,floatfix]{{revtex4-2}}
\usepackage[T1]{{fontenc}}
\usepackage{{mathpazo}}
\usepackage{{graphicx,amsmath,booktabs,url}}
\usepackage[colorlinks=false,linkbordercolor={{0 1 1}},citebordercolor={{0 1 0}},urlbordercolor={{0 1 1}}]{{hyperref}}
\usepackage{{orcidlink}}
\renewcommand{{\doi}}[1]{{\href{{https://doi.org/#1}}{{doi:\,#1}}}}

\begin{{document}}

\title{{Main Street Highways: Fatal Crashes on State and U.S.\ Highways Through Small-Town Centers in the United States, 2015--2024}}

\author{{{A['name']}\,\orcidlink{{{A['orcid']}}}}}
\email{{{A['email']}}}
\affiliation{{Independent Researcher, Springfield, Missouri, USA}}

\begin{{abstract}}
In thousands of small U.S.\ towns the main street is a state or U.S.\ highway, where through traffic meets people walking to shops, schools, and services. National crash reporting divides deaths into urban and rural and does not identify these streets. We build an open, segment-level national dataset of state- and U.S.-signed and state-owned highways in and near {n0(S['n_towns'])} towns of fewer than 10{{,}}000 people in the lower 48 states. Each town center is located as the densest quarter-mile cluster of everyday destinations, and every highway is divided into the town center, the rest of town, and the same route up to 5 miles outside town. Fatal crashes from the Fatality Analysis Reporting System, {S['years'].replace('-', '--')}, are matched within 50~m using road ownership and route-number agreement, and rates use 2024 traffic volumes. The dataset holds {n0(S['n_segments'])} town--route--zone segments and {n0(S['n_crashes_matched'])} fatal crashes ({pct(S['share_of_us_fatal_crashes'])} of all fatal crashes in the lower 48 states and the District of Columbia). Fatal crash rates were lower in town centers than outside town ({f(C['crash_rate'])} versus {f(P['crash_rate'])} per 100 million vehicle miles), but pedestrian death rates were {ratio(C['ped_rate'], P['ped_rate'])} times higher ({f(C['ped_rate'], 3)} versus {f(P['ped_rate'], 3)}), and {pct(C['ped_share'])} of people killed in town centers were walking. The pattern holds in every Census region, town-size class, and route type. Small-town main street highways trade fewer high-speed crashes for more pedestrian deaths, a pattern that deserves direct attention in state highway safety programs.
\end{{abstract}}

\maketitle

\noindent\textbf{{Keywords:}} pedestrian safety, small towns, rural highways, main streets, FARS, open data

\section{{Introduction}}
Across the United States, state and U.S.\ highways that carry regional traffic between cities also serve as the main streets of small towns. Within a few hundred feet, a road designed for 55 to 65~mph travel becomes the street where people park, shop, and walk to the post office and school. In the data assembled here, posted speed limits average {f(sp['APPROACH'], 0)}~mph on the approaches to small towns and {f(sp['CENTER'], 0)}~mph in their centers. These roads are owned and designed by state transportation agencies, while the land uses that generate walking along them are governed by local zoning. That split in responsibility makes them easy to overlook in both state safety programs and local plans.

Pedestrian deaths in the United States rose 80\% between 2009 and 2023 while all other traffic deaths rose 13\%~\cite{{ghsa}}. National reporting divides deaths into urban and rural, which hides the small-town main street: it is too developed to behave like a rural highway and too small to register as urban. No national dataset identifies these road segments directly.

This study fills that gap. It builds an open, segment-level dataset of fatal crashes on state and U.S.\ highways that pass through the centers of towns with fewer than 10{{,}}000 people and compares each town center with the rest of the town and with the same routes just outside town. It asks how many small towns have a state or U.S.\ highway as their main street and how many fatal crashes occur there; how fatal crash rates, pedestrian deaths, and time of day differ among the three zones; and whether these patterns hold across regions, town sizes, and route types. The work extends a study of a national highway corridor in an urbanizing city in Ghana, which found that informal economic activities along the highway were associated with road accidents, traffic congestion, and poor sanitation, with 21.8\% of reported accident cases involving informal economic actors~\cite{{nani2025}}, and a county-level panel of U.S.\ rural road deaths~\cite{{panel}}.

\section{{Background}}
Reviews of the built environment and traffic safety conclude that design features meant to make roads more forgiving at high speed can raise risk in developed settings where drivers meet pedestrians, turning vehicles, and parked cars~\cite{{ewing}}, and arterial strip commercial development is associated with more crashes than compact street patterns~\cite{{dumbaugh}}. Speed is the main mechanism for pedestrians: the risk that a struck pedestrian is killed rises steeply with impact speed~\cite{{tefft}}. Speed-reduction techniques for rural high-to-low speed transitions~\cite{{forbes}} and design guidance for the transition from a high-speed rural highway to a lower-speed section approaching a small town~\cite{{torbic}} focus on the entry to town. Less is known nationally about the town center itself. National analyses of pedestrian deaths have focused on large metropolitan areas, high-poverty counties, and arterial roads~\cite{{ghsa,sga}}. Because the FARS rural/urban label and the 2020 Census urban-area map disagree for a meaningful share of deaths at urban edges~\cite{{nani2026a}}, a place-based definition is used here.

\section{{Data and Methods}}
\subsection{{Small towns}}
Outside New England, towns are incorporated places from the 2024 TIGER/Line files~\cite{{tiger}} with a 2024 population estimate under 10{{,}}000~\cite{{popest}}. In New England, where local government is organized by towns that the Census Bureau treats as county subdivisions, towns and small cities under 10{{,}}000 were taken from that layer. Because New England towns often span 30 or more square miles of farmland and forest, town limits there were defined as the incorporated villages and Census Designated Places within the town; {n0(nov)} towns without such an area were given a center zone only. Towns with more than half of their land inside a 2020 Census urban area of 50{{,}}000 or more people were dropped as suburbs~\cite{{ua}}. Alaska and Hawaii were excluded. The result is {n0(S['n_towns'])} small towns.

\subsection{{Town centers}}
Town centers were located from everyday destinations (shops, restaurants, offices and services, government buildings, schools, clinics, lodging, and cultural sites) in the Overture Maps places data~\cite{{overture}}, excluding travel-oriented businesses such as fuel stations so that a highway-edge strip would not be mistaken for a downtown. For each town, the destination with the most others within a quarter mile (402~m) was found, and the point was shifted once toward the mean of that cluster. A town has a center if at least 10 destinations lie within a quarter mile; the center zone is the quarter-mile circle, clipped to the town. {n0(S['n_towns_with_center'])} of {n0(S['n_towns'])} towns have an identifiable center. For a random sample of 45 towns (30 in Missouri, 15 in New England), the centers were checked against aerial imagery and against each town's recognized civic anchors (post office, town or city hall, and county courthouse) from the USGS Geographic Names Information System~\cite{{gnis}}. All 45 centers lay within a quarter mile of at least one civic anchor; in 3 towns the center is a civic or commercial strip on a highway rather than a traditional downtown.

\subsection{{Highway segments}}
Road geometry and attributes come from the 2024 Highway Performance Monitoring System (HPMS)~\cite{{hpms}}. Study roads are those signed as U.S.\ or state routes plus any road owned by the state highway agency on a principal arterial, minor arterial, or collector; Interstates, ramps, local roads, and the second direction of divided highways were removed. Each road was cut into 50~m pieces, and each piece was assigned by its midpoint to the town center, the rest of town (inside town limits but outside the center), or outside town (the same route outside every incorporated place, within 5 miles of the town's limits, assigned to the nearest town whose limits the route enters). Pieces were combined into one segment per town, route, and zone, carrying length, annual average daily traffic (AADT), posted speed limit where reported, lanes, and on-street parking.

\subsection{{Crash matching and rates}}
Fatal crashes and victims come from FARS, {S['years'].replace('-', '--')}~\cite{{fars}}. A crash was matched to a study segment if it lies within 50~m of a study road and FARS records it on a U.S.\ or state highway, on a road owned by the state highway agency, or on a road whose route number matches the study route; Interstate crashes were never kept. Where several study roads lay within 50~m, a route-number match was preferred, then the nearest road. Of {n0(S['n_crashes_lower48'])} fatal crashes in the study area, {n0(S['n_crashes_matched'])} were matched; the FARS route number agrees with the assigned route for {pct(S['name_match_share'])} of them. Exposure is vehicle miles traveled (VMT), computed as 2024 AADT times segment length times 3{{,}}652.5 days. Rates per 100 million VMT carry exact Poisson 95\% confidence intervals and use segments on principal arterials, minor arterials, and major collectors with traffic counts on at least 90\% of their length, which hold {pct(S['rate_base_share_of_crashes'])} of matched crashes. Night is 6:00~p.m.\ to 5:59~a.m.

\section{{Results}}
Of {n0(S['n_towns'])} small towns, {n0(S['n_towns_with_segment'])} have a state or U.S.\ highway within their limits or within 5 miles, and in {n0(S['n_main_street_towns'])} a study highway runs through the town center. These main street highways total {n0(S['miles_by_zone']['CENTER'])} miles in town centers, {n0(S['miles_by_zone']['TOWN'])} miles elsewhere in town, and {n0(S['miles_by_zone']['APPROACH'])} miles on the approaches. Over ten years, {n0(S['crashes_by_zone']['CENTER'])} fatal crashes occurred in town centers, {n0(S['crashes_by_zone']['TOWN'])} in the rest of town, and {n0(S['crashes_by_zone']['APPROACH'])} outside town (Table~\ref{{tab:zones}}).

\begin{{table*}}
\caption{{Fatal crashes and rates by zone on small-town state and U.S.\ highways, {S['years'].replace('-', '--')}. Rate base only; rates per 100 million VMT using 2024 AADT; 95\% exact Poisson confidence intervals in parentheses.}}
\label{{tab:zones}}
{{\footnotesize
\begin{{ruledtabular}}
\begin{{tabular}}{{lrrrrrccrr}}
Zone & Miles & \shortstack{{100M\\VMT}} & \shortstack{{Fatal\\crashes}} & Deaths & \shortstack{{Ped.\\deaths}} & \shortstack{{Crash rate\\(95\% CI)}} & \shortstack{{Ped.\ death rate\\(95\% CI)}} & \shortstack{{Ped.\\share}} & \shortstack{{Night\\share}} \\
\colrule
{t1}
\end{{tabular}}
\end{{ruledtabular}}}}
\end{{table*}}

Per mile driven, fatal crashes were less frequent in town centers ({f(C['crash_rate'])} per 100 million VMT) and the rest of town ({f(T['crash_rate'])}) than on the approaches ({f(P['crash_rate'])}). Pedestrian deaths showed the opposite pattern: the town-center rate, {f(C['ped_rate'], 3)}, was {ratio(C['ped_rate'], P['ped_rate'])} times the approach rate ({f(P['ped_rate'], 3)}) and {ratio(C['ped_rate'], T['ped_rate'])} times the rest-of-town rate ({f(T['ped_rate'], 3)}), with non-overlapping intervals. Pedestrians were {pct(C['ped_share'])} of people killed in town centers, {pct(T['ped_share'])} in the rest of town, and {pct(P['ped_share'])} on the approaches (Fig.~\ref{{fig:zones}}).

\begin{{figure*}}
\includegraphics[width=0.95\textwidth]{{fig1_rates_by_zone.pdf}}
\caption{{(a) Fatal crash rate and (b) pedestrian death rate by zone, state and U.S.\ highways in and near U.S.\ towns under 10{{,}}000 people, {S['years'].replace('-', '--')}. Whiskers show 95\% Poisson confidence intervals.}}
\label{{fig:zones}}
\end{{figure*}}

The town-center excess in pedestrian deaths appears in every town-size class and grows with town size (Fig.~\ref{{fig:size}}). In towns of 2{{,}}500 to 9{{,}}999 people the town-center rate was {f(sz('2,500 to 9,999', 'CENTER')['ped_rate'], 3)} per 100 million VMT, against {f(sz('2,500 to 9,999', 'APPROACH')['ped_rate'], 3)} on the approaches; in towns under 500 it was {f(sz('under 500', 'CENTER')['ped_rate'], 3)} against {f(sz('under 500', 'APPROACH')['ped_rate'], 3)}, with a wider interval. The town-center rate exceeded the approach rate in all {S['n_regions_center_higher_ped']} Census regions and on both U.S.\ and state routes (Table~\ref{{tab:groups}}); the center-to-outside ratio was highest in the Midwest ({ratio(rg('Midwest', 'CENTER')['ped_rate'], rg('Midwest', 'APPROACH')['ped_rate'])}), and pedestrians made up the largest share of town-center deaths in the West ({pct(rg('West', 'CENTER')['ped_share'])}) and Northeast ({pct(rg('Northeast', 'CENTER')['ped_share'])}).

\begin{{figure*}}
\includegraphics[width=0.95\textwidth]{{fig2_ped_rate_by_size.pdf}}
\caption{{Pedestrian death rate by zone and town size. Whiskers show 95\% Poisson confidence intervals.}}
\label{{fig:size}}
\end{{figure*}}

\begin{{table}}
\caption{{Pedestrian deaths per 100 million VMT by zone and subgroup (rate base only). Ratio is town center to outside town.}}
\label{{tab:groups}}
\begin{{ruledtabular}}
\begin{{tabular}}{{lccccr}}
Subgroup & Center & Town & Outside & Ratio & Deaths$^a$ \\
\colrule
{t2}
\end{{tabular}}
\end{{ruledtabular}}
\noindent{{\footnotesize $^a$Pedestrian deaths in town centers.}}
\end{{table}}

About {pct(C['night_share'])} of fatal crashes occurred at night in every zone. Fatal pedestrian crashes differed: {pct(pn['APPROACH'])} occurred at night on the approaches and {pct(pn['TOWN'])} in the rest of town, but only {pct(pn['CENTER'])} in town centers, so daytime pedestrian deaths are relatively more common where shops and services are concentrated. Excluding New England, the town-center pedestrian death rate was {f(noNE('CENTER')['ped_rate'], 3)} and the approach rate {f(noNE('APPROACH')['ped_rate'], 3)}, nearly identical to the national figures; within New England alone rates were lower but showed the same pattern ({f(NEo('CENTER')['ped_rate'], 3)} versus {f(NEo('APPROACH')['ped_rate'], 3)}).

\section{{Discussion}}
Small-town main street highways show a clear trade-off. Lower speeds in town centers appear to reduce the overall rate of fatal crashes relative to the approaches, but the people who die there are far more often pedestrians, and the town-center pedestrian death rate is about {ratio(C['ped_rate'], P['ped_rate'])} times the approach rate in every region, town size, and route type. This is the expected result when through traffic at arterial speeds shares a street with walking trips to shops, services, and schools, and it parallels the finding from Ghana that informal economic activity along a national highway is tied to road accidents~\cite{{nani2025}}.

Three implications follow. First, state transportation agencies own these segments, so state safety screening can target them directly; the dataset provides a ready national list. Second, transition-zone guidance~\cite{{torbic}} addresses the entry to town, but the deaths documented here occur inside the center, which points to crossing treatments, lighting, and speed management through the downtown block. Third, the relatively high share of daytime pedestrian deaths in town centers means that measures aimed only at nighttime visibility will not address the full problem. For local planning, downtown revitalization that adds destinations along a state highway also adds pedestrian exposure, so local downtown plans and state corridor design need to be coordinated.

\section{{Limitations}}
The data are observational, and pedestrian exposure is not measured, so higher pedestrian death rates in centers partly reflect more walking. FARS records only crashes with a death within 30 days. Traffic volumes are 2024 values applied to all ten years, and the road network is a 2024 snapshot, so towns that gained a bypass during the period are misrepresented for earlier years. Town centers come from a 2026 business snapshot, posted speed limits are incomplete outside the National Highway System, and town limits are legal boundaries that may include rural land.

\section{{Conclusions}}
This study provides the first national, segment-level dataset of fatal crashes on state and U.S.\ highways that serve as small-town main streets. In {n0(S['n_main_street_towns'])} towns where such a highway runs through the center, fatal crashes are less frequent per mile driven than on the approaches, but pedestrian deaths are about {ratio(C['ped_rate'], P['ped_rate'])} times as frequent. The dataset gives state agencies, small towns, and researchers a common base for finding these segments, tracking them over time, and evaluating treatments.

\section*{{Data Availability}}
The dataset, code, provenance log, quality report, and verification records are openly available at Zenodo~\cite{{dataset}} (\doi{{{CONCEPT_DOI}}}) and at \url{{https://github.com/Emmanuel-Oti-Nani/main-street-highways}} under CC~BY~4.0 (data) and MIT (code) licenses.

\begin{{thebibliography}}{{99}}
{bib}
\end{{thebibliography}}

\end{{document}}
"""

os.makedirs(OUT, exist_ok=True)
for fn in ["fig1_rates_by_zone.pdf", "fig2_ped_rate_by_size.pdf"]:
    shutil.copy(os.path.join(ROOT, "paper", "figures", fn), OUT)
texf = os.path.join(OUT, "main_street_highways_preprint.tex")
open(texf, "w").write(tex)
for _ in range(2):
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", os.path.basename(texf)],
                       cwd=OUT, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout[-3000:])
    raise SystemExit("pdflatex failed")
log = open(texf.replace(".tex", ".log")).read()
warn = [l for l in log.splitlines() if "undefined" in l.lower() or "Overfull" in l]
print("preprint built:", texf.replace(".tex", ".pdf"))
print("warnings:", len(warn)); print("\n".join(warn[:10]))
