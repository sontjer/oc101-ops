---
name: openclaw-101
summary: One-command SSH templates to diagnose and maintain OpenClaw using official OpenClaw CLI commands.
---

# OpenClaw 101 Skill (Repository Edition)

This skill exposes `scripts/oc101` and watchdog helper scripts.

## Entry

- `scripts/oc101`

## Principle

- Official `openclaw` CLI only.
- SSH wrapper only; no private APIs.

## Recommended Sequence

1. `scripts/oc101 status`
2. `scripts/oc101 gateway-status`
3. `scripts/oc101 doctor`
4. `scripts/oc101 channels-probe`

## Safety

- Use `scripts/oc101 upgrade --apply` only after review + backup.
- Keep watchdog bot independent from business bot.
