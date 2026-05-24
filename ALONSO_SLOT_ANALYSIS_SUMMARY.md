# Alonso vs. Slot: Tactical Fit Analysis (Status & Methodology)

## Overview
This document serves as a handoff state for the investigation into Liverpool FC's managerial hiring decision in 2024. The analysis explores why the club's data department favored Arne Slot (evolutionary continuity) over Xabi Alonso (revolutionary structural shift) to succeed Jurgen Klopp.

## Methodology & Metrics
The analysis is grounded in comparing three managerial cohorts:
1. **Jurgen Klopp's Baseline:** Liverpool (2022-2024)
2. **Arne Slot's Continuity:** Liverpool (2024-2025)
3. **Xabi Alonso's Alternative:** Bayer Leverkusen (2022-2024)

### Core Metrics Investigated
*   **PPDA (Passes allowed Per Defensive Action):** Used to evaluate off-the-ball pressing intensity. Klopp/Slot operate at ~9.0-9.4 (high intensity), while Alonso operates at ~14.7 (compact mid-block traps).
*   **Attacking Output (xG) & Shot Distance:** Used to evaluate verticality and directness. 
*   **In-Possession Structure:** Evaluated the shift from a 4-3-3 / 4-2-3-1 (Klopp/Slot) to a rigid 3-4-2-1 (Alonso).
*   *(Contextual Metrics added via Sports Scientist Review)*: Field Tilt, Rest Defence, and Direct Speed.

## Codebase Changes & File Links

### 1. Data Ingestion Scripts (Refactored)
The following scripts were refactored from hardcoded "Liverpool" scripts into dynamic, CLI-driven tools supporting multiple teams and leagues (e.g., `--team-slug "Bayer Leverkusen"`).
*   `scripts/01_collect_fixtures.py` (Uses `argparse` & `pathlib` for safe output routing)
*   `scripts/02_collect_match_data.py` (Accepts dynamic input files)
*   `scripts/06_fetch_understat_xg.py` (Refactored to enforce Understat URL formatting)

### 2. New Scripts Created
*   `scripts/08_fetch_understat_ppda.py`: A dedicated script to pull PPDA and Deep Completions data from Understat's league history endpoints.

### 3. Data Analysis & Output
*   **Jupyter Notebook:** `notebooks/alonso_tactical_fit_analysis.ipynb`
    *   Loads the CSVs, merges match/PPDA data, and plots comparative distributions for PPDA, xG, and Shot Distances.
*   **Final Report:** `web/liverpool/alonso_vs_slot/index.html`
    *   A styled, consumer-friendly HTML report detailing the tactical conclusions.
    *   *Note: This report was heavily audited by a simulated Sports Data Scientist agent to correct anachronisms (e.g., removing departed/deceased players like Nunez and Jota) and to fix tactical misinterpretations (clarifying that Alonso's high PPDA is a calculated trap, not "passive" defending).*

## Multi-Agent Workflow Log
To execute this analysis, the following agent personas were utilized:
1.  **Ingestion Data Engineer (Sonnet 4.6):** Drafted the CLI architectures.
2.  **Adversarial Reviewer (GPT-5.4):** Critiqued the engineering drafts, enforcing strict `pathlib` usage and fixing URL serialization bugs.
3.  **Sports Data Scientist (Opus 4.7):** Reviewed the initial tactical conclusions, pointing out severe anachronisms and introducing advanced tactical context (Rest Defence, Mid-block traps vs Gegenpressing).

## Status
**COMPLETE.** The data has been fetched via Understat, processed in the Jupyter Notebook, and synthesized into the final HTML report. 

## Next Steps for Future Agents
*   If a `SPORTSMONK_API_KEY` is provided in the `.env` file, a future agent can run `01_collect_fixtures.py` and `02_collect_match_data.py` to pull granular SportsMonks event data (passing networks, average player positions) to visually map Alonso's 3-4-2-1 vs Slot's 4-2-3-1.
