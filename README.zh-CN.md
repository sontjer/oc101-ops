# openclaw-oc101-ops（中文说明）

一个以官方 CLI 为核心的 OpenClaw SSH 运维工具包。
Agent 安装提示词模板（英文）：[docs/AGENT_INSTALL_PROMPTS.md](docs/AGENT_INSTALL_PROMPTS.md)
Agent 安装提示词模板： [docs/AGENT_INSTALL_PROMPTS.zh-CN.md](docs/AGENT_INSTALL_PROMPTS.zh-CN.md)

本仓库整理了 `oc101` 包装脚本和 watchdog 监控脚本，来源于对 OpenClaw 主机（默认示例 `192.168.1.101`）的实际运维流程。

## 关键能力

当 OpenClaw Gateway 崩溃或心跳中断时，watchdog 会通过 Telegram 发送包含诊断上下文的求救告警，便于运维快速介入。

## 仓库内容

- `scripts/oc101`：官方 `openclaw` CLI 的 SSH 包装器。
- `scripts/oc101_watchdog.py`：外部心跳看门狗，支持 HMAC 验签、超时诊断、可选自动重启、Telegram 告警。
- `scripts/oc101_watchdog_run.sh`：加载 env 后启动 watchdog。
- `scripts/oc101_heartbeat_sender.sh`：部署在 OpenClaw 侧的心跳发送脚本（配合 cron）。
- `scripts/oc101_watchdog_drill.sh`：超时演练脚本（自动恢复演练前配置）。
- `examples/*.env.example`：脱敏后的配置模板。

## 设计原则

- 只调用官方 `openclaw` 命令。
- 监控链路与被监控实例分离（外部看门狗）。
- 告警 bot 与业务 bot 分离。
- 升级和配置变更遵循“先备份再执行”。

## 快速开始

1. 克隆仓库并进入目录。
2. 给脚本执行权限：

```bash
chmod +x scripts/oc101 scripts/oc101_watchdog.py scripts/oc101_watchdog_run.sh scripts/oc101_heartbeat_sender.sh scripts/oc101_watchdog_drill.sh
```

3. 准备 SSH（默认目标 `root@192.168.1.101`）。
4. 复制 watchdog 配置模板：

```bash
cp examples/oc101_watchdog.env.example examples/oc101_watchdog.env
```

5. 执行基础健康检查：

```bash
scripts/oc101 status
scripts/oc101 gateway-status
scripts/oc101 doctor
```

## `oc101` 命令清单

状态与诊断：
- `oc101 status`
- `oc101 gateway-status`
- `oc101 doctor [--fix|--repair]`
- `oc101 channels-probe`

网关管理：
- `oc101 gateway-install`
- `oc101 gateway-start`
- `oc101 gateway-stop`
- `oc101 gateway-restart`

配置管理：
- `oc101 config-get <path>`
- `oc101 config-set <path> <value>`
- `oc101 config-backup [--include-secrets] [--out <dir>]`
- `oc101 config-restore <backup.tgz>`
- `oc101 configure`

升级：
- `oc101 upgrade-status`
- `oc101 upgrade-review`
- `oc101 upgrade-plan`
- `OPENCLAW101_UPGRADE_CONFIRM=YES oc101 upgrade ... --apply`

安全与密钥：
- `oc101 security-audit`
- `oc101 security-audit-fix`
- `oc101 secrets-reload`

渠道与模型：
- `oc101 channels-add`
- `oc101 channels-login`
- `oc101 channels-list`
- `oc101 models-set <model>`
- `oc101 models-probe`

## 口头指令与命令行对照

| 口头指令 | 命令行 |
|---|---|
| “现在检查 OpenClaw 状态” | `scripts/oc101 status` |
| “检查网关状态” | `scripts/oc101 gateway-status` |
| “跑一遍 doctor 诊断” | `scripts/oc101 doctor` |
| “探测渠道健康状态” | `scripts/oc101 channels-probe` |
| “重启网关” | `scripts/oc101 gateway-restart` |
| “先备份当前配置” | `scripts/oc101 config-backup` |
| “连 secrets 一起备份” | `scripts/oc101 config-backup --include-secrets` |
| “升级前先调研最新 release 并对比” | `scripts/oc101 upgrade-review` |
| “看升级流程计划” | `scripts/oc101 upgrade-plan` |
| “确认后立刻升级” | `OPENCLAW101_UPGRADE_CONFIRM=YES scripts/oc101 upgrade --apply` |
| “把默认模型切到 MiniMax-M2.5” | `scripts/oc101 models-set minimax-cn/MiniMax-M2.5` |

## 环境变量覆盖（oc101）

- `OPENCLAW101_HOST`（默认 `192.168.1.101`）
- `OPENCLAW101_USER`（默认 `root`）
- `OPENCLAW101_IDENTITY`（可选，等价于 `ssh -i`）
- `OPENCLAW101_DEFAULT_IDENTITY`（默认 `~/.ssh/oc101_ed25519`）
- `OPENCLAW101_PASS`（可选，需安装 `sshpass`）

## Watchdog 说明

- 默认监听：`0.0.0.0:18891/heartbeat`
- 心跳使用 HMAC 签名（`X-OC-*` 头）
- 超时后会执行：`oc101 status`、`gateway-status`、`doctor`
- 若 Gateway 不健康，会通过 Telegram 发送 incident/求救告警并附带诊断结果摘要
- 支持一次性自动重启（受冷却时间和失败次数限制）
- 同一超时窗口仅发一次 incident；恢复后发送 recovered

## 安全建议

- 不要提交真实 token/secret/chat_id。
- 一旦泄露，立即轮换 bot token 和共享密钥。
- 详见 [SECURITY.md](SECURITY.md)。

## 许可证

MIT，见 [LICENSE](LICENSE)。
