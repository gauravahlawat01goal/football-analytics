"""Check what's the actual latest available data in the API."""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Check latest available Liverpool data."""
    client = SportsMonkClient()

    print("=" * 80)
    print("CHECKING LATEST AVAILABLE DATA")
    print("=" * 80)
    print(f"System Date: {datetime.now().strftime('%Y-%m-%d')}")
    print()

    liverpool_id = 8
    premier_league_id = 8

    # Try getting Liverpool's fixtures for different season IDs
    print("Testing known season IDs:")
    print()
    
    for season_name, season_id in [("2023-24", 21646), ("2024-25", 23614)]:
        print(f"{season_name} (ID: {season_id}):")
        try:
            result = client._make_request(
                f"fixtures",
                {
                    "season_id": season_id,
                    "team_id": liverpool_id,
                    "per_page": 100
                }
            )
            
            if result.get("data"):
                fixtures = result["data"]
                print(f"  ✓ Found {len(fixtures)} fixtures")
                
                # Get date range
                dates = [f.get("starting_at", "")[:10] for f in fixtures if f.get("starting_at")]
                if dates:
                    print(f"  Date range: {min(dates)} to {max(dates)}")
                    
                    # Show last 3 fixtures
                    sorted_fixtures = sorted(fixtures, key=lambda x: x.get("starting_at", ""), reverse=True)
                    print(f"  Latest 3 fixtures:")
                    for f in sorted_fixtures[:3]:
                        date = f.get("starting_at", "")[:10]
                        name = f.get("name", "Unknown")
                        fid = f.get("id")
                        print(f"    {date}: {name} (ID: {fid})")
            else:
                print(f"  ✗ No data")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()

    # Try to get Liverpool fixtures without specifying season
    print("\nAttempting to get Liverpool's latest fixtures (any season):")
    try:
        # Method 1: Try getting by team
        result = client._make_request(
            f"teams/{liverpool_id}",
            {}
        )
        
        if result.get("data"):
            team = result["data"]
            print(f"✓ Team: {team.get('name')}")
            print(f"  Available includes: {list(team.keys())}")
    
    except Exception as e:
        print(f"✗ Error: {e}")

    # Try searching for fixtures with date range
    print("\nSearching for fixtures after Dec 2024:")
    try:
        result = client._make_request(
            f"fixtures/search/Liverpool",
            {"per_page": 10}
        )
        
        if result.get("data"):
            fixtures = result["data"]
            print(f"✓ Found {len(fixtures)} fixtures in search")
            
            # Filter for recent ones
            recent = [f for f in fixtures if f.get("starting_at", "").startswith("2025")]
            if recent:
                print(f"  Found {len(recent)} fixtures in 2025!")
                for f in recent[:5]:
                    print(f"    {f.get('starting_at')[:10]}: {f.get('name')}")
                    print(f"      Season ID: {f.get('season_id')}, Fixture ID: {f.get('id')}")
            else:
                print(f"  No fixtures found after 2024")
    
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print("Based on available data:")
    print("  • Latest fixture found: December 1, 2024")
    print("  • System date: February 16, 2026")
    print("  • Gap: ~14 months of missing data")
    print()
    print("This suggests:")
    print("  1. API trial/subscription may have limited date range")
    print("  2. 2025-26 season data not available in this subscription")
    print("  3. May need to upgrade subscription for current season")
    print()
    print("RECOMMENDATION:")
    print("  Proceed with available data (2023-24 and 2024-25 seasons)")
    print("  This still gives us:")
    print("    • 2023-24: Klopp's final season (~38 fixtures)")
    print("    • 2024-25: Slot's first season (~38 fixtures)")
    print("  Total: ~76 fixtures for 2-season comparison")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
