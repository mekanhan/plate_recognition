#!/usr/bin/env python3
"""
Test Runner for LPR System
Provides convenient commands for running different test suites
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    result = subprocess.run(cmd, text=True)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='LPR System Test Runner')
    parser.add_argument('suite', nargs='?', default='all',
                       choices=['all', 'unit', 'integration', 'functional', 
                               'performance', 'fast', 'coverage'],
                       help='Test suite to run (default: all)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-k', '--keyword', type=str,
                       help='Run tests matching keyword')
    parser.add_argument('-m', '--marker', type=str,
                       help='Run tests with specific marker')
    parser.add_argument('--failfast', '-x', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('--parallel', '-n', action='store_true',
                       help='Run tests in parallel')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Generate coverage report')
    
    args = parser.parse_args()
    
    # Base pytest command - use venv if available
    python_path = "./venv/bin/python3" if Path("./venv/bin/python3").exists() else "python3"
    cmd = [python_path, '-m', 'pytest']
    
    # Add verbosity
    if args.verbose:
        cmd.append('-vv')
    else:
        cmd.append('-v')
    
    # Add test suite selection
    if args.suite == 'unit':
        cmd.extend(['tests/unit', '-m', 'unit'])
        print("🧪 Running Unit Tests...")
    elif args.suite == 'integration':
        cmd.extend(['tests/integration', '-m', 'integration'])
        print("🔗 Running Integration Tests...")
    elif args.suite == 'functional':
        cmd.extend(['tests/functional', '-m', 'functional'])
        print("✅ Running Functional Tests...")
    elif args.suite == 'performance':
        cmd.extend(['tests/performance', '-m', 'performance'])
        print("⚡ Running Performance Tests...")
    elif args.suite == 'fast':
        cmd.extend(['-m', 'not slow and not gpu and not camera'])
        print("🏃 Running Fast Tests (no slow/gpu/camera tests)...")
    elif args.suite == 'coverage':
        cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])
        print("📊 Running Tests with Coverage...")
    else:
        cmd.append('tests/')
        print("🎯 Running All Tests...")
    
    # Add keyword filter
    if args.keyword:
        cmd.extend(['-k', args.keyword])
        print(f"   Filtering by keyword: {args.keyword}")
    
    # Add marker filter
    if args.marker:
        cmd.extend(['-m', args.marker])
        print(f"   Filtering by marker: {args.marker}")
    
    # Add failfast
    if args.failfast:
        cmd.append('-x')
        print("   Stopping on first failure")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(['-n', 'auto'])
        print("   Running tests in parallel")
    
    # Add coverage if requested
    if args.coverage and args.suite != 'coverage':
        cmd.extend(['--cov=.', '--cov-report=term-missing'])
        print("   With coverage report")
    
    print("=" * 60)
    
    # Run the tests
    exit_code = run_command(cmd)
    
    print("=" * 60)
    if exit_code == 0:
        print("✅ Tests passed successfully!")
    else:
        print("❌ Tests failed!")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())