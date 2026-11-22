"""
升旗硬件驱动层 - 适配器（把 modbus_flag 包装为后端可用的服务对象）
"""
from __future__ import annotations

import threading
import time
from typing import Any

from .modbus_flag import (
    ModbusTcpClient, ModbusError, ModbusTimeout, ModbusExceptionResponse,
    probe as modbus_probe, pulses_to_height_m,
    REG_CMD_ESTOP,
)

#: 单次状态读取的缓存有效期（秒），避免前端高频轮询打爆 PLC
STATUS_CACHE_TTL = 1.0


class FlagController:
    """一根旗杆的控制器（一个 Modbus 从站）。"""

    def __init__(
        self,
        device_id: str,
        host: str,
        port: int = 502,
        unit_id: int = 1,
        timeout: float = 3.0,
        total_stroke_mm: float | None = None,
        pulses_per_meter: float | None = None,
        max_pulses: float | None = None,
        allow_write: bool = False,
    ) -> None:
        self.device_id = device_id
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.total_stroke_mm = total_stroke_mm
        self.pulses_per_meter = pulses_per_meter
        self.max_pulses = max_pulses
        self.allow_write = allow_write
        self._client = ModbusTcpClient(
            host=host, port=port, unit_id=unit_id, timeout=timeout, read_only=not allow_write,
        )
        self._lock = threading.Lock()
        self._cache: dict[str, Any] | None = None
        self._cache_at: float = 0.0

    # -- 读取 --------------------------------------------------------------

    def read_status(self, force: bool = False) -> dict[str, Any]:
        """读取并解析全部状态，附带高度换算与健康信息。"""
        with self._lock:
            now = time.monotonic()
            if not force and self._cache and (now - self._cache_at) < STATUS_CACHE_TTL:
                return self._cache

            try:
                status = self._client.read_all_status()
                status.update(self._decorate(status))
                self._cache = status
                self._cache_at = now
                return status
            except ModbusError as exc:
                offline = self._offline_payload(exc)
                self._cache = offline
                self._cache_at = now
                return offline

    def _decorate(self, status: dict[str, Any]) -> dict[str, Any]:
        height_m = pulses_to_height_m(
            status["total_pulses"],
            self.pulses_per_meter,
            self.total_stroke_mm,
            self.max_pulses,
        )
        limit_fwd = status["limit_forward"]
        limit_rev = status["limit_reverse"]
        motor = status["motor_status"]

        return {
            "height_m": height_m,
            "height_calibrated": height_m is not None,
            "at_top": limit_fwd == 1,
            "at_bottom": limit_rev == 1,
            "moving": motor != 0,
            "estop_active": False,
        }

    @staticmethod
    def _offline_payload(exc: Exception) -> dict[str, Any]:
        if isinstance(exc, ModbusExceptionResponse):
            reason = "SLAVE_NO_RESPONSE"
        elif isinstance(exc, ModbusTimeout):
            reason = "TIMEOUT"
        else:
            reason = "UNREACHABLE"
        return {
            "online": False,
            "reason": reason,
            "error": str(exc),
            "latency_ms": None,
            "height_m": None,
            "height_calibrated": False,
            "at_top": False,
            "at_bottom": False,
            "moving": False,
            "estop_active": False,
            "motor_status": None,
            "motor_status_text": "未知",
            "limit_forward": None,
            "limit_forward_text": "未知",
            "limit_reverse": None,
            "limit_reverse_text": "未知",
            "total_pulses": None,
            "raw_registers": {},
        }

    def clear_cache(self) -> None:
        with self._lock:
            self._cache = None
            self._cache_at = 0.0

    # -- 诊断 --------------------------------------------------------------

    def probe(self) -> dict[str, Any]:
        result = modbus_probe(self.host, self.port, self.unit_id, self._client.timeout)
        result["device_id"] = self.device_id
        return result

    # -- 写操作（受 allow_write 严格限制） ---------------------------------

    def _write_blocked(self) -> dict[str, Any]:
        return {
            "accepted": False,
            "reason": "READ_ONLY_MODE",
            "message": "系统处于只读监测模式，已拒绝下发控制指令",
        }

    def write_register(self, address: int, value: int) -> dict[str, Any]:
        if not self.allow_write:
            return self._write_blocked()
        try:
            with self._lock:
                self._client.write_single_register(address, value)
                self._cache = None
            return {"accepted": True, "address": f"0x{address:02X}", "value": value}
        except ModbusError as exc:
            return {"accepted": False, "reason": "MODBUS_ERROR", "error": str(exc)}

    def emergency_stop(self) -> dict[str, Any]:
        return self.write_register(REG_CMD_ESTOP, 1)


# ---------------------------------------------------------------------------
# 控制器注册表（按设备 ID 管理，配置来自数据库）
# ---------------------------------------------------------------------------

class FlagControllerRegistry:
    def __init__(self) -> None:
        self._controllers: dict[str, FlagController] = {}
        self._lock = threading.Lock()

    def upsert(self, controller: FlagController) -> None:
        with self._lock:
            self._controllers[controller.device_id] = controller

    def remove(self, device_id: str) -> None:
        with self._lock:
            self._controllers.pop(device_id, None)

    def get(self, device_id: str) -> FlagController | None:
        with self._lock:
            return self._controllers.get(device_id)

    def all(self) -> list[FlagController]:
        with self._lock:
            return list(self._controllers.values())

    def clear(self) -> None:
        with self._lock:
            self._controllers.clear()


registry = FlagControllerRegistry()
