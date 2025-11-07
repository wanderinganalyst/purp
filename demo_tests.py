#!/usr/bin/env python3
"""
Quick test demo - runs a subset of fast tests to demonstrate functionality
"""

import subprocess
import sys
import os

print("""
╔════════════════════════════════════════════════════════════════════╗
║         Purp - Test Suite Quick Demo                    ║
╚════════════════════════════════════════════════════════════════════╝

Running a quick subset of tests to demonstrate functionality...
""")

# Define quick test demos
demos = [
    {
        'name': 'Validator Unit Tests',
        'command': [sys.executable, '-m', 'pytest', 'tests/unit/test_validators.py::TestValidateUsername', '-v'],
        'description': 'Testing username validation logic'
    },
    {
        'name': 'Data Fetcher Tests',
        'command': [sys.executable, '-m', 'pytest', 'tests/unit/test_data_fetcher.py::TestDataFetcher::test_singleton_pattern', 
                    'tests/unit/test_data_fetcher.py::TestDataFetcher::test_fetch_bills_development', '-v'],
        'description': 'Testing data fetcher singleton and bills fetching'
    },
    {
        'name': 'Model Tests',
        'command': [sys.executable, '-m', 'pytest', 'tests/unit/test_models.py::TestUserModel::test_create_user',
                    'tests/unit/test_models.py::TestUserModel::test_password_hashing', '-v'],
        'description': 'Testing user model and password hashing'
    }
]

total_passed = 0
total_failed = 0

for demo in demos:
    print(f"\n{'='*70}")
    print(f"🧪 {demo['name']}")
    print(f"   {demo['description']}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(demo['command'], capture_output=False)
    
    if result.returncode == 0:
        total_passed += 1
        print(f"\n✅ {demo['name']} - PASSED")
    else:
        total_failed += 1
        print(f"\n❌ {demo['name']} - FAILED")

# Summary
print(f"\n{'='*70}")
print("QUICK DEMO SUMMARY")
print(f"{'='*70}")
print(f"✅ Passed: {total_passed}")
print(f"❌ Failed: {total_failed}")
print(f"{'='*70}\n")

if total_failed == 0:
    print("""
🎉 Quick demo complete! All sampled tests passed.

To run the full test suite:
    python run_tests.py all

To run with coverage:
    python run_tests.py all --coverage

To run specific test types:
    python run_tests.py unit
    python run_tests.py integration
    python run_tests.py e2e
    python run_tests.py docker
""")
else:
    print("""
⚠️  Some tests failed. This could be due to missing dependencies or
configuration issues. Try running:
    pip install -r requirements-test.txt
""")

sys.exit(total_failed)
