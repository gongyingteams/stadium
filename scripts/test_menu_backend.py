# -*- coding: utf-8 -*-
"""
左侧导航菜单后台可配置化 —— 后端验证脚本
用法: python scripts/test_menu_backend.py
(使用独立测试库 backend/data/menu_test.db，不影响主库)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

import os

os.environ['DATABASE_PATH'] = str(ROOT / 'backend' / 'data' / 'menu_test.db')

# 每次运行使用全新测试库: audit_logs 等表会残留上次运行的记录 (如 MENU_CONFIG_RESET),
# 不清理会导致重跑时断言失败。等价于计划 Task 2 Step 5 的 "删除 menu_test.db 后重跑"。
_test_db = Path(os.environ['DATABASE_PATH'])
if _test_db.exists():
    _test_db.unlink()

from backend.app.main import app, init_db, db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(app)


def db_rows(sql, args=()):
    with db() as conn:
        return conn.execute(sql, args).fetchall()


def db_scalar(sql, args=()):
    with db() as conn:
        return conn.execute(sql, args).fetchone()[0]


# ============ Task 1: sys_menu 表 + 默认菜单播种 ============
init_db()

assert db_scalar("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='sys_menu'") == 1, \
    'sys_menu 表未创建'

groups = db_rows("SELECT * FROM sys_menu WHERE menu_type = 'GROUP' ORDER BY sort_order")
items = db_rows("SELECT * FROM sys_menu WHERE menu_type = 'ITEM'")
assert len(groups) == 4, f'期望 4 个分组, 实际 {len(groups)}'
assert len(items) == 18, f'期望 18 个菜单项, 实际 {len(items)}'
assert groups[0]['title'] == '1. 综合态势'
assert groups[3]['title'] == '4. 配置中心'

menu_mgmt = [r for r in items if r['path'] == '/system/menu']
assert len(menu_mgmt) == 1, '缺少 /system/menu 管理入口项'
assert menu_mgmt[0]['requires_admin'] == 1, '/system/menu 必须 requires_admin=1'
assert menu_mgmt[0]['parent_id'] == groups[3]['id'], '/system/menu 应属于配置中心分组'

audio = [r for r in items if r['path'] == '/iot/audio'][0]
assert audio['badge_type'] == 'AUDIO', 'audio 项应保留 badge_type=AUDIO'
assert audio['short_title'] == '专业扩声'
assert audio['menu_key'] == 'iot-audio'

devices = [r for r in items if r['path'] == '/config/devices'][0]
assert devices['badge_type'] == 'TOTAL' and devices['requires_ops'] == 1
users = [r for r in items if r['path'] == '/system/users'][0]
assert users['requires_admin'] == 1
dynamic = [r for r in items if r['path'] == '/iot/dynamic/group-01'][0]
assert dynamic['menu_key'] == 'iot-dynamic'

# 分组父子结构完整: 每个 ITEM 的 parent_id 都指向某个 GROUP
group_ids = {g['id'] for g in groups}
assert all(r['parent_id'] in group_ids for r in items), '存在孤立菜单项'

# 全部可见、启用
assert db_scalar("SELECT count(*) FROM sys_menu WHERE visible = 0") == 0

print('Menu seed verified OK (4 组 / 18 项)')

# ============ Task 2: 菜单接口 (GET / PUT / Reset) ============
# 鉴权: 未登录 401
res = client.get('/api/menu/config')
assert res.status_code == 401, f'未登录应 401, 实际 {res.status_code}'

tokens = {}
for u, p in [('admin', 'admin123'), ('ops', 'ops123'), ('operator', 'operator123'), ('viewer', 'viewer123')]:
    r = client.post('/api/auth/login', json={'username': u, 'password': p})
    assert r.status_code == 200, f'{u} 登录失败'
    tokens[u] = r.json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


# 读取: 所有登录角色都可拿到完整树
for role in ('admin', 'ops', 'operator', 'viewer'):
    res = client.get('/api/menu/config', headers=auth(tokens[role]))
    assert res.status_code == 200, f'{role} 读取菜单应 200, 实际 {res.status_code}'

res = client.get('/api/menu/config', headers=auth(tokens['operator']))
tree = res.json()
assert len(tree['groups']) == 4, '默认树应为 4 个分组'
g4 = tree['groups'][3]
assert g4['menuKey'] == 'g-config' and g4['visible'] is True
assert g4['title'] == '4. 配置中心'
first = g4['children'][0]
assert first['menuKey'] == 'config-devices'
assert first['badgeType'] == 'TOTAL' and first['requiresOps'] is True and first['requiresAdmin'] is False
assert all(k in first for k in ('id', 'menuKey', 'title', 'shortTitle', 'path', 'icon', 'visible', 'requiresAdmin', 'requiresOps', 'badgeType'))
audio_item = tree['groups'][2]['children'][0]
assert audio_item['path'] == '/iot/audio' and audio_item['badgeType'] == 'AUDIO' and audio_item['shortTitle'] == '专业扩声'

# 写权限: 仅 admin, 其余角色 403
put_body = {'groups': tree['groups']}
for role in ('ops', 'operator', 'viewer'):
    res = client.put('/api/menu/config', json=put_body, headers=auth(tokens[role]))
    assert res.status_code == 403, f'{role} 整树保存应被拒绝, 实际 {res.status_code}'
res = client.post('/api/menu/config/reset', headers=auth(tokens['operator']))
assert res.status_code == 403, 'operator reset 应被拒绝'
# 过期/伪造 token
res = client.put('/api/menu/config', json=put_body, headers={'Authorization': 'Bearer fake.token.here'})
assert res.status_code == 401

# admin 整树保存: 改文字 / 隐藏 / 清空组 / 新增分组(含外链项)
admin = auth(tokens['admin'])
res = client.put('/api/menu/config', json=put_body, headers=admin)
assert res.status_code == 200 and res.json()['success'] is True

t2 = client.get('/api/menu/config', headers=admin).json()
t2['groups'][0]['title'] = '99. 自定义态势'
t2['groups'][0]['children'][0]['title'] = '自定义工作台'
t2['groups'][0]['children'][0]['visible'] = False
t2['groups'][1]['children'] = []  # 删掉应用门户全部项
t2['groups'].append({
    'menuKey': 'g-new', 'title': '5. 新分组', 'icon': 'SvgAppGrid', 'visible': True,
    'children': [{
        'menuKey': 'x1', 'title': '外链大屏', 'shortTitle': '大屏',
        'path': 'http://192.168.1.9:8080/screen', 'icon': 'SvgLedScreen', 'visible': True,
        'requiresAdmin': False, 'requiresOps': False, 'badgeType': '',
    }],
})
res = client.put('/api/menu/config', json=t2, headers=admin)
assert res.status_code == 200, f'整树保存失败: {res.status_code} {res.text}'
t3 = client.get('/api/menu/config', headers=admin).json()
assert t3['groups'][0]['title'] == '99. 自定义态势'
assert t3['groups'][0]['children'][0]['title'] == '自定义工作台'
assert t3['groups'][0]['children'][0]['visible'] is False
assert t3['groups'][1]['children'] == []
assert t3['groups'][-1]['title'] == '5. 新分组'
assert t3['groups'][-1]['children'][0]['path'] == 'http://192.168.1.9:8080/screen'
assert t3['groups'][-1]['children'][0]['visible'] is True
# id 全部为整数 (前端按 id 也可行, 但不应保留旧 id 语义错乱: 只断言类型)
assert all(isinstance(g['id'], int) for g in t3['groups'])

# 校验防呆: 组标题空 / 菜单项 path 空 → 400
bad = {'groups': [{'menuKey': 'g1', 'title': '', 'icon': 'SvgAppGrid', 'visible': True, 'children': []}]}
res = client.put('/api/menu/config', json=bad, headers=admin)
assert res.status_code == 400, f'空组标题应 400, 实际 {res.status_code}'
bad2 = {'groups': [{'menuKey': 'g1', 'title': 'x', 'icon': 'SvgAppGrid', 'visible': True,
                    'children': [{'menuKey': 'i', 'title': 'y', 'shortTitle': '', 'path': '',
                                  'icon': 'SvgAppGrid', 'visible': True,
                                  'requiresAdmin': False, 'requiresOps': False, 'badgeType': ''}]}]}
res = client.put('/api/menu/config', json=bad2, headers=admin)
assert res.status_code == 400, f'空菜单项 path 应 400, 实际 {res.status_code}'
# 菜单项 title 空也拒绝
bad3 = {'groups': [{'menuKey': 'g1', 'title': 'x', 'icon': 'SvgAppGrid', 'visible': True,
                    'children': [{'menuKey': 'i', 'title': '', 'shortTitle': '', 'path': '/dashboard',
                                  'icon': 'SvgAppGrid', 'visible': True,
                                  'requiresAdmin': False, 'requiresOps': False, 'badgeType': ''}]}]}
res = client.put('/api/menu/config', json=bad3, headers=admin)
assert res.status_code == 400, f'空菜单项 title 应 400, 实际 {res.status_code}'
# 全部隐藏的树应拒绝 (至少 1 个可见分组)
bad4 = {'groups': [{'menuKey': 'g1', 'title': 'x', 'icon': 'SvgAppGrid', 'visible': False, 'children': []}]}
res = client.put('/api/menu/config', json=bad4, headers=admin)
assert res.status_code == 400, f'无可见分组应 400, 实际 {res.status_code}'
# 重复链接应拒绝: 同一页面不能由两个菜单入口同时指向
dup = {'groups': [
    {'menuKey': 'g1', 'title': 'x', 'icon': 'SvgAppGrid', 'visible': True, 'children': [
        {'menuKey': 'i1', 'title': '项一', 'shortTitle': '', 'path': '/dashboard',
         'icon': 'SvgAppGrid', 'visible': True, 'requiresAdmin': False, 'requiresOps': False, 'badgeType': ''},
        {'menuKey': 'i2', 'title': '项二', 'shortTitle': '', 'path': '/dashboard',
         'icon': 'SvgAppGrid', 'visible': True, 'requiresAdmin': False, 'requiresOps': False, 'badgeType': ''},
    ]},
]}
res = client.put('/api/menu/config', json=dup, headers=admin)
assert res.status_code == 400, f'重复链接应 400, 实际 {res.status_code}'
assert '项一' in res.json()['detail'] and '项二' in res.json()['detail'], f'报错应指出冲突双方: {res.text}'
# 结尾斜杠变体也应判为同一页面
dup['groups'][0]['children'][1]['path'] = '/dashboard/'
res = client.put('/api/menu/config', json=dup, headers=admin)
assert res.status_code == 400, f'结尾斜杠变体应判为重复, 实际 {res.status_code}'
# 外链重复同样拒绝
dup['groups'][0]['children'][0]['path'] = 'http://example.com/a'
dup['groups'][0]['children'][1]['path'] = 'http://example.com/a/'
res = client.put('/api/menu/config', json=dup, headers=admin)
assert res.status_code == 400, f'外链重复应 400, 实际 {res.status_code}'
# 不重复的合法树应放行
ok = {'groups': [
    {'menuKey': 'g1', 'title': 'x', 'icon': 'SvgAppGrid', 'visible': True, 'children': [
        {'menuKey': 'i1', 'title': '项一', 'shortTitle': '', 'path': '/dashboard',
         'icon': 'SvgAppGrid', 'visible': True, 'requiresAdmin': False, 'requiresOps': False, 'badgeType': ''},
        {'menuKey': 'i2', 'title': '项二', 'shortTitle': '', 'path': 'http://example.com/a',
         'icon': 'SvgAppGrid', 'visible': True, 'requiresAdmin': False, 'requiresOps': False, 'badgeType': ''},
    ]},
]}
res = client.put('/api/menu/config', json=ok, headers=admin)
assert res.status_code == 200, f'不重复树应 200, 实际 {res.status_code} {res.text}'

# 审计落库
with db() as conn:
    rows = conn.execute("SELECT * FROM audit_logs WHERE event_type = 'MENU_CONFIG_UPDATE'").fetchall()
    assert len(rows) >= 1, '缺少 MENU_CONFIG_UPDATE 审计记录'
    assert rows[0]['username'] == 'admin' and rows[0]['result'] == 'SUCCESS'
    reset_rows = conn.execute("SELECT * FROM audit_logs WHERE event_type = 'MENU_CONFIG_RESET'").fetchall()

# 恢复默认
res = client.post('/api/menu/config/reset', headers=admin)
assert res.status_code == 200 and res.json()['success'] is True
assert len(reset_rows) == 0, 'reset 尚未执行, 不应提前有记录'
t4 = client.get('/api/menu/config', headers=admin).json()
assert t4['groups'][0]['title'] == '1. 综合态势'
assert any(c['path'] == '/system/menu' for g in t4['groups'] for c in g['children']), '恢复默认后应含管理入口'
assert sum(len(g['children']) for g in t4['groups']) == 18
assert len(t4['groups']) == 4

# 防锁死: 删掉管理入口后仍可 reset
t5 = client.get('/api/menu/config', headers=admin).json()
t5['groups'][3]['children'] = [c for c in t5['groups'][3]['children'] if c['path'] != '/system/menu']
assert len(client.put('/api/menu/config', json=t5, headers=admin).json()['data']['groups']) == 4
res = client.post('/api/menu/config/reset', headers=admin)
assert res.status_code == 200
t6 = client.get('/api/menu/config', headers=admin).json()
assert any(c['path'] == '/system/menu' for g in t6['groups'] for c in g['children']), 'reset 必须恢复管理入口'

print('Menu API verified OK')

