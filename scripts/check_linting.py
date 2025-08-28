#!/usr/bin/env python3
"""
Linting Check Script for Email Agent

This script runs Ruff linting checks and enforces the project's linting standards:
- Zero errors allowed
- Less than 50 warnings total

Exit codes:
- 0: Success (no errors, warnings under threshold)
- 1: Linting errors found
- 2: Warning threshold exceeded
"""

import re
import subprocess
import sys


def count_issues(output: str) -> tuple[int, int]:
    """Parse ruff output to count errors and warnings."""
    errors = 0
    warnings = 0

    # Ruff output format: filename:line:col: CODE message
    for line in output.strip().split('\n'):
        if not line or line.startswith('Found'):
            continue

        # Check if it's an error (E) or warning (W) or other
        if ': E' in line:
            errors += 1
        elif ': W' in line or ': ' in line:  # Most issues are warnings
            warnings += 1

    # Also check the summary line
    summary_match = re.search(r'Found (\d+) error', output)
    if summary_match:
        errors = max(errors, int(summary_match.group(1)))

    return errors, warnings


def main():
    """Run linting checks and enforce standards."""
    print("🔍 Running linting checks...")
    print("-" * 50)

    # Run ruff check
    result = subprocess.run(
        ['uv', 'run', 'ruff', 'check', '.'],
        capture_output=True,
        text=True
    )

    # Parse output
    output = result.stdout + result.stderr
    errors, warnings = count_issues(output)

    # Print results
    print("\n📊 Linting Results:")
    print(f"   Errors:   {errors}")
    print(f"   Warnings: {warnings}")
    print(f"   Total:    {errors + warnings}")

    # Check against thresholds
    print("\n📏 Thresholds:")
    print("   Max Errors:   0")
    print("   Max Warnings: 49")

    # Determine status
    if errors > 0:
        print(f"\n❌ FAILED: {errors} linting errors found (0 allowed)")
        print("\nPlease fix all errors before submitting a PR.")
        print("\nRun 'uv run ruff check --fix .' to auto-fix some issues.")
        return 1
    elif warnings >= 50:
        print(f"\n❌ FAILED: {warnings} warnings exceed threshold (49 max)")
        print("\nPlease reduce warnings before submitting a PR.")
        return 2
    else:
        print(f"\n✅ PASSED: No errors, {warnings} warnings (under threshold)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
