"""Simple test to check what data is actually available with our API subscription."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.api_client import SportsMonkClient


def main():
    """Check what data is available for a Liverpool fixture."""
    client = SportsMonkClient()
    
    print("=" * 80)
    print("API SUBSCRIPTION & DATA AVAILABILITY TEST")
    print("=" * 80)
    
    # Try the most recent fixture we found
    fixture_id = 19134454  # Ipswich vs Liverpool, 2024-08-17
    
    print(f"\nFixture ID: {fixture_id}")
    print(f"Match: Ipswich Town vs Liverpool (2024-08-17)")
    
    # Test 1: Basic fixture data (no includes)
    print("\n1. Testing basic fixture data (no includes)...")
    try:
        result = client._make_request(f"fixtures/{fixture_id}")
        print("   ✓ Success!")
        
        if result.get("data"):
            fixture = result["data"]
            print(f"\n   Available keys in fixture data:")
            for key in sorted(fixture.keys()):
                print(f"     - {key}")
            
            # Save it
            output_dir = Path(__file__).parent.parent / "data" / "raw"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_dir / f"fixture_{fixture_id}_basic.json", "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"\n   ✓ Saved to: fixture_{fixture_id}_basic.json")
    
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Test 2: Try each include separately
    print("\n2. Testing individual includes...")
    
    includes_to_test = [
        "events",
        "lineups",
        "formations",
        "statistics",
        "participants",
        "scores",
        "ballCoordinates",
        "ballcoordinates",  # Try lowercase
    ]
    
    working_includes = []
    
    for include in includes_to_test:
        try:
            result = client._make_request(
                f"fixtures/{fixture_id}",
                {"include": include}
            )
            
            if result.get("data"):
                fixture = result["data"]
                
                # Check if the include is actually in the response
                include_lower = include.lower()
                has_data = include_lower in fixture
                
                if has_data:
                    data = fixture[include_lower]
                    data_size = len(data) if isinstance(data, (list, dict)) else "N/A"
                    print(f"   ✓ {include}: Available ({data_size} items)")
                    working_includes.append(include)
                else:
                    print(f"   ⚠ {include}: Requested but not in response")
        
        except Exception as e:
            error_msg = str(e)[:80]
            print(f"   ✗ {include}: {error_msg}")
    
    # Test 3: Check subscription details
    print("\n3. Checking API subscription details...")
    try:
        # The subscription info is usually in the response
        result = client._make_request(f"fixtures/{fixture_id}")
        
        if "subscription" in result:
            subscription = result["subscription"][0]
            
            print(f"\n   Subscription info:")
            
            if "plans" in subscription:
                for plan in subscription["plans"]:
                    print(f"   📦 Plan: {plan.get('plan', 'N/A')}")
                    print(f"      Sport: {plan.get('sport', 'N/A')}")
                    print(f"      Category: {plan.get('category', 'N/A')}")
            
            if "add_ons" in subscription:
                print(f"\n   Add-ons:")
                for addon in subscription["add_ons"]:
                    print(f"   + {addon.get('add_on', 'N/A')}")
                    print(f"     Category: {addon.get('category', 'N/A')}")
            
            if "meta" in subscription:
                meta = subscription["meta"]
                print(f"\n   Trial ends: {meta.get('trial_ends_at', 'N/A')}")
                print(f"   Subscription ends: {meta.get('ends_at', 'N/A')}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if working_includes:
        print(f"\n✓ Working includes ({len(working_includes)}):")
        for inc in working_includes:
            print(f"  - {inc}")
    else:
        print("\n⚠ No includes working - basic data only available")
    
    if "ballCoordinates" not in working_includes and "ballcoordinates" not in working_includes:
        print("\n⚠ CRITICAL: Ball coordinates NOT available with current subscription")
        print("   This means we'll need to use alternative approaches:")
        print("   - Event-based positioning (events with locations)")
        print("   - Statistical analysis (touches by zone, etc.)")
        print("   - Formation-based analysis")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
