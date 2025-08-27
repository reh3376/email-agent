#!/usr/bin/env python3
"""
Pre-commit Hooks Setup Script

This script helps developers set up pre-commit hooks to catch issues before committing.
Pre-commit hooks run automatically before each commit to ensure code quality.

Benefits:
- Catch linting errors before they reach the repository
- Ensure commit messages meet minimum length requirement
- Format code automatically
- Run quick tests on changed files
"""

import sys
import subprocess
from pathlib import Path
import shutil


HOOK_CONTENT = '''#!/usr/bin/env python3
"""Pre-commit hook for Email Agent project."""

import subprocess
import sys
import re


def check_commit_message():
    """Ensure commit message is at least 15 words."""
    # Get the commit message
    with open('.git/COMMIT_EDITMSG', 'r') as f:
        msg = f.read().strip()
    
    # Skip merge commits
    if msg.startswith('Merge'):
        return True
    
    # Count words (split by whitespace)
    words = len(msg.split())
    
    if words < 15:
        print(f"❌ Commit message too short: {words} words (minimum 15)")
        print(f"   Current message: {msg}")
        print("\\nPlease write a more descriptive commit message explaining WHY you made these changes.")
        return False
    
    return True


def run_linting():
    """Run quick linting check on staged Python files."""
    # Get list of staged Python files
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True,
        text=True
    )
    
    py_files = [f for f in result.stdout.strip().split('\\n') if f.endswith('.py')]
    
    if not py_files:
        return True
    
    print(f"🔍 Checking {len(py_files)} Python files...")
    
    # Run ruff on staged files only
    result = subprocess.run(
        ['uv', 'run', 'ruff', 'check'] + py_files,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("❌ Linting errors found in staged files:")
        print(result.stdout)
        print("\\nRun 'uv run ruff check --fix' to auto-fix some issues.")
        return False
    
    return True


def main():
    """Run all pre-commit checks."""
    print("🚀 Running pre-commit checks...")
    
    # Check commit message length
    if not check_commit_message():
        return 1
    
    # Run linting
    if not run_linting():
        return 1
    
    print("✅ All pre-commit checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def setup_pre_commit():
    """Install pre-commit hook."""
    print("🔧 Setting up pre-commit hooks for Email Agent...")
    
    # Check if we're in a git repository
    if not Path('.git').exists():
        print("❌ Error: Not in a git repository root")
        return 1
    
    # Create hooks directory if it doesn't exist
    hooks_dir = Path('.git/hooks')
    hooks_dir.mkdir(exist_ok=True)
    
    # Write pre-commit hook
    hook_path = hooks_dir / 'pre-commit'
    hook_path.write_text(HOOK_CONTENT)
    
    # Make it executable
    hook_path.chmod(0o755)
    
    print("✅ Pre-commit hook installed successfully!")
    print("\nThe hook will automatically:")
    print("  • Check commit messages are at least 15 words")
    print("  • Run linting on staged Python files")
    print("  • Prevent commits with linting errors")
    
    print("\nTo bypass the hook in emergencies, use: git commit --no-verify")
    print("(But please use this sparingly!)")
    
    return 0


def remove_pre_commit():
    """Remove pre-commit hook."""
    hook_path = Path('.git/hooks/pre-commit')
    if hook_path.exists():
        hook_path.unlink()
        print("✅ Pre-commit hook removed")
    else:
        print("ℹ️  No pre-commit hook found")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == '--remove':
        remove_pre_commit()
    else:
        return setup_pre_commit()


if __name__ == "__main__":
    sys.exit(main())
