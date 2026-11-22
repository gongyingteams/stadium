# -*- coding: utf-8 -*-
"""运行时验证: 启动真实后端, 以 admin/operator 身份验证菜单接口契约。"""
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def usable_python(cand):
    """该解释器是否能 import fastapi/uvicorn (项目 .venv 可能已失效, 需要逐个候选检查)"""
    if not cand or not Path(cand).exists():
        return False
    try:
        out = subprocess.run([str(cand), '-c', 'import fastapi, uvicorn'],
                             capture_output=True, timeout=40)
        return out.returncode == 0
    except Exception:
        return False


candidates = [
    ROOT / 'backend' / '.venv' / 'Scripts' / 'python.exe',
    Path(sys.executable),
]
which = shutil.which('python') or shutil.which('python.exe')
if which:
    candidates.append(Path(which))
PY = next((c for c in candidates if usable_python(c)), None)
if PY is None:
    print('FAIL: 没有可用的 Python 解释器 (需安装 fastapi / uvicorn)')
    sys.exit(1)
print(f'使用解释器: {PY}')

# 脚本内部启动的临时后端监听 8111 (BASE 必须与之保持一致, 否则会误打到机上常驻的旧后端)
BASE = 'http://127.0.0.1:8111'

proc = subprocess.Popen(
    [str(PY), '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8111'],
    cwd=str(ROOT / 'backend'),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)


def http(method, path, body=None, token=None, timeout=30):
    data = None
    headers = {'Content-Type': 'application/json'}
    if body is not None:
        data = json.dumps(body).encode('utf-8')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', 'replace')
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def wait_ready(max_wait=30):
    for _ in range(max_wait * 2):
        try:
            status, _ = http('GET', '/api/health', timeout=2)
            if status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


try:
    if not wait_ready():
        print('FAIL: 后端 30s 内未就绪')
        sys.exit(1)
    print('backend UP')

    # 未登录 401
    status, _ = http('GET', '/api/menu/config')
    assert status == 401, f'未登录应 401, 实际 {status}'

    # admin 登录
    status, data = http('POST', '/api/auth/login', {'username': 'admin', 'password': 'admin123'})
    assert status == 200, f'admin 登录失败 {status} {data}'
    admin_token = data['access_token']

    # GET 菜单树契约: DefaultLayout 将消费的字段
    status, tree = http('GET', '/api/menu/config', token=admin_token)
    assert status == 200, f'GET 失败 {status}'
    gs = tree['groups']
    assert len(gs) == 4
    assert [g['title'] for g in gs] == ['1. 综合态势', '2. 应用门户', '3. 物联控制', '4. 配置中心']
    for g in gs:
        assert all(k in g for k in ('id', 'menuKey', 'title', 'icon', 'visible', 'children'))
        for c in g['children']:
            assert all(k in c for k in ('id', 'menuKey', 'title', 'shortTitle', 'path', 'icon', 'visible', 'requiresAdmin', 'requiresOps', 'badgeType')), f'item 缺字段: {c}'
    assert gs[2]['children'][0]['path'] == '/iot/audio'
    cfg = [c for c in gs[3]['children'] if c['path'] == '/system/menu']
    assert len(cfg) == 1 and cfg[0]['requiresAdmin'] is True
    print('GET /api/menu/config 契约 OK:', sum(len(g['children']) for g in gs), '项')

    # operator 也能读
    status, data = http('POST', '/api/auth/login', {'username': 'operator', 'password': 'operator123'})
    op_token = data['access_token']
    status, tree2 = http('GET', '/api/menu/config', token=op_token)
    assert status == 200

    # operator 写被拒
    status, _ = http('PUT', '/api/menu/config', tree, token=op_token)
    assert status == 403, f'operator PUT 应 403, 实际 {status}'

    # admin 改一项 -> 真实落库 (主库), 再读回
    tree['groups'][0]['children'][0]['title'] = '运行时验证工作台'
    status, data = http('PUT', '/api/menu/config', tree, token=admin_token)
    assert status == 200 and data['success'] is True, f'PUT 失败 {status} {data}'
    status, tree3 = http('GET', '/api/menu/config', token=admin_token)
    assert tree3['groups'][0]['children'][0]['title'] == '运行时验证工作台'
    print('PUT 持久化 OK')

    # 恢复默认
    status, data = http('POST', '/api/menu/config/reset', token=admin_token)
    assert status == 200 and data['success'] is True
    status, tree4 = http('GET', '/api/menu/config', token=admin_token)
    assert tree4['groups'][0]['children'][0]['title'] == '场馆综合态势总览工作台'
    assert sum(len(g['children']) for g in tree4['groups']) == 18
    print('RESET OK')

    print('RUNTIME VERIFY PASSED')
finally:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
