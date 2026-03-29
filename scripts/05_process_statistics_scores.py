#!/usr/bin/env python3
"""
Process statistics.json and scores.json for all fixtures into the pipeline.

Reads raw JSON from data/backup/{fixture_id}/ and writes clean CSVs to
data/processed/fixtures/{fixture_id}/statistics.csv and scores.csv.

Usage:
    python scripts/05_process_statistics_scores.py
    python scripts/05_process_statistics_scores.py --fixture-id 19134607
    python scripts/05_process_statistics_scores.py --data-dir data/raw
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.processors.scores import ScoresProcessor
from football_analytics.processors.statistics import StatisticsProcessor
from football_analytics.utils.logging_utils import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def process_fixture(
    fixture_id: int,
    stats_processor: StatisticsProcessor,
    scores_processor: ScoresProcessor,
    output_dir: Path,
) -> dict:
    """Process statistics and scores for a single fixture."""
    result = {"fixture_id": fixture_id, "statistics": False, "scores": False}

    # Statistics
    stats_df = stats_processor.parse_statistics(fixture_id)
    if not stats_df.empty:
        stats_processor.save_statistics(stats_df, fixture_id, output_dir=str(output_dir))
        result["statistics"] = True
    else:
        logger.warning(f"  No statistics for fixture {fixture_id}")

    # Scores
    scores_df = scores_processor.parse_scores(fixture_id)
    if not scores_df.empty:
        scores_processor.save_scores(scores_df, fixture_id, output_dir=str(output_dir))
        result["scores"] = True
    else:
        logger.warning(f"  No scores for fixture {fixture_id}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Process statistics.json and scores.json for all fixtures"
    )
    parser.add_argument("--fixture-id", type=int, help="Process a single fixture by ID")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/backup",
        help="Directory containing raw fixture subdirectories (default: data/backup)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/fixtures",
        help="Base output directory for processed CSVs (default: data/processed/fixtures)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)

    if args.fixture_id:
        fixture_ids = [args.fixture_id]
    else:
        fixture_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.isdigit()]
        fixture_ids = sorted(int(d.name) for d in fixture_dirs)
        logger.info(f"Found {len(fixture_ids)} fixtures in {data_dir}")

    # Create processors once — they are stateless and can be reused across fixtures
    stats_processor = StatisticsProcessor(data_dir=str(data_dir))
    scores_processor = ScoresProcessor(data_dir=str(data_dir))

    stats_ok = scores_ok = stats_fail = scores_fail = 0

    for i, fixture_id in enumerate(fixture_ids, 1):
        logger.info(f"[{i}/{len(fixture_ids)}] Fixture {fixture_id}")
        result = process_fixture(fixture_id, stats_processor, scores_processor, output_dir)

        if result["statistics"]:
            stats_ok += 1
        else:
            stats_fail += 1

        if result["scores"]:
            scores_ok += 1
        else:
            scores_fail += 1

    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Fixtures processed:       {len(fixture_ids)}")
    logger.info(f"statistics.csv written:   {stats_ok}  ({stats_fail} failed)")
    logger.info(f"scores.csv written:       {scores_ok}  ({scores_fail} failed)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
