# openclaw-oc101-ops

Operational toolkit for coding agent managing OpenClaw over SSH.

## Documentation

- Agent prompts (English): [docs/AGENT_INSTALL_PROMPTS.md](docs/AGENT_INSTALL_PROMPTS.md)
- Chinese README: [README.zh-CN.md](README.zh-CN.md)
- Agent prompts (Chinese): [docs/AGENT_INSTALL_PROMPTS.zh-CN.md](docs/AGENT_INSTALL_PROMPTS.zh-CN.md)

Tip: send the English prompt to your coding agent and let it install for you.

This repository packages the `oc101` wrapper and watchdog scripts for production-oriented OpenClaw operations.

## Key Capability

When the OpenClaw Gateway crashes or loses heartbeat, watchdog sends Telegram SOS alerts with diagnostic context so operators can respond quickly.
It also performs state analysis, root-cause diagnosis, remediation actions, and controlled restart operations.

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

## Prerequisite

Before using this toolkit for OpenClaw maintenance automation, confirm at least one supported coding agent runtime is already installed and usable on your operator machine:
- Claude Code
- Codex
- Opencode

## Quick Start

1. Clone repository and enter it.
2. Make scripts executable:

```bash
chmod +x scripts/oc101 scripts/oc101_watchdog.py scripts/oc101_watchdog_run.sh scripts/oc101_heartbeat_sender.sh scripts/oc101_watchdog_drill.sh
```

3. Configure SSH access for your target host.
4. Set required runtime env vars (at minimum):

```bash
export OPENCLAW101_HOST=<target-host>
```
5. Prepare watchdog env:

```bash
cp examples/oc101_watchdog.env.example examples/oc101_watchdog.env
```

6. Run health checks:

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
- `oc101 upgrade-review`
- `oc101 upgrade-plan`
- `OPENCLAW101_UPGRADE_CONFIRM=YES oc101 upgrade ... --apply`

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

## Spoken Instruction to CLI Mapping

| Spoken instruction | CLI command |
|---|---|
| "Check OpenClaw status now" | `scripts/oc101 status` |
| "Check gateway status" | `scripts/oc101 gateway-status` |
| "Run a doctor check" | `scripts/oc101 doctor` |
| "Probe channel health" | `scripts/oc101 channels-probe` |
| "Restart gateway" | `scripts/oc101 gateway-restart` |
| "Backup current config first" | `scripts/oc101 config-backup` |
| "Backup including secrets" | `scripts/oc101 config-backup --include-secrets` |
| "Review latest release and compare before upgrade" | `scripts/oc101 upgrade-review` |
| "Show upgrade plan" | `scripts/oc101 upgrade-plan` |
| "Confirm and upgrade now" | `OPENCLAW101_UPGRADE_CONFIRM=YES scripts/oc101 upgrade --apply` |
| "Set default model to MiniMax-M2.5" | `scripts/oc101 models-set minimax-cn/MiniMax-M2.5` |

## Environment Overrides (oc101)

- `OPENCLAW101_HOST` (required)
- `OPENCLAW101_USER` (default `root`)
- `OPENCLAW101_IDENTITY` (optional; explicit key path via `ssh -i`, takes precedence)
- `OPENCLAW101_DEFAULT_IDENTITY` (fallback key path used only when `OPENCLAW101_IDENTITY` is unset; default `~/.ssh/oc101_ed25519`)
- `OPENCLAW101_PASS` (optional, requires `sshpass`)

Watchdog alert env (Telegram):
- `OC101_WD_TELEGRAM_BOT_TOKEN` (required for Telegram alerts)
- `OC101_WD_TELEGRAM_CHAT_ID` (required for Telegram alerts)
- Must use an independent operations bot token, not the same bot token used by the monitored OpenClaw business channel/bot.

## Watchdog Notes

- Endpoint defaults to `0.0.0.0:18891/heartbeat`.
- Heartbeat includes HMAC signature (`X-OC-*` headers).
- Timeout triggers `oc101 status`, `gateway-status`, `doctor`.
- If Gateway is unhealthy, Telegram receives an incident/SOS alert with health-check outputs.
- Optional one-shot auto-restart is rate-limited by cooldown/failure counters.
- Alerts are deduplicated by timeout window and send one recovery message after heartbeat resumes.

## Security

- Never commit real tokens/secrets/IDs.
- Rotate leaked bot tokens and shared secrets immediately.
- See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
