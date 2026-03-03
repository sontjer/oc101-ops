#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-$SCRIPT_DIR/../examples/oc101_watchdog.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "env file not found: $ENV_FILE" >&2
  echo "create it first: cp $SCRIPT_DIR/../examples/oc101_watchdog.env.example $SCRIPT_DIR/../examples/oc101_watchdog.env" >&2
  exit 2
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

exec "$SCRIPT_DIR/oc101_watchdog.py"
