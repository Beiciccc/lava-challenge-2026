#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

COMMIT_MSG="${1:-chore: sync local experiment updates}"

git add README.md requirements.txt .gitignore
git add scripts src logs reports submissions data/raw data/processed

if git diff --cached --quiet; then
  echo "No tracked project updates to sync."
  exit 0
fi

git commit -m "$COMMIT_MSG"
git push origin main
echo "Synced to GitHub: $(git rev-parse --short HEAD)"
