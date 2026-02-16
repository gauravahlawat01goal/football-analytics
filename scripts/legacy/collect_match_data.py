"""
Collect detailed match data for all Liverpool fixtures.

Collects 7 data includes for each fixture:
1. ballCoordinates - Player position tracking
2. events - Match events (passes, shots, tackles, etc.)
3. lineups - Player lineups with positions
4. formations - Team formations
5. statistics - Match statistics
6. participants - Team information
7. scores - Match scores

Usage:
    # Collect all fixtures from all seasons
    python scripts/collect_match_data.py
    
    # Collect specific season
    python scripts/collect_match_data.py --season 2023_24
    
    # Collect with custom rate limit
    python scripts/collect_match_data.py --rate-limit 10
    
    # Force re-download (skip resume)
    python scripts/collect_match_data.py --force

Features:
    - Automatic resume (skips existing files)
    - Rate limiting (6 seconds default)
    - Progress tracking
    - Error handling with summary
    - Works with new fixture file format

Estimated time:
    - 7 API calls per fixture × 6 seconds = ~42 seconds per fixture
    - For 114 fixtures: ~80 minutes total
    - Resume enabled: Only new fixtures take time
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


class MatchDataCollector:
    """Collects detailed match data for fixtures."""
    
    INCLUDES = [
        "ballCoordinates",
        "events",
        "lineups",
        "formations",
        "statistics",
        "participants",
        "scores",
    ]
    
    def __init__(self, data_dir: Path, rate_limit_seconds: float = 6.0, resume: bool = True):
        """
        Initialize collector.
        
        Args:
            data_dir: Base data directory
            rate_limit_seconds: Seconds between API calls
            resume: Skip existing files
        """
        self.data_dir = data_dir
        self.rate_limit = rate_limit_seconds
        self.resume = resume
        self.client = SportsMonkClient()
        
        self.raw_dir = data_dir / "raw"
        self.logs_dir = data_dir / "logs"
        
        for dir_path in [self.raw_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Stats
        self.stats = {
            "api_calls": 0,
            "files_created": 0,
            "files_skipped": 0,
            "errors": 0,
            "fixtures_processed": 0,
            "fixtures_completed": 0,
        }
        
        # Logging
        self.log_file = self.logs_dir / f"match_data_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to file and console."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def collect_fixture(self, fixture_id: int, fixture_name: str) -> dict:
        """
        Collect all includes for a single fixture.
        
        Args:
            fixture_id: Fixture ID
            fixture_name: Fixture name (for logging)
        
        Returns:
            Dictionary mapping include_name -> success status
        """
        fixture_dir = self.raw_dir / str(fixture_id)
        fixture_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for include_name in self.INCLUDES:
            output_path = fixture_dir / f"{include_name}.json"
            
            # Resume: skip if file exists
            if self.resume and output_path.exists():
                results[include_name] = True
                self.stats["files_skipped"] += 1
                continue
            
            try:
                # Rate limit
                time.sleep(self.rate_limit)
                
                # Fetch data
                data = self.client.get_fixture_details(
                    fixture_id=fixture_id,
                    include=include_name
                )
                self.stats["api_calls"] += 1
                
                # Save to file
                with open(output_path, "w") as f:
                    json.dump(data, f, indent=2)
                
                self.stats["files_created"] += 1
                results[include_name] = True
                
            except Exception as e:
                self.log(f"  ✗ {include_name}: {str(e)[:100]}", "ERROR")
                self.stats["errors"] += 1
                results[include_name] = False
        
        return results
    
    def collect_all(self, season_filter: str = None):
        """
        Collect match data for all fixtures.
        
        Args:
            season_filter: Optional season filter (e.g., "2023_24")
        """
        self.log("\n" + "="*80)
        self.log("LIVERPOOL MATCH DATA COLLECTION")
        self.log("="*80)
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Rate limit: {self.rate_limit} seconds between calls")
        self.log(f"Resume enabled: {self.resume}")
        
        # Load fixtures from all season files
        fixture_files = sorted(self.raw_dir.glob("fixtures_*.json"))
        
        if season_filter:
            fixture_files = [f for f in fixture_files if season_filter in f.stem]
        
        if not fixture_files:
            self.log("ERROR: No fixture files found!", "ERROR")
            self.log("Please run collect_all_fixtures.py first.", "ERROR")
            return
        
        # Load all fixtures
        all_fixtures = []
        
        for fixture_file in fixture_files:
            season_name = fixture_file.stem.replace("fixtures_", "").replace("_", "/")
            
            with open(fixture_file, "r") as f:
                fixtures = json.load(f)
            
            self.log(f"Loaded {len(fixtures)} fixtures from {season_name}")
            
            for fixture in fixtures:
                fixture["season"] = season_name
                all_fixtures.append(fixture)
        
        total_fixtures = len(all_fixtures)
        total_calls = total_fixtures * len(self.INCLUDES)
        
        self.log(f"\nTotal fixtures to process: {total_fixtures}")
        self.log(f"Total API calls needed: {total_calls}")
        self.log(f"Estimated time: ~{(total_calls * self.rate_limit) / 60:.1f} minutes")
        
        if self.resume:
            # Count existing files
            existing = 0
            for fixture in all_fixtures:
                fixture_dir = self.raw_dir / str(fixture["fixture_id"])
                if fixture_dir.exists():
                    existing_files = sum(1 for inc in self.INCLUDES if (fixture_dir / f"{inc}.json").exists())
                    existing += existing_files
            
            if existing > 0:
                self.log(f"Found {existing} existing files (will skip)")
                self.log(f"Reduced time: ~{((total_calls - existing) * self.rate_limit) / 60:.1f} minutes")
        
        self.log("\n" + "="*80)
        self.log("Starting collection...")
        self.log("="*80 + "\n")
        
        # Collect each fixture
        results = {}
        
        for idx, fixture in enumerate(all_fixtures, 1):
            fixture_id = fixture["fixture_id"]
            fixture_name = fixture.get("name", f"Fixture {fixture_id}")
            season = fixture.get("season", "Unknown")
            
            self.log(f"[{idx}/{total_fixtures}] {season}: {fixture_name} (ID: {fixture_id})")
            
            try:
                fixture_results = self.collect_fixture(fixture_id, fixture_name)
                results[fixture_id] = fixture_results
                
                self.stats["fixtures_processed"] += 1
                
                # Check if all includes succeeded
                if all(fixture_results.values()):
                    self.stats["fixtures_completed"] += 1
                    self.log(f"  ✓ Complete ({sum(fixture_results.values())}/{len(self.INCLUDES)} includes)")
                else:
                    failed = [inc for inc, success in fixture_results.items() if not success]
                    self.log(f"  ⚠ Partial ({sum(fixture_results.values())}/{len(self.INCLUDES)} includes) - Failed: {', '.join(failed)}", "WARN")
                
                # Progress update
                progress = (idx / total_fixtures) * 100
                self.log(f"  Progress: {progress:.1f}% ({idx}/{total_fixtures})")
                
            except Exception as e:
                self.log(f"  ERROR: {e}", "ERROR")
                self.stats["errors"] += 1
                results[fixture_id] = {inc: False for inc in self.INCLUDES}
        
        # Final summary
        self.log("\n" + "="*80)
        self.log("COLLECTION COMPLETE")
        self.log("="*80)
        
        total_includes = total_fixtures * len(self.INCLUDES)
        successful_includes = sum(sum(r.values()) for r in results.values())
        success_rate = (successful_includes / total_includes * 100) if total_includes > 0 else 0
        
        self.log(f"Fixtures processed: {self.stats['fixtures_processed']}")
        self.log(f"Fixtures completed: {self.stats['fixtures_completed']}")
        self.log(f"Total includes: {total_includes}")
        self.log(f"Successful: {successful_includes} ({success_rate:.1f}%)")
        self.log(f"Failed: {total_includes - successful_includes}")
        self.log(f"\nAPI calls made: {self.stats['api_calls']}")
        self.log(f"Files created: {self.stats['files_created']}")
        self.log(f"Files skipped (resume): {self.stats['files_skipped']}")
        self.log(f"Errors: {self.stats['errors']}")
        self.log(f"\n✓ Data saved to: {self.raw_dir}")
        self.log(f"✓ Log saved to: {self.log_file}")
        
        # Show failed includes if any
        failed_includes = []
        for fixture_id, includes in results.items():
            for include_name, success in includes.items():
                if not success:
                    failed_includes.append((fixture_id, include_name))
        
        if failed_includes:
            self.log(f"\n⚠ Failed includes ({len(failed_includes)}):", "WARN")
            for fixture_id, include_name in failed_includes[:10]:
                self.log(f"  • Fixture {fixture_id}: {include_name}", "WARN")
            if len(failed_includes) > 10:
                self.log(f"  ... and {len(failed_includes) - 10} more", "WARN")
            self.log("\nTo retry failed includes, run this script again", "WARN")


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Collect detailed match data for Liverpool fixtures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect all fixtures
  python scripts/collect_match_data.py
  
  # Collect specific season
  python scripts/collect_match_data.py --season 2023_24
  
  # Custom rate limit
  python scripts/collect_match_data.py --rate-limit 10
  
  # Force re-download
  python scripts/collect_match_data.py --force
        """
    )
    
    parser.add_argument(
        "--season",
        type=str,
        help="Filter by season (e.g., 2023_24, 2024_25, 2025_26)"
    )
    
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=6.0,
        help="Seconds between API calls (default: 6.0)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download (disable resume)"
    )
    
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Data directory (default: ../data)"
    )
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = MatchDataCollector(
        data_dir=args.data_dir,
        rate_limit_seconds=args.rate_limit,
        resume=not args.force
    )
    
    # Collect
    try:
        collector.collect_all(season_filter=args.season)
        print("\n✅ Collection complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        print(f"   Progress saved. Run the same command to resume.")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print(f"   Check log: {collector.log_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
