"""
升旗硬件 Modbus TCP 驱动层 (零第三方依赖，仅用标准库)

现场链路:
    上位机 --Modbus TCP--> USR-K7 网关(192.168.0.7:20108) --Modbus RTU/RS485--> 升旗PLC(unit=1)

协议要点:
    - Modbus TCP 带 MBAP 头 (7 字节: tid/pid/len/unit)，不带 CRC
    - 功能码 0x03 读保持寄存器 / 0x06 写单寄存器
    - 所有寄存器均为 16 位无符号整数

安全设计:
    本模块默认 READ_ONLY=True，只允许读操作。
    写操作必须显式传入 allow_write=True，且由上层做二次确认与审计。
"""
from __future__ import annotations

import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# 寄存器定义（来源: docs/自动升旗系统对接文档.docx 第一章）
# ---------------------------------------------------------------------------

REG_MANUAL_RPM = 0x01        # RW 手动模式电机转速 (1位小数, RPM)
REG_ANTHEM_DURATION = 0x02   # RW 国歌时长 (0.1S)
REG_PULSES_PER_REV = 0x03    # RW 伺服电机每转脉冲个数 (默认 10000)
REG_MOTOR_STATUS = 0x04      # R  电机运行状态 0停止 1正转 2反转
REG_AUTO_RPM = 0x05          # R  自动模式电机转速 (1位小数, RPM)
REG_CMD_FORWARD = 0x06       # W  手动正转 (停止状态下写1有效)
REG_CMD_REVERSE = 0x07       # W  手动反转 (停止状态下写1有效)
REG_CMD_AUTO_UP = 0x08       # W  自动升旗 (停止状态下写1有效)
REG_CMD_MEASURE = 0x09       # W  自动测距 (停止+正限位, 写1有效)
REG_CMD_ESTOP = 0x0A         # W  急停 (任何状态写1有效)
REG_LIMIT_FWD = 0x0B         # R  正转限位 0未在限位 1正零位 2正限位
REG_LIMIT_REV = 0x0C         # R  反转限位 0未在限位 1反零位 2反限位
REG_PULSE_LOW = 0x0D         # R  测距脉冲数 低16位
REG_PULSE_HIGH = 0x0E        # R  测距脉冲数 高16位

#: 只读监测需要轮询的寄存器组（连续读取可以减少往返次数）
READ_BLOCK_START = REG_MANUAL_RPM      # 0x01
READ_BLOCK_COUNT = 0x0E - 0x01 + 1     # 0x01..0x0E 共 14 个

#: 电机状态枚举
MOTOR_STATUS_TEXT = {0: "停止", 1: "正转", 2: "反转"}

#: 限位枚举
LIMIT_TEXT = {0: "未在限位", 1: "在零位", 2: "在限位"}

#: Modbus 异常码
EXCEPTION_TEXT = {
    0x01: "非法功能码",
    0x02: "非法数据地址",
    0x03: "非法数据值",
    0x04: "从站设备故障",
    0x05: "确认(处理中)",
    0x06: "从站设备忙",
    0x08: "存储奇偶性差错",
    0x0A: "网关路径不可用",
    0x0B: "网关目标设备无响应",
}


class ModbusError(Exception):
    """Modbus 通信或协议异常。"""


class ModbusTimeout(ModbusError):
    """通信超时。"""


class ModbusExceptionResponse(ModbusError):
    """从站返回了异常响应 (功能码 | 0x80)。"""

    def __init__(self, function_code: int, exception_code: int) -> None:
        self.function_code = function_code
        self.exception_code = exception_code
        super().__init__(
            f"从站异常响应: 功能码 0x{function_code:02X}, "
            f"异常码 0x{exception_code:02X} ({EXCEPTION_TEXT.get(exception_code, '未知')})"
        )


# ---------------------------------------------------------------------------
# 客户端
# ---------------------------------------------------------------------------

@dataclass
class ModbusTcpClient:
    """极简 Modbus TCP 客户端（每次请求建立短连接，适合低频轮询与指令下发）。"""

    host: str
    port: int = 502
    unit_id: int = 1
    timeout: float = 3.0
    read_only: bool = True
    _tid: int = field(default=0, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    # -- 底层收发 ----------------------------------------------------------

    def _next_tid(self) -> int:
        with self._lock:
            self._tid = (self._tid + 1) & 0xFFFF
            return self._tid

    def _request(self, pdu: bytes) -> bytes:
        """发送一个 PDU，返回从站响应的 PDU 部分。"""
        tid = self._next_tid()
        frame = struct.pack(">HHH", tid, 0, len(pdu) + 1) + bytes([self.unit_id]) + pdu

        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout)
                sock.sendall(frame)

                header = self._recv_exact(sock, 7)
                r_tid, r_pid, r_len, r_unit = struct.unpack(">HHHB", header)
                if r_len < 2:
                    raise ModbusError(f"响应长度非法: {r_len}")
                body = self._recv_exact(sock, r_len - 1)
        except ModbusError:
            raise
        except socket.timeout as exc:
            raise ModbusTimeout(
                f"通信超时 {self.host}:{self.port} unit={self.unit_id}"
            ) from exc
        except OSError as exc:
            raise ModbusError(f"连接失败 {self.host}:{self.port} -> {exc}") from exc

        if r_tid != tid:
            raise ModbusError(f"事务号不匹配: 期望 {tid}, 收到 {r_tid}")

        function_code = body[0]
        if function_code & 0x80:
            exception_code = body[1] if len(body) > 1 else 0
            raise ModbusExceptionResponse(function_code & 0x7F, exception_code)
        return body

    @staticmethod
    def _recv_exact(sock: socket.socket, size: int) -> bytes:
        chunks: list[bytes] = []
        remaining = size
        while remaining > 0:
            chunk = sock.recv(remaining)
            if not chunk:
                raise ModbusError("连接被从站关闭，数据不完整")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    # -- 公共 API ----------------------------------------------------------

    def read_holding_registers(self, address: int, count: int = 1) -> list[int]:
        """功能码 0x03：读保持寄存器。"""
        if count < 1 or count > 125:
            raise ValueError("count 必须在 1..125 之间")
        pdu = struct.pack(">BHH", 0x03, address, count)
        body = self._request(pdu)
        byte_count = body[1]
        payload = body[2:2 + byte_count]
        if len(payload) != count * 2:
            raise ModbusError(f"数据长度不符: 期望 {count * 2}, 收到 {len(payload)}")
        return list(struct.unpack(f">{count}H", payload))

    def write_single_register(self, address: int, value: int) -> None:
        """功能码 0x06：写单个保持寄存器（受 read_only 保护）。"""
        if self.read_only:
            raise ModbusError("驱动处于只读模式，已拒绝写操作")
        pdu = struct.pack(">BHH", 0x06, address, value & 0xFFFF)
        self._request(pdu)

    # -- 业务封装（只读） --------------------------------------------------

    def read_all_status(self) -> dict[str, Any]:
        """一次性读取 0x01..0x0E 全部 14 个寄存器并解析为业务字段。"""
        started = time.perf_counter()
        regs = self.read_holding_registers(READ_BLOCK_START, READ_BLOCK_COUNT)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        def at(address: int) -> int:
            return regs[address - READ_BLOCK_START]

        pulses = (at(REG_PULSE_HIGH) << 16) | at(REG_PULSE_LOW)
        motor = at(REG_MOTOR_STATUS)

        return {
            "online": True,
            "latency_ms": elapsed_ms,
            "raw_registers": {
                f"0x{READ_BLOCK_START + i:02X}": v for i, v in enumerate(regs)
            },
            # -- 可写参数(回读值) --
            "manual_rpm_x10": at(REG_MANUAL_RPM),
            "manual_rpm": round(at(REG_MANUAL_RPM) / 10.0, 1),
            "anthem_duration_ds": at(REG_ANTHEM_DURATION),
            "anthem_duration_s": round(at(REG_ANTHEM_DURATION) / 10.0, 1),
            "pulses_per_rev": at(REG_PULSES_PER_REV),
            # -- 运行状态 --
            "motor_status": motor,
            "motor_status_text": MOTOR_STATUS_TEXT.get(motor, f"未知({motor})"),
            "auto_rpm_x10": at(REG_AUTO_RPM),
            "auto_rpm": round(at(REG_AUTO_RPM) / 10.0, 1),
            "limit_forward": at(REG_LIMIT_FWD),
            "limit_forward_text": LIMIT_TEXT.get(at(REG_LIMIT_FWD), "未知"),
            "limit_reverse": at(REG_LIMIT_REV),
            "limit_reverse_text": LIMIT_TEXT.get(at(REG_LIMIT_REV), "未知"),
            # -- 位置 --
            "pulse_low": at(REG_PULSE_LOW),
            "pulse_high": at(REG_PULSE_HIGH),
            "total_pulses": pulses,
        }


# ---------------------------------------------------------------------------
# 位置换算
# ---------------------------------------------------------------------------

def pulses_to_height_m(
    total_pulses: int,
    pulses_per_meter: float | None,
    total_stroke_mm: float | None,
    max_pulses: float | None,
) -> float | None:
    """
    把脉冲数换算成高度(米)。三种换算方式按优先级选用:

    1. pulses_per_meter 已知 -> 直接除
    2. total_stroke_mm + max_pulses 已知 -> 按满行程比例换算
    3. 都未配置 -> 返回 None（前端只显示脉冲数）

    标定方法: 让旗子从最低点升到最高点，记录 max_pulses，
    并填入 total_stroke_mm（实测米数 × 1000）。
    """
    if total_pulses is None:
        return None
    if pulses_per_meter and pulses_per_meter > 0:
        return round(total_pulses / pulses_per_meter, 3)
    if max_pulses and max_pulses > 0 and total_stroke_mm and total_stroke_mm > 0:
        return round((total_pulses / max_pulses) * (total_stroke_mm / 1000.0), 3)
    return None


# ---------------------------------------------------------------------------
# 健康探测
# ---------------------------------------------------------------------------

def probe(host: str, port: int, unit_id: int = 1, timeout: float = 3.0) -> dict[str, Any]:
    """连通性探测，供「添加设备」时的测试按钮使用。"""
    client = ModbusTcpClient(host=host, port=port, unit_id=unit_id, timeout=timeout)
    try:
        status = client.read_all_status()
        return {
            "reachable": True,
            "unit_id": unit_id,
            "latency_ms": status["latency_ms"],
            "motor_status_text": status["motor_status_text"],
            "limit_forward_text": status["limit_forward_text"],
            "limit_reverse_text": status["limit_reverse_text"],
            "total_pulses": status["total_pulses"],
        }
    except ModbusExceptionResponse as exc:
        return {
            "reachable": True,
            "unit_id": unit_id,
            "gateway_reachable": True,
            "slave_responded": False,
            "error": str(exc),
            "hint": "网关可达，但该从站地址无 PLC 应答。请确认从站 ID 是否正确。",
        }
    except ModbusError as exc:
        return {
            "reachable": False,
            "unit_id": unit_id,
            "error": str(exc),
            "hint": "网关不可达。请检查网线、IP、端口，以及网关是否上电。",
        }
