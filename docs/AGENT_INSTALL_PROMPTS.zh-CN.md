# Agent 安装与配置提示词模板（Codex / Claude Code / Opencode）

下面模板用于让不同代码代理自动完成 `oc101-ops` 的安装与配置。

前提条件：
- 请先确认至少一个运行环境已安装且可用：Claude Code、Codex 或 Opencode。

使用方法：
1. 把模板整段复制给对应代理。
2. 替换其中尖括号变量（如 `<TARGET_HOST>`）。
3. 让代理直接执行，不要只给建议。

## 0) 需要你先准备的参数

- `<REPO_URL>`（非必要）：仓库地址（例如 `https://github.com/sontjer/oc101-ops.git`）
- `<INSTALL_DIR>`：安装目录（例如 `~/oc101-ops`，如果已存在本地仓库目录可直接使用）
- `<TARGET_HOST>`：OpenClaw 主机 IP 或域名
- `<TARGET_USER>`：SSH 用户（通常 `root`）
- `<SSH_KEY_PATH>`：SSH 私钥路径
- `<WATCHDOG_BIND_HOST>`：watchdog 监听地址（常用 `0.0.0.0`）
- `<WATCHDOG_BIND_PORT>`：watchdog 端口（推荐 `18891`）
- `<HB_SHARED_SECRET>`：心跳签名密钥
- `<TG_BOT_TOKEN>`：运维告警机器人 token
- `<TG_CHAT_ID>`：告警接收 chat id
- `<AUTO_RESTART_ENABLED>`：`true` 或 `false`

执行闸门（必须）：
- 在执行任何安装/部署动作前，代理必须先与用户确认以下环境变量。
- 任一缺失时，先向用户提问补齐，再继续：
  - `OPENCLAW101_HOST`（必填）
  - `OPENCLAW101_USER`（默认 `root`）
  - `OPENCLAW101_IDENTITY`（可选；显式私钥路径，优先级最高）
  - `OPENCLAW101_DEFAULT_IDENTITY`（回退私钥路径；默认 `~/.ssh/oc101_ed25519`）
  - `OPENCLAW101_PASS`（可选；需安装 `sshpass`）
  - `OC101_WD_TELEGRAM_BOT_TOKEN`（启用告警时必填）
  - `OC101_WD_TELEGRAM_CHAT_ID`（启用告警时必填）

## 1) Codex 提示词模板

```text
请在当前机器上完整安装并配置 oc101-ops，按下面要求直接执行命令并修改文件，不要只输出建议。

目标：
- 从 <REPO_URL> 安装到 <INSTALL_DIR>（若 <INSTALL_DIR> 已有代码则跳过 clone）
- 配置 scripts/oc101 可连接 <TARGET_USER>@<TARGET_HOST>
- 配置 watchdog 与 heartbeat sender
- 输出最终验证结果

约束：
- 仅使用仓库内脚本与官方 openclaw CLI
- 不把任何 secret 打印到最终总结
- 先确认缺失变量，再执行命令
- 涉及服务变更后，必须执行并汇报：
  1) scripts/oc101 status
  2) scripts/oc101 gateway-status
  3) scripts/oc101 doctor

执行步骤：
1. 若 <INSTALL_DIR> 不存在或为空：clone/pull <REPO_URL> 到 <INSTALL_DIR>；否则直接使用现有目录
2. chmod +x scripts/*
3. 复制 examples/oc101_watchdog.env.example 为可用 env，并写入：
   - OC101_WD_BIND_HOST=<WATCHDOG_BIND_HOST>
   - OC101_WD_BIND_PORT=<WATCHDOG_BIND_PORT>
   - OC101_WD_SHARED_SECRET=<HB_SHARED_SECRET>
   - OC101_WD_MONITORED_HOST=<TARGET_HOST>
   - OC101_WD_TELEGRAM_BOT_TOKEN=<TG_BOT_TOKEN>
   - OC101_WD_TELEGRAM_CHAT_ID=<TG_CHAT_ID>
   - OC101_WD_AUTO_RESTART_ENABLED=<AUTO_RESTART_ENABLED>
4. 复制 examples/oc101_heartbeat_sender.env.example 为可用 env，并写入：
   - OC101_HB_WEBHOOK_URL=http://<WATCHDOG_BIND_HOST>:<WATCHDOG_BIND_PORT>/heartbeat
   - OC101_HB_SHARED_SECRET=<HB_SHARED_SECRET>
   - OC101_HB_HOST=<TARGET_HOST>
5. 导出或写入环境变量供 scripts/oc101 使用：
   - OPENCLAW101_HOST=<TARGET_HOST>
   - OPENCLAW101_USER=<TARGET_USER>
   - OPENCLAW101_IDENTITY=<SSH_KEY_PATH>
6. 启动 watchdog（前台先跑一次验证，再改为服务模式）
7. 在目标机配置 heartbeat cron（每 15 分钟）
8. 运行健康检查三连并汇报
9. 若失败，按 docs/OPERATIONS.md 排障并给出修复后结果

最后输出：
- 改动文件列表
- 服务与 cron 状态
- 三条健康检查命令结果摘要
- 下一步人工操作建议（如需）
```

## 2) Claude Code 提示词模板

```text
请作为运维执行代理，直接在终端完成 oc101-ops 的安装和配置。
不要停留在计划，遇到可执行步骤就立即执行。

参数：
REPO_URL=<REPO_URL，可留空>
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

任务：
1. 若本地无代码则安装仓库；若已有则直接赋权 scripts。
2. 基于 examples 生成可用 env 文件（不要覆盖 example 文件）。
3. 配置 oc101 所需 SSH 环境变量。
4. 验证 ssh 到目标主机可执行 openclaw 命令。
5. 部署 watchdog + heartbeat cron。
6. 执行 status/gateway-status/doctor 并给出结果。

要求：
- 不泄露 secret 到最终回复。
- 修改文件后说明路径。
- 如果网络/权限被沙箱阻断，自动请求提权后继续。
```

## 3) Opencode 提示词模板

```text
请自动化执行 oc101-ops 部署，目标是“可持续运行 + 可验证”。

输入变量：
- REPO_URL=<REPO_URL，可留空>
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

执行规范：
- 优先使用仓库已有脚本，不重复造轮子。
- 配置文件从 examples 复制生成。
- 命令失败要自动重试，并记录根因。
- 完成后输出“运行态证据”：服务状态、cron 条目、健康检查结果。

验收标准：
- oc101 status 成功
- oc101 gateway-status 显示 running
- oc101 doctor 可执行且无阻断级错误
- watchdog 进程/服务正常
- heartbeat cron 已安装
```

## 4) 安全提醒

- 不要把真实 token/secret 提交到 git。
- 发现泄露立即轮换：Telegram bot token + HMAC shared secret。
- 若目标环境是公网，建议先把 `tools.profile` 和 `tools.exec.*` 策略收敛再开放。
