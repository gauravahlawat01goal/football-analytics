"""Script to explore and find Premier League season IDs."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Explore seasons to find Premier League 2023/24 and 2024/25."""
    client = SportsMonkClient()

    print("=" * 80)
    print("EXPLORING SEASONS")
    print("=" * 80)

    # First, let's get the Premier League ID
    print("\n1. Getting Premier League info...")
    try:
        leagues_data = client.get_leagues()
        
        premier_league = None
        if leagues_data.get("data"):
            for league in leagues_data["data"]:
                if "Premier League" in league.get("name", "") and league.get("name") == "Premier League":
                    premier_league = league
                    print(f"   ✓ Found: {league['name']} (ID: {league['id']})")
                    break
        
        if not premier_league:
            print("   ✗ Premier League not found")
            # Try to print first few leagues for debugging
            print("\n   Available leagues (first 10):")
            for i, league in enumerate(leagues_data.get("data", [])[:10]):
                print(f"     {i+1}. {league.get('name')} (ID: {league['id']})")
            return
    
    except Exception as e:
        print(f"   ✗ Error fetching leagues: {e}")
        return

    # Now get seasons data with more detail
    print("\n2. Fetching all seasons...")
    try:
        seasons_data = client.get_seasons()
        
        print(f"   Total seasons found: {len(seasons_data.get('data', []))}")
        
        # Look for recent seasons (2023-2025)
        recent_seasons = []
        for season in seasons_data.get("data", []):
            name = season.get("name", "")
            year = season.get("starting_at", "")[:4] if season.get("starting_at") else ""
            
            if year in ["2023", "2024", "2025"]:
                recent_seasons.append({
                    "id": season["id"],
                    "name": name,
                    "start": season.get("starting_at"),
                    "end": season.get("ending_at"),
                    "league_id": season.get("league_id")
                })
        
        print(f"\n   Recent seasons (2023-2025): {len(recent_seasons)}")
        
        # Filter for Premier League seasons
        pl_recent = [s for s in recent_seasons if s["league_id"] == premier_league["id"]]
        
        print(f"\n   Premier League recent seasons: {len(pl_recent)}")
        for season in pl_recent:
            print(f"     - {season['name']} (ID: {season['id']})")
            print(f"       Period: {season['start']} to {season['end']}")
        
        # Update metadata
        metadata_file = Path(__file__).parent.parent / "data" / "metadata.json"
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        # Add season info
        metadata["premier_league_id"] = premier_league["id"]
        metadata["seasons"] = {}
        
        for season in pl_recent:
            name = season["name"]
            if "2023" in name:
                metadata["seasons"]["2023/24"] = {
                    "id": season["id"],
                    "name": name,
                    "start": season["start"],
                    "end": season["end"]
                }
            elif "2024" in name:
                metadata["seasons"]["2024/25"] = {
                    "id": season["id"],
                    "name": name,
                    "start": season["start"],
                    "end": season["end"]
                }
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n   ✓ Updated metadata file: {metadata_file}")
    
    except Exception as e:
        print(f"   ✗ Error fetching seasons: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
