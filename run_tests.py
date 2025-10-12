#!/usr/bin/env python3
"""
Test runner script for DockSafe.

This script provides an easy way to run tests with different configurations.
"""

import os
import sys
import subprocess
import argparse


def run_tests(test_type='all', coverage=True, verbose=False, parallel=False):
    """Run tests with specified configuration."""
    
    # Base pytest command
    cmd = ['pytest']
    
    # Add test path based on type
    if test_type == 'unit':
        cmd.append('tests/unit/')
    elif test_type == 'integration':
        cmd.append('tests/integration/')
    elif test_type == 'all':
        cmd.append('tests/')
    else:
        print(f"Unknown test type: {test_type}")
        return False
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            '--cov=app',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-report=xml:coverage.xml',
            '--cov-fail-under=80'
        ])
    
    # Add verbosity
    if verbose:
        cmd.append('-v')
    
    # Add parallel execution
    if parallel:
        cmd.extend(['-n', 'auto'])
    
    # Add other useful options
    cmd.extend([
        '--tb=short',
        '--strict-markers',
        '--disable-warnings'
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Run DockSafe tests')
    parser.add_argument(
        '--type', 
        choices=['unit', 'integration', 'all'], 
        default='all',
        help='Type of tests to run'
    )
    parser.add_argument(
        '--no-coverage', 
        action='store_true',
        help='Disable coverage reporting'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Run tests in parallel'
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run tests
    success = run_tests(
        test_type=args.type,
        coverage=not args.no_coverage,
        verbose=args.verbose,
        parallel=args.parallel
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
