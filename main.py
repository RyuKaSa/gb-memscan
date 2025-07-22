# main.py
import json
from pathlib import Path
from decoder import load_dump, build_value_map, generate_summary

OUT_FILE = Path(__file__).resolve().parent / "summary.json"

def stage_1_load():
    print("[Stage 1] Loading raw memory dump...")
    return load_dump()

def stage_2_decode(dump):
    print("[Stage 2] Decoding values from memory...")
    return build_value_map(dump)

def stage_3_summarize(values):
    print("[Stage 3] Generating structured summary...")
    return generate_summary(values)

def stage_4_output(summary):
    print(f"[Stage 4] Writing summary to {OUT_FILE}...")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("✔ Summary written.")

if __name__ == "__main__":
    dump    = stage_1_load()
    values  = stage_2_decode(dump)
    summary = stage_3_summarize(values)
    stage_4_output(summary)
