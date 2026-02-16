"""
Robust fixture collection script with resume capability and rate limiting.

Collects all Liverpool Premier League fixtures for specified seasons with:
- Automatic resume from interruptions
- Rate limiting to avoid API quota issues
- Progress tracking and checkpoints
- Detailed logging
- Backup system

Usage:
    # Collect all three seasons
    python collect_all_fixtures.py
    
    # Collect specific season
    python collect_all_fixtures.py --season-id 21646
    
    # Resume from interruption
    python collect_all_fixtures.py --resume
    
    # Dry run (check what would be collected)
    python collect_all_fixtures.py --dry-run
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


class FixtureCollector:
    """Collects fixtures with resume capability and rate limiting."""
    
    def __init__(self, data_dir: Path, rate_limit_seconds: float = 6.5):
        """
        Initialize collector.
        
        Args:
            data_dir: Base data directory
            rate_limit_seconds: Seconds between API calls (default 6.5 = ~9 req/min)
        """
        self.data_dir = data_dir
        self.rate_limit = rate_limit_seconds
        self.client = SportsMonkClient()
        
        # Setup directories
        self.raw_dir = data_dir / "raw"
        self.backup_dir = data_dir / "backup"
        self.logs_dir = data_dir / "logs"
        
        for dir_path in [self.raw_dir, self.backup_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Progress tracking
        self.progress_file = self.logs_dir / "fixture_collection_progress.json"
        self.progress = self.load_progress()
        
        # Logging
        self.log_file = self.logs_dir / f"collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to file and console."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def load_progress(self) -> Dict:
        """Load progress from file or create new."""
        if self.progress_file.exists():
            with open(self.progress_file, "r") as f:
                return json.load(f)
        
        return {
            "started_at": datetime.now().isoformat(),
            "last_updated": None,
            "seasons": {},
            "total_fixtures_collected": 0,
            "total_fixtures_expected": 0,
            "completed": False
        }
    
    def save_progress(self):
        """Save current progress."""
        self.progress["last_updated"] = datetime.now().isoformat()
        
        with open(self.progress_file, "w") as f:
            json.dump(self.progress, f, indent=2)
    
    def get_season_fixtures(self, season_id: int, season_name: str) -> List[Dict]:
        """
        Get all Liverpool fixtures for a season.
        
        Args:
            season_id: Season ID to fetch fixtures for
            season_name: Season name (e.g., "2023/24") - for logging only
        
        Returns:
            List of fixture dictionaries for Liverpool matches
        """
        self.log(f"Fetching fixtures for season {season_name} (ID: {season_id})")
        
        liverpool_id = 8
        
        try:
            # Use the working API pattern: seasons/{id} with include=fixtures.participants
            self.log(f"  Calling API: seasons/{season_id}?include=fixtures.participants")
            
            result = self.client._make_request(
                f"seasons/{season_id}",
                {"include": "fixtures.participants"}
            )
            
            time.sleep(self.rate_limit)
            
            if not result or "data" not in result:
                self.log(f"  ERROR: No data in response", "ERROR")
                return []
            
            season_data = result["data"]
            self.log(f"  Season: {season_data.get('name', 'Unknown')}")
            
            # Extract fixtures
            if "fixtures" not in season_data:
                self.log(f"  ERROR: No fixtures in season data", "ERROR")
                return []
            
            # Handle both dict and list formats
            all_fixtures = season_data["fixtures"]
            if isinstance(all_fixtures, dict) and "data" in all_fixtures:
                all_fixtures = all_fixtures["data"]
            
            self.log(f"  Total fixtures in season: {len(all_fixtures)}")
            
            # Filter for Liverpool (team_id = 8)
            liverpool_fixtures = []
            
            for fixture in all_fixtures:
                if "participants" not in fixture:
                    continue
                
                # Handle both dict and list formats for participants
                participants = fixture["participants"]
                if isinstance(participants, dict) and "data" in participants:
                    participants = participants["data"]
                
                # Check if Liverpool is one of the participants
                team_ids = [p.get("id") for p in participants]
                if liverpool_id in team_ids:
                    liverpool_fixtures.append(fixture)
            
            self.log(f"  Found {len(liverpool_fixtures)} Liverpool fixtures")
            
            if liverpool_fixtures:
                # Sort by date for clarity
                liverpool_fixtures.sort(key=lambda x: x.get("starting_at", ""))
                first_date = liverpool_fixtures[0].get("starting_at", "")[:10]
                last_date = liverpool_fixtures[-1].get("starting_at", "")[:10]
                self.log(f"  Date range: {first_date} to {last_date}")
            
            return liverpool_fixtures
        
        except Exception as e:
            self.log(f"  Error fetching fixtures: {e}", "ERROR")
            import traceback
            self.log(f"  Traceback: {traceback.format_exc()}", "ERROR")
            return []
    
    def save_fixture_list(self, season_name: str, fixtures: List[Dict]):
        """Save fixture list to file."""
        output_file = self.raw_dir / f"fixtures_{season_name.replace('/', '_')}.json"
        
        # Extract essential info
        fixture_list = []
        for f in fixtures:
            fixture_list.append({
                "fixture_id": f.get("id"),
                "season_id": f.get("season_id"),
                "league_id": f.get("league_id"),
                "date": f.get("starting_at"),
                "name": f.get("name"),
                "home_team": f.get("participants", [{}])[0].get("name") if f.get("participants") else None,
                "away_team": f.get("participants", [{}])[1].get("name") if len(f.get("participants", [])) > 1 else None,
                "home_team_id": f.get("participants", [{}])[0].get("id") if f.get("participants") else None,
                "away_team_id": f.get("participants", [{}])[1].get("id") if len(f.get("participants", [])) > 1 else None,
                "state_id": f.get("state_id"),
            })
        
        # Sort by date
        fixture_list.sort(key=lambda x: x.get("date", ""))
        
        with open(output_file, "w") as f:
            json.dump(fixture_list, f, indent=2)
        
        # Also backup
        backup_file = self.backup_dir / f"fixtures_{season_name.replace('/', '_')}.json"
        with open(backup_file, "w") as f:
            json.dump(fixture_list, f, indent=2)
        
        self.log(f"  Saved {len(fixture_list)} fixtures to {output_file}")
        
        return fixture_list
    
    def collect_season(self, season_id: int, season_name: str, dry_run: bool = False) -> Dict:
        """
        Collect all fixtures for a season.
        
        Args:
            season_id: Season ID
            season_name: Season name
            dry_run: If True, only check what would be collected
        
        Returns:
            Dict with collection results
        """
        self.log(f"\n{'='*80}")
        self.log(f"COLLECTING SEASON: {season_name} (ID: {season_id})")
        self.log(f"{'='*80}")
        
        # Check if already collected
        season_key = f"{season_name}"
        if season_key in self.progress["seasons"] and self.progress["seasons"][season_key].get("completed"):
            self.log(f"  Season {season_name} already completed. Skipping.")
            return self.progress["seasons"][season_key]
        
        if dry_run:
            self.log(f"  [DRY RUN] Would collect fixtures for {season_name}")
            return {"dry_run": True}
        
        # Get fixtures
        fixtures = self.get_season_fixtures(season_id, season_name)
        
        if not fixtures:
            self.log(f"  ERROR: No fixtures found for {season_name}", "ERROR")
            return {"error": "No fixtures found"}
        
        # Save fixture list
        fixture_list = self.save_fixture_list(season_name, fixtures)
        
        # Update progress
        self.progress["seasons"][season_key] = {
            "season_id": season_id,
            "season_name": season_name,
            "fixture_count": len(fixture_list),
            "fixtures_collected": len(fixture_list),
            "completed": True,
            "completed_at": datetime.now().isoformat(),
            "date_range": f"{fixture_list[0]['date'][:10]} to {fixture_list[-1]['date'][:10]}" if fixture_list else None
        }
        
        self.progress["total_fixtures_collected"] += len(fixture_list)
        self.save_progress()
        
        self.log(f"  ✓ Season {season_name} complete: {len(fixture_list)} fixtures")
        
        return self.progress["seasons"][season_key]
    
    def collect_all(self, season_ids: Optional[List[int]] = None, dry_run: bool = False):
        """
        Collect all seasons.
        
        Args:
            season_ids: List of season IDs to collect (None = all from metadata)
            dry_run: If True, only show what would be collected
        """
        self.log(f"\n{'='*80}")
        self.log(f"LIVERPOOL FIXTURE COLLECTION")
        self.log(f"{'='*80}")
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Rate limit: {self.rate_limit} seconds between calls")
        self.log(f"Mode: {'DRY RUN' if dry_run else 'LIVE COLLECTION'}")
        
        # Load season info from metadata
        metadata_file = self.data_dir / "metadata.json"
        
        if not metadata_file.exists():
            self.log("ERROR: metadata.json not found!", "ERROR")
            return
        
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        seasons = metadata.get("seasons", {})
        
        if not seasons:
            self.log("ERROR: No seasons found in metadata!", "ERROR")
            return
        
        # Filter seasons if specific IDs requested
        if season_ids:
            seasons = {
                name: info for name, info in seasons.items()
                if info.get("season_id") in season_ids
            }
        
        self.log(f"\nSeasons to collect:")
        for name, info in seasons.items():
            self.log(f"  - {name}: ID {info.get('season_id')}")
        
        # Estimate total fixtures
        estimated_total = len(seasons) * 38  # ~38 fixtures per season
        self.progress["total_fixtures_expected"] = estimated_total
        
        self.log(f"\nEstimated total fixtures: ~{estimated_total}")
        self.log(f"Estimated time: ~{estimated_total * self.rate_limit / 60:.1f} minutes")
        
        if dry_run:
            self.log("\n[DRY RUN] No actual collection will occur")
            return
        
        # Collect each season
        results = {}
        
        for season_name, season_info in sorted(seasons.items()):
            season_id = season_info.get("season_id")
            
            try:
                result = self.collect_season(season_id, season_name, dry_run)
                results[season_name] = result
                
            except Exception as e:
                self.log(f"ERROR collecting {season_name}: {e}", "ERROR")
                results[season_name] = {"error": str(e)}
                
                # Save progress even on error
                self.save_progress()
        
        # Final summary
        self.log(f"\n{'='*80}")
        self.log(f"COLLECTION COMPLETE")
        self.log(f"{'='*80}")
        
        total_collected = sum(
            r.get("fixture_count", 0) for r in results.values()
            if "fixture_count" in r
        )
        
        self.log(f"Total fixtures collected: {total_collected}")
        self.log(f"Total time: {(datetime.now() - datetime.fromisoformat(self.progress['started_at'])).total_seconds() / 60:.1f} minutes")
        
        for season_name, result in results.items():
            if "fixture_count" in result:
                self.log(f"  ✓ {season_name}: {result['fixture_count']} fixtures")
            elif "error" in result:
                self.log(f"  ✗ {season_name}: {result['error']}", "ERROR")
        
        self.progress["completed"] = True
        self.save_progress()
        
        self.log(f"\nProgress saved to: {self.progress_file}")
        self.log(f"Log saved to: {self.log_file}")
        
        return results


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Collect Liverpool Premier League fixtures with resume capability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect all seasons from metadata
  python collect_all_fixtures.py
  
  # Collect specific season
  python collect_all_fixtures.py --season-id 21646
  
  # Multiple specific seasons
  python collect_all_fixtures.py --season-id 21646 23614 25583
  
  # Dry run (check what would be collected)
  python collect_all_fixtures.py --dry-run
  
  # Resume from interruption (same as running normally - auto-resumes)
  python collect_all_fixtures.py
  
  # Custom rate limit (requests per minute = 60/rate_limit)
  python collect_all_fixtures.py --rate-limit 10
        """
    )
    
    parser.add_argument(
        "--season-id",
        type=int,
        nargs="+",
        help="Specific season ID(s) to collect (default: all from metadata)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be collected without actually collecting"
    )
    
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=6.5,
        help="Seconds between API calls (default: 6.5 = ~9 req/min)"
    )
    
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Data directory (default: ../data)"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous run (automatic, kept for clarity)"
    )
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = FixtureCollector(
        data_dir=args.data_dir,
        rate_limit_seconds=args.rate_limit
    )
    
    # Check if resuming
    if collector.progress.get("seasons") and not args.dry_run:
        print(f"\n⚠️  Found previous collection progress:")
        print(f"   Started: {collector.progress.get('started_at')}")
        print(f"   Fixtures collected: {collector.progress.get('total_fixtures_collected', 0)}")
        
        completed_seasons = [
            name for name, info in collector.progress.get("seasons", {}).items()
            if info.get("completed")
        ]
        
        if completed_seasons:
            print(f"   Completed seasons: {', '.join(completed_seasons)}")
        
        print(f"\n   → Will resume and collect remaining fixtures\n")
        time.sleep(2)
    
    # Collect fixtures
    try:
        results = collector.collect_all(
            season_ids=args.season_id,
            dry_run=args.dry_run
        )
        
        print("\n✅ Collection complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        print(f"   Progress saved to: {collector.progress_file}")
        print(f"   Run the same command again to resume")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print(f"   Progress saved to: {collector.progress_file}")
        print(f"   Check log: {collector.log_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
