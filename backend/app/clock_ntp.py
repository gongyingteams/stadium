"""UDP protocol client for TimeMaster master clock (0xDD/0xEE binary frame protocol)."""
from __future__ import annotations

import asyncio
import socket
import struct
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


class ClockProtocolError(RuntimeError):
    """Raised on checksum, framing, or device error responses."""


class ClockBusyError(ClockProtocolError):
    """Raised when the master clock replies 0x11 (busy)."""


class ClockTimeoutError(TimeoutError):
    """Raised when the master clock does not reply within timeout + retries."""


FUNC_NAMES: dict[int, str] = {
    0x01: "计时状态设置/查询",
    0x04: "屏幕开关",
    0x06: "分时段亮度",
    0x07: "音频开关与音量",
    0x08: "校准间隔",
    0x09: "子钟属性/增删",
    0x0A: "时偏设置/查询",
    0x0B: "卫星数主动上报",
    0x0C: "子钟故障主动上报",
    0x0D: "时区设置/查询",
    0x0E: "广播计时控制",
    0x0F: "定点计时控制",
    0x10: "查询 NTP 时间",
    0x11: "设备忙",
    0x12: "校验错误",
    0x13: "命令 ACK",
    0x14: "重复添加设备",
    0x15: "查询卫星数",
}


def build_frame(addr: int, func: int, data: bytes = b"") -> bytes:
    """Build DD [len] [addr] [func] [data...] [cksum] DA."""
    length = 2 + len(data)
    body = bytes([length & 0xFF, addr & 0xFF, func & 0xFF]) + data
    cksum = sum(body) & 0xFF
    return b"\xdd" + body + bytes([cksum, 0xDA])


def split_frames(raw: bytes) -> list[bytes]:
    """Split a UDP datagram that may contain multiple concatenated EE..EA frames."""
    frames: list[bytes] = []
    idx = 0
    n = len(raw)
    while idx < n:
        if raw[idx] != 0xEE:
            next_ee = raw.find(b"\xee", idx + 1)
            if next_ee == -1:
                break
            idx = next_ee
            continue
        if idx + 4 > n:
            break
        length = raw[idx + 1]
        total = 4 + length
        if idx + total <= n and raw[idx + total - 1] == 0xEA:
            frames.append(raw[idx : idx + total])
            idx += total
        else:
            # Fallback: try finding next EA
            end = raw.find(b"\xea", idx + 2)
            if end == -1:
                break
            frames.append(raw[idx : end + 1])
            idx = end + 1
    return frames or [raw]


def parse_frame(raw: bytes) -> dict[str, Any]:
    """Parse EE [len] [addr] [func] [data...] [cksum] EA."""
    if len(raw) < 6:
        raise ClockProtocolError(f"报文长度过短 ({len(raw)}B)")
    if raw[0] != 0xEE or raw[-1] != 0xEA:
        raise ClockProtocolError(f"帧头/帧尾无效 (head=0x{raw[0]:02X}, tail=0x{raw[-1]:02X})")
    length = raw[1]
    expected_total = 1 + 1 + length + 1 + 1  # EE + len + body(length) + cksum + EA
    if len(raw) != expected_total:
        raise ClockProtocolError(f"帧长度不匹配 (声明 len={length}, 实际总长={len(raw)})")
    body = raw[1 : 2 + length]
    cksum = raw[-2]
    calc = sum(body) & 0xFF
    if calc != cksum:
        raise ClockProtocolError(f"校验和错误 (收到 0x{cksum:02X}, 计算 0x{calc:02X})")
    addr = raw[2]
    func = raw[3]
    data = raw[4 : 2 + length]
    return {"addr": addr, "func": func, "data": data, "raw": raw, "hex": raw.hex(" ").upper()}


@dataclass
class ClockRuntimeState:
    online: bool = False
    last_seen_at: float = 0.0
    last_error: str = ""
    master_unix_s: int | None = None
    platform_drift_ms: float | None = None
    satellite_count: int | None = None
    timezone: int | None = None
    offset_s: int | None = None
    sync_interval_s: int | None = None
    protocol_logs: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=60))
    events: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=40))


class MasterClockClient:
    """Single-reader-loop UDP client with serialized request-response + unsolicited 0x0B/0x0C push."""

    def __init__(self) -> None:
        self.host: str = "192.168.7.2"
        self.port: int = 123
        self.local_port: int = 0
        self.timeout_s: float = 4.0
        self.retries: int = 2
        self.state = ClockRuntimeState()
        self._sock: socket.socket | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._tx_lock = asyncio.Lock()
        self._pending_func: int | None = None
        self._pending_future: asyncio.Future[dict[str, Any]] | None = None
        self._listeners: list[Callable[[dict[str, Any]], Awaitable[None]]] = []

    def configure(self, host: str, port: int, local_port: int = 0, timeout_s: float = 4.0, retries: int = 2) -> None:
        need_rebind = (
            self._sock is not None
            and (host != self.host or port != self.port or local_port != self.local_port)
        )
        self.host = host
        self.port = int(port)
        self.local_port = int(local_port)
        self.timeout_s = float(timeout_s)
        self.retries = int(retries)
        if need_rebind:
            self.close_socket()

    def add_listener(self, cb: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        if cb not in self._listeners:
            self._listeners.append(cb)

    def remove_listener(self, cb: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        if cb in self._listeners:
            self._listeners.remove(cb)

    def _emit_log(self, direction: str, func: int, frame: bytes, desc: str) -> dict[str, Any]:
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "direction": direction,
            "cmdName": f"0x{func:02X} {FUNC_NAMES.get(func, '协议帧')}",
            "rawHex": frame.hex(" ").upper(),
            "desc": desc,
        }
        self.state.protocol_logs.appendleft(entry)
        return entry

    async def _broadcast(self, msg: dict[str, Any]) -> None:
        for cb in list(self._listeners):
            try:
                await cb(msg)
            except Exception:
                pass

    def _ensure_socket(self) -> None:
        if self._sock is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind(("0.0.0.0", self.local_port))
        self._sock = sock
        if self._reader_task is None or self._reader_task.done():
            self._reader_task = asyncio.create_task(self._reader_loop())

    def close_socket(self) -> None:
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
        self._reader_task = None
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    async def _reader_loop(self) -> None:
        loop = asyncio.get_running_loop()
        while self._sock is not None:
            try:
                raw, _addr = await loop.sock_recvfrom(self._sock, 1024)
            except asyncio.CancelledError:
                break
            except OSError:
                await asyncio.sleep(0.2)
                continue

            for sub_raw in split_frames(raw):
                try:
                    parsed = parse_frame(sub_raw)
                except ClockProtocolError as exc:
                    self._emit_log("RX", 0x00, sub_raw, f"异常帧: {exc}")
                    continue

                func = parsed["func"]
                data = parsed["data"]
                addr = parsed["addr"]
                self.state.online = True
                self.state.last_seen_at = time.time()
                self.state.last_error = ""

                # Unsolicited 0x0B: satellite count change
                if func == 0x0B and len(data) >= 1:
                    sat = data[0]
                    self.state.satellite_count = sat
                    log_item = self._emit_log("RX", func, sub_raw, f"母钟主动上报当前锁定卫星数: {sat}")
                    evt = {"type": "satellite_change", "satellite_count": sat, "time": log_item["time"]}
                    self.state.events.appendleft(evt)
                    await self._broadcast({"type": "clock_event", "event": evt, "log": log_item})
                    continue

                # Unsolicited 0x0C: sub-clock fault / recovery
                if func == 0x0C and len(data) >= 1:
                    bus_id = (data[0] >> 4) & 0x0F
                    fault = data[0] & 0x0F
                    status_txt = "故障" if fault == 1 else "恢复正常"
                    log_item = self._emit_log("RX", func, sub_raw, f"子钟 #{addr} (总线 {bus_id}) 状态上报: {status_txt}")
                    evt = {"type": "subclock_fault", "mac": addr, "bus": bus_id, "fault": fault == 1, "time": log_item["time"]}
                    self.state.events.appendleft(evt)
                    await self._broadcast({"type": "clock_event", "event": evt, "log": log_item})
                    continue

                log_item = self._emit_log("RX", func, sub_raw, f"收到母钟应答 (地址 0x{addr:02X})")
                await self._broadcast({"type": "clock_log", "log": log_item})

                fut = self._pending_future
                if fut and not fut.done():
                    if func == 0x11:
                        fut.set_exception(ClockBusyError("母钟正忙 (0x11)，请稍后重试"))
                    elif func == 0x12:
                        fut.set_exception(ClockProtocolError("母钟返回校验错误 (0x12)"))
                    elif func == 0x14:
                        fut.set_exception(ClockProtocolError("重复添加设备 (0x14)：该屏号已注册"))
                    elif func == self._pending_func or (func == 0x13 and self._pending_func in (0x08, 0x0D, 0x0E)):
                        fut.set_result(parsed)

    async def send_and_wait(
        self,
        addr: int,
        func: int,
        data: bytes = b"",
        desc: str = "",
        timeout_s: float | None = None,
        retries: int | None = None,
    ) -> dict[str, Any]:
        frame = build_frame(addr, func, data)
        eff_timeout = self.timeout_s if timeout_s is None else float(timeout_s)
        eff_retries = self.retries if retries is None else int(retries)
        async with self._tx_lock:
            self._ensure_socket()
            loop = asyncio.get_running_loop()
            last_exc: Exception | None = None

            for attempt in range(eff_retries + 1):
                fut: asyncio.Future[dict[str, Any]] = loop.create_future()
                self._pending_func = func
                self._pending_future = fut
                log_item = self._emit_log("TX", func, frame, desc or f"下发 {FUNC_NAMES.get(func, '')} (第{attempt+1}次)")
                await self._broadcast({"type": "clock_log", "log": log_item})
                try:
                    await loop.sock_sendto(self._sock, frame, (self.host, self.port))
                    res = await asyncio.wait_for(fut, timeout=eff_timeout)
                    return res
                except asyncio.TimeoutError as exc:
                    last_exc = ClockTimeoutError(f"母钟 {self.host}:{self.port} 应答超时 ({eff_timeout}s)")
                except ClockBusyError as exc:
                    last_exc = exc
                    if attempt < eff_retries:
                        await asyncio.sleep(0.35)
                        continue
                    break
                except ClockProtocolError as exc:
                    last_exc = exc
                    break
                except OSError as exc:
                    last_exc = ClockProtocolError(f"UDP 发送失败: {exc}")
                    break
                finally:
                    self._pending_future = None
                    self._pending_func = None

            self.state.online = False
            self.state.last_error = str(last_exc)
            raise last_exc  # type: ignore[misc]

    # ---- High-level protocol methods -------------------------------------

    async def query_ntp_time(self, timeout_s: float | None = None, retries: int | None = None) -> dict[str, Any]:
        res = await self.send_and_wait(0xFF, 0x10, b"\x00", "查询母钟 Unix 时间戳", timeout_s=timeout_s, retries=retries)
        data = res["data"]
        if len(data) < 4:
            raise ClockProtocolError("0x10 应答时间戳长度不足 4 字节")
        unix_s = struct.unpack(">I", data[:4])[0]
        local_s = time.time()
        drift_ms = round((local_s - unix_s) * 1000, 1)
        self.state.master_unix_s = unix_s
        self.state.platform_drift_ms = drift_ms
        return {"master_unix_s": unix_s, "local_unix_s": round(local_s, 3), "drift_ms": drift_ms, "rx_hex": res["hex"]}

    async def query_satellites(self, timeout_s: float | None = None, retries: int | None = None) -> int:
        res = await self.send_and_wait(0xFF, 0x15, b"\x00", "查询母钟当前锁定卫星数", timeout_s=timeout_s, retries=retries)
        sat = res["data"][0] if res["data"] else 0
        self.state.satellite_count = sat
        return sat

    async def set_timezone(self, tz: int) -> int:
        if not (-12 <= tz <= 12):
            raise ClockProtocolError("时区范围必须为 -12 ~ 12")
        byte_val = tz & 0xFF
        res = await self.send_and_wait(0xFF, 0x0D, bytes([byte_val]), f"设置母钟时区 UTC{tz:+d}")
        val = res["data"][0] if res["data"] else byte_val
        signed_tz = val - 256 if val > 127 else val
        self.state.timezone = signed_tz
        return signed_tz

    async def set_offset(self, seconds: int) -> dict[str, Any]:
        neg = seconds < 0
        mag = abs(int(seconds))
        if mag > 0x7FFFFF:
            raise ClockProtocolError("时偏秒数超出 23 位范围")
        raw_val = mag | (0x800000 if neg else 0)
        payload = bytes([(raw_val >> 16) & 0xFF, (raw_val >> 8) & 0xFF, raw_val & 0xFF])
        res = await self.send_and_wait(0xFF, 0x0A, payload, f"设置时偏 {seconds:+d}s")
        self.state.offset_s = seconds
        return {"offset_s": seconds, "rx_hex": res["hex"]}

    async def set_sync_interval(self, seconds: int) -> dict[str, Any]:
        sec = max(1, min(0xFFFFFF, int(seconds)))
        payload = bytes([(sec >> 16) & 0xFF, (sec >> 8) & 0xFF, sec & 0xFF])
        try:
            res = await self.send_and_wait(0xFF, 0x08, payload, f"广播校准间隔 {sec}s", timeout_s=1.0, retries=0)
            rx_hex = res["hex"]
        except ClockTimeoutError:
            # 0xFF 广播帧部分固件不应答，发后即止
            rx_hex = "(广播已下发)"
        self.state.sync_interval_s = sec
        return {"sync_interval_s": sec, "rx_hex": rx_hex}

    async def set_screen(self, addr: int, on: bool) -> dict[str, Any]:
        res = await self.send_and_wait(addr, 0x04, bytes([1 if on else 2]), f"子钟 #{addr} 屏幕{'开启' if on else '关闭'}")
        return {"addr": addr, "screen": on, "rx_hex": res["hex"]}

    async def set_brightness(self, addr: int, seg1: tuple[int, int, int, int, int], seg2: tuple[int, int, int, int, int]) -> dict[str, Any]:
        payload = bytes([
            seg1[0] & 0xFF, seg1[1] & 0xFF, seg1[2] & 0xFF, seg1[3] & 0xFF, max(1, min(5, seg1[4])),
            seg2[0] & 0xFF, seg2[1] & 0xFF, seg2[2] & 0xFF, seg2[3] & 0xFF, max(1, min(5, seg2[4])),
        ])
        res = await self.send_and_wait(addr, 0x06, payload, f"子钟 #{addr} 分时段亮度设置")
        return {"addr": addr, "rx_hex": res["hex"]}

    async def set_audio(self, addr: int, on: bool, volume: int) -> dict[str, Any]:
        vol = max(1, min(10, int(volume))) if on else 0
        res = await self.send_and_wait(addr, 0x07, bytes([1 if on else 2, vol]), f"子钟 #{addr} 音频{'开' if on else '关'} 音量{vol}")
        return {"addr": addr, "audio": on, "volume": vol, "rx_hex": res["hex"]}

    async def set_timer(self, addr: int, mode: int, hours: int, minutes: int, seconds: int) -> dict[str, Any]:
        payload = bytes([mode & 0xFF, min(99, max(0, hours)), min(59, max(0, minutes)), min(59, max(0, seconds))])
        mode_txt = {1: "正计时", 2: "倒计时", 3: "恢复时钟"}.get(mode, f"模式{mode}")
        res = await self.send_and_wait(addr, 0x01, payload, f"子钟 #{addr} {mode_txt} {hours:02d}:{minutes:02d}:{seconds:02d}")
        return {"addr": addr, "mode": mode, "rx_hex": res["hex"]}

    async def broadcast_timer(self, bus_type: int, start: bool) -> dict[str, Any]:
        val = ((bus_type & 0x0F) << 4) | (1 if start else 0)
        res = await self.send_and_wait(0xFF, 0x0E, bytes([val]), f"总线 {bus_type} 广播{'开始计时' if start else '恢复时钟'}")
        return {"bus_type": bus_type, "start": start, "rx_hex": res["hex"]}

    async def point_timer(self, addr: int, start: bool) -> dict[str, Any]:
        res = await self.send_and_wait(addr, 0x0F, bytes([1 if start else 0]), f"子钟 #{addr} 定点{'开始计时' if start else '恢复时钟'}")
        return {"addr": addr, "start": start, "rx_hex": res["hex"]}

    async def add_sub_clock(self, addr: int, link: int, clock_type: int) -> dict[str, Any]:
        val = ((link & 0x0F) << 4) | (clock_type & 0x0F)
        res = await self.send_and_wait(addr, 0x09, bytes([val]), f"注册子钟 #{addr} (链路{link}, 类型{clock_type})")
        if not res["data"] or res["data"][0] == 0x00:
            raise ClockProtocolError(f"母钟未找到设备 #{addr} (0x09 应答 00)，请检查链路与屏号")
        return {"addr": addr, "link": link, "clock_type": clock_type, "rx_hex": res["hex"]}

    async def remove_sub_clock(self, addr: int) -> dict[str, Any]:
        res = await self.send_and_wait(addr, 0x09, b"\xFF", f"删除子钟 #{addr}")
        return {"addr": addr, "removed": True, "rx_hex": res["hex"]}


clock_client = MasterClockClient()


async def probe_master_clock(host: str, port: int, local_port: int = 0, timeout_s: float = 2.0) -> dict[str, Any]:
    """One-shot UDP probe for settings connectivity test (0x15 satellite query)."""
    frame = build_frame(0xFF, 0x15, b"\x00")
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    try:
        try:
            sock.bind(("0.0.0.0", int(local_port)))
        except OSError:
            sock.bind(("0.0.0.0", 0))
        t0 = time.perf_counter()
        await loop.sock_sendto(sock, frame, (host, int(port)))
        raw, _ = await asyncio.wait_for(loop.sock_recvfrom(sock, 1024), timeout=float(timeout_s))
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        frames = [parse_frame(f) for f in split_frames(raw)]
        sat_frame = next((f for f in frames if f["func"] == 0x15), frames[-1])
        sat = sat_frame["data"][0] if sat_frame["data"] else None
        return {"reachable": True, "latency_ms": latency_ms, "satellite_count": sat, "rx_hex": raw.hex(" ").upper()}
    except asyncio.TimeoutError:
        return {"reachable": False, "error": f"UDP {host}:{port} 应答超时 ({timeout_s}s)"}
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}
    finally:
        sock.close()
