#!/usr/bin/env python3
import json
from pathlib import Path

HERE         = Path(__file__).resolve().parent
RAW_DUMP     = HERE / "memory_dump.json"
SUMMARY_FILE = HERE / "summary.json"

def load_tbl(fname: str) -> dict[int, str]:
    path = HERE / fname
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # int(k,0) handles "0x00" → 0, "42" → 42
    return {int(k, 0): v for k, v in data.items()}

# ─── Lookup tables ─────────────────────────────────────────
CHARSET = load_tbl("dataset/charset.json")
SPECIES = load_tbl("dataset/species.json")
MOVES   = load_tbl("dataset/moves.json")
TYPES   = load_tbl("dataset/types.json")
ITEMS   = load_tbl("dataset/items.json")

BADGE_NAMES = [
    "Boulder","Cascade","Thunder","Rainbow",
    "Soul","Marsh","Volcano","Earth"
]

# ─── BCD converters ────────────────────────────────────────
def bcd3(b1: int, b2: int, b3: int) -> int:
    to_dec = lambda x: (x >> 4)*10 + (x & 0xF)
    return to_dec(b1)*10000 + to_dec(b2)*100 + to_dec(b3)

def bcd2(b1: int, b2: int) -> int:
    to_dec = lambda x: (x >> 4)*10 + (x & 0xF)
    return to_dec(b1)*100 + to_dec(b2)

# ─── Decoders ──────────────────────────────────────────────
def decode_name(bytes_seq: list[int]) -> str:
    out = []
    for b in bytes_seq:
        if b == 0x50:  # <END>
            break
        out.append(CHARSET.get(b, "?"))
    return "".join(out)

def decode_status(byte: int) -> list[str]:
    if byte == 0:
        return []
    cond = []
    if byte & 0x40: cond.append("PAR")
    if byte & 0x20: cond.append("FRZ")
    if byte & 0x10: cond.append("BRN")
    if byte & 0x08: cond.append("PSN")
    sleep = byte & 0x07
    if sleep:
        cond.append(f"SLP({sleep})")
    return cond

def lookup(table: dict[int, str], key: int) -> str:
    return table.get(key, f"Unknown({key})")

# ─── Load raw dump ─────────────────────────────────────────
with open(RAW_DUMP, encoding="utf-8") as f:
    dump = json.load(f)

# map address→(label,raw)
addr_map = {int(addr, 16): (label, raw) for addr, label, raw in dump}

# pre-extract multi-byte fields
money_raw     = [addr_map[x][1] for x in (0xD347, 0xD348, 0xD349)]
chips_raw     = [addr_map[x][1] for x in (0xD5A4, 0xD5A5)]
trainer_bytes = [addr_map[0xD158 + i][1] for i in range(5)]
rival_bytes   = [addr_map[0xD34A + i][1] for i in range(8)]

# ─── Build label→value map ────────────────────────────────
values: dict[str, object] = {}
for _, label, raw in dump:
    decoded = None

    # numeric fields
    if label == "Money[1]":
        decoded = bcd3(*money_raw)
    elif label == "Casino Chips[1]":
        decoded = bcd2(*chips_raw)
    elif label == "Badges Bitfield":
        decoded = [BADGE_NAMES[i] for i in range(8) if (raw >> i) & 1]

    # names
    elif label.startswith("Trainer Name"):
        decoded = decode_name(trainer_bytes)
    elif label.startswith("Rival Name"):
        decoded = decode_name(rival_bytes)

    # *** skip species decoding here – keep raw ID for summary ***
    # elif "Species" in label:
    #     decoded = lookup(SPECIES, raw)

    # other lookups
    elif "Move" in label:
        decoded = lookup(MOVES, raw)
    elif "Type" in label:
        decoded = lookup(TYPES, raw)
    elif label.endswith("ID"):
        decoded = lookup(ITEMS, raw)
    elif label.endswith("Status"):
        decoded = decode_status(raw)

    # event flags → boolean
    elif label.startswith(("Fought ", "Defeated ", "Have ")) or label.endswith(" gone"):
        decoded = bool(raw)

    # assign raw if nothing decoded or decode == raw
    values[label] = decoded if decoded is not None and decoded != raw else raw

# ─── Assemble summary ──────────────────────────────────────
summary = {
    "trainer": {
        "name":       values.get("Trainer Name[1]"),
        "id_hi":      values.get("Player ID-hi"),
        "id_lo":      values.get("Player ID-lo"),
        "party_size": values.get("Party Size")
    },
    "money":        values.get("Money[1]"),
    "casino_chips": values.get("Casino Chips[1]"),
    "badges":       values.get("Badges Bitfield"),
    "map": {
        "number":        values.get("Current Map Number"),
        "tileset":       values.get("Map Tileset"),
        "width":         values.get("Map Width (blocks)"),
        "height":        values.get("Map Height (blocks)"),
        "player_x":      values.get("Player X-Position"),
        "player_y":      values.get("Player Y-Position"),
        "last_location": values.get("Last Map Location")
    },
    "game_options": {
        "value":       values.get("Game Options"),
        "audio_track": values.get("Audio Track"),
        "audio_bank":  values.get("Audio Bank")
    }
}

# ─── Party ────────────────────────────────────────────────
party = []
size  = values.get("Party Size", 0) or 0
for i in range(1, size + 1):
    raw_id = values.get(f"PKM{i} Species", 0)
    lo     = values.get(f"PKM{i} HP lo", 0)
    hi     = values.get(f"PKM{i} HP hi", 0)
    # swapped order: hi-byte is low part, lo-byte is high part
    hp_current = hi + (lo << 8)

    party.append({
        "species":    SPECIES.get(raw_id, f"Unknown({raw_id})"),
        "level":      values.get(f"PKM{i} Level"),
        "hp_current": hp_current,
        "status":     values.get(f"PKM{i} Status"),
        "types":      [
            values.get(f"PKM{i} Type1"),
            values.get(f"PKM{i} Type2")
        ],
        "moves":     [values.get(f"PKM{i} Move{j}") for j in range(1, 5)],
        "pp":        [values.get(f"PKM{i} PP{j}")   for j in range(1, 5)]
    })

summary["party"] = party

# ─── Bag & PC items ───────────────────────────────────────
summary["bag"] = {
    values[f"Bag{i} ID"]: values[f"Bag{i} Qty"]
    for i in range(1, (values.get("Bag Count") or 0) + 1)
    if values.get(f"Bag{i} ID")
}
summary["pc"] = {
    values[f"PC{i} ID"]: values[f"PC{i} Qty"]
    for i in range(1, (values.get("PC Count") or 0) + 1)
    if values.get(f"PC{i} ID")
}

# ─── Event flags ─────────────────────────────────────────
summary["flags"] = {
    lbl: bool(values[lbl])
    for lbl in values
    if lbl.startswith(("Fought ", "Defeated ", "Have ")) or lbl.endswith(" gone")
}

# ─── Write out summary only ───────────────────────────────
with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"Summary written → {SUMMARY_FILE}")
