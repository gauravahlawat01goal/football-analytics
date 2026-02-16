"""Script to test ball coordinate availability for a Liverpool match."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Test fetching ball coordinates for a Liverpool fixture."""
    client = SportsMonkClient()

    print("=" * 80)
    print("TESTING BALL COORDINATE AVAILABILITY")
    print("=" * 80)

    # Use one of the fixture IDs we found: 19253429
    fixture_id = 19253429
    
    print(f"\n1. Fetching fixture {fixture_id} with basic info...")
    try:
        basic_fixture = client.get_fixture_details(fixture_id)
        
        if basic_fixture.get("data"):
            fixture = basic_fixture["data"]
            print(f"   ✓ Fixture found")
            print(f"   Match: {fixture.get('name', 'N/A')}")
            print(f"   Date: {fixture.get('starting_at', 'N/A')}")
            print(f"   Season ID: {fixture.get('season_id', 'N/A')}")
            print(f"   League ID: {fixture.get('league_id', 'N/A')}")
            print(f"   State: {fixture.get('state', {}).get('state', 'N/A')}")
            
            # Save basic info
            output_dir = Path(__file__).parent.parent / "data" / "raw"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_dir / f"fixture_{fixture_id}_basic.json", "w") as f:
                json.dump(basic_fixture, f, indent=2)
            
            print(f"   ✓ Saved to: {output_dir / f'fixture_{fixture_id}_basic.json'}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # Now try with ball coordinates
    print(f"\n2. Fetching fixture {fixture_id} WITH ball coordinates...")
    try:
        full_fixture = client.get_fixture_details(
            fixture_id,
            include="ballCoordinates,events,lineups.detailedPosition,formations,statistics,participants"
        )
        
        if full_fixture.get("data"):
            fixture = full_fixture["data"]
            print(f"   ✓ Full fixture data retrieved")
            
            # Check what's included
            print(f"\n   Included data:")
            print(f"   - ballcoordinates: {'✓' if 'ballcoordinates' in fixture else '✗'}")
            print(f"   - events: {'✓' if 'events' in fixture else '✗'}")
            print(f"   - lineups: {'✓' if 'lineups' in fixture else '✗'}")
            print(f"   - formations: {'✓' if 'formations' in fixture else '✗'}")
            print(f"   - statistics: {'✓' if 'statistics' in fixture else '✗'}")
            print(f"   - participants: {'✓' if 'participants' in fixture else '✗'}")
            
            # If ball coordinates exist, show details
            if 'ballcoordinates' in fixture:
                ball_coords = fixture['ballcoordinates']
                print(f"\n   🎯 BALL COORDINATES AVAILABLE!")
                print(f"   Total data points: {len(ball_coords)}")
                
                if len(ball_coords) > 0:
                    print(f"\n   Sample (first 3 points):")
                    for i, coord in enumerate(ball_coords[:3]):
                        print(f"     {i+1}. X: {coord.get('x')}, Y: {coord.get('y')}, "
                              f"Minute: {coord.get('minute')}, Second: {coord.get('second')}")
            else:
                print(f"\n   ⚠ Ball coordinates NOT available for this match")
                print(f"   This could mean:")
                print(f"   - Match is too old")
                print(f"   - Tracking data not available for this league/season")
                print(f"   - Need to try a more recent match")
            
            # Check events
            if 'events' in fixture:
                events = fixture['events']
                print(f"\n   Events found: {len(events)}")
                if len(events) > 0:
                    print(f"   Sample events (first 3):")
                    for i, event in enumerate(events[:3]):
                        print(f"     {i+1}. Type: {event.get('type', {}).get('name', 'N/A')}, "
                              f"Minute: {event.get('minute')}, Player: {event.get('player', {}).get('display_name', 'N/A')}")
            
            # Save full data
            output_file = output_dir / f"fixture_{fixture_id}_full.json"
            with open(output_file, "w") as f:
                json.dump(full_fixture, f, indent=2)
            
            print(f"\n   ✓ Full data saved to: {output_file}")
            
            # Update metadata with findings
            metadata_file = Path(__file__).parent.parent / "data" / "metadata.json"
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            metadata["test_fixture"] = {
                "fixture_id": fixture_id,
                "season_id": fixture.get("season_id"),
                "has_ball_coordinates": 'ballcoordinates' in fixture,
                "ball_coordinate_count": len(fixture.get('ballcoordinates', [])),
                "has_events": 'events' in fixture,
                "event_count": len(fixture.get('events', []))
            }
            
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"   ✓ Updated metadata")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
