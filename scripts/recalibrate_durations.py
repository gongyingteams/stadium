import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_COUNTRIES = ROOT / "src" / "data" / "countries_197.json"
JSON_ASSETS = ROOT / "src" / "data" / "media_assets_197.json"
AUDIO_DIR = ROOT / "public" / "uploads" / "audio"

def format_duration(sec):
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"

def update_all():
    with open(JSON_COUNTRIES, "r", encoding="utf-8") as f:
        countries = json.load(f)
    with open(JSON_ASSETS, "r", encoding="utf-8") as f:
        assets = json.load(f)

    asset_map = {a["id"]: a for a in assets}

    updated_count = 0
    durations_dict = {}

    for c in countries:
        code = c["code"]
        audio_file = AUDIO_DIR / f"{code}.mp3"
        if not audio_file.exists():
            print(f"File not found: {audio_file}")
            continue

        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_file)
        ]
        real_duration_float = float(subprocess.check_output(cmd).decode("utf-8").strip())
        real_duration_int = round(real_duration_float)

        durations_dict[code] = {
            "sec": real_duration_int,
            "precise": round(real_duration_float, 2)
        }

        # Update country record
        old_dur = c.get("anthemDuration")
        c["anthemDuration"] = real_duration_int
        c["anthemDurationPrecise"] = round(real_duration_float, 2)

        # Update media asset record if exists
        anthem_asset_id = c.get("anthemAssetId")
        if anthem_asset_id and anthem_asset_id in asset_map:
            asset_map[anthem_asset_id]["durationSec"] = real_duration_int
            asset_map[anthem_asset_id]["durationFormatted"] = format_duration(real_duration_int)

        if old_dur != real_duration_int:
            updated_count += 1

    print(f"Total countries: {len(countries)}, Durations adjusted: {updated_count}")

    # Write back to src/data/countries_197.json
    with open(JSON_COUNTRIES, "w", encoding="utf-8") as f:
        json.dump(countries, f, ensure_ascii=False, indent=2)
    print(f"Updated {JSON_COUNTRIES}")

    # Write back to src/data/media_assets_197.json
    with open(JSON_ASSETS, "w", encoding="utf-8") as f:
        json.dump(list(asset_map.values()), f, ensure_ascii=False, indent=2)
    print(f"Updated {JSON_ASSETS}")

if __name__ == "__main__":
    update_all()
