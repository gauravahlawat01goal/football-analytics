"""
Verify correct Premier League season IDs and their date ranges.
"""

from football_analytics.api_client import SportsMonkClient
from football_analytics.utils import setup_logging
import json

def main():
    """Check available seasons and their details."""
    setup_logging(level="INFO")
    
    print("=" * 70)
    print("PREMIER LEAGUE SEASON VERIFICATION")
    print("=" * 70)
    print()
    
    client = SportsMonkClient()
    
    print("Fetching all seasons...")
    seasons_response = client.get_seasons()
    
    all_seasons = seasons_response.get("data", [])
    print(f"Found {len(all_seasons)} total seasons")
    print()
    
    # Filter for Premier League (league_id = 8)
    premier_league_seasons = [
        s for s in all_seasons 
        if s.get("league_id") == 8
    ]
    
    print(f"Premier League seasons found: {len(premier_league_seasons)}")
    print()
    
    # Show recent seasons (2022 onwards)
    recent_seasons = [
        s for s in premier_league_seasons
        if s.get("name") and "202" in s.get("name", "")
    ]
    
    # Sort by name
    recent_seasons.sort(key=lambda x: x.get("name", ""), reverse=True)
    
    print("Recent Premier League Seasons:")
    print("-" * 70)
    
    for season in recent_seasons[:5]:  # Show last 5 seasons
        season_id = season.get("id")
        season_name = season.get("name")
        start = season.get("starting_at", "Unknown")
        end = season.get("ending_at", "Unknown")
        
        print(f"Season: {season_name}")
        print(f"  ID: {season_id}")
        print(f"  Dates: {start} to {end}")
        print()
    
    print("=" * 70)
    print()
    print("Based on the above, identify which season IDs to use:")
    print("  - 2023/24 (Klopp's final season)")
    print("  - 2024/25 (Slot's first season)")
    print()

if __name__ == "__main__":
    main()
