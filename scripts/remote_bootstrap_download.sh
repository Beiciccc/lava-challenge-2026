#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=remote_env.sh
source "$SCRIPT_DIR/remote_env.sh"

KAGGLE_JSON="${KAGGLE_JSON:-$HOME/.kaggle/kaggle.json}"

if [[ ! -f "$KAGGLE_JSON" ]]; then
  echo "Missing Kaggle API token: $KAGGLE_JSON" >&2
  exit 1
fi

if [[ ! -f "$IDENTITY" ]]; then
  echo "Missing SSH identity: $IDENTITY" >&2
  exit 1
fi

echo "Creating remote project directories on $REMOTE:$REMOTE_ROOT"
ssh "${SSH_BASE_OPTS[@]}" "$REMOTE" \
  "mkdir -p '$REMOTE_ROOT' '$REMOTE_ROOT/data/raw' '$REMOTE_ROOT/data/processed' '$REMOTE_ROOT/models' '$REMOTE_ROOT/submissions' '$REMOTE_ROOT/logs' ~/.kaggle"

echo "Installing Kaggle credentials on remote host"
scp -P "$REMOTE_PORT" -i "$IDENTITY" -o IdentitiesOnly=yes "$KAGGLE_JSON" "$REMOTE:~/.kaggle/kaggle.json"

echo "Downloading competition data on remote host"
ssh "${SSH_BASE_OPTS[@]}" "$REMOTE" "bash -lc '
set -euo pipefail
chmod 600 ~/.kaggle/kaggle.json
export PATH=\"\$HOME/.local/bin:\$PATH\"
if ! command -v kaggle >/dev/null 2>&1; then
  python3 -m pip install --user --upgrade kaggle
fi
kaggle competitions list -s \"$COMPETITION\"
kaggle competitions files -c \"$COMPETITION\" | sed -n \"1,25p\"
kaggle competitions download -c \"$COMPETITION\" -p \"$REMOTE_ROOT/data/raw\" --force
cd \"$REMOTE_ROOT/data/raw\"
if [[ -f \"$COMPETITION.zip\" ]]; then
  unzip -n \"$COMPETITION.zip\"
fi
find \"$REMOTE_ROOT\" -maxdepth 3 -type f | sed -n \"1,80p\"
'"

echo "Remote data download complete. Pull with: $SCRIPT_DIR/sync_pull.sh"

