#!/bin/bash

# Setup Branch Protection Rules for Email Agent Repository
# This script configures branch rulesets for collaborative development

echo "Setting up branch protection rules for email-agent repository..."

# Check if gh CLI is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "Error: GitHub CLI is not authenticated. Please run 'gh auth login' first."
    exit 1
fi

REPO="reh3376/email-agent"
echo "Repository: $REPO"

# Create main branch protection ruleset
echo "Creating main branch protection ruleset..."
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/$REPO/rulesets \
  --input docs/branch-ruleset-config.json

if [ $? -eq 0 ]; then
    echo "✅ Main branch protection ruleset created successfully"
else
    echo "❌ Failed to create main branch protection ruleset"
fi

# Create developer branch naming convention ruleset
echo "Creating developer branch naming convention ruleset..."
cat > /tmp/dev-branch-ruleset.json << 'EOF'
{
  "name": "Developer Branch Naming Convention",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/dev/**"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "restriction",
      "parameters": {
        "restrict_creations": false,
        "restrict_updates": false,
        "restrict_deletions": false
      }
    }
  ],
  "bypass_actors": [
    {
      "actor_id": 1,
      "actor_type": "RepositoryRole",
      "bypass_mode": "always"
    }
  ]
}
EOF

gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/$REPO/rulesets \
  --input /tmp/dev-branch-ruleset.json

if [ $? -eq 0 ]; then
    echo "✅ Developer branch naming ruleset created successfully"
else
    echo "❌ Failed to create developer branch naming ruleset"
fi

# Clean up
rm -f /tmp/dev-branch-ruleset.json

# Enable auto-delete head branches
echo "Enabling auto-delete head branches..."
gh api \
  --method PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/$REPO \
  -f delete_branch_on_merge=true

if [ $? -eq 0 ]; then
    echo "✅ Auto-delete head branches enabled"
else
    echo "❌ Failed to enable auto-delete head branches"
fi

echo ""
echo "Branch protection setup complete!"
echo ""
echo "Summary of rules:"
echo "1. Main branch requires:"
echo "   - Pull request with 1 approval from @reh3376"
echo "   - All CI checks must pass"
echo "   - Branches must be up-to-date"
echo "   - No direct pushes allowed"
echo ""
echo "2. Developer branches must follow pattern:"
echo "   - dev/<username>/<feature-name>"
echo ""
echo "3. Repository settings:"
echo "   - Auto-delete head branches after merge: ENABLED"
echo ""
echo "See docs/CONTRIBUTING.md for detailed workflow instructions."
