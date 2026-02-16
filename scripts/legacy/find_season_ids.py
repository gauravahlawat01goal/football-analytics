"""Script to find correct Premier League season IDs by trying common patterns."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Try to find Premier League season IDs for 2023/24 and 2024/25."""
    client = SportsMonkClient()

    print("=" * 80)
    print("FINDING PREMIER LEAGUE SEASON IDs")
    print("=" * 80)

    # Premier League ID is 8 (confirmed earlier)
    premier_league_id = 8
    liverpool_id = 8

    # Common season ID patterns for Sportsmonks:
    # Recent seasons are typically in the 21000-24000 range
    # Let's try a few likely candidates
    
    potential_season_ids = [
        21646,  # Often 2023/24
        23787,  # Another common pattern
        23872,  # Another pattern
        21826,  # 2024/25 possibility
        23983,  # Another
    ]

    print(f"\n1. Testing potential season IDs...")
    
    found_seasons = {}
    
    for season_id in potential_season_ids:
        try:
            print(f"\n   Testing season_id: {season_id}")
            
            # Try to get fixtures for this season
            result = client._make_request(
                f"fixtures/season/{season_id}",
                {"limit": 1}
            )
            
            if result.get("data"):
                # Get a fixture to check details
                fixture = result["data"][0] if len(result["data"]) > 0 else None
                
                if fixture:
                    season_name = fixture.get("season_id")
                    match_date = fixture.get("starting_at", "")[:10]
                    match_name = fixture.get("name", "Unknown")
                    
                    print(f"     ✓ Valid season! Sample match: {match_name} on {match_date}")
                    
                    # Determine which season this might be
                    year = int(match_date[:4]) if match_date else 0
                    
                    if 2023 <= year <= 2024:
                        found_seasons["2023/24"] = {
                            "season_id": season_id,
                            "sample_match": match_name,
                            "sample_date": match_date
                        }
                    elif 2024 <= year <= 2025:
                        found_seasons["2024/25"] = {
                            "season_id": season_id,
                            "sample_match": match_name,
                            "sample_date": match_date
                        }
        
        except Exception as e:
            print(f"     ✗ Not found or error: {str(e)[:80]}")

    # Alternative: Try getting seasons endpoint with filters
    print(f"\n2. Alternative: Querying seasons with filters...")
    try:
        # Get all seasons and look for league_id = 8 (Premier League)
        seasons_result = client._make_request(
            "seasons",
            {"filters": f"leagueId:{premier_league_id}"}
        )
        
        if seasons_result.get("data"):
            print(f"   ✓ Found {len(seasons_result['data'])} Premier League seasons")
            
            # Look for 2023/24 and 2024/25
            for season in seasons_result["data"]:
                name = season.get("name", "")
                season_id = season.get("id")
                
                if ("2023" in name and "2024" in name) or "2023/2024" in name:
                    print(f"     ✓ 2023/24 season: {name} (ID: {season_id})")
                    found_seasons["2023/24"] = {
                        "season_id": season_id,
                        "name": name
                    }
                
                if ("2024" in name and "2025" in name) or "2024/2025" in name:
                    print(f"     ✓ 2024/25 season: {name} (ID: {season_id})")
                    found_seasons["2024/25"] = {
                        "season_id": season_id,
                        "name": name
                    }
    
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Try one more approach: Get current Liverpool fixtures
    print(f"\n3. Getting Liverpool's current season fixtures...")
    try:
        # Try to get Liverpool's latest fixtures
        result = client._make_request(
            f"teams/{liverpool_id}",
            {"include": "latestfixtures"}
        )
        
        if result.get("data"):
            team = result["data"]
            
            if "latestfixtures" in team:
                fixtures = team["latestfixtures"]
                print(f"   ✓ Found {len(fixtures)} recent fixtures")
                
                for fixture in fixtures[:5]:
                    match_name = fixture.get("name", "Unknown")
                    match_date = fixture.get("starting_at", "")[:10]
                    season_id = fixture.get("season_id")
                    fixture_id = fixture.get("id")
                    
                    print(f"     - {match_date}: {match_name}")
                    print(f"       Fixture ID: {fixture_id}, Season ID: {season_id}")
                    
                    # Add to found seasons
                    year = int(match_date[:4]) if match_date else 0
                    if 2023 <= year <= 2024 and "2023/24" not in found_seasons:
                        found_seasons["2023/24"] = {
                            "season_id": season_id,
                            "sample_fixture_id": fixture_id,
                            "sample_date": match_date
                        }
                    elif 2024 <= year <= 2025 and "2024/25" not in found_seasons:
                        found_seasons["2024/25"] = {
                            "season_id": season_id,
                            "sample_fixture_id": fixture_id,
                            "sample_date": match_date
                        }
    
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Save findings to metadata
    print(f"\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if found_seasons:
        print(f"\n✓ Found {len(found_seasons)} season(s):")
        for season_name, data in found_seasons.items():
            print(f"\n  {season_name}:")
            for key, value in data.items():
                print(f"    {key}: {value}")
        
        # Update metadata file
        metadata_file = Path(__file__).parent.parent / "data" / "metadata.json"
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        metadata["seasons"] = found_seasons
        metadata["premier_league_id"] = premier_league_id
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✓ Metadata updated: {metadata_file}")
    else:
        print("\n⚠ No seasons found. May need to check API documentation or try different approach.")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
