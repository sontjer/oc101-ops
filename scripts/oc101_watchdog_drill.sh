#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WD_ENV="${OC101_WD_ENV:-$SCRIPT_DIR/../examples/oc101_watchdog.env.example}"
REMOTE_ENV="${OC101_DRILL_REMOTE_ENV:-/root/.openclaw/ops/heartbeat_sender.env}"
REMOTE_SENDER="${OC101_DRILL_REMOTE_SENDER:-/root/.openclaw/ops/heartbeat_sender.sh}"
REMOTE_CRON_MATCH="${OC101_DRILL_REMOTE_CRON_MATCH:-/root/.openclaw/ops/heartbeat_sender.sh}"
REMOTE_CRON_LINE=". ${REMOTE_ENV} && ${REMOTE_SENDER} >> /root/.openclaw/ops/heartbeat_sender.log 2>&1"
REMOTE_HOST="${OPENCLAW101_HOST:-}"
REMOTE_USER="${OPENCLAW101_USER:-root}"
REMOTE_IDENTITY="${OPENCLAW101_IDENTITY:-${OPENCLAW101_DEFAULT_IDENTITY:-$HOME/.ssh/oc101_ed25519}}"

TEST_STALE_SECONDS="${OC101_DRILL_TEST_STALE_SECONDS:-45}"
TEST_CHECK_SECONDS="${OC101_DRILL_TEST_CHECK_SECONDS:-10}"
PROD_STALE_SECONDS="${OC101_DRILL_PROD_STALE_SECONDS:-1200}"
PROD_CHECK_SECONDS="${OC101_DRILL_PROD_CHECK_SECONDS:-60}"
OBSERVE_SECONDS="${OC101_DRILL_OBSERVE_SECONDS:-80}"

LOG_FILE="${OC101_DRILL_LOG_FILE:-$HOME/.codex/log/oc101-watchdog.log}"

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing command: $1" >&2; exit 2; }
}

require ssh
require rg
require systemctl

[[ -f "$WD_ENV" ]] || { echo "watchdog env not found: $WD_ENV" >&2; exit 2; }
[[ -f "$LOG_FILE" ]] || touch "$LOG_FILE"
[[ -n "$REMOTE_HOST" ]] || { echo "OPENCLAW101_HOST is required" >&2; exit 2; }

ssh_remote() {
  local target="${REMOTE_USER}@${REMOTE_HOST}"
  local -a opts=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o ConnectTimeout=8
  )
  if [[ -n "${REMOTE_IDENTITY}" && -f "${REMOTE_IDENTITY}" ]]; then
    opts+=(-i "${REMOTE_IDENTITY}" -o IdentitiesOnly=yes)
  fi
  ssh "${opts[@]}" "$target" "$@"
}

mark="DRILL_$(date +%s)"
restore_done="0"

restore_all() {
  if [[ "$restore_done" == "1" ]]; then
    return
  fi
  set +e
  sed -i "s/^OC101_WD_STALE_AFTER_SECONDS=.*/OC101_WD_STALE_AFTER_SECONDS=${PROD_STALE_SECONDS}/" "$WD_ENV"
  sed -i "s/^OC101_WD_CHECK_INTERVAL_SECONDS=.*/OC101_WD_CHECK_INTERVAL_SECONDS=${PROD_CHECK_SECONDS}/" "$WD_ENV"

  ssh_remote "set -euo pipefail; (crontab -l 2>/dev/null || true) | grep -Fv \"${REMOTE_CRON_MATCH}\" > /tmp/cron.new; printf '%s\\n' \"*/15 * * * * ${REMOTE_CRON_LINE}\" >> /tmp/cron.new; crontab /tmp/cron.new; rm -f /tmp/cron.new"

  systemctl restart oc101-watchdog.service
  ssh_remote "set -a; source ${REMOTE_ENV}; set +a; ${REMOTE_SENDER}" >/dev/null 2>&1 || true
  restore_done="1"
  set -e
}

trap restore_all EXIT

echo "[drill] pause heartbeat cron"
ssh_remote "set -euo pipefail; (crontab -l 2>/dev/null || true) | grep -Fv \"${REMOTE_CRON_MATCH}\" > /tmp/cron.new; crontab /tmp/cron.new; rm -f /tmp/cron.new"

echo "[drill] set watchdog fast thresholds"
sed -i "s/^OC101_WD_STALE_AFTER_SECONDS=.*/OC101_WD_STALE_AFTER_SECONDS=${TEST_STALE_SECONDS}/" "$WD_ENV"
sed -i "s/^OC101_WD_CHECK_INTERVAL_SECONDS=.*/OC101_WD_CHECK_INTERVAL_SECONDS=${TEST_CHECK_SECONDS}/" "$WD_ENV"

echo "[drill] unlock timeout window with one heartbeat"
ssh_remote "set -a; source ${REMOTE_ENV}; set +a; ${REMOTE_SENDER}" >/dev/null
sleep 2

echo "$mark" >> "$LOG_FILE"
echo "[drill] restart watchdog and observe ${OBSERVE_SECONDS}s"
systemctl restart oc101-watchdog.service
sleep "$OBSERVE_SECONDS"

start_line="$(rg -n "$mark" "$LOG_FILE" | tail -n1 | cut -d: -f1)"
block="$(sed -n "${start_line},$ p" "$LOG_FILE")"
printf '%s\n' "$block"

incident_ok="$(printf '%s\n' "$block" | rg -c 'incident sent_to_telegram=True' || true)"
incident_fail="$(printf '%s\n' "$block" | rg -c 'incident sent_to_telegram=False' || true)"
recovered_ok="$(printf '%s\n' "$block" | rg -c 'recovery sent_to_telegram=True' || true)"

echo "incident_ok=${incident_ok}"
echo "incident_fail=${incident_fail}"
echo "recovered_ok=${recovered_ok}"

if [[ "$incident_ok" -ge 1 ]]; then
  echo "[drill] result=PASS"
else
  echo "[drill] result=FAIL"
  exit 1
fi
