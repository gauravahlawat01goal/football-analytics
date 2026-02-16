"""Script to fetch Liverpool team ID and season IDs for 2023/24 and 2024/25."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Fetch and display metadata for the tactical analysis project."""
    client = SportsMonkClient()

    print("=" * 80)
    print("FETCHING PROJECT METADATA")
    print("=" * 80)

    # 1. Search for Liverpool
    print("\n1. Searching for Liverpool FC...")
    try:
        liverpool_data = client.search_team("Liverpool")
        
        if liverpool_data.get("data"):
            liverpool = liverpool_data["data"][0]  # First result
            liverpool_id = liverpool["id"]
            liverpool_name = liverpool["name"]
            print(f"   ✓ Found: {liverpool_name} (ID: {liverpool_id})")
        else:
            print("   ✗ Liverpool not found in search results")
            return
    except Exception as e:
        print(f"   ✗ Error searching for Liverpool: {e}")
        return

    # 2. Fetch seasons
    print("\n2. Fetching available seasons...")
    try:
        seasons_data = client.get_seasons()
        
        # Look for 2023/24 and 2024/25 seasons
        seasons_of_interest = {}
        
        if seasons_data.get("data"):
            for season in seasons_data["data"]:
                season_name = season.get("name", "")
                
                if "2023/2024" in season_name or "2023/24" in season_name:
                    seasons_of_interest["2023/24"] = {
                        "id": season["id"],
                        "name": season_name,
                        "start": season.get("starting_at"),
                        "end": season.get("ending_at")
                    }
                
                if "2024/2025" in season_name or "2024/25" in season_name:
                    seasons_of_interest["2024/25"] = {
                        "id": season["id"],
                        "name": season_name,
                        "start": season.get("starting_at"),
                        "end": season.get("ending_at")
                    }
        
        print(f"   ✓ Found {len(seasons_of_interest)} relevant seasons")
        for key, season in seasons_of_interest.items():
            print(f"     - {key}: {season['name']} (ID: {season['id']})")
            print(f"       Period: {season.get('start', 'N/A')} to {season.get('end', 'N/A')}")
    
    except Exception as e:
        print(f"   ✗ Error fetching seasons: {e}")
        seasons_of_interest = {}

    # 3. Save metadata to JSON
    print("\n3. Saving metadata...")
    metadata = {
        "liverpool": {
            "team_id": liverpool_id,
            "team_name": liverpool_name
        },
        "seasons": seasons_of_interest
    }
    
    output_file = Path(__file__).parent.parent / "data" / "metadata.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"   ✓ Metadata saved to: {output_file}")

    # 4. Display summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Liverpool Team ID: {liverpool_id}")
    
    if seasons_of_interest:
        for key, season in seasons_of_interest.items():
            print(f"Season {key} ID: {season['id']}")
    else:
        print("⚠ Warning: Season IDs not found. You may need to search manually.")
    
    print("\n✓ Metadata collection complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
