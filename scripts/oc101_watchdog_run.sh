#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-$HOME/.codex/skills/openclaw-101/scripts/oc101_watchdog.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "env file not found: $ENV_FILE" >&2
  echo "create it first: cp $HOME/.codex/skills/openclaw-101/scripts/oc101_watchdog.env.example $HOME/.codex/skills/openclaw-101/scripts/oc101_watchdog.env" >&2
  exit 2
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

exec "$HOME/.codex/skills/openclaw-101/scripts/oc101_watchdog.py"
