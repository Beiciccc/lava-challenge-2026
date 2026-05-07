#!/usr/bin/env bash
set -euo pipefail

COMPETITION="${COMPETITION:-lava-challenge-2026}"
REMOTE_USER="${REMOTE_USER:-}"
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_PORT="${REMOTE_PORT:-22}"
IDENTITY="${IDENTITY:-$HOME/.ssh/id_ed25519}"
REMOTE_ROOT="${REMOTE_ROOT:-$HOME/lava-challenge-2026}"
REMOTE="${REMOTE_USER}@${REMOTE_HOST}"

if [[ -z "$REMOTE_USER" || -z "$REMOTE_HOST" ]]; then
  echo "Set REMOTE_USER and REMOTE_HOST before running GPU sync scripts." >&2
  exit 1
fi
LOCAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SSH_BASE_OPTS=(
  -p "$REMOTE_PORT"
  -i "$IDENTITY"
  -o IdentitiesOnly=yes
  -o ServerAliveInterval=30
  -o ServerAliveCountMax=3
)

RSYNC_SSH="ssh -p $REMOTE_PORT -i $IDENTITY -o IdentitiesOnly=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3"
