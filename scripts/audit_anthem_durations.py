import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_COUNTRIES = ROOT / "src" / "data" / "countries_197.json"
AUDIO_DIR = ROOT / "public" / "uploads" / "audio"

def get_real_duration(filepath):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(filepath)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def verify_all():
    with open(JSON_COUNTRIES, "r", encoding="utf-8") as f:
        countries = json.load(f)

    discrepancies = []
    updated_countries = []

    print(f"Checking all {len(countries)} countries with ffprobe...")

    for c in countries:
        code = c["code"]
        audio_file = AUDIO_DIR / f"{code}.mp3"
        if not audio_file.exists():
            print(f"MISSING AUDIO FILE: {audio_file}")
            continue

        real_sec = get_real_duration(audio_file)
        if real_sec is None:
            continue

        # Round to integer seconds, or keep float if needed
        # In human display, rounded/ceil integer second is standard
        real_round = round(real_sec)
        configured_sec = c.get("anthemDuration", 46)
        diff = real_sec - configured_sec

        c_updated = dict(c)
        c_updated["anthemDurationPrecise"] = round(real_sec, 2)
        c_updated["anthemDuration"] = real_round
        updated_countries.append(c_updated)

        if abs(diff) >= 0.5:
            discrepancies.append({
                "code": code,
                "nameCn": c["nameCn"],
                "anthemName": c["anthemName"],
                "configured": configured_sec,
                "real_sec": round(real_sec, 2),
                "diff": round(diff, 2)
            })

    print(f"\n--- Verification Report ---")
    print(f"Total checked: {len(countries)}")
    print(f"Discrepancies (|diff| >= 0.5s): {len(discrepancies)}")
    
    # Sort by diff descending
    discrepancies.sort(key=lambda x: abs(x["diff"]), reverse=True)
    print("\nTop 20 Discrepancies:")
    for d in discrepancies[:20]:
        print(f"[{d['code']}] {d['nameCn']}《{d['anthemName']}》: 配置={d['configured']}s, 实际={d['real_sec']}s, 误差={d['diff']:+}s")

    # Save comparison report
    with open("scripts/anthem_duration_audit.json", "w", encoding="utf-8") as f:
        json.dump(discrepancies, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    verify_all()
