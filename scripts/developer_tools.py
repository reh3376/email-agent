#!/usr/bin/env python3
"""
Developer Tools Script

Provides various utilities for developers working on the Email Agent project.
"""

import argparse
import subprocess
import sys


def create_branch(username: str, feature: str):
    """Create a properly named developer branch."""
    branch_name = f"dev/{username}/{feature}"

    # Check if branch already exists
    result = subprocess.run(
        ["git", "branch", "--list", branch_name], capture_output=True, text=True
    )

    if result.stdout.strip():
        print(f"❌ Branch '{branch_name}' already exists")
        return 1

    # Create and checkout branch
    subprocess.run(["git", "checkout", "-b", branch_name])
    print(f"✅ Created and checked out branch: {branch_name}")
    print("\nNext steps:")
    print("1. Make your changes")
    print("2. Commit with descriptive messages (>15 words)")
    print(f"3. Push with: git push -u origin {branch_name}")
    print("4. Create PR at: https://github.com/reh3376/email-agent/pulls")

    return 0


def check_pr_ready():
    """Check if current branch is ready for PR."""
    print("🔍 Checking PR readiness...")

    issues = []

    # Check for uncommitted changes
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.stdout.strip():
        issues.append("Uncommitted changes detected")

    # Check branch name
    result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    branch = result.stdout.strip()
    if not branch.startswith("dev/") or branch.count("/") < 2:
        issues.append(f"Invalid branch name: {branch}")

    # Run linting check
    result = subprocess.run(
        ["uv", "run", "python", "scripts/check_linting.py"], capture_output=True
    )
    if result.returncode != 0:
        issues.append("Linting check failed")

    # Check if tests pass
    print("Running tests...")
    result = subprocess.run(["uv", "run", "pytest", "-q"], capture_output=True)
    if result.returncode != 0:
        issues.append("Some tests are failing")

    if issues:
        print("\n❌ Not ready for PR:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\n✅ Ready for PR!")
        print(f"\nCreate PR at: https://github.com/reh3376/email-agent/compare/main...{branch}")

    return len(issues)


def sync_with_main():
    """Sync current branch with latest main."""
    print("🔄 Syncing with main...")

    # Save current branch
    result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    current_branch = result.stdout.strip()

    if not current_branch.startswith("dev/"):
        print("❌ Must be on a dev branch to sync")
        return 1

    # Fetch latest
    subprocess.run(["git", "fetch", "origin", "main"])

    # Merge or rebase
    print("Merging latest main...")
    result = subprocess.run(["git", "merge", "origin/main"])

    if result.returncode != 0:
        print("\n⚠️  Merge conflicts detected!")
        print("Please resolve conflicts and commit the merge.")
    else:
        print("✅ Successfully synced with main")

    return result.returncode


def validate_commit_msg(message: str = None):
    """Validate commit message meets requirements."""
    if not message:
        # Get last commit message
        result = subprocess.run(["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True)
        message = result.stdout.strip()

    words = len(message.split())

    if words < 15:
        print(f"❌ Commit message too short: {words} words (minimum 15)")
        print(f"   Message: {message}")
        return 1
    else:
        print(f"✅ Commit message OK: {words} words")
        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Developer tools for Email Agent")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create branch command
    branch_parser = subparsers.add_parser("branch", help="Create a new dev branch")
    branch_parser.add_argument("username", help="Your GitHub username")
    branch_parser.add_argument("feature", help="Feature name (no spaces)")

    # Check PR readiness
    subparsers.add_parser("check", help="Check if ready for PR")

    # Sync with main
    subparsers.add_parser("sync", help="Sync current branch with main")

    # Validate commit message
    msg_parser = subparsers.add_parser("validate-msg", help="Validate commit message")
    msg_parser.add_argument("--message", help="Message to validate (default: last commit)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "branch":
        return create_branch(args.username, args.feature)
    elif args.command == "check":
        return check_pr_ready()
    elif args.command == "sync":
        return sync_with_main()
    elif args.command == "validate-msg":
        return validate_commit_msg(args.message)


if __name__ == "__main__":
    sys.exit(main())
