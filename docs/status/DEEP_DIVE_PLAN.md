# Phase 3: Deep-Dive Analysis Plan

**Last Updated**: March 9, 2026

The high-level analysis has revealed significant tactical shifts between Slot Y1 and Y2, but most findings are surface-level. The following deep dives are organized by analytical perspective and ordered by priority.

## Data Pipeline Gaps

| Gap | Status | Notes |
|-----|--------|-------|
| `statistics.json` not processed | ✅ **Fixed** (Mar 9) | `StatisticsProcessor` → `statistics.csv` per fixture |
| `scores.json` not processed | ✅ **Fixed** (Mar 9) | `ScoresProcessor` → `scores.csv` per fixture |
| `statistics` type_id mapping unverified | ✅ **Fixed** (Mar 9) | All 44 type_ids verified via API; `type_id_mapping.csv` saved |
| Events data underused | Pending | 500 events/match in processed CSVs — integrate in deep dives |

All critical pipeline blockers resolved. Deep dives can proceed.

---

## Perspective 1: Rival Analyst (Match Preparation)

*"I'm preparing to play Liverpool next week. What do I need to know?"*

**Deep Dive 1.1: Right-Side Vulnerability Quantification**
- **Question**: Exactly how much creative output was lost when Trent left?
- **Method**: Compare events originating from right-back position (x > 0.67, y > 0.67) -- key passes, crosses, long balls, through balls -- Trent vs Bradley vs Frimpong
- **Data needed**: events.json (have it), ball_coordinates (have it), lineups (have it)
- **Output**: Per-match creative actions from RB position, Y1 vs Y2

**Deep Dive 1.2: Pressing Trigger Analysis**
- **Question**: When and where does Liverpool press in Y2 vs Y1? Has pressing intensity dropped?
- **Method**: Combine tackles + fouls + interceptions by pitch zone and match minute. Map defensive actions to ball coordinates to see WHERE on the pitch defensive actions cluster.
- **Data needed**: events.json (defensive actions), ball_coordinates
- **Output**: Pressing heatmaps by season, pressing intensity by 15-minute intervals

**Deep Dive 1.3: Build-Up Play Patterns**
- **Question**: How does Liverpool progress the ball from defense to attack? Has this changed?
- **Method**: Track ball coordinate sequences -- consecutive coordinates moving from defensive third (x < 0.33) to attacking third (x > 0.67). Measure speed, route (central vs wide), and which side.
- **Data needed**: ball_coordinates with time estimates
- **Output**: Ball progression maps, average time from defensive to attacking third

**Deep Dive 1.4: Game-State Tactical Shifts**
- **Question**: How does Liverpool play when winning vs losing vs drawing?
- **Method**: Use scores.json to determine game state at each minute, then segment ball_coordinates and events by game state. Compare ball position distributions and event frequencies.
- **Data needed**: scores.json + ball_coordinates + events.json
- **Output**: Pitch heatmaps by game state, tactical profile when chasing vs protecting leads

**Deep Dive 1.5: Set-Piece Analysis**
- **Question**: How dangerous are Liverpool from corners, free kicks?
- **Method**: Extract corner and free kick events, link to subsequent ball coordinates and goal events. Compare Y1 (Trent delivering) vs Y2 (who delivers now?)
- **Data needed**: events.json (set piece events), scores.json
- **Output**: Set-piece conversion rates, delivery zones, who takes them now

**Deep Dive 1.6: Second-Half Vulnerability Deep Dive**
- **Question**: WHY do Liverpool concede more in the second half in Y2? When exactly do they fade?
- **Method**: Segment all metrics (tackles, passes, ball position, shots conceded) into 15-minute bins. Find the inflection point where performance drops. Cross-reference with substitution timing.
- **Data needed**: All processed data, segmented by match minute
- **Output**: Performance decay curves, optimal window to attack Liverpool

---

## Perspective 2: Liverpool Coaching Staff

*"What do we need to fix? Where are the integration problems?"*

**Deep Dive 2.1: Wirtz Integration Analysis**
- **Question**: How has Wirtz changed the team's attacking patterns? Is the system optimized for him?
- **Method**: Compare matches WITH Wirtz starting vs WITHOUT (if any). Analyze ball position patterns in the final third. Look at whether Wirtz's presence shifts play centrally (away from the wings Slot used in Y1).
- **Data needed**: lineups (Wirtz starts), ball_coordinates, events.json
- **Output**: Final-third heatmaps with/without Wirtz, passing lane concentration

**Deep Dive 2.2: Ekitike vs Previous Strikers**
- **Question**: How does Ekitike's movement differ from Jota/Diaz/Nunez in the striker role?
- **Method**: Compare ball coordinate patterns in the attacking third when each striker starts. Look at shot locations, big chances created, and whether the striker drops deep or stays high.
- **Data needed**: lineups (who plays ST), ball_coordinates, statistics.json (shots, big chances)
- **Output**: Striker movement profiles, shot location maps by striker

**Deep Dive 2.3: Kerkez vs Robertson Attacking Contribution**
- **Question**: Is Kerkez providing more width but less defensive stability?
- **Method**: Compare left-side ball activity, defensive actions on the left, and counter-attack vulnerability down Liverpool's left when Kerkez plays vs Robertson.
- **Data needed**: lineups, ball_coordinates (left side y < 0.33), events.json
- **Output**: Attacking vs defensive balance comparison at LB

**Deep Dive 2.4: Double Pivot Effectiveness**
- **Question**: Is the Gravenberch-Mac Allister pivot progressing the ball effectively?
- **Method**: Look at ball coordinate progression through the central zone (0.33 < y < 0.67, 0.33 < x < 0.67). Compare pass completion, ball progression speed, and turnovers in central midfield Y1 vs Y2.
- **Data needed**: ball_coordinates, events.json (passes, turnovers)
- **Output**: Central zone control metrics, ball progression rates

**Deep Dive 2.5: First-Half Slow Start Root Cause**
- **Question**: Why are Liverpool scoring 48% fewer first-half goals? Is it tactical conservatism or execution failure?
- **Method**: Compare first-half attacking statistics (shots, big chances, passes into final third) to determine if Liverpool are ATTEMPTING less or CONVERTING less. Look at ball position assertiveness in first 30 minutes.
- **Data needed**: statistics by half (from statistics.json), ball_coordinates (first half only)
- **Output**: First-half tactical profile -- conservative or wasteful?

---

## Perspective 3: Data Science / Statistical Rigor

*"Are our findings robust? What could we be getting wrong?"*

**Deep Dive 3.1: Full Statistical Comparison (40 Metrics)**
- **Question**: Which of the 40 match statistics show statistically significant changes?
- **Method**: Process all 40 type_ids from statistics.json. Run t-tests for Y1 vs Y2 on all metrics. Apply Bonferroni correction for multiple comparisons. Rank by effect size.
- **Data needed**: statistics.json (all type_ids)
- **Output**: Table of all 40 metrics with means, p-values, effect sizes, significance flags

**Deep Dive 3.2: Opponent-Adjusted Metrics**
- **Question**: Are the Y2 regressions partly explained by facing tougher opponents?
- **Method**: Compare Y1 vs Y2 metrics ONLY for matches against the same opponents. Use fixture_season_mapping to identify common opponents.
- **Data needed**: fixture_season_mapping, statistics.json
- **Output**: Opponent-adjusted Y1 vs Y2 comparison

**Deep Dive 3.3: Home vs Away Splits**
- **Question**: Are the Y2 problems concentrated at home or away?
- **Method**: Split all Y1 vs Y2 comparisons by home/away. Check if the attacking regression is uniform or location-dependent.
- **Data needed**: fixture_season_mapping (home/away), all processed data
- **Output**: Home/away separated performance tables

**Deep Dive 3.4: Temporal Trends Within Y2**
- **Question**: Is Liverpool improving as the season goes on (integration effect)?
- **Method**: Plot key metrics by matchweek within Y2. Look for improvement trends that would suggest new players are gelling.
- **Data needed**: fixture_season_mapping (dates), statistics.json, ball_coordinates
- **Output**: Time series plots of key metrics within Y2, trend analysis

**Deep Dive 3.5: Verify Type_ID Mapping**
- **Question**: Are we reading the right statistics?
- **Method**: Call SportsMonks API `/v3/football/types` to get official type_id -> name mapping. Cross-reference with our inferred mapping.
- **Data needed**: API access
- **Output**: Verified type_id lookup table

---

## Perspective 4: Scouting / Recruitment

*"What player profiles would fix the gaps?"*

**Deep Dive 4.1: Right-Back Creative Profile Gap**
- **Question**: What specific creative outputs are missing from RB? What profile is needed?
- **Method**: Quantify Trent's Y1 output from RB position (long balls, key passes, crosses into box, set-piece deliveries). Define the gap between this and Bradley/Frimpong output.
- **Data needed**: events.json filtered by RB position, statistics.json
- **Output**: Creative output benchmarks from RB, gap analysis

**Deep Dive 4.2: Striker Movement Profile**
- **Question**: Does Ekitike's movement suit the system, or is there a mismatch?
- **Method**: Compare attacking third ball patterns with different strikers. Identify if Ekitike operates in zones where supply is high or low.
- **Data needed**: lineups, ball_coordinates, statistics.json
- **Output**: Supply-demand mismatch analysis for striker position

---

## Perspective 5: Content / Storytelling

*"What makes the best narratives for the X/Twitter thread series?"*

**Deep Dive 5.1: The Trent Effect -- Before and After**
- **Question**: Can we definitively show how Trent's departure changed Liverpool's tactical DNA?
- **Method**: Side-by-side comparison of all relevant metrics: right-side activity, long balls, set pieces, creative actions from RB, defensive line height (via offsides). Create compelling before/after visualizations.
- **Data needed**: All processed + raw statistics data
- **Output**: Publication-ready comparison, the centerpiece story of the thread series

**Deep Dive 5.2: The Predictability Problem**
- **Question**: Can we prove Liverpool have become more predictable?
- **Method**: Match-to-match variance in ball position patterns, attacking entry points, and event distributions. Lower variance = more predictable.
- **Data needed**: ball_coordinates, events.json
- **Output**: Entropy/variance measures by season, tactical predictability index

**Deep Dive 5.3: Wirtz vs Szoboszlai -- Different #10s, Different Systems**
- **Question**: How does swapping the #10 change everything around them?
- **Method**: Compare team-level metrics (not just individual) when each #10 starts. Different #10 profiles create different tactical ecosystems.
- **Data needed**: lineups, all match data
- **Output**: Ecosystem comparison -- how one player changes the whole team's profile

---

## Analysis Priority Matrix

| Priority | Deep Dive | Effort | Impact | Perspective |
|----------|-----------|--------|--------|-------------|
| 1 | 3.1 Full statistical comparison | Medium | Very High | Data science |
| 2 | 3.5 Verify type_id mapping | Low | Critical | Data science |
| 3 | 1.4 Game-state tactical shifts | High | Very High | Rival analyst |
| 4 | 1.2 Pressing trigger analysis | Medium | High | Rival analyst |
| 5 | 2.1 Wirtz integration | Medium | High | Coaching |
| 6 | 1.6 Second-half vulnerability | Medium | High | Rival analyst |
| 7 | 2.5 First-half slow start | Medium | High | Coaching |
| 8 | 3.4 Temporal trends within Y2 | Low | High | Data science |
| 9 | 1.1 Right-side vulnerability | Medium | High | Rival analyst |
| 10 | 5.1 The Trent Effect | High | Very High | Content |
| 11 | 3.2 Opponent-adjusted metrics | Medium | Medium | Data science |
| 12 | 1.3 Build-up play patterns | High | Medium | Rival analyst |
| 13 | 2.2 Ekitike vs previous strikers | Medium | Medium | Coaching |
| 14 | 3.3 Home vs away splits | Low | Medium | Data science |
| 15 | 2.4 Double pivot effectiveness | Medium | Medium | Coaching |
| 16 | 1.5 Set-piece analysis | Medium | Medium | Rival analyst |
| 17 | 2.3 Kerkez vs Robertson | Low | Medium | Coaching |
| 18 | 5.2 Predictability problem | Medium | Medium | Content |
| 19 | 5.3 Wirtz vs Szoboszlai | Medium | Medium | Content |
| 20 | 4.1 RB creative profile gap | Low | Low | Scouting |
| 21 | 4.2 Striker movement profile | Medium | Low | Scouting |
