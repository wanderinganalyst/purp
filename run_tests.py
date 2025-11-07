#!/usr/bin/env python3
"""
Test runner script for Purp application
Runs all tests and generates reports
"""

import sys
import subprocess
import os
from pathlib import Path


def run_tests(test_type='all', verbose=False, coverage=False):
    """
    Run tests based on type.
    
    Args:
        test_type: Type of tests to run ('all', 'unit', 'integration', 'e2e', 'docker')
        verbose: Enable verbose output
        coverage: Enable coverage reporting
    """
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add test path based on type
    if test_type == 'unit':
        cmd.append('tests/unit')
    elif test_type == 'integration':
        cmd.append('tests/integration')
    elif test_type == 'e2e':
        cmd.append('tests/e2e')
    elif test_type == 'docker':
        cmd.append('tests/docker')
    else:
        cmd.append('tests')
    
    # Add verbose flag
    if verbose:
        cmd.append('-vv')
    
    # Add coverage
    if coverage:
        cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])
    
    # Run tests
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for Purp application')
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        choices=['all', 'unit', 'integration', 'e2e', 'docker'],
        help='Type of tests to run (default: all)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '-c', '--coverage',
        action='store_true',
        help='Enable coverage reporting'
    )
    parser.add_argument(
        '--install-deps',
        action='store_true',
        help='Install test dependencies before running'
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            'pytest', 'pytest-cov', 'beautifulsoup4', 'requests'
        ])
        print()
    
    # Run tests
    exit_code = run_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    if args.coverage:
        print("\n📊 Coverage report generated at: htmlcov/index.html")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
