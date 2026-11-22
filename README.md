# 体育场馆应用集成管理系统（Venue IBMS Console）

前后端分离的体育场馆应用集成管控平台：Vue 3 + Vite 前端，FastAPI + SQLite 后端。

## 环境要求

- Node.js 18+（推荐 22 LTS）
- Python 3.10+（推荐 3.12）

## 快速开始（Windows）

```powershell
# 1. 克隆仓库
git clone https://github.com/gongyingteams/stadium.git
cd stadium

# 2. 安装前端依赖
npm install

# 3. 创建后端虚拟环境并安装依赖
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..

# 4. 启动（后端 8000 / 前端 3001）
.\start-dev-local.ps1
```

或手动分别启动：

```powershell
# 后端
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（项目根目录）
npx vite --host 0.0.0.0 --port 3001
```

打开 http://localhost:3001 ，后端 API 文档见 http://localhost:8000/docs 。

## 演示账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| `admin` | `admin123` | 系统管理员 |
| `ops` | `ops123` | 运维工程师 |
| `operator` | `operator123` | 场馆操作员 |
| `viewer` | `viewer123` | 只读查看者 |

## 团队协作流程

```bash
# 拉取最新代码
git pull origin main

# 开发新功能建议先建分支
git checkout -b feature/xxx

# 提交并推送
git add .
git commit -m "描述你的改动"
git push origin feature/xxx      # 分支：发起 Pull Request 合并到 main
# 或小改动直接推 main：git push origin main
```

约定：功能开发用 `feature/` 分支，修复用 `fix/` 分支，经 Pull Request 合并到 `main`。

## 目录结构

| 目录 | 说明 |
|---|---|
| `src/` | 前端源码（Vue 3） |
| `backend/` | 后端源码（FastAPI），独立 README 见 `backend/README.md` |
| `public/` | 前端静态资源 |
| `sql/` | 数据库迁移脚本 |
| `scripts/` | 构建/审计脚本 |
| `docs/` | 项目文档与协议资料 |
