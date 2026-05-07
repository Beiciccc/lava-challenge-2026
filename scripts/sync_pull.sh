#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=remote_env.sh
source "$SCRIPT_DIR/remote_env.sh"

RSYNC_ARGS=(-av --partial --progress)
if [[ "${DELETE:-0}" == "1" ]]; then
  RSYNC_ARGS+=(--delete)
fi

rsync "${RSYNC_ARGS[@]}" \
  -e "$RSYNC_SSH" \
  --exclude ".DS_Store" \
  --exclude "._*" \
  --exclude "__pycache__/" \
  --exclude ".venv/" \
  "$REMOTE:$REMOTE_ROOT/" "$LOCAL_ROOT/"
