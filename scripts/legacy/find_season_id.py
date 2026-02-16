"""Flexible script to find Premier League season ID for any season.

Usage:
    python find_season_id.py --season "2025-26"
    python find_season_id.py --season "2023-24"
    python find_season_id.py --start-date "2025-08-01" --end-date "2026-05-31"
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def parse_season_string(season_str):
    """Parse season string like '2025-26' or '2025/26' to start/end years."""
    # Handle both formats: "2025-26" and "2025/26"
    season_str = season_str.replace("/", "-")
    
    if "-" in season_str:
        parts = season_str.split("-")
        if len(parts) == 2:
            start_year = int(parts[0])
            end_year = int(parts[1])
            
            # Handle 2-digit year format (e.g., "25" -> 2025)
            if end_year < 100:
                end_year = 2000 + end_year
            
            return start_year, end_year
    
    raise ValueError(f"Invalid season format: {season_str}. Use format like '2025-26' or '2025/26'")


def find_season_id(client, season_name=None, start_year=None, end_year=None, 
                   liverpool_id=8, premier_league_id=8):
    """
    Find Premier League season ID using multiple strategies.
    
    Args:
        client: SportsMonkClient instance
        season_name: Season string like "2025-26" or "2025/26"
        start_year: Start year (e.g., 2025)
        end_year: End year (e.g., 2026)
        liverpool_id: Liverpool team ID
        premier_league_id: Premier League ID
    
    Returns:
        dict with season info or None
    """
    print("=" * 80)
    print(f"SEARCHING FOR SEASON ID")
    print("=" * 80)
    
    if season_name:
        start_year, end_year = parse_season_string(season_name)
    
    print(f"Target Season: {start_year}-{end_year}")
    print(f"Expected dates: August {start_year} to May {end_year}")
    print()
    
    found_season = None
    
    # Strategy 1: Search through all Premier League seasons
    print("STRATEGY 1: Query all Premier League seasons")
    print("-" * 80)
    
    try:
        # Try without filters first
        result = client._make_request("seasons", {"per_page": 100})
        
        if result.get("data"):
            seasons = result["data"]
            print(f"✓ Retrieved {len(seasons)} seasons total")
            
            # Filter for Premier League
            pl_seasons = [s for s in seasons if s.get("league_id") == premier_league_id]
            print(f"✓ Found {len(pl_seasons)} Premier League seasons")
            
            # Look for our target season
            for season in pl_seasons:
                season_id = season.get("id")
                name = season.get("name", "")
                starting_at = season.get("starting_at", "")[:10]
                ending_at = season.get("ending_at", "")[:10]
                
                # Check if this matches our target years
                if starting_at:
                    start_date_year = int(starting_at[:4])
                    
                    # Match if starting year matches our target
                    if start_date_year == start_year:
                        print(f"\n  ✓ FOUND! Season ID: {season_id}")
                        print(f"    Name: {name}")
                        print(f"    Period: {starting_at} to {ending_at}")
                        
                        found_season = {
                            "season_id": season_id,
                            "name": name,
                            "starting_at": starting_at,
                            "ending_at": ending_at,
                            "league_id": premier_league_id,
                            "is_current": season.get("is_current", False)
                        }
                        break
            
            if not found_season:
                print(f"\n  ✗ Season {start_year}-{end_year} not found")
                print("\n  Available Premier League seasons:")
                for season in sorted(pl_seasons, key=lambda x: x.get("starting_at", ""), reverse=True)[:10]:
                    s_id = season.get("id")
                    s_name = season.get("name", "Unknown")
                    s_start = season.get("starting_at", "")[:10]
                    print(f"    ID {s_id}: {s_name} (starts: {s_start})")
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Strategy 2: Search Liverpool fixtures in the date range
    if not found_season:
        print("\n" + "=" * 80)
        print("STRATEGY 2: Find via Liverpool fixtures")
        print("-" * 80)
        
        try:
            # Search for Liverpool fixtures
            result = client._make_request(
                "fixtures/search/Liverpool",
                {"per_page": 100}
            )
            
            if result.get("data"):
                fixtures = result["data"]
                print(f"✓ Found {len(fixtures)} fixtures in search")
                
                # Filter for fixtures in our target year range
                target_fixtures = []
                for f in fixtures:
                    date_str = f.get("starting_at", "")[:10]
                    league_id = f.get("league_id")
                    
                    if date_str and league_id == premier_league_id:
                        year = int(date_str[:4])
                        if year in [start_year, end_year]:
                            target_fixtures.append(f)
                
                if target_fixtures:
                    print(f"✓ Found {len(target_fixtures)} fixtures in {start_year}-{end_year}")
                    
                    # Get season_id from one of these fixtures
                    sample = target_fixtures[0]
                    season_id = sample.get("season_id")
                    
                    print(f"\n  ✓ FOUND! Season ID: {season_id}")
                    print(f"    Sample fixture: {sample.get('name')}")
                    print(f"    Date: {sample.get('starting_at', '')[:10]}")
                    
                    found_season = {
                        "season_id": season_id,
                        "sample_fixture": sample.get("name"),
                        "sample_date": sample.get("starting_at", "")[:10],
                        "league_id": premier_league_id
                    }
                else:
                    print(f"  ✗ No fixtures found in {start_year}-{end_year}")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Strategy 3: Try sequential IDs based on pattern
    if not found_season:
        print("\n" + "=" * 80)
        print("STRATEGY 3: Try likely IDs based on known patterns")
        print("-" * 80)
        
        # Known pattern: 2023-24=21646, 2024-25=23614 (diff ~1968)
        known_mapping = {
            2023: 21646,
            2024: 23614,
        }
        
        if start_year - 1 in known_mapping:
            base_id = known_mapping[start_year - 1]
            estimated_id = base_id + 1968  # Average increment
            
            print(f"Estimated ID: {estimated_id} (based on +1968 pattern)")
            
            # Try a range around the estimate
            test_range = range(estimated_id - 50, estimated_id + 50)
            
            for test_id in test_range:
                try:
                    result = client._make_request(f"seasons/{test_id}", {})
                    
                    if result.get("data"):
                        season = result["data"]
                        league_id = season.get("league_id")
                        starting_at = season.get("starting_at", "")[:10]
                        
                        if league_id == premier_league_id and starting_at:
                            year = int(starting_at[:4])
                            
                            if year == start_year:
                                print(f"\n  ✓ FOUND! Season ID: {test_id}")
                                print(f"    Name: {season.get('name')}")
                                print(f"    Period: {starting_at} to {season.get('ending_at', '')[:10]}")
                                
                                found_season = {
                                    "season_id": test_id,
                                    "name": season.get("name"),
                                    "starting_at": starting_at,
                                    "ending_at": season.get("ending_at", "")[:10],
                                    "league_id": premier_league_id
                                }
                                break
                    
                    time.sleep(0.1)  # Rate limiting
                
                except:
                    continue
    
    return found_season


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Find Premier League season ID for any season",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find 2025-26 season
  python find_season_id.py --season "2025-26"
  
  # Find 2023-24 season
  python find_season_id.py --season "2023/24"
  
  # Find by explicit years
  python find_season_id.py --start-year 2025 --end-year 2026
        """
    )
    
    parser.add_argument(
        "--season",
        type=str,
        help="Season string (e.g., '2025-26' or '2025/26')"
    )
    
    parser.add_argument(
        "--start-year",
        type=int,
        help="Start year (e.g., 2025)"
    )
    
    parser.add_argument(
        "--end-year",
        type=int,
        help="End year (e.g., 2026)"
    )
    
    parser.add_argument(
        "--liverpool-id",
        type=int,
        default=8,
        help="Liverpool team ID (default: 8)"
    )
    
    parser.add_argument(
        "--league-id",
        type=int,
        default=8,
        help="Premier League ID (default: 8)"
    )
    
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save result to metadata.json"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.season:
        start_year, end_year = parse_season_string(args.season)
        season_name = args.season
    elif args.start_year and args.end_year:
        start_year = args.start_year
        end_year = args.end_year
        season_name = f"{start_year}-{str(end_year)[2:]}"
    else:
        parser.error("Must provide either --season or both --start-year and --end-year")
    
    # Initialize client
    client = SportsMonkClient()
    
    # Find season
    result = find_season_id(
        client,
        season_name=None,
        start_year=start_year,
        end_year=end_year,
        liverpool_id=args.liverpool_id,
        premier_league_id=args.league_id
    )
    
    # Print results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if result:
        print(f"\n✅ SUCCESS! Found season {season_name}:")
        print()
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        # Save to metadata if requested
        if args.save:
            metadata_file = Path(__file__).parent.parent / "data" / "metadata.json"
            
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                
                if "seasons" not in metadata:
                    metadata["seasons"] = {}
                
                metadata["seasons"][season_name.replace("-", "/")] = result
                
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)
                
                print(f"\n✓ Updated metadata: {metadata_file}")
            
            except Exception as e:
                print(f"\n⚠ Error updating metadata: {e}")
    else:
        print(f"\n❌ Could not find season {season_name}")
        print("\nPossible reasons:")
        print("  1. Season doesn't exist in API yet")
        print("  2. Season uses different naming/structure")
        print("  3. API subscription doesn't include this season")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
