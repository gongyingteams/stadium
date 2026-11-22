"""
升旗设备配置持久化层

设计原则:
    设备参数全部落库，不硬编码。添加设备时由界面选择/填写。
    表结构与 main.py 现有风格保持一致（TEXT 存时间，SQLite）。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

#: 建表语句，由 main.py 的 init_db() 执行
FLAG_DEVICE_SCHEMA = """
CREATE TABLE IF NOT EXISTS flag_devices (
    device_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL DEFAULT 502,
    unit_id INTEGER NOT NULL DEFAULT 1,
    pole_type TEXT NOT NULL DEFAULT 'vertical',
    timeout_s REAL NOT NULL DEFAULT 3.0,
    pole_height_m REAL,
    total_stroke_mm REAL,
    pulses_per_meter REAL,
    max_pulses REAL,
    allow_write INTEGER NOT NULL DEFAULT 0,
    max_moving_seconds REAL NOT NULL DEFAULT 75.0,
    heartbeat_timeout_s REAL NOT NULL DEFAULT 120.0,
    region TEXT DEFAULT '',
    remark TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

#: 老库升级：补齐新增列
FLAG_DEVICE_MIGRATIONS = [
    "ALTER TABLE flag_devices ADD COLUMN max_moving_seconds REAL NOT NULL DEFAULT 75.0",
    "ALTER TABLE flag_devices ADD COLUMN heartbeat_timeout_s REAL NOT NULL DEFAULT 120.0",
    "ALTER TABLE flag_devices ADD COLUMN pole_type TEXT NOT NULL DEFAULT 'vertical'",
]

_NUMERIC_FIELDS = {
    "port": int,
    "unit_id": int,
    "timeout_s": float,
    "pole_height_m": float,
    "total_stroke_mm": float,
    "pulses_per_meter": float,
    "max_pulses": float,
    "max_moving_seconds": float,
    "heartbeat_timeout_s": float,
}

_BOOL_FIELDS = {"allow_write"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    for key, cast in _NUMERIC_FIELDS.items():
        if key in data and data[key] is not None:
            data[key] = cast(data[key])
    for key in _BOOL_FIELDS:
        if key in data:
            data[key] = bool(data[key])
    return data


class FlagStore:
    """升旗设备配置读写。db_factory 传入 main.py 的 db 函数即可。"""

    def __init__(self, db_factory: Callable[[], Any]) -> None:
        self._db = db_factory

    def init_schema(self) -> None:
        with self._db() as conn:
            conn.executescript(FLAG_DEVICE_SCHEMA)
            for sql in FLAG_DEVICE_MIGRATIONS:
                try:
                    conn.execute(sql)
                except Exception:
                    # 列已存在
                    pass

    # -- 查询 --------------------------------------------------------------

    def list_flag_devices(self) -> list[dict[str, Any]]:
        with self._db() as conn:
            rows = conn.execute("SELECT * FROM flag_devices ORDER BY device_id").fetchall()
        return [_row_to_dict(r) for r in rows]

    def get_flag_device(self, device_id: str) -> dict[str, Any] | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM flag_devices WHERE device_id=?", (device_id,)
            ).fetchone()
        return _row_to_dict(row) if row else None

    # -- 写入 --------------------------------------------------------------

    def upsert_flag_device(self, data: dict[str, Any]) -> None:
        ts = _now()
        existing = self.get_flag_device(data["device_id"])
        payload = {
            "device_id": data["device_id"],
            "name": data["name"],
            "host": data["host"],
            "port": int(data.get("port") or 502),
            "unit_id": int(data.get("unit_id") or 1),
            "pole_type": "horizontal" if data.get("pole_type") == "horizontal" else "vertical",
            "timeout_s": float(data.get("timeout_s") or 3.0),
            "pole_height_m": data.get("pole_height_m"),
            "total_stroke_mm": data.get("total_stroke_mm"),
            "pulses_per_meter": data.get("pulses_per_meter"),
            "max_pulses": data.get("max_pulses"),
            "allow_write": 1 if data.get("allow_write") else 0,
            "max_moving_seconds": float(data.get("max_moving_seconds") or 75.0),
            "heartbeat_timeout_s": float(data.get("heartbeat_timeout_s") or 120.0),
            "region": data.get("region") or "",
            "remark": data.get("remark") or "",
            "created_at": existing["created_at"] if existing else ts,
            "updated_at": ts,
        }
        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO flag_devices (
                    device_id, name, host, port, unit_id, pole_type, timeout_s,
                    pole_height_m, total_stroke_mm, pulses_per_meter, max_pulses,
                    allow_write, max_moving_seconds, heartbeat_timeout_s,
                    region, remark, created_at, updated_at
                ) VALUES (
                    :device_id, :name, :host, :port, :unit_id, :pole_type, :timeout_s,
                    :pole_height_m, :total_stroke_mm, :pulses_per_meter, :max_pulses,
                    :allow_write, :max_moving_seconds, :heartbeat_timeout_s,
                    :region, :remark, :created_at, :updated_at
                )
                ON CONFLICT(device_id) DO UPDATE SET
                    name=excluded.name, host=excluded.host, port=excluded.port,
                    unit_id=excluded.unit_id, pole_type=excluded.pole_type, timeout_s=excluded.timeout_s,
                    pole_height_m=excluded.pole_height_m,
                    total_stroke_mm=excluded.total_stroke_mm,
                    pulses_per_meter=excluded.pulses_per_meter,
                    max_pulses=excluded.max_pulses,
                    allow_write=excluded.allow_write,
                    max_moving_seconds=excluded.max_moving_seconds,
                    heartbeat_timeout_s=excluded.heartbeat_timeout_s,
                    region=excluded.region, remark=excluded.remark,
                    updated_at=excluded.updated_at
                """,
                payload,
            )

    def delete_flag_device(self, device_id: str) -> None:
        with self._db() as conn:
            conn.execute("DELETE FROM flag_devices WHERE device_id=?", (device_id,))

    # -- 启动时恢复 ----------------------------------------------------------

    def load_all(self) -> list[dict[str, Any]]:
        return self.list_flag_devices()
