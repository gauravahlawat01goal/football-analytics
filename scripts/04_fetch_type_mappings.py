#!/usr/bin/env python3
"""
Fetch the official type_id -> name mapping from the SportsMonks API.

Statistic type definitions are returned inline when fetching fixtures with
include=statistics.type. This script queries a few fixtures, collects all
unique type definitions, and saves them to:
    data/processed/metadata/type_id_mapping.csv

Also cross-references against the type_ids actually present in our
statistics.csv files and logs any unmapped IDs.

Usage:
    python scripts/04_fetch_type_mappings.py
    python scripts/04_fetch_type_mappings.py --stats-dir data/processed/fixtures
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient
from football_analytics.utils.logging_utils import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

OUTPUT_PATH = Path("data/processed/metadata/type_id_mapping.csv")

# Use our backup fixtures to extract type definitions — all stat types used
# across these 4 fixtures will cover the full range in our dataset.
SAMPLE_FIXTURE_IDS = [19134607, 18841624, 19134454, 19134479]


def fetch_type_mappings() -> pd.DataFrame:
    """
    Extract the type_id -> name mapping from our own fixture data.

    The SportsMonks /v3/core/types endpoint only returns event-level types
    (goals, cards, etc.). Statistic type definitions are returned inline when
    fetching fixtures with include=statistics.type. We query our backup
    fixtures, collect all unique type definitions, and build the lookup table.
    """
    client = SportsMonkClient()
    logger.info("Fetching statistic type definitions via fixture statistics.type include...")

    seen: dict[int, dict] = {}

    for fixture_id in SAMPLE_FIXTURE_IDS:
        try:
            response = client.get_fixture_details(fixture_id, include="statistics.type")
        except Exception as e:
            logger.warning(f"  Fixture {fixture_id}: {e}")
            continue

        stats = response.get("data", {}).get("statistics", [])
        for entry in stats:
            t = entry.get("type")
            if t and t.get("id") not in seen:
                seen[t["id"]] = t

        logger.info(f"  Fixture {fixture_id}: {len(stats)} stats, {len(seen)} unique types so far")

    if not seen:
        logger.error("No type definitions retrieved")
        return pd.DataFrame()

    rows = [
        {
            "type_id": t["id"],
            "name": t.get("name"),
            "code": t.get("code"),
            "developer_name": t.get("developer_name"),
            "model_type": t.get("model_type"),
            "stat_group": t.get("stat_group"),
        }
        for t in seen.values()
    ]

    df = pd.DataFrame(rows).sort_values("type_id").reset_index(drop=True)
    logger.info(f"Collected {len(df)} unique type mappings")
    return df


def cross_reference_with_statistics(mapping_df: pd.DataFrame, stats_dir: Path) -> None:
    """Log any type_ids present in our data that are missing from the mapping."""
    csv_files = list(stats_dir.glob("*/statistics.csv"))
    if not csv_files:
        logger.warning(f"No statistics.csv files found in {stats_dir}")
        return

    logger.info(f"Cross-referencing against {len(csv_files)} statistics.csv files...")

    all_type_ids = set()
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            if "type_id" in df.columns:
                all_type_ids.update(df["type_id"].dropna().astype(int).tolist())
        except Exception:
            pass

    mapped_ids = set(mapping_df["type_id"].dropna().astype(int).tolist())
    unmapped = all_type_ids - mapped_ids

    logger.info(f"Unique type_ids in our statistics data: {len(all_type_ids)}")
    logger.info(f"Mapped by API response:                 {len(all_type_ids - unmapped)}")

    if unmapped:
        logger.warning(f"Unmapped type_ids ({len(unmapped)}): {sorted(unmapped)}")
    else:
        logger.info("All type_ids in our data are mapped.")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch type_id mappings from SportsMonks API"
    )
    parser.add_argument(
        "--stats-dir",
        type=str,
        default="data/processed/fixtures",
        help="Directory containing processed fixture subdirectories (for cross-reference check)",
    )
    args = parser.parse_args()

    mapping_df = fetch_type_mappings()

    if mapping_df.empty:
        logger.error("No mapping data retrieved. Exiting.")
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    mapping_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    logger.info(f"Saved type_id mapping to {OUTPUT_PATH}")

    cross_reference_with_statistics(mapping_df, Path(args.stats_dir))

    # Print full statistic type list for quick validation
    stat_types = mapping_df[mapping_df["model_type"] == "statistic"]
    if not stat_types.empty:
        logger.info(f"\nAll {len(stat_types)} statistic types:")
        for _, row in stat_types.iterrows():
            logger.info(f"  type_id={row['type_id']:>6}  [{row['stat_group']}]  {row['name']}")


if __name__ == "__main__":
    main()
