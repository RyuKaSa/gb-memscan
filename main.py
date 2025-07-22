# main.py
import json
from pathlib import Path
from decoder import load_dump, build_value_map, generate_summary, generate_prose

JSON_OUT_FILE  = Path(__file__).resolve().parent / "json_summary.json"
PROSE_OUT_FILE = Path(__file__).resolve().parent / "prose_summary.txt"  # ← fixed extension

WRITE_TO_FILE  = True  # ← Toggle this flag to control writing

def stage_1_load():
    print("[Stage 1] Loading raw memory dump...")
    return load_dump()

def stage_2_decode(dump):
    print("[Stage 2] Decoding values from memory...")
    return build_value_map(dump)

def stage_3_summarize(values):
    print("[Stage 3] Generating structured summary...")
    return generate_summary(values)

def stage_4_output(summary: dict) -> dict:
    print("[Stage 4] Output handling...")
    if WRITE_TO_FILE:
        with open(JSON_OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"[Stage 4][DEBUG] Summary written to {JSON_OUT_FILE}")
    return summary

def stage_5_generate_prose(summary: dict) -> str:
    print("[Stage 5] Generating prose summary...")
    prose = generate_prose(summary)
    if WRITE_TO_FILE:
        with open(PROSE_OUT_FILE, "w", encoding="utf-8") as f:
            f.write(prose)
        print(f"[Stage 5][DEBUG] Prose written to {PROSE_OUT_FILE}")
    return prose

if __name__ == "__main__":
    dump     = stage_1_load()
    values   = stage_2_decode(dump)
    summary  = stage_3_summarize(values)
    summary  = stage_4_output(summary)
    prose    = stage_5_generate_prose(summary)
