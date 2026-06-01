#!/bin/bash
# release.sh - Create a new gradleInit release (all 3 repos)
#
# Usage: ./release.sh <version>
# Example: ./release.sh 1.0.0
#
# This script:
# 1. Updates version in gradleInit.py and README.md
# 2. Signs all 3 repositories (gradleInit, gradleInitTemplates, gradleInitModules)
# 3. Creates git tags and pushes to all repos
# 4. Creates GitHub release

set -e

VERSION="$1"
DEVL_DIR="/c/devl"
KEY_NAME="gradleInit.official"

if [[ -z "$VERSION" ]]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.0"
    exit 1
fi

# Validate version format (semver)
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in semver format (e.g., 1.0.0)"
    exit 1
fi

REPOS=("gradleInit" "gradleInitTemplates" "gradleInitModules")

# Check all repos exist and have no uncommitted changes (ignore untracked files)
echo "==> Checking repositories..."
for repo in "${REPOS[@]}"; do
    repo_path="${DEVL_DIR}/${repo}"
    if [[ ! -d "$repo_path" ]]; then
        echo "Error: Repository not found: $repo_path"
        exit 1
    fi
    
    cd "$repo_path"
    # Only check for modified/staged files, ignore untracked (??)
    if [[ -n $(git status --porcelain | grep -v "^??") ]]; then
        echo "Error: $repo has uncommitted changes"
        git status --short | grep -v "^??"
        exit 1
    fi
    
    branch=$(git branch --show-current)
    if [[ "$branch" != "main" ]]; then
        echo "Warning: $repo is not on main branch (current: $branch)"
    fi
done
echo "[OK] All repositories clean"

# Get current version
cd "${DEVL_DIR}/gradleInit"
CURRENT_VERSION=$(grep -oP "SCRIPT_VERSION = \"\K[^\"]+(?=\")" gradleInit.py)
echo ""
echo "    Current version: $CURRENT_VERSION"
echo "    New version:     $VERSION"
echo ""
read -p "Continue with release v$VERSION? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 1. Update version in gradleInit
echo ""
echo "==> Updating version in gradleInit..."
cd "${DEVL_DIR}/gradleInit"

# Update SCRIPT_VERSION constant
sed -i "s/SCRIPT_VERSION = \"$CURRENT_VERSION\"/SCRIPT_VERSION = \"$VERSION\"/" gradleInit.py

# Update docstring version
sed -i "s/^Version: .*/Version: $VERSION/" gradleInit.py

# Update README.md
sed -i "s/gradleInit v$CURRENT_VERSION/gradleInit v$VERSION/g" README.md
sed -i "s/version-$CURRENT_VERSION-/version-$VERSION-/g" README.md
echo "[OK] Updated gradleInit.py and README.md"

# 2. Sign all repositories
echo ""
echo "==> Signing repositories..."
for repo in "${REPOS[@]}"; do
    repo_path="${DEVL_DIR}/${repo}"
    echo "[SIGN] $repo"
    gradleInit sign --repo "$repo_path" --key "$KEY_NAME"
done
echo "[OK] All repositories signed"

# 3. Commit, tag, and push each repository
echo ""
echo "==> Committing and tagging..."
for repo in "${REPOS[@]}"; do
    repo_path="${DEVL_DIR}/${repo}"
    cd "$repo_path"
    
    echo "--- $repo ---"
    
    # Add changes (only tracked files + signature files)
    git add -u
    git add CHECKSUMS.sha256 CHECKSUMS.sig 2>/dev/null || true
    
    # For gradleInit, also add version changes
    if [[ "$repo" == "gradleInit" ]]; then
        git add gradleInit.py README.md
    fi
    
    # Check if there are changes to commit
    if git diff --cached --quiet; then
        echo "[SKIP] No changes to commit"
    else
        git commit -m "Release v$VERSION"
        echo "[OK] Committed"
    fi
    
    # Create annotated tag
    git tag -a "v$VERSION" -m "Release v$VERSION"
    echo "[OK] Tagged v$VERSION"
    
    # Push
    git push origin main
    git push origin "v$VERSION"
    echo "[OK] Pushed"
    echo ""
done

# 4. Create GitHub release (only for gradleInit)
echo "==> Creating GitHub release..."
cd "${DEVL_DIR}/gradleInit"
gh release create "v$VERSION" \
    --title "gradleInit v$VERSION" \
    --generate-notes

echo ""
echo "========================================"
echo "  Release v$VERSION complete!"
echo "========================================"
echo ""
echo "Repositories released:"
for repo in "${REPOS[@]}"; do
    echo "  - $repo"
done
echo ""
echo "GitHub Release: $(gh repo view --json url -q .url)/releases/tag/v$VERSION"
