# Branch Protection Setup Checklist

Use this checklist when configuring branch protection in GitHub settings.

## Main Branch Protection Rule

### Basic Settings

- [ ] Ruleset name: `Main Branch Protection`
- [ ] Enforcement: `Active`
- [ ] Target: `main` branch

### Protection Rules

- [ ] ✅ Restrict deletions
- [ ] ✅ Restrict force pushes
- [ ] ❌ Restrict creations (leave off)

### Pull Request Requirements

- [ ] ✅ Require pull request before merging
  - [ ] Required approvals: `1`
  - [ ] ✅ Dismiss stale PR approvals on new commits
  - [ ] ✅ Require review from CODEOWNERS
  - [ ] ✅ Require approval of most recent push
  - [ ] ✅ Require conversation resolution

### Status Checks

- [ ] ✅ Require status checks to pass
- [ ] ✅ Require branches to be up to date
- [ ] Add required checks:
  - [ ] `CI / Test and Lint (ubuntu-latest, 3.11)`
  - [ ] `CI / Test and Lint (ubuntu-latest, 3.12)`
  - [ ] `CI / Test and Lint (windows-latest, 3.11)`
  - [ ] `CI / Test and Lint (macos-latest, 3.11)`
  - [ ] `CI / Build Package`
  - [ ] `CI / Type Check`

### Optional Settings

- [ ] Require signed commits (optional)
- [ ] Configure bypass list (if needed)

## Developer Branch Rule

### Basic Settings

- [ ] Ruleset name: `Developer Branch Naming`
- [ ] Enforcement: `Evaluate` or `Active`
- [ ] Target: `dev/**/*` pattern

### Notes

- This enforces `dev/<username>/<feature>` naming
- Set to `Evaluate` to warn, `Active` to block

## Repository Settings

### General Settings
- [ ] Go to Settings → General
- [ ] Scroll to "Pull Requests" section
- [ ] ✅ Enable "Automatically delete head branches"
  - This deletes feature branches after merge
  - Keeps repository clean and organized

## Post-Setup Tasks

- [ ] Test protection by trying direct push (should fail)
- [ ] Test PR workflow with a sample change
- [ ] Document any custom settings
- [ ] Share setup with team members
