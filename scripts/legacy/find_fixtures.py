"""Script to find Liverpool fixtures and determine season IDs."""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Find Liverpool fixtures to determine available seasons."""
    client = SportsMonkClient()

    print("=" * 80)
    print("FINDING LIVERPOOL FIXTURES")
    print("=" * 80)

    liverpool_id = 8  # From previous script

    # Try different approaches to get fixtures
    print("\n1. Attempting to fetch recent Liverpool fixtures...")
    
    # Try using the team endpoint with includes
    try:
        # Get team details with current season info
        print("\n   Trying: teams/{id} with includes...")
        team_data = client._make_request(
            f"teams/{liverpool_id}",
            {"include": "activeSeasons"}
        )
        
        if team_data.get("data"):
            print(f"   ✓ Team data retrieved")
            
            # Check if activeSeasons is included
            team = team_data["data"]
            if "activeseasons" in team:
                print(f"\n   Active seasons found: {len(team['activeseasons'])}")
                for season in team["activeseasons"]:
                    print(f"     - Season ID: {season.get('id')}, Name: {season.get('name')}")
            else:
                print("   Note: activeSeasons not in response")
                print(f"   Available keys: {list(team.keys())}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Try to get all fixtures for Liverpool (may be rate limited)
    print("\n2. Trying to fetch Liverpool fixtures directly...")
    try:
        # Sportsmonks API structure: fixtures/teams/{team_id}
        fixtures_data = client._make_request(
            f"fixtures",
            {"filter": f"teamId:{liverpool_id}"}
        )
        
        if fixtures_data.get("data"):
            print(f"   ✓ Found {len(fixtures_data['data'])} fixtures")
            
            # Analyze seasons from fixtures
            seasons_seen = {}
            for fixture in fixtures_data["data"][:50]:  # First 50
                season_id = fixture.get("season_id")
                league_id = fixture.get("league_id")
                date = fixture.get("starting_at", "")[:10]
                
                if season_id not in seasons_seen:
                    seasons_seen[season_id] = {
                        "season_id": season_id,
                        "league_id": league_id,
                        "first_match": date,
                        "count": 0
                    }
                seasons_seen[season_id]["count"] += 1
            
            print(f"\n   Seasons found in fixtures:")
            for season_id, info in sorted(seasons_seen.items()):
                print(f"     - Season {season_id}: {info['count']} matches, starting {info['first_match']}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Try searching for a specific recent match
    print("\n3. Trying to search for recent Liverpool match...")
    try:
        # Search for fixtures with Liverpool, sorted by date
        fixtures_data = client._make_request(
            "fixtures/search/Liverpool"
        )
        
        if fixtures_data.get("data"):
            print(f"   ✓ Found {len(fixtures_data['data'])} matches")
            
            # Show first 10 recent matches
            print("\n   Recent matches:")
            for fixture in fixtures_data["data"][:10]:
                home = fixture.get("participants", [{}])[0].get("name", "Unknown") if fixture.get("participants") else "Unknown"
                away = fixture.get("participants", [{}])[1].get("name", "Unknown") if len(fixture.get("participants", [])) > 1 else "Unknown"
                date = fixture.get("starting_at", "N/A")[:10]
                season_id = fixture.get("season_id")
                fixture_id = fixture.get("id")
                
                print(f"     {date}: {home} vs {away} (Fixture ID: {fixture_id}, Season: {season_id})")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
