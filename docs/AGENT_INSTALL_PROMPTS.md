# Agent Install and Configuration Prompt Templates (Codex / Claude Code / Opencode)

Use these templates to let coding agents install and configure `oc101-ops` automatically.

How to use:
1. Copy one full template into the target agent.
2. Replace placeholders in angle brackets (for example `<TARGET_HOST>`).
3. Ask the agent to execute directly, not just provide a plan.

## 0) Inputs You Must Prepare

- `<REPO_URL>`: repository URL (for example `https://github.com/sontjer/oc101-ops.git`)
- `<INSTALL_DIR>`: install directory (for example `~/oc101-ops`)
- `<TARGET_HOST>`: OpenClaw host IP/domain
- `<TARGET_USER>`: SSH user (usually `root`)
- `<SSH_KEY_PATH>`: SSH private key path
- `<WATCHDOG_BIND_HOST>`: watchdog bind host (usually `0.0.0.0`)
- `<WATCHDOG_BIND_PORT>`: watchdog port (recommended `18891`)
- `<HB_SHARED_SECRET>`: heartbeat HMAC shared secret
- `<TG_BOT_TOKEN>`: Telegram operations bot token
- `<TG_CHAT_ID>`: Telegram chat id for alerts
- `<AUTO_RESTART_ENABLED>`: `true` or `false`

## 1) Codex Prompt Template

```text
Install and configure oc101-ops fully on this machine. Execute commands and edit files directly; do not stop at recommendations.

Goals:
- Install from <REPO_URL> into <INSTALL_DIR>
- Configure scripts/oc101 to connect to <TARGET_USER>@<TARGET_HOST>
- Configure watchdog and heartbeat sender
- Return final verification results

Constraints:
- Use only scripts in this repo and official openclaw CLI
- Do not print secrets in the final summary
- After any service-impacting change, run and report:
  1) scripts/oc101 status
  2) scripts/oc101 gateway-status
  3) scripts/oc101 doctor

Steps:
1. clone/pull <REPO_URL> into <INSTALL_DIR>
2. chmod +x scripts/*
3. Copy examples/oc101_watchdog.env.example to a working env and set:
   - OC101_WD_BIND_HOST=<WATCHDOG_BIND_HOST>
   - OC101_WD_BIND_PORT=<WATCHDOG_BIND_PORT>
   - OC101_WD_SHARED_SECRET=<HB_SHARED_SECRET>
   - OC101_WD_MONITORED_HOST=<TARGET_HOST>
   - OC101_WD_TELEGRAM_BOT_TOKEN=<TG_BOT_TOKEN>
   - OC101_WD_TELEGRAM_CHAT_ID=<TG_CHAT_ID>
   - OC101_WD_AUTO_RESTART_ENABLED=<AUTO_RESTART_ENABLED>
4. Copy examples/oc101_heartbeat_sender.env.example to a working env and set:
   - OC101_HB_WEBHOOK_URL=http://<WATCHDOG_BIND_HOST>:<WATCHDOG_BIND_PORT>/heartbeat
   - OC101_HB_SHARED_SECRET=<HB_SHARED_SECRET>
   - OC101_HB_HOST=<TARGET_HOST>
5. Export or write environment variables for scripts/oc101:
   - OPENCLAW101_HOST=<TARGET_HOST>
   - OPENCLAW101_USER=<TARGET_USER>
   - OPENCLAW101_IDENTITY=<SSH_KEY_PATH>
6. Start watchdog (foreground validation first, then service mode)
7. Configure heartbeat cron on target host (every 15 minutes)
8. Run the 3 health checks and report
9. If failures occur, follow docs/OPERATIONS.md and report fixed state

Final output must include:
- changed files
- service and cron status
- summary of the 3 health checks
- any required manual next steps
```

## 2) Claude Code Prompt Template

```text
Act as an operations execution agent. Install and configure oc101-ops directly in terminal.
Do not stop at planning when actions are executable.

Parameters:
REPO_URL=<REPO_URL>
INSTALL_DIR=<INSTALL_DIR>
TARGET_HOST=<TARGET_HOST>
TARGET_USER=<TARGET_USER>
SSH_KEY_PATH=<SSH_KEY_PATH>
WATCHDOG_BIND_HOST=<WATCHDOG_BIND_HOST>
WATCHDOG_BIND_PORT=<WATCHDOG_BIND_PORT>
HB_SHARED_SECRET=<HB_SHARED_SECRET>
TG_BOT_TOKEN=<TG_BOT_TOKEN>
TG_CHAT_ID=<TG_CHAT_ID>
AUTO_RESTART_ENABLED=<AUTO_RESTART_ENABLED>

Tasks:
1. Install repository and set script execute permissions.
2. Create working env files from examples (do not overwrite example files).
3. Configure SSH env vars required by oc101.
4. Verify ssh + openclaw command execution on target host.
5. Deploy watchdog and heartbeat cron.
6. Run status/gateway-status/doctor and report results.

Requirements:
- Never reveal secrets in final response.
- Report modified file paths.
- If sandbox blocks network/permissions, request escalation and continue.
```

## 3) Opencode Prompt Template

```text
Automate oc101-ops deployment end-to-end with a "running and verifiable" result.

Input variables:
- REPO_URL=<REPO_URL>
- INSTALL_DIR=<INSTALL_DIR>
- TARGET_HOST=<TARGET_HOST>
- TARGET_USER=<TARGET_USER>
- SSH_KEY_PATH=<SSH_KEY_PATH>
- WATCHDOG_BIND_HOST=<WATCHDOG_BIND_HOST>
- WATCHDOG_BIND_PORT=<WATCHDOG_BIND_PORT>
- HB_SHARED_SECRET=<HB_SHARED_SECRET>
- TG_BOT_TOKEN=<TG_BOT_TOKEN>
- TG_CHAT_ID=<TG_CHAT_ID>
- AUTO_RESTART_ENABLED=<AUTO_RESTART_ENABLED>

Execution policy:
- Reuse existing scripts from repository; avoid reimplementation.
- Generate real env files from examples.
- Auto-retry failed commands when appropriate and capture root cause.
- Produce runtime evidence: service status, cron entry, health-check outputs.

Acceptance criteria:
- oc101 status succeeds
- oc101 gateway-status shows running
- oc101 doctor runs without blocking-level issues
- watchdog process/service is healthy
- heartbeat cron is installed
```

## 4) Security Notes

- Never commit real tokens/secrets to git.
- Rotate immediately if leaked: Telegram bot token and HMAC shared secret.
- For internet-facing environments, tighten `tools.profile` and `tools.exec.*` before broad enablement.
