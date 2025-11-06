#!/usr/bin/env python3
"""
Demo script to show production vs development mode behavior
"""

import os
import sys

def demo_development_mode():
    """Demonstrate development mode with mock data"""
    print("\n" + "="*70)
    print("DEVELOPMENT MODE DEMO")
    print("="*70)
    
    # Ensure we're in development mode
    os.environ['FLASK_ENV'] = 'development'
    
    from utils.data_fetcher import get_data_fetcher
    
    fetcher = get_data_fetcher()
    
    print("\n📋 Fetching Bills (Mock Data)...")
    bills = fetcher.fetch_bills()
    print(f"   Retrieved {len(bills)} bills from cache")
    print(f"   First bill: {bills[0]['number']} - {bills[0]['title'][:50]}...")
    
    print("\n👥 Fetching Representatives (Mock Data)...")
    reps = fetcher.fetch_representatives({'zip': '65101', 'city': 'Jefferson City', 'state': 'MO', 'street': '201 W Capitol'})
    print(f"   Senator: {reps['senator']['name']} ({reps['senator']['party']})")
    print(f"   Representative: {reps['representative']['name']} ({reps['representative']['party']})")
    
    print(f"\n✓ Mock data loaded from: {fetcher.MOCK_DATA_FILE}")

def demo_production_mode():
    """Demonstrate production mode with real data fetching"""
    print("\n" + "="*70)
    print("PRODUCTION MODE DEMO")
    print("="*70)
    
    # Set production mode
    os.environ['FLASK_ENV'] = 'production'
    
    # Force reload of the module to pick up new environment
    if 'utils.data_fetcher' in sys.modules:
        del sys.modules['utils.data_fetcher']
    
    from utils.data_fetcher import get_data_fetcher
    
    fetcher = get_data_fetcher()
    
    print("\n📋 Fetching Bills (Real Data)...")
    print("   Note: This would fetch from Missouri Legislature website")
    print("   (Skipping actual fetch in demo to avoid network delay)")
    
    print("\n👥 Fetching Representatives (Real Data)...")
    print("   Note: This would use RepresentativeLookup to scrape real data")
    print("   (Skipping actual fetch in demo to avoid network delay)")
    
    print("\n⚠️  In production, all data is fetched fresh from external sources")

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         Data Fetcher - Production vs Development Demo           ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    This script demonstrates how the data fetcher behaves differently
    in production vs development environments.
    """)
    
    # Demo development mode
    demo_development_mode()
    
    # Demo production mode
    demo_production_mode()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
    Development Mode:
    ✓ Uses cached mock data from data/mock_data.json
    ✓ No network requests needed
    ✓ Fast and consistent for testing
    ✓ Automatically generates mock data if not exists
    
    Production Mode:
    ✓ Fetches real data from external sources
    ✓ Bills from Missouri Legislature website
    ✓ Representatives from MO Senate website
    ✓ Fresh data on every request
    
    To switch modes, set FLASK_ENV environment variable:
    - export FLASK_ENV=development  (default)
    - export FLASK_ENV=production
    """)
    print("="*70 + "\n")
