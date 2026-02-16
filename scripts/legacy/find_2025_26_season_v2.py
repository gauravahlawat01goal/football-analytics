"""Script to find the 2025-2026 Premier League season ID - Alternative approach."""

import json
import sys
from pathlib import Path
from datetime import datetime
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Find the Premier League season ID for 2025-2026."""
    client = SportsMonkClient()

    print("=" * 80)
    print("FINDING 2025-2026 PREMIER LEAGUE SEASON ID")
    print("=" * 80)
    print(f"Current Date: {datetime.now().strftime('%Y-%m-%d')}")
    print()

    # Known info
    liverpool_id = 8
    premier_league_id = 8
    
    known_seasons = {
        "2023-24": 21646,
        "2024-25": 23614,
    }

    print("Known Seasons:")
    for season, sid in known_seasons.items():
        print(f"  {season}: {sid}")
    print()

    # Strategy 1: Get Liverpool team info with current season
    print("=" * 80)
    print("STRATEGY 1: Get Liverpool team info")
    print("=" * 80)
    
    found_2025_26 = None
    
    try:
        result = client._make_request(
            f"teams/{liverpool_id}",
            {"include": "currentseason"}
        )
        
        if result.get("data"):
            team = result["data"]
            print(f"✓ Team: {team.get('name')}")
            
            if "currentseason" in team:
                current_season = team["currentseason"]
                season_id = current_season.get("id")
                season_name = current_season.get("name")
                is_current = current_season.get("is_current")
                starting_at = current_season.get("starting_at", "")[:10]
                ending_at = current_season.get("ending_at", "")[:10]
                
                print(f"\nCurrent Season:")
                print(f"  ID: {season_id}")
                print(f"  Name: {season_name}")
                print(f"  Period: {starting_at} to {ending_at}")
                print(f"  Is Current: {is_current}")
                
                # Check if this is 2025-26
                if ("2025" in str(season_name) and "2026" in str(season_name)) or \
                   (starting_at and starting_at.startswith("2025")):
                    print(f"\n  >>> THIS IS 2025-2026! <<<")
                    found_2025_26 = {
                        "season_id": season_id,
                        "name": season_name,
                        "starting_at": starting_at,
                        "ending_at": ending_at,
                        "is_current": is_current
                    }
    
    except Exception as e:
        print(f"✗ Error: {e}\n")

    # Strategy 2: Get a recent Liverpool fixture and check its season
    print("\n" + "=" * 80)
    print("STRATEGY 2: Check recent Liverpool fixture")
    print("=" * 80)
    
    try:
        # Use the team's latest fixtures
        result = client._make_request(
            f"teams/{liverpool_id}",
            {"include": "latest"}
        )
        
        if result.get("data"):
            team = result["data"]
            
            if "latest" in team and team["latest"]:
                latest = team["latest"]
                print(f"\nLatest fixture:")
                print(f"  Name: {latest.get('name')}")
                print(f"  Date: {latest.get('starting_at', '')[:10]}")
                print(f"  Fixture ID: {latest.get('id')}")
                print(f"  Season ID: {latest.get('season_id')}")
                
                season_id = latest.get('season_id')
                match_date = latest.get('starting_at', '')[:10]
                
                # If this is a 2025 or 2026 match, this is our season!
                if match_date and (match_date.startswith('2025') or match_date.startswith('2026')):
                    print(f"\n  >>> This looks like 2025-2026 season! <<<")
                    
                    if not found_2025_26:
                        # Get more details about this season
                        try:
                            season_result = client._make_request(f"seasons/{season_id}", {})
                            if season_result.get("data"):
                                season_data = season_result["data"]
                                found_2025_26 = {
                                    "season_id": season_id,
                                    "name": season_data.get("name"),
                                    "starting_at": season_data.get("starting_at", "")[:10],
                                    "ending_at": season_data.get("ending_at", "")[:10],
                                    "is_current": season_data.get("is_current", False)
                                }
                        except:
                            found_2025_26 = {
                                "season_id": season_id,
                                "sample_date": match_date
                            }
    
    except Exception as e:
        print(f"✗ Error: {e}\n")

    # Strategy 3: Check the most recent fixture we have in our data
    print("\n" + "=" * 80)
    print("STRATEGY 3: Check our collected fixtures")
    print("=" * 80)
    
    try:
        fixtures_file = Path(__file__).parent.parent / "data" / "raw" / "fixtures_list.json"
        
        if fixtures_file.exists():
            with open(fixtures_file, "r") as f:
                fixtures = json.load(f)
            
            print(f"\n✓ Found {len(fixtures)} fixtures in our data")
            
            # Find the most recent fixture
            fixtures_sorted = sorted(fixtures, key=lambda x: x.get("date", ""), reverse=True)
            
            print("\nMost recent fixtures:")
            for fixture in fixtures_sorted[:5]:
                print(f"  {fixture.get('date')}: {fixture.get('name')}")
                print(f"    Season ID: {fixture.get('season_id')}, Fixture ID: {fixture.get('fixture_id')}")
                
                # Check if this is 2025-26
                date = fixture.get('date', '')
                season_id = fixture.get('season_id')
                
                if date.startswith('2025') or date.startswith('2026'):
                    if not found_2025_26 and season_id:
                        print(f"    >>> Potential 2025-2026 season! <<<")
                        found_2025_26 = {
                            "season_id": season_id,
                            "sample_date": date,
                            "sample_fixture": fixture.get('name')
                        }
                print()
        else:
            print("  No fixtures file found")
    
    except Exception as e:
        print(f"✗ Error: {e}\n")

    # Strategy 4: Manually test season IDs near the known ones
    print("=" * 80)
    print("STRATEGY 4: Manually test season IDs")
    print("=" * 80)
    
    # Since 23614 is 2024-25, let's try IDs after that
    test_range = range(23615, 23650)  # Test 35 IDs
    
    print(f"\nTesting season IDs from 23615 to 23649...")
    
    for season_id in test_range:
        try:
            # Try to get info about this season
            result = client._make_request(f"seasons/{season_id}", {})
            
            if result.get("data"):
                season = result["data"]
                name = season.get("name", "Unknown")
                league_id = season.get("league_id")
                starting_at = season.get("starting_at", "")[:10]
                
                # Only care about Premier League (league_id = 8)
                if league_id == premier_league_id:
                    print(f"  ✓ {season_id}: {name} (starts: {starting_at})")
                    
                    # Check if this is 2025-26
                    if ("2025" in str(name) and "2026" in str(name)) or \
                       (starting_at and starting_at.startswith("2025")):
                        print(f"    >>> THIS IS 2025-2026! <<<")
                        if not found_2025_26:
                            found_2025_26 = {
                                "season_id": season_id,
                                "name": name,
                                "starting_at": starting_at,
                                "league_id": league_id
                            }
            
            time.sleep(0.2)  # Rate limiting
        
        except Exception as e:
            # Silently skip invalid IDs
            pass

    # Final Results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if found_2025_26:
        print("\n✅ SUCCESS! Found 2025-2026 season:")
        print()
        for key, value in found_2025_26.items():
            print(f"  {key}: {value}")
        
        # Update metadata
        metadata_file = Path(__file__).parent.parent / "data" / "metadata.json"
        
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            # Add 2025-26 season info
            if "seasons" not in metadata:
                metadata["seasons"] = {}
            
            metadata["seasons"]["2025/26"] = {
                "season_id": found_2025_26["season_id"],
                **{k: v for k, v in found_2025_26.items() if k != "season_id"}
            }
            
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"\n✓ Updated metadata: {metadata_file}")
        
        except Exception as e:
            print(f"\n⚠ Error updating metadata: {e}")
    
    else:
        print("\n❌ Could not find 2025-2026 season ID")
        print("\n⚠️ NOTE: If today is actually Feb 16, 2024 (not 2026),")
        print("   then the 2025-26 season doesn't exist yet!")
        print("   The current season would be 2023-24.")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
