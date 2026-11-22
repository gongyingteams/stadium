"""FastAPI router for Master Clock (UDP 0xDD/0xEE) and MySQL clock_view integration."""
from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from typing import Annotated, Any, Callable

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.clock_db import encrypt_password, fetch_sub_clocks, test_mysql_connection
from app.clock_ntp import ClockBusyError, ClockProtocolError, ClockTimeoutError, clock_client, probe_master_clock

router = APIRouter(prefix="/api/clock", tags=["clock"])

_deps: dict[str, Any] = {}
_drift_history: deque[dict[str, Any]] = deque(maxlen=30)
_subclock_cache: dict[str, Any] = {"items": [], "fetched_at": 0.0, "error": ""}


DEFAULT_CLOCK_SETTINGS: dict[str, Any] = {
    "masterIp": "192.168.7.2",
    "masterPort": 123,
    "localPort": 0,
    "timeoutS": 4.0,
    "retries": 2,
    "timezone": 8,
    "mysqlHost": "",
    "mysqlPort": 3306,
    "mysqlDatabase": "clock",
    "mysqlView": "clock_view",
    "mysqlUser": "",
    "mysqlPassword": "",
}


class ClockSettingsPayload(BaseModel):
    masterIp: str = Field(default="192.168.7.2", min_length=1, max_length=128)
    masterPort: int = Field(default=123, ge=1, le=65535)
    localPort: int = Field(default=0, ge=0, le=65535)
    timeoutS: float = Field(default=4.0, gt=0.2, le=30.0)
    retries: int = Field(default=2, ge=0, le=5)
    timezone: int = Field(default=8, ge=-12, le=12)
    mysqlHost: str = Field(default="", max_length=128)
    mysqlPort: int = Field(default=3306, ge=1, le=65535)
    mysqlDatabase: str = Field(default="clock", max_length=64)
    mysqlView: str = Field(default="clock_view", max_length=64)
    mysqlUser: str = Field(default="", max_length=64)
    mysqlPassword: str = Field(default="", max_length=128)
    keepExistingPassword: bool = Field(default=True)


class ClockCommandPayload(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    addr: int = Field(default=0xFF, ge=0, le=255)
    on: bool | None = None
    volume: int | None = None
    mode: int | None = None
    hours: int | None = None
    minutes: int | None = None
    seconds: int | None = None
    bus_type: int | None = None
    start: bool | None = None
    link: int | None = None
    clock_type: int | None = None
    timezone: int | None = None
    offset_s: int | None = None
    interval_s: int | None = None
    seg1: list[int] | None = None
    seg2: list[int] | None = None


def configure_clock_router(
    db_fn: Callable[[], Any],
    audit_fn: Callable[..., None],
    decode_token_fn: Callable[[str], dict[str, Any]],
    user_dep: Any,
    admin_ops_dep: Any,
    ctrl_roles_dep: Any,
    jwt_secret: str,
    now_fn: Callable[[], str],
) -> APIRouter:
    _deps["db"] = db_fn
    _deps["audit"] = audit_fn
    _deps["decode_token"] = decode_token_fn
    _deps["secret"] = jwt_secret
    _deps["now"] = now_fn

    def _load_settings() -> dict[str, Any]:
        cfg = DEFAULT_CLOCK_SETTINGS.copy()
        with db_fn() as conn:
            row = conn.execute("SELECT value FROM sys_settings WHERE key = 'clockConfig'").fetchone()
            if row and row["value"]:
                try:
                    cfg.update(json.loads(row["value"]))
                except Exception:
                    pass
        return cfg

    def _save_settings(cfg: dict[str, Any], username: str) -> None:
        with db_fn() as conn:
            conn.execute(
                """INSERT INTO sys_settings (key, value, updated_at, updated_by)
                   VALUES ('clockConfig', ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at, updated_by=excluded.updated_by""",
                (json.dumps(cfg, ensure_ascii=False), now_fn(), username),
            )

    def _apply_client_cfg(cfg: dict[str, Any]) -> None:
        clock_client.configure(
            host=cfg.get("masterIp") or "192.168.7.2",
            port=int(cfg.get("masterPort") or 123),
            local_port=int(cfg.get("localPort") or 0),
            timeout_s=float(cfg.get("timeoutS") or 4.0),
            retries=int(cfg.get("retries") if cfg.get("retries") is not None else 2),
        )

    # Apply persisted settings on startup
    _apply_client_cfg(_load_settings())

    @router.get("/settings")
    def get_clock_settings(user: dict[str, Any] = Depends(user_dep)) -> dict[str, Any]:
        cfg = _load_settings()
        has_pwd = bool(cfg.get("mysqlPassword"))
        safe = {**cfg, "mysqlPassword": "", "hasMysqlPassword": has_pwd}
        return safe

    @router.post("/settings")
    def save_clock_settings(body: ClockSettingsPayload, user: dict[str, Any] = Depends(admin_ops_dep)) -> dict[str, Any]:
        prev = _load_settings()
        data = body.model_dump(exclude={"keepExistingPassword"})
        if body.mysqlPassword:
            data["mysqlPassword"] = encrypt_password(body.mysqlPassword, jwt_secret)
        elif body.keepExistingPassword:
            data["mysqlPassword"] = prev.get("mysqlPassword", "")
        else:
            data["mysqlPassword"] = ""
        _save_settings(data, user["sub"])
        _apply_client_cfg(data)
        audit_fn(user["sub"], user.get("role"), "CLOCK_SETTINGS_SAVE", data["masterIp"], "SAVE", "SUCCESS",
                 details={k: v for k, v in data.items() if k != "mysqlPassword"})
        return {**data, "mysqlPassword": "", "hasMysqlPassword": bool(data.get("mysqlPassword"))}

    @router.post("/settings/test")
    async def test_clock_settings(body: ClockSettingsPayload, user: dict[str, Any] = Depends(admin_ops_dep)) -> dict[str, Any]:
        prev = _load_settings()
        cfg = body.model_dump()
        if not cfg.get("mysqlPassword") and body.keepExistingPassword:
            cfg["mysqlPassword"] = prev.get("mysqlPassword", "")
        udp_res = await probe_master_clock(body.masterIp, body.masterPort, body.localPort, timeout_s=min(3.0, body.timeoutS))
        if body.mysqlHost.strip():
            mysql_res = await asyncio.to_thread(test_mysql_connection, cfg, jwt_secret)
        else:
            mysql_res = {"reachable": False, "skipped": True, "error": "未填写 MySQL 主机 IP"}
        return {"udp": udp_res, "mysql": mysql_res}

    @router.get("/status")
    async def get_clock_status(user: dict[str, Any] = Depends(user_dep)) -> dict[str, Any]:
        cfg = _load_settings()
        try:
            sat = await clock_client.query_satellites(timeout_s=0.8, retries=0)
            tinfo = await clock_client.query_ntp_time(timeout_s=0.8, retries=0)
            _drift_history.append({
                "time": time.strftime("%H:%M:%S"),
                "driftMs": tinfo["drift_ms"],
                "sat": sat,
            })
        except (ClockTimeoutError, ClockProtocolError):
            pass

        st = clock_client.state
        return {
            "online": st.online,
            "lastError": st.last_error,
            "masterIp": cfg.get("masterIp"),
            "masterPort": cfg.get("masterPort"),
            "timezone": st.timezone if st.timezone is not None else cfg.get("timezone", 8),
            "masterUnixS": st.master_unix_s,
            "platformDriftMs": st.platform_drift_ms,
            "satelliteCount": st.satellite_count,
            "offsetS": st.offset_s,
            "syncIntervalS": st.sync_interval_s,
            "mysqlConfigured": bool((cfg.get("mysqlHost") or "").strip()),
            "protocolLogs": list(st.protocol_logs),
            "events": list(st.events),
            "driftHistory": list(_drift_history),
        }

    @router.get("/time")
    async def get_clock_time(user: dict[str, Any] = Depends(user_dep)) -> dict[str, Any]:
        try:
            tinfo = await clock_client.query_ntp_time()
            _drift_history.append({
                "time": time.strftime("%H:%M:%S"),
                "driftMs": tinfo["drift_ms"],
                "sat": clock_client.state.satellite_count,
            })
            return {"online": True, **tinfo, "driftHistory": list(_drift_history)}
        except (ClockTimeoutError, ClockProtocolError) as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.get("/subclocks")
    async def get_sub_clocks(refresh: bool = False, user: dict[str, Any] = Depends(user_dep)) -> dict[str, Any]:
        cfg = _load_settings()
        if not (cfg.get("mysqlHost") or "").strip():
            return {"configured": False, "online": False, "items": [], "count": 0, "cachedAt": None}
        now_ts = time.time()
        if not refresh and _subclock_cache["fetched_at"] and (now_ts - _subclock_cache["fetched_at"]) < 60.0 and not _subclock_cache["error"]:
            return {
                "configured": True,
                "online": True,
                "cached": True,
                "items": _subclock_cache["items"],
                "count": len(_subclock_cache["items"]),
                "cachedAt": _subclock_cache["fetched_at"],
            }
        try:
            items = await asyncio.to_thread(fetch_sub_clocks, cfg, jwt_secret)
            _subclock_cache["items"] = items
            _subclock_cache["fetched_at"] = time.time()
            _subclock_cache["error"] = ""
            return {
                "configured": True,
                "online": True,
                "items": items,
                "count": len(items),
                "cachedAt": _subclock_cache["fetched_at"],
            }
        except Exception as exc:
            _subclock_cache["error"] = str(exc)
            return {
                "configured": True,
                "online": False,
                "error": str(exc),
                "items": _subclock_cache["items"],
                "count": len(_subclock_cache["items"]),
                "cachedAt": _subclock_cache["fetched_at"] or None,
            }

    @router.post("/sync")
    async def force_clock_sync(user: dict[str, Any] = Depends(ctrl_roles_dep)) -> dict[str, Any]:
        cfg = _load_settings()
        tz = int(cfg.get("timezone") if cfg.get("timezone") is not None else 8)
        try:
            # 协议规定：0x0D 修改/下发时区会立即同步一次全网子钟时间
            await clock_client.set_timezone(tz)
            interval = clock_client.state.sync_interval_s or 3600
            res = await clock_client.set_sync_interval(interval)
            tinfo = await clock_client.query_ntp_time()
            sat = await clock_client.query_satellites()
            audit_fn(user["sub"], user.get("role"), "CLOCK_SYNC", clock_client.host, "SYNC", "SUCCESS", details={"timezone": tz, **res, **tinfo, "sat": sat})
            return {"ok": True, "message": "已触发母钟立即全网同步子钟时间并更新校时间隔", "timezone": tz, **res, **tinfo, "satelliteCount": sat}
        except (ClockTimeoutError, ClockProtocolError) as exc:
            audit_fn(user["sub"], user.get("role"), "CLOCK_SYNC", clock_client.host, "SYNC", "FAILED", details={"error": str(exc)})
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.post("/command")
    async def run_clock_command(body: ClockCommandPayload, user: dict[str, Any] = Depends(ctrl_roles_dep)) -> dict[str, Any]:
        act = body.action.strip().lower()
        point_actions = {"set_screen", "set_brightness", "set_audio", "set_timer", "point_timer", "add", "remove"}
        if act in point_actions and not (1 <= body.addr <= 254):
            raise HTTPException(status_code=400, detail=f"定点指令 {act} 的子钟地址必须在 1 ~ 254 之间 (当前 {body.addr})")
        try:
            if act == "set_screen":
                res = await clock_client.set_screen(body.addr, bool(body.on))
            elif act == "set_brightness":
                s1 = tuple(body.seg1 or [6, 0, 18, 0, 5])
                s2 = tuple(body.seg2 or [18, 0, 23, 59, 3])
                res = await clock_client.set_brightness(body.addr, s1, s2)  # type: ignore[arg-type]
            elif act == "set_audio":
                res = await clock_client.set_audio(body.addr, bool(body.on), int(body.volume or 0))
            elif act == "set_timer":
                res = await clock_client.set_timer(body.addr, int(body.mode or 3), int(body.hours or 0), int(body.minutes or 0), int(body.seconds or 0))
            elif act == "broadcast_timer":
                res = await clock_client.broadcast_timer(int(body.bus_type or 1), bool(body.start))
            elif act == "point_timer":
                res = await clock_client.point_timer(body.addr, bool(body.start))
            elif act == "add":
                res = await clock_client.add_sub_clock(body.addr, int(body.link or 1), int(body.clock_type or 2))
            elif act == "remove":
                res = await clock_client.remove_sub_clock(body.addr)
            elif act == "set_timezone":
                tz = await clock_client.set_timezone(int(body.timezone if body.timezone is not None else 8))
                res = {"timezone": tz}
            elif act == "set_offset":
                res = await clock_client.set_offset(int(body.offset_s or 0))
            elif act == "set_interval":
                res = await clock_client.set_sync_interval(int(body.interval_s or 3600))
            else:
                raise HTTPException(status_code=400, detail=f"不支持的时钟控制指令: {body.action}")
            audit_fn(user["sub"], user.get("role"), "CLOCK_COMMAND", f"#{body.addr}", act, "SUCCESS", details=res)
            return {"ok": True, "action": act, **res}
        except ClockBusyError as exc:
            audit_fn(user["sub"], user.get("role"), "CLOCK_COMMAND", f"#{body.addr}", act, "BUSY", details={"error": str(exc)})
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except (ClockTimeoutError, ClockProtocolError) as exc:
            audit_fn(user["sub"], user.get("role"), "CLOCK_COMMAND", f"#{body.addr}", act, "FAILED", details={"error": str(exc)})
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.websocket("/ws")
    async def clock_ws(websocket: WebSocket, token: str = "") -> None:
        try:
            decode_token_fn(token)
        except HTTPException:
            await websocket.close(code=1008)
            return

        await websocket.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)

        async def _on_event(msg: dict[str, Any]) -> None:
            if not queue.full():
                await queue.put(msg)

        clock_client.add_listener(_on_event)
        stop_event = asyncio.Event()

        async def _push_events() -> None:
            while not stop_event.is_set():
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                    await websocket.send_json(msg)
                except asyncio.TimeoutError:
                    st = clock_client.state
                    await websocket.send_json({
                        "type": "clock_status",
                        "online": st.online,
                        "masterUnixS": st.master_unix_s,
                        "platformDriftMs": st.platform_drift_ms,
                        "satelliteCount": st.satellite_count,
                        "timezone": st.timezone,
                    })
                except Exception:
                    stop_event.set()
                    break

        async def _recv_client() -> None:
            try:
                while not stop_event.is_set():
                    raw = await websocket.receive_text()
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    mtype = (msg or {}).get("type")
                    if mtype == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif mtype == "refresh":
                        try:
                            sat = await clock_client.query_satellites()
                            tinfo = await clock_client.query_ntp_time()
                            await websocket.send_json({
                                "type": "clock_status",
                                "online": True,
                                "masterUnixS": tinfo["master_unix_s"],
                                "platformDriftMs": tinfo["drift_ms"],
                                "satelliteCount": sat,
                                "timezone": clock_client.state.timezone,
                            })
                        except Exception:
                            pass
            except WebSocketDisconnect:
                stop_event.set()
            except Exception:
                stop_event.set()

        t1 = asyncio.create_task(_push_events())
        t2 = asyncio.create_task(_recv_client())
        try:
            done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
            stop_event.set()
            for task in pending:
                task.cancel()
            for task in done:
                _ = task.exception() if not task.cancelled() else None
        finally:
            clock_client.remove_listener(_on_event)
            stop_event.set()

    return router
