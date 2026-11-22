"""LAN IP camera & vMix video source probing, control, and stream proxy router."""
from __future__ import annotations

import socket
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:
    import imageio_ffmpeg  # type: ignore
except Exception:  # pragma: no cover
    imageio_ffmpeg = None  # type: ignore

try:
    import pymysql  # type: ignore
except Exception:  # pragma: no cover
    pymysql = None  # type: ignore

UNDERWATER_DB_CFG = {
    "host": "192.168.0.33",
    "port": 3306,
    "user": "user_view",
    "password": "zm123456",
    "database": "image_platform",
    "charset": "utf8mb4",
}

router = APIRouter(prefix="/api/video", tags=["video"])


class VideoProbeRequest(BaseModel):
    target: str
    protocol: str = "auto"


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


def _connect_underwater_db():
    if pymysql is None:
        raise HTTPException(status_code=500, detail="后端未安装 pymysql 驱动")
    return pymysql.connect(
        **UNDERWATER_DB_CFG,
        connect_timeout=4,
        read_timeout=6,
        cursorclass=pymysql.cursors.DictCursor,
    )


@router.get("/underwater/ledger")
def get_underwater_ledger(alert_limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """Read all tables (cameras, alerts, settings, devices) from image_platform MySQL."""
    try:
        conn = _connect_underwater_db()
    except Exception:
        return {
            "online": False,
            "error": "连接数据库失败",
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
            "database": "192.168.0.33:3306 / image_platform",
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
