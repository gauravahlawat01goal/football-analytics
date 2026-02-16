"""
Quick fixture collection using team fixtures endpoint.

This is much faster than date-by-date search.
"""

from football_analytics.api_client import SportsMonkClient
from football_analytics.utils import setup_logging, save_json

def main():
    """Collect Liverpool fixtures using team fixtures endpoint."""
    setup_logging(level="INFO", log_file="logs/collect_fixtures_quick.log")
    
    print("=" * 70)
    print("LIVERPOOL FIXTURE COLLECTION (QUICK METHOD)")
    print("=" * 70)
    print()
    
    client = SportsMonkClient()
    
    print("Fetching fixtures for Liverpool (team_id=8)...")
    print()
    
    all_fixtures = []
    
    for season_id in [21646, 23614]:
        season_name = "2023/24" if season_id == 21646 else "2024/25"
        print(f"Fetching {season_name} (season ID: {season_id})...")
        
        try:
            # Use the proper method
            response = client.get_team_fixtures(
                team_id=8,
                season_id=season_id,
                include="participants"
            )
            
            fixtures = response.get("data", [])
            print(f"  ✓ Found {len(fixtures)} fixtures")
            
            # Extract metadata
            for fixture in fixtures:
                participants = fixture.get("participants", [])
                home_team = participants[0].get("name", "Unknown") if participants else "Unknown"
                away_team = (
                    participants[1].get("name", "Unknown") if len(participants) > 1 else "Unknown"
                )
                
                all_fixtures.append(
                    {
                        "fixture_id": fixture["id"],
                        "season_id": fixture.get("season_id"),
                        "league_id": fixture.get("league_id"),
                        "date": fixture.get("starting_at"),
                        "name": f"{home_team} vs {away_team}",
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_team_id": participants[0].get("id") if participants else None,
                        "away_team_id": (
                            participants[1].get("id") if len(participants) > 1 else None
                        ),
                    }
                )
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Save
    output_path = "data/raw/fixtures_list.json"
    save_json(all_fixtures, output_path)
    
    print()
    print("=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(f"Total fixtures: {len(all_fixtures)}")
    print(f"Saved to: {output_path}")
    print()
    
    # Summary by season
    by_season = {}
    for f in all_fixtures:
        season_id = f["season_id"]
        by_season.setdefault(season_id, []).append(f)
    
    for season_id in sorted(by_season.keys()):
        season_name = "2023/24" if season_id == 21646 else "2024/25"
        print(f"  {season_name}: {len(by_season[season_id])} fixtures")
        # Show first 3
        for fixture in by_season[season_id][:3]:
            print(f"    - {fixture['date'][:10]}: {fixture['name']}")
    
    print()
    print("Next step: Run 02_collect_match_data.py")
    print()


if __name__ == "__main__":
    main()
