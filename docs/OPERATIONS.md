# Operations Checklist

## Routine checks

```bash
scripts/oc101 status
scripts/oc101 gateway-status
scripts/oc101 doctor
```

## Before upgrade/config change

```bash
scripts/oc101 upgrade-status
scripts/oc101 config-backup
scripts/oc101 upgrade-plan
```

## After upgrade/config change

```bash
scripts/oc101 status
scripts/oc101 gateway-status
scripts/oc101 doctor
```

## Heartbeat anti-regression checks

1. Verify deployed cron uses `set -a` style:

```bash
ssh root@<target-host> 'crontab -l | grep -F "/root/.openclaw/ops/heartbeat_sender.sh"'
```

Expected line:

```bash
*/15 * * * * set -a; . /root/.openclaw/ops/heartbeat_sender.env; set +a; /root/.openclaw/ops/heartbeat_sender.sh >> /root/.openclaw/ops/heartbeat_sender.log 2>&1
```

2. Verify required env keys are exported:

```bash
ssh root@<target-host> 'grep -nE "^(export )?OC101_HB_(WEBHOOK_URL|SHARED_SECRET)=" /root/.openclaw/ops/heartbeat_sender.env'
```

3. Manual one-shot sender test:

```bash
ssh root@<target-host> 'set -a; . /root/.openclaw/ops/heartbeat_sender.env; set +a; /root/.openclaw/ops/heartbeat_sender.sh'
```

4. Confirm watchdog receives `200`:

```bash
tail -n 50 ~/.codex/log/oc101-watchdog.log | grep -E 'POST /heartbeat|heartbeat accepted| 200 -' | tail -n 5
```

## Git boundary checklist (avoid config drift)

These runtime files are not in this repo working directory and must be managed separately:
- `/root/.openclaw/ops/heartbeat_sender.env`
- root user crontab on target host
- watchdog systemd unit files and overrides

Before/after each change window, capture:

```bash
ssh root@<target-host> 'crontab -l'
ssh root@<target-host> 'sha256sum /root/.openclaw/ops/heartbeat_sender.sh /root/.openclaw/ops/heartbeat_sender.env'
systemctl cat oc101-watchdog.service
```

Or run the bundled one-shot audit:

```bash
scripts/oc101_runtime_audit.sh
```
