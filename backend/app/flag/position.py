"""
升旗位置追踪 —— 只呈现真实数据，不做任何推算

设计原则（严格遵循"不能有误差"的要求）:
    1. 只有限位开关触发的瞬间才有精确高度，直接展示
    2. 运行中不显示任何推算米数，只显示方向和已运行时间
    3. 中间位置静止时明确标记"位置未知"，绝不猜测

为什么不做推算:
    实测已证明 0x0D/0x0E 是"测距总脉冲"而非实时位置。
    在 USR-K7 + 伺服控制箱这套链路上，没有任何位置反馈。
    用时间积分推算必然有误差（加减速曲线未知、网络延迟 63~220ms 波动、
    丢步、打滑），因此本模块拒绝推算。

未来切换:
    立杆式 PLC (192.168.2.3) 有实时位置 (VD128/VD132/VD136)。
    网络打通后把 source 改成 's7_realtime' 即可，本模块接口不变。
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

#: 位置状态
STATE_AT_TOP = "AT_TOP"                    # 在正零位（顶部），高度精确
STATE_AT_BOTTOM = "AT_BOTTOM"              # 在反零位（底部），高度精确
STATE_MOVING_UP = "MOVING_UP"              # 上升中，高度未知
STATE_MOVING_DOWN = "MOVING_DOWN"          # 下降中，高度未知
STATE_IDLE_UNKNOWN = "IDLE_UNKNOWN"        # 中间位置静止，高度未知

#: 电机状态值 -> 方向
MOTOR_STOP = 0
MOTOR_FORWARD = 1   # 正转 = 上升 = 1
MOTOR_REVERSE = 2   # 反转 = 下降 = 2

#: 正零位/反零位判定（来自寄存器 0x0B / 0x0C 的值 1）
LIMIT_ZERO_POSITION = 1


@dataclass
class PositionSnapshot:
    """一次位置判断的结果，可直接序列化为 API 响应。"""

    state: str
    position_text: str
    height_m: float | None          # 仅在精确时给出
    height_exact: bool
    moving_seconds: float | None
    note: str
    # 审计用：这个结论的依据
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "position_state": self.state,
            "position_text": self.position_text,
            "height_m": self.height_m,
            "height_exact": self.height_exact,
            "moving_seconds": (
                round(self.moving_seconds, 1)
                if self.moving_seconds is not None else None
            ),
            "position_note": self.note,
            "position_evidence": self.evidence,
        }


class FlagPositionTracker:
    """
    基于限位开关的位置追踪器。

    只做三件事:
        1. 检测限位 -> 锁定精确高度
        2. 检测运行 -> 记录方向与起始时刻（用于显示已运行时间）
        3. 其余情况 -> 如实报告"未知"
    """

    def __init__(
        self,
        device_id: str,
        total_stroke_mm: float | None = None,
    ) -> None:
        self.device_id = device_id
        #: 满行程高度（米）。未配置时无法把限位换算成米数，只能报告"在顶部/在底部"
        self.total_stroke_mm = total_stroke_mm
        self._lock = threading.Lock()
        #: 最后一次确认的锚点: 'TOP' | 'BOTTOM' | None
        self._anchor: str | None = None
        self._anchor_at: float | None = None
        #: 当前运动状态
        self._moving: str | None = None       # 'UP' | 'DOWN' | None
        self._moving_since: float | None = None
        #: 上一次观测到的电机状态，用于检测启停
        self._last_motor_status: int | None = None

    # -- 内部 --------------------------------------------------------------

    @property
    def stroke_m(self) -> float | None:
        if self.total_stroke_mm and self.total_stroke_mm > 0:
            return self.total_stroke_mm / 1000.0
        return None

    def _height_for_anchor(self, anchor: str) -> float | None:
        stroke = self.stroke_m
        if stroke is None:
            return None
        return stroke if anchor == "TOP" else 0.0

    def _anchor_label(self, anchor: str) -> str:
        return "正零位(顶部)" if anchor == "TOP" else "反零位(底部)"

    # -- 主入口 ------------------------------------------------------------

    def update(self, status: dict[str, Any]) -> PositionSnapshot:
        """
        用一次寄存器快照更新追踪器并返回位置结论。

        status 需要包含 read_flag_registers 的字段:
            run_status, limit_top, limit_bottom
        """
        motor = status.get("run_status")
        limit_top = status.get("limit_top")
        limit_bottom = status.get("limit_bottom")
        now = time.monotonic()

        with self._lock:
            evidence = {
                "run_status": motor,
                "limit_top": limit_top,
                "limit_bottom": limit_bottom,
            }

            # ---- 1) 限位优先：这是唯一能给出精确高度的依据 ----
            if limit_top == LIMIT_ZERO_POSITION:
                self._anchor = "TOP"
                self._anchor_at = now
                self._moving = None
                self._moving_since = None
                self._last_motor_status = motor
                height = self._height_for_anchor("TOP")
                text = (
                    f"{height:.2f} m" if height is not None
                    else "在正零位(顶部)"
                )
                return PositionSnapshot(
                    state=STATE_AT_TOP,
                    position_text=text,
                    height_m=height,
                    height_exact=True,
                    moving_seconds=None,
                    note=(
                        "限位开关 0x0B=1 实测，高度精确"
                        if height is not None
                        else "限位开关 0x0B=1 实测；未配置行程，无法换算米数"
                    ),
                    evidence=evidence,
                )

            if limit_bottom == LIMIT_ZERO_POSITION:
                self._anchor = "BOTTOM"
                self._anchor_at = now
                self._moving = None
                self._moving_since = None
                self._last_motor_status = motor
                height = self._height_for_anchor("BOTTOM")
                text = (
                    f"{height:.2f} m" if height is not None
                    else "在反零位(底部)"
                )
                return PositionSnapshot(
                    state=STATE_AT_BOTTOM,
                    position_text=text,
                    height_m=height,
                    height_exact=True,
                    moving_seconds=None,
                    note=(
                        "限位开关 0x0C=1 实测，高度精确"
                        if height is not None
                        else "限位开关 0x0C=1 实测；未配置行程，无法换算米数"
                    ),
                    evidence=evidence,
                )

            # ---- 2) 运行中：只报方向和耗时，不给米数 ----
            if motor == MOTOR_FORWARD:
                if self._moving != "UP":
                    self._moving = "UP"
                    self._moving_since = now
                elapsed = now - (self._moving_since or now)
                self._last_motor_status = motor
                return PositionSnapshot(
                    state=STATE_MOVING_UP,
                    position_text=f"↑ 上升中 · 已运行 {elapsed:.1f}s",
                    height_m=None,
                    height_exact=False,
                    moving_seconds=elapsed,
                    note="电机正转运行中；该控制箱无位置反馈，不显示推算高度",
                    evidence=evidence,
                )

            if motor == MOTOR_REVERSE:
                if self._moving != "DOWN":
                    self._moving = "DOWN"
                    self._moving_since = now
                elapsed = now - (self._moving_since or now)
                self._last_motor_status = motor
                return PositionSnapshot(
                    state=STATE_MOVING_DOWN,
                    position_text=f"↓ 下降中 · 已运行 {elapsed:.1f}s",
                    height_m=None,
                    height_exact=False,
                    moving_seconds=elapsed,
                    note="电机反转运行中；该控制箱无位置反馈，不显示推算高度",
                    evidence=evidence,
                )

            # ---- 3) 中间静止：如实报未知 ----
            self._moving = None
            self._moving_since = None
            self._last_motor_status = motor

            if self._anchor:
                anchor_label = self._anchor_label(self._anchor)
                height = self._height_for_anchor(self._anchor)
                return PositionSnapshot(
                    state=STATE_IDLE_UNKNOWN,
                    position_text=f"位置未知（上次在{anchor_label}）",
                    height_m=None,
                    height_exact=False,
                    moving_seconds=None,
                    note=(
                        "旗面在中间位置静止。无位置反馈寄存器，"
                        f"精确高度不可知；上次确认锚点={anchor_label}"
                        + (f"({height:.2f} m)" if height is not None else "")
                    ),
                    evidence=evidence,
                )

            return PositionSnapshot(
                state=STATE_IDLE_UNKNOWN,
                position_text="位置未知",
                height_m=None,
                height_exact=False,
                moving_seconds=None,
                note="尚无任何限位锚点。请先让旗面运行到顶端或底端触发限位开关",
                evidence=evidence,
            )

    # -- 诊断 --------------------------------------------------------------

    def state_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "device_id": self.device_id,
                "anchor": self._anchor,
                "moving": self._moving,
                "stroke_m": self.stroke_m,
                "last_motor_status": self._last_motor_status,
            }


# ---------------------------------------------------------------------------
# 追踪器注册表（与 FlagController 一一对应）
# ---------------------------------------------------------------------------

class PositionTrackerRegistry:
    def __init__(self) -> None:
        self._trackers: dict[str, FlagPositionTracker] = {}
        self._lock = threading.Lock()

    def get_or_create(
        self,
        device_id: str,
        total_stroke_mm: float | None = None,
    ) -> FlagPositionTracker:
        with self._lock:
            tracker = self._trackers.get(device_id)
            if tracker is None:
                tracker = FlagPositionTracker(device_id, total_stroke_mm)
                self._trackers[device_id] = tracker
            else:
                # 行程可能被修改，同步最新配置
                tracker.total_stroke_mm = total_stroke_mm
            return tracker

    def remove(self, device_id: str) -> None:
        with self._lock:
            self._trackers.pop(device_id, None)

    def all(self) -> list[FlagPositionTracker]:
        with self._lock:
            return list(self._trackers.values())

    def clear(self) -> None:
        with self._lock:
            self._trackers.clear()


trackers = PositionTrackerRegistry()
