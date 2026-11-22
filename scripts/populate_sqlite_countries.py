import json
import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "backend" / "data" / "venue_backend.db"
JSON_PATH = ROOT / "src" / "data" / "countries_197.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def populate():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        countries = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
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

    cur.execute("CREATE INDEX IF NOT EXISTS idx_country_region ON sys_country(region);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_country_code ON sys_country(code);")

    inserted = 0
    updated = 0
    current_time = now()

    for idx, c in enumerate(countries):
        cur.execute("""
        INSERT INTO sys_country (
            id, code, code_alpha3, name_cn, name_en, region, pattern, c1, c2, c3,
            flag_desc, image_url, flag_asset_id, flag_asset_name, flag_source_type,
            anthem_name, anthem_en, anthem_duration, anthem_url, anthem_asset_id,
            anthem_asset_name, anthem_file_name, anthem_source_type, sort_order,
            status, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            1, ?, ?
        )
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
            c["id"], c["code"], c["codeAlpha3"], c["nameCn"], c["nameEn"], c["region"],
            c["pattern"], c["c1"], c["c2"], c["c3"], c.get("flagDesc", ""),
            c["imageUrl"], c["flagAssetId"], c["flagAssetName"], c.get("flagSourceType", "asset"),
            c["anthemName"], c.get("anthemEn", ""), c["anthemDuration"],
            c["anthemUrl"], c["anthemAssetId"], c["anthemAssetName"],
            c.get("anthemFileName", ""), c.get("anthemSourceType", "asset"),
            idx + 1, current_time, current_time
        ))
        inserted += 1

    conn.commit()
    count = cur.execute("SELECT count(*) FROM sys_country").fetchone()[0]
    conn.close()
    print(f"SQLite sys_country populated successfully! Total rows: {count}")

if __name__ == "__main__":
    populate()
