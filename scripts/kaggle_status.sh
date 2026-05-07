#!/usr/bin/env bash
set -euo pipefail

COMPETITION="${COMPETITION:-lava-challenge-2026}"

echo "Competition:"
kaggle competitions list -s "$COMPETITION"

echo
echo "Recent submissions:"
kaggle competitions submissions -c "$COMPETITION" || true

echo
echo "Files:"
kaggle competitions files -c "$COMPETITION" | sed -n "1,30p"

