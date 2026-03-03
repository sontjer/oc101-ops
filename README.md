# openclaw-oc101-ops

Official-CLI-first operations toolkit for managing OpenClaw over SSH.

中文说明: [README.zh-CN.md](README.zh-CN.md)
Agent prompts (zh-CN): [docs/AGENT_INSTALL_PROMPTS.zh-CN.md](docs/AGENT_INSTALL_PROMPTS.zh-CN.md)

This repository packages the `oc101` wrapper and watchdog scripts that were used to operate an OpenClaw host (`192.168.1.101`) in production-like workflows.

## What This Repo Contains

- `scripts/oc101`: SSH wrapper around official `openclaw` CLI commands.
- `scripts/oc101_watchdog.py`: external heartbeat watchdog with HMAC verification, timeout diagnosis, optional auto-restart, and Telegram alerting.
- `scripts/oc101_watchdog_run.sh`: watchdog launcher that loads an env file.
- `scripts/oc101_heartbeat_sender.sh`: heartbeat sender for OpenClaw host cron.
- `scripts/oc101_watchdog_drill.sh`: timeout drill script with auto-restore.
- `examples/*.env.example`: sanitized configuration templates.

## Design Principles

- Use official `openclaw` commands only.
- Keep monitoring outside the monitored OpenClaw instance.
- Alerting bot must be independent from business bots.
- Prefer safe workflows for upgrades and config changes (backup first).

## Quick Start

1. Clone repository and enter it.
2. Make scripts executable:

```bash
chmod +x scripts/oc101 scripts/oc101_watchdog.py scripts/oc101_watchdog_run.sh scripts/oc101_heartbeat_sender.sh scripts/oc101_watchdog_drill.sh
```

3. Configure SSH access for target host (default: `root@192.168.1.101`).
4. Prepare watchdog env:

```bash
cp examples/oc101_watchdog.env.example examples/oc101_watchdog.env
```

5. Run health checks:

```bash
scripts/oc101 status
scripts/oc101 gateway-status
scripts/oc101 doctor
```

## `oc101` Commands

Status and health:
- `oc101 status`
- `oc101 gateway-status`
- `oc101 doctor [--fix|--repair]`
- `oc101 channels-probe`

Gateway:
- `oc101 gateway-install`
- `oc101 gateway-start`
- `oc101 gateway-stop`
- `oc101 gateway-restart`

Config:
- `oc101 config-get <path>`
- `oc101 config-set <path> <value>`
- `oc101 config-backup [--include-secrets] [--out <dir>]`
- `oc101 config-restore <backup.tgz>`
- `oc101 configure`

Upgrade:
- `oc101 upgrade-status`
- `oc101 upgrade-plan`
- `oc101 upgrade ... --apply`

Security and secrets:
- `oc101 security-audit`
- `oc101 security-audit-fix`
- `oc101 secrets-reload`

Channels and models:
- `oc101 channels-add`
- `oc101 channels-login`
- `oc101 channels-list`
- `oc101 models-set <model>`
- `oc101 models-probe`

## Environment Overrides (oc101)

- `OPENCLAW101_HOST` (default `192.168.1.101`)
- `OPENCLAW101_USER` (default `root`)
- `OPENCLAW101_IDENTITY` (optional `ssh -i`)
- `OPENCLAW101_DEFAULT_IDENTITY` (default `~/.ssh/oc101_ed25519`)
- `OPENCLAW101_PASS` (optional, requires `sshpass`)

## Watchdog Notes

- Endpoint defaults to `0.0.0.0:18891/heartbeat`.
- Heartbeat includes HMAC signature (`X-OC-*` headers).
- Timeout triggers `oc101 status`, `gateway-status`, `doctor`.
- Optional one-shot auto-restart is rate-limited by cooldown/failure counters.
- Alerts are deduplicated by timeout window and send one recovery message after heartbeat resumes.

## Security

- Never commit real tokens/secrets/IDs.
- Rotate leaked bot tokens and shared secrets immediately.
- See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
