"""Script to find the 2025-2026 Premier League season ID."""

import json
import sys
from pathlib import Path
from datetime import datetime

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

    # Premier League ID is 8
    premier_league_id = 8
    liverpool_id = 8

    # Known season IDs for reference
    known_seasons = {
        "2023-24": 21646,
        "2024-25": 23614,
    }

    print("Known Seasons:")
    for season, sid in known_seasons.items():
        print(f"  {season}: {sid}")
    print()

    # Strategy 1: Query seasons endpoint with filter
    print("=" * 80)
    print("STRATEGY 1: Query seasons endpoint")
    print("=" * 80)
    
    found_2025_26 = None
    
    try:
        result = client._make_request(
            "seasons",
            {
                "filters": f"leagueId:{premier_league_id}",
                "per_page": 100
            }
        )
        
        if result.get("data"):
            print(f"✓ Found {len(result['data'])} Premier League seasons\n")
            
            # Sort by ID (newer seasons have higher IDs)
            seasons = sorted(result["data"], key=lambda x: x.get("id", 0), reverse=True)
            
            print("Recent seasons:")
            for season in seasons[:10]:  # Show top 10 most recent
                season_id = season.get("id")
                name = season.get("name", "Unknown")
                is_current = season.get("is_current", False)
                starting_at = season.get("starting_at", "")[:10]
                ending_at = season.get("ending_at", "")[:10]
                
                print(f"  ID {season_id}: {name}")
                print(f"    Period: {starting_at} to {ending_at}")
                print(f"    Current: {is_current}")
                
                # Check if this is 2025-26
                if ("2025" in name and "2026" in name) or "2025/2026" in name:
                    print(f"    >>> THIS IS 2025-2026! <<<")
                    found_2025_26 = {
                        "season_id": season_id,
                        "name": name,
                        "starting_at": starting_at,
                        "ending_at": ending_at,
                        "is_current": is_current
                    }
                
                print()
    
    except Exception as e:
        print(f"✗ Error querying seasons endpoint: {e}\n")

    # Strategy 2: Get Liverpool's most recent fixtures
    print("=" * 80)
    print("STRATEGY 2: Check Liverpool's recent fixtures")
    print("=" * 80)
    
    try:
        # Get fixtures with latest first
        result = client._make_request(
            f"fixtures",
            {
                "filters": f"localTeamId:{liverpool_id},leagueId:{premier_league_id}",
                "order": "starting_at:desc",
                "per_page": 20
            }
        )
        
        if result.get("data"):
            fixtures = result["data"]
            print(f"✓ Found {len(fixtures)} recent Liverpool fixtures\n")
            
            # Group by season_id
            season_fixtures = {}
            for fixture in fixtures:
                season_id = fixture.get("season_id")
                match_date = fixture.get("starting_at", "")[:10]
                match_name = fixture.get("name", "Unknown")
                
                if season_id not in season_fixtures:
                    season_fixtures[season_id] = []
                
                season_fixtures[season_id].append({
                    "date": match_date,
                    "name": match_name
                })
            
            # Show fixtures grouped by season
            print("Fixtures by season:")
            for season_id, fixtures_list in sorted(season_fixtures.items(), reverse=True):
                print(f"\n  Season ID {season_id}:")
                
                # Show date range
                dates = [f["date"] for f in fixtures_list if f["date"]]
                if dates:
                    print(f"    Date range: {min(dates)} to {max(dates)}")
                    print(f"    Fixtures: {len(fixtures_list)}")
                    
                    # Check if this looks like 2025-26
                    years = set(int(d[:4]) for d in dates if d)
                    if 2025 in years or 2026 in years:
                        print(f"    >>> LIKELY 2025-2026 SEASON! <<<")
                        if not found_2025_26:
                            found_2025_26 = {
                                "season_id": season_id,
                                "date_range": f"{min(dates)} to {max(dates)}",
                                "fixture_count": len(fixtures_list)
                            }
                    
                    # Show first 3 fixtures
                    print(f"    Sample fixtures:")
                    for fixture in fixtures_list[:3]:
                        print(f"      - {fixture['date']}: {fixture['name']}")
    
    except Exception as e:
        print(f"✗ Error querying fixtures: {e}\n")

    # Strategy 3: Try common ID patterns
    print("=" * 80)
    print("STRATEGY 3: Try likely season ID patterns")
    print("=" * 80)
    
    # Based on the pattern:
    # 2023-24: 21646
    # 2024-25: 23614
    # The increment is ~1968, so 2025-26 might be around 25582
    
    likely_ids = [
        25582,  # Based on pattern (+1968)
        25600,  # Round number nearby
        23615,  # Sequential from 23614
        25500,  # Another possibility
        26000,  # Round number
    ]
    
    print(f"Testing likely IDs based on pattern analysis:")
    print(f"  Pattern: 21646 (2023-24) → 23614 (2024-25) → ~25582? (2025-26)\n")
    
    for test_id in likely_ids:
        try:
            print(f"  Testing {test_id}...", end=" ")
            
            result = client._make_request(
                f"fixtures/season/{test_id}",
                {"limit": 1}
            )
            
            if result.get("data") and len(result["data"]) > 0:
                fixture = result["data"][0]
                match_date = fixture.get("starting_at", "")[:10]
                match_name = fixture.get("name", "Unknown")
                
                print(f"✓ Valid!")
                print(f"    Sample: {match_name} on {match_date}")
                
                # Check year
                year = int(match_date[:4]) if match_date else 0
                if year >= 2025:
                    print(f"    >>> LIKELY 2025-2026! <<<")
                    if not found_2025_26:
                        found_2025_26 = {
                            "season_id": test_id,
                            "sample_match": match_name,
                            "sample_date": match_date
                        }
            else:
                print("✗ No data")
        
        except Exception as e:
            print(f"✗ Error")

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
        print("\nPossible reasons:")
        print("  1. Season may not be available in API yet")
        print("  2. Different league/competition structure")
        print("  3. Season uses different naming convention")
        print("\nRecommendation:")
        print("  - Check Sportsmonks API documentation")
        print("  - Contact Sportsmonks support")
        print("  - Verify subscription includes current season")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
