"""标准时钟系统对接后端模块（母钟 UDP 配置持久化 + MySQL 台账配置 + 状态/WebSocket）。

设计原则：
1. 对接参数（母钟 IP/端口/超时/时区 + 子钟 MySQL 主机/库/视图/账号/密码）全部持久化到 SQLite `clock_settings` 表。
2. 密码使用基于 JWT_SECRET 派生的密钥加密落库，GET 接口不回传明文密码，仅回传 `hasMysqlPassword` 标记。
3. 未安装 pymysql 时优雅降级为 TCP 端口探活，不抛 500 异常。
"""
from __future__ import annotations

import base64
import hashlib
import socket
import struct
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.clock_ntp import build_frame, parse_frame, split_frames

try:
    from cryptography.fernet import Fernet
except Exception:  # pragma: no cover
    Fernet = None  # type: ignore

try:
    import pymysql  # type: ignore
except Exception:  # pragma: no cover
    pymysql = None  # type: ignore

router = APIRouter(prefix="/api/clock", tags=["clock"])

_db_hook = None
_audit_hook = None
_secret_key = "development-only-change-me"
_drift_history: deque[dict[str, Any]] = deque(maxlen=30)
_protocol_logs: deque[dict[str, Any]] = deque(maxlen=40)

CLOCK_SETTINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS clock_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    master_ip TEXT NOT NULL DEFAULT '192.168.7.2',
    master_port INTEGER NOT NULL DEFAULT 123,
    local_port INTEGER NOT NULL DEFAULT 0,
    timeout_s REAL NOT NULL DEFAULT 4.0,
    retries INTEGER NOT NULL DEFAULT 2,
    timezone INTEGER NOT NULL DEFAULT 8,
    mysql_host TEXT NOT NULL DEFAULT '',
    mysql_port INTEGER NOT NULL DEFAULT 3306,
    mysql_database TEXT NOT NULL DEFAULT 'clock',
    mysql_view TEXT NOT NULL DEFAULT 'clock_view',
    mysql_user TEXT NOT NULL DEFAULT '',
    mysql_password_enc TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);
"""


def configure(db_hook, audit_hook, secret_key: str) -> None:
    global _db_hook, _audit_hook, _secret_key
    _db_hook = db_hook
    _audit_hook = audit_hook
    _secret_key = secret_key or _secret_key
    init_schema()


def init_schema() -> None:
    if not _db_hook:
        return
    with _db_hook() as conn:
        conn.executescript(CLOCK_SETTINGS_SCHEMA)
        row = conn.execute("SELECT id FROM clock_settings WHERE id = 1").fetchone()
        if not row:
            conn.execute(
                """INSERT INTO clock_settings (
                    id, master_ip, master_port, local_port, timeout_s, retries, timezone,
                    mysql_host, mysql_port, mysql_database, mysql_view, mysql_user, mysql_password_enc, updated_at
                ) VALUES (1, '192.168.7.2', 123, 0, 4.0, 2, 8, '', 3306, 'clock', 'clock_view', '', '', ?)""",
                (_now(),),
            )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fernet() -> Any:
    if Fernet is None:
        return None
    digest = hashlib.sha256(_secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt_secret(plain: str) -> str:
    if not plain:
        return ""
    f = _fernet()
    if f is None:
        return base64.b64encode(plain.encode("utf-8")).decode("ascii")
    return f.encrypt(plain.encode("utf-8")).decode("ascii")


def _decrypt_secret(cipher: str) -> str:
    if not cipher:
        return ""
    f = _fernet()
    if f is None:
        try:
            return base64.b64decode(cipher.encode("ascii")).decode("utf-8")
        except Exception:
            return ""
    try:
        return f.decrypt(cipher.encode("ascii")).decode("utf-8")
    except Exception:
        return ""


class ClockSettingsPayload(BaseModel):
    masterIp: str = Field(default="192.168.7.2", max_length=128)
    masterPort: int = Field(default=123, ge=1, le=65535)
    localPort: int = Field(default=0, ge=0, le=65535)
    timeoutS: float = Field(default=4.0, gt=0, le=30)
    retries: int = Field(default=2, ge=0, le=10)
    timezone: int = Field(default=8, ge=-12, le=12)
    mysqlHost: str = Field(default="", max_length=128)
    mysqlPort: int = Field(default=3306, ge=1, le=65535)
    mysqlDatabase: str = Field(default="clock", max_length=128)
    mysqlView: str = Field(default="clock_view", max_length=128)
    mysqlUser: str = Field(default="", max_length=128)
    mysqlPassword: str = Field(default="", max_length=256)
    keepExistingPassword: bool = Field(default=True)


class ClockCommandPayload(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    addr: int | None = None
    bus_type: int | None = None
    start: bool | None = None
    on: bool | None = None
    mode: int | None = None
    volume: int | None = None
    hours: int | None = None
    minutes: int | None = None
    seconds: int | None = None
    timezone: int | None = None
    interval_s: int | None = None
    offset_s: int | None = None
    link: int | None = None
    clock_type: int | None = None
    seg1: list[int] | None = None
    seg2: list[int] | None = None
    seg3: list[int] | None = None


def _load_row() -> dict[str, Any]:
    with _db_hook() as conn:
        row = conn.execute("SELECT * FROM clock_settings WHERE id = 1").fetchone()
    return dict(row) if row else {}


def _row_to_public(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "masterIp": row.get("master_ip") or "192.168.7.2",
        "masterPort": int(row.get("master_port") or 123),
        "localPort": int(row.get("local_port") or 0),
        "timeoutS": float(row.get("timeout_s") or 4.0),
        "retries": int(row.get("retries") if row.get("retries") is not None else 2),
        "timezone": int(row.get("timezone") if row.get("timezone") is not None else 8),
        "mysqlHost": row.get("mysql_host") or "",
        "mysqlPort": int(row.get("mysql_port") or 3306),
        "mysqlDatabase": row.get("mysql_database") or "clock",
        "mysqlView": row.get("mysql_view") or "clock_view",
        "mysqlUser": row.get("mysql_user") or "",
        "hasMysqlPassword": bool(row.get("mysql_password_enc")),
        "updatedAt": row.get("updated_at") or "",
    }


def _build_udp_frame(addr: int, cmd: int, data: bytes = b"") -> bytes:
    """构建 TimeMaster 0xDD..0xDA 协议帧。"""
    body = bytes([addr & 0xFF, cmd & 0xFF]) + data
    length = len(body)
    checksum = (length + sum(body)) & 0xFF
    return bytes([0xDD, length]) + body + bytes([checksum, 0xDA])


def _probe_udp_master(ip: str, port: int, local_port: int, timeout_s: float) -> dict[str, Any]:
    if not ip:
        return {"reachable": False, "error": "未配置母钟 IP"}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(min(max(timeout_s, 0.5), 3.0))
    t0 = time.perf_counter()
    try:
        if local_port and local_port > 0:
            sock.bind(("0.0.0.0", local_port))

        def _query_func(func_code: int, payload: bytes, cmd_name: str) -> dict[int, bytes]:
            tx = build_frame(0xFF, func_code, payload)
            _protocol_logs.append({
                "direction": "TX",
                "time": time.strftime("%H:%M:%S"),
                "cmdName": cmd_name,
                "rawHex": tx.hex(" ").upper(),
                "desc": f"发送至 {ip}:{port}",
            })
            sock.sendto(tx, (ip, port))
            raw, _ = sock.recvfrom(1024)
            _protocol_logs.append({
                "direction": "RX",
                "time": time.strftime("%H:%M:%S"),
                "cmdName": cmd_name,
                "rawHex": raw.hex(" ").upper(),
                "desc": f"来自 {ip}:{port} 应答",
            })
            parsed_map: dict[int, bytes] = {}
            for frame in split_frames(raw):
                try:
                    info = parse_frame(frame)
                    parsed_map[info["func"]] = info["data"]
                except Exception:
                    continue
            return parsed_map

        sat_map = _query_func(0x15, b"\x00", "0x15 查询卫星数")
        sat = sat_map[0x15][0] if 0x15 in sat_map and sat_map[0x15] else None

        time_map = _query_func(0x10, b"\x00", "0x10 查询母钟时间")
        master_unix_s = None
        drift_ms = None
        if 0x10 in time_map and len(time_map[0x10]) >= 4:
            master_unix_s = struct.unpack(">I", time_map[0x10][:4])[0]
            drift_ms = round((time.time() - master_unix_s) * 1000, 1)

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "reachable": True,
            "latency_ms": latency_ms,
            "satellite_count": sat,
            "master_unix_s": master_unix_s,
            "drift_ms": drift_ms,
        }
    except socket.timeout:
        return {"reachable": False, "error": f"UDP 响应超时 ({ip}:{port})"}
    except OSError as exc:
        return {"reachable": False, "error": str(exc)}
    finally:
        sock.close()


def _probe_mysql(host: str, port: int, db_name: str, view_name: str, user: str, password: str) -> dict[str, Any]:
    host = (host or "").strip()
    if not host:
        return {"reachable": False, "skipped": True, "error": "未配置 MySQL 主机"}
    if pymysql is not None and user:
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                charset="gb18030",
                connect_timeout=3,
                read_timeout=3,
            )
            try:
                safe_view = "".join(ch for ch in (view_name or "clock_view") if ch.isalnum() or ch == "_")
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM `{safe_view}`")
                    cnt = int(cur.fetchone()[0])
                return {"reachable": True, "count": cnt}
            finally:
                conn.close()
        except Exception:
            return {"reachable": False, "error": "连接数据库失败"}

    # 无 pymysql 时做 TCP 端口可达性检测
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.5)
    try:
        sock.connect((host, port))
        return {"reachable": True, "count": 0, "note": "TCP 端口连通（后端未安装 pymysql 驱动，未执行 SQL 计数）"}
    except OSError as exc:
        return {"reachable": False, "error": f"MySQL TCP 不可达 ({host}:{port}): {exc}"}
    finally:
        sock.close()


@router.get("/settings")
def get_clock_settings() -> dict[str, Any]:
    return _row_to_public(_load_row())


@router.post("/settings")
def save_clock_settings(body: ClockSettingsPayload) -> dict[str, Any]:
    current = _load_row()
    if body.mysqlPassword:
        pwd_enc = _encrypt_secret(body.mysqlPassword)
    elif body.keepExistingPassword and current.get("mysql_password_enc"):
        pwd_enc = current["mysql_password_enc"]
    else:
        pwd_enc = ""

    ts = _now()
    with _db_hook() as conn:
        conn.execute(
            """
            UPDATE clock_settings SET
                master_ip = ?, master_port = ?, local_port = ?, timeout_s = ?, retries = ?, timezone = ?,
                mysql_host = ?, mysql_port = ?, mysql_database = ?, mysql_view = ?, mysql_user = ?,
                mysql_password_enc = ?, updated_at = ?
            WHERE id = 1
            """,
            (
                body.masterIp.strip(),
                body.masterPort,
                body.localPort,
                body.timeoutS,
                body.retries,
                body.timezone,
                body.mysqlHost.strip(),
                body.mysqlPort,
                body.mysqlDatabase.strip() or "clock",
                body.mysqlView.strip() or "clock_view",
                body.mysqlUser.strip(),
                pwd_enc,
                ts,
            ),
        )
    if _audit_hook:
        _audit_hook("clock_settings", "CLOCK_SETTINGS", "save", "SUCCESS", {"masterIp": body.masterIp, "mysqlHost": body.mysqlHost})
    return {"ok": True, **_row_to_public(_load_row())}


@router.post("/settings/test")
def test_clock_settings(body: ClockSettingsPayload) -> dict[str, Any]:
    current = _load_row()
    pwd = body.mysqlPassword or (_decrypt_secret(current.get("mysql_password_enc", "")) if body.keepExistingPassword else "")
    udp_res = _probe_udp_master(body.masterIp.strip(), body.masterPort, body.localPort, min(body.timeoutS, 2.5))
    mysql_res = _probe_mysql(
        body.mysqlHost.strip(),
        body.mysqlPort,
        body.mysqlDatabase.strip() or "clock",
        body.mysqlView.strip() or "clock_view",
        body.mysqlUser.strip(),
        pwd,
    )
    return {"udp": udp_res, "mysql": mysql_res}


@router.get("/status")
def clock_status() -> dict[str, Any]:
    row = _load_row()
    pub = _row_to_public(row)
    udp_res = _probe_udp_master(pub["masterIp"], pub["masterPort"], pub["localPort"], min(pub["timeoutS"], 1.5))
    if udp_res.get("reachable") and udp_res.get("drift_ms") is not None:
        _drift_history.append({
            "time": time.strftime("%H:%M:%S"),
            "driftMs": udp_res["drift_ms"],
            "sat": udp_res.get("satellite_count"),
        })
    return {
        "online": bool(udp_res.get("reachable")),
        "mysqlConfigured": bool(pub["mysqlHost"]),
        "satelliteCount": udp_res.get("satellite_count"),
        "masterUnixS": udp_res.get("master_unix_s"),
        "platformDriftMs": udp_res.get("drift_ms"),
        "protocolLogs": list(_protocol_logs),
        "driftHistory": list(_drift_history),
    }


@router.get("/subclocks")
def clock_subclocks() -> dict[str, Any]:
    row = _load_row()
    host = (row.get("mysql_host") or "").strip()
    if not host:
        return {"configured": False, "online": False, "items": []}
    if pymysql is None:
        return {"configured": True, "online": False, "items": [], "error": "后端未安装 pymysql 驱动，无法直连 MySQL 读取子钟台账"}
    pwd = _decrypt_secret(row.get("mysql_password_enc", ""))
    try:
        conn = pymysql.connect(
            host=host,
            port=int(row.get("mysql_port") or 3306),
            user=row.get("mysql_user") or "",
            password=pwd,
            database=row.get("mysql_database") or "clock",
            charset="gb18030",
            connect_timeout=3,
            read_timeout=3,
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            safe_view = "".join(ch for ch in (row.get("mysql_view") or "clock_view") if ch.isalnum() or ch == "_")
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM `{safe_view}` ORDER BY id ASC LIMIT 500")
                items = []
                for row_item in cur.fetchall():
                    d = dict(row_item)
                    d.setdefault("screenPower", True)
                    items.append(d)
            return {"configured": True, "online": True, "items": items}
        finally:
            conn.close()
    except Exception:
        return {"configured": True, "online": False, "items": [], "error": "连接数据库失败"}


def _send_udp_cmd(
    ip: str,
    port: int,
    local_port: int,
    timeout_s: float,
    addr: int,
    func: int,
    data: bytes,
    cmd_name: str,
) -> dict[str, Any]:
    """Send a single TimeMaster 0xDD..0xDA UDP command frame and validate reply (with busy/timeout retry)."""
    if not ip:
        raise HTTPException(status_code=400, detail="未配置母钟 IP")

    last_exc: Exception | None = None
    for attempt in range(6):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(min(max(timeout_s, 0.8), 4.0))
        t0 = time.perf_counter()
        try:
            if local_port and local_port > 0:
                sock.bind(("0.0.0.0", local_port))
            tx = build_frame(addr, func, data)
            _protocol_logs.append({
                "direction": "TX",
                "time": time.strftime("%H:%M:%S"),
                "cmdName": cmd_name,
                "rawHex": tx.hex(" ").upper(),
                "desc": f"发送至 {ip}:{port} (addr=#{addr})",
            })
            sock.sendto(tx, (ip, port))
            raw, _ = sock.recvfrom(1024)
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            _protocol_logs.append({
                "direction": "RX",
                "time": time.strftime("%H:%M:%S"),
                "cmdName": cmd_name,
                "rawHex": raw.hex(" ").upper(),
                "desc": f"来自 {ip}:{port} 应答 ({latency_ms}ms)",
            })
            parsed_frames = []
            busy = False
            for frame in split_frames(raw):
                try:
                    info = parse_frame(frame)
                    parsed_frames.append(info)
                    if info["func"] == 0x11:
                        busy = True
                    elif info["func"] == 0x12:
                        raise HTTPException(status_code=502, detail="母钟返回校验和错误 (0x12)")
                except HTTPException:
                    raise
                except Exception:
                    continue
            if busy:
                if attempt < 5:
                    time.sleep(0.45)
                    continue
                raise HTTPException(status_code=409, detail="母钟当前忙 (0x11)，请稍后重试")
            return {"latency_ms": latency_ms, "rx_hex": raw.hex(" ").upper(), "frames": parsed_frames}
        except socket.timeout as exc:
            last_exc = exc
            if attempt < 5:
                time.sleep(0.25)
                continue
            raise HTTPException(status_code=504, detail=f"母钟 UDP 通信超时 ({ip}:{port})") from exc
        except OSError as exc:
            raise HTTPException(status_code=502, detail=f"母钟 UDP 发送失败: {exc}") from exc
        finally:
            sock.close()
    raise HTTPException(status_code=504, detail=f"母钟 UDP 通信超时: {last_exc}")


@router.post("/sync")
def clock_sync_now() -> dict[str, Any]:
    row = _load_row()
    pub = _row_to_public(row)
    tz = int(pub.get("timezone") if pub.get("timezone") is not None else 8)
    _send_udp_cmd(pub["masterIp"], pub["masterPort"], pub["localPort"], pub["timeoutS"], 0xFF, 0x0D, bytes([tz & 0xFF]), f"0x0D 全网授时同步 (UTC{tz:+d})")
    udp_res = _probe_udp_master(pub["masterIp"], pub["masterPort"], pub["localPort"], min(pub["timeoutS"], 2.0))
    return {
        "ok": True,
        "master_unix_s": udp_res.get("master_unix_s"),
        "satelliteCount": udp_res.get("satellite_count"),
        "latency_ms": udp_res.get("latency_ms"),
    }


@router.post("/command")
def clock_command(body: ClockCommandPayload) -> dict[str, Any]:
    row = _load_row()
    pub = _row_to_public(row)
    ip, port, local_port, timeout_s = pub["masterIp"], pub["masterPort"], pub["localPort"], pub["timeoutS"]
    act = body.action.strip().lower()
    addr = int(body.addr or 0)

    point_actions = {"set_screen", "set_brightness", "set_audio", "set_timer", "point_timer", "add", "remove"}
    if act in point_actions and not (1 <= addr <= 254):
        raise HTTPException(status_code=400, detail=f"定点指令 {act} 的子钟地址必须在 1 ~ 254 之间 (当前 {addr})")

    if act == "set_screen":
        on = bool(body.on)
        res = _send_udp_cmd(ip, port, local_port, timeout_s, addr, 0x04, bytes([1 if on else 2]), f"0x04 子钟 #{addr} {'亮屏' if on else '熄屏'}")
    elif act == "set_brightness":
        s1 = body.seg1 or [6, 0, 18, 0, 5]
        s2 = body.seg2 or [18, 0, 23, 59, 3]
        payload = bytes([
            int(s1[0]) & 0xFF, int(s1[1]) & 0xFF, int(s1[2]) & 0xFF, int(s1[3]) & 0xFF, max(1, min(5, int(s1[4]))),
            int(s2[0]) & 0xFF, int(s2[1]) & 0xFF, int(s2[2]) & 0xFF, int(s2[3]) & 0xFF, max(1, min(5, int(s2[4]))),
        ])
        res = _send_udp_cmd(ip, port, local_port, timeout_s, addr, 0x06, payload, f"0x06 子钟 #{addr} 分时段亮度")
    elif act == "set_audio":
        on = bool(body.on)
        vol = max(1, min(10, int(body.volume or 1))) if on else 0
        res = _send_udp_cmd(ip, port, local_port, timeout_s, addr, 0x07, bytes([1 if on else 2, vol]), f"0x07 子钟 #{addr} 音频{'开' if on else '关'} 音量{vol}")
    elif act == "set_timer":
        mode = int(body.mode or 3)
        h = min(99, max(0, int(body.hours or 0)))
        m = min(59, max(0, int(body.minutes or 0)))
        s = min(59, max(0, int(body.seconds or 0)))
        res = _send_udp_cmd(ip, port, local_port, timeout_s, addr, 0x01, bytes([mode & 0xFF, h, m, s]), f"0x01 子钟 #{addr} 计时模式 {mode}")
    elif act == "broadcast_timer":
        bus = int(body.bus_type or 1)
        start = bool(body.start)
        val = ((bus & 0x0F) << 4) | (1 if start else 0)
        res = _send_udp_cmd(ip, port, local_port, timeout_s, 0xFF, 0x0E, bytes([val]), f"0x0E 总线 {bus} 广播{'开始' if start else '恢复'}")
    elif act == "point_timer":
        start = bool(body.start)
        res = _send_udp_cmd(ip, port, local_port, timeout_s, addr, 0x0F, bytes([1 if start else 0]), f"0x0F 子钟 #{addr} 定点{'开始' if start else '恢复'}")
    elif act == "set_timezone":
        tz = int(body.timezone if body.timezone is not None else 8)
        res = _send_udp_cmd(ip, port, local_port, timeout_s, 0xFF, 0x0D, bytes([tz & 0xFF]), f"0x0D 设置时区 UTC{tz:+d}")
    elif act == "set_interval":
        interval_s = max(60, min(65535, int(body.interval_s or 3600)))
        res = _send_udp_cmd(ip, port, local_port, timeout_s, 0xFF, 0x08, struct.pack(">H", interval_s), f"0x08 校时间隔 {interval_s}s")
    else:
        raise HTTPException(status_code=400, detail=f"不支持的时钟控制指令: {body.action}")

    return {"ok": True, "action": act, "addr": addr, "latency_ms": res["latency_ms"], "rx_hex": res["rx_hex"]}
