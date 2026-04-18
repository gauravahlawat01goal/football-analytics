# Liverpool FC Tactical Analysis

Data-driven analysis of Liverpool FC's tactical evolution across three seasons — Klopp's final year (2023-24), Slot Year 1 (2024-25), and Slot Year 2 (2025-26) — using the SportsMonks API.

**Goal**: Answer *how* and *why* Liverpool's playing style has changed, not just *what* the numbers say. Output is a 6-part X/Twitter thread series backed by statistical analysis and spatial data.

**Published**: [gauravahlawat01goal.github.io/football-analytics](https://gauravahlawat01goal.github.io/football-analytics/) — Jekyll publication site with full methodology, verified findings, and the thread series.

---

## Project Status

**~75% complete** — analysis phase complete, 26 charts generated, entering content publishing phase.

| Phase | Status |
|-------|--------|
| Data collection (114 fixtures, 7 includes each) | ✅ Complete |
| Data processing pipeline | ✅ Complete |
| Understat Tier 2 (xG) + FBRef Tier 3 (PPDA) | ✅ Integrated |
| Deep Dive 3.1: Full statistical comparison + ball zone presence | ✅ Complete |
| Deep Dive 1.4: Game-state tactical shifts | ✅ Complete |
| Analysis scripts 01–06 (replaces Jupyter execution) | ✅ Complete — 26 PNG charts generated |
| Remaining deep-dive analyses (07–10) | ⏳ Planned |
| GitHub Pages publication site | ✅ Live — Jekyll, PR #10 |
| X/Twitter thread series | 🔄 Thread 1 drafted + adversarially reviewed, pending publish |

See [`docs/status/PROJECT_STATUS.md`](docs/status/PROJECT_STATUS.md) for full phase breakdown and [`docs/status/DEEP_DIVE_PLAN.md`](docs/status/DEEP_DIVE_PLAN.md) for all 21 planned analyses.

---

## Key Findings So Far

- Results **regressed** in Y2: 2.14 (Klopp) → 2.12 (Y1) → 1.63 PPG (Y2)
- Formation shifted: 4-3-3 → 4-2-3-1
- Right-side attacking collapsed after Trent's transfer to Real Madrid (R-to-L ratio: 1.47 → 0.90)
- **Confirmed** (Bonferroni-corrected, Klopp vs Slot Y2): Shots On Target −37.2% (d=0.88), Tackles −25.7% (d=0.86), Goal Attempts −29.3% (d=0.87)
- **xG decline is quality, not luck**: xG/match 2.49 → 2.45 → 1.81 (−27%). All 3 seasons underperform xG by ~0.2/match consistently — Y2 regression is genuine chance quality decline
- **Set-piece xG halved**: 0.679 → 0.487 → 0.339/match — Trent's departure directly measurable
- **Pressing collapsed**: Tackles/match 17.9 → 13.3 (−26%, Bonferroni-confirmed)
- **Deadlock problem**: Y2 scores 0.73 go-ahead goals/match from level, down 25% vs Y1/Klopp (0.97). Y2 leads in only 63% of games vs 82% Y1
- **Second-half vulnerability**: Y2 concedes more after 60′; first-half goals dropped 48%

---

## Project Structure

```
football-analytics/
├── notebooks/                          # Analysis notebooks (source of truth for methodology)
│   ├── 01_statistical_comparison.ipynb # Deep Dive 3.1 — 44-metric comparison + zone presence
│   ├── 02_game_state_tactics.ipynb     # Deep Dive 1.4 — game-state reconstruction + lead management
│   ├── 03_pressing_analysis.ipynb      # Deep Dive 1.2 — pressing volume + FBRef PPDA
│   ├── 04_xg_analysis.ipynb            # Understat xG — quality vs luck proof + shot maps
│   ├── 05_wirtz_integration.ipynb      # Deep Dive 2.1 — with/without Wirtz spatial + temporal
│   └── 06_second_half.ipynb            # Deep Dive 1.6 — H1 vs H2 goals + decay curve
├── scripts/analysis/                   # Standalone scripts (run without Jupyter)
│   ├── 01_statistical_comparison.py    # Generates figures/01_statistical/
│   ├── 02_game_state_tactics.py        # Generates figures/02_game_state/
│   ├── 03_pressing_analysis.py         # Generates figures/03_pressing/
│   ├── 04_xg_analysis.py              # Generates figures/04_xg/
│   ├── 05_wirtz_integration.py         # Generates figures/05_wirtz/
│   └── 06_second_half.py              # Generates figures/06_second_half/
├── figures/                            # Generated charts (26 PNGs across 6 subdirs)
├── scripts/
│   ├── 01_collect_fixtures*.py         # Fixture collection (date search / team endpoint)
│   ├── 02_collect_match_data.py        # Fetch all includes per fixture (7 API calls each)
│   ├── 03_process_match_data.py        # Main processing pipeline
│   ├── 04_fetch_type_mappings.py       # Verify statistics type_id mapping
│   ├── 05_process_statistics_scores.py # Process statistics.csv and scores.csv per fixture
│   ├── 06_fetch_understat_xg.py        # Fetch Understat per-shot xG (Tier 2)
│   └── 07_fetch_fbref_ppda.py          # Fetch FBRef PPDA (Tier 3)
├── src/liverpool_strategy/
│   ├── analysis/
│   │   └── notebook_helpers.py         # Shared: cohens_d, mw_test, colors, setup_plot_style
│   └── game_state.py                   # Game-state reconstruction logic
├── src/football_analytics/
│   ├── api_client.py                   # SportsMonks API v3 client
│   ├── collectors/                     # Fixture + match data collectors
│   ├── processors/                     # One processor per data type
│   │   ├── ball_coordinates.py
│   │   ├── events.py
│   │   ├── lineups.py
│   │   ├── formations.py
│   │   ├── statistics.py
│   │   └── scores.py
│   └── utils/                          # Logging, JSON helpers, backup
├── web/                                # GitHub Pages publication site (Jekyll)
│   ├── _config.yml                     # Site config, baseurl /football-analytics
│   ├── _layouts/                       # default.html + post.html templates
│   ├── assets/css/style.css            # Design system (dark theme, Liverpool red)
│   ├── index.md                        # Landing page — auto-lists all posts
│   └── _posts/                         # One .md file per published thread
│       └── 2026-04-18-xg-decline-not-bad-luck.md
├── data/
│   ├── raw/{fixture_id}/               # Raw JSON from API (gitignored)
│   └── processed/
│       ├── fixtures/{fixture_id}/      # Processed CSVs per fixture (gitignored)
│       └── metadata/                   # fixture_season_mapping.csv, type_id_mapping.csv, liverpool_players.csv
├── docs/                               # Analysis docs (gitignored — local only)
│   ├── status/PROJECT_STATUS.md
│   ├── status/DEEP_DIVE_PLAN.md
│   └── analysis/                       # Findings logs and summaries
└── pyproject.toml
```

---

## Data

**101 fixtures processed** across three seasons:

| Season | Manager | Fixtures | Notes |
|--------|---------|----------|-------|
| 2023-24 | Klopp | 37 | Full season |
| 2024-25 | Slot Y1 | 34 | Full season |
| 2025-26 | Slot Y2 | 30 | Partial (season ongoing) |

Per fixture, six processed CSVs:

| File | Contents |
|------|----------|
| `ball_coordinates.csv` | Ball position tracking (~900 coords/match), pitch zone, estimated minute |
| `events.csv` | Match events (shots, tackles, goals, cards) with pitch coordinates |
| `lineups.csv` | Player lineups with positions |
| `formations.csv` | Team formations per period |
| `statistics.csv` | 44 match statistics per team (shots, passes, possession, etc.) |
| `scores.csv` | Period-level scores (1st half, 2nd half, full time) |

---

## Setup

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- SportsMonks API key ([free tier available](https://www.sportmonks.com/))

### Installation

```bash
git clone https://github.com/gauravahlawat01goal/football-analytics.git
cd football-analytics
poetry install
cp .env.example .env
# Add your SPORTSMONK_API_KEY to .env
```

### Running the pipeline

```bash
# 1. Collect fixtures for a season
poetry run python scripts/01_collect_fixtures_quick.py

# 2. Fetch match data (ball coords, events, lineups, formations, statistics, scores, participants)
echo "y" | poetry run python scripts/02_collect_match_data.py

# 3. Process all fixtures through the main pipeline
poetry run python scripts/03_process_match_data.py --all

# 4. Process statistics + scores
poetry run python scripts/05_process_statistics_scores.py --data-dir data/raw

# 5. Run analysis notebooks
poetry run jupyter notebook notebooks/
```

### Running the analysis scripts

No Jupyter required. Each script runs end-to-end and saves charts to `figures/`:

```bash
# Run any individual analysis
poetry run python scripts/analysis/04_xg_analysis.py       # xG charts (Thread 1 source)
poetry run python scripts/analysis/01_statistical_comparison.py
poetry run python scripts/analysis/02_game_state_tactics.py
poetry run python scripts/analysis/03_pressing_analysis.py
poetry run python scripts/analysis/05_wirtz_integration.py
poetry run python scripts/analysis/06_second_half.py
```

Charts are saved to `figures/04_xg/`, `figures/01_statistical/`, etc.

### Running tests

```bash
poetry run pytest
```

---

## Notebooks

| Notebook | Status | Description |
|----------|--------|-------------|
| `01_statistical_comparison.ipynb` | ✅ Done | 44-metric Mann-Whitney U comparison across seasons. Confirmatory (Klopp vs Slot) + exploratory (Y1 vs Y2) with separate Bonferroni correction. Ball zone presence analysis. |
| `02_game_state_tactics.ipynb` | ✅ Done | Game-state reconstruction (WIN/DRAW/LOSS) from goal events. Lead management, goals by game state. Key finding: Y2's regression is a deadlock problem — 25% fewer go-ahead goals/match from level. |
| `03_pressing_analysis.ipynb` | ✅ Written | Pressing volume (tackles, interceptions, fouls) with violin plots + significance tests. FBRef PPDA auto-loads if available. Needs Jupyter execution. |
| `04_xg_analysis.ipynb` | ✅ Written | Understat per-shot xG analysis. xG vs goals scatter (quality vs luck proof). Shot location pitch maps. Set-piece vs open-play xG breakdown. Needs Jupyter execution. |
| `05_wirtz_integration.ipynb` | ✅ Written | With/without Wirtz starting — attacking output (Key Passes, Big Chances, Shots) + spatial final-third analysis + temporal integration trend. Needs Jupyter execution. |
| `06_second_half.ipynb` | ✅ Written | H1 vs H2 goals, goal timing in 15-min bins, territorial decay curve, substitution timing proxy. Needs Jupyter execution. |

---

## Development

```bash
poetry run black src/ tests/
poetry run ruff check --fix src/ tests/
```

---

## About

Portfolio project. Analysis and thread series published on [X/Twitter](https://twitter.com/gauravahlawat01goal). Data provided by [SportsMonks](https://www.sportmonks.com/).
