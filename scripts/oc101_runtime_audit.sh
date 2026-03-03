#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_HOST="${OPENCLAW101_HOST:-192.168.1.101}"
TARGET_USER="${OPENCLAW101_USER:-root}"
TARGET="${TARGET_USER}@${TARGET_HOST}"

REPO_SENDER="${ROOT_DIR}/scripts/oc101_heartbeat_sender.sh"
SKILL_SENDER="/root/.codex/skills/openclaw-101/scripts/oc101_heartbeat_sender.sh"
REMOTE_SENDER="/root/.openclaw/ops/heartbeat_sender.sh"
REMOTE_ENV="/root/.openclaw/ops/heartbeat_sender.env"
REMOTE_CRON_PATTERN="/root/.openclaw/ops/heartbeat_sender.sh"
EXPECTED_CRON='set -a; . /root/.openclaw/ops/heartbeat_sender.env; set +a; /root/.openclaw/ops/heartbeat_sender.sh'

echo "== Target =="
echo "host=${TARGET_HOST} user=${TARGET_USER}"

echo
echo "== Local script hashes =="
sha256sum "${REPO_SENDER}" "${SKILL_SENDER}"

echo
echo "== Remote runtime hashes =="
ssh "${TARGET}" "sha256sum '${REMOTE_SENDER}' '${REMOTE_ENV}'"

echo
echo "== Remote cron heartbeat line =="
CRON_LINE="$(ssh "${TARGET}" "crontab -l | grep -F '${REMOTE_CRON_PATTERN}' || true")"
if [[ -z "${CRON_LINE}" ]]; then
  echo "MISSING: heartbeat cron line not found"
else
  echo "${CRON_LINE}"
  if [[ "${CRON_LINE}" == *"${EXPECTED_CRON}"* ]]; then
    echo "PASS: cron uses set -a anti-regression style"
  else
    echo "WARN: cron does not match set -a anti-regression style"
  fi
fi

echo
echo "== Remote env key declaration style =="
ssh "${TARGET}" "grep -nE '^(export )?OC101_HB_(WEBHOOK_URL|SHARED_SECRET)=' '${REMOTE_ENV}' || true"

echo
echo "== Watchdog service source =="
ssh "${TARGET}" "systemctl cat oc101-watchdog.service | sed -n '1,120p'"

echo
echo "== Sender one-shot test =="
ssh "${TARGET}" "set -a; . '${REMOTE_ENV}'; set +a; '${REMOTE_SENDER}'"

