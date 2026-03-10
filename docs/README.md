# Documentation

Liverpool FC tactical analysis across 3 seasons (2023-26), comparing Arne Slot's system against Jurgen Klopp's final season using SportsMonks API match data. The end goal is a 6-part X/Twitter thread series backed by data visualizations.

## Where Things Stand

**Phase 3 (Analysis) is ~45% done. Overall project is ~65% complete.**

Data collection and processing are finished -- 96 matches processed with ball coordinates, events, lineups, formations, statistics, and scores. The pipeline gap (statistics.json and scores.json not being processed) was resolved on March 9, 2026. All 44 statistic type_ids are now verified against the API. High-level analysis revealed key findings (results regression in Slot Y2, right-side attacking collapse after Trent's transfer, formation shift from 4-3-3 to 4-2-3-1). What remains is deep-dive analysis, visualizations, and content creation.

For full status details: [`status/PROJECT_STATUS.md`](status/PROJECT_STATUS.md)

## What Needs To Be Done

**Next** -- execute the 21 planned deep-dive analyses in priority order starting with Deep Dive 3.1 (full statistical comparison across all 44 metrics):
- Full statistical comparison across 40 metrics (t-tests, effect sizes)
- Game-state tactical shifts (winning/losing/drawing)
- Pressing trigger analysis
- Wirtz integration impact
- And 17 more...

Full plan with priorities: [`status/DEEP_DIVE_PLAN.md`](status/DEEP_DIVE_PLAN.md)

**Finally** -- build visualizations and write the X/Twitter thread series.

## Folder Structure

```
docs/
├── README.md                          # This file
├── status/                            # Project status and planning
│   ├── PROJECT_STATUS.md              # Current phase, blockers, what's next
│   └── DEEP_DIVE_PLAN.md             # 21 planned deep-dive analyses
├── analysis/                          # Analysis outputs and methodology
│   ├── ANALYSIS_LOG.md               # Running log of all findings (28+)
│   ├── KEY_FINDINGS_SUMMARY.md       # Executive summary of major findings
│   ├── SLOT_YEAR_COMPARISON.md       # Slot Year 1 vs Year 2 comparison
│   ├── CRITICAL_REVIEW.md           # Self-assessment and corrections
│   └── CRITICAL_ANALYSIS_FRAMEWORK.md # Analytical methodology
├── technical/                         # Pipeline and data documentation
│   ├── DATA_PROCESSING_PIPELINE.md   # Pipeline architecture
│   ├── PROCESSING_FAILURES_ANALYSIS.md # 18 failed fixtures analysis
│   └── DATA_STRATEGY.md             # Data analysis strategy
├── reference/                         # Reference materials
│   ├── SEASON_ID_RESOLUTION.md       # API season IDs (21646, 23614, 25583)
│   ├── BREAKTHROUGH_FIXTURE_COLLECTION.md # How fixture collection was solved
│   └── STEP_3_COMPLETE.md           # Data collection confirmation
└── archive/                           # Historical/superseded documents
    ├── COMPLETED_PHASES.md           # Phase 0-2 detailed history
    └── (14 historical files)
```

## Quick Reference

| I want to... | Go to |
|---|---|
| See project status and what's next | [`status/PROJECT_STATUS.md`](status/PROJECT_STATUS.md) |
| Pick up a deep-dive analysis task | [`status/DEEP_DIVE_PLAN.md`](status/DEEP_DIVE_PLAN.md) |
| Read key findings so far | [`analysis/KEY_FINDINGS_SUMMARY.md`](analysis/KEY_FINDINGS_SUMMARY.md) |
| Understand the data pipeline | [`technical/DATA_PROCESSING_PIPELINE.md`](technical/DATA_PROCESSING_PIPELINE.md) |
| See Slot Y1 vs Y2 comparison | [`analysis/SLOT_YEAR_COMPARISON.md`](analysis/SLOT_YEAR_COMPARISON.md) |
| Review analysis methodology | [`analysis/CRITICAL_ANALYSIS_FRAMEWORK.md`](analysis/CRITICAL_ANALYSIS_FRAMEWORK.md) |
| Look up API season IDs | [`reference/SEASON_ID_RESOLUTION.md`](reference/SEASON_ID_RESOLUTION.md) |
| Check why 18 fixtures failed | [`technical/PROCESSING_FAILURES_ANALYSIS.md`](technical/PROCESSING_FAILURES_ANALYSIS.md) |
| See Phase 0-2 completed work | [`archive/COMPLETED_PHASES.md`](archive/COMPLETED_PHASES.md) |

## Adding New Documentation

**Naming**: `UPPER_SNAKE_CASE.md`.

**Where to put it**:
- Active project status or planning -> `status/`
- Analysis findings, comparisons, methodology -> `analysis/`
- Pipeline, processing, data architecture -> `technical/`
- Lookup tables, API details, one-time solutions -> `reference/`
- Superseded or completed-phase docs -> `archive/`

**Required metadata** at the top of every doc:
```markdown
# Document Title

**Last Updated**: YYYY-MM-DD
**Purpose**: One-line description
```

**Rules**:
- Don't create status snapshots (e.g., `STATUS_REPORT_FEB_16.md`). Update `status/PROJECT_STATUS.md` instead.
- Don't version filenames (e.g., `PLAN_V2.md`). Use git history for versioning.
- Archive superseded docs rather than deleting them.
