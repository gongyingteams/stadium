import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

res_all = client.get('/api/countries')
assert res_all.status_code == 200
data_all = res_all.json()
count_all = data_all.get('count')
print('Total count:', count_all)
assert count_all == 197, f'Expected 197, got {count_all}'

regions = {
    '亚洲': 48,
    '欧洲': 44,
    '非洲': 54,
    '北美洲': 23,
    '南美洲': 12,
    '大洋洲': 14,
    '其他': 2
}

for reg, expected_count in regions.items():
    res = client.get(f'/api/countries?region={reg}')
    assert res.status_code == 200
    actual = res.json()['count']
    assert actual == expected_count, f'Region {reg}: expected {expected_count}, got {actual}'
    print(f'Region {reg}: {actual} countries verified')

# Single country
res_cn = client.get('/api/countries/CN')
assert res_cn.status_code == 200
cn_data = res_cn.json()
assert cn_data['code'] == 'CN'
assert cn_data['codeAlpha3'] == 'CHN'
# anthemDuration 以实际音频时长为准: 中国国歌真实时长 48.56s, 经 scripts/recalibrate_durations.py
# 重新校准入库为 49 (原种子默认值 46 已过期, 见 scripts/anthem_duration_audit.json)
assert cn_data['anthemDuration'] == 49
print('CN country endpoint verified:', cn_data['nameCn'], cn_data['code'], cn_data['anthemName'])

# Static SVG file
res_svg = client.get('/uploads/flags/CN.svg')
assert res_svg.status_code == 200
assert '<svg' in res_svg.text
print('Static SVG endpoint verified, length:', len(res_svg.text))

# Static MP3 file
res_mp3 = client.get('/uploads/audio/CN.mp3')
assert res_mp3.status_code == 200
assert len(res_mp3.content) > 100000
print('Static MP3 endpoint verified, bytes:', len(res_mp3.content))

print('ALL BACKEND VERIFICATION CHECKS PASSED PERFECTLY!')
