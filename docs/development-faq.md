# Development FAQ

## What is "Auto-delete head branches after merge"?

When you create a pull request, you work on a "feature branch" (e.g., `dev/johndoe/add-filter`). 
When this PR is merged into `main`, the feature branch still exists on GitHub.

**Auto-delete head branches** means:
- After your PR is merged, GitHub automatically deletes the feature branch
- This keeps the repository clean (no old branches cluttering things up)
- Your local copy remains untouched - you can delete it manually

**Benefits:**
- Cleaner repository with only active branches
- Less confusion about which branches are still being worked on
- Encourages the pattern of: branch → work → merge → start fresh

**My Recommendation:** Enable this feature. It's standard practice and keeps things tidy.

## What are Pre-commit Hooks?

Pre-commit hooks are scripts that run automatically BEFORE each commit is created.
Think of them as quality gates that catch issues before they enter the repository.

### For This Project, Pre-commit Hooks Would:

1. **Check commit message length** (must be >15 words)
2. **Run linting on changed files** (catch errors before commit)
3. **Ensure no large files** are accidentally committed
4. **Verify branch naming** is correct

### Benefits:

- **Catch issues early** - before they reach GitHub
- **Save CI time** - don't wait for GitHub Actions to find simple errors
- **Maintain consistency** - everyone follows the same standards
- **Reduce review friction** - fewer nitpicky comments on PRs

### How to Set Up:

```bash
# Install pre-commit hooks
uv run python scripts/setup_pre_commit.py

# Remove them (if needed)
uv run python scripts/setup_pre_commit.py --remove
```

### Emergency Bypass:

If you absolutely need to commit without checks:
```bash
git commit --no-verify -m "Emergency fix: detailed explanation here..."
```

**My Recommendation:** Pre-commit hooks are valuable for maintaining code quality.
They're especially helpful for:
- New developers learning the standards
- Catching simple mistakes before they waste CI time
- Ensuring consistent commit messages

The hooks I've created are lightweight and won't slow down your workflow.
