"""Read-only MySQL client for the vendor's clock_view ledger (charset gb18030)."""
from __future__ import annotations

import base64
import hashlib
import re
from typing import Any

import pymysql

_IDENT_RE = re.compile(r"^[a-zA-Z0-9_]{1,64}$")


def _derive_key(secret: str) -> bytes:
    return hashlib.sha256(secret.encode("utf-8")).digest()


def encrypt_password(plain: str, secret: str) -> str:
    if not plain:
        return ""
    key = _derive_key(secret)
    raw = plain.encode("utf-8")
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return "enc:" + base64.urlsafe_b64encode(xored).decode("ascii")


def decrypt_password(stored: str, secret: str) -> str:
    if not stored:
        return ""
    if not stored.startswith("enc:"):
        return stored
    key = _derive_key(secret)
    raw = base64.urlsafe_b64decode(stored[4:].encode("ascii"))
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return plain.decode("utf-8")


def _safe_ident(name: str, default: str) -> str:
    val = (name or default).strip()
    if not _IDENT_RE.match(val):
        raise ValueError(f"非法数据库标识符: {val}")
    return val


def _connect(cfg: dict[str, Any], secret: str):
    host = (cfg.get("mysqlHost") or "").strip()
    if not host:
        raise ValueError("尚未配置子钟 MySQL 主机 IP")
    port = int(cfg.get("mysqlPort") or 3306)
    db_name = _safe_ident(cfg.get("mysqlDatabase") or "clock", "clock")
    user = (cfg.get("mysqlUser") or "").strip()
    password = decrypt_password(cfg.get("mysqlPassword") or "", secret)
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        charset="gb18030",
        connect_timeout=4,
        read_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )


def _to_int(val: Any, default: int) -> int:
    s = str(val if val is not None else "").strip()
    if s.lstrip("-").isdigit():
        return int(s)
    return default


def _parse_bright(val: Any, default: int = 5) -> int:
    """Parse integer brightness or time-segmented rule like '08:00-21:00->5,21:00-08:00->5'."""
    s = str(val if val is not None else "").strip()
    if not s:
        return default
    if s.lstrip("-").isdigit():
        return int(s)
    import datetime as _dt
    import re as _re
    now_hm = _dt.datetime.now().strftime("%H:%M")
    matches = _re.findall(r"(\d{2}:\d{2})-(\d{2}:\d{2})->(\d+)", s)
    for start_hm, end_hm, lvl_str in matches:
        lvl = int(lvl_str)
        if start_hm <= end_hm:
            if start_hm <= now_hm < end_hm:
                return lvl
        else:
            if now_hm >= start_hm or now_hm < end_hm:
                return lvl
    if matches:
        return int(matches[0][2])
    m = _re.search(r"(\d+)", s)
    return int(m.group(1)) if m else default


def fetch_sub_clocks(cfg: dict[str, Any], secret: str) -> list[dict[str, Any]]:
    """Query sub-clock ledger from clock_view (read-only)."""
    view_name = _safe_ident(cfg.get("mysqlView") or "clock_view", "clock_view")
    conn = _connect(cfg, secret)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT build, floor, room, model, mac, status, bright, volume, link, update_at "
                f"FROM `{view_name}` ORDER BY mac ASC"
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    items: list[dict[str, Any]] = []
    for r in rows:
        mac = _to_int(r.get("mac"), 0)
        raw_model = str(r.get("model") or "").strip()
        model = "未知" if not raw_model or raw_model == "-" else raw_model
        status_txt = str(r.get("status") or "正常").strip()
        upd = r.get("update_at")
        raw_bright = str(r.get("bright") or "").strip()
        items.append({
            "mac": mac,
            "build": str(r.get("build") or "").strip(),
            "floor": str(r.get("floor") or "").strip(),
            "room": str(r.get("room") or "").strip(),
            "model": model,
            "link": _to_int(r.get("link"), 1),
            "bright": _parse_bright(raw_bright, 5),
            "brightRaw": raw_bright,
            "volume": _to_int(r.get("volume"), 8),
            "status": status_txt,
            "update_at": upd.isoformat() if hasattr(upd, "isoformat") else str(upd or ""),
            "driftMs": 0 if status_txt == "正常" else None,
            "mode": "CLOCK",
            "screenPower": True,
            "faultReason": "" if status_txt == "正常" else f"台账状态异常 ({status_txt})",
        })
    return items


def test_mysql_connection(cfg: dict[str, Any], secret: str) -> dict[str, Any]:
    """Verify MySQL connectivity and count rows in clock_view."""
    view_name = _safe_ident(cfg.get("mysqlView") or "clock_view", "clock_view")
    try:
        conn = _connect(cfg, secret)
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) AS cnt FROM `{view_name}`")
                row = cur.fetchone()
                cnt = int(row["cnt"]) if row else 0
        finally:
            conn.close()
        return {"reachable": True, "count": cnt}
    except Exception:
        return {"reachable": False, "error": "连接数据库失败"}
