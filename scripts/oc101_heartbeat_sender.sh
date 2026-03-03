#!/usr/bin/env bash
set -euo pipefail

WEBHOOK_URL="${OC101_HB_WEBHOOK_URL:-}"
SHARED_SECRET="${OC101_HB_SHARED_SECRET:-}"
HOST_ID="${OC101_HB_HOST:-openclaw-host}"
SERVICE_ID="${OC101_HB_SERVICE:-openclaw-gateway}"
STATUS="${OC101_HB_STATUS:-ok}"
VERSION="${OC101_HB_VERSION:-unknown}"
CHANNEL="${OC101_HB_CHANNEL:-stable}"

if [[ -z "$WEBHOOK_URL" || -z "$SHARED_SECRET" ]]; then
  echo "OC101_HB_WEBHOOK_URL and OC101_HB_SHARED_SECRET are required" >&2
  exit 2
fi

command -v openssl >/dev/null 2>&1 || { echo "openssl not found" >&2; exit 2; }
command -v curl >/dev/null 2>&1 || { echo "curl not found" >&2; exit 2; }

TS="$(date +%s)"
NONCE="$(openssl rand -hex 12)"
PATH_PART="$(printf '%s' "$WEBHOOK_URL" | sed -E 's#^https?://[^/]+##')"
if [[ -z "$PATH_PART" ]]; then
  PATH_PART="/"
fi

BODY="$(printf '{"host":"%s","service":"%s","status":"%s","version":"%s","channel":"%s","ts":%s}' \
  "$HOST_ID" "$SERVICE_ID" "$STATUS" "$VERSION" "$CHANNEL" "$TS")"

BODY_HASH="$(printf '%s' "$BODY" | openssl dgst -sha256 -binary | xxd -p -c 256)"
CANONICAL="POST\n${PATH_PART}\n${TS}\n${NONCE}\n${BODY_HASH}"
SIGNATURE="$(printf '%b' "$CANONICAL" | openssl dgst -sha256 -hmac "$SHARED_SECRET" -binary | xxd -p -c 256)"

curl --silent --show-error --fail --max-time 10 \
  -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-OC-Timestamp: ${TS}" \
  -H "X-OC-Nonce: ${NONCE}" \
  -H "X-OC-Signature: ${SIGNATURE}" \
  -d "$BODY"
