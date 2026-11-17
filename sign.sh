#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEY_NAME="gradleInit.official"
DEVL_DIR="/c/devl"

sign_and_push() {
  local repo_name="$1"
  local repo_path="${DEVL_DIR}/${repo_name}"
  
  echo "=== ${repo_name} ==="
  
  if [ ! -d "$repo_path" ]; then
    echo "[ERROR] Repository not found: ${repo_path}"
    return 1
  fi
  
  # Sign
  echo "[SIGN] ${repo_path}"
  gradleInit sign --repo "$repo_path" --key "$KEY_NAME"
  
  # Git operations
  cd "$repo_path"
  
  # Add only signature files
  git add CHECKSUMS.sha256 CHECKSUMS.sig
  
  # Check if there are changes to commit
  if git diff --cached --quiet; then
    echo "[SKIP] No changes to commit"
  else
    git commit -m "Signed release"
    git push
    echo "[OK] Pushed"
  fi
  
  echo ""
}

echo "Signing repositories with key: ${KEY_NAME}"
echo ""

sign_and_push gradleInit
sign_and_push gradleInitTemplates
sign_and_push gradleInitModules

echo "=== Done ==="
