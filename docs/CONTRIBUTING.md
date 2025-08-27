# Contributing to Email Agent

Welcome to the Email Agent project! This document outlines our collaboration workflow and branch protection rules.

## Branch Protection Rules

### Main Branch (`main`)

- **Protected**: Direct pushes are disabled
- **Reviews Required**: All PRs require approval from @reh3376
- **Status Checks**: All CI checks must pass before merging
- **Up-to-date**: Branches must be up-to-date with main before merging

## Branching Strategy

### Developer Branches

All developers must work in their designated branch namespace:

```
dev/<github-username>/<feature-name>
```

Examples:

- `dev/johndoe/add-email-filtering`
- `dev/janesmith/fix-classification-bug`
- `dev/bobchen/update-documentation`

### Branch Naming Rules

- **Required prefix**: `dev/<username>/`
- **Feature suffix**: Use descriptive kebab-case names
- **No spaces**: Use hyphens instead of spaces
- **Lowercase**: Keep all branch names lowercase

## Workflow Process

### 1. Create Your Branch

```bash
# Switch to main and pull latest
git checkout main
git pull origin main

# Create your dev branch
git checkout -b dev/<your-username>/<feature-name>
```

### 2. Make Your Changes

- Write clean, well-documented code
- Follow the project's coding standards
- Add tests for new functionality
- Update documentation as needed

### 3. Commit Guidelines

Use conventional commits:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/modifications
- `refactor:` Code refactoring
- `style:` Formatting changes
- `chore:` Maintenance tasks

Example:

```bash
git commit -m "feat: add email attachment validation"
```

### 4. Push Your Branch

```bash
git push origin dev/<your-username>/<feature-name>
```

### 5. Create Pull Request

- Create PR from your branch to `main`
- Fill out the PR template completely
- Link any related issues
- Ensure all CI checks pass

### 6. Code Review Process

- @reh3376 will review all PRs
- Address any feedback promptly
- Keep PRs focused and reasonably sized
- Resolve all review comments before merge

## CI Requirements

All PRs must pass:

1. **Linting**: Ruff checks for Python code quality
2. **Formatting**: Code must be properly formatted
3. **Tests**: All tests must pass with adequate coverage
4. **Type Checking**: Type annotations must be valid
5. **Build**: Package must build successfully

## Getting Started

1. Fork the repository (if external contributor)
2. Clone your fork/the repo
3. Set up the development environment:
   ```bash
   uv venv
   uv pip install -e ".[dev]"
   ```
4. Create your developer branch
5. Make your changes
6. Submit a PR

## Questions?

If you have questions about the contribution process, please:

1. Check existing documentation
2. Review recent PRs for examples
3. Ask in the PR comments
4. Contact @reh3376 directly

Thank you for contributing to Email Agent!
