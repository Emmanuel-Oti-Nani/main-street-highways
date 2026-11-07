// 08_manuscript.js - build the TRB Annual Meeting manuscript (Word) from paper/stats.json.
//
// Plain-language note: this script writes the paper. Every number in the text and tables is
// read from paper/stats.json, which the data pipeline produces, so the paper cannot disagree
// with the data. Run: node code/08_manuscript.js  (add --final after verification to remove
// the DRAFT banner). Output: paper/manuscript_TRB2028.docx
//
// TRB format (2027 instructions): Times New Roman >=10 pt, single spaced, single column,
// line numbers restarting each page, page numbers centered at bottom, tables and figures
// embedded near first mention, max 7,500 words with each table counted as 250 words,
// abstract max 250 words, references called out (Author, Year).

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  WidthType, BorderStyle, Footer, Header, PageNumber, LineNumberRestartFormat, ShadingType,
  HeadingLevel,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const S = JSON.parse(fs.readFileSync(path.join(ROOT, "paper", "stats.json")));
const A = JSON.parse(fs.readFileSync(path.join(ROOT, "AUTHORS.json"))).authors[0];
const FINAL = process.argv.includes("--final");

// ---------- number helpers (every number below comes from S) ----------
const n0 = (x) => Math.round(x).toLocaleString("en-US");
const f = (x, d = 2) => Number(x).toFixed(d);
const pct = (x, d = 0) => (100 * x).toFixed(d) + "%";
const R = (z, list = S.rates_pooled, key, val) =>
  list.find((r) => r.zone === z && (key ? r[key] === val : true));
const C = R("CENTER"), T = R("TOWN"), P = R("APPROACH");
const ratio = (a, b) => (a / b).toFixed(1);
const sp = S.speed_limit_by_zone;
const noNE = (z) => R(z, S.rates_pooled_excl_new_england);
const NEo = (z) => R(z, S.rates_new_england_only);

// ---------- document pieces ----------
const FONT = "Times New Roman";
let words = 0;
const count = (t) => { words += t.split(/\s+/).filter(Boolean).length; };
function para(text, opts = {}) {
  // text: string or array of [string, {bold, italics}] runs
  const runs = (Array.isArray(text) ? text : [[text, {}]]).map(([t, o]) => {
    if (!opts.nocount) count(t);
    return new TextRun({ text: t, font: FONT, size: 24, ...o });
  });
  return new Paragraph({ children: runs, spacing: { after: 160, line: 240 }, alignment: opts.align,
                         indent: opts.indent, keepNext: opts.keepNext });
}
function heading(t, level = 1) {
  count(t);
  return new Paragraph({ heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    children: [new TextRun({ text: level === 1 ? t.toUpperCase() : t, font: FONT, size: 24, bold: true })],
    spacing: { before: 240, after: 120 }, keepNext: true });
}
function caption(t) {
  count(t);
  return new Paragraph({ children: [new TextRun({ text: t, font: FONT, size: 24, bold: true })],
                         spacing: { before: 120, after: 120 }, keepNext: true });
}
function note(t) {
  count(t);
  return new Paragraph({ children: [new TextRun({ text: t, font: FONT, size: 20 })], spacing: { after: 200 } });
}
let tables = 0;
function table(headers, rows, widths) {
  tables += 1;
  const total = widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
  const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const cell = (t, i, head, last) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders: { top: head ? border : none, bottom: head || last ? border : none, left: none, right: none },
    shading: head ? { type: ShadingType.CLEAR, color: "auto", fill: "F2F2F2" } : undefined,
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT,
      children: [new TextRun({ text: String(t), font: FONT, size: 18, bold: head })] })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, i, true, false)) }),
           ...rows.map((r, j) => new TableRow({ children: r.map((c, i) => cell(c, i, false, j === rows.length - 1)) }))],
  });
}
function figure(file, w, h) {
  return new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(ROOT, "paper", "figures", file)),
                              transformation: { width: w, height: h } })] });
}

// ---------- content ----------
const TITLE = "Main Street Highways: Fatal Crashes on State and U.S. Highways Through Small-Town Centers in the United States, 2015-2024";
const zl = { CENTER: "Town center", TOWN: "Rest of town", APPROACH: "Outside town (0-5 mi)" };
const body = [];
const add = (...x) => body.push(...x);

// Abstract (structured, <= 250 words)
const abstractParts = [
  ["Objective. ", `In thousands of small U.S. towns the main street is a state or U.S. highway. This study builds an open, segment-level national dataset of those roads and compares fatal crashes in town centers with the same routes in the rest of town and just outside town.`],
  ["Methods. ", `Towns under 10,000 people outside large urban areas (${n0(S.n_towns)}) were identified from Census boundaries. Each town center was located as the densest quarter-mile cluster of everyday destinations. State-owned and U.S. or state-signed highways from the 2024 Highway Performance Monitoring System were cut into 50 m pieces and labeled town center, rest of town, or outside town (0 to 5 miles). Fatal crashes from FARS, ${S.years}, were matched within 50 m using road ownership and route-name agreement. Rates use 2024 traffic.`],
  ["Results. ", `The dataset holds ${n0(S.n_segments)} town-route-zone segments and ${n0(S.n_crashes_matched)} fatal crashes (${pct(S.share_of_us_fatal_crashes)} of all fatal crashes in the lower 48 states and the District of Columbia). Fatal crash rates were lower in town centers than outside town (${f(C.crash_rate)} versus ${f(P.crash_rate)} per 100 million vehicle miles), but pedestrian death rates were ${ratio(C.ped_rate, P.ped_rate)} times higher (${f(C.ped_rate, 3)} versus ${f(P.ped_rate, 3)}), and ${pct(C.ped_share)} of people killed in town centers were walking. The pattern held in every region, town size, and route type.`],
  ["Conclusions. ", `Main street highways trade fewer high-speed crashes for more pedestrian deaths. Pedestrian safety on these segments deserves direct attention in state highway programs. The dataset is openly available.`],
];

add(heading("Abstract"));
abstractParts.forEach(([h, t]) => add(para([[h, { bold: true }], [t, {}]])));
add(para([["Keywords: ", { bold: true }], ["pedestrian safety, small towns, rural highways, main streets, FARS, open data", {}]]));

add(heading("Introduction"));
add(para(`Across the United States, state and U.S. highways that carry regional traffic between cities also serve as the main streets of small towns. Within a few hundred feet, a road designed for 55 to 65 mph travel becomes the street where people park, shop, cross to the post office, and walk to school. In this study's data, posted speed limits average ${f(sp.APPROACH, 0)} mph on the approaches to small towns and ${f(sp.CENTER, 0)} mph in their centers. These roads are owned and designed by state transportation agencies, while the land uses that generate walking along them are governed by local zoning. That split in responsibility makes them easy to overlook in both state safety programs and local plans.`));
add(para(`National pedestrian deaths have risen sharply over the past 15 years. The Governors Highway Safety Association reports that pedestrian deaths rose 80% between 2009 and 2023 while all other traffic deaths rose 13% (GHSA, 2025). Most national reporting splits deaths into "urban" and "rural," which hides the small-town main street: it is too developed to behave like a rural highway and too small to register as urban. No national dataset identifies these road segments directly.`));
add(para(`This study fills that gap. It builds an open, segment-level dataset of fatal crashes on state and U.S. highways that pass through the centers of towns with fewer than 10,000 people, and compares each town center with the rest of the town and with the same routes just outside town. The research questions are: (1) How many small towns have a state or U.S. highway as their main street, and how many fatal crashes occur on those segments? (2) How do fatal crash rates, pedestrian deaths, and time of day differ between town centers, the rest of town, and the approaches? (3) Do these patterns hold across regions, town sizes, and route types?`));
add(para(`The study extends earlier work by the author on highway corridors in an urbanizing city in Ghana, which found that informal economic activities along a national highway were associated with road accidents, traffic congestion, and poor sanitation, with 21.8% of reported accident cases involving informal economic actors (Nani et al., 2025), and on the author's county-level panel of U.S. rural road deaths (Nani, 2026b). The U.S. small-town main street is a different setting, but the question is the same: what happens to safety when a through highway is also a place where people trade and walk.`));

add(heading("Background"));
add(para(`Research on the built environment and traffic safety has long found that the design logic of high-speed roads fits poorly in places with active roadside uses. Reviews of this literature conclude that design features meant to make roads more forgiving at high speed can raise risk in developed settings where drivers meet pedestrians, turning vehicles, and parked cars (Ewing and Dumbaugh, 2009). Studies of community design and crash patterns similarly find that arterial strip commercial development is associated with more crashes than traditional, compact street patterns (Dumbaugh and Rae, 2009).`));
add(para(`Speed is the main mechanism for pedestrians. The risk that a struck pedestrian is killed rises steeply with vehicle impact speed (Tefft, 2013). This makes the transition from rural highway to town street a central safety problem. NCHRP Synthesis 412 reviewed speed-reduction techniques for rural high-to-low speed transitions (Forbes, 2011), and NCHRP Report 737 provided design guidance for the transition from a high-speed rural highway to a lower-speed section, typically approaching a small town (Torbic et al., 2012). That guidance focuses on the entry to town. Less is known nationally about what happens after the transition, in the town center itself, and how outcomes there compare with the approach.`));
add(para(`National analyses of pedestrian deaths have focused on large metropolitan areas, high-poverty counties, and arterial roads (GHSA, 2025; Smart Growth America, 2024). The author's earlier validation study showed that the FARS rural or urban label and the 2020 Census urban-area map disagree for a meaningful share of deaths at the edges of urban areas (Nani, 2026a), which is one reason a place-based definition is used here instead of the FARS label.`));

add(heading("Data and Methods"));
add(para(`All inputs are public. The full pipeline, provenance log, and outputs are released openly (see Data Availability). Table and figure values in this paper are generated directly from the pipeline's statistics file.`));
add(heading("Small Towns", 2));
add(para(`Outside New England, towns are incorporated places from the 2024 Census TIGER/Line files with a 2024 population estimate under 10,000 (U.S. Census Bureau, 2024, 2025). In New England, local government is organized by towns that the Census Bureau treats as county subdivisions, so towns and small cities under 10,000 were taken from that layer instead. Because New England towns often span 30 or more square miles of farmland and forest, "town limits" there were defined as the incorporated villages and Census Designated Places within the town; ${n0(S.towns_by_rule["new england town, no village (center only)"])} New England towns without such an area were given a center zone only. To exclude suburbs, any town with more than half of its land inside a 2020 Census urban area of 50,000 or more people was dropped (U.S. Census Bureau, 2023). Alaska and Hawaii were excluded. The result is ${n0(S.n_towns)} small towns.`));
add(heading("Town Centers", 2));
add(para(`A town center was defined from the locations of everyday destinations: shops, restaurants, offices and services, government buildings, schools, clinics, lodging, and cultural sites, from the Overture Maps places release of October 2026 (Overture Maps Foundation, 2026). Travel-oriented businesses such as fuel stations and car dealers were excluded so that a commercial strip at a highway edge would not be mistaken for a downtown. For each town, the destination with the most other destinations within a quarter mile (402 m) was found, and the center point was shifted once toward the mean of that cluster. A town has a center if at least 10 destinations lie within a quarter mile of that point; the town center zone is the quarter-mile circle, clipped to the town. ${n0(S.n_towns_with_center)} of ${n0(S.n_towns)} towns have an identifiable center. The rule was checked for a random sample of 45 towns (30 in Missouri, 15 in New England) against aerial imagery and against each town\'s recognized civic anchors (post office, town or city hall, and county courthouse) from the USGS Geographic Names Information System (U.S. Geological Survey, 2021). All 45 centers lay within a quarter mile of at least one civic anchor; in 3 towns the center is a civic or commercial strip on a highway rather than a traditional downtown.`));
add(heading("Highway Segments", 2));
add(para(`Road geometry and attributes come from the 2024 Highway Performance Monitoring System (HPMS) spatial data for each state (FHWA, 2025). Study roads are those signed as U.S. or state routes, plus any road owned by the state highway agency on a principal arterial, minor arterial, or collector. Interstates, ramps, local roads, and the second direction of divided highways were removed. Route signing alone was not sufficient because some states leave it blank for most of their system. Each road was cut into 50 m pieces, and each piece was assigned by its midpoint to one of three zones: town center; rest of town (inside town limits but outside the center); or outside town (the same route outside every incorporated place, within 5 miles of the town's limits, and assigned to the nearest town whose limits the route enters). Pieces were then combined into one segment per town, route, and zone, carrying length, traffic (annual average daily traffic, AADT), posted speed limit where reported, lanes, and on-street parking.`));
add(heading("Crash Matching", 2));
add(para(`Fatal crashes and victims come from the Fatality Analysis Reporting System (FARS), ${S.years} (NHTSA, 2026). A crash was matched to a study segment if its coordinates lie within 50 m of a study road and FARS records it on a U.S. or state highway, on a road owned by the state highway agency, or on a road whose route number matches the study route. The route-number test was needed because some states code state farm-to-market and similar routes as "other" roads with ownership not reported. Interstate crashes were never kept, which removes crashes at interchanges near study routes. Where more than one study road lay within 50 m, a route-number match was preferred, then the nearest road. Of ${n0(S.n_crashes_lower48)} fatal crashes in the study area, ${n0(S.n_crashes_matched)} were matched. The median distance from crash point to road is under 3 m, and the FARS route number agrees with the assigned route for ${pct(S.name_match_share)} of matched crashes.`));
add(heading("Rates", 2));
add(para(`Exposure is vehicle miles traveled (VMT), computed as 2024 AADT times segment length times 3,652.5 days. Rates are expressed per 100 million VMT, with exact Poisson 95% confidence intervals. Because traffic counts are largely missing on minor collectors, rates use segments on principal arterials, minor arterials, and major collectors with counts on at least 90% of their length; these hold ${pct(S.rate_base_share_of_crashes)} of matched crashes. Pedestrian deaths are FARS person records with person type pedestrian and fatal injury. Night is 6:00 p.m. to 5:59 a.m.`));

add(heading("Results"));
add(heading("A National Picture", 2));
add(para(`Of ${n0(S.n_towns)} small towns, ${n0(S.n_towns_with_segment)} have a state or U.S. highway within their limits or within 5 miles, and in ${n0(S.n_main_street_towns)} a study highway runs through the town center. These main street highways total ${n0(S.miles_by_zone.CENTER)} miles in town centers, ${n0(S.miles_by_zone.TOWN)} miles elsewhere in town, and ${n0(S.miles_by_zone.APPROACH)} miles on the approaches. Over ten years, ${n0(S.crashes_by_zone.CENTER)} fatal crashes occurred in town centers, ${n0(S.crashes_by_zone.TOWN)} in the rest of town, and ${n0(S.crashes_by_zone.APPROACH)} on the approaches (Table 1).`, { keepNext: true }));

add(caption("TABLE 1 Fatal Crashes and Rates by Zone, Small-Town State and U.S. Highways, " + S.years));
const t1rows = [C, T, P].map((r) => [zl[r.zone], n0(r.miles), f(r.vmt_100m, 0), n0(r.fatal_crashes), n0(r.fatalities),
  n0(r.ped_fatalities), `${f(r.crash_rate)} (${f(r.crash_rate_lo)}-${f(r.crash_rate_hi)})`,
  `${f(r.ped_rate, 3)} (${f(r.ped_rate_lo, 3)}-${f(r.ped_rate_hi, 3)})`, pct(r.ped_share, 1), pct(r.night_share, 1)]);
add(table(["Zone", "Miles", "100M VMT", "Fatal crashes", "Deaths", "Pedestrian deaths",
           "Crash rate (95% CI)", "Pedestrian death rate (95% CI)", "Pedestrian share of deaths", "Night share"],
          t1rows, [1300, 750, 750, 800, 750, 900, 1250, 1400, 900, 700]));
add(note(`Note: Rate base only (principal arterials, minor arterials, and major collectors with traffic counts). Rates per 100 million vehicle miles traveled (VMT) using 2024 AADT. CI = exact Poisson confidence interval.`));

add(para(`Per mile driven, fatal crashes were less frequent in town centers (${f(C.crash_rate)} per 100 million VMT) and the rest of town (${f(T.crash_rate)}) than on the approaches (${f(P.crash_rate)}). Pedestrian deaths showed the opposite pattern. The pedestrian death rate in town centers, ${f(C.ped_rate, 3)} per 100 million VMT, was ${ratio(C.ped_rate, P.ped_rate)} times the rate on the approaches (${f(P.ped_rate, 3)}) and ${ratio(C.ped_rate, T.ped_rate)} times the rate in the rest of town (${f(T.ped_rate, 3)}). The confidence intervals do not overlap. Pedestrians were ${pct(C.ped_share)} of people killed in town centers, ${pct(T.ped_share)} in the rest of town, and ${pct(P.ped_share)} on the approaches (Figure 1).`));
add(figure("fig1_rates_by_zone.png", 620, 262));
add(caption(`FIGURE 1 (a) Fatal crash rate and (b) pedestrian death rate per 100 million vehicle miles traveled (VMT), by zone. State and U.S. highways in and near U.S. towns under 10,000 people, ${S.years}; FARS crashes, HPMS ${S.hpms_year} traffic. Whiskers: 95% Poisson confidence intervals.`));

add(heading("Town Size, Region, and Route Type", 2));
const sz = (b, z) => R(z, S.rates_by_size, "size_band", b);
add(para(`The town-center excess in pedestrian deaths appears in every town size class and grows with town size (Figure 2). In towns of 2,500 to 9,999 people, the town-center pedestrian death rate was ${f(sz("2,500 to 9,999", "CENTER").ped_rate, 3)} per 100 million VMT, compared with ${f(sz("2,500 to 9,999", "APPROACH").ped_rate, 3)} on the approaches. In towns under 500, the center rate was ${f(sz("under 500", "CENTER").ped_rate, 3)} against ${f(sz("under 500", "APPROACH").ped_rate, 3)}, based on fewer deaths and with a wider interval.`));
add(figure("fig2_ped_rate_by_size.png", 620, 246));
add(caption("FIGURE 2 Pedestrian deaths per 100 million VMT by zone and town size. Whiskers: 95% Poisson confidence intervals."));

const rg = (g, z) => R(z, S.rates_by_region, "region", g);
const rt = (g, z) => R(z, S.rates_by_us_signed, "route_type", g);
const groups = [
  ...["under 500", "500 to 2,499", "2,500 to 9,999"].map((b) => ["Towns of " + b, (z) => sz(b, z)]),
  ...["Northeast", "Midwest", "South", "West"].map((g) => [g, (z) => rg(g, z)]),
  ["U.S. routes", (z) => rt("US", z)], ["State routes", (z) => rt("State", z)],
  ["Excluding New England", noNE], ["New England only", NEo],
];
add(para(`Table 2 compares the three zones across subgroups. The town-center pedestrian death rate exceeded the approach rate in all ${S.n_regions_center_higher_ped} Census regions and on both U.S. and state routes. The center-to-outside ratio was highest in the Midwest (${ratio(rg("Midwest", "CENTER").ped_rate, rg("Midwest", "APPROACH").ped_rate)}), and pedestrians made up the largest share of town-center deaths in the West (${pct(rg("West", "CENTER").ped_share)}) and Northeast (${pct(rg("Northeast", "CENTER").ped_share)}).`, { keepNext: true }));
add(caption("TABLE 2 Pedestrian Death Rate per 100 Million VMT by Zone and Subgroup"));
add(table(["Subgroup", "Town center", "Rest of town", "Outside town", "Ratio, center to outside", "Center pedestrian deaths"],
  groups.map(([lab, g]) => [lab, f(g("CENTER").ped_rate, 3), f(g("TOWN").ped_rate, 3), f(g("APPROACH").ped_rate, 3),
                            ratio(g("CENTER").ped_rate, g("APPROACH").ped_rate), n0(g("CENTER").ped_fatalities)]),
  [2400, 1300, 1300, 1300, 1600, 1500]));
add(note(`Note: Rate base only. New England towns use village limits (see Data and Methods).`));

add(heading("Time of Day", 2));
const pn = S.ped_crash_night_share_by_zone;
add(para(`About ${pct(C.night_share)} of fatal crashes occurred at night (6:00 p.m. to 5:59 a.m.) in every zone. Fatal pedestrian crashes differed: ${pct(pn.APPROACH)} occurred at night on the approaches and ${pct(pn.TOWN)} in the rest of town, but only ${pct(pn.CENTER)} in town centers, so daytime pedestrian deaths are relatively more common where shops and services are concentrated.`));

add(heading("Sensitivity to the New England Rule", 2));
add(para(`Because New England towns were defined differently, results were recomputed without them. Excluding New England, the town-center pedestrian death rate was ${f(noNE("CENTER").ped_rate, 3)} and the approach rate ${f(noNE("APPROACH").ped_rate, 3)} per 100 million VMT, nearly identical to the national figures. Within New England alone, rates were lower overall but showed the same pattern (${f(NEo("CENTER").ped_rate, 3)} versus ${f(NEo("APPROACH").ped_rate, 3)}).`));

add(heading("Discussion"));
add(para(`Small-town main street highways show a clear trade-off. Lower speeds in town centers appear to reduce the overall rate of fatal crashes compared with the approaches, but the people who die there are far more often pedestrians. The town-center pedestrian death rate is about ${ratio(C.ped_rate, P.ped_rate)} times the approach rate, consistent across regions, town sizes, and route types. This is the expected result when through traffic at arterial speeds shares a street with walking trips to shops, services, and schools, and it parallels the earlier finding from Ghana that informal economic activity along a national highway is tied to road accidents (Nani et al., 2025).`));
add(para(`Three implications follow for practice. First, state transportation agencies own these segments, so state Highway Safety Improvement Program screening can target them directly; the dataset provides a ready national list. Second, transition-zone guidance (Torbic et al., 2012) addresses the entry to town, but the deaths documented here occur inside the center, which points to crossing treatments, lighting, and speed management through the downtown block, not only at the town line. Third, the relatively high share of daytime pedestrian deaths in town centers suggests that measures aimed only at nighttime visibility will not address the full problem.`));
add(para(`For local planning, the dataset connects a town's land-use pattern, through its center, to the state road that serves it. Downtown revitalization that adds destinations along a state highway will add pedestrian exposure. Coordinating local downtown plans with state corridor design is one way to make sure that success on main street does not come with more deaths.`));

add(heading("Limitations"));
add(para(`The data are observational. Pedestrian exposure, the number of people walking, is not measured, so higher pedestrian death rates in centers partly reflect more walking. FARS records only crashes with a death within 30 days. Traffic volumes are the 2024 values applied to all ten years, and the road network is a 2024 snapshot, so towns that gained a bypass during the period are misrepresented for earlier years. Town centers are defined from a 2026 business snapshot. Posted speed limits are incomplete outside the National Highway System. Town limits are legal boundaries and may include rural land. These limits are documented in full with the dataset.`));

add(heading("Conclusions"));
add(para(`This study provides the first national, segment-level dataset of fatal crashes on state and U.S. highways that serve as small-town main streets. In ${n0(S.n_main_street_towns)} towns where such a highway runs through the center, fatal crashes are less frequent per mile driven than on the approaches, but pedestrian deaths are about ${ratio(C.ped_rate, P.ped_rate)} times as frequent. The dataset gives state agencies, small towns, and researchers a common base for finding these segments, tracking them over time, and evaluating treatments.`));

add(heading("Data Availability"));
add(para(`The dataset, code, provenance log, and documentation are available at Zenodo, https://doi.org/10.5281/zenodo.24030310 (Nani, 2026c), and GitHub, https://github.com/Emmanuel-Oti-Nani/main-street-highways.`));
add(heading("Author Contributions"));
add(para(`The author confirms sole responsibility for the following: study conception and design, data collection, analysis and interpretation of results, and manuscript preparation.`));
add(heading("Declaration of Conflicting Interests"));
add(para(`The author declares no potential conflicts of interest with respect to the research, authorship, and/or publication of this article.`));
add(heading("Funding"));
add(para(`The author received no financial support for the research, authorship, and/or publication of this article.`));

add(heading("References"));
const refs = [
  "Dumbaugh, E., and R. Rae. 2009. Safe Urban Form: Revisiting the Relationship Between Community Design and Traffic Safety. Journal of the American Planning Association, Vol. 75, No. 3, pp. 309-329.",
  "Ewing, R., and E. Dumbaugh. 2009. The Built Environment and Traffic Safety: A Review of Empirical Evidence. Journal of Planning Literature, Vol. 23, No. 4, pp. 347-367.",
  "FHWA. 2025. Highway Performance Monitoring System, 2024 Spatial Data by State. Federal Highway Administration, Washington, D.C. https://geo.dot.gov. Accessed November 2026.",
  "Forbes, G. J. 2011. NCHRP Synthesis 412: Speed Reduction Techniques for Rural High-to-Low Speed Transitions. Transportation Research Board, Washington, D.C. https://doi.org/10.17226/22890.",
  "GHSA. 2025. Pedestrian Traffic Fatalities by State: 2024 Preliminary Data (January-December). Governors Highway Safety Association, Washington, D.C.",
  "Nani, E. O. 2026a. How Rural Is Rural? Agreement Between the FARS Rural/Urban Label and 2020 Census Urban Areas for U.S. Traffic Deaths, 2015-2024. EarthArXiv preprint. https://doi.org/10.31223/X5RV4C.",
  "Nani, E. O. 2026b. U.S. Rural Road Fatality County Panel (Version 1.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.23547649.",
  "Nani, E. O. 2026c. Main Street Highways: Fatal Crashes on State and U.S. Highways Through Small-Town Centers (Version 1.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24030310.",
  "Nani, E. O., G. Camynta-Baezie, J. Anbazu, N. S. Antwi, D. Blija, E. Adabor, and M. O. Asibey. 2025. A Burgeon in Informal Economic Activities Along Highways in Urbanizing Cities: Implications for Sustainable Development. Transportation in Developing Economies, Vol. 11, No. 1, Article 5. https://doi.org/10.1007/s40890-024-00222-0.",
  "NHTSA. 2026. Fatality Analysis Reporting System (FARS) National Data Files, 2015-2024. National Highway Traffic Safety Administration, Washington, D.C. https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars. Accessed November 2026.",
  "Overture Maps Foundation. 2026. Overture Maps Places, Release 2026-10-21.0. https://overturemaps.org. Accessed November 2026.",
  "Smart Growth America. 2024. Dangerous by Design 2024. Smart Growth America, Washington, D.C.",
  "Tefft, B. C. 2013. Impact Speed and a Pedestrian's Risk of Severe Injury or Death. Accident Analysis & Prevention, Vol. 50, pp. 871-878.",
  "Torbic, D. J., D. K. Gilmore, K. M. Bauer, C. D. Bokenkroger, D. W. Harwood, L. M. Lucas, R. J. Frazier, C. S. Kinzel, D. L. Petree, and M. D. Forsberg. 2012. NCHRP Report 737: Design Guidance for High-Speed to Low-Speed Transition Zones for Rural Highways. Transportation Research Board, Washington, D.C. https://doi.org/10.17226/22670.",
  "U.S. Geological Survey. 2021. Geographic Names Information System, Domestic Names Archive (August 25, 2021). https://www.usgs.gov/tools/geographic-names-information-system-gnis. Accessed November 2026.",
  "U.S. Census Bureau. 2023. 2020 Census Urban Areas. Washington, D.C.",
  "U.S. Census Bureau. 2024. TIGER/Line Shapefiles, 2024: Places and County Subdivisions. Washington, D.C.",
  "U.S. Census Bureau. 2025. Annual Estimates of the Resident Population for Incorporated Places and Minor Civil Divisions, Vintage 2024. Washington, D.C.",
];
refs.forEach((r) => add(new Paragraph({ indent: { left: 360, hanging: 360 }, spacing: { after: 100 },
  children: [new TextRun({ text: (count(r), r), font: FONT, size: 24 })] })));

// ---------- title page ----------
const wordTotal = words + 250 * tables;
const titlePage = [
  ...(FINAL ? [] : [para("DRAFT - NOT VERIFIED - DO NOT SUBMIT", { nocount: true, align: AlignmentType.CENTER })]),
  new Paragraph({ spacing: { before: 1200, after: 480 }, alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: TITLE, font: FONT, size: 28, bold: true })] }),
  para([[A.name, { bold: true }]], { nocount: true }),
  para(A.affiliation, { nocount: true }),
  para("Email: " + A.email, { nocount: true }),
  para("ORCID: " + A.orcid, { nocount: true }),
  new Paragraph({ spacing: { before: 720 }, children: [] }),
  para(`Word Count: ${n0(words)} words + ${tables} table(s) x 250 = ${n0(wordTotal)} words`, { nocount: true }),
  para("Submission Date: [VERIFY: date of submission]", { nocount: true }),
  new Paragraph({ pageBreakBefore: true, children: [] }),
];

const doc = new Document({
  creator: A.name, title: TITLE,
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      lineNumbers: { countBy: 1, restart: LineNumberRestartFormat.NEW_PAGE, distance: 360 },
    },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Nani", font: FONT, size: 20 })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] }) },
    children: [...titlePage, ...body],
  }],
});

const out = path.join(ROOT, "paper", "manuscript_TRB2028.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log(`manuscript written: ${out}`);
  console.log(`text words ${words}, tables ${tables}, TRB count ${wordTotal} (limit 7,500)`);
});
