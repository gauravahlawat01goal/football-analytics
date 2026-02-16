"""
Optimized fixture collection with smarter date intervals.

Searches on typical match days (Saturdays, Sundays, Wednesdays, Thursdays)
to reduce API calls while still finding all fixtures.
"""

from datetime import datetime, timedelta
from football_analytics.api_client import SportsMonkClient
from football_analytics.utils import setup_logging, save_json
import time


def get_match_days(start_date: datetime, end_date: datetime):
    """Generate dates that are likely to have matches (weekends + midweek)."""
    dates = []
    current = start_date
    
    while current <= end_date:
        # Premier League typically plays: Sat (5), Sun (6), Wed (2), Thu (3)
        weekday = current.weekday()
        if weekday in [2, 3, 5, 6]:  # Wed, Thu, Sat, Sun
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return dates


def main():
    """Collect Liverpool fixtures using optimized date search."""
    setup_logging(level="INFO", log_file="logs/01_collect_fixtures_optimized.log")
    
    print("=" * 70)
    print("LIVERPOOL FIXTURE COLLECTION (OPTIMIZED)")
    print("=" * 70)
    print()
    print("Strategy: Search on typical match days (Sat, Sun, Wed, Thu)")
    print()
    
    client = SportsMonkClient()
    
    seasons = {
        21646: ("2023-08-01", "2024-05-31"),  # 2023/24
        23614: ("2024-08-01", "2025-05-31"),  # 2024/25
    }
    
    all_fixtures = []
    
    for season_id, (start_str, end_str) in seasons.items():
        season_name = "2023/24" if season_id == 21646 else "2024/25"
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
        
        match_days = get_match_days(start_date, end_date)
        
        print(f"Season {season_name}:")
        print(f"  Searching {len(match_days)} potential match days...")
        print()
        
        found_count = 0
        
        for idx, date_str in enumerate(match_days, 1):
            try:
                # Rate limit
                time.sleep(6)
                
                # Fetch fixtures for this date
                result = client._make_request(
                    f"fixtures/date/{date_str}",
                    params={"include": "participants"}
                )
                
                # Filter for Liverpool
                for fixture in result.get("data", []):
                    participants = fixture.get("participants", [])
                    
                    # Check if Liverpool (team_id=8) is in this match
                    has_liverpool = any(p.get("id") == 8 for p in participants)
                    
                    if has_liverpool:
                        home_team = participants[0].get("name", "Unknown") if participants else "Unknown"
                        away_team = (
                            participants[1].get("name", "Unknown")
                            if len(participants) > 1
                            else "Unknown"
                        )
                        
                        fixture_data = {
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
                        
                        all_fixtures.append(fixture_data)
                        found_count += 1
                        
                        print(f"  ✓ {date_str}: {fixture_data['name']} (ID: {fixture['id']})")
                
                # Progress update every 20 dates
                if idx % 20 == 0:
                    print(f"  Progress: {idx}/{len(match_days)} dates searched, {found_count} fixtures found")
            
            except Exception as e:
                # 404 is expected when no matches on that date
                if "404" not in str(e):
                    print(f"  ✗ {date_str}: {str(e)[:80]}")
        
        print(f"  Season complete: {found_count} fixtures found")
        print()
    
    # Save results
    output_path = "data/raw/fixtures_list.json"
    save_json(all_fixtures, output_path)
    
    print("=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(f"Total fixtures found: {len(all_fixtures)}")
    print(f"Saved to: {output_path}")
    print()
    
    # Summary by season
    by_season = {}
    for f in all_fixtures:
        season_id = f["season_id"]
        by_season.setdefault(season_id, []).append(f)
    
    for season_id in sorted(by_season.keys()):
        season_name = "2023/24" if season_id == 21646 else "2024/25"
        fixtures = by_season[season_id]
        print(f"  {season_name}: {len(fixtures)} fixtures")
        print(f"    First: {fixtures[0]['date'][:10]} - {fixtures[0]['name']}")
        print(f"    Last:  {fixtures[-1]['date'][:10]} - {fixtures[-1]['name']}")
        print()
    
    print("Next step: Run 02_collect_match_data.py")
    print()


if __name__ == "__main__":
    main()
