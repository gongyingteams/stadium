"""Small, runnable FastAPI backend for the venue control console.

The demo users and SQLite store make this useful offline. Replace the demo
secret and passwords before deploying; no frontend defaults are trusted.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.flag_modbus import (
    FLAG_MODBUS_UNIT_ID,
    ModbusCommandError,
    ModbusConnectionError,
    execute_flag_command,
    read_flag_registers,
)
from app.flag_ws import flag_ws_hub
from app import clock_api as _clock_api

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("DATABASE_PATH", str(ROOT / "data" / "venue_backend.db")))
JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
JWT_TTL = int(os.getenv("JWT_EXPIRE_MINUTES", "30")) * 60
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173,https://dev.gongying.bond,http://dev.gongying.bond").split(",") if x.strip()]
# 内网段来源正则 (允许局域网内任意电脑通过 IP 直接访问前端时跨域调用后端)
# 说明: 生产态前端已改为同源相对路径 /api (Nginx 反代), 此处用于开发态/直连后端场景
CORS_ORIGIN_REGEX = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|"
    r"192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d{1,5})?$",
)

ROLES = {"admin", "ops", "operator", "viewer"}
ROLE_NAMES = {"admin": "系统管理员", "ops": "运维工程师", "operator": "场馆操作员", "viewer": "只读查看者"}
# Deliberately documented demo credentials; production should use an external identity store.
DEMO_USERS = {
    "admin": ("admin123", "总控管理员", "admin"),
    "ops": ("ops123", "运维工程师", "ops"),
    "operator": ("operator123", "场馆操作员", "operator"),
    "viewer": ("viewer123", "只读查看者", "viewer"),
}

DEFAULT_SYSTEM_SETTINGS: dict[str, Any] = {
    "systemName": "应用集成管控平台",
    "systemSubTitle": "IBMS CONSOLE v1.0",
    "version": "IBMS CONSOLE v1.0",
    "logoType": "PRESET",
    "logoUrl": "",
    "systemLogo": "",
    "logoPresetName": "SvgPortal",
    "systemLogoPreset": "SvgPortal",
    "copyrightText": "Copyright © 2026 应用集成管控平台 版权所有",
    "copyrightOwner": "华体智能体育场馆集成工程技术中心",
    "copyrightYears": "2024 - 2026",
    "icpNumber": "京ICP备20260118号-1",
    "securityFilingNumber": "京公网安备 11010802026001号",
    "commercialLicense": "商业授权版 (Enterprise Tier - 26台纳管设备全功能就绪)",
    "operatorName": "华体智慧物联科技有限公司",
    "serviceHotline": "400-820-2026 / 010-88882026",
    "supportEmail": "ops-support@venue-ibms.com",
    "onSiteOffice": "主场馆 B1 层弱电智能化总控指挥机房 A01",
    "serviceContractCode": "HT-IBMS-2026-N09",
    "maintainerName": "华体技术运维保障组",
    "storageDriver": "LOCAL",
    "activeStorageVendor": "LOCAL",
    "localConfig": {
        "storagePath": "/data/venue-ibms/uploads/",
        "urlPrefix": "/uploads/",
        "maxFileSizeMb": 200,
        "allowedExtensions": ".jpg,.png,.svg,.webp,.mp3,.wav,.mp4,.json,.bin,.pdf"
    },
    "ossConfig": {
        "vendor": "ALIYUN",
        "endpoint": "",
        "bucket": "",
        "accessKeyId": "",
        "accessKeySecret": "",
        "customDomain": "",
        "pathPrefix": "",
        "acl": "public-read",
        "enableHttps": True,
        "isEncrypted": False
    }
}

# 左侧导航菜单出厂默认树 (前后端各维护一份镜像: 后端 DEFAULT_MENU_TREE / 前端 DEFAULT_MENU_CONFIG)
# 字段与 API 契约 (驼峰) 一致; 数据库列名用下划线, 接口层做转换。
DEFAULT_MENU_TREE: list[dict[str, Any]] = [
    {
        "menuKey": "g-situation",
        "title": "1. 综合态势",
        "icon": "SvgDashboard",
        "visible": True,
        "children": [
            {"menuKey": "dashboard", "title": "场馆综合态势总览工作台", "shortTitle": "态势总览",
             "path": "/dashboard", "icon": "SvgDashboard", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": ""},
        ],
    },
    {
        "menuKey": "g-portal",
        "title": "2. 应用门户",
        "icon": "SvgPortal",
        "visible": True,
        "children": [
            {"menuKey": "portal-nav", "title": "场馆应用与网站聚合导航大厅", "shortTitle": "应用导航",
             "path": "/portal/nav", "icon": "SvgCompassNav", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": ""},
            {"menuKey": "portal-external", "title": "外部系统与本地软件集成中心", "shortTitle": "外部集成",
             "path": "/portal/external", "icon": "SvgIframeApp", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": ""},
        ],
    },
    {
        "menuKey": "g-iot",
        "title": "3. 物联控制",
        "icon": "SvgIotControl",
        "visible": True,
        "children": [
            {"menuKey": "iot-audio", "title": "扩声调音与场景音效控制台", "shortTitle": "专业扩声",
             "path": "/iot/audio", "icon": "SvgSoundMatrix", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": "AUDIO"},
            {"menuKey": "iot-lighting", "title": "场地照明场景与能耗监测台", "shortTitle": "场地照明",
             "path": "/iot/lighting", "icon": "SvgLighting", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": "LIGHTING"},
            {"menuKey": "iot-screen", "title": "LED大屏与推屏调度控制台", "shortTitle": "大屏调度",
             "path": "/iot/screen", "icon": "SvgLedScreen", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": "SCREEN"},
            {"menuKey": "iot-score", "title": "赛事计时计分接收与大屏推屏", "shortTitle": "计时计分",
             "path": "/iot/score", "icon": "SvgMatchScore", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": "SCORE"},
            {"menuKey": "iot-flag", "title": "自动升旗仪式与音画同步仿真台", "shortTitle": "智能升旗",
             "path": "/iot/flag", "icon": "SvgFlagSystem", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": "FLAG"},
            {"menuKey": "iot-clock", "title": "标准时钟卫星授时与子钟监测台", "shortTitle": "时钟同步",
             "path": "/iot/clock", "icon": "SvgMasterClock", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": "CLOCK"},
            {"menuKey": "iot-video", "title": "现场水下监控与转播监视台", "shortTitle": "视频监控",
             "path": "/iot/video", "icon": "SvgCameraMatrix", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": "VIDEO"},
            {"menuKey": "iot-media", "title": "媒体播控台(背景音乐与视频投屏)", "shortTitle": "媒体播控",
             "path": "/iot/media", "icon": "SvgMediaPlayer", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": "MEDIA"},
            {"menuKey": "iot-dynamic", "title": "动态低代码通用设备控制台", "shortTitle": "动态设备",
             "path": "/iot/dynamic/group-01", "icon": "SvgDynamicDevice", "visible": True,
             "requiresAdmin": False, "requiresOps": False, "badgeType": ""},
        ],
    },
    {
        "menuKey": "g-config",
        "title": "4. 配置中心",
        "icon": "SvgLowCodeConfig",
        "visible": True,
        "children": [
            {"menuKey": "config-devices", "title": "物联硬件设备管理与总控中台", "shortTitle": "设备管理",
             "path": "/config/devices", "icon": "SvgDeviceSetting", "visible": True,
             "requiresAdmin": False, "requiresOps": True, "badgeType": "TOTAL"},
            {"menuKey": "system-users", "title": "用户角色管理与细粒度权限配置", "shortTitle": "角色权限",
             "path": "/system/users", "icon": "SvgUserRole", "visible": True,
             "requiresAdmin": True, "requiresOps": False, "badgeType": ""},
            {"menuKey": "ops-channels", "title": "告警规则与通知渠道配置中心", "shortTitle": "告警通道",
             "path": "/ops/channels", "icon": "SvgNotifyChannel", "visible": True,
             "requiresAdmin": True, "requiresOps": False, "badgeType": ""},
            {"menuKey": "ops-audit", "title": "操作审计日志与导出留存中心", "shortTitle": "审计日志",
             "path": "/ops/audit", "icon": "SvgAuditLog", "visible": True,
             "requiresAdmin": False, "requiresOps": True, "badgeType": ""},
            {"menuKey": "system-settings", "title": "平台系统设置与对象存储中心", "shortTitle": "系统设置",
             "path": "/system/settings", "icon": "SvgSettingGear", "visible": True,
             "requiresAdmin": True, "requiresOps": False, "badgeType": ""},
            {"menuKey": "system-menu", "title": "导航菜单配置中心", "shortTitle": "菜单配置",
             "path": "/system/menu", "icon": "SvgMenuList", "visible": True,
             "requiresAdmin": True, "requiresOps": False, "badgeType": ""},
        ],
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def seed_menu(connection: sqlite3.Connection) -> None:
    """按 DEFAULT_MENU_TREE 播种左侧导航菜单 (表为空时调用)。"""
    now_str = now()
    order = 1
    for group in DEFAULT_MENU_TREE:
        connection.execute(
            """INSERT INTO sys_menu
               (parent_id, menu_type, menu_key, title, short_title, path, icon, visible,
                sort_order, requires_admin, requires_ops, badge_type, created_at, updated_at, updated_by)
               VALUES (0, 'GROUP', ?, ?, ?, '', ?, ?, ?, 0, 0, '', ?, ?, 'system')""",
            (group["menuKey"], group["title"], group["title"], group["icon"],
             int(group.get("visible", True)), order, now_str, now_str),
        )
        order += 1
        group_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        for item in group.get("children", []):
            connection.execute(
                """INSERT INTO sys_menu
                   (parent_id, menu_type, menu_key, title, short_title, path, icon, visible,
                    sort_order, requires_admin, requires_ops, badge_type, created_at, updated_at, updated_by)
                   VALUES (?, 'ITEM', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'system')""",
                (group_id, item["menuKey"], item["title"], item.get("shortTitle", ""),
                 item.get("path", ""), item.get("icon", "SvgPortal"),
                 int(item.get("visible", True)), order,
                 int(item.get("requiresAdmin", False)), int(item.get("requiresOps", False)),
                 item.get("badgeType", ""), now_str, now_str),
            )
            order += 1


def init_db() -> None:
    with db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
                username TEXT, role TEXT, event_type TEXT NOT NULL, target TEXT NOT NULL,
                action TEXT NOT NULL, result TEXT NOT NULL, ip TEXT, details TEXT
            );
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                level TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'OPEN',
                source TEXT NOT NULL, detail TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mock_state (
                id INTEGER PRIMARY KEY CHECK (id = 1), enabled INTEGER NOT NULL,
                changed_at TEXT NOT NULL, changed_by TEXT NOT NULL, reason TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sys_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by TEXT DEFAULT 'system'
            );
            CREATE TABLE IF NOT EXISTS user_external_apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                app_name TEXT NOT NULL,
                app_type TEXT NOT NULL DEFAULT 'BS',
                target_path TEXT NOT NULL,
                start_args TEXT DEFAULT '',
                app_desc TEXT DEFAULT '',
                auth_username TEXT DEFAULT '',
                auth_password TEXT DEFAULT '',
                icon_type TEXT DEFAULT 'PRESET',
                icon TEXT DEFAULT 'SvgAppGrid',
                custom_icon_url TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                status INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sys_menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL DEFAULT 0,
                menu_type TEXT NOT NULL DEFAULT 'ITEM',
                menu_key TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                short_title TEXT NOT NULL DEFAULT '',
                path TEXT NOT NULL DEFAULT '',
                icon TEXT NOT NULL DEFAULT 'SvgPortal',
                visible INTEGER NOT NULL DEFAULT 1,
                sort_order INTEGER NOT NULL DEFAULT 0,
                requires_admin INTEGER NOT NULL DEFAULT 0,
                requires_ops INTEGER NOT NULL DEFAULT 0,
                badge_type TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by TEXT NOT NULL DEFAULT 'system'
            );
            CREATE INDEX IF NOT EXISTS idx_sys_menu_parent ON sys_menu(parent_id, sort_order);
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO mock_state VALUES (1, ?, ?, 'system', 'initial development mode')",
            (int(MOCK_MODE), now()),
        )
        connection.execute(
            "INSERT OR IGNORE INTO sys_settings(key, value, updated_at, updated_by) VALUES('all', ?, ?, 'system')",
            (json.dumps(DEFAULT_SYSTEM_SETTINGS, ensure_ascii=False), now())
        )
        # 左侧导航菜单: 表为空时播种出厂默认菜单树
        if connection.execute("SELECT count(*) FROM sys_menu").fetchone()[0] == 0:
            seed_menu(connection)
        # 平滑增加新增字段（应对本地SQLite已有表）
        cols = [c[1] for c in connection.execute("PRAGMA table_info(user_external_apps)").fetchall()]
        if "auth_username" not in cols:
            connection.execute("ALTER TABLE user_external_apps ADD COLUMN auth_username TEXT DEFAULT ''")
        if "auth_password" not in cols:
            connection.execute("ALTER TABLE user_external_apps ADD COLUMN auth_password TEXT DEFAULT ''")
        if "icon_type" not in cols:
            connection.execute("ALTER TABLE user_external_apps ADD COLUMN icon_type TEXT DEFAULT 'PRESET'")
        if "custom_icon_url" not in cols:
            connection.execute("ALTER TABLE user_external_apps ADD COLUMN custom_icon_url TEXT DEFAULT ''")

        ext_count = connection.execute("SELECT count(*) FROM user_external_apps").fetchone()[0]
        if ext_count == 0:
            demo_ext = [
                ("admin", "Antigravity IDE 智能开发环境", "CS", "D:\\antigravity\\Antigravity IDE\\antigravity.exe", "--portable", "场馆工控协议自动化二次开发与调测环境", "admin", "dev@2026", "PRESET", "SvgDynamicDevice", "", 1, 1, now()),
                ("admin", "票务检票闸机综合管控后台", "BS", "http://192.168.1.88:8080/ticketing/gate", "", "东区与南区观众安检通道智能闸机核销控制系统", "gate_admin", "TicketPass#88", "PRESET", "SvgAppGrid", "", 2, 1, now()),
                ("admin", "Novastar NovaLCT 屏幕配置工具", "CS", "C:\\Program Files\\Novastar\\NovaLCT\\NovaLCT.exe", "", "全彩主大屏箱体映射、灰度校准与多路网口发送卡配置端", "", "", "PRESET", "SvgLedScreen", "", 3, 1, now()),
                ("admin", "PLC 备用电源自动化巡检脚本", "UNKNOWN", "D:\\scripts\\plc_battery_check.bat", "--fast-check", "双回路UPS与柴油发电机状态探针诊断批处理", "", "", "PRESET", "SvgDeviceSetting", "", 4, 1, now()),
                ("operator", "ARES-21 赛事计时计分现场终端", "CS", "C:\\Program Files\\Ares21\\Client\\ares21.exe", "--event=swimming", "游泳跳水大项终点触板与发令台脉冲接收工作站", "op_timing", "Timing@2026", "PRESET", "SvgMatchScore", "", 1, 1, now()),
                ("operator", "场馆公共广播与背景音乐播放系统", "BS", "http://192.168.1.66:8888/broadcasting", "", "看台与热身池分区分区音频广播Web客户端", "audio_op", "Broadcast#99", "PRESET", "SvgSoundMatrix", "", 2, 1, now()),
            ]
            connection.executemany(
                "INSERT INTO user_external_apps(username, app_name, app_type, target_path, start_args, app_desc, auth_username, auth_password, icon_type, icon, custom_icon_url, sort_order, status, created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                demo_ext
            )
        alarm_count = connection.execute("SELECT count(*) FROM alarms").fetchone()[0]
        if alarm_count == 0:
            demo_alarms = [
                ("10:22:15", "EMERGENCY", "观众大厅数码子钟时间漂移过大", "OPEN", "标准时钟子钟 CLK-HALL-06", "与北斗主母钟时钟偏差达到 1450ms (阈值 500ms)，可能引发检录时间不同步"),
                ("10:15:32", "WARNING", "配电箱回路B3瞬时过流波动", "CONFIRMED", "比赛池场地照明配电柜 B3", "训练模式向赛事模式过渡时出现 14.2A 阶跃波动，现已进入自适应稳压"),
                ("09:58:40", "EMERGENCY", "水下高清视频流丢包率超过 15%", "OPEN", "跳水池水下摄像机 CAM-SUB-02", "RTSP 码流检测到关键帧延迟达 850ms，触发网络交换机光电转换器排查预警"),
                ("09:40:18", "WARNING", "串口通讯心跳超时重试 (COM3/RS232)", "PROCESSING", "Soundcraft Vi3000 数字调音台", "主控制台下发场景音效切流指令时收到应答延迟 320ms，已自动启用备用总线重发成功"),
                ("09:12:05", "INFO", "RTSP流自愈重连完成", "RECOVERED", "看台主摄像机 CAM-FIELD-01", "交换机瞬时抖动触发指数退避重连状态机，耗时 1.2s 自动恢复"),
                ("08:30:00", "INFO", "大屏输入信号源成功切换为计时计分", "CLOSED", "Novastar UHD-v3.0 视频推屏处理器", "已完成 SDI-1 (转播流) 向 TCP 接收卡 (ARES-21) 的画面无缝淡入淡出切换"),
            ]
            connection.executemany(
                "INSERT INTO alarms(created_at, level, title, status, source, detail) VALUES(?,?,?,?,?,?)",
                demo_alarms
            )

        # 确保 197 个国家资料库表结构就绪并填充
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sys_country (
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                code_alpha3 TEXT NOT NULL,
                name_cn TEXT NOT NULL,
                name_en TEXT NOT NULL,
                region TEXT NOT NULL,
                pattern TEXT NOT NULL DEFAULT 'solid',
                c1 TEXT NOT NULL DEFAULT '#2563EB',
                c2 TEXT NOT NULL DEFAULT '#FFFFFF',
                c3 TEXT NOT NULL DEFAULT '#0F172A',
                flag_desc TEXT DEFAULT '',
                image_url TEXT NOT NULL,
                flag_asset_id TEXT NOT NULL,
                flag_asset_name TEXT NOT NULL,
                flag_source_type TEXT NOT NULL DEFAULT 'asset',
                anthem_name TEXT NOT NULL,
                anthem_en TEXT DEFAULT '',
                anthem_duration INTEGER NOT NULL DEFAULT 46,
                anthem_url TEXT NOT NULL,
                anthem_asset_id TEXT NOT NULL,
                anthem_asset_name TEXT NOT NULL,
                anthem_file_name TEXT NOT NULL,
                anthem_source_type TEXT NOT NULL DEFAULT 'asset',
                sort_order INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_country_region ON sys_country(region);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_country_code ON sys_country(code);")

        c_count = connection.execute("SELECT count(*) FROM sys_country").fetchone()[0]
        if c_count < 197:
            json_file = ROOT.parent / "src" / "data" / "countries_197.json"
            if not json_file.exists():
                json_file = ROOT / "data" / "countries_197.json"
            if json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as jf:
                        raw_countries = json.load(jf)
                    cur_now = now()
                    country_rows = []
                    for idx, c in enumerate(raw_countries):
                        country_rows.append((
                            c["id"], c["code"], c.get("codeAlpha3", c["code"]), c["nameCn"], c["nameEn"],
                            c["region"], c.get("pattern", "solid"), c.get("c1", "#2563EB"),
                            c.get("c2", "#FFFFFF"), c.get("c3", "#0F172A"), c.get("flagDesc", ""),
                            c["imageUrl"], c["flagAssetId"], c["flagAssetName"], c.get("flagSourceType", "asset"),
                            c["anthemName"], c.get("anthemEn", ""), c["anthemDuration"],
                            c["anthemUrl"], c["anthemAssetId"], c["anthemAssetName"],
                            c.get("anthemFileName", ""), c.get("anthemSourceType", "asset"),
                            idx + 1, 1, cur_now, cur_now
                        ))
                    connection.executemany("""
                        INSERT OR REPLACE INTO sys_country (
                            id, code, code_alpha3, name_cn, name_en, region, pattern, c1, c2, c3,
                            flag_desc, image_url, flag_asset_id, flag_asset_name, flag_source_type,
                            anthem_name, anthem_en, anthem_duration, anthem_url, anthem_asset_id,
                            anthem_asset_name, anthem_file_name, anthem_source_type, sort_order,
                            status, created_at, updated_at
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, country_rows)
                except Exception as ex:
                    print("Error seeding countries to SQLite:", ex)


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(username: str, role: str) -> str:
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = b64(json.dumps({"sub": username, "role": role, "iat": int(time.time()), "exp": int(time.time()) + JWT_TTL}, separators=(",", ":")).encode())
    unsigned = f"{header}.{payload}".encode()
    return f"{header}.{payload}.{b64(hmac.new(JWT_SECRET.encode(), unsigned, hashlib.sha256).digest())}"


def decode_token(token: str) -> dict[str, Any]:
    try:
        header, payload, signature = token.split(".")
        expected = b64(hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("bad signature")
        claims = json.loads(unb64(payload))
        if int(claims["exp"]) <= int(time.time()) or claims["role"] not in ROLES:
            raise ValueError("expired or invalid claims")
        return claims
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, base64.binascii.Error) as exc:
        raise HTTPException(status_code=401, detail="无效或已过期的会话") from exc


def audit(username: str | None, role: str | None, event: str, target: str, action: str, result: str, ip: str = "", details: Any = None) -> None:
    with db() as connection:
        connection.execute(
            "INSERT INTO audit_logs(timestamp,username,role,event_type,target,action,result,ip,details) VALUES(?,?,?,?,?,?,?,?,?)",
            (now(), username, role, event, target, action, result, ip, json.dumps(details, ensure_ascii=False) if details is not None else ""),
        )


async def current_user(authorization: Annotated[str | None, Header()] = None) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="需要 Bearer 会话令牌")
    return decode_token(authorization[7:].strip())


def require_roles(*roles: str) -> Callable:
    async def dependency(user: Annotated[dict[str, Any], Depends(current_user)]) -> dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
        return user
    return dependency


User = Annotated[dict[str, Any], Depends(current_user)]
AdminOps = Annotated[dict[str, Any], Depends(require_roles("admin", "ops"))]
AdminOnly = Annotated[dict[str, Any], Depends(require_roles("admin"))]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class MockToggleRequest(BaseModel):
    enabled: bool
    reason: str = Field(min_length=1, max_length=255)


class CommandRequest(BaseModel):
    action: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="Venue IBMS Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = ROOT.parent / "public" / "uploads"
if not uploads_dir.exists():
    uploads_dir = ROOT.parent / "dist" / "uploads"
if not uploads_dir.exists():
    uploads_dir = ROOT / "uploads"
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "venue-ibms-backend", "time": now()}


@app.post("/api/auth/login")
def login(body: LoginRequest, request: Request) -> dict[str, Any]:
    record = DEMO_USERS.get(body.username)
    if not record or not hmac.compare_digest(body.password, record[0]):
        audit(body.username, None, "LOGIN", "auth", "login", "FAILURE", request.client.host if request.client else "")
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = issue_token(body.username, record[2])
    audit(body.username, record[2], "LOGIN", "auth", "login", "SUCCESS", request.client.host if request.client else "")
    return {"access_token": token, "token_type": "bearer", "expires_in": JWT_TTL, "user": {"username": body.username, "display_name": record[1], "role": record[2], "role_name": ROLE_NAMES[record[2]]}}


@app.post("/api/auth/logout")
def logout(user: User, request: Request) -> dict[str, str]:
    audit(user["sub"], user["role"], "LOGOUT", "auth", "logout", "SUCCESS", request.client.host if request.client else "")
    return {"status": "logged_out", "message": "会话已注销；JWT将在短时效内自然失效"}


@app.get("/api/me")
def me(user: User) -> dict[str, Any]:
    record = DEMO_USERS[user["sub"]]
    return {"username": user["sub"], "display_name": record[1], "role": user["role"], "role_name": ROLE_NAMES[user["role"]], "expires_at": user["exp"]}


@app.get("/api/audit")
def get_audit(user: AdminOps, limit: int = 100) -> dict[str, Any]:
    limit = max(1, min(limit, 500))
    with db() as connection:
        rows = connection.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@app.get("/api/alarms")
def get_alarms(user: AdminOps) -> dict[str, Any]:
    with db() as connection:
        rows = connection.execute("SELECT * FROM alarms ORDER BY id DESC").fetchall()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@app.get("/api/mock/status")
def mock_status(user: User) -> dict[str, Any]:
    with db() as connection:
        row = connection.execute("SELECT * FROM mock_state WHERE id=1").fetchone()
    return {"enabled": bool(row["enabled"]), "changed_at": row["changed_at"], "changed_by": row["changed_by"], "reason": row["reason"]}


@app.post("/api/mock/toggle")
def mock_toggle(body: MockToggleRequest, user: AdminOps) -> dict[str, Any]:
    with db() as connection:
        connection.execute("UPDATE mock_state SET enabled=?, changed_at=?, changed_by=?, reason=? WHERE id=1", (int(body.enabled), now(), user["sub"], body.reason))
    audit(user["sub"], user["role"], "MOCK_TOGGLE", "mock", "toggle", "SUCCESS", details=body.model_dump())
    return mock_status(user)


class FlagCommandRequest(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    unit_id: int = Field(default=FLAG_MODBUS_UNIT_ID, ge=1, le=247)
    anthem_duration_sec: float | None = None
    manual_rpm: float | None = None
    register_addr: int | None = Field(default=None, alias="register")
    value: int | None = None

    model_config = {"populate_by_name": True}


@app.get("/api/flag/status")
def flag_hardware_status(user: User, unit_id: int = FLAG_MODBUS_UNIT_ID) -> dict[str, Any]:
    """Read live register status from the USR-K7 flag gateway (192.168.0.7:20108)."""
    try:
        data = read_flag_registers(unit_id=unit_id)
        return {"online": True, "mode": "modbus_tcp_gateway", **data}
    except ModbusConnectionError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ModbusCommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/flag/command")
async def flag_hardware_command(
    body: FlagCommandRequest,
    user: Annotated[dict[str, Any], Depends(require_roles("admin", "ops", "operator"))],
) -> dict[str, Any]:
    """Execute a real flag-raising hardware command via USR-K7 Modbus TCP gateway."""
    payload: dict[str, Any] = {}
    if body.anthem_duration_sec is not None:
        payload["anthem_duration_sec"] = body.anthem_duration_sec
    if body.manual_rpm is not None:
        payload["manual_rpm"] = body.manual_rpm
    if body.register_addr is not None:
        payload["register"] = body.register_addr
    if body.value is not None:
        payload["value"] = body.value

    try:
        receipt = await asyncio.to_thread(
            execute_flag_command, body.action, payload=payload, unit_id=body.unit_id
        )
        audit(user["sub"], user["role"], "FLAG_COMMAND", f"USR-K7:UID{body.unit_id}", body.action, "SUCCESS", details=receipt)
        if isinstance(receipt, dict) and isinstance(receipt.get("status"), dict):
            await flag_ws_hub.broadcast_status(body.unit_id, receipt["status"], event=f"command:{body.action}")
        else:
            flag_ws_hub.trigger_refresh()
        return receipt
    except ModbusCommandError as exc:
        audit(user["sub"], user["role"], "FLAG_COMMAND", f"USR-K7:UID{body.unit_id}", body.action, "REJECTED", details={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ModbusConnectionError as exc:
        audit(user["sub"], user["role"], "FLAG_COMMAND", f"USR-K7:UID{body.unit_id}", body.action, "GATEWAY_ERROR", details={"error": str(exc)})
        raise HTTPException(status_code=504, detail=str(exc)) from exc


@app.websocket("/api/flag/ws")
async def flag_hardware_ws(websocket: WebSocket, token: str = "", unit_id: int = FLAG_MODBUS_UNIT_ID) -> None:
    """WebSocket 实时推送智能升旗硬件状态（单后台采集广播，避免多端并发读串口）。"""
    if not token:
        await websocket.close(code=4401, reason="缺少认证令牌")
        return
    try:
        decode_token(token)
    except HTTPException:
        await websocket.close(code=4401, reason="认证令牌无效或已过期")
        return

    uid = max(1, min(247, int(unit_id or FLAG_MODBUS_UNIT_ID)))
    await flag_ws_hub.connect(websocket, unit_id=uid)
    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = (msg or {}).get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": round(time.time(), 3)})
            elif msg_type == "refresh":
                flag_ws_hub.trigger_refresh()
    except WebSocketDisconnect:
        await flag_ws_hub.disconnect(websocket)
    except Exception:
        await flag_ws_hub.disconnect(websocket)


@app.post("/api/devices/{device_id}/command")
def device_command(device_id: str, body: CommandRequest, user: Annotated[dict[str, Any], Depends(require_roles("admin", "ops", "operator"))]) -> dict[str, Any]:
    with db() as connection:
        mock = bool(connection.execute("SELECT enabled FROM mock_state WHERE id=1").fetchone()[0])
    if device_id.upper().startswith("FLG-") and not mock:
        try:
            unit_id = int(body.payload.get("unit_id", FLAG_MODBUS_UNIT_ID))
            receipt = execute_flag_command(body.action, payload=body.payload, unit_id=unit_id)
            audit(user["sub"], user["role"], "DEVICE_COMMAND", device_id, body.action, "SUCCESS", details=receipt)
            return receipt
        except ModbusCommandError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ModbusConnectionError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
    if mock:
        receipt = {"accepted": True, "simulated": True, "receipt": f"MOCK-{secrets.token_hex(6).upper()}", "device_id": device_id, "action": body.action, "message": "模拟模式：未向真实硬件发送指令"}
        result = "MOCK_SUCCESS"
    else:
        receipt = {"accepted": False, "simulated": False, "device_id": device_id, "action": body.action, "error": "未配置真实设备驱动，已拒绝发送"}
        result = "REJECTED_NO_DRIVER"
    audit(user["sub"], user["role"], "DEVICE_COMMAND", device_id, body.action, result, details=receipt)
    if not mock:
        raise HTTPException(status_code=503, detail=receipt)
    return receipt


class ExternalAppPayload(BaseModel):
    app_name: str = Field(min_length=1, max_length=128)
    app_type: str = Field(default="BS")  # BS, CS, UNKNOWN
    target_path: str = Field(min_length=1, max_length=512)
    start_args: str = Field(default="")
    app_desc: str = Field(default="")
    auth_username: str = Field(default="")
    auth_password: str = Field(default="")
    icon_type: str = Field(default="PRESET")  # PRESET, CUSTOM
    icon: str = Field(default="SvgAppGrid")
    custom_icon_url: str = Field(default="")
    sort_order: int = Field(default=0)


@app.get("/api/external-apps")
def get_external_apps(user: User) -> dict[str, Any]:
    username = user["sub"]
    with db() as connection:
        rows = connection.execute(
            "SELECT * FROM user_external_apps WHERE username = ? AND status = 1 ORDER BY sort_order ASC, id ASC",
            (username,)
        ).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows), "username": username}


@app.post("/api/external-apps")
def create_external_app(body: ExternalAppPayload, user: User) -> dict[str, Any]:
    username = user["sub"]
    with db() as connection:
        cursor = connection.execute(
            """INSERT INTO user_external_apps (username, app_name, app_type, target_path, start_args, app_desc, auth_username, auth_password, icon_type, icon, custom_icon_url, sort_order, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
            (username, body.app_name, body.app_type, body.target_path, body.start_args, body.app_desc, body.auth_username, body.auth_password, body.icon_type, body.icon, body.custom_icon_url, body.sort_order, now())
        )
        new_id = cursor.lastrowid
        row = connection.execute("SELECT * FROM user_external_apps WHERE id = ?", (new_id,)).fetchone()
    audit(username, user.get("role"), "EXTERNAL_APP_ADD", body.app_name, "CREATE", "SUCCESS", details={"app_id": new_id, "type": body.app_type})
    return dict(row)


@app.put("/api/external-apps/{app_id}")
def update_external_app(app_id: int, body: ExternalAppPayload, user: User) -> dict[str, Any]:
    username = user["sub"]
    with db() as connection:
        existing = connection.execute("SELECT * FROM user_external_apps WHERE id = ? AND username = ?", (app_id, username)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="外部集成软件不存在或无权限编辑")
        connection.execute(
            """UPDATE user_external_apps SET app_name=?, app_type=?, target_path=?, start_args=?, app_desc=?, auth_username=?, auth_password=?, icon_type=?, icon=?, custom_icon_url=?, sort_order=?
               WHERE id=? AND username=?""",
            (body.app_name, body.app_type, body.target_path, body.start_args, body.app_desc, body.auth_username, body.auth_password, body.icon_type, body.icon, body.custom_icon_url, body.sort_order, app_id, username)
        )
        row = connection.execute("SELECT * FROM user_external_apps WHERE id = ?", (app_id,)).fetchone()
    audit(username, user.get("role"), "EXTERNAL_APP_UPDATE", body.app_name, "UPDATE", "SUCCESS", details={"app_id": app_id})
    return dict(row)


@app.delete("/api/external-apps/{app_id}")
def delete_external_app(app_id: int, user: User) -> dict[str, Any]:
    username = user["sub"]
    with db() as connection:
        existing = connection.execute("SELECT * FROM user_external_apps WHERE id = ? AND username = ?", (app_id, username)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="外部集成软件不存在或无权限删除")
        connection.execute("DELETE FROM user_external_apps WHERE id = ? AND username = ?", (app_id, username))
    audit(username, user.get("role"), "EXTERNAL_APP_DELETE", str(app_id), "DELETE", "SUCCESS", details={"app_id": app_id})
    return {"success": True, "message": "已从个人外部集成列表中移除", "id": app_id}


@app.post("/api/external-apps/{app_id}/launch")
def launch_external_app(app_id: int, user: User) -> dict[str, Any]:
    username = user["sub"]
    with db() as connection:
        app_record = connection.execute("SELECT * FROM user_external_apps WHERE id = ? AND username = ?", (app_id, username)).fetchone()
        if not app_record:
            raise HTTPException(status_code=404, detail="外部集成软件不存在")
    app_data = dict(app_record)
    audit(username, user.get("role"), "EXTERNAL_APP_LAUNCH", app_data["app_name"], "LAUNCH", "SUCCESS", details={"app_id": app_id, "type": app_data["app_type"]})
    return {
        "success": True,
        "app_id": app_id,
        "app_name": app_data["app_name"],
        "app_type": app_data["app_type"],
        "target_path": app_data["target_path"],
        "start_args": app_data["start_args"],
        "auth_username": app_data.get("auth_username", ""),
        "auth_password": app_data.get("auth_password", ""),
        "launch_action": "BROWSER_REDIRECT" if app_data["app_type"] == "BS" else "DESKTOP_EXECUTE"
    }


PUBLIC_SETTING_KEYS = {
    "systemName", "systemSubTitle", "version", "logoType", "logoUrl", "systemLogo",
    "logoPresetName", "systemLogoPreset", "copyrightText", "copyrightOwner",
    "copyrightYears", "icpNumber", "securityFilingNumber", "commercialLicense",
    "operatorName", "serviceHotline", "supportEmail", "updatedAt"
}


@app.get("/api/settings/public")
def get_public_settings() -> dict[str, Any]:
    """无需鉴权的系统基础品牌信息接口（供登录页、无鉴权页面及 Header 标牌使用）"""
    with db() as connection:
        row = connection.execute("SELECT value FROM sys_settings WHERE key = 'all'").fetchone()
        if row and row["value"]:
            try:
                full_settings = json.loads(row["value"])
            except Exception:
                full_settings = DEFAULT_SYSTEM_SETTINGS
        else:
            full_settings = DEFAULT_SYSTEM_SETTINGS
    # 仅输出公共白名单字段，剔除 OSS 密钥等敏感信息
    public_data = {k: full_settings.get(k, DEFAULT_SYSTEM_SETTINGS.get(k, "")) for k in PUBLIC_SETTING_KEYS}
    return public_data


@app.get("/api/settings")
def get_system_settings(user: User) -> dict[str, Any]:
    """完整系统设置读取（需登录鉴权）"""
    with db() as connection:
        row = connection.execute("SELECT value FROM sys_settings WHERE key = 'all'").fetchone()
        if row and row["value"]:
            try:
                full_settings = json.loads(row["value"])
            except Exception:
                full_settings = DEFAULT_SYSTEM_SETTINGS
        else:
            full_settings = DEFAULT_SYSTEM_SETTINGS
    return full_settings


@app.post("/api/settings")
def update_system_settings(body: dict[str, Any], user: User) -> dict[str, Any]:
    """更新全站系统设置（仅限 admin / ops 角色）"""
    if user.get("role") not in ("admin", "ops"):
        raise HTTPException(status_code=403, detail="仅系统管理员和运维工程师可修改系统配置")
    username = user["sub"]
    with db() as connection:
        row = connection.execute("SELECT value FROM sys_settings WHERE key = 'all'").fetchone()
        current = DEFAULT_SYSTEM_SETTINGS.copy()
        if row and row["value"]:
            try:
                current.update(json.loads(row["value"]))
            except Exception:
                pass
        current.update(body)
        current["updatedAt"] = now()
        current["updatedBy"] = username
        val_str = json.dumps(current, ensure_ascii=False)
        connection.execute(
            """INSERT INTO sys_settings (key, value, updated_at, updated_by)
               VALUES ('all', ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at, updated_by=excluded.updated_by""",
            (val_str, now(), username)
        )
    audit(username, user.get("role"), "SYSTEM_SETTINGS_UPDATE", current.get("systemName", "IBMS"), "UPDATE", "SUCCESS", details={"keys": list(body.keys())})
    return {"success": True, "message": "系统全局配置已持久化至服务器数据库", "data": current}


# ================= 左侧导航菜单配置 (仅总管理员可写) =================

class MenuItemPayload(BaseModel):
    id: int | None = None
    menuKey: str = ""
    title: str = ""
    shortTitle: str = ""
    path: str = ""
    icon: str = "SvgPortal"
    visible: bool = True
    requiresAdmin: bool = False
    requiresOps: bool = False
    badgeType: str = ""


class MenuGroupPayload(BaseModel):
    id: int | None = None
    menuKey: str = ""
    title: str = ""
    icon: str = "SvgPortal"
    visible: bool = True
    children: list[MenuItemPayload] = Field(default_factory=list)


class MenuTreePayload(BaseModel):
    groups: list[MenuGroupPayload] = Field(default_factory=list)


def _menu_row_to_item(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "menuKey": row["menu_key"],
        "title": row["title"],
        "shortTitle": row["short_title"],
        "path": row["path"],
        "icon": row["icon"],
        "visible": bool(row["visible"]),
        "requiresAdmin": bool(row["requires_admin"]),
        "requiresOps": bool(row["requires_ops"]),
        "badgeType": row["badge_type"],
    }


def _load_menu_tree() -> list[dict[str, Any]]:
    with db() as connection:
        group_rows = connection.execute(
            "SELECT * FROM sys_menu WHERE menu_type = 'GROUP' ORDER BY sort_order, id"
        ).fetchall()
        items_by_parent: dict[int, list[sqlite3.Row]] = {}
        for r in connection.execute(
            "SELECT * FROM sys_menu WHERE menu_type = 'ITEM' ORDER BY sort_order, id"
        ).fetchall():
            items_by_parent.setdefault(r["parent_id"], []).append(r)
    return [
        {
            "id": g["id"],
            "menuKey": g["menu_key"],
            "title": g["title"],
            "icon": g["icon"],
            "visible": bool(g["visible"]),
            "children": [_menu_row_to_item(i) for i in items_by_parent.get(g["id"], [])],
        }
        for g in group_rows
    ]


def _menu_slug(source: str) -> str:
    """把路径/标题碾成 menu_key 段: '/iot/audio' -> 'iot-audio', 中文标题 -> 'menu'。"""
    s = (source or "").strip().strip("/")
    s = re.sub(r"[\s/_:.]+", "-", s).lower()
    s = re.sub(r"[^a-z0-9-]", "", s).strip("-")
    return s or "menu"


@app.get("/api/menu/config")
def get_menu_config(user: User) -> dict[str, Any]:
    """读取完整导航菜单树 (所有登录角色可读, 用于侧边栏渲染)。"""
    return {"groups": _load_menu_tree()}


@app.put("/api/menu/config")
def update_menu_config(body: MenuTreePayload, user: AdminOnly) -> dict[str, Any]:
    """整树原子替换导航菜单 (仅 admin)。本地编辑 -> 整体提交, 天然覆盖增删改排序。"""
    groups = body.groups
    if not groups:
        raise HTTPException(status_code=400, detail="菜单树不能为空")
    if not any(g.visible for g in groups):
        raise HTTPException(status_code=400, detail="至少保留 1 个可见分组, 不能把全部分组隐藏")
    total = sum(1 + len(g.children) for g in groups)
    if total > 200:
        raise HTTPException(status_code=400, detail=f"菜单节点总数超限 ({total} > 200)")
    for g in groups:
        if not (g.title or "").strip():
            raise HTTPException(status_code=400, detail="存在标题为空的分组")
        for c in g.children:
            if not (c.title or "").strip():
                raise HTTPException(status_code=400, detail="存在标题为空的菜单项")
            if not (c.path or "").strip():
                raise HTTPException(status_code=400, detail=f"菜单项「{c.title.strip()}」的链接不能为空")

    # 链接唯一性: 同一个页面(含外链)只能由一个菜单项指向, 避免两个及以上菜单同时指向一个页面造成重复配置。
    # 规范化: 去首尾空白 + 去掉结尾斜杠 ("/iot/audio/" 与 "/iot/audio" 视为同一页面)。
    def _norm_menu_path(p: str) -> str:
        return (p or "").strip().rstrip("/") or "/"

    path_owner: dict[str, str] = {}
    for g in groups:
        for c in g.children:
            key = _norm_menu_path(c.path)
            if key in path_owner:
                raise HTTPException(
                    status_code=400,
                    detail=(f"菜单项「{c.title.strip()}」与「{path_owner[key]}」同时指向页面 {key}, "
                            "同一页面只能由一个菜单入口指向, 请修改或删除重复项"),
                )
            path_owner[key] = c.title.strip()

    username = user["sub"]
    now_str = now()
    seen: set[str] = set()
    with db() as connection:
        connection.execute("DELETE FROM sys_menu")
        order = 1
        item_count = 0
        for group in groups:
            gkey = (group.menuKey or "").strip() or _menu_slug(group.title)
            base, n = gkey, 2
            while gkey in seen:
                gkey = f"{base}-{n}"
                n += 1
            seen.add(gkey)
            connection.execute(
                """INSERT INTO sys_menu
                   (parent_id, menu_type, menu_key, title, short_title, path, icon, visible,
                    sort_order, requires_admin, requires_ops, badge_type, created_at, updated_at, updated_by)
                   VALUES (0, 'GROUP', ?, ?, ?, '', ?, ?, ?, 0, 0, '', ?, ?, ?)""",
                (gkey, group.title.strip(), group.title.strip(), group.icon,
                 int(group.visible), order, now_str, now_str, username),
            )
            order += 1
            group_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            for child in group.children:
                ckey = (child.menuKey or "").strip() or _menu_slug(child.path or child.title)
                base, n = ckey, 2
                while ckey in seen:
                    ckey = f"{base}-{n}"
                    n += 1
                seen.add(ckey)
                connection.execute(
                    """INSERT INTO sys_menu
                       (parent_id, menu_type, menu_key, title, short_title, path, icon, visible,
                        sort_order, requires_admin, requires_ops, badge_type, created_at, updated_at, updated_by)
                       VALUES (?, 'ITEM', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (group_id, ckey, child.title.strip(), child.shortTitle.strip(),
                     child.path.strip(), child.icon, int(child.visible), order,
                     int(child.requiresAdmin), int(child.requiresOps), child.badgeType.strip(),
                     now_str, now_str, username),
                )
                order += 1
                item_count += 1

    audit(username, user.get("role"), "MENU_CONFIG_UPDATE", "导航菜单", "整树保存", "SUCCESS",
          details={"group_count": len(groups), "item_count": item_count})
    return {"success": True, "message": "导航菜单配置已持久化", "data": {"groups": _load_menu_tree()}}


@app.post("/api/menu/config/reset")
def reset_menu_config(user: AdminOnly) -> dict[str, Any]:
    """恢复出厂默认导航菜单 (仅 admin)。防锁死: 即便管理入口被删也可由此还原。"""
    username = user["sub"]
    with db() as connection:
        connection.execute("DELETE FROM sys_menu")
        seed_menu(connection)
    audit(username, user.get("role"), "MENU_CONFIG_RESET", "导航菜单", "恢复默认", "SUCCESS")
    return {"success": True, "message": "导航菜单已恢复为出厂默认配置", "data": {"groups": _load_menu_tree()}}


class CountryPayload(BaseModel):
    id: str | None = None
    code: str = Field(min_length=2, max_length=16)
    codeAlpha3: str | None = None
    nameCn: str = Field(min_length=1, max_length=128)
    nameEn: str = Field(default="")
    region: str = Field(default="亚洲")
    pattern: str = Field(default="solid")
    c1: str = Field(default="#2563EB")
    c2: str = Field(default="#FFFFFF")
    c3: str = Field(default="#0F172A")
    flagDesc: str = Field(default="")
    imageUrl: str = Field(default="")
    flagAssetId: str = Field(default="")
    flagAssetName: str = Field(default="")
    flagSourceType: str = Field(default="asset")
    anthemName: str = Field(default="")
    anthemEn: str = Field(default="")
    anthemDuration: int = Field(default=46)
    anthemUrl: str = Field(default="")
    anthemAssetId: str = Field(default="")
    anthemAssetName: str = Field(default="")
    anthemFileName: str = Field(default="")
    anthemSourceType: str = Field(default="asset")
    sortOrder: int = Field(default=0)


def row_to_country_dict(r: sqlite3.Row) -> dict[str, Any]:
    d = dict(r)
    return {
        "id": d["id"],
        "code": d["code"],
        "codeAlpha3": d.get("code_alpha3", d["code"]),
        "nameCn": d["name_cn"],
        "nameEn": d["name_en"],
        "region": d["region"],
        "pattern": d["pattern"],
        "c1": d["c1"],
        "c2": d["c2"],
        "c3": d["c3"],
        "flagDesc": d.get("flag_desc", ""),
        "imageUrl": d["image_url"],
        "flagAssetId": d["flag_asset_id"],
        "flagAssetName": d["flag_asset_name"],
        "flagSourceType": d["flag_source_type"],
        "anthemName": d["anthem_name"],
        "anthemEn": d.get("anthem_en", ""),
        "anthemDuration": d["anthem_duration"],
        "anthemUrl": d["anthem_url"],
        "anthemAssetId": d["anthem_asset_id"],
        "anthemAssetName": d["anthem_asset_name"],
        "anthemFileName": d.get("anthem_file_name", ""),
        "anthemSourceType": d["anthem_source_type"],
        "sortOrder": d.get("sort_order", 0),
        "status": d.get("status", 1),
    }


@app.get("/api/countries")
def get_countries(region: str | None = None, keyword: str | None = None) -> dict[str, Any]:
    """获取所有国家列表（支持大洲与关键字过滤）"""
    with db() as conn:
        query = "SELECT * FROM sys_country WHERE status = 1"
        params: list[Any] = []
        if region and region != "全部":
            query += " AND region = ?"
            params.append(region)
        if keyword:
            kw = f"%{keyword.strip()}%"
            query += " AND (code LIKE ? OR code_alpha3 LIKE ? OR name_cn LIKE ? OR name_en LIKE ? OR anthem_name LIKE ?)"
            params.extend([kw, kw, kw, kw, kw])
        query += " ORDER BY sort_order ASC, code ASC"
        rows = conn.execute(query, params).fetchall()
        items = [row_to_country_dict(r) for r in rows]
    return {"items": items, "count": len(items)}


@app.get("/api/countries/{code}")
def get_country(code: str) -> dict[str, Any]:
    """按缩写代码获取单个国家"""
    with db() as conn:
        row = conn.execute("SELECT * FROM sys_country WHERE code = ? OR id = ?", (code.upper(), code)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"国家代码 {code} 不存在")
        return row_to_country_dict(row)


@app.post("/api/countries")
def create_country(body: CountryPayload, user: User) -> dict[str, Any]:
    """新增或更新国家记录"""
    code = body.code.strip().upper()
    alpha3 = (body.codeAlpha3 or code).upper()
    name_cn = body.nameCn.strip()
    name_en = body.nameEn.strip() or name_cn
    cid = body.id or code
    cur_now = now()

    with db() as conn:
        conn.execute("""
            INSERT INTO sys_country (
                id, code, code_alpha3, name_cn, name_en, region, pattern, c1, c2, c3,
                flag_desc, image_url, flag_asset_id, flag_asset_name, flag_source_type,
                anthem_name, anthem_en, anthem_duration, anthem_url, anthem_asset_id,
                anthem_asset_name, anthem_file_name, anthem_source_type, sort_order,
                status, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(code) DO UPDATE SET
                code_alpha3=excluded.code_alpha3,
                name_cn=excluded.name_cn,
                name_en=excluded.name_en,
                region=excluded.region,
                pattern=excluded.pattern,
                c1=excluded.c1,
                c2=excluded.c2,
                c3=excluded.c3,
                flag_desc=excluded.flag_desc,
                image_url=excluded.image_url,
                flag_asset_id=excluded.flag_asset_id,
                flag_asset_name=excluded.flag_asset_name,
                anthem_name=excluded.anthem_name,
                anthem_en=excluded.anthem_en,
                anthem_duration=excluded.anthem_duration,
                anthem_url=excluded.anthem_url,
                anthem_asset_id=excluded.anthem_asset_id,
                anthem_asset_name=excluded.anthem_asset_name,
                anthem_file_name=excluded.anthem_file_name,
                updated_at=excluded.updated_at
        """, (
            cid, code, alpha3, name_cn, name_en, body.region, body.pattern,
            body.c1, body.c2, body.c3, body.flagDesc,
            body.imageUrl or f"/uploads/flags/{code}.svg",
            body.flagAssetId or f"ast_flag_{code}",
            body.flagAssetName or f"{name_cn}国旗",
            body.flagSourceType,
            body.anthemName or f"{name_cn}国歌",
            body.anthemEn, body.anthemDuration,
            body.anthemUrl or f"/uploads/audio/{code}.mp3",
            body.anthemAssetId or f"ast_anthem_{code}",
            body.anthemAssetName or f"{name_cn}国歌",
            body.anthemFileName or f"{name_cn}.mp3",
            body.anthemSourceType,
            body.sortOrder, 1, cur_now, cur_now
        ))
        row = conn.execute("SELECT * FROM sys_country WHERE code = ?", (code,)).fetchone()
    audit(user["sub"], user.get("role"), "COUNTRY_UPSERT", name_cn, "UPSERT", "SUCCESS", details={"code": code})
    return {"success": True, "data": row_to_country_dict(row)}


@app.delete("/api/countries/{code}")
def delete_country(code: str, user: User) -> dict[str, Any]:
    """删除国家记录（软删除，仅限 admin / ops）"""
    if user.get("role") not in ("admin", "ops"):
        raise HTTPException(status_code=403, detail="仅系统管理员和运维工程师可删除国家")
    code = code.upper()
    with db() as conn:
        existing = conn.execute("SELECT name_cn FROM sys_country WHERE code = ?", (code,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="国家不存在")
        conn.execute("UPDATE sys_country SET status = 0, updated_at = ? WHERE code = ?", (now(), code))
    audit(user["sub"], user.get("role"), "COUNTRY_DELETE", code, "DELETE", "SUCCESS")
    return {"success": True, "message": f"已将国家 {code} 从列表中移除"}


@app.post("/api/countries/reset")
def reset_countries(user: User) -> dict[str, Any]:
    """一键重置为 197 国官方标准基线库（仅限 admin / ops）"""
    if user.get("role") not in ("admin", "ops"):
        raise HTTPException(status_code=403, detail="仅系统管理员和运维工程师可重置国家资料库")
    json_file = ROOT.parent / "src" / "data" / "countries_197.json"
    if not json_file.exists():
        json_file = ROOT / "data" / "countries_197.json"
    if not json_file.exists():
        raise HTTPException(status_code=500, detail="未找到 197 国基准数据文件")
    with open(json_file, "r", encoding="utf-8") as jf:
        raw_countries = json.load(jf)
    cur_now = now()
    country_rows = []
    for idx, c in enumerate(raw_countries):
        country_rows.append((
            c["id"], c["code"], c.get("codeAlpha3", c["code"]), c["nameCn"], c["nameEn"],
            c["region"], c.get("pattern", "solid"), c.get("c1", "#2563EB"),
            c.get("c2", "#FFFFFF"), c.get("c3", "#0F172A"), c.get("flagDesc", ""),
            c["imageUrl"], c["flagAssetId"], c["flagAssetName"], c.get("flagSourceType", "asset"),
            c["anthemName"], c.get("anthemEn", ""), c["anthemDuration"],
            c["anthemUrl"], c["anthemAssetId"], c["anthemAssetName"],
            c.get("anthemFileName", ""), c.get("anthemSourceType", "asset"),
            idx + 1, 1, cur_now, cur_now
        ))
    with db() as conn:
        conn.execute("DELETE FROM sys_country")
        conn.executemany("""
            INSERT INTO sys_country (
                id, code, code_alpha3, name_cn, name_en, region, pattern, c1, c2, c3,
                flag_desc, image_url, flag_asset_id, flag_asset_name, flag_source_type,
                anthem_name, anthem_en, anthem_duration, anthem_url, anthem_asset_id,
                anthem_asset_name, anthem_file_name, anthem_source_type, sort_order,
                status, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, country_rows)
    audit(user["sub"], user.get("role"), "COUNTRY_RESET", "197国资料库", "RESET", "SUCCESS", details={"count": len(country_rows)})
    return {"success": True, "message": f"已成功恢复 197 国官方基线资料库", "count": len(country_rows)}


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    # Keep accidental exception details out of API responses.
    return JSONResponse(status_code=500, content={"detail": "内部服务错误"})


# ===== FLAG INTEGRATION (app.flag) BEGIN =====
# 自动升旗硬件对接
#   设备参数全部存库（flag_devices 表），添加设备时由界面填写，不硬编码
#   默认 allow_write=False 即只读监测；开启后才允许下发动作指令
#   位置只报限位开关的精确值，绝不推算（见 app/flag/position.py）
#   运动有硬保护：超时自动急停 + 心跳看门狗（见 app/flag/motion_guard.py）
from app.flag import FLAG_DEVICE_SCHEMA, FlagStore  # noqa: E402
from app.flag import flag_api as _flag_api  # noqa: E402
from app.flag.flag_api import router as flag_router  # noqa: E402
from app.flag.flag_service import FlagController, registry as _flag_registry  # noqa: E402
from app.flag.motion_guard import guards as _flag_guards  # noqa: E402

_flag_store = FlagStore(db)


def _flag_audit(device_id: str, event_type: str, action: str, result: str, details=None) -> None:
    audit("system", "system", event_type, device_id, action, result, details=details)


def _init_flag_devices() -> None:
    """建表 + 把库中配置加载到内存注册表，并装配保护器。"""
    _flag_store.init_schema()
    for row in _flag_store.load_all():
        ctrl = FlagController(
            device_id=row["device_id"],
            host=row["host"],
            port=row["port"],
            unit_id=row["unit_id"],
            timeout=row["timeout_s"],
            total_stroke_mm=row.get("total_stroke_mm"),
            pulses_per_meter=row.get("pulses_per_meter"),
            max_pulses=row.get("max_pulses"),
            allow_write=bool(row.get("allow_write")),
        )
        _flag_registry.upsert(ctrl)
        _flag_guards.get_or_create(
            row["device_id"],
            emergency_callback=ctrl.emergency_stop,
            max_moving_seconds=float(row.get("max_moving_seconds") or 75.0),
            heartbeat_timeout=float(row.get("heartbeat_timeout_s") or 120.0),
        )


def _flag_read_run_status(device_id: str):
    """供看门狗读取 0x04 电机状态。失败返回 None 表示跳过本轮。"""
    ctrl = _flag_registry.get(device_id)
    if ctrl is None:
        return None
    status = ctrl.read_status()
    if not status.get("online"):
        return None
    return status.get("motor_status")


_init_flag_devices()
_flag_api.configure(lambda: _flag_store, _flag_audit)
_flag_guards.set_status_reader(_flag_read_run_status)
_flag_guards.start()
app.include_router(flag_router)
# ===== FLAG INTEGRATION (app.flag) END =====

# ===== CLOCK INTEGRATION (app.clock_api) =====
_clock_api.configure(db, _flag_audit, JWT_SECRET)
app.include_router(_clock_api.router)

# ===== VIDEO INTEGRATION (app.video_router) =====
from app.video_router import router as _video_router  # noqa: E402

app.include_router(_video_router)


@app.websocket("/api/clock/ws")
async def clock_hardware_ws(websocket: WebSocket, token: str = "") -> None:
    """标准时钟 WebSocket 状态通道（鉴权 + 心跳保活）。"""
    if not token:
        await websocket.close(code=4401, reason="缺少认证令牌")
        return
    try:
        decode_token(token)
    except HTTPException:
        await websocket.close(code=4401, reason="认证令牌无效或已过期")
        return

    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_json()
            if (msg or {}).get("type") == "ping":
                await websocket.send_json({"type": "pong", "ts": round(time.time(), 3)})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

