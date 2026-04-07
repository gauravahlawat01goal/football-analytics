"""
Fetch per-match PPDA and tactical metrics for Liverpool from FBRef via soccerdata.

PPDA (Passes Allowed Per Defensive Action) measures pressing intensity:
    lower PPDA = more intense pressing (fewer opponent passes per Liverpool def. action)
    typical range: 6–14 for PL teams

Outputs:
    data/processed/fbref/team_match_stats.csv   — misc + passing stats per match
    data/processed/fbref/ppda.csv               — PPDA per match (simplified)

Usage:
    poetry run python scripts/07_fetch_fbref_ppda.py
    poetry run python scripts/07_fetch_fbref_ppda.py --force-refresh

Requires:
    pip install soccerdata

Notes:
    FBRef frequently returns 403 errors. The soccerdata library retries 5× with
    exponential backoff. If all retries fail, the season is skipped and logged.
    Run again later when rate limits reset.
"""

import argparse
import logging
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Map our season labels to soccerdata's season format
SEASONS = {
    "2023-24": "2023-2024",
    "2024-25": "2024-2025",
    "2025-26": "2025-2026",
}

MANAGER_MAP = {
    "2023-24": "Klopp",
    "2024-25": "Slot",
    "2025-26": "Slot",
}

LIVERPOOL_FBREF_NAME = "Liverpool"
LEAGUE = "ENG-Premier League"
PROCESSED_DIR = Path("data/processed")
OUT_DIR = PROCESSED_DIR / "fbref"

# PPDA-related columns in FBRef misc stats
# FBRef PPDA is labelled 'ppda' and 'ppda_att' (defensive and attacking halves)
PPDA_COLS = ["ppda", "ppda_att"]


def fetch_season_stats(season_label: str, soccerdata_season: str) -> pd.DataFrame | None:
    """Fetch misc team match stats for one season. Returns None on failure."""
    try:
        import soccerdata as sd  # noqa: PLC0415
    except ImportError:
        log.error("soccerdata not installed. Run: pip install soccerdata")
        return None

    log.info("Fetching FBRef stats for %s...", season_label)
    try:
        fbref = sd.FBref(leagues=LEAGUE, seasons=soccerdata_season)
        # read_team_match_stats with stat_type='misc' includes PPDA, fouls, cards, etc.
        stats = fbref.read_team_match_stats(stat_type="misc")
        return stats
    except Exception as exc:
        log.warning("  Failed to fetch %s: %s", season_label, str(exc)[:200])
        return None


def extract_liverpool_ppda(stats: pd.DataFrame, season_label: str) -> pd.DataFrame:
    """
    Filter to Liverpool rows and extract PPDA + key misc stats.

    soccerdata FBref columns have MultiIndex headers for team_match_stats.
    We need to flatten and filter to Liverpool.
    """
    # Flatten MultiIndex columns if present
    if isinstance(stats.columns, pd.MultiIndex):
        stats = stats.copy()
        stats.columns = ["_".join(str(c) for c in col).strip("_") for col in stats.columns]

    log.debug("Columns after flatten: %s", list(stats.columns)[:20])

    # Filter to Liverpool rows
    # The index usually has (league, season, game_id, team, opponent, date)
    if hasattr(stats.index, "names") and "team" in (stats.index.names or []):
        lfc = stats.xs(LIVERPOOL_FBREF_NAME, level="team", drop_level=False)
    else:
        # Try filtering by column if team is a column
        team_col = next((c for c in stats.columns if "team" in c.lower()), None)
        if team_col:
            lfc = stats[stats[team_col].str.contains(LIVERPOOL_FBREF_NAME, na=False)]
        else:
            log.warning("  Cannot identify Liverpool rows — returning raw data for manual inspection")
            lfc = stats

    lfc = lfc.copy()
    lfc["season"] = season_label
    lfc["manager"] = MANAGER_MAP[season_label]
    return lfc.reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch FBRef PPDA data for Liverpool")
    parser.add_argument("--force-refresh", action="store_true", help="Re-fetch even if cache exists")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stats_path = OUT_DIR / "team_match_stats.csv"
    ppda_path = OUT_DIR / "ppda.csv"

    if stats_path.exists() and not args.force_refresh:
        log.info("team_match_stats.csv already exists — skipping. Use --force-refresh to re-fetch.")
        all_stats = pd.read_csv(stats_path)
    else:
        season_frames = []
        for season_label, soccerdata_season in SEASONS.items():
            raw = fetch_season_stats(season_label, soccerdata_season)
            if raw is None:
                log.warning("  No data for %s — FBRef may be rate-limiting. Try again later.", season_label)
                continue
            season_df = extract_liverpool_ppda(raw, season_label)
            season_frames.append(season_df)
            log.info("  %d Liverpool match rows for %s", len(season_df), season_label)

        if not season_frames:
            log.error("No data fetched from FBRef. FBRef may be temporarily blocking requests.")
            log.info("Suggestion: run again in a few minutes, or try from a different IP/VPN.")
            return

        all_stats = pd.concat(season_frames, ignore_index=True)
        all_stats.to_csv(stats_path, index=False)
        log.info("Saved %d rows to %s", len(all_stats), stats_path)

    # Extract just the PPDA view
    ppda_cols = [c for c in all_stats.columns if "ppda" in c.lower() or c in ("season", "manager", "date")]
    if ppda_cols:
        ppda_df = all_stats[ppda_cols].dropna(subset=[c for c in ppda_cols if "ppda" in c.lower()])
        ppda_df.to_csv(ppda_path, index=False)
        log.info("Saved PPDA data (%d rows) to %s", len(ppda_df), ppda_path)

        for season_label in SEASONS:
            season_ppda = ppda_df[ppda_df["season"] == season_label]
            ppda_col = next((c for c in ppda_cols if "ppda" in c.lower() and "att" not in c.lower()), None)
            if ppda_col and not season_ppda.empty:
                log.info("  %s PPDA: mean=%.2f, min=%.2f, max=%.2f",
                         season_label,
                         season_ppda[ppda_col].mean(),
                         season_ppda[ppda_col].min(),
                         season_ppda[ppda_col].max())
    else:
        log.warning("No PPDA columns found. Available: %s", list(all_stats.columns)[:30])


if __name__ == "__main__":
    main()
