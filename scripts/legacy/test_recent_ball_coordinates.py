"""Test ball coordinate availability for recent Liverpool fixtures."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def test_fixture(client, fixture_id, fixture_name, output_dir):
    """Test a single fixture for ball coordinate availability."""
    
    print(f"\n{'='*70}")
    print(f"Testing: {fixture_name}")
    print(f"Fixture ID: {fixture_id}")
    print(f"{'='*70}")
    
    try:
        # Fetch with all includes
        result = client.get_fixture_details(
            fixture_id,
            include="ballCoordinates,events,lineups,formations,statistics,participants"
        )
        
        if not result.get("data"):
            print("   ✗ No data returned")
            return False
        
        fixture = result["data"]
        
        # Check what data is available
        print("\n📊 Data availability:")
        
        has_ball_coords = "ballcoordinates" in fixture
        has_events = "events" in fixture
        has_lineups = "lineups" in fixture
        has_formations = "formations" in fixture
        has_statistics = "statistics" in fixture
        
        print(f"   Ball Coordinates: {'✓ YES' if has_ball_coords else '✗ NO'}")
        print(f"   Events:           {'✓ YES' if has_events else '✗ NO'}")
        print(f"   Lineups:          {'✓ YES' if has_lineups else '✗ NO'}")
        print(f"   Formations:       {'✓ YES' if has_formations else '✗ NO'}")
        print(f"   Statistics:       {'✓ YES' if has_statistics else '✗ NO'}")
        
        # Detailed analysis of ball coordinates
        if has_ball_coords:
            ball_coords = fixture["ballcoordinates"]
            coord_count = len(ball_coords)
            
            print(f"\n⚽ BALL COORDINATES DETAILS:")
            print(f"   Total points: {coord_count}")
            
            if coord_count > 0:
                print(f"\n   Sample data (first 5 points):")
                for i, coord in enumerate(ball_coords[:5]):
                    print(f"   {i+1}. X={coord.get('x'):.3f}, Y={coord.get('y'):.3f}, "
                          f"Min={coord.get('minute')}, Sec={coord.get('second')}")
                
                # Calculate coverage
                minutes_covered = len(set(c.get('minute') for c in ball_coords if c.get('minute')))
                print(f"\n   Coverage: {minutes_covered} minutes")
                print(f"   Density: ~{coord_count/90:.1f} points per minute")
        
        # Event analysis
        if has_events:
            events = fixture["events"]
            print(f"\n⚽ EVENTS: {len(events)} total")
            
            # Count event types
            event_types = {}
            for event in events:
                event_type = event.get("type", {}).get("name", "Unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            print(f"   Event type breakdown:")
            for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"     - {event_type}: {count}")
        
        # Lineups analysis
        if has_lineups:
            lineups = fixture["lineups"]
            print(f"\n👥 LINEUPS: {len(lineups)} teams")
            
            for lineup in lineups:
                team_name = lineup.get("participant", {}).get("name", "Unknown")
                formation = lineup.get("formation", "Unknown")
                players = lineup.get("detailedposition", [])
                
                print(f"   {team_name}: {formation} formation, {len(players)} players")
        
        # Save detailed data
        output_file = output_dir / f"fixture_{fixture_id}_detailed.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Saved to: {output_file.name}")
        
        return has_ball_coords
    
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test ball coordinate availability for recent Liverpool fixtures."""
    client = SportsMonkClient()
    
    print("=" * 80)
    print("TESTING BALL COORDINATE AVAILABILITY FOR LIVERPOOL FIXTURES")
    print("=" * 80)
    
    # Load fixtures from metadata
    metadata_file = Path(__file__).parent.parent / "data" / "metadata.json"
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    # Setup output directory
    output_dir = Path(__file__).parent.parent / "data" / "raw" / "test_fixtures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test fixtures from both seasons
    results = {}
    
    for season_name, fixtures in metadata.get("sample_fixtures", {}).items():
        print(f"\n\n{'#'*80}")
        print(f"# SEASON: {season_name}")
        print(f"{'#'*80}")
        
        season_results = []
        
        # Test up to 2 fixtures per season
        for fixture in fixtures[:2]:
            fixture_id = fixture["fixture_id"]
            fixture_name = fixture["name"]
            
            has_coords = test_fixture(client, fixture_id, fixture_name, output_dir)
            season_results.append({
                "fixture_id": fixture_id,
                "name": fixture_name,
                "has_ball_coordinates": has_coords
            })
        
        results[season_name] = season_results
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    for season_name, season_results in results.items():
        coord_count = sum(1 for r in season_results if r["has_ball_coordinates"])
        total = len(season_results)
        
        print(f"\n{season_name}:")
        print(f"   Tested: {total} fixtures")
        print(f"   With ball coordinates: {coord_count}/{total}")
        
        for result in season_results:
            status = "✓" if result["has_ball_coordinates"] else "✗"
            print(f"   {status} {result['name']} (ID: {result['fixture_id']})")
    
    # Update metadata
    metadata["ball_coordinate_test_results"] = results
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Results saved to metadata")
    print("=" * 80)


if __name__ == "__main__":
    main()
