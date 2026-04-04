"""
Game state analysis helpers.
"""

from pathlib import Path

import pandas as pd


def get_lfc_is_home(fixture_id: int, fixtures_dir: Path, liverpool_id: int) -> bool | None:
    """
    Derive whether Liverpool is home or away from the scores.csv participant field.
    """
    sc_path = fixtures_dir / str(fixture_id) / "scores.csv"
    if not sc_path.exists():
        return None
    sc = pd.read_csv(sc_path)
    lfc_rows = sc[sc["participant_id"] == liverpool_id]
    if lfc_rows.empty:
        return None

    if "description" in lfc_rows.columns:
        current_rows = lfc_rows[lfc_rows["description"] == "CURRENT"]
        if not current_rows.empty:
            lfc_rows = current_rows

    participant_series = lfc_rows["participant"].dropna()
    if participant_series.empty:
        return None

    return participant_series.iloc[0] == "home"


def reconstruct_game_states(
    events_df: pd.DataFrame, lfc_is_home: bool
) -> list[tuple[int, int, int, str]]:
    """
    Build a sorted list of (effective_minute, lfc_goals, opp_goals, state) intervals
    from goal events in events_df.

    State legend:
        WIN  = Liverpool leading
        DRAW = level
        LOSS = Liverpool trailing
    """
    goals = events_df[
        events_df["result"].notna() & (events_df["result"].astype(str).str.strip() != "")
    ].copy()

    # Effective minute = minute + injury time (if any)
    goals["eff_minute"] = goals["minute"].fillna(0) + goals["extra_minute"].fillna(0)
    goals = goals.sort_values("eff_minute").reset_index(drop=True)

    intervals = [(0, 0, 0, "DRAW")]  # kick-off: 0-0

    for _, row in goals.iterrows():
        result_str = str(row["result"]).strip()
        if "-" not in result_str:
            continue
        parts = result_str.split("-")
        if len(parts) != 2:
            continue
        try:
            home_g, away_g = int(parts[0]), int(parts[1])
        except ValueError:
            continue

        lfc_g = home_g if lfc_is_home else away_g
        opp_g = away_g if lfc_is_home else home_g

        if lfc_g > opp_g:
            state = "WIN"
        elif lfc_g < opp_g:
            state = "LOSS"
        else:
            state = "DRAW"

        intervals.append((int(row["eff_minute"]), lfc_g, opp_g, state))

    return intervals


def get_state_at_minute(intervals: list[tuple[int, int, int, str]], minute: int) -> str:
    """Return Liverpool game state at a given match minute."""
    state = "DRAW"
    for m, _lg, _og, s in intervals:
        if m <= minute:
            state = s
        else:
            break
    return state


def final_score(intervals: list[tuple[int, int, int, str]]) -> tuple[int, int]:
    """Return (lfc_goals, opp_goals) from the last interval.

    Raises:
        ValueError: If ``intervals`` is empty.
    """
    if not intervals:
        raise ValueError("intervals must be a non-empty list of game state intervals")
    return intervals[-1][1], intervals[-1][2]
