# Venue IBMS FastAPI backend

独立于现有 Vue 前端的可运行基础服务。默认使用 SQLite（`backend/data/venue_backend.db`）保存审计日志、告警和 Mock 状态；启动时自动建表。演示账号仅用于本地联调，前端不会自动登录：

| 用户名 | 密码 | 角色 |
|---|---|---|
| `admin` | `admin123` | admin |
| `ops` | `ops123` | ops |
| `operator` | `operator123` | operator |
| `viewer` | `viewer123` | viewer |

## Windows 运行

```powershell
cd backend
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:JWT_SECRET = "replace-with-a-long-random-secret"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

也可以从仓库根目录启动：`python -m uvicorn app.main:app --app-dir backend --reload --port 8000`。

打开 `http://localhost:8000/docs` 查看 OpenAPI。Vite 开发端 `http://localhost:3000` 已在 CORS 白名单中；没有修改现有 Vite 配置。

## API 行为

- `POST /api/auth/login` 接收 `{ "username": "admin", "password": "admin123" }`，返回 30 分钟 HS256 Bearer JWT。演示账号不会由服务或前端默认登录。
- `POST /api/auth/logout`、`GET /api/me` 需要 `Authorization: Bearer <token>`。
- `GET /api/audit` 和 `GET /api/alarms` 只允许 `admin`、`ops`；`POST /api/mock/toggle` 也只允许这两个角色。`/api/mock/status` 需要登录。
- `POST /api/devices/{device_id}/command` 允许 `admin`、`ops`、`operator`。Mock 开启时返回带 `MOCK-...` 的明确模拟回执且不接触硬件；关闭时如果没有注册驱动，返回 HTTP 503 并明确拒绝，不伪装成功。
- `GET /api/health` 无需登录。

生产部署前必须设置随机 `JWT_SECRET`、修改演示账号/迁移至真实身份源，并将 `MOCK_MODE=false` 前先注册真实驱动。SQLite 是基础服务的持久化实现，后续可替换为 MySQL/Redis。
