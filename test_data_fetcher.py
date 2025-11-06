#!/usr/bin/env python3
"""
End-to-end test of the data fetcher system
"""

import os
import sys
import json

def test_data_fetcher():
    """Test the data fetcher functionality"""
    print("\n" + "="*70)
    print("DATA FETCHER END-TO-END TEST")
    print("="*70)
    
    # Ensure we're in development mode
    os.environ['FLASK_ENV'] = 'development'
    
    from utils.data_fetcher import get_data_fetcher
    from pathlib import Path
    
    fetcher = get_data_fetcher()
    
    # Test 1: Mock data file exists
    print("\n[Test 1] Checking mock data file...")
    assert fetcher.MOCK_DATA_FILE.exists(), "Mock data file should exist"
    print("✓ Mock data file exists at:", fetcher.MOCK_DATA_FILE)
    
    # Test 2: Fetch bills
    print("\n[Test 2] Fetching bills...")
    bills = fetcher.fetch_bills()
    assert isinstance(bills, list), "Bills should be a list"
    assert len(bills) > 0, "Should have at least one bill"
    assert 'number' in bills[0], "Bill should have 'number' field"
    assert 'title' in bills[0], "Bill should have 'title' field"
    assert 'sponsor' in bills[0], "Bill should have 'sponsor' field"
    print(f"✓ Fetched {len(bills)} bills")
    print(f"  First bill: {bills[0]['number']} - {bills[0]['title'][:50]}...")
    
    # Test 3: Fetch representatives (Jefferson City)
    print("\n[Test 3] Fetching representatives for Jefferson City...")
    address_jc = {'street': '201 W Capitol Ave', 'city': 'Jefferson City', 'state': 'MO', 'zip': '65101'}
    reps_jc = fetcher.fetch_representatives(address_jc)
    assert 'senator' in reps_jc, "Should have senator info"
    assert 'representative' in reps_jc, "Should have representative info"
    assert 'name' in reps_jc['senator'], "Senator should have name"
    assert 'name' in reps_jc['representative'], "Representative should have name"
    print(f"✓ Senator: {reps_jc['senator']['name']}")
    print(f"✓ Representative: {reps_jc['representative']['name']}")
    
    # Test 4: Fetch representatives (St. Louis)
    print("\n[Test 4] Fetching representatives for St. Louis...")
    address_stl = {'street': '123 Main St', 'city': 'St. Louis', 'state': 'MO', 'zip': '63101'}
    reps_stl = fetcher.fetch_representatives(address_stl)
    assert reps_stl['senator']['name'] != reps_jc['senator']['name'], "Different cities should have different reps"
    print(f"✓ Senator: {reps_stl['senator']['name']}")
    print(f"✓ Representative: {reps_stl['representative']['name']}")
    
    # Test 5: Unknown zip code fallback
    print("\n[Test 5] Testing fallback for unknown zip code...")
    address_unknown = {'street': '999 Unknown St', 'city': 'Unknown', 'state': 'MO', 'zip': '99999'}
    reps_unknown = fetcher.fetch_representatives(address_unknown)
    assert reps_unknown is not None, "Should return fallback data"
    print(f"✓ Fallback works: {reps_unknown['senator']['name']}")
    
    # Test 6: Mock data structure
    print("\n[Test 6] Validating mock data structure...")
    with open(fetcher.MOCK_DATA_FILE, 'r') as f:
        mock_data = json.load(f)
    assert 'generated_at' in mock_data, "Should have generation timestamp"
    assert 'bills' in mock_data, "Should have bills data"
    assert 'representatives' in mock_data, "Should have representatives data"
    assert '65101' in mock_data['representatives'], "Should have Jefferson City data"
    assert '63101' in mock_data['representatives'], "Should have St. Louis data"
    assert '64101' in mock_data['representatives'], "Should have Kansas City data"
    assert 'default' in mock_data['representatives'], "Should have default fallback"
    print("✓ Mock data structure is valid")
    print(f"  Generated at: {mock_data['generated_at']}")
    print(f"  Bills count: {len(mock_data['bills'])}")
    print(f"  Rep locations: {len(mock_data['representatives'])} zip codes")
    
    # Test 7: Environment detection
    print("\n[Test 7] Testing environment detection...")
    assert not fetcher.is_production, "Should be in development mode"
    print("✓ Correctly detected development mode")
    
    # Test 8: Singleton pattern
    print("\n[Test 8] Testing singleton pattern...")
    fetcher2 = get_data_fetcher()
    assert fetcher is fetcher2, "Should return same instance"
    print("✓ Singleton pattern working correctly")
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70)
    print("""
Summary:
✓ Mock data file exists and is valid
✓ Bills fetching works correctly
✓ Representatives fetching works correctly
✓ Zip code-based lookup works
✓ Unknown zip fallback works
✓ Mock data structure is complete
✓ Environment detection works
✓ Singleton pattern implemented

The data fetcher is fully functional and ready to use!
    """)

if __name__ == '__main__':
    try:
        test_data_fetcher()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
