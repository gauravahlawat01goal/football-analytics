# Liverpool FC Tactical Analysis

Data-driven analysis of Liverpool FC's tactical evolution across three seasons — Klopp's final year (2023-24), Slot Year 1 (2024-25), and Slot Year 2 (2025-26) — using the SportsMonks API.

**Goal**: Answer *how* and *why* Liverpool's playing style has changed, not just *what* the numbers say. Output is a 6-part X/Twitter thread series backed by statistical analysis and spatial data.

---

## Project Status

**~75% complete** — pipeline done, Deep Dives 3.1 and 1.4 complete, analysis notebooks in progress.

| Phase | Status |
|-------|--------|
| Data collection (114 fixtures, 7 includes each) | ✅ Complete |
| Data processing pipeline | ✅ Complete |
| Deep Dive 3.1: Full statistical comparison + ball zone presence | ✅ Complete |
| Deep Dive 1.4: Game-state tactical shifts | ✅ Complete |
| Deep Dive 1.2: Pressing trigger analysis | 🔄 Next |
| Remaining 17 deep-dive analyses | ⏳ Planned |
| X/Twitter thread series | ⏳ Not started |

See [`docs/status/PROJECT_STATUS.md`](docs/status/PROJECT_STATUS.md) for full phase breakdown and [`docs/status/DEEP_DIVE_PLAN.md`](docs/status/DEEP_DIVE_PLAN.md) for all 21 planned analyses.

---

## Key Findings So Far

- Results **regressed** in Y2: 2.14 (Klopp) → 2.12 (Y1) → 1.63 PPG (Y2)
- Formation shifted: 4-3-3 → 4-2-3-1
- Right-side attacking collapsed after Trent's transfer to Real Madrid (R-to-L ratio: 1.47 → 0.90)
- **Confirmed** (Bonferroni-corrected, Klopp vs Slot Y2): Ball Safe −13.5% (d=1.11), Shots On Target −37.2% (d=0.88), Goal Attempts −29.3% (d=0.87), Tackles −25.7% (d=0.86)
- **Directional signals** (Y1 → Y2, nominally significant): Big Chances Created −32.6%, Shots On Target −28.0%, Successful Headers +45.5%
- **Game-state**: Y2 leads in only 63% of games (vs 82% Y1). Y2 scores 0.73 go-ahead goals/match from level — down 25% vs Y1/Klopp (0.97). The regression is a deadlock problem, not a lead-management problem.

---

## Project Structure

```
football-analytics/
├── notebooks/                          # Analysis notebooks
│   ├── 01_statistical_comparison.ipynb # Deep Dive 3.1 — 44-metric comparison + zone presence
│   └── 02_game_state_tactics.ipynb     # Deep Dive 1.4 — game-state reconstruction + lead management
├── scripts/
│   ├── 01_collect_fixtures*.py         # Fixture collection (date search / team endpoint)
│   ├── 02_collect_match_data.py        # Fetch all includes per fixture (7 API calls each)
│   ├── 03_process_match_data.py        # Main processing pipeline
│   ├── 04_fetch_type_mappings.py       # Verify statistics type_id mapping
│   └── 05_process_statistics_scores.py # Process statistics.csv and scores.csv per fixture
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

### Running tests

```bash
poetry run pytest
```

---

## Notebooks

| Notebook | Status | Description |
|----------|--------|-------------|
| `01_statistical_comparison.ipynb` | ✅ Done | 44-metric Welch's t-test comparison across seasons. Confirmatory (Klopp vs Slot) + exploratory (Y1 vs Y2) with separate Bonferroni correction. Ball zone presence analysis. |
| `02_game_state_tactics.ipynb` | ✅ Done | Game-state reconstruction (WIN/DRAW/LOSS) from goal events. Lead management, goals by game state, pitch heatmaps by state. Key finding: Y2's regression is a deadlock problem — 25% fewer go-ahead goals per match from level. |
| `03_pressing_analysis.ipynb` | 🔄 Next | Defensive event mapping to pitch zones. Pressing intensity and pressing line height by 15-min intervals. |
| `04_wirtz_integration.ipynb` | ⏳ Planned | With/without Wirtz starting — final third patterns, key passes, big chances created. |

---

## Development

```bash
poetry run black src/ tests/
poetry run ruff check --fix src/ tests/
```

---

## About

Portfolio project. Analysis and thread series published on [X/Twitter](https://twitter.com/gauravahlawat01goal). Data provided by [SportsMonks](https://www.sportmonks.com/).
