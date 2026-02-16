"""
Download detailed match data for all Liverpool fixtures.

This script uses the MatchDataCollector to download all 7 data includes
for each fixture:
1. ballCoordinates - Ball tracking data
2. events - Match events
3. lineups - Player lineups
4. formations - Team formations
5. statistics - Match statistics
6. participants - Team information
7. scores - Score details

Usage:
    poetry run python scripts/02_collect_match_data.py

Input:
    data/raw/fixtures_list.json (from 01_collect_fixtures.py)

Output:
    data/raw/{fixture_id}/{include_name}.json for each fixture

Features:
    - Automatic resume (skips existing files)
    - Rate limiting (6 seconds between requests)
    - Progress tracking
    - Error handling with summary report
    - Automatic backup to data/backup/

Estimated time:
    ~7 API calls per fixture × 6 seconds = ~42 seconds per fixture
    For 57 fixtures: ~40 minutes total

TODO (Framework Evolution):
    - Add --fixtures-file argument for custom input
    - Add --includes argument to select specific includes
    - Add --parallel flag for async collection
    - Add --retry flag to retry only failed includes
    - Add email/Slack notification on completion
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.collectors import MatchDataCollector
from football_analytics.utils import backup_directory, load_json, setup_logging


def print_header():
    """Print script header."""
    print("=" * 70)
    print("LIVERPOOL MATCH DATA COLLECTION")
    print("=" * 70)
    print()


def print_configuration(num_fixtures: int):
    """Print collection configuration."""
    print("Configuration:")
    print(f"  Fixtures to collect: {num_fixtures}")
    print("  Includes per fixture: 7")
    print(f"  Total API calls: {num_fixtures * 7}")
    print("  Rate limit: 6 seconds between calls")
    print(f"  Estimated time: ~{(num_fixtures * 7 * 6) / 60:.1f} minutes")
    print("  Output directory: data/raw/")
    print()


def print_includes_info():
    """Print information about what will be collected."""
    includes = [
        ("ballCoordinates", "Ball position tracking throughout match"),
        ("events", "Match events (passes, shots, tackles, etc.)"),
        ("lineups", "Player lineups with positions"),
        ("formations", "Team formations"),
        ("statistics", "Match statistics"),
        ("participants", "Team information"),
        ("scores", "Score details"),
    ]

    print("Includes to be collected:")
    for include_name, description in includes:
        print(f"  • {include_name}: {description}")
    print()


def backup_collected_data(fixture_ids: list):
    """Create backup of collected data."""
    print()
    print("Creating backup of collected data...")

    backed_up = 0
    for fixture_id in fixture_ids:
        fixture_dir = Path(f"data/raw/{fixture_id}")
        if fixture_dir.exists():
            try:
                backup_directory(fixture_dir, Path("data/backup"))
                backed_up += 1
            except Exception as e:
                print(f"  Warning: Failed to backup fixture {fixture_id}: {e}")

    print(f"✓ Backed up {backed_up}/{len(fixture_ids)} fixtures to data/backup/")
    print()


def print_summary(results: dict, collector: MatchDataCollector):
    """Print collection summary."""
    print()
    print("=" * 70)
    print("COLLECTION SUMMARY")
    print("=" * 70)

    # Calculate success rates
    total_fixtures = len(results)
    total_includes = total_fixtures * 7
    successful_includes = sum(sum(includes.values()) for includes in results.values())

    print(f"Fixtures processed: {total_fixtures}")
    print(f"Total includes: {total_includes}")
    print(f"Successful: {successful_includes} ({successful_includes/total_includes*100:.1f}%)")
    print(f"Failed: {total_includes - successful_includes}")
    print()

    # Show failed includes if any
    failed_includes = []
    for fixture_id, includes in results.items():
        for include_name, success in includes.items():
            if not success:
                failed_includes.append((fixture_id, include_name))

    if failed_includes:
        print(f"Failed includes ({len(failed_includes)}):")
        for fixture_id, include_name in failed_includes[:10]:  # Show first 10
            print(f"  • Fixture {fixture_id}: {include_name}")
        if len(failed_includes) > 10:
            print(f"  ... and {len(failed_includes) - 10} more")
        print()
        print("To retry failed includes, you can run this script again")
        print("or use the retry_failed_includes() method programmatically.")
        print()

    # Stats
    stats = collector.get_stats()
    print("Statistics:")
    print(f"  API calls made: {stats['api_calls']}")
    print(f"  Files created: {stats['files_created']}")
    print(f"  Files skipped (resume): {stats['files_skipped']}")
    print(f"  Errors: {stats['errors']}")
    print()

    # Data location
    print("✓ Data saved to: data/raw/")
    print("✓ Backup created in: data/backup/")
    print()

    print("Next steps:")
    print("  1. Verify data quality (check a few fixture directories)")
    print("  2. Run 03_process_ball_coords.py to process ball coordinates")
    print("  3. Run 04_process_events.py to process match events")
    print()


def main():
    """Download all match data for Liverpool fixtures."""
    # Setup logging
    setup_logging(level="INFO", log_file="logs/02_collect_match_data.log")

    print_header()

    # Load fixtures list
    fixtures_path = Path("data/raw/fixtures_list.json")

    if not fixtures_path.exists():
        print("ERROR: fixtures_list.json not found!")
        print("Please run 01_collect_fixtures.py first.")
        print()
        return

    fixtures = load_json(fixtures_path)

    print(f"Loaded {len(fixtures)} fixtures from {fixtures_path}")
    print()

    # Print configuration
    print_configuration(len(fixtures))
    print_includes_info()

    # Confirm before starting
    print("This will take approximately", f"{(len(fixtures) * 7 * 6) / 60:.1f}", "minutes")
    print("Resume is enabled - existing files will be skipped")
    print()

    response = input("Continue? [Y/n]: ").strip().lower()
    if response and response != "y":
        print("Collection cancelled.")
        return

    print()
    print("Starting collection...")
    print("=" * 70)
    print()

    # Initialize collector
    collector = MatchDataCollector(
        output_dir="data/raw", rate_limit_seconds=6.0, resume=True  # Skip existing files
    )

    # Collect all fixtures
    results = collector.collect_all_fixtures(fixtures)

    # Create backup
    fixture_ids = [f["fixture_id"] for f in fixtures]
    backup_collected_data(fixture_ids)

    # Print summary
    print_summary(results, collector)


if __name__ == "__main__":
    main()
