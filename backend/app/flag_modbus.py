"""Modbus TCP client for the USR-K7 flag-raising gateway (192.168.0.7:20108)."""
from __future__ import annotations

import os
import socket
import struct
import threading
import time
from typing import Any

FLAG_MODBUS_HOST = os.getenv("FLAG_MODBUS_HOST", "192.168.0.7")
FLAG_MODBUS_PORT = int(os.getenv("FLAG_MODBUS_PORT", "20108"))
FLAG_MODBUS_UNIT_ID = int(os.getenv("FLAG_MODBUS_UNIT_ID", "1"))
FLAG_MODBUS_TIMEOUT = float(os.getenv("FLAG_MODBUS_TIMEOUT", "3.0"))

_LOCK = threading.Lock()
_TID_COUNTER = 0
_LAST_IO_AT = 0.0
_MIN_FRAME_GAP_SEC = 0.22

RUN_STATUS_MAP = {0: "电机停止", 1: "电机正转", 2: "电机反转"}
LIMIT_TOP_MAP = {0: "未在限位", 1: "在正零位", 2: "在正限位"}
LIMIT_BOTTOM_MAP = {0: "未在限位", 1: "在反零位", 2: "在反限位"}


class ModbusConnectionError(RuntimeError):
    """Raised when the USR-K7 gateway is unreachable or times out."""


class ModbusCommandError(ValueError):
    """Raised when a command violates preconditions or returns a Modbus exception."""


def _next_tid() -> int:
    global _TID_COUNTER
    _TID_COUNTER = (_TID_COUNTER % 65000) + 1
    return _TID_COUNTER


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ModbusConnectionError("与升旗网关连接被关闭")
        buf.extend(chunk)
    return bytes(buf)


def _exchange_once(pdu_payload: bytes, unit_id: int) -> tuple[bytes, str, str]:
    """Send a single Modbus TCP ADU and return (response_pdu, tx_hex, rx_hex)."""
    global _LAST_IO_AT
    gap = time.perf_counter() - _LAST_IO_AT
    if gap < _MIN_FRAME_GAP_SEC:
        time.sleep(_MIN_FRAME_GAP_SEC - gap)

    tid = _next_tid()
    length = 1 + len(pdu_payload)
    adu = struct.pack(">HHHB", tid, 0, length, unit_id) + pdu_payload
    tx_hex = adu.hex(" ")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(FLAG_MODBUS_TIMEOUT)
    try:
        sock.connect((FLAG_MODBUS_HOST, FLAG_MODBUS_PORT))
        sock.sendall(adu)
        mbap = _recv_exact(sock, 7)
        resp_tid, resp_pid, resp_len, resp_uid = struct.unpack(">HHHB", mbap)
        if resp_pid != 0 or resp_len < 2:
            raise ModbusConnectionError("收到无效的 Modbus TCP 响应头")
        if resp_tid != tid:
            raise ModbusConnectionError(f"Modbus 事务号不匹配 (期望 {tid}, 实际 {resp_tid})")
        pdu = _recv_exact(sock, resp_len - 1)
        rx_hex = (mbap + pdu).hex(" ")
    except OSError as exc:
        raise ModbusConnectionError(
            f"无法连接升旗网关 {FLAG_MODBUS_HOST}:{FLAG_MODBUS_PORT} ({exc})"
        ) from exc
    finally:
        _LAST_IO_AT = time.perf_counter()
        sock.close()

    fc = pdu[0]
    if fc & 0x80:
        exc_code = pdu[1] if len(pdu) > 1 else 0
        raise ModbusCommandError(f"设备返回 Modbus 异常响应 (功能码 0x{fc:02X}, 异常码 0x{exc_code:02X})")
    return pdu, tx_hex, rx_hex


def _exchange(pdu_payload: bytes, unit_id: int, retries: int = 2) -> tuple[bytes, str, str]:
    """Exchange Modbus TCP ADU with automatic retry on transient 0x0B/0x0A busy responses."""
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return _exchange_once(pdu_payload, unit_id)
        except ModbusCommandError as exc:
            last_exc = exc
            if ("异常码 0x0B" in str(exc) or "异常码 0x0A" in str(exc)) and attempt < retries:
                time.sleep(0.28)
                continue
            raise
    assert last_exc is not None
    raise last_exc


def read_flag_registers(unit_id: int = FLAG_MODBUS_UNIT_ID) -> dict[str, Any]:
    """Read holding registers 0x01..0x0E (14 registers) from the flag controller."""
    with _LOCK:
        t0 = time.perf_counter()
        pdu_req = struct.pack(">BHH", 0x03, 0x0001, 14)
        pdu_resp, tx_hex, rx_hex = _exchange(pdu_req, unit_id)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    if len(pdu_resp) < 2 or pdu_resp[0] != 0x03:
        raise ModbusConnectionError("读取寄存器响应功能码异常")
    byte_count = pdu_resp[1]
    if byte_count != 28 or len(pdu_resp) < 30:
        raise ModbusConnectionError(f"读取寄存器响应长度异常 (期望 28 字节, 实际 {byte_count})")

    vals = struct.unpack(">14H", pdu_resp[2:30])
    regs = {f"0x{idx:02X}": vals[idx - 1] for idx in range(1, 15)}

    manual_rpm = round(vals[0] / 10.0, 1)
    anthem_duration_sec = round(vals[1] / 10.0, 1)
    pulses_per_rev = vals[2] or 10000
    run_status = vals[3]
    auto_rpm = round(vals[4] / 10.0, 1)
    limit_top = vals[10]
    limit_bottom = vals[11]
    low_16 = vals[12]
    high_16 = vals[13]
    total_pulses = (high_16 << 16) | low_16
    total_turns = round(total_pulses / pulses_per_rev, 2) if pulses_per_rev else 0.0

    return {
        "gateway": {"host": FLAG_MODBUS_HOST, "port": FLAG_MODBUS_PORT, "unit_id": unit_id},
        "elapsed_ms": elapsed_ms,
        "tx_hex": tx_hex,
        "rx_hex": rx_hex,
        "registers": regs,
        "manual_rpm": manual_rpm,
        "anthem_duration_sec": anthem_duration_sec,
        "pulses_per_rev": pulses_per_rev,
        "run_status": run_status,
        "run_status_text": RUN_STATUS_MAP.get(run_status, f"未知({run_status})"),
        "auto_rpm": auto_rpm,
        "limit_top": limit_top,
        "limit_top_text": LIMIT_TOP_MAP.get(limit_top, f"未知({limit_top})"),
        "limit_bottom": limit_bottom,
        "limit_bottom_text": LIMIT_BOTTOM_MAP.get(limit_bottom, f"未知({limit_bottom})"),
        "total_pulses": total_pulses,
        "total_turns": total_turns,
    }


def write_flag_register(register_addr: int, value: int, unit_id: int = FLAG_MODBUS_UNIT_ID) -> dict[str, Any]:
    """Write a single 16-bit holding register using Modbus function 0x06."""
    if not (0 <= register_addr <= 0xFFFF and 0 <= value <= 0xFFFF):
        raise ModbusCommandError("寄存器地址或写入值超出 uint16 范围")
    with _LOCK:
        t0 = time.perf_counter()
        pdu_req = struct.pack(">BHH", 0x06, register_addr, value)
        pdu_resp, tx_hex, rx_hex = _exchange(pdu_req, unit_id)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    if len(pdu_resp) < 5 or pdu_resp[0] != 0x06:
        raise ModbusConnectionError("写寄存器响应功能码异常")
    echo_addr, echo_val = struct.unpack(">HH", pdu_resp[1:5])
    if echo_addr != register_addr or echo_val != value:
        raise ModbusConnectionError("写寄存器回显校验不一致")

    return {
        "register": f"0x{register_addr:02X}",
        "value": value,
        "elapsed_ms": elapsed_ms,
        "tx_hex": tx_hex,
        "rx_hex": rx_hex,
    }


def execute_flag_command(
    action: str,
    payload: dict[str, Any] | None = None,
    unit_id: int = FLAG_MODBUS_UNIT_ID,
) -> dict[str, Any]:
    """Execute a high-level flag command with safety precondition checks."""
    payload = payload or {}
    act = (action or "").strip().lower()
    steps: list[dict[str, Any]] = []

    if act in ("estop", "emergency_stop", "stop"):
        steps.append(write_flag_register(0x0A, 1, unit_id=unit_id))
        status = read_flag_registers(unit_id=unit_id)
        return {
            "accepted": True,
            "simulated": False,
            "action": act,
            "message": "已向急停寄存器 0x0A 写入 1，电机急停执行完成",
            "steps": steps,
            "status": status,
        }

    if act == "set_anthem_duration":
        sec = float(payload.get("anthem_duration_sec", 0))
        if sec <= 0 or sec > 600:
            raise ModbusCommandError("国歌时长必须在 0.1 ~ 600 秒之间")
        steps.append(write_flag_register(0x02, max(1, round(sec * 10)), unit_id=unit_id))
        status = read_flag_registers(unit_id=unit_id)
        return {
            "accepted": True,
            "simulated": False,
            "action": act,
            "message": f"已写入国歌时长 {sec:.1f}s (寄存器 0x02={round(sec * 10)})",
            "steps": steps,
            "status": status,
        }

    if act == "set_manual_rpm":
        rpm = float(payload.get("manual_rpm", 0))
        if rpm <= 0 or rpm > 3000:
            raise ModbusCommandError("手动转速必须在 0.1 ~ 3000 RPM 之间")
        steps.append(write_flag_register(0x01, max(1, round(rpm * 10)), unit_id=unit_id))
        status = read_flag_registers(unit_id=unit_id)
        return {
            "accepted": True,
            "simulated": False,
            "action": act,
            "message": f"已写入手动转速 {rpm:.1f} RPM (寄存器 0x01={round(rpm * 10)})",
            "steps": steps,
            "status": status,
        }

    if act == "write_register":
        reg = int(payload.get("register", 0))
        val = int(payload.get("value", 0))
        steps.append(write_flag_register(reg, val, unit_id=unit_id))
        status = read_flag_registers(unit_id=unit_id)
        return {
            "accepted": True,
            "simulated": False,
            "action": act,
            "message": f"已写入寄存器 0x{reg:02X} = {val}",
            "steps": steps,
            "status": status,
        }

    # Pre-check current status for motion commands
    before = read_flag_registers(unit_id=unit_id)

    if act in ("auto_raise", "raise", "official_ceremony", "simulate_ceremony"):
        if before["run_status"] != 0:
            raise ModbusCommandError(f"当前电机正在运行（{before['run_status_text']}），请先急停后再执行自动升旗")
        if payload.get("anthem_duration_sec") is not None:
            sec = float(payload["anthem_duration_sec"])
            if sec > 0:
                target_val = max(1, round(sec * 10))
                if before["registers"].get("0x02") != target_val:
                    steps.append(write_flag_register(0x02, target_val, unit_id=unit_id))
        steps.append(write_flag_register(0x08, 1, unit_id=unit_id))
        after = read_flag_registers(unit_id=unit_id)
        return {
            "accepted": True,
            "simulated": False,
            "action": act,
            "message": "已下发自动升旗指令 (0x08=1)",
            "steps": steps,
            "status": after,
        }

    if act in ("manual_forward", "upper_zero", "force_top"):
        if before["run_status"] != 0:
            raise ModbusCommandError(f"当前电机正在运行（{before['run_status_text']}），请先急停后再执行手动正转")
        if before["limit_top"] != 0:
            raise ModbusCommandError(f"当前已处于最高点（{before['limit_top_text']}），已自动拦截上升指令")
        if payload.get("manual_rpm") is not None:
            rpm = float(payload["manual_rpm"])
            if rpm > 0:
                steps.append(write_flag_register(0x01, max(1, round(rpm * 10)), unit_id=unit_id))
        steps.append(write_flag_register(0x06, 1, unit_id=unit_id))
        after = read_flag_registers(unit_id=unit_id)
        return {
            "accepted": True,
            "simulated": False,
            "action": act,
            "message": "已下发手动正转指令 (0x06=1)",
            "steps": steps,
            "status": after,
        }

    if act in ("manual_reverse", "lower_flag"):
        if before["run_status"] != 0:
            raise ModbusCommandError(f"当前电机正在运行（{before['run_status_text']}），请先急停后再执行手动反转")
        if before["limit_bottom"] != 0:
            raise ModbusCommandError(f"当前已处于最低点（{before['limit_bottom_text']}），已自动拦截下降指令")
        if payload.get("manual_rpm") is not None:
            rpm = float(payload["manual_rpm"])
            if rpm > 0:
                steps.append(write_flag_register(0x01, max(1, round(rpm * 10)), unit_id=unit_id))
        steps.append(write_flag_register(0x07, 1, unit_id=unit_id))
        after = read_flag_registers(unit_id=unit_id)
        return {
            "accepted": True,
            "simulated": False,
            "action": act,
            "message": "已下发手动反转指令 (0x07=1)",
            "steps": steps,
            "status": after,
        }

    if act == "auto_measure":
        if before["run_status"] != 0:
            raise ModbusCommandError(f"当前电机正在运行（{before['run_status_text']}），请先急停后再执行自动测距")
        if before["limit_top"] == 0:
            raise ModbusCommandError("自动测距要求电机处于最高点限位（当前 0x0B=0 未在限位）")
        steps.append(write_flag_register(0x09, 1, unit_id=unit_id))
        after = read_flag_registers(unit_id=unit_id)
        return {
            "accepted": True,
            "simulated": False,
            "action": act,
            "message": "已下发自动测距指令 (0x09=1)",
            "steps": steps,
            "status": after,
        }

    raise ModbusCommandError(f"不支持的升旗控制指令: {action}")
