#!/usr/bin/env python3
import argparse
import hashlib
import hmac
import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Tuple
from urllib import parse, request


@dataclass
class Config:
    bind_host: str
    bind_port: int
    path: str
    shared_secret: str
    timestamp_skew_seconds: int
    nonce_ttl_seconds: int
    check_interval_seconds: int
    stale_after_seconds: int
    recovery_grace_seconds: int
    restart_cooldown_seconds: int
    max_auto_restart_failures: int
    auto_restart_enabled: bool
    gateway_recheck_delay_seconds: int
    oc101_path: str
    monitored_host: str
    monitored_service: str
    telegram_bot_token: str
    telegram_chat_id: str
    state_file: str
    log_file: str


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes", "on")


def load_config() -> Config:
    script_dir = Path(__file__).resolve().parent
    default_oc101 = str(script_dir / "oc101")
    return Config(
        bind_host=os.environ.get("OC101_WD_BIND_HOST", "0.0.0.0"),
        bind_port=env_int("OC101_WD_BIND_PORT", 18891),
        path=os.environ.get("OC101_WD_PATH", "/heartbeat"),
        shared_secret=os.environ.get("OC101_WD_SHARED_SECRET", ""),
        timestamp_skew_seconds=env_int("OC101_WD_TIMESTAMP_SKEW_SECONDS", 120),
        nonce_ttl_seconds=env_int("OC101_WD_NONCE_TTL_SECONDS", 600),
        check_interval_seconds=env_int("OC101_WD_CHECK_INTERVAL_SECONDS", 60),
        stale_after_seconds=env_int("OC101_WD_STALE_AFTER_SECONDS", 1200),
        recovery_grace_seconds=env_int("OC101_WD_RECOVERY_GRACE_SECONDS", 300),
        restart_cooldown_seconds=env_int("OC101_WD_RESTART_COOLDOWN_SECONDS", 1800),
        max_auto_restart_failures=env_int("OC101_WD_MAX_AUTO_RESTART_FAILURES", 3),
        auto_restart_enabled=env_bool("OC101_WD_AUTO_RESTART_ENABLED", True),
        gateway_recheck_delay_seconds=env_int("OC101_WD_GATEWAY_RECHECK_DELAY_SECONDS", 45),
        oc101_path=os.environ.get("OC101_WD_OC101_PATH", default_oc101),
        monitored_host=os.environ.get("OC101_WD_MONITORED_HOST", "openclaw-host"),
        monitored_service=os.environ.get("OC101_WD_MONITORED_SERVICE", "openclaw-gateway"),
        telegram_bot_token=os.environ.get("OC101_WD_TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.environ.get("OC101_WD_TELEGRAM_CHAT_ID", ""),
        state_file=os.environ.get("OC101_WD_STATE_FILE", os.path.expanduser("~/.codex/tmp/oc101-watchdog-state.json")),
        log_file=os.environ.get("OC101_WD_LOG_FILE", os.path.expanduser("~/.codex/log/oc101-watchdog.log")),
    )


class StateStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        if self.path.exists():
            try:
                self.state = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.state = {}
        else:
            self.state = {}

        self.state.setdefault("heartbeats", {})
        self.state.setdefault("nonces", {})
        self.state.setdefault("alerts", {})

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)

    def with_lock(self):
        return self.lock


def now_ts() -> int:
    return int(time.time())


def ts_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sign(secret: str, method: str, path: str, ts: str, nonce: str, body_hash: str) -> str:
    canonical = f"{method}\n{path}\n{ts}\n{nonce}\n{body_hash}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def run_cmd(cmd: list[str], timeout: int = 90) -> Tuple[int, str]:
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, text=True)
        return proc.returncode, proc.stdout.strip()
    except Exception as exc:
        return 99, f"command failed: {' '.join(cmd)}\n{exc}"


def gateway_is_healthy(output: str, code: int) -> bool:
    if code != 0:
        return False
    text = output.lower()
    return ("running" in text or "state active" in text) and "not running" not in text


def tg_send(cfg: Config, text: str) -> Tuple[bool, str]:
    if not cfg.telegram_bot_token or not cfg.telegram_chat_id:
        return False, "telegram not configured"
    url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    data = parse.urlencode({
        "chat_id": cfg.telegram_chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    try:
        with request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        return True, body
    except Exception as exc:
        return False, str(exc)


class Context:
    def __init__(self, cfg: Config, store: StateStore):
        self.cfg = cfg
        self.store = store
        Path(cfg.log_file).parent.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str) -> None:
        line = f"[{ts_iso(now_ts())}] {msg}\n"
        with open(self.cfg.log_file, "a", encoding="utf-8") as f:
            f.write(line)

    def key(self) -> str:
        return f"{self.cfg.monitored_host}|{self.cfg.monitored_service}"

    def run_oc101(self, subcmd: str) -> Tuple[int, str]:
        return run_cmd([self.cfg.oc101_path, subcmd])

    def diagnose_and_maybe_restart(self, reason: str) -> None:
        key = self.key()
        ts = now_ts()

        with self.store.with_lock():
            alert = self.store.state["alerts"].setdefault(key, {})
            if bool(alert.get("timeout_open", False)):
                return
            last_restart_ts = int(alert.get("last_restart_ts", 0))
            failure_count = int(alert.get("failure_count", 0))

        status_code, status_out = self.run_oc101("status")
        gw_code, gw_out = self.run_oc101("gateway-status")
        doctor_code, doctor_out = self.run_oc101("doctor")
        gw_ok = gateway_is_healthy(gw_out, gw_code)

        did_restart = False
        restart_out = ""
        post_code = -1
        post_out = ""

        if (not gw_ok and self.cfg.auto_restart_enabled and
                ts - last_restart_ts >= self.cfg.restart_cooldown_seconds and
                failure_count < self.cfg.max_auto_restart_failures):
            did_restart = True
            _, restart_out = self.run_oc101("gateway-restart")
            time.sleep(self.cfg.gateway_recheck_delay_seconds)
            post_code, post_out = self.run_oc101("gateway-status")
            gw_ok = gateway_is_healthy(post_out, post_code)

        if not gw_ok:
            failure_count += 1

        lines = [
            f"[WATCHDOG] incident host={self.cfg.monitored_host} service={self.cfg.monitored_service}",
            f"reason={reason}",
            f"status_rc={status_code}",
            f"gateway_rc={gw_code}",
            f"doctor_rc={doctor_code}",
            f"gateway_healthy={gw_ok}",
            f"auto_restart_attempted={did_restart}",
        ]
        if did_restart:
            lines.append(f"post_restart_gateway_rc={post_code}")
        lines.extend([
            "--- status ---",
            status_out[:1200],
            "--- gateway-status ---",
            gw_out[:1200],
            "--- doctor ---",
            doctor_out[:1200],
        ])
        if did_restart:
            lines.extend([
                "--- gateway-restart ---",
                restart_out[:1200],
                "--- post-restart gateway-status ---",
                post_out[:1200],
            ])
        msg = "\n".join(lines)
        ok, tg_info = tg_send(self.cfg, msg)
        self.log(f"incident sent_to_telegram={ok} info={tg_info[:200]}")

        with self.store.with_lock():
            alert = self.store.state["alerts"].setdefault(key, {})
            alert["timeout_open"] = True
            alert["open"] = not gw_ok
            alert["last_alert_ts"] = ts
            alert["failure_count"] = failure_count
            if did_restart:
                alert["last_restart_ts"] = ts
            self.store.save()

    def maybe_send_recovered(self) -> None:
        key = self.key()
        with self.store.with_lock():
            alert = self.store.state["alerts"].setdefault(key, {})
            if not alert.get("timeout_open", False):
                return
            alert["timeout_open"] = False
            alert["open"] = False
            alert["failure_count"] = 0
            alert["last_alert_ts"] = now_ts()
            self.store.save()

        msg = (
            f"[WATCHDOG] recovered host={self.cfg.monitored_host} "
            f"service={self.cfg.monitored_service}"
        )
        ok, tg_info = tg_send(self.cfg, msg)
        self.log(f"recovery sent_to_telegram={ok} info={tg_info[:200]}")


class Handler(BaseHTTPRequestHandler):
    ctx: Context = None

    def _json(self, code: int, payload: Dict):
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        cfg = self.ctx.cfg
        if self.path != cfg.path:
            self._json(404, {"ok": False, "error": "not found"})
            return

        if not cfg.shared_secret:
            self._json(500, {"ok": False, "error": "shared secret not configured"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"ok": False, "error": "invalid content length"})
            return

        body = self.rfile.read(content_length)
        ts_header = self.headers.get("X-OC-Timestamp", "")
        nonce = self.headers.get("X-OC-Nonce", "")
        signature = self.headers.get("X-OC-Signature", "")

        if not ts_header or not nonce or not signature:
            self._json(400, {"ok": False, "error": "missing signature headers"})
            return

        try:
            ts = int(ts_header)
        except ValueError:
            self._json(400, {"ok": False, "error": "invalid timestamp"})
            return

        now = now_ts()
        if abs(now - ts) > cfg.timestamp_skew_seconds:
            self._json(400, {"ok": False, "error": "timestamp skew"})
            return

        expected = sign(cfg.shared_secret, "POST", cfg.path, ts_header, nonce, sha256_hex(body))
        if not hmac.compare_digest(expected, signature):
            self._json(401, {"ok": False, "error": "bad signature"})
            return

        key = f"nonce:{nonce}"
        with self.ctx.store.with_lock():
            nonces = self.ctx.store.state["nonces"]
            prev = int(nonces.get(key, 0))
            if prev and now - prev <= cfg.nonce_ttl_seconds:
                self._json(409, {"ok": False, "error": "replayed nonce"})
                return
            nonces[key] = now
            for k, v in list(nonces.items()):
                if now - int(v) > cfg.nonce_ttl_seconds:
                    del nonces[k]

            hb_key = self.ctx.key()
            self.ctx.store.state["heartbeats"][hb_key] = {
                "last_seen": now,
                "body": body.decode("utf-8", errors="replace")[:2000],
            }
            self.ctx.store.save()

        self.ctx.log(f"heartbeat accepted from {self.client_address[0]}")
        self._json(200, {"ok": True, "ts": now})

    def log_message(self, fmt, *args):
        self.ctx.log("http " + (fmt % args))


def monitor_loop(ctx: Context):
    cfg = ctx.cfg
    key = ctx.key()
    while True:
        now = now_ts()
        stale = False
        last_seen = 0

        with ctx.store.with_lock():
            hb = ctx.store.state["heartbeats"].get(key)
            if hb:
                last_seen = int(hb.get("last_seen", 0))
            if not hb or (now - last_seen > cfg.stale_after_seconds):
                stale = True

        if stale:
            age = now - last_seen if last_seen else -1
            ctx.log(f"stale heartbeat detected age={age}")
            ctx.diagnose_and_maybe_restart(reason=f"heartbeat_timeout age={age}")
        else:
            if now - last_seen <= cfg.recovery_grace_seconds:
                ctx.maybe_send_recovered()

        time.sleep(cfg.check_interval_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenClaw heartbeat watchdog")
    parser.add_argument("--check-config", action="store_true", help="validate config and exit")
    args = parser.parse_args()

    cfg = load_config()
    if not cfg.shared_secret:
        print("OC101_WD_SHARED_SECRET is required", flush=True)
        return 2
    if not Path(cfg.oc101_path).exists():
        print(f"oc101 script not found: {cfg.oc101_path}", flush=True)
        return 2

    store = StateStore(cfg.state_file)
    ctx = Context(cfg, store)
    if args.check_config:
        print("config ok", flush=True)
        return 0

    Handler.ctx = ctx
    server = HTTPServer((cfg.bind_host, cfg.bind_port), Handler)

    t = threading.Thread(target=monitor_loop, args=(ctx,), daemon=True)
    t.start()

    ctx.log(f"watchdog started bind={cfg.bind_host}:{cfg.bind_port}{cfg.path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        ctx.log("watchdog stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
