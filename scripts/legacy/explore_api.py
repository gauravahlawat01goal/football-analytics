"""Script to explore available API endpoints and data structure."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Explore API structure to understand how to access recent Liverpool data."""
    client = SportsMonkClient()

    print("=" * 80)
    print("API EXPLORATION")
    print("=" * 80)

    liverpool_id = 8

    # Test 1: Get team with all available includes
    print("\n1. Getting team with various includes...")
    includes_to_try = [
        "league",
        "country",
        "venues",
        "coaches",
        "sidelined",
    ]
    
    for include in includes_to_try:
        try:
            result = client._make_request(f"teams/{liverpool_id}", {"include": include})
            print(f"   ✓ {include}: Success")
            
            if result.get("data") and include in result["data"]:
                data = result["data"][include]
                if isinstance(data, list):
                    print(f"     - {len(data)} items")
                elif isinstance(data, dict):
                    print(f"     - Dict with keys: {list(data.keys())[:5]}")
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"   ✗ {include}: {error_msg}")

    # Test 2: Get leagues and look at structure
    print("\n2. Exploring leagues structure...")
    try:
        leagues = client.get_leagues()
        if leagues.get("data"):
            # Find Premier League
            for league in leagues["data"]:
                if league.get("id") == 8:  # Premier League
                    print(f"   ✓ Premier League found:")
                    print(f"     Keys available: {list(league.keys())}")
                    
                    # Check if it has season info
                    if "current_season_id" in league:
                        print(f"     Current season ID: {league['current_season_id']}")
                    break
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 3: Try different fixture endpoints
    print("\n3. Testing fixture endpoints...")
    
    # Try to get today's fixtures
    from datetime import datetime, timedelta
    
    test_dates = [
        datetime.now().strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "2024-08-17",  # Start of 2024/25 Premier League season
        "2024-01-01",  # Middle of 2023/24 season
    ]
    
    for date in test_dates:
        try:
            result = client._make_request(f"fixtures/date/{date}")
            if result.get("data"):
                fixtures = result["data"]
                # Filter for Liverpool
                liverpool_fixtures = [f for f in fixtures if 
                                     f.get("participants") and 
                                     any(p.get("id") == liverpool_id for p in f.get("participants", []))]
                
                if liverpool_fixtures:
                    for fixture in liverpool_fixtures:
                        fixture_id = fixture.get("id")
                        season_id = fixture.get("season_id")
                        match_name = fixture.get("name", "Unknown")
                        print(f"   ✓ {date}: {match_name}")
                        print(f"     Fixture ID: {fixture_id}, Season ID: {season_id}")
                        
                        # Save this info
                        metadata_file = Path(__file__).parent.parent / "data" / "metadata.json"
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        
                        if "recent_fixtures" not in metadata:
                            metadata["recent_fixtures"] = []
                        
                        metadata["recent_fixtures"].append({
                            "fixture_id": fixture_id,
                            "season_id": season_id,
                            "date": date,
                            "name": match_name
                        })
                        
                        with open(metadata_file, "w") as f:
                            json.dump(metadata, f, indent=2)
                else:
                    print(f"   - {date}: No Liverpool fixtures")
        except Exception as e:
            error_msg = str(e)[:80]
            print(f"   ✗ {date}: {error_msg}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
