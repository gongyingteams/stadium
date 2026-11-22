"""
电机保护层 —— 防止上位机失误导致电机无法停止

背景:
    2026-11-16 15:41 现场发生电机持续反转无法停止的事故。
    根因: 上位机下发 0x07=1 后，PLC 会持续运行直到碰到限位；
          若上位机不主动干预，一旦限位失效就永远转下去。

本模块提供三层保护:
    1. 超时自动急停 —— 任何运动指令超过最大时长，自动写 0x0A=1
    2. 心跳看门狗 —— 上位机长时间无交互，自动急停
    3. 限位预检 —— 已在顶部禁止上升、已在底部禁止下降

所有保护都在后台线程执行，即使前端崩溃也能生效。
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

#: 单次运动的默认最大时长（秒）
#: 依据: 国歌最长 49.4s，满行程 12m 需 ~48.5s，留 30% 余量
DEFAULT_MAX_MOVING_SECONDS = 75.0

#: 心跳超时（秒）—— 上位机超过此时长无任何请求则自动急停
DEFAULT_HEARTBEAT_TIMEOUT = 120.0

#: 保护检查周期（秒）
WATCH_INTERVAL = 0.5


class UnsafeCommand(Exception):
    """命令被安全策略拒绝。"""


class MotionGuard:
    """
    单个设备的运动保护器。

    用法:
        guard.on_motion_started('UP')
        ... 后台每 0.5s 调 guard.tick()
        guard.on_motion_stopped()
    """

    def __init__(
        self,
        device_id: str,
        emergency_callback: Callable[[], Any],
        max_moving_seconds: float = DEFAULT_MAX_MOVING_SECONDS,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
    ) -> None:
        self.device_id = device_id
        self._emergency = emergency_callback
        self.max_moving_seconds = max_moving_seconds
        self.heartbeat_timeout = heartbeat_timeout

        self._lock = threading.Lock()
        self._motion_started_at: float | None = None
        self._motion_direction: str | None = None
        self._last_heartbeat = time.monotonic()
        self._auto_stop_count = 0
        self._last_auto_stop_reason: str | None = None
        #: 强制锁：急停触发后，未显式解除前禁止再下发运动指令
        self._latched = False

    # -- 心跳 --------------------------------------------------------------

    def heartbeat(self) -> None:
        """前端每次请求都调用，刷新看门狗。"""
        with self._lock:
            self._last_heartbeat = time.monotonic()

    # -- 运动生命周期 -------------------------------------------------------

    def on_motion_started(self, direction: str) -> None:
        with self._lock:
            self._motion_started_at = time.monotonic()
            self._motion_direction = direction

    def on_motion_stopped(self) -> None:
        with self._lock:
            self._motion_started_at = None
            self._motion_direction = None

    def is_latched(self) -> bool:
        with self._lock:
            return self._latched

    def clear_latch(self) -> None:
        """人工确认现场安全后，解除急停锁。"""
        with self._lock:
            self._latched = False
            self._motion_started_at = None
            self._motion_direction = None

    # -- 指令前安全检查 -----------------------------------------------------

    def check_can_move(
        self,
        direction: str,
        run_status: int | None,
        limit_top: int | None,
        limit_bottom: int | None,
    ) -> None:
        """
        下发运动指令前调用。不满足条件抛 UnsafeCommand。

        direction: 'UP' | 'DOWN'
        """
        with self._lock:
            if self._latched:
                raise UnsafeCommand(
                    "急停保护已锁定（上次自动急停触发）。"
                    "请确认现场安全后调用 /api/flag/devices/{id}/clear-latch 解除"
                )
            if self._motion_started_at is not None:
                elapsed = time.monotonic() - self._motion_started_at
                raise UnsafeCommand(
                    f"电机已在运行中（{self._motion_direction}, 已 {elapsed:.1f}s），"
                    "请先停止再下发新指令"
                )

        if run_status not in (None, 0):
            raise UnsafeCommand(f"电机未处于停止状态（0x04={run_status}），拒绝下发运动指令")

        if direction == "UP" and limit_top == 1:
            raise UnsafeCommand("已在正零位（顶部），禁止继续上升，否则将顶死机械结构")
        if direction == "DOWN" and limit_bottom == 1:
            raise UnsafeCommand("已在反零位（底部），禁止继续下降，否则将顶死机械结构")

    # -- 后台巡检 -----------------------------------------------------------

    def tick(self, run_status: int | None) -> bool:
        """
        后台每 WATCH_INTERVAL 调用一次。

        返回 True 表示本次触发了自动急停。
        """
        now = time.monotonic()
        reason: str | None = None

        with self._lock:
            if run_status == 0:
                # 电机已停止，清除运动计时（plc 自己到了限位）
                if self._motion_started_at is not None:
                    self._motion_started_at = None
                    self._motion_direction = None
                return False

            # 电机在运行
            if self._motion_started_at is None:
                # 上位机不知道它启动了（比如 PLC 自己触发），也要监控
                self._motion_started_at = now
                self._motion_direction = self._motion_direction or "UNKNOWN"

            elapsed = now - self._motion_started_at

            if elapsed > self.max_moving_seconds:
                reason = (
                    f"运动超时 {elapsed:.1f}s > 上限 {self.max_moving_seconds:.0f}s，"
                    "自动急停"
                )
            elif now - self._last_heartbeat > self.heartbeat_timeout:
                idle = now - self._last_heartbeat
                reason = (
                    f"上位机心跳丢失 {idle:.0f}s > 上限 "
                    f"{self.heartbeat_timeout:.0f}s，自动急停"
                )

            if reason:
                self._latched = True
                self._auto_stop_count += 1
                self._last_auto_stop_reason = reason
                self._motion_started_at = None
                self._motion_direction = None

        if reason:
            try:
                self._emergency()
            except Exception:
                # 急停自己失败时不能抛出去，否则看门狗停了
                pass
            return True
        return False

    def state_dict(self) -> dict[str, Any]:
        with self._lock:
            now = time.monotonic()
            return {
                "device_id": self.device_id,
                "latched": self._latched,
                "moving_direction": self._motion_direction,
                "moving_seconds": (
                    round(now - self._motion_started_at, 1)
                    if self._motion_started_at is not None else None
                ),
                "max_moving_seconds": self.max_moving_seconds,
                "heartbeat_age_seconds": round(now - self._last_heartbeat, 1),
                "heartbeat_timeout": self.heartbeat_timeout,
                "auto_stop_count": self._auto_stop_count,
                "last_auto_stop_reason": self._last_auto_stop_reason,
            }


class MotionGuardRegistry:
    """管理所有设备的 MotionGuard，并运行统一后台巡检线程。"""

    def __init__(self) -> None:
        self._guards: dict[str, MotionGuard] = {}
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        #: 由上层注入: device_id -> 当前 run_status 读取函数
        self._status_reader: Callable[[str], int | None] | None = None

    def set_status_reader(self, reader: Callable[[str], int | None]) -> None:
        self._status_reader = reader

    def get_or_create(
        self,
        device_id: str,
        emergency_callback: Callable[[], Any],
        max_moving_seconds: float = DEFAULT_MAX_MOVING_SECONDS,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
    ) -> MotionGuard:
        with self._lock:
            guard = self._guards.get(device_id)
            if guard is None:
                guard = MotionGuard(
                    device_id, emergency_callback,
                    max_moving_seconds, heartbeat_timeout,
                )
                self._guards[device_id] = guard
            return guard

    def get(self, device_id: str) -> MotionGuard | None:
        with self._lock:
            return self._guards.get(device_id)

    def remove(self, device_id: str) -> None:
        with self._lock:
            self._guards.pop(device_id, None)

    def all(self) -> list[MotionGuard]:
        with self._lock:
            return list(self._guards.values())

    # -- 后台线程 -----------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="flag-motion-guard", daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            guards = self.all()
            reader = self._status_reader
            if reader:
                for guard in guards:
                    try:
                        run_status = reader(guard.device_id)
                    except Exception:
                        continue
                    guard.tick(run_status)
            self._stop_event.wait(WATCH_INTERVAL)

    def state_list(self) -> list[dict[str, Any]]:
        return [g.state_dict() for g in self.all()]


guards = MotionGuardRegistry()
