# Liverpool FC Tactical Analysis - Project Status

**Last Updated**: March 9, 2026
**Current Phase**: Phase 3 - Analysis (In Progress)
**Next Step**: Execute deep-dive analyses per DEEP_DIVE_PLAN.md priority order
**Status**: Pipeline gaps resolved — statistics and scores now in pipeline; all type_ids verified

---

## Project Summary

**Goal**: Analyze Liverpool FC's tactical evolution across 3 seasons (2023-24, 2024-25, 2025-26) with focus on:
- Arne Slot's tactical system vs Jurgen Klopp's approach
- Ryan Gravenberch's role in midfield control
- Data-driven insights for X/Twitter audience

**Data Source**: SportsMonks API v3
**Output**: X/Twitter thread series (6+ threads), visualizations, GitHub portfolio case study

---

## Phase Completion

| Phase | Status | Completion | Details |
|-------|--------|------------|---------|
| **Phase 0: Project Setup** | Complete | 100% | API access, git repo, dependencies |
| **Phase 1: Data Collection** | Complete | 100% | 114 fixtures collected, all includes |
| **Phase 2A: Processing Code** | Complete | 100% | 11/11 files fixed and hardened |
| **Phase 2B: Data Processing** | Complete | 100% | 96/114 fixtures processed (84% success) |
| **Phase 2C: Data Validation** | Complete | 100% | Quality validated, issues documented |
| **Phase 3: Analysis** | In Progress | ~40% | High-level analysis complete, deep dives needed |
| **Phase 4: Content Creation** | Not Started | 0% | X/Twitter threads |

**Overall Project Completion**: ~60%
**Critical Path**: Process raw statistics -> Deep-dive analyses -> Visualizations -> Content

---

## Phase 3: Analysis Progress

### Completed

**High-Level Structural Analysis** (see `../analysis/KEY_FINDINGS_SUMMARY.md`):
- Three-phase comparison (Klopp -> Slot Y1 -> Slot Y2)
- Formation change identified: 4-3-3 -> 4-2-3-1
- Personnel evolution mapped
- Gravenberch role transformation documented (wide CM -> defensive pivot)
- Home vs away patterns analyzed
- Opponent quality impact (Top 6 vs Other) analyzed

**Slot Year 1 vs Year 2 Comparison** (see `../analysis/SLOT_YEAR_COMPARISON.md`):
- Player-by-player positional analysis
- Width distribution shift (right-biased -> left-biased)
- Match-to-match consistency comparison

**Critical Self-Review** (see `../analysis/CRITICAL_REVIEW.md`):
- Discovered `statistics.json` (40 metrics/match) was never processed
- Revealed results REGRESSION in Year 2 (2.12 -> 1.68 PPG)
- Discovered attacking orientation flip (right -> left) due to Trent transfer
- Big chances created dropped 32%, long balls dropped 31%

### Analysis Corrections Made

1. **"Same system, better players" narrative was wrong** -- results regressed
2. **Trent was transferred (Real Madrid), not injured** -- permanent structural change
3. **Right-side attacking collapse missed** -- R-to-L ratio flipped from 1.47 to 0.90
4. **statistics.json data was never processed** -- 40 metrics/match sat unused
5. **Formation position data over-interpreted** -- starting positions != in-match movement

### Pipeline Fixes Completed (March 9, 2026)

**`statistics.json` now processed** — new `StatisticsProcessor` (`processors/statistics.py`) flattens each fixture's statistics into `data/processed/fixtures/{id}/statistics.csv`. Schema: `fixture_id, type_id, participant_id, location, value`. 4/4 backup fixtures processed successfully (78-88 entries per fixture).

**`scores.json` now processed** — new `ScoresProcessor` (`processors/scores.py`) flattens period-level scores into `data/processed/fixtures/{id}/scores.csv`. Schema: `fixture_id, type_id, participant_id, description, goals, participant`. Period entries: 1ST_HALF, 2ND_HALF, 2ND_HALF_ONLY, CURRENT.

**`type_id` mapping verified** — `scripts/04_fetch_type_mappings.py` confirmed all 44 type_ids in our data via the `statistics.type` include. Saved to `data/processed/metadata/type_id_mapping.csv`. 44/44 mapped, 0 unknown. Key stats available: Shots Total, Shots On Target, Ball Possession %, Passes, Successful Passes, Tackles, Interceptions, Key Passes, Big Chances Created, Successful Dribbles, Dangerous Attacks, Corners, Fouls, Long Passes, and more.

**Note on scores.json**: Period-level aggregates only (1ST_HALF / 2ND_HALF totals). For minute-by-minute game state, reconstruct from goal events in `events.csv` (already processed).

### What Remains

**Deep-dive analyses needed** -- see `DEEP_DIVE_PLAN.md` for the full plan (21 analyses across 5 perspectives). Pipeline gaps are resolved — all required data is now in processed CSVs.

---

## Key Documents

| Document | Purpose | Status |
|----------|---------|--------|
| `../analysis/CRITICAL_ANALYSIS_FRAMEWORK.md` | Analytical framework and methodology | Complete |
| `../analysis/ANALYSIS_LOG.md` | Running log of all findings (28+ findings) | Active |
| `../analysis/KEY_FINDINGS_SUMMARY.md` | Executive summary of all major findings | Complete |
| `../analysis/SLOT_YEAR_COMPARISON.md` | Detailed Y1 vs Y2 comparison | Complete |
| `../analysis/CRITICAL_REVIEW.md` | Self-assessment of gaps and errors | Complete |
| `DEEP_DIVE_PLAN.md` | 21 planned deep-dive analyses | Planned |

---

## Known Issues & Limitations

### Data Limitations

1. **Low Possession Inference** -- 0% in most fixtures; no possession events in API events.json. Workaround: use official stats from statistics.json.
2. **Event-Coordinate Linking** -- 60-80% success rate due to timing mismatches. Acceptable for analysis.
3. **18 Failed Fixtures** -- all future/incomplete matches. 96 high-quality matches available. See `../technical/PROCESSING_FAILURES_ANALYSIS.md`.
4. **No Opponent Data** -- only Liverpool fixtures collected. Out of scope for initial analysis.

### Technical Debt

1. **No Unit Tests** -- 0% coverage. Plan: write after analysis phase.
2. **Incomplete Type Hints** -- partial. Low priority.
3. **No CI/CD Pipeline** -- manual testing only. Low priority.

---

## Success Metrics

### Phase 3 (Current)

- [ ] 5 analysis notebooks completed
- [ ] All research questions answered
- [ ] 20+ publication-quality visualizations
- [ ] Findings documented

### Phase 4 (Future)

- [ ] 6 X/Twitter threads published
- [ ] Portfolio case study completed

---

## Next Steps

1. ~~**Process raw statistics/scores data** into pipeline~~ ✅ Done (March 9, 2026)
2. ~~**Verify type_id mapping**~~ ✅ Done — all 44 type_ids confirmed (March 9, 2026)
3. **Execute deep-dive analyses** per `DEEP_DIVE_PLAN.md` priority order — start with Deep Dive 3.1 (full statistical comparison across all 44 metrics)
4. **Build visualization library** (`src/football_analytics/visualizations.py`)
5. **Create analysis notebooks** in `notebooks/`
6. **Content creation** -- X/Twitter thread series

---

**Document Version**: 2.0
**Owner**: Gaurav Ahlawat
