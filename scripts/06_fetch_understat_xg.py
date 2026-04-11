"""
Fetch per-match and per-shot xG data from Understat for Liverpool's 3 seasons.

Outputs:
    data/processed/understat/match_xg.csv       — one row per fixture
    data/processed/understat/shots.csv          — one row per shot

Usage:
    poetry run python scripts/06_fetch_understat_xg.py
    poetry run python scripts/06_fetch_understat_xg.py --force-refresh

Requires:
    pip install understatapi
"""

import argparse
import logging
import time
from pathlib import Path

import pandas as pd
from understatapi import UnderstatClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Liverpool's Understat team_id / slug
LIVERPOOL_SLUG = "Liverpool"

# Map our season labels to Understat's year parameter (start year)
SEASONS = {
    "2023-24": "2023",
    "2024-25": "2024",
    "2025-26": "2025",
}

# Map Klopp / Slot by season
MANAGER_MAP = {
    "2023-24": "Klopp",
    "2024-25": "Slot",
    "2025-26": "Slot",
}

PROCESSED_DIR = Path("data/processed")
OUT_DIR = PROCESSED_DIR / "understat"


def fetch_match_xg(client: UnderstatClient) -> pd.DataFrame:
    """Fetch per-match xG for Liverpool across all 3 seasons."""
    rows = []
    for season_label, understat_year in SEASONS.items():
        log.info("Fetching match xG for %s (Understat year=%s)...", season_label, understat_year)
        try:
            matches = client.team(LIVERPOOL_SLUG).get_match_data(season=understat_year)
        except Exception as exc:
            log.error("Failed to fetch %s: %s", season_label, exc)
            continue

        for m in matches:
            if not m.get("isResult"):
                continue  # skip future fixtures

            lfc_side = m["side"]  # 'h' or 'a'
            opp_side = "a" if lfc_side == "h" else "h"

            rows.append(
                {
                    "understat_match_id": m["id"],
                    "season": season_label,
                    "manager": MANAGER_MAP[season_label],
                    "date": m["datetime"],
                    "lfc_side": lfc_side,
                    "home_team": m["h"]["title"],
                    "away_team": m["a"]["title"],
                    "lfc_goals": int(m["goals"][lfc_side]),
                    "opp_goals": int(m["goals"][opp_side]),
                    "lfc_xg": float(m["xG"][lfc_side]),
                    "opp_xg": float(m["xG"][opp_side]),
                    "result": m["result"],  # 'w', 'd', 'l' from Liverpool's perspective
                }
            )

        log.info("  %d completed matches for %s", sum(1 for m in matches if m.get("isResult")), season_label)
        time.sleep(1.0)  # polite rate limiting

    return pd.DataFrame(rows)


def fetch_shots(
    client: UnderstatClient, match_xg_df: pd.DataFrame, delay: float = 0.5
) -> pd.DataFrame:
    """Fetch per-shot data for all matches in match_xg_df."""
    all_shots = []
    total = len(match_xg_df)

    for idx, row in match_xg_df.iterrows():
        match_id = row["understat_match_id"]
        log.info(
            "Fetching shots for match %s (%s vs %s) [%d/%d]...",
            match_id,
            row["home_team"],
            row["away_team"],
            idx + 1,
            total,
        )
        try:
            shot_data = client.match(str(match_id)).get_shot_data()
        except Exception as exc:
            log.warning("  Skipping match %s: %s", match_id, exc)
            continue

        lfc_side = row["lfc_side"]
        lfc_shots = shot_data.get(lfc_side, [])

        for s in lfc_shots:
            all_shots.append(
                {
                    "understat_shot_id": s["id"],
                    "understat_match_id": match_id,
                    "season": row["season"],
                    "manager": row["manager"],
                    "date": row["date"],
                    "minute": int(s["minute"]),
                    "player": s["player"],
                    "player_id": s["player_id"],
                    "x": float(s["X"]),  # 0–1 scale, higher = closer to goal
                    "y": float(s["Y"]),  # 0–1 scale
                    "xg": float(s["xG"]),
                    "result": s["result"],  # Goal, SavedShot, MissedShots, BlockedShot
                    "situation": s["situation"],  # OpenPlay, SetPiece, FromCorner, Penalty, DirectFreekick
                    "shot_type": s["shotType"],  # LeftFoot, RightFoot, Head
                    "last_action": s.get("lastAction", ""),
                    "player_assisted": s.get("player_assisted", ""),
                }
            )

        time.sleep(delay)

    return pd.DataFrame(all_shots)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Understat xG data for Liverpool")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Re-fetch even if output files already exist",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    match_path = OUT_DIR / "match_xg.csv"
    shots_path = OUT_DIR / "shots.csv"

    client = UnderstatClient()

    # --- Match-level xG ---
    if match_path.exists() and not args.force_refresh:
        log.info("match_xg.csv already exists — skipping. Use --force-refresh to re-fetch.")
        match_df = pd.read_csv(match_path)
    else:
        match_df = fetch_match_xg(client)
        match_df.to_csv(match_path, index=False)
        log.info("Saved %d rows to %s", len(match_df), match_path)

    log.info("Match xG summary:\n%s", match_df.groupby("season")[["lfc_xg", "opp_xg", "lfc_goals", "opp_goals"]].mean().round(2))

    # --- Shot-level data ---
    if shots_path.exists() and not args.force_refresh:
        log.info("shots.csv already exists — skipping. Use --force-refresh to re-fetch.")
    else:
        shots_df = fetch_shots(client, match_df)
        shots_df.to_csv(shots_path, index=False)
        log.info("Saved %d shots to %s", len(shots_df), shots_path)
        log.info("Shots summary:\n%s", shots_df.groupby("season")["xg"].agg(["count", "mean", "sum"]).round(3))


if __name__ == "__main__":
    main()
