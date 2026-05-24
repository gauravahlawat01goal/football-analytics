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

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.collectors import FixtureCollector
from football_analytics.utils import setup_logging


def main() -> None:
    """Collect team fixtures."""
    parser = argparse.ArgumentParser(description="Collect team fixtures.")
    parser.add_argument("--team-id", type=int, required=True, help="API Team ID")
    parser.add_argument("--team-name", type=str, required=True, help="Used for file naming")
    parser.add_argument("--season-ids", type=int, nargs="+", required=True, help="SportsMonks season IDs")
    parser.add_argument("--interval", type=int, default=7)
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Directory to save outputs")
    args = parser.parse_args()

    # Format team name safely for file creation
    safe_team_name = args.team_name.lower().replace(" ", "_")
    output_filename = f"{safe_team_name}_fixtures_list.json"
    
    # Configure path using pathlib and ensure parent directories exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename

    # Setup logging
    setup_logging(level="INFO", log_file="logs/01_collect_fixtures.log")

    print("=" * 70)
    print(f"{args.team_name.upper()} FIXTURE COLLECTION")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Team: {args.team_name} (ID: {args.team_id})")
    print(f"  Seasons: {args.season_ids}")
    print(f"  Output: {output_path}")
    print()

    # Initialize collector
    collector = FixtureCollector(
        team_id=args.team_id,
        output_dir=str(output_dir),
        rate_limit_seconds=6.0,
        resume=True,
    )
    # The FixtureCollector by default outputs to `fixtures_list.json` in output_dir. Let's see if we can override it.
    # We might need to handle the output_filename separately or rely on renaming it after.
    # Let's check if FixtureCollector allows custom filename. It might just write to `fixtures_list.json`.
    # Let's fix this up by reading the source of FixtureCollector.

    # Collect fixtures for both seasons
    print("Starting collection...")
    print()

    fixtures = collector.collect_fixtures_for_seasons(
        season_ids=args.season_ids, search_interval_days=args.interval
    )

    # Move the file if the default name was used
    default_output = output_dir / "fixtures_list.json"
    if default_output.exists() and default_output != output_path:
        import shutil
        import json
        
        # Load from default, save to customized, remove default
        with open(default_output, "r") as f:
            data = json.load(f)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        default_output.unlink()

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
        print(f"  Season (ID {season_id}): {len(season_fixtures)} fixtures")

        # Show sample fixtures
        print("    Sample fixtures:")
        for fixture in season_fixtures[:3]:
            print(f"      - {fixture['date'][:10]}: {fixture['name']}")

    print()
    print(f"✓ Fixtures saved to: {output_path}")
    print()

    # Print statistics
    stats = collector.get_stats()
    print("Statistics:")
    print(f"  API calls made: {stats['api_calls']}")
    print(f"  Files created: {stats['files_created']}")
    print(f"  Errors encountered: {stats['errors']}")
    print()

    print(f"Next step: Run 02_collect_match_data.py --input-file {output_path}")
    print()


if __name__ == "__main__":
    main()
