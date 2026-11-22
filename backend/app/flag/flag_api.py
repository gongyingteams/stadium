"""
升旗硬件 REST API

设计原则:
    1. 设备配置存数据库，不硬编码 —— 添加设备时填写 IP/端口/从站ID/行程
    2. 默认只读模式 —— 不下发任何会动电机的指令
    3. 位置只报真实值 —— 见 position.py
    4. 运动有硬保护 —— 见 motion_guard.py
    5. 所有指令留审计

挂载方式（main.py 末尾）:
    from .flag_api import router as flag_router
    app.include_router(flag_router)
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .flag_service import FlagController, registry
from .motion_guard import UnsafeCommand, guards
from .position import trackers
from .modbus_flag import (
    REG_ANTHEM_DURATION, REG_CMD_AUTO_UP, REG_CMD_ESTOP,
    REG_CMD_FORWARD, REG_CMD_MEASURE, REG_CMD_REVERSE, REG_MANUAL_RPM,
)

router = APIRouter(prefix="/api/flag", tags=["flag"])

_db_hook = None
_audit_hook = None


def configure(db_hook, audit_hook) -> None:
    """由 main.py 调用，注入数据库/审计依赖。"""
    global _db_hook, _audit_hook
    _db_hook = db_hook
    _audit_hook = audit_hook


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

class FlagDevicePayload(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    host: str = Field(min_length=1, max_length=128)
    port: int = Field(default=502, ge=1, le=65535)
    unit_id: int = Field(default=1, ge=1, le=247)
    pole_type: str = Field(default="vertical", pattern="^(vertical|horizontal)$")
    timeout_s: float = Field(default=3.0, gt=0, le=30)
    pole_height_m: float | None = Field(default=None, gt=0, le=100)
    total_stroke_mm: float | None = Field(default=None, gt=0)
    pulses_per_meter: float | None = Field(default=None, gt=0)
    max_pulses: float | None = Field(default=None, gt=0)
    allow_write: bool = Field(default=False)
    max_moving_seconds: float = Field(default=75.0, gt=5, le=600)
    heartbeat_timeout_s: float = Field(default=120.0, gt=10, le=3600)
    region: str = Field(default="", max_length=128)
    remark: str = Field(default="", max_length=255)


class CommandPayload(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    value: int | None = None
    anthem_duration_sec: float | None = None
    manual_rpm: float | None = None


class WriteFlagPayload(BaseModel):
    address: int = Field(ge=1, le=0x0E)
    value: int = Field(ge=0, le=0xFFFF)


#: 运动类动作 -> 方向（用于 guard 预检）
MOTION_ACTIONS: dict[str, str] = {
    "forward": "UP",
    "manual_forward": "UP",
    "auto_up": "UP",
    "auto_raise": "UP",
    "raise": "UP",
    "reverse": "DOWN",
    "manual_reverse": "DOWN",
    "lower_flag": "DOWN",
}

#: 全部动作 -> (寄存器, 默认写入值, 中文名)
ACTIONS: dict[str, tuple[int, int, str]] = {
    # 运动
    "auto_up":        (REG_CMD_AUTO_UP, 1, "自动升旗"),
    "forward":        (REG_CMD_FORWARD, 1, "手动正转(上升)"),
    "reverse":        (REG_CMD_REVERSE, 1, "手动反转(下降)"),
    "measure":        (REG_CMD_MEASURE, 1, "自动测距"),
    "emergency":      (REG_CMD_ESTOP, 1, "急停"),
    # 参数
    "set_anthem":     (REG_ANTHEM_DURATION, 0, "设置国歌时长"),
    "set_manual_rpm": (REG_MANUAL_RPM, 0, "设置手动转速"),
}

#: 兼容原始对话的 action 命名
ALIASES: dict[str, str] = {
    "estop": "emergency",
    "emergency_stop": "emergency",
    "stop": "emergency",
    "manual_forward": "forward",
    "upper_zero": "forward",
    "force_top": "forward",
    "manual_reverse": "reverse",
    "lower_flag": "reverse",
    "auto_raise": "auto_up",
    "raise": "auto_up",
    "official_ceremony": "auto_up",
    "simulate_ceremony": "auto_up",
    "auto_measure": "measure",
    "set_anthem_duration": "set_anthem",
}


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------

def _resolve_action(raw: str) -> str:
    act = (raw or "").strip().lower()
    return ALIASES.get(act, act)


def _require_device(device_id: str) -> FlagController:
    ctrl = registry.get(device_id)
    if ctrl is None:
        raise HTTPException(status_code=404, detail="设备不存在或未加载")
    return ctrl


def _tracker_for(ctrl: FlagController):
    row = (_db_hook().get_flag_device(ctrl.device_id) or {}) if _db_hook else {}
    return trackers.get_or_create(
        ctrl.device_id,
        row.get("total_stroke_mm") or ctrl.total_stroke_mm,
    )


def _status_with_position(ctrl: FlagController, force: bool = False) -> dict[str, Any]:
    """读状态 + 计算位置 + 刷新心跳。"""
    status = ctrl.read_status(force=force)
    tracker = _tracker_for(ctrl)
    # 位置追踪需要原始寄存器字段，统一字段名
    pos_input = {
        "run_status": status.get("motor_status"),
        "limit_top": status.get("limit_forward"),
        "limit_bottom": status.get("limit_reverse"),
    }
    pos = tracker.update(pos_input)

    guard = guards.get(ctrl.device_id)
    if guard:
        guard.heartbeat()

    return {**status, **pos.to_dict()}


def _apply_to_registry(body: FlagDevicePayload) -> None:
    ctrl = FlagController(
        device_id=body.device_id,
        host=body.host,
        port=body.port,
        unit_id=body.unit_id,
        timeout=body.timeout_s,
        total_stroke_mm=body.total_stroke_mm,
        pulses_per_meter=body.pulses_per_meter,
        max_pulses=body.max_pulses,
        allow_write=body.allow_write,
    )
    registry.upsert(ctrl)

    guards.get_or_create(
        body.device_id,
        emergency_callback=(lambda: ctrl.emergency_stop()),
        max_moving_seconds=body.max_moving_seconds,
        heartbeat_timeout=body.heartbeat_timeout_s,
    )
    trackers.get_or_create(body.device_id, body.total_stroke_mm)


# ---------------------------------------------------------------------------
# 设备配置 CRUD
# ---------------------------------------------------------------------------

@router.get("/devices")
def list_devices() -> dict[str, Any]:
    rows = _db_hook().list_flag_devices()
    items = []
    for row in rows:
        ctrl = registry.get(row["device_id"])
        status = _status_with_position(ctrl) if ctrl else None
        guard = guards.get(row["device_id"])
        items.append({
            **row,
            "status": status,
            "guard": guard.state_dict() if guard else None,
        })
    return {"items": items, "total": len(items)}


@router.post("/devices")
def create_device(body: FlagDevicePayload) -> dict[str, Any]:
    _db_hook().upsert_flag_device(body.model_dump())
    _apply_to_registry(body)
    return {"ok": True, "device_id": body.device_id}


@router.put("/devices/{device_id}")
def update_device(device_id: str, body: FlagDevicePayload) -> dict[str, Any]:
    if device_id != body.device_id:
        raise HTTPException(status_code=400, detail="路径 device_id 与请求体不一致")
    _db_hook().upsert_flag_device(body.model_dump())
    _apply_to_registry(body)
    return {"ok": True, "device_id": device_id}


@router.delete("/devices/{device_id}")
def delete_device(device_id: str) -> dict[str, Any]:
    _db_hook().delete_flag_device(device_id)
    registry.remove(device_id)
    guards.remove(device_id)
    trackers.remove(device_id)
    return {"ok": True}


# ---------------------------------------------------------------------------
# 连通性测试
# ---------------------------------------------------------------------------

@router.post("/probe")
def probe_device(body: FlagDevicePayload) -> dict[str, Any]:
    tmp = FlagController(
        device_id="__probe__",
        host=body.host, port=body.port, unit_id=body.unit_id,
        timeout=body.timeout_s, allow_write=False,
    )
    result = tmp.probe()
    result["provided"] = {"host": body.host, "port": body.port, "unit_id": body.unit_id}
    return result


@router.get("/devices/{device_id}/probe")
def probe_saved_device(device_id: str) -> dict[str, Any]:
    return _require_device(device_id).probe()


# ---------------------------------------------------------------------------
# 状态读取
# ---------------------------------------------------------------------------

@router.get("/devices/{device_id}/status")
def device_status(device_id: str, force: bool = False) -> dict[str, Any]:
    ctrl = _require_device(device_id)
    return {"device_id": device_id, "status": _status_with_position(ctrl, force)}


@router.get("/devices/{device_id}/position")
def device_position(device_id: str) -> dict[str, Any]:
    """只返回位置信息。"""
    ctrl = _require_device(device_id)
    status = _status_with_position(ctrl)
    return {
        "device_id": device_id,
        **{k: v for k, v in status.items() if k.startswith("position_") or k in ("height_m", "height_exact")},
        "run_status": status.get("motor_status"),
        "run_status_text": status.get("motor_status_text"),
        "limit_top": status.get("limit_forward"),
        "limit_top_text": status.get("limit_forward_text"),
        "limit_bottom": status.get("limit_reverse"),
        "limit_bottom_text": status.get("limit_reverse_text"),
    }


@router.get("/devices/{device_id}/registers")
def device_registers(device_id: str) -> dict[str, Any]:
    ctrl = _require_device(device_id)
    st = ctrl.read_status(force=True)
    return {
        "device_id": device_id,
        "online": st.get("online"),
        "raw_registers": st.get("raw_registers", {}),
    }


# ---------------------------------------------------------------------------
# 保护状态
# ---------------------------------------------------------------------------

@router.get("/devices/{device_id}/guard")
def device_guard(device_id: str) -> dict[str, Any]:
    guard = guards.get(device_id)
    if guard is None:
        raise HTTPException(status_code=404, detail="保护器不存在")
    return guard.state_dict()


@router.post("/devices/{device_id}/clear-latch")
def clear_latch(device_id: str) -> dict[str, Any]:
    """人工确认现场安全后，解除自动急停锁定。"""
    guard = guards.get(device_id)
    if guard is None:
        raise HTTPException(status_code=404, detail="保护器不存在")
    guard.clear_latch()
    if _audit_hook:
        _audit_hook(
            device_id=device_id, event_type="FLAG_CLEAR_LATCH",
            action="clear_latch", result="SUCCESS",
            details={"state": guard.state_dict()},
        )
    return {"ok": True, "guard": guard.state_dict()}


@router.post("/devices/{device_id}/heartbeat")
def heartbeat(device_id: str) -> dict[str, Any]:
    guard = guards.get(device_id)
    if guard is None:
        raise HTTPException(status_code=404, detail="保护器不存在")
    guard.heartbeat()
    return {"ok": True}


@router.get("/guards")
def all_guards() -> dict[str, Any]:
    return {"items": guards.state_list()}


# ---------------------------------------------------------------------------
# 指令下发
# ---------------------------------------------------------------------------

@router.post("/devices/{device_id}/command")
def device_command(device_id: str, body: CommandPayload) -> dict[str, Any]:
    ctrl = _require_device(device_id)
    action = _resolve_action(body.action)

    if action not in ACTIONS:
        raise HTTPException(status_code=400, detail=f"未知动作: {body.action}")

    guard = guards.get(device_id)
    if guard:
        guard.heartbeat()

    address, default_value, label = ACTIONS[action]

    # ---- 运动类指令：先做安全预检 ----
    if action in MOTION_ACTIONS and guard:
        st = ctrl.read_status(force=True)
        try:
            guard.check_can_move(
                direction=MOTION_ACTIONS[action],
                run_status=st.get("motor_status"),
                limit_top=st.get("limit_forward"),
                limit_bottom=st.get("limit_reverse"),
            )
        except UnsafeCommand as exc:
            if _audit_hook:
                _audit_hook(
                    device_id=device_id, event_type="FLAG_COMMAND",
                    action=body.action, result="REJECTED_UNSAFE",
                    details={"error": str(exc)},
                )
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    # ---- 计算写入值 ----
    value = default_value
    if action == "set_anthem":
        sec = body.anthem_duration_sec if body.anthem_duration_sec is not None else (
            (body.value / 10.0) if body.value is not None else None
        )
        if sec is None:
            raise HTTPException(status_code=400, detail="set_anthem 需要 anthem_duration_sec")
        if not (0.1 <= sec <= 600):
            raise HTTPException(status_code=400, detail="国歌时长需在 0.1~600 秒之间")
        value = max(1, round(sec * 10))
    elif action == "set_manual_rpm":
        rpm = body.manual_rpm if body.manual_rpm is not None else (
            (body.value / 10.0) if body.value is not None else None
        )
        if rpm is None:
            raise HTTPException(status_code=400, detail="set_manual_rpm 需要 manual_rpm")
        value = max(1, round(rpm * 10))
    elif body.value is not None:
        value = body.value

    result = ctrl.write_register(address, value)
    result.update({"device_id": device_id, "action": body.action, "label": label})

    if _audit_hook:
        _audit_hook(
            device_id=device_id, event_type="FLAG_COMMAND", action=body.action,
            result="SUCCESS" if result.get("accepted") else "REJECTED",
            details=result,
        )

    # ---- 成功后登记运动状态 ----
    if result.get("accepted") and guard:
        if action in MOTION_ACTIONS:
            guard.on_motion_started(MOTION_ACTIONS[action])
        elif action == "emergency":
            guard.on_motion_stopped()

    return result


@router.post("/devices/{device_id}/register")
def write_register(device_id: str, body: WriteFlagPayload) -> dict[str, Any]:
    ctrl = _require_device(device_id)
    guard = guards.get(device_id)
    if guard:
        guard.heartbeat()
    result = ctrl.write_register(body.address, body.value)
    if _audit_hook:
        _audit_hook(
            device_id=device_id, event_type="FLAG_RAW_WRITE",
            action=f"0x{body.address:02X}={body.value}",
            result="SUCCESS" if result.get("accepted") else "REJECTED",
            details=result,
        )
    if result.get("accepted") and guard and body.address == REG_CMD_ESTOP and body.value == 1:
        guard.on_motion_stopped()
    return result


@router.post("/devices/{device_id}/emergency-stop")
def emergency_stop(device_id: str) -> dict[str, Any]:
    ctrl = _require_device(device_id)
    guard = guards.get(device_id)
    if guard:
        guard.heartbeat()
    result = ctrl.emergency_stop()
    if _audit_hook:
        _audit_hook(
            device_id=device_id, event_type="FLAG_ESTOP",
            action="emergency_stop",
            result="SUCCESS" if result.get("accepted") else "REJECTED",
            details=result,
        )
    if result.get("accepted") and guard:
        guard.on_motion_stopped()
    return result


@router.get("/health")
def flag_health() -> dict[str, Any]:
    items = []
    for ctrl in registry.all():
        st = _status_with_position(ctrl)
        items.append({
            "device_id": ctrl.device_id,
            "host": f"{ctrl.host}:{ctrl.port}",
            "unit_id": ctrl.unit_id,
            "online": st.get("online"),
            "reason": st.get("reason"),
            "latency_ms": st.get("latency_ms"),
            "read_only": not ctrl.allow_write,
            "position_state": st.get("position_state"),
            "position_text": st.get("position_text"),
            "height_m": st.get("height_m"),
            "height_exact": st.get("height_exact"),
        })
    online = sum(1 for i in items if i["online"])
    return {
        "total": len(items),
        "online": online,
        "offline": len(items) - online,
        "items": items,
    }
