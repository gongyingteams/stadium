"""LAN IP camera & vMix video source probing, control, snapshot, and stream proxy router."""
from __future__ import annotations

import base64
import json
import re
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

try:
    import imageio_ffmpeg  # type: ignore
except Exception:  # pragma: no cover
    imageio_ffmpeg = None  # type: ignore

try:
    import pymysql  # type: ignore
except Exception:  # pragma: no cover
    pymysql = None  # type: ignore

DEFAULT_UNDERWATER_DB_CFG: dict[str, Any] = {
    "host": "192.168.0.33",
    "port": 3306,
    "user": "user_view",
    "password": "zm123456",
    "database": "image_platform",
    "charset": "utf8mb4",
}

router = APIRouter(prefix="/api/video", tags=["video"])

ROOT_DIR = Path(__file__).resolve().parents[2]
UNDERWATER_DB_CFG_FILE = ROOT_DIR / "backend" / "data" / "underwater_db_config.json"
SNAPSHOT_DIR = ROOT_DIR / "public" / "uploads" / "snapshots"
SNAPSHOT_META_FILE = SNAPSHOT_DIR / "index.json"
_LATEST_FRAMES: dict[str, tuple[float, bytes]] = {}


class UnderwaterDbConfigRequest(BaseModel):
    host: str
    port: int = 3306
    user: str = "user_view"
    password: str = ""
    keepPassword: bool = True
    database: str = "image_platform"
    charset: str = "utf8mb4"


class VideoProbeRequest(BaseModel):
    target: str
    protocol: str = "auto"


class SnapshotRequest(BaseModel):
    cameraId: str = ""
    cameraName: str = ""
    streamUrl: str = ""
    imageBase64: str = ""


class VmixCutRequest(BaseModel):
    baseUrl: str
    inputNumber: int


class PtzCommandRequest(BaseModel):
    host: str
    port: int = 1259
    action: str
    speed: int = 8
    preset: int = 1


def _parse_host_port(target: str, default_port: int = 80) -> tuple[str, int, str]:
    raw = (target or "").strip()
    if not raw:
        raise ValueError("请输入摄像机 IP 或流地址")
    if "://" not in raw:
        raw_for_parse = f"http://{raw}"
    else:
        raw_for_parse = raw
    parsed = urllib.parse.urlparse(raw_for_parse)
    host = parsed.hostname or ""
    if not host:
        raise ValueError("无法识别有效的主机 IP 或域名")
    port = parsed.port or (554 if parsed.scheme == "rtsp" else default_port)
    return host, port, parsed.scheme


def _tcp_open(host: str, port: int, timeout: float = 0.8) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, port)) == 0
    except OSError:
        return False
    finally:
        sock.close()


def _fetch_vmix_info(base_url: str) -> dict[str, Any]:
    api_url = base_url.rstrip("/") + "/api"
    req = urllib.request.Request(api_url, method="GET")
    with urllib.request.urlopen(req, timeout=2.5) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))
    inputs: list[dict[str, Any]] = []
    for node in root.findall("./inputs/input"):
        inputs.append({
            "number": int(node.attrib.get("number", "0") or 0),
            "type": node.attrib.get("type", ""),
            "title": node.attrib.get("title", ""),
            "state": node.attrib.get("state", ""),
        })
    active = int((root.findtext("./active") or "0").strip() or 0)
    preview = int((root.findtext("./preview") or "0").strip() or 0)
    version = (root.findtext("./version") or "").strip()

    live_lan_ready = False
    live_lan_status = 0
    m3u8_url = base_url.rstrip("/") + "/livelan/stream.m3u8"
    try:
        mreq = urllib.request.Request(m3u8_url, method="GET")
        with urllib.request.urlopen(mreq, timeout=2.0) as mresp:
            live_lan_status = mresp.status
            live_lan_ready = mresp.status == 200
    except urllib.error.HTTPError as exc:
        live_lan_status = exc.code
    except Exception:
        live_lan_status = 0

    return {
        "version": version,
        "active": active,
        "preview": preview,
        "inputs": inputs,
        "liveLanReady": live_lan_ready,
        "liveLanStatus": live_lan_status,
        "liveLanUrl": m3u8_url,
    }


@router.post("/probe")
def probe_video_source(body: VideoProbeRequest) -> dict[str, Any]:
    try:
        host, explicit_port, scheme = _parse_host_port(body.target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ports_to_check = sorted({explicit_port, 80, 554, 8000, 8080, 8088, 1935})
    open_ports = [p for p in ports_to_check if _tcp_open(host, p)]

    is_vmix = False
    vmix_info: dict[str, Any] | None = None
    vmix_port = explicit_port if explicit_port in open_ports and body.protocol == "vmix" else (8088 if 8088 in open_ports else None)
    if vmix_port is not None:
        base_url = f"http://{host}:{vmix_port}"
        try:
            vmix_info = _fetch_vmix_info(base_url)
            is_vmix = True
        except Exception:
            vmix_info = None

    if is_vmix and vmix_info is not None:
        input_names = "、".join(f"#{i['number']} {i['title']}" for i in vmix_info["inputs"] if i.get("title"))
        if vmix_info["liveLanReady"]:
            msg = f"已连通 vMix 服务（v{vmix_info['version']}），检测到采集机位：{input_names}；LiveLAN HLS 流已就绪。"
        else:
            msg = (
                f"已连通 vMix 服务（v{vmix_info['version']}），检测到采集机位：{input_names}；"
                f"但 /livelan/stream.m3u8 返回 {vmix_info['liveLanStatus'] or '未启用'}（需在 vMix 软件开启 LiveLAN 推流）。"
            )
    elif open_ports:
        port_desc = ", ".join(str(p) for p in open_ports)
        rtsp_hint = "（包含 RTSP 554 视频流端口）" if 554 in open_ports else ""
        msg = f"目标主机 {host} 网络可达，开放端口：{port_desc}{rtsp_hint}。"
    else:
        msg = f"无法连接 {host} 的常用视频端口（{', '.join(str(p) for p in ports_to_check)}），请检查网线与同网段 IP。"

    return {
        "host": host,
        "scheme": scheme,
        "reachable": bool(open_ports),
        "openPorts": open_ports,
        "isVmix": is_vmix,
        "vmix": vmix_info,
        "message": msg,
    }


@router.post("/vmix/cut")
def vmix_cut_input(body: VmixCutRequest) -> dict[str, Any]:
    base = body.baseUrl.strip().rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = f"http://{base}"
    cut_url = f"{base}/api/?Function=CutDirect&Input={body.inputNumber}"
    try:
        req = urllib.request.Request(cut_url, method="GET")
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            status = resp.status
        info = _fetch_vmix_info(base)
        return {"ok": status == 200, "vmix": info}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"切换 vMix 机位失败: {exc}") from exc


@router.get("/proxy")
def proxy_http_stream(url: str = Query(..., description="LAN HTTP/HLS/MJPEG stream URL")):
    target = url.strip()
    if not target.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="仅支持代理 http:// 或 https:// 流地址")

    try:
        req = urllib.request.Request(target, method="GET")
        resp = urllib.request.urlopen(req, timeout=5.0)
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=exc.code, detail=f"上游视频源返回 HTTP {exc.code}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"无法拉取上游视频流: {exc}") from exc

    content_type = resp.headers.get("Content-Type", "application/octet-stream")
    if target.lower().endswith(".m3u8") or "mpegurl" in content_type.lower():
        raw_text = resp.read().decode("utf-8", errors="replace")
        resp.close()
        rewritten_lines: list[str] = []
        for line in raw_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                rewritten_lines.append(line)
            else:
                abs_seg = urllib.parse.urljoin(target, stripped)
                rewritten_lines.append(f"/api/video/proxy?url={urllib.parse.quote(abs_seg, safe='')}")
        return Response(content="\n".join(rewritten_lines), media_type="application/vnd.apple.mpegurl")

    def _iter_chunks():
        try:
            while True:
                chunk = resp.read(32768)
                if not chunk:
                    break
                yield chunk
        finally:
            resp.close()

    return StreamingResponse(_iter_chunks(), media_type=content_type)


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        if k == "hik_password":
            out[k] = "******" if v else ""
        elif isinstance(v, (bytes, bytearray)):
            out[k] = int.from_bytes(v, "big") if len(v) <= 4 else v.hex()
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat(sep=" ")
        else:
            out[k] = v
    return out


def _load_underwater_db_cfg() -> dict[str, Any]:
    cfg = dict(DEFAULT_UNDERWATER_DB_CFG)
    if UNDERWATER_DB_CFG_FILE.exists():
        try:
            saved = json.loads(UNDERWATER_DB_CFG_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                if saved.get("host"):
                    cfg["host"] = str(saved["host"]).strip()
                if saved.get("port"):
                    cfg["port"] = int(saved["port"])
                if saved.get("user") is not None:
                    cfg["user"] = str(saved["user"]).strip()
                if saved.get("password") is not None:
                    cfg["password"] = str(saved["password"])
                if saved.get("database"):
                    cfg["database"] = str(saved["database"]).strip()
                if saved.get("charset"):
                    cfg["charset"] = str(saved["charset"]).strip()
        except Exception:
            pass
    return cfg


def _save_underwater_db_cfg(cfg: dict[str, Any]) -> None:
    UNDERWATER_DB_CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
    UNDERWATER_DB_CFG_FILE.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _public_underwater_db_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "host": cfg["host"],
        "port": int(cfg["port"]),
        "user": cfg["user"],
        "database": cfg["database"],
        "charset": cfg.get("charset") or "utf8mb4",
        "hasPassword": bool(cfg.get("password")),
    }


def _resolve_db_cfg_from_request(body: UnderwaterDbConfigRequest) -> dict[str, Any]:
    current = _load_underwater_db_cfg()
    host = (body.host or "").strip()
    database = (body.database or "").strip()
    user = (body.user or "").strip()
    if not host:
        raise HTTPException(status_code=400, detail="请填写数据库主机 IP 或域名")
    if not database:
        raise HTTPException(status_code=400, detail="请填写数据库名称")
    port = int(body.port or 3306)
    if port < 1 or port > 65535:
        raise HTTPException(status_code=400, detail="数据库端口必须在 1~65535 之间")
    password = body.password if (body.password != "" or not body.keepPassword) else current.get("password", "")
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "charset": (body.charset or "utf8mb4").strip() or "utf8mb4",
    }


def _connect_underwater_db(cfg_override: dict[str, Any] | None = None):
    if pymysql is None:
        raise HTTPException(status_code=500, detail="后端未安装 pymysql 驱动")
    cfg = cfg_override or _load_underwater_db_cfg()
    return pymysql.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset=cfg.get("charset") or "utf8mb4",
        connect_timeout=4,
        read_timeout=6,
        cursorclass=pymysql.cursors.DictCursor,
    )


@router.get("/underwater/db-config")
def get_underwater_db_config() -> dict[str, Any]:
    cfg = _load_underwater_db_cfg()
    return {"ok": True, "config": _public_underwater_db_cfg(cfg)}


@router.post("/underwater/db-config")
def save_underwater_db_config(body: UnderwaterDbConfigRequest) -> dict[str, Any]:
    cfg = _resolve_db_cfg_from_request(body)
    _save_underwater_db_cfg(cfg)
    return {
        "ok": True,
        "message": f"已保存水下台账数据库配置（{cfg['host']}:{cfg['port']} / {cfg['database']}）",
        "config": _public_underwater_db_cfg(cfg),
    }


@router.post("/underwater/db-config/test")
def test_underwater_db_config(body: UnderwaterDbConfigRequest) -> dict[str, Any]:
    cfg = _resolve_db_cfg_from_request(body)
    try:
        conn = _connect_underwater_db(cfg)
    except HTTPException:
        raise
    except Exception as exc:
        return {
            "ok": False,
            "message": f"连接数据库失败（{cfg['host']}:{cfg['port']} / {cfg['database']}）：{exc}",
        }
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS ver")
            ver_row = cur.fetchone() or {}
            ver = ver_row.get("ver") or "MySQL"
            cam_cnt = None
            try:
                cur.execute("SELECT COUNT(*) AS cnt FROM `tb_camera`")
                cam_cnt = int((cur.fetchone() or {}).get("cnt") or 0)
            except Exception:
                cam_cnt = None
        extra = f"，检测到 tb_camera 共 {cam_cnt} 条记录" if cam_cnt is not None else ""
        return {
            "ok": True,
            "message": f"连接成功！版本 {ver}（{cfg['host']}:{cfg['port']} / {cfg['database']}{extra}）",
        }
    except Exception as exc:
        return {"ok": False, "message": f"数据库查询异常：{exc}"}
    finally:
        conn.close()


@router.get("/underwater/ledger")
def get_underwater_ledger(alert_limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """Read all tables (cameras, alerts, settings, devices) from configured underwater MySQL."""
    cfg = _load_underwater_db_cfg()
    db_label = f"{cfg['host']}:{cfg['port']} / {cfg['database']}"
    pub_cfg = _public_underwater_db_cfg(cfg)
    try:
        conn = _connect_underwater_db(cfg)
    except Exception:
        return {
            "online": False,
            "error": "连接数据库失败",
            "database": db_label,
            "dbConfig": pub_cfg,
            "cameras": [],
            "alerts": [],
            "settings": [],
            "devices": [],
            "alertTotal": 0,
            "latestAlertId": 0,
        }

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM `tb_camera` ORDER BY `state` DESC, `id` ASC")
            cameras = [_serialize_row(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM `tb_alert_settings` ORDER BY `id` ASC")
            settings = [_serialize_row(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM `tb_device` ORDER BY `id` ASC")
            devices = [_serialize_row(r) for r in cur.fetchall()]

            cur.execute("SELECT COUNT(*) AS cnt, MAX(`id`) AS max_id FROM `tb_alert_history`")
            stat_row = cur.fetchone() or {}
            alert_total = int(stat_row.get("cnt") or 0)
            latest_alert_id = int(stat_row.get("max_id") or 0)

            cur.execute(
                "SELECT `id`, `title`, `content`, `camera_id`, `push_devices`, `state`, "
                "`create_time`, `created_by`, `update_time`, `updated_by`, "
                "(`push_success` + 0) AS `push_success`, `camera_group`, "
                "(`image` IS NOT NULL AND LENGTH(`image`) > 0) AS `has_image` "
                "FROM `tb_alert_history` ORDER BY `id` DESC LIMIT %s",
                (alert_limit,),
            )
            alerts = [_serialize_row(r) for r in cur.fetchall()]

        return {
            "online": True,
            "database": db_label,
            "dbConfig": pub_cfg,
            "cameras": cameras,
            "alerts": alerts,
            "settings": settings,
            "devices": devices,
            "alertTotal": alert_total,
            "latestAlertId": latest_alert_id,
        }
    except Exception:
        return {
            "online": False,
            "error": "连接数据库失败",
            "database": db_label,
            "dbConfig": pub_cfg,
            "cameras": [],
            "alerts": [],
            "settings": [],
            "devices": [],
            "alertTotal": 0,
            "latestAlertId": 0,
        }
    finally:
        conn.close()


@router.get("/underwater/alert-image/{alert_id}")
def get_underwater_alert_image(alert_id: int) -> dict[str, Any]:
    """Fetch base64 snapshot image for a specific tb_alert_history row."""
    try:
        conn = _connect_underwater_db()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="连接数据库失败") from exc
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT `id`, `title`, `content`, `image`, `create_time` FROM `tb_alert_history` WHERE `id` = %s", (alert_id,))
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="报警记录不存在")
        img = row.get("image") or ""
        if img and not img.startswith("data:image"):
            img = f"data:image/png;base64,{img}"
        return {
            "id": row["id"],
            "title": row.get("title") or "",
            "content": row.get("content") or "",
            "create_time": row["create_time"].isoformat(sep=" ") if hasattr(row.get("create_time"), "isoformat") else str(row.get("create_time") or ""),
            "image": img,
        }
    finally:
        conn.close()


def _get_ffmpeg_bin() -> str:
    if imageio_ffmpeg is None:
        raise HTTPException(status_code=500, detail="后端未安装 imageio-ffmpeg 组件，无法转码 RTSP 视频流")
    return imageio_ffmpeg.get_ffmpeg_exe()


@router.get("/rtsp/mjpeg")
def stream_rtsp_as_mjpeg(url: str = Query(..., description="RTSP/HTTP stream URL")) -> StreamingResponse:
    """Transcode RTSP H.264/H.265 stream to low-latency multipart MJPEG for browser <img> playback."""
    target = url.strip()
    if not target.startswith(("rtsp://", "rtsps://", "http://", "https://")):
        raise HTTPException(status_code=400, detail="仅支持 rtsp:// 或 http:// 流地址")

    ffmpeg_exe = _get_ffmpeg_bin()
    cmd = [
        ffmpeg_exe,
        "-rtsp_transport", "tcp",
        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-i", target,
        "-vf", "scale=1280:-1",
        "-r", "15",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-q:v", "6",
        "pipe:1",
    ]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    def _mjpeg_generator():
        buf = bytearray()
        try:
            assert proc.stdout is not None
            while True:
                chunk = proc.stdout.read(16384)
                if not chunk:
                    break
                buf.extend(chunk)
                while True:
                    soi = buf.find(b"\xff\xd8")
                    if soi == -1:
                        if len(buf) > 65536:
                            buf.clear()
                        break
                    eoi = buf.find(b"\xff\xd9", soi + 2)
                    if eoi == -1:
                        if soi > 0:
                            del buf[:soi]
                        break
                    jpg = bytes(buf[soi : eoi + 2])
                    del buf[: eoi + 2]
                    _LATEST_FRAMES[target] = (time.time(), jpg)
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        + f"Content-Length: {len(jpg)}\r\n\r\n".encode("ascii")
                        + jpg
                        + b"\r\n"
                    )
        finally:
            try:
                proc.kill()
                proc.wait(timeout=2)
            except Exception:
                pass

    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.post("/ptz")
def send_visca_ptz(body: PtzCommandRequest) -> dict[str, Any]:
    """Send raw Sony VISCA command over TCP port 1259 to IP PTZ camera."""
    host = (body.host or "").strip()
    if not host:
        raise HTTPException(status_code=400, detail="请指定摄像机 IP")

    act = (body.action or "").strip().upper()
    pan_spd = max(1, min(0x18, int(body.speed)))
    tilt_spd = max(1, min(0x14, int(body.speed)))
    zoom_spd = max(1, min(7, int(body.speed) // 2 or 3))
    preset_id = max(0, min(127, int(body.preset)))

    cmd_map: dict[str, bytes] = {
        "UP": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x03, 0x01, 0xFF]),
        "DOWN": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x03, 0x02, 0xFF]),
        "LEFT": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x01, 0x03, 0xFF]),
        "RIGHT": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x02, 0x03, 0xFF]),
        "UP_LEFT": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x01, 0x01, 0xFF]),
        "UP_RIGHT": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x02, 0x01, 0xFF]),
        "DOWN_LEFT": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x01, 0x02, 0xFF]),
        "DOWN_RIGHT": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x02, 0x02, 0xFF]),
        "STOP": bytes([0x81, 0x01, 0x06, 0x01, pan_spd, tilt_spd, 0x03, 0x03, 0xFF]),
        "HOME": bytes([0x81, 0x01, 0x06, 0x04, 0xFF]),
        "ZOOM_IN": bytes([0x81, 0x01, 0x04, 0x07, 0x20 | zoom_spd, 0xFF]),
        "ZOOM_OUT": bytes([0x81, 0x01, 0x04, 0x07, 0x30 | zoom_spd, 0xFF]),
        "ZOOM_STOP": bytes([0x81, 0x01, 0x04, 0x07, 0x00, 0xFF]),
        "FOCUS_FAR": bytes([0x81, 0x01, 0x04, 0x08, 0x23, 0xFF]),
        "FOCUS_NEAR": bytes([0x81, 0x01, 0x04, 0x08, 0x33, 0xFF]),
        "FOCUS_STOP": bytes([0x81, 0x01, 0x04, 0x08, 0x00, 0xFF]),
        "FOCUS_AUTO": bytes([0x81, 0x01, 0x04, 0x38, 0x02, 0xFF]),
        "PRESET_SET": bytes([0x81, 0x01, 0x04, 0x3F, 0x01, preset_id, 0xFF]),
        "PRESET_CALL": bytes([0x81, 0x01, 0x04, 0x3F, 0x02, preset_id, 0xFF]),
    }
    frame = cmd_map.get(act)
    if frame is None:
        raise HTTPException(status_code=400, detail=f"不支持的 PTZ 指令: {act}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.5)
    try:
        sock.connect((host, body.port))
        sock.sendall(frame)
        try:
            resp = sock.recv(64)
        except socket.timeout:
            resp = b""
        return {
            "ok": True,
            "host": host,
            "port": body.port,
            "action": act,
            "tx_hex": frame.hex(" ").upper(),
            "rx_hex": resp.hex(" ").upper(),
        }
    except OSError as exc:
        raise HTTPException(status_code=502, detail=f"摄像机 PTZ 连接失败 ({host}:{body.port}): {exc}") from exc
    finally:
        sock.close()


def _ensure_snapshot_dir() -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR


def _load_snapshot_meta() -> list[dict[str, Any]]:
    if not SNAPSHOT_META_FILE.exists():
        return []
    try:
        data = json.loads(SNAPSHOT_META_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_snapshot_meta(items: list[dict[str, Any]]) -> None:
    _ensure_snapshot_dir()
    SNAPSHOT_META_FILE.write_text(
        json.dumps(items[:200], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _format_snapshot_record(item: dict[str, Any]) -> dict[str, Any] | None:
    filename = str(item.get("filename") or "").strip()
    if not filename or Path(filename).name != filename:
        return None
    file_path = SNAPSHOT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        return None
    stat = file_path.stat()
    return {
        "id": filename,
        "filename": filename,
        "cameraId": str(item.get("cameraId") or ""),
        "cameraName": str(item.get("cameraName") or filename),
        "streamUrl": str(item.get("streamUrl") or ""),
        "url": f"/api/video/snapshots/file/{urllib.parse.quote(filename)}",
        "publicUrl": f"/uploads/snapshots/{urllib.parse.quote(filename)}",
        "filePath": str(file_path.resolve()),
        "storageDir": str(SNAPSHOT_DIR.resolve()),
        "size": stat.st_size,
        "createdAt": str(item.get("createdAt") or datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")),
    }


def _grab_frame_from_stream(stream_url: str) -> bytes | None:
    target = (stream_url or "").strip()
    if not target:
        return None
    cached = _LATEST_FRAMES.get(target)
    if cached and (time.time() - cached[0]) <= 10.0 and cached[1]:
        return cached[1]
    if not target.startswith(("rtsp://", "rtsps://", "http://", "https://")):
        return None
    if imageio_ffmpeg is None:
        return None

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe]
    if target.startswith(("rtsp://", "rtsps://")):
        cmd.extend(["-rtsp_transport", "tcp"])
    cmd.extend([
        "-i", target,
        "-frames:v", "1",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-q:v", "3",
        "pipe:1",
    ])
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=6,
            creationflags=creationflags,
        )
        raw = res.stdout or b""
        soi = raw.find(b"\xff\xd8")
        eoi = raw.rfind(b"\xff\xd9")
        if soi != -1 and eoi != -1 and eoi > soi:
            return raw[soi : eoi + 2]
    except Exception:
        return None
    return None


@router.get("/snapshots")
def list_video_snapshots() -> dict[str, Any]:
    """List saved camera snapshots and return the local storage directory path."""
    snap_dir = _ensure_snapshot_dir()
    meta_items = _load_snapshot_meta()
    seen: set[str] = set()
    records: list[dict[str, Any]] = []

    for item in meta_items:
        rec = _format_snapshot_record(item)
        if rec and rec["filename"] not in seen:
            seen.add(rec["filename"])
            records.append(rec)

    # 扫描目录中可能存在但未登记到 index.json 的截图文件
    extra_files = sorted(
        (p for p in snap_dir.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for p in extra_files:
        if p.name in seen:
            continue
        rec = _format_snapshot_record({"filename": p.name, "cameraName": p.stem})
        if rec:
            seen.add(p.name)
            records.append(rec)

    return {
        "ok": True,
        "storageDir": str(snap_dir.resolve()),
        "snapshots": records,
    }


@router.post("/snapshot")
def capture_video_snapshot(body: SnapshotRequest) -> dict[str, Any]:
    """Capture a camera frame (from client base64 or active RTSP/HTTP stream) and save to public/uploads/snapshots."""
    snap_dir = _ensure_snapshot_dir()
    img_bytes: bytes | None = None
    ext = ".jpg"

    raw_b64 = (body.imageBase64 or "").strip()
    if raw_b64:
        if raw_b64.startswith("data:image/png"):
            ext = ".png"
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        try:
            img_bytes = base64.b64decode(raw_b64)
        except Exception:
            img_bytes = None

    if not img_bytes:
        img_bytes = _grab_frame_from_stream(body.streamUrl)

    if not img_bytes or len(img_bytes) < 64:
        raise HTTPException(
            status_code=502,
            detail="未获取到实时视频画面，请确认摄像机在线且正在正常出流后重试抓拍",
        )

    now_dt = datetime.now()
    safe_cam_id = re.sub(r"[^a-zA-Z0-9_-]+", "", str(body.cameraId or "cam"))[:24] or "cam"
    filename = f"snap_{now_dt.strftime('%Y%m%d_%H%M%S_%f')[:19]}_{safe_cam_id}{ext}"
    file_path = snap_dir / filename
    file_path.write_bytes(img_bytes)

    masked_stream = re.sub(r"//[^/@]+@", "//***@", (body.streamUrl or "").strip())
    meta_entry = {
        "filename": filename,
        "cameraId": str(body.cameraId or ""),
        "cameraName": (body.cameraName or "").strip() or f"摄像机 {safe_cam_id}",
        "streamUrl": masked_stream,
        "createdAt": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
    }
    meta_items = _load_snapshot_meta()
    meta_items.insert(0, meta_entry)
    _save_snapshot_meta(meta_items)

    record = _format_snapshot_record(meta_entry)
    return {
        "ok": True,
        "storageDir": str(snap_dir.resolve()),
        "snapshot": record,
    }


@router.get("/snapshots/file/{filename}")
def get_video_snapshot_file(filename: str):
    """Serve a saved snapshot image directly."""
    if not filename or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="非法文件名")
    file_path = SNAPSHOT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="抓拍截图文件不存在")
    media_type = "image/png" if file_path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(str(file_path), media_type=media_type)


@router.delete("/snapshots/{filename}")
def delete_video_snapshot(filename: str) -> dict[str, Any]:
    """Delete a saved snapshot image and its metadata entry."""
    if not filename or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="非法文件名")
    file_path = SNAPSHOT_DIR / filename
    if file_path.exists() and file_path.is_file():
        file_path.unlink()
    meta_items = [item for item in _load_snapshot_meta() if item.get("filename") != filename]
    _save_snapshot_meta(meta_items)
    return {"ok": True, "filename": filename}
