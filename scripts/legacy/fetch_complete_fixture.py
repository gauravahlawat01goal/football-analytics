"""Fetch complete fixture data with ball coordinates (requesting each include separately)."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def fetch_complete_fixture(client, fixture_id, output_dir):
    """Fetch all data for a fixture by requesting includes separately."""
    
    print(f"\nFetching fixture {fixture_id}...")
    
    fixture_data = {}
    
    # List of includes to fetch separately
    includes = ["events", "lineups", "formations", "statistics", "participants", "scores", "ballCoordinates"]
    
    # Start with basic data
    try:
        result = client._make_request(f"fixtures/{fixture_id}")
        fixture_data = result["data"]
        print(f"   ✓ Basic data fetched")
    except Exception as e:
        print(f"   ✗ Error fetching basic data: {e}")
        return None
    
    # Fetch each include separately
    for include in includes:
        try:
            result = client._make_request(
                f"fixtures/{fixture_id}",
                {"include": include}
            )
            
            if result.get("data"):
                fixture = result["data"]
                include_lower = include.lower()
                
                if include_lower in fixture:
                    fixture_data[include_lower] = fixture[include_lower]
                    
                    data_count = len(fixture[include_lower]) if isinstance(fixture[include_lower], list) else "N/A"
                    print(f"   ✓ {include}: {data_count} items")
        
        except Exception as e:
            print(f"   ✗ {include}: {str(e)[:60]}")
    
    return fixture_data


def main():
    """Fetch complete data for a sample Liverpool fixture."""
    client = SportsMonkClient()
    
    print("=" * 80)
    print("FETCHING COMPLETE FIXTURE DATA WITH BALL COORDINATES")
    print("=" * 80)
    
    # Use the fixture we know works
    fixture_id = 19134454  # Ipswich vs Liverpool, 2024-08-17
    
    # Setup output directory
    output_dir = Path(__file__).parent.parent / "data" / "raw" / "ball_coordinates"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch complete data
    fixture_data = fetch_complete_fixture(client, fixture_id, output_dir)
    
    if not fixture_data:
        print("\n✗ Failed to fetch fixture data")
        return
    
    # Analyze ball coordinates
    print(f"\n{'='*80}")
    print("BALL COORDINATE ANALYSIS")
    print(f"{'='*80}")
    
    if "ballcoordinates" in fixture_data:
        ball_coords = fixture_data["ballcoordinates"]
        
        print(f"\n✓ Ball coordinates available!")
        print(f"   Total data points: {len(ball_coords)}")
        
        if len(ball_coords) > 0:
            # Sample data
            print(f"\n   Sample (first 10 points):")
            for i, coord in enumerate(ball_coords[:10]):
                x_val = float(coord.get('x', 0))
                y_val = float(coord.get('y', 0))
                minute = coord.get('minute', 0)
                second = coord.get('second', 0)
                print(f"   {i+1:2d}. X={x_val:6.3f}, Y={y_val:6.3f}, "
                      f"Min={minute}:{second:02d}")
            
            # Statistics
            x_coords = [float(c.get('x', 0)) for c in ball_coords if c.get('x')]
            y_coords = [float(c.get('y', 0)) for c in ball_coords if c.get('y')]
            
            print(f"\n   Coordinate ranges:")
            print(f"   X: {min(x_coords):.3f} to {max(x_coords):.3f}")
            print(f"   Y: {min(y_coords):.3f} to {max(y_coords):.3f}")
            
            # Coverage by minute
            minutes = [c.get('minute') for c in ball_coords if c.get('minute') is not None]
            unique_minutes = len(set(minutes))
            
            print(f"\n   Coverage:")
            print(f"   Minutes tracked: {unique_minutes}")
            if unique_minutes > 0:
                print(f"   Average points per minute: {len(ball_coords)/unique_minutes:.1f}")
            else:
                print(f"   Note: Minute data not populated in coordinates")
    
    # Analyze events
    if "events" in fixture_data:
        events = fixture_data["events"]
        
        print(f"\n{'='*80}")
        print("EVENT ANALYSIS")
        print(f"{'='*80}")
        
        print(f"\n   Total events: {len(events)}")
        
        # Sample events
        print(f"\n   Sample events (first 10):")
        for i, event in enumerate(events[:10]):
            event_type = event.get("type", {}).get("name", "Unknown")
            minute = event.get("minute", "?")
            player_name = event.get("player", {}).get("display_name", "Unknown")
            team = event.get("participant", {}).get("name", "Unknown")
            
            print(f"   {i+1:2d}. Min {minute:2}: {event_type:20s} - {player_name:25s} ({team})")
    
    # Analyze lineups
    if "lineups" in fixture_data:
        lineups = fixture_data["lineups"]
        
        print(f"\n{'='*80}")
        print("LINEUP ANALYSIS")
        print(f"{'='*80}")
        
        for lineup in lineups:
            team_name = lineup.get("participant", {}).get("name", "Unknown")
            formation = lineup.get("formation", "Unknown")
            player_id = lineup.get("player_id")
            position = lineup.get("detailedPosition", {}).get("name", "Unknown") if lineup.get("detailedPosition") else "Unknown"
            player_name = lineup.get("player", {}).get("display_name", "Unknown") if lineup.get("player") else "Unknown"
            
            print(f"   {team_name:20s}: {player_name:20s} - {position}")
    
    # Save complete data
    output_file = output_dir / f"fixture_{fixture_id}_complete.json"
    with open(output_file, "w") as f:
        json.dump(fixture_data, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✓ Complete data saved to: {output_file.name}")
    print(f"   File size: {output_file.stat().st_size / 1024:.1f} KB")
    print("=" * 80)


if __name__ == "__main__":
    main()
