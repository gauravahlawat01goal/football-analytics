"""
Collect all Liverpool fixtures for 2023/24 and 2024/25 seasons.

This script uses the FixtureCollector to find all Liverpool matches
in the specified seasons by searching date-by-date through the Premier
League calendar.

Usage:
    poetry run python scripts/01_collect_fixtures.py

Output:
    data/raw/fixtures_list.json - List of all Liverpool fixtures

Configuration:
    - Team ID: 8 (Liverpool)
    - Seasons: 21646 (2023/24), 23614 (2024/25)
    - Search interval: 7 days

TODO (Framework Evolution):
    - Accept team_id and season_ids as command-line arguments
    - Add --league flag for other leagues
    - Add --output flag for custom output path
    - Add progress bar with tqdm
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.collectors import FixtureCollector
from football_analytics.utils import setup_logging


def main():
    """Collect Liverpool fixtures for both seasons."""
    # Setup logging
    setup_logging(level="INFO", log_file="logs/01_collect_fixtures.log")

    print("=" * 70)
    print("LIVERPOOL FIXTURE COLLECTION")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  Team: Liverpool (ID: 8)")
    print("  Seasons: 2023/24 (21646), 2024/25 (23614)")
    print("  Output: data/raw/fixtures_list.json")
    print()

    # Initialize collector
    collector = FixtureCollector(
        team_id=8,  # Liverpool
        output_dir="data/raw",
        rate_limit_seconds=6.0,
        resume=True,  # Skip if fixtures_list.json already exists
    )

    # Collect fixtures for both seasons
    print("Starting collection...")
    print()

    fixtures = collector.collect_fixtures_for_seasons(
        season_ids=[21646, 23614], search_interval_days=7  # 2023/24, 2024/25  # Check every week
    )

    # Print summary
    print()
    print("=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(f"Total fixtures found: {len(fixtures)}")
    print()

    # Group by season for summary
    by_season = {}
    for fixture in fixtures:
        season_id = fixture["season_id"]
        by_season.setdefault(season_id, []).append(fixture)

    for season_id, season_fixtures in sorted(by_season.items()):
        season_name = "2023/24" if season_id == 21646 else "2024/25"
        print(f"  Season {season_name} (ID {season_id}): {len(season_fixtures)} fixtures")

        # Show sample fixtures
        print("    Sample fixtures:")
        for fixture in season_fixtures[:3]:
            print(f"      - {fixture['date'][:10]}: {fixture['name']}")

    print()
    print("✓ Fixtures saved to: data/raw/fixtures_list.json")
    print()

    # Print statistics
    stats = collector.get_stats()
    print("Statistics:")
    print(f"  API calls made: {stats['api_calls']}")
    print(f"  Files created: {stats['files_created']}")
    print(f"  Errors encountered: {stats['errors']}")
    print()

    print("Next step: Run 02_collect_match_data.py to download detailed match data")
    print()


if __name__ == "__main__":
    main()
