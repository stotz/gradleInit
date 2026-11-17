#!/bin/bash
# release.sh - Create or delete a gradleInit release (all 3 repos)
#
# Usage:
#   ./release.sh <version>            Create release vX.Y.Z (all 3 repos)
#   ./release.sh --delete <version>   Delete release/tag vX.Y.Z (all 3 repos)
#
# Examples:
#   ./release.sh 1.0.0
#   ./release.sh --delete 1.0.0
#
# Create mode:
#   1. Updates version in gradleInit.py and README.md
#   2. Signs all 3 repositories (gradleInit, gradleInitTemplates, gradleInitModules)
#   3. Creates git tags and pushes to all repos
#   4. Creates GitHub release
#
# Delete mode:
#   Removes the GitHub release, the remote tag and the local tag for the given
#   version from all 3 repos. Each step is idempotent: anything already absent is
#   skipped, so the command is safe to re-run.

set -e

DEVL_DIR="/c/devl"
KEY_NAME="gradleInit.official"
REPOS=("gradleInit" "gradleInitTemplates" "gradleInitModules")

usage() {
    echo "Usage:"
    echo "  ./release.sh <version>            Create release vX.Y.Z (all 3 repos)"
    echo "  ./release.sh --delete <version>   Delete release/tag vX.Y.Z (all 3 repos)"
    echo "Example: ./release.sh 1.0.0   |   ./release.sh --delete 1.0.0"
}

# Strip an optional leading 'v' so both '1.2.3' and 'v1.2.3' are accepted.
strip_v() { echo "${1#v}"; }

is_semver() { [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; }

# ============================================================================
# Delete mode
# ============================================================================
if [[ "$1" == "--delete" ]]; then
    DEL_VERSION="$(strip_v "$2")"
    if [[ -z "$DEL_VERSION" ]]; then
        usage
        exit 1
    fi
    if ! is_semver "$DEL_VERSION"; then
        echo "Error: Version must be in semver format (e.g., 1.0.0)"
        exit 1
    fi

    TAG="v$DEL_VERSION"
    echo "==> This will delete GitHub release and tag $TAG from:"
    for repo in "${REPOS[@]}"; do
        echo "      - $repo"
    done
    echo ""
    read -p "Delete $TAG everywhere? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
    echo ""

    for repo in "${REPOS[@]}"; do
        repo_path="${DEVL_DIR}/${repo}"
        echo "--- $repo ---"

        if [[ ! -d "$repo_path" ]]; then
            echo "[SKIP] repository not found: $repo_path"
            echo ""
            continue
        fi
        cd "$repo_path"

        # 1. GitHub release (gh detects the repo from the cwd's origin remote).
        if gh release view "$TAG" >/dev/null 2>&1; then
            if gh release delete "$TAG" --yes >/dev/null 2>&1; then
                echo "[OK]   GitHub release $TAG deleted"
            else
                echo "[WARN] could not delete GitHub release $TAG"
            fi
        else
            echo "[SKIP] no GitHub release $TAG"
        fi

        # 2. Remote tag.
        if [[ -n "$(git ls-remote origin "refs/tags/$TAG" 2>/dev/null)" ]]; then
            if git push origin ":refs/tags/$TAG" >/dev/null 2>&1; then
                echo "[OK]   remote tag $TAG deleted"
            else
                echo "[WARN] could not delete remote tag $TAG"
            fi
        else
            echo "[SKIP] no remote tag $TAG"
        fi

        # 3. Local tag.
        if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null 2>&1; then
            if git tag -d "$TAG" >/dev/null 2>&1; then
                echo "[OK]   local tag $TAG deleted"
            else
                echo "[WARN] could not delete local tag $TAG"
            fi
        else
            echo "[SKIP] no local tag $TAG"
        fi

        echo ""
    done

    echo "[OK] $TAG removed where present. You can now re-run ./release.sh $DEL_VERSION"
    exit 0
fi

# ============================================================================
# Create mode
# ============================================================================
VERSION="$1"

if [[ -z "$VERSION" ]]; then
    usage
    exit 1
fi

if ! is_semver "$VERSION"; then
    echo "Error: Version must be in semver format (e.g., 1.0.0)"
    exit 1
fi

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

# Get current version (for display only; replacements below are version-agnostic)
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

# Version-agnostic replacements: always set the target $VERSION regardless of the
# previous value. This stays correct even if SCRIPT_VERSION was bumped by hand.
sed -i -E 's/^SCRIPT_VERSION = .*/SCRIPT_VERSION = "'"$VERSION"'"/' gradleInit.py
sed -i "s/^Version: .*/Version: $VERSION/" gradleInit.py
sed -i -E "s/gradleInit v[0-9]+\.[0-9]+\.[0-9]+/gradleInit v$VERSION/g" README.md
sed -i -E "s/version-[0-9]+\.[0-9]+\.[0-9]+-blue/version-$VERSION-blue/g" README.md
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
