"""智能升旗 WebSocket 实时状态广播服务。

架构说明（混合模式）：
- 状态同步：后端单协程有序轮询 USR-K7 串口网关，通过 WebSocket 广播给所有在线前端，
  避免多端/多标签页并发访问 9600 bps 串口造成阻塞。
- 指令下发：保留 HTTP POST (/api/flag/command) 强回执语义，指令执行后立即触发一次 WS 广播。
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import WebSocket

from app.flag.motion_guard import guards
from app.flag_modbus import (
    FLAG_MODBUS_UNIT_ID,
    ModbusCommandError,
    ModbusConnectionError,
    read_flag_registers,
)


class FlagWsHub:
    """单实例采集 + 多客户端 WebSocket 广播中心。"""

    def __init__(self) -> None:
        self._clients: dict[WebSocket, int] = {}
        self._lock = asyncio.Lock()
        self._wake_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._last_run_status: dict[int, int] = {}
        self._last_online: dict[int, bool] = {}

    async def connect(self, ws: WebSocket, unit_id: int = FLAG_MODBUS_UNIT_ID) -> None:
        await ws.accept()
        async with self._lock:
            self._clients[ws] = unit_id
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._poll_loop())
        self._wake_event.set()

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.pop(ws, None)

    def trigger_refresh(self) -> None:
        """唤醒采集循环立即执行一次状态读取。"""
        self._wake_event.set()

    async def broadcast_status(self, unit_id: int, status: dict[str, Any], event: str = "command") -> None:
        """在 HTTP 控制指令执行完成后，立即把最新状态推送给所有订阅客户端。"""
        self._last_run_status[unit_id] = int(status.get("run_status", 0))
        self._last_online[unit_id] = True
        payload = {
            "type": "flag_status",
            "event": event,
            "online": True,
            "mode": "modbus_tcp_gateway",
            "unit_id": unit_id,
            "data": {"online": True, "mode": "modbus_tcp_gateway", **status},
            "guards": guards.state_list(),
            "ts": round(time.time(), 3),
        }
        await self._send_to_unit(unit_id, payload)

    async def _send_to_unit(self, unit_id: int, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = [ws for ws, uid in self._clients.items() if uid == unit_id]
        if not targets:
            return
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.pop(ws, None)

    async def _poll_loop(self) -> None:
        while True:
            async with self._lock:
                unit_ids = sorted(set(self._clients.values()))
            if not unit_ids:
                # 无在线客户端时停止后台轮询，避免无谓占用串口资源
                return

            any_moving = False
            any_offline = False

            for uid in unit_ids:
                try:
                    data = await asyncio.to_thread(read_flag_registers, uid)
                    run_st = int(data.get("run_status", 0))
                    self._last_run_status[uid] = run_st
                    self._last_online[uid] = True
                    if run_st != 0:
                        any_moving = True
                    payload = {
                        "type": "flag_status",
                        "event": "poll",
                        "online": True,
                        "mode": "modbus_tcp_gateway",
                        "unit_id": uid,
                        "data": {"online": True, "mode": "modbus_tcp_gateway", **data},
                        "guards": guards.state_list(),
                        "ts": round(time.time(), 3),
                    }
                    await self._send_to_unit(uid, payload)
                except (ModbusConnectionError, ModbusCommandError) as exc:
                    any_offline = True
                    self._last_online[uid] = False
                    payload = {
                        "type": "flag_status",
                        "event": "poll_error",
                        "online": False,
                        "unit_id": uid,
                        "error": str(exc),
                        "guards": guards.state_list(),
                        "ts": round(time.time(), 3),
                    }
                    await self._send_to_unit(uid, payload)
                except Exception as exc:
                    any_offline = True
                    payload = {
                        "type": "flag_status",
                        "event": "poll_error",
                        "online": False,
                        "unit_id": uid,
                        "error": f"采集异常: {exc}",
                        "guards": guards.state_list(),
                        "ts": round(time.time(), 3),
                    }
                    await self._send_to_unit(uid, payload)

            # 动态节拍：运动中 0.3s 快速追踪限位与状态，待机时 1.5s，离线时 2.5s
            interval = 0.3 if any_moving else (2.5 if any_offline else 1.5)
            self._wake_event.clear()
            try:
                await asyncio.wait_for(self._wake_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass


flag_ws_hub = FlagWsHub()
