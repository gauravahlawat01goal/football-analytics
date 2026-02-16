"""Script to find Liverpool fixtures from 2024-2025 seasons (corrected for system date)."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Find Liverpool fixtures from actual 2023/24 and 2024/25 seasons."""
    client = SportsMonkClient()

    print("=" * 80)
    print("FINDING LIVERPOOL FIXTURES (2023/24 & 2024/25 SEASONS)")
    print("=" * 80)

    liverpool_id = 8

    # Key dates from the actual seasons
    test_dates = [
        # 2024/25 season dates
        "2024-08-17",  # Opening weekend 2024/25
        "2024-09-01",
        "2024-10-01",
        "2024-11-01",
        "2024-12-01",
        "2025-01-01",
        # 2023/24 season dates
        "2023-08-13",  # Opening weekend 2023/24
        "2023-09-01",
        "2023-12-01",
        "2024-02-01",
        "2024-05-01",
    ]

    found_fixtures = []
    season_ids = set()

    print("\nSearching for Liverpool fixtures...")
    
    for date in test_dates:
        try:
            result = client._make_request(f"fixtures/date/{date}", {"include": "participants"})
            
            if result.get("data"):
                fixtures = result["data"]
                
                # Filter for Liverpool (team_id = 8)
                for fixture in fixtures:
                    participants = fixture.get("participants", [])
                    
                    # Check if Liverpool is in this match
                    has_liverpool = any(
                        p.get("id") == liverpool_id 
                        for p in participants
                    )
                    
                    if has_liverpool:
                        fixture_id = fixture.get("id")
                        season_id = fixture.get("season_id")
                        league_id = fixture.get("league_id")
                        
                        # Get team names
                        home_team = participants[0].get("name", "Unknown") if len(participants) > 0 else "Unknown"
                        away_team = participants[1].get("name", "Unknown") if len(participants) > 1 else "Unknown"
                        match_name = f"{home_team} vs {away_team}"
                        
                        print(f"   ✓ {date}: {match_name}")
                        print(f"     Fixture ID: {fixture_id}, Season ID: {season_id}, League: {league_id}")
                        
                        found_fixtures.append({
                            "fixture_id": fixture_id,
                            "season_id": season_id,
                            "league_id": league_id,
                            "date": date,
                            "name": match_name
                        })
                        
                        season_ids.add(season_id)
        
        except Exception as e:
            error_msg = str(e)[:100]
            # Don't print errors for dates with no matches
            if "404" not in str(e):
                print(f"   ✗ {date}: {error_msg}")

    # Analyze what we found
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if found_fixtures:
        print(f"\n✓ Found {len(found_fixtures)} Liverpool fixtures")
        print(f"✓ Unique season IDs: {sorted(season_ids)}")
        
        # Group by season
        fixtures_by_season = {}
        for fixture in found_fixtures:
            season_id = fixture["season_id"]
            if season_id not in fixtures_by_season:
                fixtures_by_season[season_id] = []
            fixtures_by_season[season_id].append(fixture)
        
        print(f"\nFixtures by season:")
        for season_id in sorted(fixtures_by_season.keys()):
            fixtures = fixtures_by_season[season_id]
            print(f"\n  Season ID {season_id}:")
            print(f"    {len(fixtures)} fixtures found")
            print(f"    Date range: {fixtures[0]['date']} to {fixtures[-1]['date']}")
            print(f"    Sample: {fixtures[0]['name']}")
            print(f"    Fixture IDs: {[f['fixture_id'] for f in fixtures[:3]]}...")
        
        # Save to metadata
        metadata_file = Path(__file__).parent.parent / "data" / "metadata.json"
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        # Determine which season is which based on dates
        metadata["seasons"] = {}
        metadata["sample_fixtures"] = {}
        
        for season_id, fixtures in fixtures_by_season.items():
            # Check date range to determine season
            first_date = fixtures[0]["date"]
            year = int(first_date[:4])
            
            if year == 2023:
                season_name = "2023/24"
            elif year == 2024:
                month = int(first_date[5:7])
                if month >= 8:  # August or later = new season
                    season_name = "2024/25"
                else:
                    season_name = "2023/24"
            else:
                season_name = f"season_{season_id}"
            
            metadata["seasons"][season_name] = {
                "season_id": season_id,
                "fixture_count": len(fixtures),
                "date_range": f"{fixtures[0]['date']} to {fixtures[-1]['date']}"
            }
            
            metadata["sample_fixtures"][season_name] = [
                {
                    "fixture_id": f["fixture_id"],
                    "date": f["date"],
                    "name": f["name"]
                }
                for f in fixtures[:5]  # Save first 5
            ]
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✓ Metadata updated: {metadata_file}")
    
    else:
        print("\n⚠ No Liverpool fixtures found. API may have limitations on historical data access.")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
