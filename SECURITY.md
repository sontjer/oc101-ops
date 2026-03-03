# Security Policy

## Supported Scope

This repository is an operations toolkit. Security-sensitive areas include:
- SSH access to OpenClaw host
- Watchdog shared secret and Telegram bot token
- OpenClaw config backups (especially with `--include-secrets`)

## Secret Handling Rules

- Do not commit any `.env` files with real values.
- Use `examples/*.env.example` templates only.
- Rotate secrets immediately if exposed in logs/chat/commits.
- Store backups containing secrets in encrypted storage.

## Minimum Hardening Baseline

- Use SSH key auth instead of password auth.
- Limit who can run `oc101` on operator machines.
- Keep OpenClaw and system packages updated.
- Run `openclaw security audit` regularly.

## Reporting

If you discover a vulnerability in this toolkit, open a private report to repository maintainers and include:
- impact
- reproduction steps
- proposed mitigation
